from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from social.models import Friendship
from tracker.models import Habit, HabitCompletion
from django.utils import timezone
from datetime import timedelta

class TestSocialViews(TestCase):
    def setUp(self):
        self.user1 = get_user_model().objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = get_user_model().objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.user3 = get_user_model().objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )
        self.client.force_login(self.user1)

    def test_send_friend_request(self):
        response = self.client.get(
            reverse('social:send_friend_request', kwargs={'username': self.user2.username})
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Friendship.objects.filter(
                sender=self.user1,
                receiver=self.user2,
                status='pending'
            ).exists()
        )

    def test_handle_friend_request_accept(self):
        friendship = Friendship.objects.create(
            sender=self.user2,
            receiver=self.user1,
            status='pending'
        )
        response = self.client.get(
            reverse('social:handle_friend_request', 
                   kwargs={'friendship_id': friendship.id, 'action': 'accept'})
        )
        self.assertEqual(response.status_code, 302)
        friendship.refresh_from_db()
        self.assertEqual(friendship.status, 'accepted')

    def test_handle_friend_request_decline(self):
        friendship = Friendship.objects.create(
            sender=self.user2,
            receiver=self.user1,
            status='pending'
        )
        response = self.client.get(
            reverse('social:handle_friend_request', 
                   kwargs={'friendship_id': friendship.id, 'action': 'decline'})
        )
        self.assertEqual(response.status_code, 302)
        friendship.refresh_from_db()
        self.assertEqual(friendship.status, 'declined')

    def test_friends_list_view(self):
        Friendship.objects.create(
            sender=self.user1,
            receiver=self.user2,
            status='accepted'
        )
        response = self.client.get(reverse('social:friends_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user2.username)

    def test_leaderboard_view(self):
        # Create some habits and completions for testing
        habit = Habit.objects.create(
            user=self.user1,
            name="Test Habit",
            frequency="daily",
            category="health"
        )
        habit.toggle_completion()  # Complete the habit

        response = self.client.get(reverse('social:leaderboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user1.username)

    def test_leaderboard_category_filter(self):
        # Create and complete a health habit
        habit = Habit.objects.create(
            user=self.user1,
            name="Test Habit",
            frequency="daily",
            category="health"
        )
        habit.toggle_completion()

        # Check health category - should see user with completed habit
        response = self.client.get(reverse('social:leaderboard') + '?category=health')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user1.username)

        # Create learning habit but don't complete it
        learning_habit = Habit.objects.create(
            user=self.user1,
            name="Learning Habit",
            frequency="daily",
            category="learning"
        )

        # Check learning category - should still see user because they have a habit
        response = self.client.get(reverse('social:leaderboard') + '?category=learning')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user1.username)

    def test_cannot_send_friend_request_to_self(self):
        response = self.client.get(
            reverse('social:send_friend_request', kwargs={'username': self.user1.username})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Friendship.objects.filter(
                sender=self.user1,
                receiver=self.user1
            ).exists()
        )

    def test_cannot_handle_other_users_friend_request(self):
        friendship = Friendship.objects.create(
            sender=self.user2,
            receiver=self.user3,  # Not self.user1
            status='pending'
        )
        
        response = self.client.get(
            reverse('social:handle_friend_request', 
                   kwargs={'friendship_id': friendship.id, 'action': 'accept'})
        )
        self.assertEqual(response.status_code, 302)  # Redirects with error message
        self.assertRedirects(response, reverse('tracker:dashboard', kwargs={'username': self.user1.username}))

    def test_leaderboard_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('social:leaderboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_friends_list_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('social:friends_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url) 