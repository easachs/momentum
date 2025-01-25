from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

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
    title = models.CharField(
        max_length=255,
        null=False,
        blank=False
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    due = models.DateField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='wishlist'
    )

    link = models.URLField(
        blank=True, 
        null=True
    )

    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} at {self.company}"

    def save(self, *args, **kwargs):
        # Check if this is a new instance
        is_new = self._state.adding
        
        # Get the old status if this is an existing instance
        if not is_new:
            old_status = Application.objects.get(pk=self.pk).status
        else:
            old_status = 'wishlist'  # For new instances, old status is wishlist
        
        # Save the application
        super().save(*args, **kwargs)
        
        # Create status change record if status changed
        if old_status != self.status:
            # Only skip status change for new wishlist applications
            if not (is_new and self.status == 'wishlist'):
                StatusChange.objects.create(
                    application=self,
                    old_status=old_status,
                    new_status=self.status
                )

    def is_due_soon(self):
        if not self.due:
            return False
        return self.due - timezone.now().date() <= timedelta(days=7)

    @classmethod
    def get_analytics(cls, user):
        """Get application analytics for dashboard"""
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        total = cls.objects.filter(user=user).count()  # Count ALL applications
        week = cls.objects.filter(user=user, created_at__gte=week_ago).count()
        month = cls.objects.filter(user=user, created_at__gte=month_ago).count()
        offers = cls.objects.filter(user=user, status='offered').count()

        return {
            'total': total,
            'week': week,
            'month': month,
            'offers': offers
        }

class StatusChange(models.Model):
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='status_changes'
    )
    old_status = models.CharField(
        max_length=15,
        choices=Application.STATUS_CHOICES,
        null=True,
        blank=True
    )
    new_status = models.CharField(
        max_length=15,
        choices=Application.STATUS_CHOICES
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['changed_at']

    def __str__(self):
        return f"{self.application}: {self.old_status or 'Initial'} → {self.new_status}"

class Contact(models.Model):
    ROLE_CHOICES = [
        ('hiring_manager', 'Hiring Manager'),
        ('reference', 'Reference'),
        ('recruiter', 'Recruiter'),
        ('interviewer', 'Interviewer'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contacts'
    )
    name = models.CharField(max_length=100)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='other'
    )
    company = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['user', 'email']  # Prevent duplicate contacts

    def __str__(self):
        return f"{self.name} ({self.get_role_display()} at {self.company})"