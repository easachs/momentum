from django.urls import reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect

from .models import Habit


class HabitListView(LoginRequiredMixin, ListView):
    model = Habit
    template_name = "tracker/habit_list.html"  # Rails equivalent: index.html.erb
    context_object_name = 'habits'

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)


class HabitDetailView(LoginRequiredMixin, DetailView):
    model = Habit
    template_name = "tracker/habit_detail.html"  # Rails equivalent: show.html.erb

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)


class HabitCreateView(LoginRequiredMixin, CreateView):
    model = Habit
    fields = ["name", "description", "frequency", "category"]  # Form fields
    template_name = "tracker/habit_form.html"  # Rails equivalent: new.html.erb
    success_url = reverse_lazy('tracker:habit_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class HabitUpdateView(LoginRequiredMixin, UpdateView):
    model = Habit
    fields = ["name", "description", "frequency", "category"]
    template_name = "tracker/habit_form.html"  # Rails equivalent: edit.html.erb
    success_url = reverse_lazy('tracker:habit_list')

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)


class HabitDeleteView(LoginRequiredMixin, DeleteView):
    model = Habit
    template_name = "tracker/habit_confirm_delete.html"
    success_url = reverse_lazy("tracker:habit_list")  # Rails equivalent: `redirect_to`

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)