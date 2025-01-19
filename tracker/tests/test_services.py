from django.test import TestCase
from django.contrib.auth import get_user_model
from tracker.models import Habit, HabitCompletion, Badge
from social.models import Friendship
from tracker.services.badge_service import BadgeService
from datetime import timedelta
from django.utils import timezone
from unittest.mock import patch, MagicMock
from tracker.services.ai_service import AIHabitService

class TestBadgeService(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.badge_service = BadgeService(self.user)

    def test_completion_badges(self):
        """Test awarding completion badges"""
        habit = Habit.objects.create(
            user=self.user,
            name="Test Habit",
            frequency="daily"
        )
        
        # Create 10 completions
        for i in range(10):
            HabitCompletion.objects.create(
                habit=habit,
                completed_at=timezone.now().date() - timedelta(days=i)
            )
        
        self.badge_service.check_completion_badges()
        self.assertTrue(Badge.objects.filter(
            user=self.user,
            badge_type='completions_10'
        ).exists())

    def test_streak_badges(self):
        """Test awarding streak badges"""
        habit = Habit.objects.create(
            user=self.user,
            name="Test Habit",
            frequency="daily",
            category="health"
        )
        
        # Create 7-day streak
        for i in range(7):
            HabitCompletion.objects.create(
                habit=habit,
                completed_at=timezone.now().date() - timedelta(days=i)
            )
        
        self.badge_service.check_streak_badges()
        self.assertTrue(Badge.objects.filter(
            user=self.user,
            badge_type='health_7_day'
        ).exists())

    def test_badges_are_permanent(self):
        """Test that badges aren't removed when conditions no longer met"""
        # Create a 10-completion badge
        Badge.objects.create(user=self.user, badge_type='completions_10')
        
        # Check badges with only 5 completions
        habit = Habit.objects.create(user=self.user, name="Test Habit")
        for i in range(5):
            HabitCompletion.objects.create(
                habit=habit,
                completed_at=timezone.now().date() - timedelta(days=i)
            )
        
        self.badge_service.check_completion_badges()
        # Badge should still exist
        self.assertTrue(Badge.objects.filter(
            user=self.user,
            badge_type='completions_10'
        ).exists())

    def test_check_all_badges(self):
        """Test checking all badge types"""
        habit = Habit.objects.create(
            user=self.user,
            name="Test Habit",
            frequency="daily",
            category="health"
        )
        
        # Create completions for streak and completion badges
        for i in range(10):  # Changed from 7 to 10 to get the completions_10 badge
            HabitCompletion.objects.create(
                habit=habit,
                completed_at=timezone.now().date() - timedelta(days=i)
            )
        
        self.badge_service.check_all_badges()
        
        # Should have both completion and streak badges
        self.assertTrue(Badge.objects.filter(
            user=self.user,
            badge_type='completions_10'
        ).exists())
        self.assertTrue(Badge.objects.filter(
            user=self.user,
            badge_type='health_7_day'
        ).exists())

    def test_social_badges(self):
        """Test awarding social badges"""
        friend = get_user_model().objects.create_user(
            username='friend',
            password='testpass123'
        )
        Friendship.objects.create(
            sender=self.user,
            receiver=friend,
            status='accepted'
        )
        
        self.badge_service.check_social_badges()
        self.assertTrue(Badge.objects.filter(
            user=self.user,
            badge_type='first_friend'
        ).exists())

class TestAIService(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.habit = Habit.objects.create(
            user=self.user,
            name="Test Habit",
            frequency="daily",
            category="health"
        )
    
    @patch('tracker.services.ai_service.OpenAI')
    def test_generate_habit_summary(self, mock_openai):
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test summary"))]
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        service = AIHabitService()
        summary = service.generate_habit_summary(self.user)
        
        self.assertEqual(summary, "Test summary")
        mock_openai.return_value.chat.completions.create.assert_called_once()

    def test_gather_habit_stats(self):
        # Create some completions
        for i in range(3):
            HabitCompletion.objects.create(
                habit=self.habit,
                completed_at=timezone.now().date() - timedelta(days=i)
            )
        
        service = AIHabitService()
        stats = service._gather_habit_stats(Habit.objects.filter(user=self.user))
        
        self.assertEqual(len(stats), 1)
        self.assertEqual(stats[0]['name'], "Test Habit")
        self.assertEqual(stats[0]['monthly_completions'], 3)

    def test_build_prompt(self):
        habit_context = [{
            'name': 'Test Habit',
            'frequency': 'daily',
            'streak': 3,
            'monthly_completions': 10,
            'category': 'health'
        }]
        
        service = AIHabitService()
        prompt = service._build_prompt('testuser', habit_context)
        
        self.assertIn('testuser', prompt)
        self.assertIn('Test Habit', prompt)
        self.assertIn('health', prompt)
        self.assertIn('3', prompt)  # streak
        self.assertIn('10', prompt)  # monthly completions

    @patch('tracker.services.ai_service.OpenAI')
    def test_handle_openai_error(self, mock_openai):
        mock_openai.return_value.chat.completions.create.side_effect = Exception("API Error")
        
        service = AIHabitService()
        result = service.generate_habit_summary(self.user)
        
        self.assertTrue(result.startswith("Error:")) 