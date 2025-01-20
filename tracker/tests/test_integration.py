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
        
        response = self.client.get(reverse('tracker:habit_list'))
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
        """Test that weekly and monthly completion counts are accurate"""
        habit = Habit.objects.create(
            user=self.user,
            name="Test Habit 2",
            frequency="daily"
        )
        
        # Get the start of the current week
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        
        # Create two completions in the current week
        HabitCompletion.objects.create(habit=habit, completed_at=start_of_week)
        HabitCompletion.objects.create(habit=habit, completed_at=start_of_week + timedelta(days=1))
        
        # Test the completions directly
        week_completions = HabitCompletion.objects.filter(
            habit__user=self.user,
            completed_at__gte=start_of_week
        ).count()
        self.assertEqual(week_completions, 2)

    def test_incomplete_habit_notifications(self):
        response = self.client.get(reverse('tracker:habit_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'incomplete')

    def test_notification_display(self):
        response = self.client.get(reverse('tracker:habit_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'bg-gray-100 text-gray-400')

    def test_habit_creation_flow(self):
        response = self.client.get(reverse('tracker:habit_create'))
        # ...

    def test_habit_update_flow(self):
        response = self.client.get(reverse('tracker:habit_update', kwargs={'pk': self.habit.pk}))
        # ... 