from django.urls import reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.utils import timezone
from django.db.models import Count, Q

from .models import Habit


class HabitListView(LoginRequiredMixin, ListView):
    model = Habit
    template_name = "tracker/habit_list.html"
    context_object_name = 'habits_summary'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        start_of_week = today - timezone.timedelta(days=today.weekday())
        
        # Get habits and annotate with completion status for today and this week
        habits = Habit.objects.filter(user=self.request.user).annotate(
            completed_today=Count('completions', filter=Q(completions__completed_at=today)),
            completed_this_week=Count('completions', filter=Q(completions__completed_at__gte=start_of_week))
        )
        
        # Calculate streaks for each habit
        daily_habits = []
        weekly_habits = []
        
        for habit in habits:
            # Calculate the streak for each habit
            streak = habit.current_streak()
            habit.streak = streak  # Add streak as an attribute
            
            if habit.frequency == 'daily':
                daily_habits.append(habit)
            else:
                weekly_habits.append(habit)
        
        context['daily_habits'] = daily_habits
        context['weekly_habits'] = weekly_habits
        return context


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


@login_required
def toggle_habit_completion(request, pk):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    habit.toggle_completion()
    
    # Simply redirect back to the previous page
    referer = request.META.get('HTTP_REFERER')
    return redirect(referer) if referer else redirect('tracker:habit_detail', pk=pk)


class DashboardAndHabitListView(LoginRequiredMixin, ListView):
    model = Habit
    template_name = "tracker/dashboard_and_habit_list.html"
    context_object_name = 'habits_summary'

    def get_queryset(self):
        today = timezone.now().date()
        start_of_week = today - timezone.timedelta(days=today.weekday())
        
        # Get habits and annotate with completion status for today and this week
        return Habit.objects.filter(user=self.request.user).annotate(
            completed_today=Count('completions', filter=Q(completions__completed_at=today)),
            completed_this_week=Count('completions', filter=Q(completions__completed_at__gte=start_of_week))
        )