import pytest
from django.core.exceptions import ValidationError
from tracker.models import Habit
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.db.utils import IntegrityError
from django.urls import reverse

@pytest.mark.django_db
class TestHabitModel:
    def test_create_habit(self):
        # Arrange: Create a test user and habit
        user = get_user_model().objects.create(
            email='test@example.com',
            username='testuser'
        )
        habit = Habit.objects.create(
            user=user,
            name="Exercise",
            description="Go for a run",
            frequency="daily"
        )

        # Act & Assert: Verify the habit was created successfully
        assert habit.name == "Exercise"
        assert habit.description == "Go for a run"
        assert habit.frequency == "daily"
        assert habit.user == user
        assert str(habit) == "Exercise"  # Tests the __str__ method

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
        user = get_user_model().objects.create(email='test@example.com')
        Habit.objects.create(
            user=user,
            name="Exercise",
            frequency="daily"
        )
        
        # Delete user should delete their habits
        user.delete()
        assert Habit.objects.count() == 0

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
        user = get_user_model().objects.create(email='test@example.com')
        habit = Habit.objects.create(
            user=user,
            name="Exercise",
            frequency="daily"
        )
        assert str(habit) == "Exercise"
        # Get the expected URL using reverse() to ensure it matches the URL patterns
        expected_url = reverse('tracker:habit_detail', args=[habit.pk])
        assert habit.get_absolute_url() == expected_url

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