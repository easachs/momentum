from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from applications.models import Application

class TestApplicationListView(TestCase):
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

    def test_application_list_view(self):
        response = self.client.get(reverse("applications:application_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applications/application_list.html")
        self.assertContains(response, "Test Company")

    def test_application_list_view_filtering(self):
        # Create applications with different statuses
        Application.objects.create(
            user=self.user, company="Company A", title="Position A", status="wishlist"
        )

        # Test filtering by status
        response = self.client.get(
            reverse("applications:application_list") + "?status=wishlist"
        )
        self.assertEqual(len(response.context["applications"]), 1)
        self.assertContains(response, "Company A")
        self.assertNotContains(response, "Test Company")

    def test_application_list_view_sorting(self):
        Application.objects.create(
            user=self.user,
            company="Company A",
            title="Position A",
            status="wishlist",
            due=date(2024, 1, 1),
        )

        # Test sorting by due date
        response = self.client.get(reverse("applications:application_list") + "?sort=due")
        applications = list(response.context["applications"])
        self.assertTrue(applications[0].due <= applications[1].due)

    def test_application_list_filtering_and_sorting(self):
        # Test application filtering and sorting
        # Create additional applications with different statuses and dates
        Application.objects.create(
            user=self.user,
            company="Company A",
            title="Position A",
            status="wishlist",
            due=date(2024, 1, 1),
        )
        Application.objects.create(
            user=self.user,
            company="Company B",
            title="Position B",
            status="rejected",
            due=date(2024, 6, 1),
        )

        # Test status filtering
        response = self.client.get(
            reverse("applications:application_list") + "?status=wishlist"
        )
        self.assertEqual(len(response.context["applications"]), 1)
        self.assertContains(response, "Company A")

        # Test sorting by due date
        response = self.client.get(reverse("applications:application_list"))
        applications = list(response.context["applications"])
        self.assertTrue(applications[0].due <= applications[1].due)

    def test_application_list_filtering_workflow(self):
        # Test the filtering and sorting workflow
        Application.objects.all().delete()
        # Create applications with different statuses

        [
            Application.objects.create(
                user=self.user,
                company=f"Company {i}",
                title=f"Position {i}",
                status=status,
                due=date(2024, i + 1, 1),
            )
            for i, status in enumerate(["wishlist", "applied", "interviewing"])
        ]

        # Test filtering by each status
        for status in ["wishlist", "applied", "interviewing"]:
            response = self.client.get(
                f"{reverse('applications:application_list')}?status={status}"
            )
            self.assertEqual(len(response.context["applications"]), 1)
            self.assertContains(
                response,
                f"Company {['wishlist', 'applied', 'interviewing'].index(status)}",
            )

        # Test different sort orders
        response = self.client.get(f"{reverse('applications:application_list')}?sort=due")
        apps = list(response.context["applications"])
        self.assertEqual(len(apps), 3)
        self.assertTrue(
            all(apps[i].due <= apps[i + 1].due for i in range(len(apps) - 1))
        )
