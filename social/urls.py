from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    path('friends/', views.friends_list, name='friends_list'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('friend-request/<str:username>/', views.send_friend_request, name='send_friend_request'),
    path('handle-request/<int:friendship_id>/<str:action>/', views.handle_friend_request, name='handle_friend_request'),
    path('unfriend/<int:friendship_id>/', views.unfriend, name='unfriend'),
] 