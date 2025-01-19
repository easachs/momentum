from django.db import models
from django.conf import settings
from django.urls import reverse

class Friendship(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined')
    ]
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='friendship_requests_sent',
        on_delete=models.CASCADE
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='friendship_requests_received',
        on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=8,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('sender', 'receiver')
        
    def __str__(self):
        return f"{self.sender} -> {self.receiver} ({self.status})" 