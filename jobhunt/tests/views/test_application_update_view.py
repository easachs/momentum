from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from jobhunt.models import Application

class TestApplicationUpdateView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

        self.application = Application.objects.create(
            user=self.user,
            company="Test Company",
            title="Test Position",
            status="applied",
            due=date(2024, 12, 31),
        )

    def test_update_view(self):
        response = self.client.post(
            reverse("jobhunt:application_update", kwargs={"pk": self.application.pk}),
            {
                "company": "Updated Company",
                "title": "Updated Position",
                "status": "interviewing",
                "due": "2024-12-31",
                "notes": "Updated notes",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.company, "Updated Company")
        self.assertEqual(self.application.status, "interviewing")
