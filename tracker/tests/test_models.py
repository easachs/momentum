from datetime import timedelta
import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from django.db.utils import IntegrityError
from django.urls import reverse
from django.test import TestCase
from tracker.models import Habit, HabitCompletion, Badge

@pytest.mark.django_db
class TestHabitModel(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.habit = Habit.objects.create(
            name='Test Habit',
            user=self.user,
            frequency='daily'
        )

    def test_create_habit(self):
        user = get_user_model().objects.create_user(
            email='test2@example.com',
            username='testuser2',
            password='testpass123'
        )
        habit = Habit.objects.create(
            user=user,
            name="Exercise",
            description="Go for a run",
            frequency="daily"
        )

        self.assertEqual(habit.name, "Exercise")
        self.assertEqual(habit.description, "Go for a run")
        self.assertEqual(habit.frequency, "daily")
        self.assertEqual(habit.user, user)
        self.assertEqual(str(habit), "Exercise")

    def test_habit_name_min_length(self):
        user = get_user_model().objects.create(email='test@example.com')
        with pytest.raises(ValidationError):
            habit = Habit.objects.create(
                user=user,
                name="Ab",  # Too short (min length is 3)
                frequency="daily"
            )
            habit.full_clean()

    def test_habit_unique_name_per_user(self):
        user = get_user_model().objects.create(email='test@example.com')
        Habit.objects.create(
            user=user,
            name="Exercise",
            frequency="daily"
        )

        # Try to create another habit with the same name for the same user
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Habit.objects.create(
                    user=user,
                    name="Exercise",
                    frequency="daily"
                )

    def test_habit_same_name_different_users(self):
        user1 = get_user_model().objects.create(
            email='test1@example.com',
            username='testuser1'  # Add unique username
        )
        user2 = get_user_model().objects.create(
            email='test2@example.com',
            username='testuser2'  # Add unique username
        )

        # Same habit name should work for different users
        habit1 = Habit.objects.create(
            user=user1,
            name="Exercise",
            frequency="daily"
        )
        habit2 = Habit.objects.create(
            user=user2,
            name="Exercise",
            frequency="daily"
        )

        assert habit1.name == habit2.name
        assert habit1.user != habit2.user

    def test_habit_cascade_delete(self):
        habit_id = self.habit.id
        self.user.delete()
        self.assertEqual(Habit.objects.filter(id=habit_id).count(), 0)

    def test_habit_invalid_frequency(self):
        user = get_user_model().objects.create(email='test@example.com')
        with pytest.raises(ValidationError):
            habit = Habit.objects.create(
                user=user,
                name="Exercise",
                frequency="monthly"  # Invalid frequency
            )
            habit.full_clean()

    def test_habit_invalid_category(self):
        user = get_user_model().objects.create(email='test@example.com')
        with pytest.raises(ValidationError):
            habit = Habit.objects.create(
                user=user,
                name="Exercise",
                frequency="daily",
                category="invalid"  # Invalid category
            )
            habit.full_clean()

    def test_habit_created_at_auto_set(self):
        user = get_user_model().objects.create(email='test@example.com')
        before = timezone.now()
        habit = Habit.objects.create(
            user=user,
            name="Exercise",
            frequency="daily"
        )
        after = timezone.now()
        assert before <= habit.created_at <= after

    def test_habit_str_representation(self):
        habit = Habit.objects.create(
            name='Test Habit ' + timezone.now().strftime('%Y%m%d%H%M%S'),
            user=self.user
        )
        expected_url = reverse('tracker:habit_detail', kwargs={'pk': habit.pk})
        self.assertEqual(habit.get_absolute_url(), expected_url)

    def test_habit_blank_description_allowed(self):
        user = get_user_model().objects.create(email='test@example.com')
        habit = Habit.objects.create(
            user=user,
            name="Exercise",
            description="",
            frequency="daily"
        )
        habit.full_clean()  # Should not raise ValidationError

    def test_habit_null_description_allowed(self):
        user = get_user_model().objects.create(email='test@example.com')
        habit = Habit.objects.create(
            user=user,
            name="Exercise",
            description=None,
            frequency="daily"
        )
        habit.full_clean()  # Should not raise ValidationError

    def test_habit_completion_methods(self):
        user = get_user_model().objects.create(email='test@example.com')
        habit = Habit.objects.create(
            user=user,
            name="Exercise",
            frequency="daily"
        )

        # Initially not completed
        assert not habit.is_completed_for_date()

        # Toggle to completed
        assert habit.toggle_completion() is True
        assert habit.is_completed_for_date()

        # Toggle back to not completed
        assert habit.toggle_completion() is False
        assert not habit.is_completed_for_date()

    def test_habit_completion_unique_per_date(self):
        user = get_user_model().objects.create(email='test@example.com')
        habit = Habit.objects.create(
            user=user,
            name="Exercise",
            frequency="daily"
        )

        # Complete for today
        habit.toggle_completion()
        assert habit.completions.count() == 1

        # Try to complete again for today
        habit.toggle_completion()
        assert habit.completions.count() == 0  # Should be removed

    def test_habit_completion_with_specific_date(self):
        user = get_user_model().objects.create(email='test@example.com')
        habit = Habit.objects.create(
            user=user,
            name="Exercise",
            frequency="daily"
        )

        # Complete for a specific date
        specific_date = timezone.now().date() - timedelta(days=1)
        assert habit.toggle_completion(specific_date) is True
        assert habit.is_completed_for_date(specific_date)
        assert not habit.is_completed_for_date()  # Today should still be incomplete

    def test_habit_completion_cascade_delete(self):
        user = get_user_model().objects.create(email='test@example.com')
        habit = Habit.objects.create(
            user=user,
            name="Exercise",
            frequency="daily"
        )

        # Create some completions
        habit.toggle_completion()
        habit.toggle_completion(timezone.now().date() - timedelta(days=1))
        assert habit.completions.count() == 2

        # Delete habit should delete completions
        habit.delete()
        assert HabitCompletion.objects.count() == 0

    def test_habit_completion_str_representation(self):
        user = get_user_model().objects.create(email='test@example.com')
        habit = Habit.objects.create(
            user=user,
            name="Exercise",
            frequency="daily"
        )

        completion = HabitCompletion.objects.create(
            habit=habit,
            completed_at=timezone.now().date()
        )

        expected_str = f"{habit.name} completed on {completion.completed_at}"
        assert str(completion) == expected_str

class TestBadgeModel(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.user2 = get_user_model().objects.create_user(
            username='testuser2',
            password='testpass123'
        )

    def test_badge_uniqueness(self):
        """Test that a user can't get duplicate badges"""
        badge1 = Badge.objects.create(user=self.user, badge_type='first_friend')
        # Try to create duplicate
        badge2, created = Badge.objects.get_or_create(user=self.user, badge_type='first_friend')
        self.assertFalse(created)
        self.assertEqual(badge1, badge2)

    def test_get_user_highest_badges(self):
        """Test getting highest badges for each category"""
        # Create some badges
        Badge.objects.create(user=self.user, badge_type='completions_10')
        Badge.objects.create(user=self.user, badge_type='completions_50')
        Badge.objects.create(user=self.user, badge_type='health_7_day')
        Badge.objects.create(user=self.user, badge_type='health_30_day')

        highest_badges = Badge.get_user_highest_badges(self.user)
        self.assertEqual(highest_badges['completions'], 'completions_50')
        self.assertEqual(highest_badges['health'], 'health_30_day')
