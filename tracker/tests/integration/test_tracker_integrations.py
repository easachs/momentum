from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from tracker.models import Habit
class TestTrackerIntegrations(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client.force_login(self.user)
        self.habit = Habit.objects.create(
            name="Test Habit",
            user=self.user,
            frequency="daily",
            description=""
        )

    def test_redirect_after_create(self):
        response = self.client.post(
            reverse('tracker:habit_create'),
            {'name': 'New Habit', 'frequency': 'daily', 'category': 'health'}
        )
        self.assertRedirects(
            response,
            reverse('tracker:habit_list')
        )
