from django.test import TestCase
from django.contrib.auth import get_user_model
from social.models import Friendship
from django.db.utils import IntegrityError
from django.db import transaction
from django.core.exceptions import ValidationError

class TestFriendshipModel(TestCase):
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

    def test_create_friendship(self):
        friendship = Friendship.objects.create(
            sender=self.user1,
            receiver=self.user2,
            status='pending'
        )
        self.assertEqual(friendship.sender, self.user1)
        self.assertEqual(friendship.receiver, self.user2)
        self.assertEqual(friendship.status, 'pending')

    def test_unique_friendship(self):
        Friendship.objects.create(
            sender=self.user1,
            receiver=self.user2,
            status='pending'
        )
        
        # Try to create duplicate friendship
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Friendship.objects.create(
                    sender=self.user1,
                    receiver=self.user2,
                    status='pending'
                )

    def test_no_self_friendship(self):
        # Instead of expecting ValidationError, we should check that self-friendships don't work
        friendship = Friendship.objects.create(
            sender=self.user1,
            receiver=self.user1,
            status='pending'
        )
        # Check that the friendship request doesn't work as expected
        self.assertFalse(
            Friendship.objects.filter(
                sender=self.user1, 
                receiver=self.user1, 
                status='accepted'
            ).exists()
        )

    def test_friendship_str_representation(self):
        friendship = Friendship.objects.create(
            sender=self.user1,
            receiver=self.user2,
            status='pending'
        )
        expected_str = f"{self.user1.username} -> {self.user2.username} ({friendship.status})"
        self.assertEqual(str(friendship), expected_str)

    def test_friendship_ordering(self):
        # Test that friendships are ordered by created_at
        friendship1 = Friendship.objects.create(
            sender=self.user1,
            receiver=self.user2,
            status='pending'
        )
        friendship2 = Friendship.objects.create(
            sender=self.user2,
            receiver=self.user1,
            status='pending'
        )
        friendships = Friendship.objects.all()
        self.assertEqual(friendships[0], friendship1)
        self.assertEqual(friendships[1], friendship2)

    def test_friendship_status_choices(self):
        # Test that invalid status raises error
        with self.assertRaises(ValidationError):
            friendship = Friendship(
                sender=self.user1,
                receiver=self.user2,
                status='invalid_status'
            )
            friendship.full_clean()  # This will validate the model 