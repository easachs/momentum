from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from social.models import Friendship

class TestSendFriendRequestView(TestCase):
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
        self.client.force_login(self.user1)

    def test_send_friend_request(self):
        response = self.client.get(
            reverse(
                "social:send_friend_request", kwargs={"username": self.user2.username}
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Friendship.objects.filter(
                sender=self.user1, receiver=self.user2, status="pending"
            ).exists()
        )

    def test_cannot_send_friend_request_to_self(self):
        response = self.client.get(
            reverse(
                "social:send_friend_request", kwargs={"username": self.user1.username}
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Friendship.objects.filter(sender=self.user1, receiver=self.user1).exists()
        )
