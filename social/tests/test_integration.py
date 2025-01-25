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
from jobhunt.models import Application

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
        """Test that dashboard displays correct analytics"""
        test_now = self.mock_now.return_value
        
        habit = Habit.objects.create(
            user=self.user1,
            name="Test Habit",
            frequency="daily",
            created_at=test_now
        )
        
        # Create a completion for this week
        HabitCompletion.objects.create(
            habit=habit,
            completed_at=test_now
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
        self.assertTrue('habit_analytics' in response.context)
        self.assertEqual(response.context['habit_analytics']['total_habits'], 1)
        self.assertEqual(response.context['habit_analytics']['this_week_completions'], 1)

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
        self.assertEqual(response.context['habit_analytics']['this_week_completions'], 0)
        self.assertEqual(response.context['habit_analytics']['this_month_completions'], 0)

    def test_analytics_with_edge_dates(self):
        """Test that analytics handle edge dates correctly"""
        habit = Habit.objects.create(
            user=self.user1,
            name="Test Habit",
            frequency="daily",
            created_at=self.mock_now.return_value
        )
        # Create a completion at the start of the month
        HabitCompletion.objects.create(
            habit=habit,
            completed_at=timezone.now().date().replace(day=1)
        )
        
        response = self.client.get(
            reverse('social:dashboard', kwargs={'username': self.user1.username})
        )
        self.assertEqual(response.context['habit_analytics']['this_month_completions'], 1)

    def test_completion_rate_calculation(self):
        """Test that completion rates are calculated correctly"""
        # Set the mock time to today before creating the habit
        test_now = timezone.datetime.combine(self.today, timezone.datetime.min.time())
        test_now = timezone.make_aware(test_now)
        self.mock_now.return_value = test_now
        
        habit = Habit.objects.create(
            user=self.user1,
            name="Test Habit",
            frequency="daily",
            created_at=test_now  # Explicitly set creation time
        )

        # Add 1 completion for today out of 1 possible completion
        completions = []
        completion = HabitCompletion.objects.create(
            habit=habit,
            completed_at=test_now
        )
        completions.append(completion)
        
        response = self.client.get(
            reverse('social:dashboard', kwargs={'username': self.user1.username})
        )
        
        # For a daily habit created today:
        # - Total possible completions = 1 (today)
        # - Actual completions = 1
        # - Expected rate = 100%
        self.assertEqual(response.context['habit_analytics']['completion_rate'], 100.0)

    def test_weekly_habit_completion_rate(self):
        """Test completion rate calculation for weekly habits"""
        habit = Habit.objects.create(
            user=self.user1,
            name="Weekly Habit",
            frequency="weekly",
            created_at=self.mock_now.return_value
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
        self.assertEqual(response.context['habit_analytics']['completion_rate'], 100.0)

    def test_multiple_habits_completion_rate(self):
        """Test completion rate calculation with multiple habits"""
        # Create habits with explicit creation time
        habits = [
            Habit.objects.create(
                user=self.user1,
                name=f"Test Habit {i}",
                frequency="daily",
                created_at=self.mock_now.return_value
            ) for i in range(3)
        ]
        
        # Add completions
        for habit in habits:
            HabitCompletion.objects.create(habit=habit, completed_at=self.today)
        
        response = self.client.get(
            reverse('social:dashboard', kwargs={'username': self.user1.username})
        )
        
        # Daily habits: 3 completions out of 3 possible = 100%
        self.assertEqual(response.context['habit_analytics']['completion_rate'], 100.0)

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
            self.assertLess(len(context.captured_queries), 25)  # Increased due to application analytics

    def test_dashboard_application_analytics(self):
        """Test that application analytics appear correctly on dashboard"""
        dates = [
            self.mock_now.return_value,
            self.mock_now.return_value - timedelta(days=3),
            self.mock_now.return_value - timedelta(days=10),
        ]
        
        statuses = ['wishlist', 'applied', 'offered']
        
        for date, status in zip(dates, statuses):
            self.mock_now.return_value = date
            Application.objects.create(
                user=self.user1,
                company=f'Company {date}',
                title=f'Position {date}',
                status=status,
            )
            
        # Reset mock time back to original for analytics calculation
        self.mock_now.return_value = timezone.datetime.combine(self.today, timezone.datetime.min.time())
        
        # View own dashboard
        self.client.force_login(self.user1)
        response = self.client.get(reverse('social:dashboard', kwargs={'username': self.user1.username}))
        self.assertEqual(response.status_code, 200)
        
        # Check analytics are present and correct
        analytics = response.context['application_analytics']
        self.assertEqual(analytics['total'], 3)
        self.assertEqual(analytics['week'], 2)
        self.assertEqual(analytics['offers'], 1)
        
        # Check analytics are visible in HTML
        self.assertContains(response, 'Application Analytics')
        self.assertContains(response, 'Total Applications')
        self.assertContains(response, 'Total Offers')
        
        # Check analytics are hidden for non-friends
        self.client.force_login(self.user2)
        response = self.client.get(reverse('social:dashboard', kwargs={'username': self.user1.username}))
        self.assertNotContains(response, 'Application Analytics')

class TestConcurrentOperations(TransactionTestCase):
    def setUp(self):
        # Set up timezone mock like other tests
        fixed_date = timezone.datetime(2024, 1, 1).astimezone(timezone.get_current_timezone())
        self.patcher = mock.patch('django.utils.timezone.now')
        self.mock_now = self.patcher.start()
        self.mock_now.return_value = fixed_date

        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.habit = Habit.objects.create(
            user=self.user,
            name="Concurrent Habit",
            frequency="daily"
        )
        
    def tearDown(self):
        self.patcher.stop()

    def test_concurrent_completions(self):
        """Test concurrent habit completions"""
        today = self.mock_now.return_value.date()
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
        self.assertLess(len(context), 25, "Too many queries being executed")
