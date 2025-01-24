from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from social.models import Friendship
from tracker.models import Habit, HabitCompletion
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from concurrent.futures import ThreadPoolExecutor
from django.test.utils import CaptureQueriesContext
from django.db import connection
from unittest import mock

class TestSocialIntegration(TestCase):
    def setUp(self):
        # Set up a fixed time first, before creating any objects
        fixed_date = timezone.datetime(2024, 1, 1).astimezone(timezone.get_current_timezone())
        self.patcher = mock.patch('django.utils.timezone.now')
        self.mock_now = self.patcher.start()
        self.mock_now.return_value = fixed_date
        
        self.user1 = get_user_model().objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = get_user_model().objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.client.force_login(self.user1)
        self.today = fixed_date.date()
        print("\nTest setup:")
        print(f"  today: {self.today}")
        print(f"  mocked now: {self.mock_now.return_value}")

    def tearDown(self):
        self.patcher.stop()

    def test_friend_request_to_habit_viewing_flow(self):
        # Create a habit for user2
        habit = Habit.objects.create(
            user=self.user2,
            name="Test Habit",
            frequency="daily"
        )

        # Try to view user2's dashboard (should not see analytics)
        response = self.client.get(reverse('social:dashboard', kwargs={'username': self.user2.username}))
        self.assertNotContains(response, 'Your Habit Analytics')

        # Send friend request
        self.client.get(
            reverse('social:send_friend_request', kwargs={'username': self.user2.username})
        )

        # Login as user2
        self.client.force_login(self.user2)

        # Accept friend request
        friendship = Friendship.objects.get(sender=self.user1, receiver=self.user2)
        self.client.get(
            reverse('social:handle_friend_request', 
                   kwargs={'friendship_id': friendship.id, 'action': 'accept'})
        )

        # Login back as user1
        self.client.force_login(self.user1)

        # Now should be able to see user2's analytics
        response = self.client.get(reverse('social:dashboard', kwargs={'username': self.user2.username}))
        self.assertContains(response, "user2's Habit Analytics")

    def test_leaderboard_completion_update_flow(self):
        # Create habits for both users
        habit1 = Habit.objects.create(
            user=self.user1,
            name="User1 Habit",
            frequency="daily",
            category="health"
        )
        
        habit2 = Habit.objects.create(
            user=self.user2,
            name="User2 Habit",
            frequency="daily",
            category="health"
        )

        # Complete habit2 multiple times to ensure higher completion count
        for _ in range(5):
            habit2.toggle_completion()
        
        # Check leaderboard order
        response = self.client.get(reverse('social:leaderboard'))
        
        # Instead of searching raw HTML, check the actual data
        leaderboard_data = response.context['leaderboard_data']
        
        # Verify both users are in the leaderboard
        user_ids = [entry['user'].id for entry in leaderboard_data]
        self.assertIn(self.user1.id, user_ids)
        self.assertIn(self.user2.id, user_ids)
        
        # Check that user2 comes before user1 in the leaderboard data
        user2_index = next(i for i, entry in enumerate(leaderboard_data) if entry['user'] == self.user2)
        user1_index = next(i for i, entry in enumerate(leaderboard_data) if entry['user'] == self.user1)
        self.assertTrue(user2_index < user1_index)

    def test_dashboard_analytics_display(self):
        """Test that dashboard displays analytics correctly"""
        # Create some habits and completions
        habit = Habit.objects.create(
            user=self.user1,
            name="Test Habit",
            frequency="daily"
        )
        HabitCompletion.objects.create(
            habit=habit,
            completed_at=timezone.now()
        )

        # Create friendship to allow viewing analytics
        if self.user1 != self.user2:
            Friendship.objects.create(
                sender=self.user1,
                receiver=self.user2,
                status='accepted'
            )

        response = self.client.get(
            reverse('social:dashboard', kwargs={'username': self.user1.username})
        )
        self.assertEqual(response.status_code, 200)
        # Check that analytics are displayed
        self.assertTrue('analytics' in response.context)
        self.assertEqual(response.context['analytics']['total_habits'], 1)
        self.assertEqual(response.context['analytics']['this_week_completions'], 1)

    def test_dashboard_friend_requests(self):
        """Test that dashboard shows friend requests"""
        # Create a pending friend request
        Friendship.objects.create(
            sender=self.user2,
            receiver=self.user1,
            status='pending'
        )

        response = self.client.get(
            reverse('social:dashboard', kwargs={'username': self.user1.username})
        )
        # Check that friend requests are in the context
        self.assertTrue('friend_requests' in response.context)
        self.assertEqual(len(response.context['friend_requests']), 1)
        self.assertEqual(response.context['friend_requests'][0].sender, self.user2)

    def test_analytics_with_future_dates(self):
        """Test analytics calculations with future-dated completions"""
        habit = Habit.objects.create(
            user=self.user1,
            name="Future Habit",
            frequency="daily"
        )
        future_date = timezone.now().date() + timedelta(days=1)
        HabitCompletion.objects.create(
            habit=habit,
            completed_at=future_date
        )
        
        response = self.client.get(
            reverse('social:dashboard', kwargs={'username': self.user1.username})
        )
        self.assertEqual(response.context['analytics']['this_week_completions'], 0)
        self.assertEqual(response.context['analytics']['this_month_completions'], 0)

    def test_analytics_with_edge_dates(self):
        """Test that analytics handle edge dates correctly"""
        habit = Habit.objects.create(
            user=self.user1,
            name="Test Habit",
            frequency="daily"
        )
        # Create a completion at the start of the month
        HabitCompletion.objects.create(
            habit=habit,
            completed_at=timezone.now().date().replace(day=1)
        )
        
        response = self.client.get(
            reverse('social:dashboard', kwargs={'username': self.user1.username})
        )
        self.assertEqual(response.context['analytics']['this_month_completions'], 1)

    def test_completion_rate_calculation(self):
        """Test that completion rates are calculated correctly"""
        habit = Habit.objects.create(
            user=self.user1,
            name="Test Habit",
            frequency="daily"
        )
        
        # Add 1 completion for today out of 1 possible completion
        completions = []
        completion = HabitCompletion.objects.create(
            habit=habit,
            completed_at=self.today
        )
        completions.append(completion)
        
        response = self.client.get(
            reverse('social:dashboard', kwargs={'username': self.user1.username})
        )
        
        # For a daily habit created today:
        # - Total possible completions = 1 (today)
        # - Actual completions = 1
        # - Expected rate = 100%
        self.assertEqual(response.context['analytics']['completion_rate'], 100.0)

    def test_weekly_habit_completion_rate(self):
        """Test completion rate calculation for weekly habits"""
        habit = Habit.objects.create(
            user=self.user1,
            name="Weekly Habit",
            frequency="weekly"
        )
        
        # Add 1 completion for this week
        HabitCompletion.objects.create(
            habit=habit,
            completed_at=self.today
        )
        
        response = self.client.get(
            reverse('social:dashboard', kwargs={'username': self.user1.username})
        )
        
        # For a weekly habit created today:
        # - Total possible completions = 1 (this week)
        # - Actual completions = 1
        # - Expected rate = 100%
        self.assertEqual(response.context['analytics']['completion_rate'], 100.0)

    def test_multiple_habits_completion_rate(self):
        """Test completion rate calculation with multiple habits"""
        daily_habit1 = Habit.objects.create(
            user=self.user1,
            name="Daily Habit 1",
            frequency="daily"
        )
        daily_habit2 = Habit.objects.create(
            user=self.user1,
            name="Daily Habit 2",
            frequency="daily"
        )
        weekly_habit = Habit.objects.create(
            user=self.user1,
            name="Weekly Habit",
            frequency="weekly"
        )
        
        # Add completions
        HabitCompletion.objects.create(habit=daily_habit1, completed_at=self.today)
        HabitCompletion.objects.create(habit=weekly_habit, completed_at=self.today)
        
        response = self.client.get(
            reverse('social:dashboard', kwargs={'username': self.user1.username})
        )
        
        # Daily habit1: 1 completion out of 1 possible
        # Daily habit2: 0 completions out of 1 possible
        # Weekly habit: 1 completion out of 1 possible
        # Total: 2 completions out of 3 possible = 66.7%
        self.assertEqual(response.context['analytics']['completion_rate'], 66.7)

    def test_analytics_query_efficiency(self):
        """Test that analytics calculations are efficient"""
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(
                reverse('social:dashboard', kwargs={'username': self.user1.username})
            )
            self.assertEqual(response.status_code, 200)
            
            analytics_queries = [
                q for q in context.captured_queries 
                if 'analytics' in str(q['sql']).lower() or 
                   'habit' in str(q['sql']).lower()
            ]
            
            # Analytics should use efficient aggregation
            self.assertLess(len(analytics_queries), 5)

    def test_dashboard_query_count(self):
        """Test that dashboard view uses efficient queries"""
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(
                reverse('social:dashboard', kwargs={'username': self.user1.username})
            )
            self.assertEqual(response.status_code, 200)
            
            # Dashboard is more complex, but should still be optimized
            self.assertLess(len(context.captured_queries), 20)

