from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from applications.models import Application

class ApplicationIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_application_lifecycle(self):
        # Test the complete lifecycle of an application
        # Create application
        response = self.client.post(
            reverse('applications:application_create'),
            {
                'company': 'Lifecycle Company',
                'title': 'Lifecycle Position',
                'status': 'wishlist',
                'due': '2024-12-31',
                'notes': 'Initial application'
            }
        )
        self.assertEqual(response.status_code, 302)

        # Get the created application
        application = Application.objects.get(title='Lifecycle Position')

        # No status change should be created for initial wishlist status
        self.assertEqual(application.status_changes.count(), 0)

        # Update status to applied
        response = self.client.post(
            reverse('applications:application_update', kwargs={'pk': application.pk}),
            {
                'company': 'Lifecycle Company',
                'title': 'Lifecycle Position',
                'status': 'applied',
                'due': '2024-12-31',
                'notes': 'Updated to applied'
            }
        )
        self.assertEqual(response.status_code, 302)

        # Verify status change was recorded
        application.refresh_from_db()
        latest_status = application.status_changes.latest('changed_at')
        self.assertEqual(latest_status.old_status, 'wishlist')
        self.assertEqual(latest_status.new_status, 'applied')

        # Delete application
        response = self.client.post(
            reverse('applications:application_delete', kwargs={'pk': application.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Application.objects.filter(pk=application.pk).exists()
        )
