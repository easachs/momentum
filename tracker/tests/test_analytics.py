import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone
from tracker.models import Habit, HabitCompletion

# Import the fixture
@pytest.fixture
def test_user():
    return get_user_model().objects.create(
        email='test@example.com',
        username='testuser'
    )

@pytest.mark.django_db
class TestHabitAnalytics:
    def test_category_performance_stats(self, test_user, client):
        client.force_login(test_user)
        # Create habits in different categories
        habit1 = Habit.objects.create(
            user=test_user,
            name="Health Habit",
            category="health",
            frequency="daily"
        )
        habit2 = Habit.objects.create(
            user=test_user,
            name="Learning Habit",
            category="learning",
            frequency="daily"
        )

        # Complete some habits
        habit1.toggle_completion()
        
        response = client.get(reverse('tracker:habit_list'))
        category_stats = {
            stat['category']: stat 
            for stat in response.context['analytics']['category_stats']
        }

        # Check health category stats
        assert category_stats['health']['completed'] == 1
        assert category_stats['health']['total'] == 1  # One day since creation

        # Check learning category stats
        assert category_stats['learning']['completed'] == 0
        assert category_stats['learning']['total'] == 1  # One day since creation

    def test_weekly_monthly_completion_counts(self, test_user, client):
        client.force_login(test_user)
        today = timezone.now().date()
        habit = Habit.objects.create(
            user=test_user,
            name="Test Habit",
            frequency="daily"
        )

        # Create completions across different time periods
        dates = [
            today,
            today - timedelta(days=1),
            today - timedelta(days=7),
            today - timedelta(days=14),
            today - timedelta(days=30)
        ]
        for date in dates:
            HabitCompletion.objects.create(habit=habit, completed_at=date)

        response = client.get(reverse('tracker:habit_list'))
        analytics = response.context['analytics']

        assert analytics['this_week_completions'] == 2  # Today and yesterday
        assert analytics['this_month_completions'] == 4  # All except the 30-day-old one 