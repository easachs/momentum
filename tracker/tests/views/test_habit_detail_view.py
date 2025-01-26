from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test.utils import CaptureQueriesContext
from django.db import connection
from tracker.models import Habit, HabitCompletion

class TestHabitDetailView(TestCase):
    """Tests for the Habit Detail View"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        created_at = timezone.localtime(timezone.now()) - timedelta(days=5)
        self.habit = Habit.objects.create(
            user=self.user,
            name="Test Habit",
            frequency="daily",
            category="health",
            created_at=created_at,
        )

    def test_habit_detail_view_requires_login(self):
        self.client.logout()
        response = self.client.get(
            reverse("tracker:habit_detail", kwargs={"pk": self.habit.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)


    def test_habit_detail_view_shows_correct_context(self):
        """Test that habit detail view shows correct context data"""
        response = self.client.get(
            reverse('tracker:habit_detail', kwargs={'pk': self.habit.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Habit")
        self.assertEqual(response.context['habit'], self.habit)
        self.assertIn('analytics', response.context)

    def test_habit_detail_view_shows_completion_status(self):
        """Test that completed habits show completion status"""
        today = timezone.localtime(timezone.now()).date()
        self.habit.completions.create(completed_at=today)

        response = self.client.get(
            reverse('tracker:habit_detail', kwargs={'pk': self.habit.pk})
        )

        self.assertTrue(response.context['today_completion'])
        self.assertContains(response, 'bg-green-200 text-green-700')

    def test_habit_detail_completion_rate(self):
        """Test that habit detail view shows correct completion rate"""
        today = timezone.localtime(timezone.now()).date()
        # Create 3 completions in the last 6 days
        for i in range(3):
            HabitCompletion.objects.create(
                habit=self.habit,
                completed_at=today - timedelta(days=i)
            )

        response = self.client.get(
            reverse("tracker:habit_detail", kwargs={"pk": self.habit.pk})
        )
        self.assertEqual(response.status_code, 200)

        # Should show 3 completions out of 6 possible days (50%)
        self.assertContains(response, "50.0%")

        # Verify the context data
        analytics = response.context["analytics"]
        self.assertEqual(analytics["completion_rate"], 50.0)
        self.assertEqual(analytics["total_completions"], 3)
        self.assertEqual(analytics["total_possible"], 6)  # 6 days including today

    def test_habit_detail_view_unauthorized_access(self):
        """Test that users can't access other users' habits"""
        other_user = get_user_model().objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        other_habit = Habit.objects.create(
            user=other_user,
            name="Other Habit",
            frequency="daily",
            category="health"
        )

        response = self.client.get(
            reverse('tracker:habit_detail', kwargs={'pk': other_habit.pk})
        )
        self.assertEqual(response.status_code, 404)

    # Query Optimization
    def test_habit_detail_query_count(self):
        # Test that habit detail view uses efficient queries
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(
                reverse("tracker:habit_detail", kwargs={"pk": self.habit.pk})
            )
            self.assertEqual(response.status_code, 200)

            # We expect queries for:
            # 1. User authentication
            # 2. Get habit with prefetched completions
            # 3. Get badges
            # 4. Get completion counts
            # 5. Get streak data
            # 6. Get category stats
            self.assertLess(len(context.captured_queries), 10)