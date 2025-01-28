from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

class TestHabitIntegration(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_generate_ai_summary(self):
        # Test AI summary generation endpoint
        response = self.client.post(reverse('tracker:generate_ai_summary'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('content' in response.json())
