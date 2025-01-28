from django.urls import reverse

class NavigationService:
    @staticmethod
    def get_home_redirect_url(user):
        """Determine the appropriate home page URL for a user"""
        if user.is_authenticated:
            return reverse('social:dashboard', kwargs={'username': user.username})
        return reverse('account_login') 