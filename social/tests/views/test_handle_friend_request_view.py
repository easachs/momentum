from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from social.models import Friendship

class TestHandleFriendRequestView(TestCase):
    def setUp(self):
        self.user1 = get_user_model().objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass123"
        )
        self.user2 = get_user_model().objects.create_user(
            username="user2",
            email="user2@example.com",
            password="testpass123"
        )
        self.user3 = get_user_model().objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )
        self.client.force_login(self.user1)

    def test_handle_friend_request_accept(self):
        friendship = Friendship.objects.create(
            sender=self.user2, receiver=self.user1, status="pending"
        )
        response = self.client.get(
            reverse(
                "social:handle_friend_request",
                kwargs={"friendship_id": friendship.id, "action": "accept"},
            )
        )
        self.assertEqual(response.status_code, 302)
        friendship.refresh_from_db()
        self.assertEqual(friendship.status, "accepted")

    def test_handle_friend_request_decline(self):
        friendship = Friendship.objects.create(
            sender=self.user2, receiver=self.user1, status="pending"
        )
        response = self.client.get(
            reverse(
                "social:handle_friend_request",
                kwargs={"friendship_id": friendship.id, "action": "decline"},
            )
        )
        self.assertEqual(response.status_code, 302)
        friendship.refresh_from_db()
        self.assertEqual(friendship.status, "declined")

    def test_cannot_handle_other_users_friend_request(self):
        friendship = Friendship.objects.create(
            sender=self.user2,
            receiver=self.user3,  # Not self.user1
            status="pending",
        )

        response = self.client.get(
            reverse(
                "social:handle_friend_request",
                kwargs={"friendship_id": friendship.id, "action": "accept"},
            )
        )
        self.assertEqual(response.status_code, 302)  # Redirects with error message
        self.assertRedirects(
            response,
            reverse("social:dashboard", kwargs={"username": self.user1.username}),
        )
