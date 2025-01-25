from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from tracker.models import Habit, HabitCompletion

class TestHabitViews(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_login(self.user)
        self.habit = Habit.objects.create(
            name='Test Habit',
            user=self.user,
            frequency='daily',
            description=''  # Add empty string for description
        )

    def test_habit_create_view(self):
        url = reverse('tracker:habit_create')
        data = {
            'name': 'Read Books',
            'description': 'Read for 30 minutes',
            'frequency': 'daily',
            'category': 'learning'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Habit.objects.filter(name='Read Books').exists())

    def test_habit_update_view(self):
        url = reverse('tracker:habit_update', args=[self.habit.pk])
        data = {
            'name': 'Exercise Updated',
            'description': '',  # Add empty string for description
            'frequency': self.habit.frequency,
            'category': 'health'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.habit.refresh_from_db()
        self.assertEqual(self.habit.name, 'Exercise Updated')

    def test_habit_delete_view(self):
        url = reverse('tracker:habit_delete', args=[self.habit.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Habit.objects.filter(pk=self.habit.pk).exists())

    def test_cannot_update_other_users_habit(self):
        other_user = get_user_model().objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='testpass123'
        )
        self.client.force_login(other_user)

        url = reverse('tracker:habit_update', args=[self.habit.pk])
        data = {
            'name': 'Hacked Exercise',
            'description': '',  # Add empty string for description
            'frequency': self.habit.frequency,
            'category': 'health'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 404)
        self.habit.refresh_from_db()
        self.assertEqual(self.habit.name, 'Test Habit')

    def test_cannot_delete_other_users_habit(self):
        other_user = get_user_model().objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='testpass123'
        )
        self.client.force_login(other_user)

        url = reverse('tracker:habit_delete', args=[self.habit.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Habit.objects.filter(pk=self.habit.pk).exists())

    def test_toggle_completion_view(self):
        """Test that toggle_completion view works"""
        today = timezone.now().date()
        response = self.client.post(
            reverse('tracker:toggle_completion', kwargs={'pk': self.habit.pk}),
            {'date': today.strftime('%Y-%m-%d')}
        )
        self.assertEqual(response.status_code, 302)

    def test_toggle_completion_requires_login(self):
        self.client.logout()
        url = reverse('tracker:toggle_completion', args=[self.habit.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_toggle_completion_with_invalid_habit_id(self):
        url = reverse('tracker:toggle_completion', args=[99999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_habit_list_view_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('tracker:habit_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_habit_list_view_shows_user_habits(self):
        response = self.client.get(reverse('tracker:habit_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Habit')

    def test_user_can_only_see_own_habits(self):
        other_user = get_user_model().objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        self.client.force_login(other_user)
        response = self.client.get(reverse('tracker:habit_list'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Test Habit')

    def test_habit_create_view_invalid_data(self):
        url = reverse('tracker:habit_create')
        data = {
            'name': 'Ab',  # Too short
            'frequency': 'invalid',
            'category': 'invalid'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)  # Returns to form with errors
        self.assertFalse(Habit.objects.filter(name='Ab').exists())

    def test_habit_update_view_invalid_data(self):
        url = reverse('tracker:habit_update', args=[self.habit.pk])
        data = {
            'name': 'Ab',  # Too short
            'frequency': 'invalid',
            'category': 'invalid'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)  # Returns to form with errors
        self.habit.refresh_from_db()
        self.assertEqual(self.habit.name, 'Test Habit')  # Name unchanged

    def test_habit_list_empty_for_new_user(self):
        new_user = get_user_model().objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )
        self.client.force_login(new_user)
        response = self.client.get(reverse('tracker:habit_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No habits yet')

    def test_habit_detail_view(self):
        response = self.client.get(
            reverse('tracker:habit_detail', kwargs={'pk': self.habit.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Habit')

    def test_redirect_after_create(self):
        response = self.client.post(
            reverse('tracker:habit_create'),
            {'name': 'New Habit', 'frequency': 'daily', 'category': 'health'}
        )
        self.assertRedirects(
            response,
            reverse('tracker:habit_list')
        )

    def test_unauthenticated_user_redirected_to_login(self):
        self.client.logout()  # Make sure to log out first
        response = self.client.get(reverse('tracker:habit_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_toggle_completion_preserves_referer(self):
        """Test that toggle_completion preserves the referer header"""
        response = self.client.post(
            reverse('tracker:toggle_completion', kwargs={'pk': self.habit.pk}),
            HTTP_REFERER='/some/url/'
        )  # Also not providing a date parameter
        self.assertEqual(response.status_code, 302)

    def test_habit_list_shows_completion_status(self):
        self.habit.toggle_completion()
        response = self.client.get(
            reverse('tracker:habit_list')
        )
        self.assertContains(response, 'bg-green-200 text-green-700')

    def test_habit_detail_shows_completion_status(self):
        self.habit.toggle_completion()
        response = self.client.get(
            reverse('tracker:habit_detail', kwargs={'pk': self.habit.pk})
        )
        self.assertContains(response, 'bg-green-200 text-green-700')

    def test_view_mode_switching(self):
        response = self.client.get(
            reverse('tracker:habit_list') + '?view=category'
        )
        self.assertEqual(response.status_code, 200)

    def test_streak_calculation(self):
        today = timezone.now().date()

        # Create completions for the last 3 days
        for i in range(3):
            HabitCompletion.objects.create(
                habit=self.habit,
                completed_at=today - timedelta(days=i)
            )

        response = self.client.get(reverse('tracker:habit_list'))
        self.assertContains(response, 'Streak: 3')

    def test_dashboard_analytics(self):
        """Test dashboard analytics calculation"""
        habit = Habit.objects.create(
            user=self.user,
            name="Analytics Test Habit",
            frequency="daily"
        )

        # Create some completions
        for i in range(5):
            HabitCompletion.objects.create(
                habit=habit,
                completed_at=timezone.now().date() - timedelta(days=i)
            )

        response = self.client.get(reverse('social:dashboard', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('habit_analytics' in response.context)
        self.assertEqual(response.context['habit_analytics']['total_habits'], 2)

    def test_habit_analytics_calculation(self):
        """Test that habit analytics are calculated correctly"""
        today = timezone.now().date()
        one_day_ago = today - timedelta(days=1)

        # Create test habits with known completion patterns
        health_habits = [
            Habit.objects.create(
                user=self.user,
                name=f"Daily Health {i}",
                category="health",
                frequency="daily",
                created_at=one_day_ago
            ) for i in range(4)
        ]

        weekly_habit = Habit.objects.create(
            user=self.user,
            name="Weekly Health",
            category="health",
            frequency="weekly",
            created_at=one_day_ago
        )

        # Create completions matching the scenario:
        # - Two daily habits completed both days (4 completions)
        # - One daily habit completed once (1 completion)
        # - One daily habit not completed
        # - Weekly habit completed once (1 completion)

        # First two daily habits - complete both days
        for habit in health_habits[:2]:
            for days_ago in [0, 1]:
                HabitCompletion.objects.create(
                    habit=habit,
                    completed_at=today - timedelta(days=days_ago)
                )

        # Third daily habit - complete only today
        HabitCompletion.objects.create(
            habit=health_habits[2],
            completed_at=today
        )

        # Fourth daily habit - no completions

        # Weekly habit - complete once
        HabitCompletion.objects.create(
            habit=weekly_habit,
            completed_at=today
        )

        # Get analytics through the view
        response = self.client.get(reverse('tracker:habit_list'))
        analytics = response.context['habit_analytics']

        # Verify calculations
        health_stats = next(
            stat for stat in analytics['category_stats']
            if stat['category'] == 'health'
        )

        # Expected values:
        # - Total possible: 9 daily (4 habits × 2 days + 1 from setup) + 1 weekly = 10
        # - Total completed: 4 (two habits × 2 days) + 1 (one habit × 1 day) + 1 weekly = 6
        # - Completion rate: 6/10 ≈ 60%

        self.assertEqual(health_stats['total'], 10)  # Total possible
        self.assertEqual(health_stats['completed'], 6)  # Actual completions
        self.assertAlmostEqual(health_stats['percentage'], 60.0, places=1)  # Completion rate
