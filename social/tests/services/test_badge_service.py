from datetime import timedelta
from django.utils import timezone
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.test.utils import CaptureQueriesContext
from django.db import connection
from social.models import Friendship, Badge
from habits.models import Habit, HabitCompletion
from social.services.badges.badge_service import BadgeService
from applications.models import Application, Contact

class TestBadgeService(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.service = BadgeService(self.user)
        self.today = timezone.localtime(timezone.now()).date()

    def test_health_streak_badge(self):
        # Test 7-day streak badge for health habits
        habit = Habit.objects.create(
            user=self.user, name="Exercise", frequency="daily", category="health"
        )

        # Create 7-day streak
        for i in range(7):
            HabitCompletion.objects.create(
                habit=habit, completed_at=self.today - timedelta(days=i)
            )

        self.service.check_streak_badges()
        self.assertTrue(
            Badge.objects.filter(user=self.user, badge_type="health_7_day").exists()
        )

    def test_learning_streak_badge(self):
        # Test 7-day streak badge for learning habits
        habit = Habit.objects.create(
            user=self.user, name="Study", frequency="daily", category="learning"
        )

        # Create 7-day streak
        for i in range(7):
            HabitCompletion.objects.create(
                habit=habit, completed_at=self.today - timedelta(days=i)
            )

        self.service.check_streak_badges()
        self.assertTrue(
            Badge.objects.filter(user=self.user, badge_type="learning_7_day").exists()
        )

    def test_productivity_streak_badge(self):
        # Test 7-day streak badge for productivity habits
        habit = Habit.objects.create(
            user=self.user, name="Work", frequency="daily", category="productivity"
        )

        # Create 7-day streak
        for i in range(7):
            HabitCompletion.objects.create(
                habit=habit, completed_at=self.today - timedelta(days=i)
            )

        self.service.check_streak_badges()
        self.assertTrue(
            Badge.objects.filter(
                user=self.user, badge_type="productivity_7_day"
            ).exists()
        )

    def test_weekly_habits_dont_count_for_streaks(self):
        # Test that weekly habits don't contribute to streak badges
        habit = Habit.objects.create(
            user=self.user,
            name="Weekly Exercise",
            frequency="weekly",
            category="health",
        )

        # Create completions for 7 consecutive weeks
        for i in range(7):
            HabitCompletion.objects.create(
                habit=habit, completed_at=self.today - timedelta(weeks=i)
            )

        self.service.check_streak_badges()
        self.assertFalse(
            Badge.objects.filter(user=self.user, badge_type="health_7_day").exists()
        )

    def test_first_friend_badge(self):
        # Test that making a friend awards the badge
        friend = get_user_model().objects.create_user(
            username="friend", password="testpass123"
        )

        # Create accepted friendship
        Friendship.objects.create(sender=self.user, receiver=friend, status="accepted")

        self.service.check_social_badges()
        self.assertTrue(
            Badge.objects.filter(user=self.user, badge_type="first_friend").exists()
        )

    def test_completion_badges_mixed_habits(self):
        # Test completion badges work with mix of daily and weekly habits
        # Create one daily and one weekly habit
        daily_habit = Habit.objects.create(
            user=self.user, name="Daily Exercise", frequency="daily"
        )
        weekly_habit = Habit.objects.create(
            user=self.user, name="Weekly Review", frequency="weekly"
        )

        # Create 6 daily completions
        for i in range(6):
            HabitCompletion.objects.create(
                habit=daily_habit, completed_at=self.today - timedelta(days=i)
            )

        # Create 4 weekly completions
        for i in range(4):
            HabitCompletion.objects.create(
                habit=weekly_habit, completed_at=self.today - timedelta(weeks=i)
            )

        # Should have 10 total completions (6 daily + 4 weekly)
        self.service.check_completion_badges()
        self.assertTrue(
            Badge.objects.filter(user=self.user, badge_type="completions_10").exists()
        )

    def test_mixed_completion_rates_daily(self):
        # Test completion rates with multiple daily habits at different completion levels
        # Create three daily habits
        habits = [
            Habit.objects.create(
                user=self.user, name=f"Daily Habit {i}", frequency="daily"
            )
            for i in range(3)
        ]

        # First habit: 2/3 days completed
        for i in range(2):
            HabitCompletion.objects.create(
                habit=habits[0], completed_at=self.today - timedelta(days=i)
            )

        # Second habit: 1/3 days completed
        HabitCompletion.objects.create(habit=habits[1], completed_at=self.today)

        # Third habit: 0/3 days completed

        # Should have 3 total completions out of 9 possible (3 habits × 3 days)
        self.service.check_completion_badges()
        self.assertFalse(
            Badge.objects.filter(user=self.user, badge_type="completions_10").exists()
        )

    def test_mixed_completion_rates_weekly(self):
        # Test completion rates with multiple weekly habits at different completion levels
        # Create three weekly habits
        habits = [
            Habit.objects.create(
                user=self.user, name=f"Weekly Habit {i}", frequency="weekly"
            )
            for i in range(3)
        ]

        # First habit: completed last 3 weeks
        for i in range(3):
            HabitCompletion.objects.create(
                habit=habits[0], completed_at=self.today - timedelta(weeks=i)
            )

        # Second habit: completed only this week
        HabitCompletion.objects.create(habit=habits[1], completed_at=self.today)

        # Third habit: no completions

        # Should have 4 completions total
        self.service.check_completion_badges()
        self.assertFalse(
            Badge.objects.filter(user=self.user, badge_type="completions_10").exists()
        )

    def test_mixed_completion_rates_combined(self):
        # Test completion rates with mix of daily and weekly habits at different completion levels
        # Create two daily habits
        daily_habits = [
            Habit.objects.create(
                user=self.user, name=f"Daily Habit {i}", frequency="daily"
            )
            for i in range(2)
        ]

        # Create two weekly habits
        weekly_habits = [
            Habit.objects.create(
                user=self.user, name=f"Weekly Habit {i}", frequency="weekly"
            )
            for i in range(2)
        ]

        # First daily habit: 3/5 days completed
        for i in range(3):
            HabitCompletion.objects.create(
                habit=daily_habits[0], completed_at=self.today - timedelta(days=i)
            )

        # Second daily habit: 2/5 days completed
        for i in range(2):
            HabitCompletion.objects.create(
                habit=daily_habits[1], completed_at=self.today - timedelta(days=i)
            )

        # First weekly habit: completed last 2 weeks
        for i in range(2):
            HabitCompletion.objects.create(
                habit=weekly_habits[0], completed_at=self.today - timedelta(weeks=i)
            )

        # Second weekly habit: no completions

        # Should have 7 completions total (3 + 2 + 2 + 0)
        self.service.check_completion_badges()
        self.assertFalse(
            Badge.objects.filter(user=self.user, badge_type="completions_10").exists()
        )

        # Add 3 more completions to get to 10
        for i in range(3):
            HabitCompletion.objects.create(
                habit=weekly_habits[1], completed_at=self.today - timedelta(weeks=i)
            )

        # Now should have 10 completions and get the badge
        self.service.check_completion_badges()
        self.assertTrue(
            Badge.objects.filter(user=self.user, badge_type="completions_10").exists()
        )

    def test_badge_check_query_efficiency(self):
        # Test that badge checking is efficient
        with CaptureQueriesContext(connection) as context:
            service = BadgeService(self.user)
            service.check_all_badges()

            # Badge checks should be optimized
            self.assertLess(len(context.captured_queries), 8)

    def test_applications_5_badge(self):
        # Create 4 applications
        for i in range(4):
            Application.objects.create(
                user=self.user,
                company=f"Company {i}",
                title=f"Position {i}",
                status="wishlist"
            )
        
        self.service.check_application_badges()
        self.assertFalse(
            Badge.objects.filter(
                user=self.user,
                badge_type='applications_5'
            ).exists()
        )

        # Create 5th application
        Application.objects.create(
            user=self.user,
            company="Company 5",
            title="Position 5",
            status="wishlist"
        )

        self.service.check_application_badges()
        self.assertTrue(
            Badge.objects.filter(
                user=self.user,
                badge_type='applications_5'
            ).exists()
        )

    def test_applied_5_badge(self):
        # Create 4 applied applications
        for i in range(4):
            Application.objects.create(
                user=self.user,
                company=f"Company {i}",
                title=f"Position {i}",
                status="applied"
            )
        
        self.service.check_application_badges()
        self.assertFalse(
            Badge.objects.filter(
                user=self.user,
                badge_type='applied_5'
            ).exists()
        )

        # Create 5th applied application
        Application.objects.create(
            user=self.user,
            company="Company 5",
            title="Position 5",
            status="applied"
        )

        self.service.check_application_badges()
        self.assertTrue(
            Badge.objects.filter(
                user=self.user,
                badge_type='applied_5'
            ).exists()
        )

    def test_job_offered_badge(self):
        # Create non-offered application
        Application.objects.create(
            user=self.user,
            company="Company",
            title="Position",
            status="applied"
        )
        
        self.service.check_application_badges()
        self.assertFalse(
            Badge.objects.filter(
                user=self.user,
                badge_type='job_offered'
            ).exists()
        )

        # Create offered application
        Application.objects.create(
            user=self.user,
            company="Dream Co",
            title="Dream Job",
            status="offered"
        )

        self.service.check_application_badges()
        self.assertTrue(
            Badge.objects.filter(
                user=self.user,
                badge_type='job_offered'
            ).exists()
        )

    def test_first_contact_badge(self):
        self.service.check_contact_badges()
        self.assertFalse(
            Badge.objects.filter(
                user=self.user,
                badge_type='first_contact'
            ).exists()
        )

        # Create first contact
        Contact.objects.create(
            user=self.user,
            name="John Doe",
            company="Tech Co",
            role="recruiter"
        )

        self.service.check_contact_badges()
        self.assertTrue(
            Badge.objects.filter(
                user=self.user,
                badge_type='first_contact'
            ).exists()
        )

    def test_wishlist_expired_badge(self):
        # Create non-expired wishlist application
        Application.objects.create(
            user=self.user,
            company="Future Co",
            title="Future Position",
            status="wishlist",
            due=self.today + timedelta(days=1)
        )
        
        self.service.check_application_badges()
        self.assertFalse(
            Badge.objects.filter(
                user=self.user,
                badge_type='wishlist_expired'
            ).exists()
        )

        # Create expired wishlist application
        Application.objects.create(
            user=self.user,
            company="Past Co",
            title="Past Position",
            status="wishlist",
            due=self.today - timedelta(days=1)
        )

        self.service.check_application_badges()
        self.assertTrue(
            Badge.objects.filter(
                user=self.user,
                badge_type='wishlist_expired'
            ).exists()
        )

    def test_badges_other_user(self):
        """Test that badges aren't awarded for other users' actions"""
        other_user = get_user_model().objects.create_user(
            username='otheruser',
            password='testpass123'
        )

        # Create 5 applications for other user
        for i in range(5):
            Application.objects.create(
                user=other_user,
                company=f"Company {i}",
                title=f"Position {i}",
                status="applied"
            )

        self.service.check_application_badges()
        self.assertFalse(
            Badge.objects.filter(
                user=self.user,
                badge_type='applications_5'
            ).exists()
        )
        self.assertFalse(
            Badge.objects.filter(
                user=self.user,
                badge_type='applied_5'
            ).exists()
        )
