from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.contrib.auth import get_user_model
from social.models import Friendship
from tracker.models import Habit, HabitCompletion
from django.utils import timezone
from datetime import timedelta
from unittest import mock
from django.db import connection

class TestSocialViews(TestCase):
    def setUp(self):
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
        self.user3 = get_user_model().objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )
        self.client.force_login(self.user1)

        # Set up timezone mock
        fixed_date = timezone.datetime(2024, 1, 1).astimezone(timezone.get_current_timezone())
        self.patcher = mock.patch('django.utils.timezone.now')
        self.mock_now = self.patcher.start()
        self.mock_now.return_value = fixed_date

    def test_send_friend_request(self):
        response = self.client.get(
            reverse('social:send_friend_request', kwargs={'username': self.user2.username})
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Friendship.objects.filter(
                sender=self.user1,
                receiver=self.user2,
                status='pending'
            ).exists()
        )

    def test_handle_friend_request_accept(self):
        friendship = Friendship.objects.create(
            sender=self.user2,
            receiver=self.user1,
            status='pending'
        )
        response = self.client.get(
            reverse('social:handle_friend_request', 
                   kwargs={'friendship_id': friendship.id, 'action': 'accept'})
        )
        self.assertEqual(response.status_code, 302)
        friendship.refresh_from_db()
        self.assertEqual(friendship.status, 'accepted')

    def test_handle_friend_request_decline(self):
        friendship = Friendship.objects.create(
            sender=self.user2,
            receiver=self.user1,
            status='pending'
        )
        response = self.client.get(
            reverse('social:handle_friend_request', 
                   kwargs={'friendship_id': friendship.id, 'action': 'decline'})
        )
        self.assertEqual(response.status_code, 302)
        friendship.refresh_from_db()
        self.assertEqual(friendship.status, 'declined')

    def test_friends_list_view(self):
        Friendship.objects.create(
            sender=self.user1,
            receiver=self.user2,
            status='accepted'
        )
        response = self.client.get(reverse('social:friends_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user2.username)

    def test_leaderboard_view(self):
        # Create some habits and completions for testing
        habit = Habit.objects.create(
            user=self.user1,
            name="Test Habit",
            frequency="daily",
            category="health"
        )
        habit.toggle_completion()  # Complete the habit

        response = self.client.get(reverse('social:leaderboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user1.username)

    def test_leaderboard_category_filter(self):
        # Create and complete a health habit
        habit = Habit.objects.create(
            user=self.user1,
            name="Test Habit",
            frequency="daily",
            category="health"
        )
        habit.toggle_completion()

        # Check health category - should see user with completed habit
        response = self.client.get(reverse('social:leaderboard') + '?category=health')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user1.username)

        # Create learning habit but don't complete it
        learning_habit = Habit.objects.create(
            user=self.user1,
            name="Learning Habit",
            frequency="daily",
            category="learning"
        )

        # Check learning category - should still see user because they have a habit
        response = self.client.get(reverse('social:leaderboard') + '?category=learning')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user1.username)

    def test_cannot_send_friend_request_to_self(self):
        response = self.client.get(
            reverse('social:send_friend_request', kwargs={'username': self.user1.username})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Friendship.objects.filter(
                sender=self.user1,
                receiver=self.user1
            ).exists()
        )

    def test_cannot_handle_other_users_friend_request(self):
        friendship = Friendship.objects.create(
            sender=self.user2,
            receiver=self.user3,  # Not self.user1
            status='pending'
        )
        
        response = self.client.get(
            reverse('social:handle_friend_request', 
                   kwargs={'friendship_id': friendship.id, 'action': 'accept'})
        )
        self.assertEqual(response.status_code, 302)  # Redirects with error message
        self.assertRedirects(response, reverse('social:dashboard', kwargs={'username': self.user1.username}))

    def test_leaderboard_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('social:leaderboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_friends_list_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('social:friends_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_dashboard_view(self):
        """Test the dashboard view for authenticated user"""
        response = self.client.get(
            reverse('social:dashboard', kwargs={'username': self.user1.username})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'social/dashboard.html')
        self.assertTrue(response.context['is_own_profile'])
        self.assertEqual(response.context['viewed_user'], self.user1)

    def test_dashboard_view_unauthenticated(self):
        """Test that unauthenticated users are redirected to login"""
        self.client.logout()
        response = self.client.get(
            reverse('social:dashboard', kwargs={'username': self.user1.username})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_dashboard_view_other_user(self):
        """Test viewing another user's dashboard"""
        other_user = get_user_model().objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        # Create friendship to allow viewing
        Friendship.objects.create(
            sender=self.user1,
            receiver=other_user,
            status='accepted'
        )
        response = self.client.get(
            reverse('social:dashboard', kwargs={'username': other_user.username})
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_own_profile'])
        self.assertEqual(response.context['viewed_user'], other_user)

    def test_dashboard_habit_analytics(self):
        """Test that dashboard habit analytics are calculated correctly"""
        # Set a fixed time for the entire test
        test_now = timezone.datetime(2024, 1, 3, 12, 0).astimezone(timezone.get_current_timezone())
        self.mock_now.return_value = test_now
        
        one_day_ago = test_now - timedelta(days=1)
        
        # Create habits with explicit created_at times
        health_habits = [
            Habit.objects.create(
                user=self.user1,
                name=f"Daily Health {i}",
                category="health",
                frequency="daily",
                created_at=one_day_ago
            ) for i in range(4)
        ]
        
        weekly_habit = Habit.objects.create(
            user=self.user1,
            name="Weekly Health",
            category="health",
            frequency="weekly",
            created_at=one_day_ago
        )
        
        # Create completions with explicit completed_at times
        for habit in health_habits[:2]:
            for days_ago in [0, 1]:
                HabitCompletion.objects.create(
                    habit=habit,
                    completed_at=test_now - timedelta(days=days_ago)
                )
        
        # Third daily habit - complete only today
        HabitCompletion.objects.create(
            habit=health_habits[2],
            completed_at=test_now
        )
        
        # Weekly habit - complete once
        HabitCompletion.objects.create(
            habit=weekly_habit,
            completed_at=test_now
        )
        
        # Get analytics through the dashboard view
        response = self.client.get(
            reverse('social:dashboard', kwargs={'username': self.user1.username})
        )
        analytics = response.context['habit_analytics']
        
        # Verify calculations
        health_stats = next(
            stat for stat in analytics['category_stats'] 
            if stat['category'] == 'health'
        )
        
        # Expected values:
        # - Total possible: 8 daily (4 habits × 2 days) + 1 weekly = 9
        # - Total completed: 4 (two habits × 2 days) + 1 (one habit × 1 day) + 1 weekly = 6
        # - Completion rate: 6/9 ≈ 67%
        
        self.assertEqual(health_stats['total'], 9)  # Total possible
        self.assertEqual(health_stats['completed'], 6)  # Actual completions
        self.assertAlmostEqual(health_stats['percentage'], 66.7, places=1)  # Completion rate 

    def test_get_habit_analytics_query_efficiency(self):
        """Test that get_habit_analytics uses efficient queries"""
        # Create some test habits with completions
        habits = []
        for i in range(3):
            habit = Habit.objects.create(
                user=self.user1,
                name=f"Test Habit {i}",
                frequency="daily"
            )
            habits.append(habit)
            
            # Add some completions
            for j in range(5):  # 5 completions per habit
                HabitCompletion.objects.create(
                    habit=habit,
                    completed_at=timezone.now().date() - timedelta(days=j)
                )

        # Test query efficiency
        with CaptureQueriesContext(connection) as context:
            from social.views import get_habit_analytics
            analytics = get_habit_analytics(Habit.objects.filter(user=self.user1))
            # Should only need a few queries to get all the data
            self.assertLess(len(context.captured_queries), 5)

    def tearDown(self):
        self.patcher.stop()
