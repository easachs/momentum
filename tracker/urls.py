from django.urls import path

from . import views
from .views import HabitListView

app_name = "tracker"

urlpatterns = [
    path("", views.HabitListView.as_view(), name="habit_list"),
    path("<int:pk>/", views.HabitDetailView.as_view(), name="habit_detail"),
    path("create/", views.HabitCreateView.as_view(), name="habit_create"),
    path("<int:pk>/update/", views.HabitUpdateView.as_view(), name="habit_update"),
    path("<int:pk>/delete/", views.HabitDeleteView.as_view(), name="habit_delete"),
    path('<int:pk>/toggle-completion/', views.toggle_habit_completion, name='habit_completion_toggle'),
]
