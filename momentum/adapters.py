from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect

class GoogleOnlyAdapter(DefaultSocialAccountAdapter):
    """Only allow Google authentication."""
    def is_open_for_signup(self, request, sociallogin):
        return sociallogin.account.provider == 'google'

    def pre_social_login(self, request, sociallogin):
        if sociallogin.account.provider != 'google':
            return redirect('google_oauth2_login')

    def get_connect_redirect_url(self, request, socialaccount):
        return oauth2_login(request, 'google')
