from django.urls import path

from . import views

app_name = "tracker"

urlpatterns = [
    path("", views.HabitListView.as_view(), name="habit_list"),  # List habits
    path(
        "<int:pk>/", views.HabitDetailView.as_view(), name="habit_detail"
    ),  # Show habit
    path(
        "create/", views.HabitCreateView.as_view(), name="habit_create"
    ),  # Create habit
    path(
        "<int:pk>/update/", views.HabitUpdateView.as_view(), name="habit_update"
    ),  # Update habit
    path(
        "<int:pk>/delete/", views.HabitDeleteView.as_view(), name="habit_delete"
    ),  # Delete habit
    path('<int:pk>/toggle-completion/', views.toggle_habit_completion, name='habit_completion_toggle'),
]
