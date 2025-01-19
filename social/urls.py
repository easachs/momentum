from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    path('friend-request/<str:username>/', views.send_friend_request, name='send_friend_request'),
    path('friend-request/<int:friendship_id>/<str:action>/', views.handle_friend_request, name='handle_friend_request'),
] 