class TestConcurrentOperations(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.habit = Habit.objects.create(
            user=self.user,
            name="Concurrent Habit",
            frequency="daily"
        )
        
    def test_concurrent_completions(self):
        """Test concurrent habit completions"""
        today = timezone.now().date()
        def complete_habit():
            with transaction.atomic():
                HabitCompletion.objects.get_or_create(
                    habit=self.habit,
                    completed_at=today
                )
                
        # Run multiple completions concurrently
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(complete_habit) for _ in range(4)]
            
        # Verify we have exactly one completion for today
        self.assertEqual(
            HabitCompletion.objects.filter(
                habit=self.habit,
                completed_at=today
            ).count(),
            1
        )

class TestPerformance(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create 100 habits
        habits = [
            Habit(
                user=cls.user,
                name=f"Habit {i}",
                frequency="daily"
            ) for i in range(100)
        ]
        Habit.objects.bulk_create(habits)
        
        # Create 1000 completions
        completions = []
        for habit in Habit.objects.all():
            for i in range(10):
                completions.append(
                    HabitCompletion(
                        habit=habit,
                        completed_at=timezone.now().date() - timedelta(days=i)
                    )
                )
        HabitCompletion.objects.bulk_create(completions)
        
    def test_analytics_performance(self):
        """Test analytics performance with large dataset"""
        self.client.force_login(self.user)
        
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(
                reverse('social:dashboard', kwargs={'username': self.user.username})
            )
            
        # Assert reasonable query count (adjust number based on optimizations)
        self.assertLess(len(context), 20, "Too many queries being executed") 