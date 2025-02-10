from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from habits.models import Habit

class TestHabitCreateView(TestCase):
    # Tests for the Habit Create View
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_habit_create_view(self):
        url = reverse("habits:habit_create")
        data = {
            "name": "Read Books",
            "description": "Read for 30 minutes",
            "frequency": "daily",
            "category": "learning",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Habit.objects.filter(name="Read Books").exists())

    def test_habit_create_view_invalid_data(self):
        url = reverse("habits:habit_create")
        data = {
            "name": "Ab",  # Too short
            "frequency": "invalid",
            "category": "invalid",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)  # Returns to form with errors
        self.assertFalse(Habit.objects.filter(name="Ab").exists())
