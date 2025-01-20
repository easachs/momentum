from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, date
from jobhunt.models import Application, StatusChange

class ApplicationModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.application = Application.objects.create(
            user=self.user,
            company='Test Company',
            title='Test Position',
            status='wishlist',
            due=date(2024, 12, 31)
        )

    def test_string_representation(self):
        """Test Application model methods"""
        self.assertEqual(
            str(self.application),
            'Test Position at Test Company'
        )

    def test_is_due_soon(self):
        # Test not due soon
        self.application.due = timezone.now().date() + timedelta(days=10)
        self.assertFalse(self.application.is_due_soon())

        # Test due soon
        self.application.due = timezone.now().date() + timedelta(days=5)
        self.assertTrue(self.application.is_due_soon())

        # Test no due date
        self.application.due = None
        self.assertFalse(self.application.is_due_soon())

    def test_status_change_creation(self):
        # Initially no status changes for wishlist
        self.assertEqual(self.application.status_changes.count(), 0)
        
        # Update to applied
        self.application.status = 'applied'
        self.application.save()
        
        initial_status_change = self.application.status_changes.last()
        self.assertEqual(initial_status_change.old_status, 'wishlist')
        self.assertEqual(initial_status_change.new_status, 'applied')

        # Test status update
        self.application.status = 'interviewing'
        self.application.save()
        
        status_changes = self.application.status_changes.all()
        self.assertEqual(status_changes.count(), 2)  # Initial + update
        latest_change = status_changes.latest('changed_at')
        self.assertEqual(latest_change.old_status, 'applied')
        self.assertEqual(latest_change.new_status, 'interviewing')

class StatusChangeModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.application = Application.objects.create(
            user=self.user,
            company='Test Company',
            title='Test Position',
            status='applied'
        )

    def test_string_representation(self):
        status_change = StatusChange.objects.create(
            application=self.application,
            old_status='applied',
            new_status='interviewing'
        )
        self.assertEqual(
            str(status_change),
            f"{self.application}: applied → interviewing"
        )

    def test_ordering(self):
        StatusChange.objects.create(
            application=self.application,
            old_status='applied',
            new_status='interviewing'
        )
        StatusChange.objects.create(
            application=self.application,
            old_status='interviewing',
            new_status='offered'
        )
        
        status_changes = self.application.status_changes.all()
        self.assertTrue(
            status_changes[0].changed_at <= status_changes[1].changed_at
        ) 