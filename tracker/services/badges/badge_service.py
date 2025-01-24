from django.db.models import Q
from ...models import Badge, Habit, HabitCompletion
import logging

logger = logging.getLogger(__name__)

class BadgeService:
    def __init__(self, user):
        self.user = user

    def check_all_badges(self):
        """Check all possible badges for the user"""
        self.check_completion_badges()
        self.check_social_badges()
        self.check_streak_badges()

    def check_social_badges(self):
        """Check and award social badges"""
        from social.models import Friendship
        
        # Check for first friend badge
        has_friends = Friendship.objects.filter(
            (Q(sender=self.user) | Q(receiver=self.user)),
            status='accepted'
        ).exists()
        
        if has_friends:
            self._award_badge('first_friend')

    def check_completion_badges(self):
        """Check and award completion-based badges"""
        # Get total completions and per-habit counts in one query
        total_completions = HabitCompletion.objects.filter(
            habit__user=self.user
        ).count()

        logger.info(f"Checking completion badges for {self.user.username}")
        logger.info(f"Total completions: {total_completions}")
        
        # Check each threshold - order matters to log all eligible badges
        if total_completions >= 100:
            self._award_badge('completions_100')
        if total_completions >= 50:
            self._award_badge('completions_50')
        if total_completions >= 10:
            self._award_badge('completions_10')

    def check_streak_badges(self):
        """Check and award streak-based badges"""
        habits = (Habit.objects
            .filter(user=self.user, frequency='daily')
            .prefetch_related('completions')
            .select_related('user'))
        
        logger.info(f"Checking streak badges for {self.user.username}")
        
        for category in ['health', 'learning', 'productivity']:
            category_habits = [h for h in habits if h.category == category]
            longest_streak = max((habit.current_streak() for habit in category_habits), default=0)
            
            logger.info(f"{category} longest streak: {longest_streak}")
            
            # Check each threshold - order matters to log all eligible badges
            if longest_streak >= 30:
                self._award_badge(f'{category}_30_day')
            if longest_streak >= 7:
                self._award_badge(f'{category}_7_day')

    def _award_badge(self, badge_type):
        """Award a badge if it hasn't been awarded yet. Once awarded, badges are permanent."""
        badge, created = Badge.objects.get_or_create(
            user=self.user,
            badge_type=badge_type
        )
        if created:
            logger.info(f"Awarded {badge_type} badge to {self.user.username}")
        return badge 