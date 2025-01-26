from django import template
from social.models import Badge
from django.db.models import Q

register = template.Library()

@register.filter
def get_user_badges(user):
    """Get the highest badges for a user"""
    return Badge.get_user_highest_badges(user)
