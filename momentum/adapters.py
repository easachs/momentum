from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect

class NoNewUsersAccountAdapter(DefaultAccountAdapter):
    """Disable regular registration and login."""
    def is_open_for_signup(self, request):
        return False

    def login(self, request, user):
        # Use the parent class's login method
        return super().login(request, user)

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Only allow Google authentication."""
    def is_open_for_signup(self, request, sociallogin):
        return sociallogin.account.provider == 'google' 