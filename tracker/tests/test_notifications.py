import pytest
from django.urls import reverse
from tracker.models import Habit
from django.contrib.auth import get_user_model

@pytest.fixture
def test_user():
    return get_user_model().objects.create(
        email='test@example.com',
        username='testuser'
    )

@pytest.mark.django_db
class TestHabitNotifications:
    def test_incomplete_habit_notifications(self, test_user, client):
        client.force_login(test_user)
        # Create some habits
        Habit.objects.create(
            user=test_user,
            name="Daily Habit 1",
            frequency="daily"
        )
        Habit.objects.create(
            user=test_user,
            name="Daily Habit 2",
            frequency="daily"
        )
        Habit.objects.create(
            user=test_user,
            name="Weekly Habit",
            frequency="weekly"
        )

        response = client.get(reverse('tracker:habit_list'))
        notifications = response.context['notifications']

        # Initially all habits are incomplete
        assert notifications['incomplete_daily'] == 2
        assert notifications['incomplete_weekly'] == 1

        # Complete one daily habit
        habit = Habit.objects.get(name="Daily Habit 1")
        habit.toggle_completion()

        response = client.get(reverse('tracker:habit_list'))
        notifications = response.context['notifications']

        # Check updated incomplete counts
        assert notifications['incomplete_daily'] == 1
        assert notifications['incomplete_weekly'] == 1

    def test_notification_display(self, test_user, client):
        client.force_login(test_user)
        Habit.objects.create(
            user=test_user,
            name="Test Habit",
            frequency="daily"
        )

        response = client.get(reverse('tracker:habit_list'))
        content = response.content.decode()

        # Check that notification is displayed
        assert 'You have 1 incomplete daily habit today' in content

        # Complete the habit
        habit = Habit.objects.first()
        habit.toggle_completion()

        response = client.get(reverse('tracker:habit_list'))
        content = response.content.decode()

        # Check that notification is no longer displayed
        assert 'You have 1 incomplete daily habit today' not in content 