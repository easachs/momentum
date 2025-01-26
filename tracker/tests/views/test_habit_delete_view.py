from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from tracker.models import Habit

class TestHabitDeleteView(TestCase):
    """Tests for the Habit Delete View"""

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

    def test_habit_delete_view(self):
        url = reverse("tracker:habit_delete", args=[self.habit.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Habit.objects.filter(pk=self.habit.pk).exists())

    def test_habit_delete_view_cannot_delete_other_users_habit(self):
        other_user = get_user_model().objects.create_user(
            email="other@example.com", username="otheruser", password="testpass123"
        )
        self.client.force_login(other_user)

        url = reverse("tracker:habit_delete", args=[self.habit.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Habit.objects.filter(pk=self.habit.pk).exists())
