from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from tracker.models import Habit, HabitCompletion

class TestHabitViews(TestCase):
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
            frequency='daily',
            description=''  # Add empty string for description
        )

    def test_habit_create_view(self):
        url = reverse('tracker:habit_create')
        data = {
            'name': 'Read Books',
            'description': 'Read for 30 minutes',
            'frequency': 'daily',
            'category': 'learning'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Habit.objects.filter(name='Read Books').exists())

    def test_habit_update_view(self):
        url = reverse('tracker:habit_update', args=[self.habit.pk])
        data = {
            'name': 'Exercise Updated',
            'description': '',  # Add empty string for description
            'frequency': self.habit.frequency,
            'category': 'health'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.habit.refresh_from_db()
        self.assertEqual(self.habit.name, 'Exercise Updated')

    def test_habit_delete_view(self):
        url = reverse('tracker:habit_delete', args=[self.habit.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Habit.objects.filter(pk=self.habit.pk).exists())

    def test_cannot_update_other_users_habit(self):
        other_user = get_user_model().objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='testpass123'
        )
        self.client.force_login(other_user)
        
        url = reverse('tracker:habit_update', args=[self.habit.pk])
        data = {
            'name': 'Hacked Exercise',
            'description': '',  # Add empty string for description
            'frequency': self.habit.frequency,
            'category': 'health'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 404)
        self.habit.refresh_from_db()
        self.assertEqual(self.habit.name, 'Test Habit')

    def test_cannot_delete_other_users_habit(self):
        other_user = get_user_model().objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='testpass123'
        )
        self.client.force_login(other_user)
        
        url = reverse('tracker:habit_delete', args=[self.habit.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Habit.objects.filter(pk=self.habit.pk).exists())

    def test_toggle_completion_view(self):
        url = reverse('tracker:habit_completion_toggle', args=[self.habit.pk])
        
        # Initially not completed
        self.assertFalse(self.habit.is_completed_for_date())
        
        # Toggle to completed
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.habit.refresh_from_db()
        self.assertTrue(self.habit.is_completed_for_date())
        
        # Toggle back to not completed
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.habit.refresh_from_db()
        self.assertFalse(self.habit.is_completed_for_date())

    def test_toggle_completion_requires_login(self):
        self.client.logout()
        url = reverse('tracker:habit_completion_toggle', args=[self.habit.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_toggle_completion_with_invalid_habit_id(self):
        url = reverse('tracker:habit_completion_toggle', args=[99999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_habit_list_view_requires_login(self):
        self.client.logout()  # Make sure to log out first
        response = self.client.get(reverse('tracker:habit_list', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_habit_list_view_shows_user_habits(self):
        response = self.client.get(reverse('tracker:habit_list', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Habit')

    def test_user_can_only_see_own_habits(self):
        other_user = get_user_model().objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        self.client.force_login(other_user)
        response = self.client.get(reverse('tracker:habit_list', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Test Habit')

    def test_habit_create_view_invalid_data(self):
        url = reverse('tracker:habit_create')
        data = {
            'name': 'Ab',  # Too short
            'frequency': 'invalid',
            'category': 'invalid'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)  # Returns to form with errors
        self.assertFalse(Habit.objects.filter(name='Ab').exists())

    def test_habit_update_view_invalid_data(self):
        url = reverse('tracker:habit_update', args=[self.habit.pk])
        data = {
            'name': 'Ab',  # Too short
            'frequency': 'invalid',
            'category': 'invalid'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)  # Returns to form with errors
        self.habit.refresh_from_db()
        self.assertEqual(self.habit.name, 'Test Habit')  # Name unchanged

    def test_habit_list_empty_for_new_user(self):
        new_user = get_user_model().objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )
        self.client.force_login(new_user)
        response = self.client.get(reverse('tracker:habit_list', kwargs={'username': new_user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No habits yet')

    def test_habit_detail_view(self):
        response = self.client.get(
            reverse('tracker:habit_detail', 
                   kwargs={'username': self.user.username, 'pk': self.habit.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Habit')

    def test_redirect_after_create(self):
        response = self.client.post(
            reverse('tracker:habit_create'),
            {
                'name': 'New Habit',
                'frequency': 'daily',
                'category': 'health'
            }
        )
        self.assertRedirects(
            response, 
            reverse('tracker:habit_list', kwargs={'username': self.user.username})
        )

    def test_unauthenticated_user_redirected_to_login(self):
        self.client.logout()  # Make sure to log out first
        response = self.client.get(reverse('tracker:habit_list', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_toggle_completion_preserves_referer(self):
        referer = reverse('tracker:habit_list', kwargs={'username': self.user.username})
        response = self.client.post(
            reverse('tracker:habit_completion_toggle', kwargs={'pk': self.habit.pk}),
            HTTP_REFERER=referer
        )
        self.assertRedirects(response, referer)

    def test_habit_list_shows_completion_status(self):
        self.habit.toggle_completion()
        response = self.client.get(
            reverse('tracker:habit_list', kwargs={'username': self.user.username})
        )
        self.assertContains(response, 'bg-green-200 text-green-700')

    def test_habit_detail_shows_completion_status(self):
        self.habit.toggle_completion()
        response = self.client.get(
            reverse('tracker:habit_detail', 
                   kwargs={'username': self.user.username, 'pk': self.habit.pk})
        )
        self.assertContains(response, 'bg-green-200 text-green-700')

    def test_view_mode_switching(self):
        response = self.client.get(
            reverse('tracker:habit_list', kwargs={'username': self.user.username}) + '?view=category'
        )
        self.assertEqual(response.status_code, 200)

    def test_streak_calculation(self):
        today = timezone.now().date()
        
        # Create completions for the last 3 days
        for i in range(3):
            HabitCompletion.objects.create(
                habit=self.habit,
                completed_at=today - timedelta(days=i)
            )
        
        response = self.client.get(reverse('tracker:habit_list', kwargs={'username': self.user.username}))
        self.assertContains(response, 'Streak: 3') 