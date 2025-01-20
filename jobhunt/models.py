from django.db import models
from django.contrib.auth import get_user_model

class Application(models.Model):
    STATUS_CHOICES = [
        ('wishlist', 'Wishlist'),
        ('applied', 'Applied'),
        ('interviewing', 'Interviewing'),
        ('offered', 'Offered'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='applications',
        null=False,
        blank=False
    )

    company = models.CharField(
        max_length=255,
        null=False,
        blank=False
    )
    job_title = models.CharField(
        max_length=255,
        null=False,
        blank=False
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='wishlist'
    )

    job_link = models.URLField(blank=True, null=True)

    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.job_title} at {self.company}"