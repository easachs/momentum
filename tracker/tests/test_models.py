import pytest
from tracker.models import Habit

@pytest.mark.django_db
def test_create_habit():
    # Arrange: Create a new Habit instance
    habit = Habit.objects.create(
        name="Exercise",
        description="Go for a run",
        frequency="daily"
    )

    # Act & Assert: Verify the habit was created successfully
    assert habit.name == "Exercise"
    assert habit.description == "Go for a run"
    assert habit.frequency == "daily"
    assert str(habit) == "Exercise"  # Tests the __str__ method