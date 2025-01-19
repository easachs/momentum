from django.db import models
from django.core.validators import MinLengthValidator
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from tracker.templatetags.markdown_filters import markdown_filter


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
    created_at = models.DateTimeField(auto_now_add=True)

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
        # Default parameter handling (Ruby: date = Time.current.to_date)
        if date is None:
            date = timezone.now().date()
        # exists? in Rails
        return self.completions.filter(completed_at=date).exists()

    def toggle_completion(self, date=None):
        # find_or_create_by in Rails
        if date is None:
            date = timezone.now().date()
        completion, created = self.completions.get_or_create(completed_at=date)
        if not created:
            completion.delete()
        return created

    def current_streak(self):
        # Complex business logic method
        # Similar to how you'd write it in Ruby, but with Python syntax
        today = timezone.now().date()
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
        today = timezone.now().date()
        days_since_creation = (today - self.created_at.date()).days + 1  # +1 to include today
        
        if self.frequency == 'daily':
            return days_since_creation
        else:  # weekly
            # Calculate full weeks since creation, rounding up if there's a partial week
            return (days_since_creation + 6) // 7  # Using integer division to round up


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
        # Compound unique index - Rails: add_index :habit_completions, [:habit_id, :completed_at], unique: true
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