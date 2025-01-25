from django.db import models
from django.urls import reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Q, Prefetch, Subquery, OuterRef, Case, When, Value
from django.db.models.functions import TruncWeek, TruncMonth, ExtractWeek
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
import logging

from .models import Habit, HabitCompletion, AIHabitSummary
from .services.ai.ai_service import AIHabitService
from tracker.templatetags.markdown.filters import markdown_filter
from .services.badges.badge_service import BadgeService

logger = logging.getLogger(__name__)


class HabitListView(LoginRequiredMixin, ListView):
    model = Habit
    template_name = "tracker/habit_list.html"
    context_object_name = 'habits'

    def get_queryset(self):
        from django.db.models import Value
        from django.db.models.functions import Cast
        
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)

        return (Habit.objects.filter(user=self.request.user)
            .select_related('user')
            .annotate(
                completed_today=Count('completions', 
                    filter=Q(completions__completed_at=Cast(Value(today), output_field=models.DateField()))),
                completed_this_week=Count('completions', 
                    filter=Q(completions__completed_at__gte=Cast(Value(start_of_week), output_field=models.DateField()))),
                month_count=Count('completions', 
                    filter=Q(completions__completed_at__gte=Cast(Value(start_of_month), output_field=models.DateField()))),
                total_completions=Count('completions'),
                # Add annotations for notifications
                needs_completion_daily=Case(
                    When(frequency='daily', completed_today=0, then=Value(1)),
                    default=Value(0),
                    output_field=models.IntegerField(),
                ),
                needs_completion_weekly=Case(
                    When(frequency='weekly', completed_this_week=0, then=Value(1)),
                    default=Value(0),
                    output_field=models.IntegerField(),
                )
            ).prefetch_related(
                'completions'  # Single prefetch for all completions we need
            ))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['viewed_user'] = self.request.user
        habits = self.get_queryset()
        
        # Add friendship status
        if self.request.user != self.request.user:
            friendship = Friendship.objects.filter(
                (Q(sender=self.request.user, receiver=self.request.user) |
                 Q(sender=self.request.user, receiver=self.request.user))
            ).first()
            
            context['friendship'] = friendship
        
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)
        thirty_days_ago = today - timedelta(days=30)
        
        
        # Add category filter
        selected_category = self.request.GET.get('category')
        if selected_category:
            habits = habits.filter(category=selected_category)

        context['notifications'] = {
            'incomplete_daily': habits.filter(frequency='daily').filter(completed_today=0).count(),
            'incomplete_weekly': habits.filter(frequency='weekly').filter(completed_this_week=0).count(),
        }

        habits_data = [
            {
                "name": habit.name,
                "category": habit.category,
                "frequency": habit.frequency,
                "completions_count": habit.total_completions,
                "possible_completions": habit.get_total_possible_completions(),
                "week_count": habit.completed_this_week,
                "month_count": habit.month_count,
                "streak_days": habit.current_streak(),
            }
            for habit in habits
        ]

        # Calculate totals
        total_completions = sum(h['completions_count'] for h in habits_data)
        total_possible = sum(h['possible_completions'] for h in habits_data)

        # Calculate category stats from the same data
        category_stats = []
        by_category = {}
        for habit in habits_data:
            cat = habit.get('category')
            if cat not in by_category:
                by_category[cat] = {'completed': 0, 'possible': 0, 'count': 0, 'streak': 0}
            by_category[cat]['completed'] += habit['completions_count']
            by_category[cat]['possible'] += habit['possible_completions']
            by_category[cat]['count'] += 1
            by_category[cat]['streak'] = max(by_category[cat]['streak'], habit['streak_days'])

        for category, data in by_category.items():
            if data['possible'] > 0:  # Only add categories with possible completions
                category_stats.append({
                    'category': category,
                    'completed': data['completed'],
                    'total': data['possible'],
                    'habit_count': data['count'],
                    'percentage': round(
                        data['completed'] * 100 / data['possible'], 1
                    )
                })

        # Get habits for the template
        context['object_list'] = habits  # Use the same queryset we already have

        context['habit_analytics'] = {
            'total_habits': len(habits_data),
            'completion_rate': round(
                total_completions * 100 / total_possible if total_possible > 0 else 0.0, 1
            ),
            'this_week_completions': sum(h['week_count'] for h in habits_data),
            'this_month_completions': sum(h['month_count'] for h in habits_data),
            'category_stats': category_stats,
            'best_streak': max((h['streak_days'] for h in habits_data), default=0),
            'habits': habits
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
            context['has_any_habits'] = any(data['habits'] for data in categorized_habits.values())
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
        
        # Add the rest of the analytics...
        context['analytics'] = {
            'total_completions': total_completions,
            'category_stats': category_stats,
            'this_week_completions': sum(h['week_count'] for h in habits_data),
            'total_possible': total_possible,
            'completion_rate': round(
                total_completions * 100 / total_possible if total_possible > 0 else 0.0, 1
            )
        }

        # Add category choices for filtering
        context['habit_categories'] = Habit.CATEGORY_CHOICES

        # Add latest AI summary to context
        if self.request.user == self.request.user:
            context['latest_summary'] = AIHabitSummary.objects.filter(
                user=self.request.user
            ).first()

        return context


class HabitDetailView(LoginRequiredMixin, DetailView):
    model = Habit
    template_name = "tracker/habit_detail.html"

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user).prefetch_related(
            Prefetch(
                'completions',
                queryset=HabitCompletion.objects.filter(
                    completed_at__gte=timezone.now().date() - timedelta(days=30)
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        start_of_week = today - timedelta(days=today.weekday())
        habit = self.get_object()
        
        # Get all needed completions in one query
        completions_qs = habit.completions.all()  # Already prefetched
        
        # Check for completion based on habit frequency
        if habit.frequency == 'weekly':
            today_completed = any(
                c.completed_at >= start_of_week and c.completed_at <= today 
                for c in completions_qs
            )
        else:  # daily
            today_completed = any(c.completed_at == today for c in completions_qs)

        context.update({
            'today': today,
            'yesterday': yesterday,
            'today_completion': today_completed,
            'yesterday_completion': any(c.completed_at == yesterday for c in completions_qs),
            'analytics': {
                'total_completions': completions_qs.count(),
                'total_possible': habit.get_total_possible_completions(),
                'this_week_completions': sum(1 for c in completions_qs if c.completed_at >= start_of_week),
                'this_month_completions': sum(1 for c in completions_qs if c.completed_at.month == today.month),
                'current_streak': habit.current_streak(),
                'longest_streak': habit.longest_streak(),
            }
        })
        return context

    def _get_habit_analytics(self, habit):
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)
        
        # Calculate total possible completions and actual completions
        days_since_creation = (today - habit.created_at.date()).days + 1
        total_possible = days_since_creation if habit.frequency == 'daily' else (days_since_creation + 6) // 7
        
        completions = habit.completions.filter(completed_at__gte=habit.created_at.date()).count()
        
        return {
            'total_completions': completions,
            'total_possible': total_possible,
            'completion_rate': (completions / total_possible * 100) if total_possible > 0 else 0,
            'this_week_completions': habit.completions.filter(completed_at__gte=start_of_week).count(),
            'this_month_completions': habit.completions.filter(completed_at__gte=start_of_month).count(),
            'current_streak': habit.current_streak(),
            'longest_streak': habit.longest_streak(),
        }


class HabitCreateView(LoginRequiredMixin, CreateView):
    model = Habit
    fields = ["name", "description", "frequency", "category"]
    template_name = "tracker/habit_form.html"

    def get_success_url(self):
        return reverse('tracker:habit_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class HabitUpdateView(LoginRequiredMixin, UpdateView):
    model = Habit
    fields = ["name", "description", "frequency", "category"]
    template_name = "tracker/habit_form.html"
    
    def get_success_url(self):
        return reverse('social:dashboard', kwargs={'username': self.request.user.username})

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)


class HabitDeleteView(LoginRequiredMixin, DeleteView):
    model = Habit
    template_name = "tracker/habit_confirm_delete.html"
    
    def get_success_url(self):
        return reverse('social:dashboard', kwargs={'username': self.request.user.username})

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)


@require_POST
@login_required
def toggle_habit_completion(request, pk):
    habit = get_object_or_404(
        Habit.objects.select_related('user'),
        pk=pk, user=request.user
    )
    date_str = request.POST.get('date')
    if date_str:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        date = timezone.now().date()
    today = timezone.now().date()
    
    start_of_week = date - timedelta(days=date.weekday())
    
    if habit.frequency == 'weekly':
        # For weekly habits, find any completion this week
        existing_completion = HabitCompletion.objects.filter(
            habit=habit,
            completed_at__gte=start_of_week,
            completed_at__lte=date
        ).first()
        
        if existing_completion:
            # If completed this week, delete the completion
            existing_completion.delete()
        else:
            # If not completed this week, create a completion
            HabitCompletion.objects.create(habit=habit, completed_at=date)
    else:
        # Handle daily habits
        existing_completion = HabitCompletion.objects.filter(
            habit=habit,
            completed_at=date
        ).first()

        if existing_completion:
            # If toggling same day, delete it
            existing_completion.delete()
        else:
            # Create new completion
            HabitCompletion.objects.create(habit=habit, completed_at=date)
    
    # Check badges after modifying completions
    badge_service = BadgeService(request.user)
    badge_service.check_completion_badges()
    
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('tracker:habit_detail', pk=pk)


def root_redirect(request):
    """Redirect root URL to either dashboard or login page"""
    if request.user.is_authenticated:
        return redirect('social:dashboard', username=request.user.username)
    return redirect('account_login')


@login_required
@csrf_protect
@require_http_methods(["POST"])
def generate_ai_summary(request):
    try:
        service = AIHabitService()
        summary_content = service.generate_habit_summary(request.user)
        
        if summary_content.startswith('Error:'):
            return JsonResponse({
                'error': summary_content
            }, status=500)
        
        summary = AIHabitSummary.objects.create(
            user=request.user,
            content=summary_content
        )
        
        # Render the markdown to HTML before sending
        rendered_content = markdown_filter(summary_content)
        
        return JsonResponse({
            'content': rendered_content,  # This is now HTML
            'raw_content': summary_content,  # Keep the raw markdown just in case
            'created_at': summary.created_at.isoformat()
        })
    except Exception as e:
        logger.error(f"Error in generate_ai_summary: {str(e)}")
        return JsonResponse({
            'error': 'An unexpected error occurred'
        }, status=500)