from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from social.models import Friendship

class TestUnfriendView(TestCase):
    # Tests for the Unfriend View
    def setUp(self):
        # Set up two users and create a friendship between them
        self.user1 = get_user_model().objects.create_user(
            username='testuser1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = get_user_model().objects.create_user(
            username='testuser2',
            email='user2@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser1', password='testpass123')

        # Create friendship
        self.friendship = Friendship.objects.create(
            sender=self.user1,
            receiver=self.user2,
            status='accepted'
        )

    def test_unfriend_view_requires_login(self):
        # Test that unfriend view requires login
        self.client.logout()
        response = self.client.post(
            reverse('social:unfriend', kwargs={'friendship_id': self.friendship.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_unfriend_success(self):
        # Test successful unfriending
        response = self.client.post(
            reverse('social:unfriend', kwargs={'friendship_id': self.friendship.id})
        )
        self.assertEqual(response.status_code, 302)
        
        # Check that friendship is deleted
        self.assertEqual(
            Friendship.objects.filter(
                sender=self.user1, 
                receiver=self.user2, 
                status='accepted'
            ).count(),
            0
        )

    def test_unfriend_nonexistent_user(self):
        # Test unfriending a nonexistent user
        response = self.client.post(
            reverse('social:unfriend', kwargs={'friendship_id': 999999})
        )
        self.assertEqual(response.status_code, 404)

    def test_unfriend_non_friend(self):
        # Test unfriending someone who isn't a friend
        # Create a third user who isn't friends with user1
        user3 = get_user_model().objects.create_user(
            username='testuser3',
            email='user3@example.com',
            password='testpass123'
        )

        response = self.client.post(
            reverse('social:unfriend', kwargs={'friendship_id': 999999})
        )
        self.assertEqual(response.status_code, 404)

    def test_unfriend_preserves_other_friendships(self):
        # Test that unfriending doesn't affect other friendships
        # Create another friendship
        user3 = get_user_model().objects.create_user(
            username='testuser3',
            email='user3@example.com',
            password='testpass123'
        )
        other_friendship = Friendship.objects.create(
            sender=self.user1,
            receiver=user3,
            status='accepted'
        )
        
        # Unfriend user2
        self.client.post(
            reverse('social:unfriend', kwargs={'friendship_id': self.friendship.id})
        )
        
        # Check that friendship with user3 still exists
        self.assertTrue(
            Friendship.objects.filter(id=other_friendship.id).exists()
        )

    def test_get_method_requires_login(self):
        # Test that GET requests require login
        self.client.logout()
        response = self.client.get(
            reverse('social:unfriend', kwargs={'friendship_id': self.friendship.id})
        )
        self.assertEqual(response.status_code, 302)  # Redirects to login
