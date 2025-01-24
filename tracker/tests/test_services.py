from django.test import TestCase
from django.contrib.auth import get_user_model
from tracker.models import Habit, HabitCompletion, Badge
from social.models import Friendship
from tracker.services.badges.badge_service import BadgeService
from datetime import timedelta
from django.utils import timezone
from unittest.mock import patch, MagicMock
from tracker.services.ai.ai_service import AIHabitService

class TestBadgeService(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.badge_service = BadgeService(self.user)
        self.today = timezone.now().date()

    def test_health_streak_badge(self):
        """Test 7-day streak badge for health habits"""
        habit = Habit.objects.create(
            user=self.user,
            name="Exercise",
            frequency="daily",
            category="health"
        )
        
        # Create 7-day streak
        for i in range(7):
            HabitCompletion.objects.create(
                habit=habit,
                completed_at=self.today - timedelta(days=i)
            )
        
        self.badge_service.check_streak_badges()
        self.assertTrue(
            Badge.objects.filter(
                user=self.user,
                badge_type='health_7_day'
            ).exists()
        )

    def test_learning_streak_badge(self):
        """Test 7-day streak badge for learning habits"""
        habit = Habit.objects.create(
            user=self.user,
            name="Study",
            frequency="daily",
            category="learning"
        )
        
        # Create 7-day streak
        for i in range(7):
            HabitCompletion.objects.create(
                habit=habit,
                completed_at=self.today - timedelta(days=i)
            )
        
        self.badge_service.check_streak_badges()
        self.assertTrue(
            Badge.objects.filter(
                user=self.user,
                badge_type='learning_7_day'
            ).exists()
        )

    def test_productivity_streak_badge(self):
        """Test 7-day streak badge for productivity habits"""
        habit = Habit.objects.create(
            user=self.user,
            name="Work",
            frequency="daily",
            category="productivity"
        )
        
        # Create 7-day streak
        for i in range(7):
            HabitCompletion.objects.create(
                habit=habit,
                completed_at=self.today - timedelta(days=i)
            )
        
        self.badge_service.check_streak_badges()
        self.assertTrue(
            Badge.objects.filter(
                user=self.user,
                badge_type='productivity_7_day'
            ).exists()
        )

    def test_weekly_habits_dont_count_for_streaks(self):
        """Test that weekly habits don't contribute to streak badges"""
        habit = Habit.objects.create(
            user=self.user,
            name="Weekly Exercise",
            frequency="weekly",
            category="health"
        )
        
        # Create completions for 7 consecutive weeks
        for i in range(7):
            HabitCompletion.objects.create(
                habit=habit,
                completed_at=self.today - timedelta(weeks=i)
            )
        
        self.badge_service.check_streak_badges()
        self.assertFalse(
            Badge.objects.filter(
                user=self.user,
                badge_type='health_7_day'
            ).exists()
        )

    def test_first_friend_badge(self):
        """Test that making a friend awards the badge"""
        friend = get_user_model().objects.create_user(
            username='friend',
            password='testpass123'
        )
        
        # Create accepted friendship
        Friendship.objects.create(
            sender=self.user,
            receiver=friend,
            status='accepted'
        )
        
        self.badge_service.check_social_badges()
        self.assertTrue(
            Badge.objects.filter(
                user=self.user,
                badge_type='first_friend'
            ).exists()
        )

    def test_completion_badges_mixed_habits(self):
        """Test completion badges work with mix of daily and weekly habits"""
        # Create one daily and one weekly habit
        daily_habit = Habit.objects.create(
            user=self.user,
            name="Daily Exercise",
            frequency="daily"
        )
        weekly_habit = Habit.objects.create(
            user=self.user,
            name="Weekly Review",
            frequency="weekly"
        )
        
        # Create 6 daily completions
        for i in range(6):
            HabitCompletion.objects.create(
                habit=daily_habit,
                completed_at=self.today - timedelta(days=i)
            )
        
        # Create 4 weekly completions
        for i in range(4):
            HabitCompletion.objects.create(
                habit=weekly_habit,
                completed_at=self.today - timedelta(weeks=i)
            )
        
        # Should have 10 total completions (6 daily + 4 weekly)
        self.badge_service.check_completion_badges()
        self.assertTrue(
            Badge.objects.filter(
                user=self.user,
                badge_type='completions_10'
            ).exists()
        )

    def test_mixed_completion_rates_daily(self):
        """Test completion rates with multiple daily habits at different completion levels"""
        # Create three daily habits
        habits = [
            Habit.objects.create(
                user=self.user,
                name=f"Daily Habit {i}",
                frequency="daily"
            ) for i in range(3)
        ]
        
        # First habit: 2/3 days completed
        for i in range(2):
            HabitCompletion.objects.create(
                habit=habits[0],
                completed_at=self.today - timedelta(days=i)
            )
        
        # Second habit: 1/3 days completed
        HabitCompletion.objects.create(
            habit=habits[1],
            completed_at=self.today
        )
        
        # Third habit: 0/3 days completed
        
        # Should have 3 total completions out of 9 possible (3 habits × 3 days)
        self.badge_service.check_completion_badges()
        self.assertFalse(
            Badge.objects.filter(
                user=self.user,
                badge_type='completions_10'
            ).exists()
        )

    def test_mixed_completion_rates_weekly(self):
        """Test completion rates with multiple weekly habits at different completion levels"""
        # Create three weekly habits
        habits = [
            Habit.objects.create(
                user=self.user,
                name=f"Weekly Habit {i}",
                frequency="weekly"
            ) for i in range(3)
        ]
        
        # First habit: completed last 3 weeks
        for i in range(3):
            HabitCompletion.objects.create(
                habit=habits[0],
                completed_at=self.today - timedelta(weeks=i)
            )
        
        # Second habit: completed only this week
        HabitCompletion.objects.create(
            habit=habits[1],
            completed_at=self.today
        )
        
        # Third habit: no completions
        
        # Should have 4 completions total
        self.badge_service.check_completion_badges()
        self.assertFalse(
            Badge.objects.filter(
                user=self.user,
                badge_type='completions_10'
            ).exists()
        )

    def test_mixed_completion_rates_combined(self):
        """Test completion rates with mix of daily and weekly habits at different completion levels"""
        # Create two daily habits
        daily_habits = [
            Habit.objects.create(
                user=self.user,
                name=f"Daily Habit {i}",
                frequency="daily"
            ) for i in range(2)
        ]
        
        # Create two weekly habits
        weekly_habits = [
            Habit.objects.create(
                user=self.user,
                name=f"Weekly Habit {i}",
                frequency="weekly"
            ) for i in range(2)
        ]
        
        # First daily habit: 3/5 days completed
        for i in range(3):
            HabitCompletion.objects.create(
                habit=daily_habits[0],
                completed_at=self.today - timedelta(days=i)
            )
        
        # Second daily habit: 2/5 days completed
        for i in range(2):
            HabitCompletion.objects.create(
                habit=daily_habits[1],
                completed_at=self.today - timedelta(days=i)
            )
        
        # First weekly habit: completed last 2 weeks
        for i in range(2):
            HabitCompletion.objects.create(
                habit=weekly_habits[0],
                completed_at=self.today - timedelta(weeks=i)
            )
        
        # Second weekly habit: no completions
        
        # Should have 7 completions total (3 + 2 + 2 + 0)
        self.badge_service.check_completion_badges()
        self.assertFalse(
            Badge.objects.filter(
                user=self.user,
                badge_type='completions_10'
            ).exists()
        )
        
        # Add 3 more completions to get to 10
        for i in range(3):
            HabitCompletion.objects.create(
                habit=weekly_habits[1],
                completed_at=self.today - timedelta(weeks=i)
            )
        
        # Now should have 10 completions and get the badge
        self.badge_service.check_completion_badges()
        self.assertTrue(
            Badge.objects.filter(
                user=self.user,
                badge_type='completions_10'
            ).exists()
        )

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
    
    @patch('tracker.services.ai.ai_service.OpenAI')
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

    @patch('tracker.services.ai.ai_service.OpenAI')
    def test_handle_openai_error(self, mock_openai):
        mock_openai.return_value.chat.completions.create.side_effect = Exception("API Error")
        
        service = AIHabitService()
        result = service.generate_habit_summary(self.user)
        
        self.assertTrue(result.startswith("Error:")) 