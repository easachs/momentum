from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from tracker.models import Habit, HabitCompletion

class TestDashboardView(TestCase):
    """Tests for the Dashboard View"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")
        self.habit = Habit.objects.create(
            user=self.user, name="Test Habit", frequency="daily", category="health"
        )

    def test_dashboard_analytics(self):
        """Test dashboard analytics calculation"""
        habit = Habit.objects.create(
            user=self.user, name="Analytics Test Habit", frequency="daily"
        )

        # Create some completions
        for i in range(5):
            HabitCompletion.objects.create(
                habit=habit,
                completed_at=timezone.localtime(timezone.now()).date()
                - timedelta(days=i),
            )

        response = self.client.get(
            reverse("social:dashboard", kwargs={"username": self.user.username})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue("habit_analytics" in response.context)
        self.assertEqual(response.context["habit_analytics"]["total_habits"], 2)

    def test_streak_analytics(self):
        """Test streak calculations in analytics"""
        habit = Habit.objects.create(
            user=self.user,
            name="Streak Test Habit",
            frequency="daily",
            category="health",
        )

        today = timezone.localtime(timezone.now()).date()
        # Create completions for the last 5 days
        for i in range(5):
            HabitCompletion.objects.create(
                habit=habit, completed_at=today - timedelta(days=i)
            )

        response = self.client.get(
            reverse("social:dashboard", kwargs={"username": self.user.username})
        )
        analytics = response.context["habit_analytics"]

        self.assertEqual(analytics["best_streak"], 5)
