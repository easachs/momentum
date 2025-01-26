from django.contrib.auth import get_user_model
from django.test import TestCase
from tracker.models import Badge


class TestBadgeModel(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.user2 = get_user_model().objects.create_user(
            username="testuser2", password="testpass123"
        )

    def test_badge_uniqueness(self):
        """Test that a user can't get duplicate badges"""
        badge1 = Badge.objects.create(user=self.user, badge_type="first_friend")
        # Try to create duplicate
        badge2, created = Badge.objects.get_or_create(
            user=self.user, badge_type="first_friend"
        )
        self.assertFalse(created)
        self.assertEqual(badge1, badge2)

    def test_get_user_highest_badges(self):
        """Test getting highest badges for each category"""
        # Create some badges
        Badge.objects.create(user=self.user, badge_type="completions_10")
        Badge.objects.create(user=self.user, badge_type="completions_50")
        Badge.objects.create(user=self.user, badge_type="health_7_day")
        Badge.objects.create(user=self.user, badge_type="health_30_day")

        highest_badges = Badge.get_user_highest_badges(self.user)
        self.assertEqual(highest_badges["completions"], "completions_50")
        self.assertEqual(highest_badges["health"], "health_30_day")
