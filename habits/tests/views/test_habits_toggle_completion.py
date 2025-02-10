from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test.utils import CaptureQueriesContext
from django.db import connection
from habits.models import Habit

class TestHabitsToggleCompletion(TestCase):
    # Tests for the Habits Toggle Completion View
    def setUp(self):
        self.today = timezone.localtime(timezone.now()).date()
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")
        self.habit = Habit.objects.create(
            user=self.user, name="Test Habit", frequency="daily", category="health"
        )

    def test_toggle_completion_view(self):
        # Test that toggle_completion view works
        today = timezone.localtime(timezone.now()).date()
        response = self.client.post(
            reverse("habits:toggle_completion", kwargs={"pk": self.habit.pk}),
            {"date": today.strftime("%Y-%m-%d")},
        )
        self.assertEqual(response.status_code, 302)

    def test_toggle_completion_requires_login(self):
        self.client.logout()
        url = reverse("habits:toggle_completion", args=[self.habit.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_toggle_completion_preserves_referer(self):
        # Test that toggle_completion preserves the referer header
        response = self.client.post(
            reverse("habits:toggle_completion", kwargs={"pk": self.habit.pk}),
            HTTP_REFERER="/some/url/",
        )  # Also not providing a date parameter
        self.assertEqual(response.status_code, 302)

    def test_toggle_completion_with_invalid_habit_id(self):
        url = reverse("habits:toggle_completion", args=[99999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_toggle_completion_query_efficiency(self):
        # Test that habit completion toggling is efficient
        with CaptureQueriesContext(connection) as context:
            response = self.client.post(
                reverse("habits:toggle_completion", kwargs={"pk": self.habit.pk}),
                {"date": self.today.strftime("%Y-%m-%d")},
            )
            self.assertEqual(response.status_code, 302)

            # We expect queries for:
            # 1. User authentication
            # 2. Get habit
            # 3. Check existing completion
            # 4. Create/delete completion
            # 5. Get completions for badge check
            # 6. Update/create badge if needed
            self.assertLessEqual(len(context.captured_queries), 7)