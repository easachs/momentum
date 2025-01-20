from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from social.models import Friendship
from tracker.models import Habit, HabitCompletion
from django.utils import timezone
from datetime import timedelta

class TestSocialIntegration(TestCase):
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
        self.client.force_login(self.user1)

    def test_friend_request_to_habit_viewing_flow(self):
        # Create a habit for user2
        habit = Habit.objects.create(
            user=self.user2,
            name="Test Habit",
            frequency="daily"
        )

        # Try to view user2's dashboard (should not see analytics)
        response = self.client.get(reverse('social:dashboard', kwargs={'username': self.user2.username}))
        self.assertNotContains(response, 'Your Habit Analytics')

        # Send friend request
        self.client.get(
            reverse('social:send_friend_request', kwargs={'username': self.user2.username})
        )

        # Login as user2
        self.client.force_login(self.user2)

        # Accept friend request
        friendship = Friendship.objects.get(sender=self.user1, receiver=self.user2)
        self.client.get(
            reverse('social:handle_friend_request', 
                   kwargs={'friendship_id': friendship.id, 'action': 'accept'})
        )

        # Login back as user1
        self.client.force_login(self.user1)

        # Now should be able to see user2's analytics
        response = self.client.get(reverse('social:dashboard', kwargs={'username': self.user2.username}))
        self.assertContains(response, "user2's Habit Analytics")

    def test_leaderboard_completion_update_flow(self):
        # Create habits for both users
        habit1 = Habit.objects.create(
            user=self.user1,
            name="User1 Habit",
            frequency="daily",
            category="health"
        )
        
        habit2 = Habit.objects.create(
            user=self.user2,
            name="User2 Habit",
            frequency="daily",
            category="health"
        )

        # Complete habit2 multiple times to ensure higher completion count
        for _ in range(5):
            habit2.toggle_completion()
        
        # Check leaderboard order
        response = self.client.get(reverse('social:leaderboard'))
        
        # Instead of searching raw HTML, check the actual data
        leaderboard_data = response.context['leaderboard_data']
        
        # Verify both users are in the leaderboard
        user_ids = [entry['user'].id for entry in leaderboard_data]
        self.assertIn(self.user1.id, user_ids)
        self.assertIn(self.user2.id, user_ids)
        
        # Check that user2 comes before user1 in the leaderboard data
        user2_index = next(i for i, entry in enumerate(leaderboard_data) if entry['user'] == self.user2)
        user1_index = next(i for i, entry in enumerate(leaderboard_data) if entry['user'] == self.user1)
        self.assertTrue(user2_index < user1_index)

    def test_dashboard_analytics_display(self):
        """Test that dashboard displays analytics correctly"""
        # Create some habits and completions
        habit = Habit.objects.create(
            user=self.user1,
            name="Test Habit",
            frequency="daily"
        )
        HabitCompletion.objects.create(
            habit=habit,
            completed_at=timezone.now()
        )

        # Create friendship to allow viewing analytics
        if self.user1 != self.user2:
            Friendship.objects.create(
                sender=self.user1,
                receiver=self.user2,
                status='accepted'
            )

        response = self.client.get(
            reverse('social:dashboard', kwargs={'username': self.user1.username})
        )
        self.assertEqual(response.status_code, 200)
        # Check that analytics are displayed
        self.assertTrue('analytics' in response.context)
        self.assertEqual(response.context['analytics']['total_habits'], 1)
        self.assertEqual(response.context['analytics']['this_week_completions'], 1)

    def test_dashboard_friend_requests(self):
        """Test that dashboard shows friend requests"""
        # Create a pending friend request
        Friendship.objects.create(
            sender=self.user2,
            receiver=self.user1,
            status='pending'
        )

        response = self.client.get(
            reverse('social:dashboard', kwargs={'username': self.user1.username})
        )
        # Check that friend requests are in the context
        self.assertTrue('friend_requests' in response.context)
        self.assertEqual(len(response.context['friend_requests']), 1)
        self.assertEqual(response.context['friend_requests'][0].sender, self.user2) 