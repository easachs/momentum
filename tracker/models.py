from django.db import models
from django.core.validators import MinLengthValidator
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone


class Habit(models.Model):
    CATEGORY_CHOICES = [
        ("health", "Health"),
        ("productivity", "Productivity"),
        ("learning", "Learning"),
    ]

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='habits',
        null=False,
        blank=False
    )
    name = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(3)]  # Ensures name has at least 3 characters
    )  # Similar to Rails `t.string :name`
    description = models.TextField(blank=True, null=True)
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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['name', 'user']  # This ensures name is unique per user

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tracker:habit_detail', args=[self.pk])

    def is_completed_for_date(self, date=None):
        if date is None:
            date = timezone.now().date()
        return self.completions.filter(completed_at=date).exists()

    def toggle_completion(self, date=None):
        if date is None:
            date = timezone.now().date()
        completion, created = self.completions.get_or_create(completed_at=date)
        if not created:
            completion.delete()
        return created


class HabitCompletion(models.Model):
    habit = models.ForeignKey(
        Habit,
        on_delete=models.CASCADE,
        related_name='completions'
    )
    completed_at = models.DateField()
    
    class Meta:
        unique_together = ['habit', 'completed_at']  # Prevent duplicate completions
        ordering = ['-completed_at']  # Most recent first

    def __str__(self):
        return f"{self.habit.name} completed on {self.completed_at}"