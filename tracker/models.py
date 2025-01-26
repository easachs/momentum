from datetime import timedelta
from django.db import models
from django.core.validators import MinLengthValidator
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

# Models in Django are similar to ActiveRecord models in Rails
# They inherit from models.Model instead of ApplicationRecord

class Habit(models.Model):
    # Enum-like choices - Similar to Rails enum but defined explicitly
    # In Rails this might be: enum category: { health: 0, productivity: 1, learning: 2 }
    CATEGORY_CHOICES = [
        ("health", "Health"),
        ("productivity", "Productivity"),
        ("learning", "Learning"),
    ]

    # ForeignKey is equivalent to belongs_to in Rails
    # on_delete=models.CASCADE is like dependent: :destroy
    # related_name='habits' creates the inverse has_many (like has_many :habits in User model)
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='habits',
        null=False,
        blank=False
    )

    # CharField is similar to t.string in Rails migrations
    # validators are like Rails validations but defined at the field level
    name = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(3)]  # Rails: validates :name, length: { minimum: 3 }
    )

    # TextField is like t.text in Rails
    # blank=True, null=True allows empty values (Rails: allows_nil: true)
    description = models.TextField(blank=True, null=True)

    # Choices field - another enum-like field
    # In Rails: enum frequency: { daily: 0, weekly: 1 }
    frequency = models.CharField(
        max_length=10,
        choices=[("daily", "Daily"), ("weekly", "Weekly")],
        default="daily",
    )

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="health",
    )

    # auto_now_add is like t.timestamps in Rails (for created_at)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        # Compound unique constraint - Rails: validates :name, uniqueness: { scope: :user_id }
        unique_together = ['name', 'user']

    # String representation - like def to_s in Ruby
    def __str__(self):
        return self.name

    # Similar to Rails' url helpers but more explicit
    def get_absolute_url(self):
        return reverse('tracker:habit_detail', kwargs={'pk': self.pk})

    # Instance methods - similar to Ruby instance methods
    def is_completed_for_date(self, date=None):
        if date is None:
            date = timezone.localtime(timezone.now()).date()

        if self.frequency == 'weekly':
            # For weekly habits, check if completed any time this week
            start_of_week = date - timedelta(days=date.weekday())
            return self.completions.filter(
                completed_at__gte=start_of_week,
                completed_at__lte=date
            ).exists()
        else:
            # For daily habits, check just this date
            return self.completions.filter(completed_at=date).exists()

    def toggle_completion(self, date=None):
        if date is None:
            date = timezone.localtime(timezone.now()).date()

        if self.frequency == 'weekly':
            # For weekly habits, find any completion this week
            start_of_week = date - timedelta(days=date.weekday())
            completion = self.completions.filter(
                completed_at__gte=start_of_week,
                completed_at__lte=date
            ).first()

            if completion:
                # If already completed this week, remove the completion
                completion.delete()
                return False
            else:
                # If not completed this week, create a completion
                self.completions.create(completed_at=date)
                return True
        else:
            # Handle daily habits as before
            completion, created = self.completions.get_or_create(completed_at=date)
            if not created:
                completion.delete()
            return created

    def current_streak(self):
        # Complex business logic method
        # Similar to how you'd write it in Ruby, but with Python syntax
        today = timezone.localtime(timezone.now()).date()
        streak = 0
        date = today

        if self.frequency == 'daily':
            # While loop is similar to Ruby's while
            while self.is_completed_for_date(date):
                streak += 1
                date -= timedelta(days=1)
        else:  # weekly
            current_week_start = today - timedelta(days=today.weekday())
            week_start = current_week_start

            while True:  # Ruby's loop do
                week_end = week_start + timedelta(days=6)
                if self.completions.filter(
                    completed_at__gte=week_start,
                    completed_at__lte=week_end
                ).exists():
                    streak += 1
                    week_start -= timedelta(days=7)
                else:
                    break

        return streak

    def longest_streak(self):
        """Calculate the longest streak of habit completions"""
        completions = self.completions.order_by('completed_at').values_list('completed_at', flat=True)
        if not completions:
            return 0

        longest = current = 1
        if self.frequency == 'daily':
            # No need to convert to dates since completed_at is already a date
            dates = list(completions)  # Convert queryset to list
            for i in range(1, len(dates)):
                if (dates[i] - dates[i-1]).days == 1:
                    current += 1
                    longest = max(longest, current)
                else:
                    current = 1
        else:  # weekly
            # Group completions by week
            week_completions = {}
            for completion in completions:
                # completion is already a date, so no need for .date()
                week_start = completion - timedelta(days=completion.weekday())
                week_completions[week_start] = True

            # Sort weeks and count consecutive ones
            weeks = sorted(week_completions.keys())
            for i in range(1, len(weeks)):
                if (weeks[i] - weeks[i-1]).days == 7:
                    current += 1
                    longest = max(longest, current)
                else:
                    current = 1

        return longest

    def get_total_possible_completions(self):
        """Calculate total possible completions since habit creation"""
        today = timezone.localtime(timezone.now()).date()
        created_at_date = self.created_at.date() if hasattr(self.created_at, 'date') else self.created_at
        days_since_creation = (today - created_at_date).days + 1
        
        if self.frequency == 'daily':
            return max(1, days_since_creation)
        else:  # weekly
            return max(1, (days_since_creation + 6) // 7)

    def get_current_week_completion(self):
        """Return completion for current week if it exists"""
        today = timezone.localtime(timezone.now()).date()
        start_of_week = today - timedelta(days=today.weekday())
        return self.completions.filter(
            completed_at__gte=start_of_week,
            completed_at__lte=today
        ).first()


# Join model - similar to a HABTM or has_many :through in Rails
class HabitCompletion(models.Model):
    # belongs_to :habit in Rails
    habit = models.ForeignKey(
        Habit,
        on_delete=models.CASCADE,  # dependent: :destroy
        related_name='completions'  # has_many :completions
    )
    completed_at = models.DateField()

    class Meta:
        # This ensures database-level uniqueness
        unique_together = ['habit', 'completed_at']
        # Default ordering - Rails: default_scope { order(completed_at: :desc) }
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.habit.name} completed on {self.completed_at}"

