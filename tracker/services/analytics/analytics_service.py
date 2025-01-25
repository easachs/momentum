from datetime import timedelta
from django.utils import timezone
from django.db.models import (
    Count, Q, Value, Case, When, DateField, IntegerField
)
from django.db.models.functions import Cast
from tracker.models import Habit, AIHabitSummary

class HabitAnalyticsService:
    def __init__(self, user):
        self.user = user

    def get_habits_with_analytics(self):
        """Get habits with all necessary annotations for analytics"""
        today = timezone.localtime(timezone.now()).date()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)

        return (self.user.habits.all()
            .select_related('user')
            .annotate(
                completed_today=Count('completions',
                    filter=Q(completions__completed_at=today)),
                completed_this_week=Count('completions',
                    filter=Q(
                        completions__completed_at__gte=start_of_week,
                        completions__completed_at__lte=today
                    )),
                month_count=Count('completions',
                    filter=Q(completions__completed_at__gte=Cast(Value(start_of_month),
                                                             output_field=DateField()))),
                total_completions=Count('completions'),
                needs_completion_daily=Case(
                    When(frequency='daily', completed_today=0, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                needs_completion_weekly=Case(
                    When(frequency='weekly', completed_this_week=0, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ).prefetch_related('completions'))

    def get_habits_data(self, habits):
        """Convert habits queryset to analytics-ready data structure"""
        return [
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

    def get_category_stats(self, habits_data):
        """Calculate statistics per category"""
        by_category = {}
        for habit in habits_data:
            cat = habit.get('category')
            if cat not in by_category:
                by_category[cat] = {'completed': 0, 'possible': 0, 'count': 0, 'streak': 0}
            by_category[cat]['completed'] += habit['completions_count']
            by_category[cat]['possible'] += habit['possible_completions']
            by_category[cat]['count'] += 1
            by_category[cat]['streak'] = max(by_category[cat]['streak'], habit['streak_days'])

        category_stats = []
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
        return category_stats

    def get_analytics(self, habits=None):
        """Get complete analytics for habits"""
        if habits is None:
            habits = self.get_habits_with_analytics()

        habits_data = self.get_habits_data(habits)
        category_stats = self.get_category_stats(habits_data)

        total_completions = sum(h['completions_count'] for h in habits_data)
        total_possible = sum(h['possible_completions'] for h in habits_data)

        return {
            'total_habits': len(habits_data),
            'completion_rate': round(
                total_completions * 100 / total_possible if total_possible > 0 else 0.0, 1
            ),
            'this_week_completions': sum(h['week_count'] for h in habits_data),
            'this_month_completions': sum(h['month_count'] for h in habits_data),
            'category_stats': category_stats,
            'best_streak': max((h['streak_days'] for h in habits_data), default=0),
            'total_completions': total_completions,
            'total_possible': total_possible,
        }

    def get_notifications(self, habits):
        """Get notification counts for incomplete habits"""
        return {
            'incomplete_daily': habits.filter(frequency='daily', completed_today=0).count(),
            'incomplete_weekly': habits.filter(frequency='weekly', completed_this_week=0).count(),
        }

    def get_habits_by_view_mode(self, habits, view_mode='frequency'):
        """Organize habits based on view mode (category or frequency)"""
        # Add streak to each habit
        for habit in habits:
            habit.streak = habit.current_streak()

        if view_mode == 'category':
            categorized_habits = {}
            for category, label in Habit.CATEGORY_CHOICES:
                categorized_habits[category] = {
                    'label': label,
                    'habits': []
                }
            
            for habit in habits:
                categorized_habits[habit.category]['habits'].append(habit)
            
            return {
                'categorized_habits': categorized_habits,
                'has_any_habits': any(data['habits'] for data in categorized_habits.values())
            }
        else:  # frequency view
            daily_habits = []
            weekly_habits = []
            
            for habit in habits:
                if habit.frequency == 'daily':
                    daily_habits.append(habit)
                else:
                    weekly_habits.append(habit)
            
            return {
                'daily_habits': daily_habits,
                'weekly_habits': weekly_habits
            }

    def get_habit_detail_data(self, habit, completions=None):
        """Get all analytics data needed for habit detail view"""
        today = timezone.localtime(timezone.now()).date()
        yesterday = today - timedelta(days=1)
        start_of_week = today - timedelta(days=today.weekday())

        if completions is None:
            completions = list(habit.completions.all())

        # Determine completion status based on frequency
        if habit.frequency == 'weekly':
            week_completions = [c for c in completions 
                              if start_of_week <= c.completed_at <= today]
            today_completion = bool(week_completions)
        else:  # daily
            today_completion = any(c.completed_at == today for c in completions)

        # Get detailed analytics
        analytics = self._get_habit_detail_analytics(habit, completions)

        return {
            'today': today,
            'yesterday': yesterday,
            'today_completion': today_completion,
            'yesterday_completion': any(c.completed_at == yesterday for c in completions),
            'show_yesterday': habit.frequency == 'daily' and habit.created_at.date() <= yesterday,
            'analytics': analytics,
        }

    def _get_habit_detail_analytics(self, habit, completions=None):
        """Calculate detailed analytics for a single habit"""
        today = timezone.localtime(timezone.now()).date()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)

        if completions is None:
            completions = list(habit.completions.all())

        # Calculate total possible completions based on frequency
        days_since_creation = (today - habit.created_at.date()).days + 1
        if habit.frequency == 'daily':
            total_possible = days_since_creation
        else:  # weekly
            total_possible = (days_since_creation + 6) // 7

        # Count actual completions
        total_completions = len([c for c in completions 
                               if c.completed_at >= habit.created_at.date()])
        week_completions = len([c for c in completions 
                              if start_of_week <= c.completed_at <= today])
        month_completions = len([c for c in completions 
                               if start_of_month <= c.completed_at <= today])

        return {
            'total_completions': total_completions,
            'total_possible': total_possible,
            'completion_rate': round(
                (total_completions * 100 / total_possible) if total_possible > 0 else 0, 1
            ),
            'this_week_completions': week_completions,
            'this_month_completions': month_completions,
            'current_streak': habit.current_streak(),
            'longest_streak': habit.longest_streak(),
        }

    def get_list_view_data(self, view_mode='frequency', selected_category=None):
        """Get all data needed for the habit list view"""
        # Get habits with annotations
        habits = self.get_habits_with_analytics()
        
        # Apply category filter if needed
        if selected_category:
            habits = habits.filter(category=selected_category)
        
        # Get analytics and notifications
        analytics = self.get_analytics(habits)
        notifications = self.get_notifications(habits)
        
        # Get habits organized by view mode
        view_data = self.get_habits_by_view_mode(habits, view_mode)
        
        # Get latest AI summary
        latest_summary = AIHabitSummary.objects.filter(
            user=self.user
        ).first()
        
        return {
            'object_list': habits,
            'notifications': notifications,
            'habit_analytics': analytics,
            'analytics': analytics,
            'view_mode': view_mode,
            'habit_categories': Habit.CATEGORY_CHOICES,
            'latest_summary': latest_summary,
            **view_data  # Include categorized_habits or daily/weekly habits
        }
