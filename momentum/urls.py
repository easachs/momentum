"""
URL configuration for momentum project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from allauth.socialaccount.providers.google.views import oauth2_login, oauth2_callback
from django.shortcuts import redirect
from django.contrib.auth.decorators import user_passes_test
from tracker.views import root_redirect

# Redirect admin login to Google OAuth
admin.site.login = lambda request, **kwargs: redirect('google_oauth2_login')

urlpatterns = [
    # Add the root URL pattern
    path('', root_redirect, name='root'),
    
    # Direct Google OAuth URLs
    path('accounts/google/login/', oauth2_login, name='google_oauth2_login'),
    path('accounts/google/login/callback/', oauth2_callback, name='google_oauth2_callback'),
    path('accounts/', include('allauth.urls')),
    path('admin/', admin.site.urls),
    path('social/', include('social.urls')),
    path('', include('tracker.urls')),
    path("__reload__/", include("django_browser_reload.urls")),
]
