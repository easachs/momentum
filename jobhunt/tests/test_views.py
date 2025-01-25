from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from jobhunt.models import Application

class ApplicationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        self.application = Application.objects.create(
            user=self.user,
            company='Test Company',
            title='Test Position',
            status='applied',
            due=date(2024, 12, 31)
        )

    def test_list_view(self):
        response = self.client.get(reverse('jobhunt:application_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobhunt/application_list.html')
        self.assertContains(response, 'Test Company')

    def test_list_view_filtering(self):
        # Create applications with different statuses
        Application.objects.create(
            user=self.user,
            company='Company A',
            title='Position A',
            status='wishlist'
        )

        # Test filtering by status
        response = self.client.get(reverse('jobhunt:application_list') + '?status=wishlist')
        self.assertEqual(len(response.context['applications']), 1)
        self.assertContains(response, 'Company A')
        self.assertNotContains(response, 'Test Company')

    def test_list_view_sorting(self):
        Application.objects.create(
            user=self.user,
            company='Company A',
            title='Position A',
            status='wishlist',
            due=date(2024, 1, 1)
        )

        # Test sorting by due date
        response = self.client.get(reverse('jobhunt:application_list') + '?sort=due')
        applications = list(response.context['applications'])
        self.assertTrue(
            applications[0].due <= applications[1].due
        )

    def test_detail_view(self):
        response = self.client.get(
            reverse('jobhunt:application_detail', kwargs={'pk': self.application.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobhunt/application_detail.html')
        self.assertContains(response, 'Test Position')
        self.assertContains(response, 'Test Company')

    def test_create_view(self):
        response = self.client.post(
            reverse('jobhunt:application_create'),
            {
                'company': 'New Company',
                'title': 'New Position',
                'status': 'wishlist',
                'due': '2024-12-31',
                'notes': 'Test notes'
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Application.objects.filter(title='New Position').exists()
        )

    def test_update_view(self):
        response = self.client.post(
            reverse('jobhunt:application_update', kwargs={'pk': self.application.pk}),
            {
                'company': 'Updated Company',
                'title': 'Updated Position',
                'status': 'interviewing',
                'due': '2024-12-31',
                'notes': 'Updated notes'
            }
        )
        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.company, 'Updated Company')
        self.assertEqual(self.application.status, 'interviewing')

    def test_filtering_and_sorting(self):
        """Test application filtering and sorting"""
        # Create additional applications with different statuses and dates
        Application.objects.create(
            user=self.user,
            company='Company A',
            title='Position A',
            status='wishlist',
            due=date(2024, 1, 1)
        )
        Application.objects.create(
            user=self.user,
            company='Company B',
            title='Position B',
            status='rejected',
            due=date(2024, 6, 1)
        )

        # Test status filtering
        response = self.client.get(reverse('jobhunt:application_list') + '?status=wishlist')
        self.assertEqual(len(response.context['applications']), 1)
        self.assertContains(response, 'Company A')

        # Test sorting by due date
        response = self.client.get(reverse('jobhunt:application_list'))
        applications = list(response.context['applications'])
        self.assertTrue(
            applications[0].due <= applications[1].due
        )
