from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from jobhunt.models import Application, StatusChange
from datetime import date

class ApplicationIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_application_lifecycle(self):
        """Test the complete lifecycle of an application"""
        # Create application
        response = self.client.post(
            reverse('jobhunt:application_create'),
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
            reverse('jobhunt:application_update', kwargs={'pk': application.pk}),
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
            reverse('jobhunt:application_delete', kwargs={'pk': application.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Application.objects.filter(pk=application.pk).exists()
        )

    def test_filtering_workflow(self):
        """Test the filtering and sorting workflow"""
        # Create applications with different statuses
        applications = [
            Application.objects.create(
                user=self.user,
                company=f'Company {i}',
                title=f'Position {i}',
                status=status,
                due=date(2024, i+1, 1)
            ) for i, status in enumerate(['wishlist', 'applied', 'interviewing'])
        ]
        
        # Test filtering by each status
        for status in ['wishlist', 'applied', 'interviewing']:
            response = self.client.get(f"{reverse('jobhunt:application_list')}?status={status}")
            self.assertEqual(len(response.context['applications']), 1)
            self.assertContains(response, f'Company {["wishlist", "applied", "interviewing"].index(status)}')
        
        # Test different sort orders
        response = self.client.get(f"{reverse('jobhunt:application_list')}?sort=due")
        apps = list(response.context['applications'])
        self.assertEqual(len(apps), 3)
        self.assertTrue(all(apps[i].due <= apps[i+1].due for i in range(len(apps)-1)))

    def test_status_change_history(self):
        """Test the status change history functionality"""
        # Create application with wishlist status (no status change created)
        application = Application.objects.create(
            user=self.user,
            company='History Company',
            title='History Position',
            status='wishlist'
        )
        
        status_sequence = ['applied', 'interviewing', 'offered']
        for status in status_sequence:
            application.status = status
            application.save()
        
        # Verify status history
        changes = application.status_changes.all()
        self.assertEqual(len(changes), len(status_sequence))  # No change for initial wishlist
        
        # Verify order of changes
        statuses = ['wishlist'] + status_sequence[:-1]  # old statuses
        new_statuses = status_sequence  # new statuses
        for i in range(len(changes)):
            self.assertEqual(changes[i].old_status, statuses[i])
            self.assertEqual(changes[i].new_status, new_statuses[i]) 