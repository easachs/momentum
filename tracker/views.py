from django.urls import reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
from allauth.socialaccount.providers.google.views import oauth2_login

from .models import Habit


class HabitListView(LoginRequiredMixin, ListView):
    model = Habit
    template_name = "tracker/habit_list.html"  # Rails equivalent: index.html.erb


class HabitDetailView(LoginRequiredMixin, DetailView):
    model = Habit
    template_name = "tracker/habit_detail.html"  # Rails equivalent: show.html.erb


class HabitCreateView(LoginRequiredMixin, CreateView):
    model = Habit
    fields = ["name", "description", "frequency", "category"]  # Form fields
    template_name = "tracker/habit_form.html"  # Rails equivalent: new.html.erb
    success_url = reverse_lazy('tracker:habit_list')


class HabitUpdateView(LoginRequiredMixin, UpdateView):
    model = Habit
    fields = ["name", "description", "frequency", "category"]
    template_name = "tracker/habit_form.html"  # Rails equivalent: edit.html.erb
    success_url = reverse_lazy('tracker:habit_list')


class HabitDeleteView(LoginRequiredMixin, DeleteView):
    model = Habit
    template_name = "tracker/habit_confirm_delete.html"
    success_url = reverse_lazy("tracker:habit_list")  # Rails equivalent: `redirect_to`


class CustomLoginView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('tracker:habit_list')
        return oauth2_login(request, 'google')