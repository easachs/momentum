from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from jobhunt.models import Application

class TestApplicationDeleteView(TestCase):
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

    def test_delete_view(self):
        response = self.client.post(
            reverse("jobhunt:application_delete", kwargs={"pk": self.application.pk}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Application.objects.filter(pk=self.application.pk).exists())
