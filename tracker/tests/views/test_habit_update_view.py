from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from tracker.models import Habit

class TestHabitUpdateView(TestCase):
    # Tests for the Habit Update View
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")
        self.habit = Habit.objects.create(
            user=self.user,
            name="Test Habit",
            frequency="daily",
            category="health"
        )

    def test_habit_update_view(self):
        url = reverse("tracker:habit_update", args=[self.habit.pk])
        data = {
            "name": "Exercise Updated",
            "description": "",  # Add empty string for description
            "frequency": self.habit.frequency,
            "category": "health",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.habit.refresh_from_db()
        self.assertEqual(self.habit.name, "Exercise Updated")

    def test_habit_update_view_invalid_data(self):
        url = reverse("tracker:habit_update", args=[self.habit.pk])
        data = {
            "name": "Ab",  # Too short
            "frequency": "invalid",
            "category": "invalid",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)  # Returns to form with errors
        self.habit.refresh_from_db()
        self.assertEqual(self.habit.name, "Test Habit")  # Name unchanged

    def test_habit_update_view_cannot_update_other_users_habit(self):
        other_user = get_user_model().objects.create_user(
            email="other@example.com", username="otheruser", password="testpass123"
        )
        self.client.force_login(other_user)

        url = reverse("tracker:habit_update", args=[self.habit.pk])
        data = {
            "name": "Hacked Exercise",
            "description": "",  # Add empty string for description
            "frequency": self.habit.frequency,
            "category": "health",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 404)
        self.habit.refresh_from_db()
        self.assertEqual(self.habit.name, "Test Habit")

    def test_get_method_requires_login(self):
        """Test that GET requests require login"""
        self.client.logout()
        response = self.client.get(
            reverse('tracker:habit_update', kwargs={'pk': self.habit.pk})
        )
        self.assertEqual(response.status_code, 302)  # Redirects to login
