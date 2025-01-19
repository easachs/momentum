from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from tracker.models import Habit, HabitCompletion

class TestHabitIntegration(TestCase):
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
            category='health'
        )

    def test_category_performance_stats(self):
        # Create habits in different categories
        habit1 = Habit.objects.create(
            user=self.user,
            name="Health Habit",
            category="health",
            frequency="daily"
        )
        habit2 = Habit.objects.create(
            user=self.user,
            name="Learning Habit",
            category="learning",
            frequency="daily"
        )

        # Complete one habit
        habit1.toggle_completion()
        
        response = self.client.get(reverse('tracker:habit_list', kwargs={'username': self.user.username}))
        category_stats = {
            stat['category']: stat 
            for stat in response.context['analytics']['category_stats']
        }

        # Check health category stats (now we have 2 health habits, one completed)
        self.assertEqual(category_stats['health']['completed'], 1)
        self.assertEqual(category_stats['health']['total'], 2)  # Updated to expect 2 total

        # Check learning category stats
        self.assertEqual(category_stats['learning']['completed'], 0)
        self.assertEqual(category_stats['learning']['total'], 1)

    def test_weekly_monthly_completion_counts(self):
        today = timezone.now().date()
        habit = Habit.objects.create(
            user=self.user,
            name="Test Habit 2",
            frequency="daily"
        )

        # Create completions across different time periods
        dates = [
            today,
            today - timedelta(days=1),
            today - timedelta(days=7),
            today - timedelta(days=14),
            today - timedelta(days=30)
        ]
        for date in dates:
            HabitCompletion.objects.create(habit=habit, completed_at=date)

        response = self.client.get(reverse('tracker:habit_list', kwargs={'username': self.user.username}))
        analytics = response.context['analytics']

        self.assertEqual(analytics['this_week_completions'], 2)  # Today and yesterday
        self.assertEqual(analytics['this_month_completions'], 4)  # All except the 30-day-old one

    def test_incomplete_habit_notifications(self):
        response = self.client.get(reverse('tracker:habit_list', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'incomplete')

    def test_notification_display(self):
        response = self.client.get(reverse('tracker:habit_list', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'bg-gray-100 text-gray-400') 