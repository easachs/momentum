from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from django.core.exceptions import ValidationError

class Book(models.Model):
    STATUS_CHOICES = [
        ('TBR', 'To Be Read'),
        ('RDG', 'Reading'),
        ('CMP', 'Completed'),
        ('DNF', 'Did Not Finish')
    ]

    GENRE_CHOICES = [
        ('FIC', 'Fiction'),
        ('NON', 'Non-Fiction')
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='books'
    )
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True)
    pages = models.PositiveIntegerField(null=True, blank=True)
    genre = models.CharField(
        max_length=3,
        choices=GENRE_CHOICES,
        default='FIC'
    )
    date_started = models.DateField(null=True, blank=True)
    date_finished = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=3,
        choices=STATUS_CHOICES,
        default='TBR'
    )
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1, 'Rating must be between 1 and 5'),
            MaxValueValidator(5, 'Rating must be between 1 and 5')
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_started', '-date_finished', 'title']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'date_started']),
            models.Index(fields=['user', 'date_finished']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def get_absolute_url(self):
        return reverse('books:book_detail', kwargs={'pk': self.pk})

    def clean(self):
        # Validate dates
        if self.date_started and self.date_finished:
            if self.date_finished < self.date_started:
                raise ValidationError({
                    'date_finished': 'Finish date cannot be before start date'
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
