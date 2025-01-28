import logging
from datetime import datetime, timedelta
from django.db import models
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q, Case, When, Value
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from django.db.models.functions import Cast

from tracker.templatetags.markdown.filters import markdown_filter
from .models import Habit
from .services.ai.ai_service import AIHabitService
from social.services.badges.badge_service import BadgeService
from .services.analytics.analytics_service import HabitAnalyticsService
from .services.habits.habit_service import HabitService
from .services.navigation.navigation_service import NavigationService
from .forms import HabitForm

logger = logging.getLogger(__name__)

class HabitListView(LoginRequiredMixin, ListView):
    model = Habit
    template_name = "tracker/habit_list.html"
    context_object_name = 'habits'

    def get_queryset(self):
        today = timezone.localtime(timezone.now()).date()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)

        return (Habit.objects.filter(user=self.request.user)
            .select_related('user')
            .annotate(
                completed_today=Count('completions',
                    filter=Q(completions__completed_at=Cast(Value(today), output_field=models.DateField()))),
                completed_this_week=Count('completions',
                    filter=Q(completions__completed_at__gte=Cast(Value(start_of_week),
                                                                 output_field=models.DateField()))),
                month_count=Count('completions',
                    filter=Q(completions__completed_at__gte=Cast(Value(start_of_month),
                                                                 output_field=models.DateField()))),
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

        analytics_service = HabitAnalyticsService(self.request.user)
        view_mode = self.request.GET.get('view', 'frequency')
        selected_category = self.request.GET.get('category')

        context.update(
            analytics_service.get_list_view_data(
                view_mode=view_mode,
                selected_category=selected_category
            )
        )

        return context

class HabitDetailView(LoginRequiredMixin, DetailView):
    model = Habit
    template_name = "tracker/habit_detail.html"

    def get_queryset(self):
        return (Habit.objects
            .filter(user=self.request.user)
            .prefetch_related('completions'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        habit = self.get_object()

        # Get analytics data from service
        analytics_service = HabitAnalyticsService(self.request.user)
        context.update(analytics_service.get_habit_detail_data(habit))
        context['habit'] = habit

        return context

class HabitCreateView(LoginRequiredMixin, CreateView):
    model = Habit
    form_class = HabitForm
    template_name = "tracker/habit_form.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('tracker:habit_detail', kwargs={'pk': self.object.pk})

class HabitUpdateView(LoginRequiredMixin, UpdateView):
    model = Habit
    form_class = HabitForm
    template_name = "tracker/habit_form.html"

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse('tracker:habit_detail', kwargs={'pk': self.object.pk})

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

    # Get the date to toggle (today by default)
    date_str = request.POST.get('date')
    if date_str:
        toggle_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        toggle_date = timezone.localtime(timezone.now()).date()

    # Use service to handle completion logic
    habit_service = HabitService(request.user)
    was_completed = habit_service.toggle_completion(habit, toggle_date)

    # Only check badges if we completed (not uncompleted)
    if was_completed:
        badge_service = BadgeService(request.user)
        badge_service.check_completion_badges()

    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('tracker:habit_detail', pk=pk)

def root_redirect(request):
    """Redirect root URL to either dashboard or login page"""
    nav_service = NavigationService()
    return redirect(nav_service.get_home_redirect_url(request.user))

@login_required
@csrf_protect
@require_http_methods(["POST"])
def generate_ai_summary(request):
    service = AIHabitService()
    summary, error = service.create_summary(request.user)

    if error:
        return JsonResponse({'error': error}, status=500)

    # Render the markdown to HTML before sending
    rendered_content = markdown_filter(summary.content)

    return JsonResponse({
        'content': rendered_content,
        'raw_content': summary.content,
        'created_at': summary.created_at.isoformat()
    })
