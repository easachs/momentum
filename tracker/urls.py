from django.urls import path

from . import views

app_name = "tracker"

urlpatterns = [
    path('habits/', views.HabitListView.as_view(), name='habit_list'),
    path('habits/create/', views.HabitCreateView.as_view(), name='habit_create'),
    path('habits/<int:pk>/', views.HabitDetailView.as_view(), name='habit_detail'),
    path('habits/<int:pk>/edit/', views.HabitUpdateView.as_view(), name='habit_update'),
    path('habits/<int:pk>/delete/', views.HabitDeleteView.as_view(), name='habit_delete'),
    path('habits/<int:pk>/toggle/', views.toggle_habit_completion, name='toggle_completion'),
    path('habits/ai-summary/', views.generate_ai_summary, name='generate_ai_summary'),
    path('<str:username>/', views.DashboardView.as_view(), name='dashboard'),
]
