from django.db.models.signals import post_save
from django.dispatch import receiver
from social.services.badges.badge_service import BadgeService
from .models import Application

@receiver(post_save, sender=Application)
def check_application_badges(instance, **kwargs):
    """Check badges when an application is created or updated"""
    badge_service = BadgeService(instance.user)
    badge_service.check_application_badges()
