from django.db import models
from django.core.validators import MinLengthValidator
from django.urls import reverse
from django.contrib.auth import get_user_model


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
        return reverse("tracker:habit_detail", args=[self.pk])