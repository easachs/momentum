from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from jobhunt.models import Application

class TestApplicationCreateView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_create_view(self):
        response = self.client.post(
            reverse("jobhunt:application_create"),
            {
                "company": "New Company",
                "title": "New Position",
                "status": "wishlist",
                "due": "2024-12-31",
                "notes": "Test notes",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Application.objects.filter(title="New Position").exists())
