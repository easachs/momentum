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

@pytest.fixture
def test_habit(test_user):
    return Habit.objects.create(
        user=test_user,
        name="Exercise",
        description="Go for a run",
        frequency="daily",
        category="health"
    )

@pytest.mark.django_db
class TestHabitViews:
    def test_habit_list_view_requires_login(self, client):
        url = reverse('tracker:habit_list')
        response = client.get(url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_habit_list_view_shows_user_habits(self, client, test_user, test_habit):
        client.force_login(test_user)
        url = reverse('tracker:habit_list')
        response = client.get(url)
        assert response.status_code == 200
        assert test_habit.name in str(response.content)

    def test_habit_create_view(self, client, test_user):
        client.force_login(test_user)
        url = reverse('tracker:habit_create')
        data = {
            'name': 'Read Books',
            'description': 'Read for 30 minutes',
            'frequency': 'daily',
            'category': 'learning'
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert Habit.objects.filter(name='Read Books').exists()

    def test_habit_update_view(self, client, test_user, test_habit):
        client.force_login(test_user)
        url = reverse('tracker:habit_update', args=[test_habit.pk])
        data = {
            'name': 'Exercise Updated',
            'description': test_habit.description,
            'frequency': test_habit.frequency,
            'category': test_habit.category
        }
        response = client.post(url, data)
        assert response.status_code == 302
        test_habit.refresh_from_db()
        assert test_habit.name == 'Exercise Updated'

    def test_habit_delete_view(self, client, test_user, test_habit):
        client.force_login(test_user)
        url = reverse('tracker:habit_delete', args=[test_habit.pk])
        response = client.post(url)
        assert response.status_code == 302
        assert not Habit.objects.filter(pk=test_habit.pk).exists()

    def test_user_can_only_see_own_habits(self, client, test_user, test_habit):
        # Create another user and their habit
        other_user = get_user_model().objects.create(
            email='other@example.com',
            username='otheruser'
        )
        other_habit = Habit.objects.create(
            user=other_user,
            name="Other's Exercise",
            description="Other's workout",
            frequency="daily",
            category="health"
        )

        # Login as test_user
        client.force_login(test_user)
        
        # Check list view
        response = client.get(reverse('tracker:habit_list'))
        assert test_habit.name in str(response.content)
        assert other_habit.name not in str(response.content)

        # Try to access other user's habit detail
        response = client.get(reverse('tracker:habit_detail', args=[other_habit.pk]))
        assert response.status_code == 404 

    def test_habit_create_view_invalid_data(self, client, test_user):
        client.force_login(test_user)
        url = reverse('tracker:habit_create')
        data = {
            'name': 'Ab',  # Too short
            'frequency': 'invalid',
            'category': 'invalid'
        }
        response = client.post(url, data)
        assert response.status_code == 200  # Returns to form with errors
        assert not Habit.objects.filter(name='Ab').exists()

    def test_habit_update_view_invalid_data(self, client, test_user, test_habit):
        client.force_login(test_user)
        url = reverse('tracker:habit_update', args=[test_habit.pk])
        data = {
            'name': 'Ab',  # Too short
            'frequency': 'invalid',
            'category': 'invalid'
        }
        response = client.post(url, data)
        assert response.status_code == 200  # Returns to form with errors
        test_habit.refresh_from_db()
        assert test_habit.name == "Exercise"  # Name unchanged

    def test_cannot_update_other_users_habit(self, client, test_user, test_habit):
        other_user = get_user_model().objects.create(
            email='other@example.com',
            username='otheruser'
        )
        client.force_login(other_user)
        
        # Try to update
        url = reverse('tracker:habit_update', args=[test_habit.pk])
        data = {
            'name': 'Hacked Exercise',
            'description': test_habit.description,
            'frequency': test_habit.frequency,
            'category': test_habit.category
        }
        response = client.post(url, data)
        assert response.status_code == 404
        test_habit.refresh_from_db()
        assert test_habit.name == "Exercise"  # Name unchanged

    def test_cannot_delete_other_users_habit(self, client, test_user, test_habit):
        other_user = get_user_model().objects.create(
            email='other@example.com',
            username='otheruser'
        )
        client.force_login(other_user)
        
        # Try to delete
        url = reverse('tracker:habit_delete', args=[test_habit.pk])
        response = client.post(url)
        assert response.status_code == 404
        assert Habit.objects.filter(pk=test_habit.pk).exists()

    def test_habit_list_empty_for_new_user(self, client):
        user = get_user_model().objects.create(
            email='new@example.com',
            username='newuser'
        )
        client.force_login(user)
        url = reverse('tracker:habit_list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'No habits yet.' in str(response.content)

    def test_habit_detail_view(self, client, test_user, test_habit):
        client.force_login(test_user)
        url = reverse('tracker:habit_detail', args=[test_habit.pk])
        response = client.get(url)
        assert response.status_code == 200
        assert test_habit.name in str(response.content)
        assert test_habit.description in str(response.content)
        assert test_habit.get_frequency_display() in str(response.content)
        assert test_habit.get_category_display() in str(response.content)

    def test_redirect_after_create(self, client, test_user):
        client.force_login(test_user)
        url = reverse('tracker:habit_create')
        data = {
            'name': 'New Habit',
            'description': 'Description',
            'frequency': 'daily',
            'category': 'health'
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert response.url == reverse('tracker:habit_list')

    def test_unauthenticated_user_redirected_to_login(self, client):
        urls = [
            reverse('tracker:habit_list'),
            reverse('tracker:habit_create'),
            reverse('tracker:habit_detail', args=[1]),
            reverse('tracker:habit_update', args=[1]),
            reverse('tracker:habit_delete', args=[1]),
        ]
        for url in urls:
            response = client.get(url)
            assert response.status_code == 302
            assert '/accounts/login/' in response.url 

    def test_toggle_completion_view(self, client, test_user, test_habit):
        client.force_login(test_user)
        url = reverse('tracker:habit_completion_toggle', args=[test_habit.pk])
        
        # Initially not completed
        assert not test_habit.is_completed_for_date()
        
        # Toggle to completed
        response = client.post(url)
        assert response.status_code == 302  # Redirect
        test_habit.refresh_from_db()
        assert test_habit.is_completed_for_date()
        
        # Toggle back to not completed
        response = client.post(url)
        assert response.status_code == 302  # Redirect
        test_habit.refresh_from_db()
        assert not test_habit.is_completed_for_date()

    def test_cannot_toggle_other_users_habit_completion(self, client, test_user, test_habit):
        other_user = get_user_model().objects.create(
            email='other@example.com',
            username='otheruser'
        )
        client.force_login(other_user)
        
        url = reverse('tracker:habit_completion_toggle', args=[test_habit.pk])
        response = client.post(url)
        assert response.status_code == 404
        
        test_habit.refresh_from_db()
        assert not test_habit.is_completed_for_date()

    def test_toggle_completion_requires_login(self, client, test_habit):
        url = reverse('tracker:habit_completion_toggle', args=[test_habit.pk])
        response = client.post(url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_toggle_completion_preserves_referer(self, client, test_user, test_habit):
        client.force_login(test_user)
        url = reverse('tracker:habit_completion_toggle', args=[test_habit.pk])
        
        # Test with referer from list view
        response = client.post(url, HTTP_REFERER='/tracker/')
        assert response.status_code == 302
        assert response.url == '/tracker/'
        
        # Test with no referer (should go to detail view)
        response = client.post(url)
        assert response.status_code == 302
        assert response.url == reverse('tracker:habit_detail', args=[test_habit.pk]) 

    def test_habit_list_shows_completion_status(self, client, test_user, test_habit):
        client.force_login(test_user)
        
        # Initially not completed
        response = client.get(reverse('tracker:habit_list'))
        assert 'Not Done' in str(response.content)
        assert 'Mark Complete' in str(response.content)
        
        # After completion
        test_habit.toggle_completion()
        response = client.get(reverse('tracker:habit_list'))
        assert 'Done' in str(response.content)
        assert 'Mark Incomplete' in str(response.content)

    def test_habit_detail_shows_completion_status(self, client, test_user, test_habit):
        client.force_login(test_user)
        url = reverse('tracker:habit_detail', args=[test_habit.pk])
        
        # Initially not completed
        response = client.get(url)
        assert 'Mark Complete' in str(response.content)
        
        # After completion
        test_habit.toggle_completion()
        response = client.get(url)
        assert 'Mark Incomplete' in str(response.content)

    def test_toggle_completion_with_invalid_habit_id(self, client, test_user):
        client.force_login(test_user)
        url = reverse('tracker:habit_completion_toggle', args=[99999])  # Non-existent ID
        response = client.post(url)
        assert response.status_code == 404 