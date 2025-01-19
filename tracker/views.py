from django.urls import reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Q
from django.db.models.functions import TruncWeek, TruncMonth

from .models import Habit, HabitCompletion


class HabitListView(LoginRequiredMixin, ListView):
    model = Habit
    template_name = "tracker/habit_list.html"
    context_object_name = 'habits_summary'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        start_of_week = today - timezone.timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)
        thirty_days_ago = today - timedelta(days=30)
        
        habits = Habit.objects.filter(user=self.request.user)
        
        # Add category filter
        selected_category = self.request.GET.get('category')
        if selected_category:
            habits = habits.filter(category=selected_category)
        
        # Get incomplete habits
        incomplete_daily = habits.filter(
            frequency='daily',
            completions__completed_at=today
        ).count()
        incomplete_weekly = habits.filter(
            frequency='weekly',
            completions__completed_at__gte=start_of_week
        ).count()
        
        context['notifications'] = {
            'incomplete_daily': habits.filter(frequency='daily').count() - incomplete_daily,
            'incomplete_weekly': habits.filter(frequency='weekly').count() - incomplete_weekly,
        }
        
        # Get completion analytics
        earliest_habit = habits.order_by('created_at').first()
        earliest_date = earliest_habit.created_at.date() if earliest_habit else today

        # Calculate total possible completions and actual completions
        total_possible = 0
        total_completions = 0
        for habit in habits:
            days_since_creation = (today - habit.created_at.date()).days + 1
            if habit.frequency == 'daily':
                total_possible += days_since_creation
            else:  # weekly
                total_possible += (days_since_creation + 6) // 7  # Round up to nearest week

            # Count actual completions for this habit
            completions = HabitCompletion.objects.filter(
                habit=habit,
                completed_at__gte=habit.created_at.date()
            ).count()
            total_completions += completions

        context['analytics'] = {
            'total_habits': habits.count(),
            'total_completions': total_completions,
            'completion_rate': (total_completions / total_possible * 100) if total_possible > 0 else 0,
            
            # Weekly summary
            'this_week_completions': HabitCompletion.objects.filter(
                habit__user=self.request.user,
                completed_at__gte=start_of_week
            ).count(),
            
            # Monthly summary
            'this_month_completions': HabitCompletion.objects.filter(
                habit__user=self.request.user,
                completed_at__gte=start_of_month
            ).count(),
        }

        # Complex query building (similar to Rails scopes)
        habits = habits.annotate(
            completed_today=Count('completions', filter=Q(completions__completed_at=today)),
            completed_this_week=Count('completions', filter=Q(completions__completed_at__gte=start_of_week))
        )
        
        # View mode handling (similar to Rails params[:view])
        view_mode = self.request.GET.get('view', 'frequency')
        context['view_mode'] = view_mode
        
        if view_mode == 'category':
            # Group by category
            categorized_habits = {}
            for category, label in Habit.CATEGORY_CHOICES:
                categorized_habits[category] = {
                    'label': label,
                    'habits': []
                }
            
            for habit in habits:
                habit.streak = habit.current_streak()
                categorized_habits[habit.category]['habits'].append(habit)
            
            context['categorized_habits'] = categorized_habits
        else:
            # Original frequency-based grouping
            daily_habits = []
            weekly_habits = []
            
            for habit in habits:
                habit.streak = habit.current_streak()
                if habit.frequency == 'daily':
                    daily_habits.append(habit)
                else:
                    weekly_habits.append(habit)
            
            context['daily_habits'] = daily_habits
            context['weekly_habits'] = weekly_habits
        
        # First, calculate total possible completions and actual completions per category
        category_stats = {}
        for category, _ in Habit.CATEGORY_CHOICES:
            category_stats[category] = {
                'total': 0,
                'completed': HabitCompletion.objects.filter(
                    habit__user=self.request.user,
                    habit__category=category
                ).count()
            }
            
            # Calculate total possible completions for this category
            for habit in habits.filter(category=category):
                days_since_creation = (today - habit.created_at.date()).days + 1
                if habit.frequency == 'daily':
                    category_stats[category]['total'] += days_since_creation
                else:  # weekly
                    category_stats[category]['total'] += (days_since_creation + 6) // 7

        # Add to analytics context
        context['analytics']['category_stats'] = [
            {
                'category': category,
                'total': stats['total'],
                'completed': stats['completed']
            }
            for category, stats in category_stats.items()
        ]
        
        # Add the rest of the analytics...
        context['analytics'].update({
            'daily_stats': HabitCompletion.objects.filter(
                habit__user=self.request.user,
                completed_at__gte=thirty_days_ago
            ).annotate(
                date=TruncWeek('completed_at')
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date'),
        })
        
        # Add category choices for filtering
        context['habit_categories'] = Habit.CATEGORY_CHOICES
        
        return context


class HabitDetailView(LoginRequiredMixin, DetailView):
    model = Habit
    template_name = "tracker/habit_detail.html"

    def get_queryset(self):
        # Only allow viewing own habits
        return Habit.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        start_of_week = today - timezone.timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)
        habit = self.get_object()

        # Calculate total possible completions and actual completions
        days_since_creation = (today - habit.created_at.date()).days + 1
        total_possible = days_since_creation if habit.frequency == 'daily' else (days_since_creation + 6) // 7

        completions = habit.completions.filter(completed_at__gte=habit.created_at.date()).count()
        
        context.update({
            'today': today,
            'yesterday': yesterday,
            'today_completion': HabitCompletion.objects.filter(
                habit=habit,
                completed_at=today
            ).exists(),
            'yesterday_completion': HabitCompletion.objects.filter(
                habit=habit,
                completed_at=yesterday
            ).exists(),
            'analytics': {
                'total_completions': completions,
                'total_possible': total_possible,
                'completion_rate': (completions / total_possible * 100) if total_possible > 0 else 0,
                'this_week_completions': habit.completions.filter(completed_at__gte=start_of_week).count(),
                'this_month_completions': habit.completions.filter(completed_at__gte=start_of_month).count(),
                'current_streak': habit.current_streak(),
                'longest_streak': habit.longest_streak(),
            }
        })
        return context


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
    date = request.POST.get('date')
    if date:
        habit.toggle_completion(timezone.datetime.strptime(date, '%Y-%m-%d').date())
    else:
        habit.toggle_completion()
    
    referer = request.META.get('HTTP_REFERER')
    return redirect(referer) if referer else redirect('tracker:habit_detail', pk=pk)