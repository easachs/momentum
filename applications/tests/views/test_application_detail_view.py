from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from applications.models import Application

class TestApplicationDetailView(TestCase):
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

    def test_detail_view(self):
        response = self.client.get(
            reverse("applications:application_detail", kwargs={"pk": self.application.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applications/application_detail.html")
        self.assertContains(response, "Test Position")
        self.assertContains(response, "Test Company")