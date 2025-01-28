from django.urls import path

from . import views

app_name = "tracker"

urlpatterns = [
    path('', views.HabitListView.as_view(), name='habit_list'),
    path('create/', views.HabitCreateView.as_view(), name='habit_create'),
    path('<int:pk>/', views.HabitDetailView.as_view(), name='habit_detail'),
    path('<int:pk>/edit/', views.HabitUpdateView.as_view(), name='habit_update'),
    path('<int:pk>/delete/', views.HabitDeleteView.as_view(), name='habit_delete'),
    path('<int:pk>/toggle/', views.toggle_habit_completion, name='toggle_completion'),
    path('ai-summary/', views.generate_ai_summary, name='generate_ai_summary')
]
