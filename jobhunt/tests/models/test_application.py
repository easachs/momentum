from datetime import timedelta, date
from unittest import mock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from jobhunt.models import Application, StatusChange

class ApplicationModelTests(TestCase):
    def setUp(self):
        # Set up timezone mock
        fixed_date = timezone.datetime(2024, 1, 1).astimezone(timezone.get_current_timezone())
        self.patcher = mock.patch('django.utils.timezone.now')
        self.mock_now = self.patcher.start()
        self.mock_now.return_value = fixed_date

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

    def tearDown(self):
        self.patcher.stop()

    def test_string_representation(self):
        # Test Application model methods
        self.assertEqual(
            str(self.application),
            'Test Position at Test Company'
        )

    def test_is_due_soon(self):
        # Test not due soon
        self.application.due = timezone.localtime(timezone.now()).date() + timedelta(
            days=10
        )
        self.assertFalse(self.application.is_due_soon())

        # Test due soon
        self.application.due = timezone.localtime(timezone.now()).date() + timedelta(
            days=5
        )
        self.assertTrue(self.application.is_due_soon())

        # Test no due date
        self.application.due = None
        self.assertFalse(self.application.is_due_soon())

    def test_status_change_creation(self):
        # Test that status changes are tracked correctly
        # Initially no status changes for wishlist
        self.assertEqual(self.application.status_changes.count(), 0)

        # Update to applied
        self.application.status = 'applied'
        self.application.save()

        # Should have one status change
        self.assertEqual(self.application.status_changes.count(), 1)
        status_change = self.application.status_changes.first()
        self.assertEqual(status_change.old_status, 'wishlist')
        self.assertEqual(status_change.new_status, 'applied')

        # Test status update
        self.application.status = 'interviewing'
        self.application.save()

        status_changes = self.application.status_changes.order_by('changed_at')
        self.assertEqual(status_changes.count(), 2)  # Initial + update

        # Get the second (latest) change
        latest_change = status_changes[1]
        self.assertEqual(latest_change.old_status, 'applied')
        self.assertEqual(latest_change.new_status, 'interviewing')

    def test_analytics_calculation(self):
        # Test that application analytics are calculated correctly
        # Create applications with different dates and statuses
        dates = [
            self.mock_now.return_value,
            self.mock_now.return_value - timedelta(days=3),
            self.mock_now.return_value - timedelta(days=10),
            self.mock_now.return_value - timedelta(days=20),
            self.mock_now.return_value - timedelta(days=40)
        ]

        statuses = ['wishlist', 'applied', 'offered', 'offered', 'rejected']

        # Create the test applications (excluding the one created in setUp)
        for date, status in zip(dates, statuses):
            self.mock_now.return_value = date
            Application.objects.create(
                user=self.user,
                company=f'Company {date}',
                title=f'Position {date}',
                status=status,
            )
        
        # Reset mock time back to original for analytics calculation
        self.mock_now.return_value = timezone.datetime.combine(
            self.mock_now.return_value.date(),
            timezone.datetime.min.time()
        )

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

    def test_status_change_history(self):
        # Test the status change history functionality
        # Create application with wishlist status (no status change created)
        application = Application.objects.create(
            user=self.user,
            company="History Company",
            title="History Position",
            status="wishlist",
        )

        status_sequence = ["applied", "interviewing", "offered"]
        for status in status_sequence:
            application.status = status
            application.save()

        # Verify status history
        changes = application.status_changes.all()
        self.assertEqual(
            len(changes), len(status_sequence)
        )  # No change for initial wishlist

        # Verify order of changes
        statuses = ["wishlist"] + status_sequence[:-1]  # old statuses
        new_statuses = status_sequence  # new statuses
        for i in range(len(changes)):
            self.assertEqual(changes[i].old_status, statuses[i])
            self.assertEqual(changes[i].new_status, new_statuses[i])

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

    def test_status_change_history(self):
        # Test the status change history functionality
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
