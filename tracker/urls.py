from django.urls import path

from . import views
from .views import HabitListView

app_name = "tracker"

urlpatterns = [
    path('<str:username>/', views.HabitListView.as_view(), name='habit_list'),
    path('<str:username>/habit/<int:pk>/', views.HabitDetailView.as_view(), name='habit_detail'),
    path('habit/create/', views.HabitCreateView.as_view(), name='habit_create'),
    path('habit/<int:pk>/update/', views.HabitUpdateView.as_view(), name='habit_update'),
    path('habit/<int:pk>/delete/', views.HabitDeleteView.as_view(), name='habit_delete'),
    path('habit/<int:pk>/toggle/', views.toggle_habit_completion, name='habit_completion_toggle'),
]
