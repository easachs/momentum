from django.db import models
from django.conf import settings
from django.urls import reverse

class Food(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='foods'
    )
    date = models.DateField()
    name = models.CharField(max_length=200)
    calories = models.IntegerField()
    protein = models.IntegerField()
    carbs = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date']),
        ]

    def __str__(self):
        return f"{self.name} ({self.date})"

    def get_absolute_url(self):
        return reverse('nutrition:food_detail', kwargs={'pk': self.pk})

class Weight(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='weights'
    )
    date = models.DateField(unique=True)
    weight = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', 'date']),
        ]

    def __str__(self):
        return f"{self.weight}lbs on {self.date}"
