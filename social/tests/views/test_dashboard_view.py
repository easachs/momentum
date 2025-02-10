from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from social.models import Friendship
from habits.models import Habit, HabitCompletion
from unittest import mock
from django.db import connection
from django.test.utils import CaptureQueriesContext
class TestDashboardView(TestCase):
    # Tests for the Dashboard View

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

        # Set up timezone mock
        fixed_date = timezone.datetime(2024, 1, 1).astimezone(
            timezone.get_current_timezone()
        )
        self.patcher = mock.patch("django.utils.timezone.now")
        self.mock_now = self.patcher.start()
        self.mock_now.return_value = fixed_date

    def test_dashboard_view(self):
        # Test the dashboard view for authenticated user
        response = self.client.get(
            reverse("social:dashboard", kwargs={"username": self.user.username})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "social/dashboard.html")
        self.assertTrue(response.context["is_own_profile"])
        self.assertEqual(response.context["viewed_user"], self.user)

    def test_dashboard_view_unauthenticated(self):
        # Test that unauthenticated users are redirected to login
        self.client.logout()
        response = self.client.get(
            reverse("social:dashboard", kwargs={"username": self.user.username})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_dashboard_view_other_user(self):
        # Test viewing another user's dashboard
        other_user = get_user_model().objects.create_user(
            username="otheruser", password="testpass123"
        )
        # Create friendship to allow viewing
        Friendship.objects.create(
            sender=self.user, receiver=other_user, status="accepted"
        )
        response = self.client.get(
            reverse("social:dashboard", kwargs={"username": other_user.username})
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["is_own_profile"])
        self.assertEqual(response.context["viewed_user"], other_user)

    def test_dashboard_analytics(self):
        # Test dashboard analytics calculation
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
        self.assertEqual(response.context["habit_analytics"]["total_habits"], 1)

    def test_more_dashboard_analytics(self):
        # Test that dashboard habit analytics are calculated correctly
        # Set a fixed time for the entire test
        test_now = timezone.datetime(2024, 1, 3, 12, 0).astimezone(
            timezone.get_current_timezone()
        )
        self.mock_now.return_value = test_now

        one_day_ago = test_now - timedelta(days=1)

        # Create habits with explicit created_at times
        health_habits = [
            Habit.objects.create(
                user=self.user,
                name=f"Daily Health {i}",
                category="health",
                frequency="daily",
                created_at=one_day_ago,
            )
            for i in range(4)
        ]

        weekly_habit = Habit.objects.create(
            user=self.user,
            name="Weekly Health",
            category="health",
            frequency="weekly",
            created_at=one_day_ago,
        )

        # Create completions with explicit completed_at times
        for habit in health_habits[:2]:
            for days_ago in [0, 1]:
                HabitCompletion.objects.create(
                    habit=habit, completed_at=test_now - timedelta(days=days_ago)
                )

        # Third daily habit - complete only today
        HabitCompletion.objects.create(habit=health_habits[2], completed_at=test_now)

        # Weekly habit - complete once
        HabitCompletion.objects.create(habit=weekly_habit, completed_at=test_now)

        # Get analytics through the dashboard view
        response = self.client.get(
            reverse("social:dashboard", kwargs={"username": self.user.username})
        )
        analytics = response.context["habit_analytics"]

        # Verify calculations
        health_stats = next(
            stat for stat in analytics["category_stats"] if stat["category"] == "health"
        )

        # Expected values:
        # - Total possible: 8 daily (4 habits × 2 days) + 1 weekly = 9
        # - Total completed: 4 (two habits × 2 days) + 1 (one habit × 1 day) + 1 weekly = 6
        # - Completion rate: 6/9 ≈ 67%

        self.assertEqual(health_stats["total"], 9)  # Total possible
        self.assertEqual(health_stats["completed"], 6)  # Actual completions
        self.assertAlmostEqual(
            health_stats["percentage"], 66.7, places=1
        )  # Completion rate

    def test_habit_analytics_query_efficiency(self):
        # Test that get_habit_analytics uses efficient queries
        # Create some test habits with completions
        habits = []
        for i in range(3):
            habit = Habit.objects.create(
                user=self.user, name=f"Test Habit {i}", frequency="daily"
            )
            habits.append(habit)

            # Add some completions
            for j in range(5):  # 5 completions per habit
                HabitCompletion.objects.create(
                    habit=habit,
                    completed_at=timezone.localtime(timezone.now()).date()
                    - timedelta(days=j),
                )

        # Test query efficiency
        with CaptureQueriesContext(connection) as context:
            from social.views import get_habit_analytics

            analytics = get_habit_analytics(Habit.objects.filter(user=self.user))
            # Should only need a few queries to get all the data
            self.assertLess(len(context.captured_queries), 5)

    def tearDown(self):
        self.patcher.stop()

    def test_streak_analytics(self):
        # Test streak calculations in analytics
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
