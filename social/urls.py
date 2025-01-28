from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    path('friends/', views.FriendsListView.as_view(), name='friends_list'),
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),
    path('friend-request/<str:username>/',
         views.FriendRequestView.as_view(), name='send_friend_request'),
    path('handle-request/<int:friendship_id>/<str:action>/',
         views.HandleFriendRequestView.as_view(), name='handle_friend_request'),
    path('unfriend/<int:friendship_id>/', views.UnfriendView.as_view(), name='unfriend'),
    path('<str:username>/', views.DashboardView.as_view(), name='dashboard')
]
