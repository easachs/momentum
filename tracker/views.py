from django.urls import reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from .models import Habit


class HabitListView(ListView):
    model = Habit
    template_name = "tracker/habit_list.html"  # Rails equivalent: index.html.erb


class HabitDetailView(DetailView):
    model = Habit
    template_name = "tracker/habit_detail.html"  # Rails equivalent: show.html.erb


class HabitCreateView(CreateView):
    model = Habit
    fields = ["name", "description", "frequency", "category"]  # Form fields
    template_name = "tracker/habit_form.html"  # Rails equivalent: new.html.erb
    success_url = reverse_lazy('tracker:habit_list')


class HabitUpdateView(UpdateView):
    model = Habit
    fields = ["name", "description", "frequency", "category"]
    template_name = "tracker/habit_form.html"  # Rails equivalent: edit.html.erb
    success_url = reverse_lazy('tracker:habit_list')


class HabitDeleteView(DeleteView):
    model = Habit
    template_name = "tracker/habit_confirm_delete.html"
    success_url = reverse_lazy("tracker:habit_list")  # Rails equivalent: `redirect_to`