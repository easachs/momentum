from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.utils import timezone
from tracker.models import Habit, HabitCompletion

class TestHabitListView(TestCase):
    """Tests for the Habit List View"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")
        created_at = timezone.localtime(timezone.now())
        self.habit1 = Habit.objects.create(
            user=self.user,
            name="Health Habit",
            frequency="daily",
            category="health",
            created_at=created_at
        )
        self.habit2 = Habit.objects.create(
            user=self.user,
            name="Productivity Habit",
            frequency="daily",
            category="productivity",
            created_at=created_at
        )
        self.habit3 = Habit.objects.create(
            user=self.user,
            name="Learning Habit",
            frequency="daily",
            category="learning",
            created_at=created_at
        )

    def test_habit_list_view_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("tracker:habit_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_habit_list_view_shows_user_habits(self):
        response = self.client.get(reverse("tracker:habit_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Health Habit")
        self.assertContains(response, "Productivity Habit")
        self.assertContains(response, "Learning Habit")

    def test_habit_list_view_user_can_only_see_own_list(self):
        other_user = get_user_model().objects.create_user(
            username="otheruser", email="other@example.com", password="testpass123"
        )
        self.client.force_login(other_user)
        response = self.client.get(reverse("tracker:habit_list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Health Habit")
        self.assertNotContains(response, "Productivity Habit")
        self.assertNotContains(response, "Learning Habit")

    def test_habit_list_view_empty_for_new_user(self):
        new_user = get_user_model().objects.create_user(
            username="newuser", email="new@example.com", password="testpass123"
        )
        self.client.force_login(new_user)
        response = self.client.get(reverse("tracker:habit_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No habits yet")

    def test_habit_list_view_shows_completion_status(self):
        self.habit1.toggle_completion()
        response = self.client.get(reverse("tracker:habit_list"))
        self.assertContains(response, "bg-green-200 text-green-700")

    def test_habit_list_view_mode_switching(self):
        response = self.client.get(
            reverse('tracker:habit_list') + '?view=category'
        )
        self.assertEqual(response.status_code, 200)

    def test_habit_list_view_streak_calculation(self):
        today = timezone.now().date()
        for i in range(3):
            HabitCompletion.objects.create(
                habit=self.habit1, completed_at=today - timedelta(days=i)
            )

        response = self.client.get(reverse("tracker:habit_list"))
        self.assertContains(response, "Streak: 3")

    def test_habit_list_view_incomplete_habit_notifications(self):
        response = self.client.get(reverse("tracker:habit_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "incomplete")
        self.assertContains(response, "bg-yellow-50 border-l-4 border-yellow-400 p-4")

    def test_habit_list_query_count(self):
        """Test that habit list view uses efficient queries"""
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(reverse("tracker:habit_list"))
            self.assertEqual(response.status_code, 200)
            self.assertLess(len(context.captured_queries), 20)

    def test_habit_list_view_analytics_calculation(self):
        """Test that habit analytics are calculated correctly"""
        # First delete all habits
        Habit.objects.all().delete()

        today = timezone.localtime(timezone.now()).date()
        one_day_ago = today - timedelta(days=1)

        # Create test habits...
        health_habits = [
            Habit.objects.create(
                user=self.user,
                name=f"Daily Health {i}",
                category="health",
                frequency="daily",
                created_at=one_day_ago
            ) for i in range(4)
        ]

        # Create weekly habit today instead of yesterday
        weekly_habit = Habit.objects.create(
            user=self.user,
            name="Weekly Health",
            category="health",
            frequency="weekly",
            created_at=today,  # Changed from one_day_ago
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
                    habit=habit, completed_at=today - timedelta(days=days_ago)
                )

        # Third daily habit - complete only today
        HabitCompletion.objects.create(habit=health_habits[2], completed_at=today)

        # Fourth daily habit - no completions

        # Weekly habit - complete once
        HabitCompletion.objects.create(habit=weekly_habit, completed_at=today)

        # Get analytics through the view
        response = self.client.get(reverse("tracker:habit_list"))
        analytics = response.context["habit_analytics"]
        
        health_stats = next(
            stat for stat in analytics["category_stats"] if stat["category"] == "health"
        )

        # Expected values:
        # - Total possible: 8 daily (4 habits × 2 days) + 1 weekly = 9
        # - Total completed: 4 (two habits × 2 days) + 1 (one habit × 1 day) + 1 weekly = 6
        # - Completion rate: 6/9 ≈ 66.7%

        self.assertEqual(health_stats["total"], 9)
        self.assertEqual(health_stats["completed"], 6)
        self.assertAlmostEqual(health_stats["percentage"], 66.7, places=1)

    def test_habit_list_view_category_performance_stats(self):
        # Complete one habit
        self.habit1.toggle_completion()

        response = self.client.get(reverse("tracker:habit_list"))
        category_stats = {
            stat["category"]: stat
            for stat in response.context["analytics"]["category_stats"]
        }

        # Check health category stats (now we have 4 health habits, one completed)
        self.assertEqual(category_stats["health"]["completed"], 1)
        self.assertEqual(category_stats["health"]["total"], 1)

        # Check learning category stats
        self.assertEqual(category_stats["learning"]["completed"], 0)
        self.assertEqual(category_stats["learning"]["total"], 1)

    def test_habit_list_view_analytics_with_mixed_frequencies(self):
        """Test analytics calculations with mix of daily/weekly habits"""
        Habit.objects.all().delete()

        now = timezone.localtime(timezone.now())
        today = now.date()

        daily_habit = Habit.objects.create(
            user=self.user, 
            name="Daily Analytics Test", 
            frequency="daily",
            created_at=now
        )
        weekly_habit = Habit.objects.create(
            user=self.user, 
            name="Weekly Analytics Test", 
            frequency="weekly",
            created_at=now
        )

        # Complete both habits for today
        HabitCompletion.objects.create(habit=daily_habit, completed_at=today)
        HabitCompletion.objects.create(habit=weekly_habit, completed_at=today)

        response = self.client.get(reverse("tracker:habit_list"))
        analytics = response.context["analytics"]

        self.assertEqual(analytics["this_week_completions"], 2)
        self.assertAlmostEqual(analytics["completion_rate"], 100.0, places=1)

    def test_habit_list_view_analytics_across_categories(self):
        """Test analytics calculations across different categories"""
        categories = ["health", "learning", "productivity"]
        habits_per_category = {}

        today = timezone.now().date()
        # Create a habit in each category
        for category in categories:
            habit = Habit.objects.create(
                user=self.user,
                name=f"{category.title()} Test Habit",
                frequency="daily",
                category=category,
            )
            habits_per_category[category] = habit
            # Complete the health and learning habits
            if category in ["health", "learning"]:
                HabitCompletion.objects.create(habit=habit, completed_at=today)

        response = self.client.get(reverse("tracker:habit_list"))
        category_stats = {
            stat["category"]: stat
            for stat in response.context["analytics"]["category_stats"]
        }

        # Check each category's stats
        self.assertEqual(category_stats["health"]["completed"], 1)
        self.assertEqual(category_stats["learning"]["completed"], 1)
        self.assertEqual(category_stats["productivity"]["completed"], 0)

        # Check overall completion rate (2 out of 6 possible for daily habits)
        self.assertAlmostEqual(
            response.context["analytics"]["completion_rate"], 33.3, places=1
        )

    def test_habit_list_view_analytics_with_deleted_habits(self):
        """Test habit analytics handle deleted habits correctly"""
        habit = Habit.objects.create(
            user=self.user, name="To Delete Habit", frequency="daily"
        )

        # Add some completions
        HabitCompletion.objects.create(habit=habit, completed_at=timezone.now().date())

        # Get analytics before deletion
        response = self.client.get(reverse("tracker:habit_list"))
        completions_before = response.context["analytics"]["total_completions"]
        habit.delete()

        # Check analytics after deletion
        response = self.client.get(reverse("tracker:habit_list"))
        completions_after = response.context["analytics"]["total_completions"]

        # Completions should be reduced
        self.assertEqual(completions_after, completions_before - 1)
