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
        if self.pk:  # If this is an update
            old_instance = Application.objects.get(pk=self.pk)
            if old_instance.status != self.status:
                StatusChange.objects.create(
                    application=self,
                    old_status=old_instance.status,
                    new_status=self.status
                )
        elif self.status != 'wishlist':  # If this is a new instance not starting with wishlist
            # We'll create a status change after saving
            should_create_initial = True
        else:
            should_create_initial = False
        
        super().save(*args, **kwargs)
        
        # Create initial status change if needed
        if not self.pk and should_create_initial:
            StatusChange.objects.create(
                application=self,
                old_status=None,
                new_status=self.status
            )

    def is_due_soon(self):
        if not self.due:
            return False
        return self.due - timezone.now().date() <= timedelta(days=7)

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