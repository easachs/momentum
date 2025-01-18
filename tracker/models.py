from django.db import models
from django.core.validators import MinLengthValidator
from django.urls import reverse


class Habit(models.Model):
    CATEGORY_CHOICES = [
        ("health", "Health"),
        ("productivity", "Productivity"),
        ("learning", "Learning"),
    ]

    name = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(3)],  # Ensures name has at least 3 characters
        unique=True,  # Prevents duplicate habit names
    )  # Similar to Rails `t.string :name`
    description = models.TextField(
        blank=True, null=True
    )  # Similar to Rails `t.text :description`
    frequency = models.CharField(
        max_length=10,
        choices=[("daily", "Daily"), ("weekly", "Weekly")],
        default="daily",
    )  # Like Rails enums with predefined choices
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="health",
    )  # Allows categorization of habits
    created_at = models.DateTimeField(
        auto_now_add=True
    )  # Rails equivalent: `t.timestamps`

    def __str__(self):
        return self.name  # For better readability in admin or shell

    def get_absolute_url(self):
        """
        Defines the default URL to redirect to when referring to this model.
        Redirects to the detail page for the habit.
        """
        return reverse("tracker:habit_detail", args=[self.pk])  # Uses the habit's primary key