from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from social.models import Friendship

class TestFriendsListView(TestCase):
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

    def test_friends_list_view(self):
        Friendship.objects.create(
            sender=self.user1, receiver=self.user2, status="accepted"
        )
        response = self.client.get(reverse("social:friends_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user2.username)

    def test_friends_list_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("social:friends_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)
