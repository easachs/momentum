from django.db import models
from django.conf import settings

class Friendship(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined')
    ]

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='sent_friendships',
        on_delete=models.CASCADE
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='received_friendships',
        on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name='rejected_friendships',
        on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('sender', 'receiver')

    def __str__(self):
        return f"{self.sender} -> {self.receiver} ({self.status})"

class Badge(models.Model):
    BADGE_CHOICES = [
        # Completion badges
        ("completions_10", "10 Completions"),
        ("completions_50", "50 Completions"),
        ("completions_100", "100 Completions"),
        # Streak badges
        ("health_7_day", "7 Day Health Streak"),
        ("health_30_day", "30 Day Health Streak"),
        ("learning_7_day", "7 Day Learning Streak"),
        ("learning_30_day", "30 Day Learning Streak"),
        ("productivity_7_day", "7 Day Productivity Streak"),
        ("productivity_30_day", "30 Day Productivity Streak"),
        # Social badges
        ("first_friend", "Made a Friend"),
        # New job application badges
        ("applications_5", "5 Applications Created"),
        ("applied_5", "5 Applications Submitted"),
        ("job_offered", "Job Offer Received"),
        ("first_contact", "First Contact Added"),
        ("wishlist_expired", "Wishlist Item Expired"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    badge_type = models.CharField(max_length=50, choices=BADGE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "badge_type")

    def __str__(self):
        return f"{self.get_badge_type_display()} - {self.user.username}"

    @classmethod
    def get_user_highest_badges(cls, user):
        """Get the highest badge for each category for a user"""
        badges = cls.objects.filter(user=user)
        highest_badges = {
            "health": None,
            "learning": None,
            "productivity": None,
            "friend": None,
            "completions": None,
            # Add job application badges
            "applications": None,
            "applied": None,
            "offered": None,
            "contact": None,
            "wishlist": None,
        }

        # Check streak badges
        for category in ["health", "learning", "productivity"]:
            if badges.filter(badge_type=f"{category}_30_day").exists():
                highest_badges[category] = f"{category}_30_day"
            elif badges.filter(badge_type=f"{category}_7_day").exists():
                highest_badges[category] = f"{category}_7_day"

        # Check friend badge
        if badges.filter(badge_type="first_friend").exists():
            highest_badges["friend"] = "first_friend"

        # Check completion badges
        if badges.filter(badge_type="completions_100").exists():
            highest_badges["completions"] = "completions_100"
        elif badges.filter(badge_type="completions_50").exists():
            highest_badges["completions"] = "completions_50"
        elif badges.filter(badge_type="completions_10").exists():
            highest_badges["completions"] = "completions_10"

        # Check job application badges
        if badges.filter(badge_type="applications_5").exists():
            highest_badges["applications"] = "applications_5"
        if badges.filter(badge_type="applied_5").exists():
            highest_badges["applied"] = "applied_5"
        if badges.filter(badge_type="job_offered").exists():
            highest_badges["offered"] = "job_offered"
        if badges.filter(badge_type="first_contact").exists():
            highest_badges["contact"] = "first_contact"
        if badges.filter(badge_type="wishlist_expired").exists():
            highest_badges["wishlist"] = "wishlist_expired"

        return highest_badges