class AIHabitSummary(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class Badge(models.Model):
    BADGE_CHOICES = [
        # Completion badges
        ('completions_10', '10 Completions'),
        ('completions_50', '50 Completions'),
        ('completions_100', '100 Completions'),
        # Streak badges
        ('health_7_day', '7 Day Health Streak'),
        ('health_30_day', '30 Day Health Streak'),
        ('learning_7_day', '7 Day Learning Streak'),
        ('learning_30_day', '30 Day Learning Streak'),
        ('productivity_7_day', '7 Day Productivity Streak'),
        ('productivity_30_day', '30 Day Productivity Streak'),
        # Social badges
        ('first_friend', 'Made a Friend'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    badge_type = models.CharField(max_length=50, choices=BADGE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge_type')

    def __str__(self):
        return f"{self.get_badge_type_display()} - {self.user.username}"

    @classmethod
    def get_user_highest_badges(cls, user):
        """Get the highest badge for each category for a user"""
        badges = cls.objects.filter(user=user)
        highest_badges = {
            'health': None,
            'learning': None,
            'productivity': None,
            'friend': None,
            'completions': None
        }

        # Check streak badges
        for category in ['health', 'learning', 'productivity']:
            if badges.filter(badge_type=f'{category}_30_day').exists():
                highest_badges[category] = f'{category}_30_day'
            elif badges.filter(badge_type=f'{category}_7_day').exists():
                highest_badges[category] = f'{category}_7_day'

        # Check friend badge
        if badges.filter(badge_type='first_friend').exists():
            highest_badges['friend'] = 'first_friend'

        # Check completion badges
        if badges.filter(badge_type='completions_100').exists():
            highest_badges['completions'] = 'completions_100'
        elif badges.filter(badge_type='completions_50').exists():
            highest_badges['completions'] = 'completions_50'
        elif badges.filter(badge_type='completions_10').exists():
            highest_badges['completions'] = 'completions_10'

        return highest_badges
