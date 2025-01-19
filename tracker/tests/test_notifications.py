from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from tracker.models import Habit
from django.utils import timezone

class TestHabitNotifications(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_login(self.user)
        self.habit = Habit.objects.create(
            name='Test Habit',
            user=self.user,
            frequency='daily'
        )

    def test_incomplete_habit_notifications(self):
        response = self.client.get(reverse('tracker:habit_list', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'incomplete')

    def test_notification_display(self):
        response = self.client.get(reverse('tracker:habit_list', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Not Done') 