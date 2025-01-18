import pytest
from tracker.models import Habit
from django.contrib.auth import get_user_model

@pytest.mark.django_db
def test_create_habit():
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