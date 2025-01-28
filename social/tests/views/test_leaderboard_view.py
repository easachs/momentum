from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from tracker.models import Habit

class TestLeaderboardView(TestCase):
    def setUp(self):
        self.user1 = get_user_model().objects.create_user(
            username="user1", email="user1@example.com", password="testpass123"
        )
        self.user2 = get_user_model().objects.create_user(
            username="user2", email="user2@example.com", password="testpass123"
        )
        self.client.force_login(self.user1)

    def test_leaderboard_view(self):
        # Create some habits and completions for testing
        habit = Habit.objects.create(
            user=self.user1, name="Test Habit", frequency="daily", category="health"
        )
        habit.toggle_completion()  # Complete the habit

        response = self.client.get(reverse("social:leaderboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user1.username)

    def test_leaderboard_category_filter(self):
        # Create and complete a health habit
        habit = Habit.objects.create(
            user=self.user1, name="Test Habit", frequency="daily", category="health"
        )
        habit.toggle_completion()

        # Check health category - should see user with completed habit
        response = self.client.get(reverse("social:leaderboard") + "?category=health")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user1.username)

        # Create learning habit but don't complete it
        Habit.objects.create(
            user=self.user1,
            name="Learning Habit",
            frequency="daily",
            category="learning",
        )

        # Check learning category - should still see user because they have a habit
        response = self.client.get(reverse("social:leaderboard") + "?category=learning")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user1.username)

    def test_leaderboard_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("social:leaderboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)
