import logging
from django.db.models import Q, Count, Exists
from django.utils import timezone
from social.models import Badge
from habits.models import Habit, HabitCompletion
from jobhunt.models import Application, Contact

logger = logging.getLogger(__name__)

class BadgeService:
    def __init__(self, user):
        self.user = user

    def check_all_badges(self):
        """Check all possible badges for the user"""
        self.check_completion_badges()
        self.check_social_badges()
        self.check_streak_badges()
        self.check_application_badges()
        self.check_contact_badges()

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
        
        for category in ['health', 'learning', 'productivity']:
            category_habits = [h for h in habits if h.category == category]
            longest_streak = max((habit.current_streak() for habit in category_habits), default=0)
            
            # Check each threshold - order matters to log all eligible badges
            if longest_streak >= 30:
                self._award_badge(f'{category}_30_day')
            if longest_streak >= 7:
                self._award_badge(f'{category}_7_day')

    def check_application_badges(self):
        """Check and award job application badges"""
        # Get all applications in one query with annotations
        applications = Application.objects.filter(user=self.user)
        total_count = applications.count()
        
        if total_count >= 5:
            self._award_badge('applications_5')

        # Get counts and flags for other badges
        status_stats = applications.aggregate(
            applied_count=Count('id', filter=Q(status='applied')),
            has_offer=Count('id', filter=Q(status='offered')),
            has_expired_wishlist=Count(
                'id',
                filter=Q(
                    status='wishlist',
                    due__lt=timezone.localtime(timezone.now()).date()
                )
            )
        )

        if status_stats['applied_count'] >= 5:
            self._award_badge('applied_5')
        
        if status_stats['has_offer'] > 0:
            self._award_badge('job_offered')
            
        if status_stats['has_expired_wishlist'] > 0:
            self._award_badge('wishlist_expired')

    def check_contact_badges(self):
        """Check and award contact badges"""
        has_contact = Contact.objects.filter(user=self.user).exists()
        if has_contact:
            self._award_badge('first_contact')

    def _award_badge(self, badge_type):
        """Award a badge if it hasn't been awarded yet. Once awarded, badges are permanent."""
        Badge.objects.get_or_create(
            user=self.user,
            badge_type=badge_type
        )
