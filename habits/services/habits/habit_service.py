from datetime import timedelta
from habits.models import HabitCompletion

class HabitService:
    def __init__(self, user):
        self.user = user

    def toggle_completion(self, habit, toggle_date):
        """Toggle completion status for a habit on a specific date"""
        if habit.frequency == 'weekly':
            return self._toggle_weekly_completion(habit, toggle_date)
        return self._toggle_daily_completion(habit, toggle_date)

    def _toggle_weekly_completion(self, habit, toggle_date):
        start_of_week = toggle_date - timedelta(days=toggle_date.weekday())
        existing_completion = HabitCompletion.objects.filter(
            habit=habit,
            completed_at__gte=start_of_week,
            completed_at__lte=toggle_date
        ).exists()
        
        if existing_completion:
            HabitCompletion.objects.filter(
                habit=habit,
                completed_at__gte=start_of_week,
                completed_at__lte=toggle_date
            ).delete()
        else:
            HabitCompletion.objects.create(
                habit=habit,
                completed_at=toggle_date
            )
        return not existing_completion

    def _toggle_daily_completion(self, habit, toggle_date):
        existing_completion = HabitCompletion.objects.filter(
            habit=habit,
            completed_at=toggle_date
        ).exists()
        
        if existing_completion:
            HabitCompletion.objects.filter(
                habit=habit,
                completed_at=toggle_date
            ).delete()
        else:
            HabitCompletion.objects.create(
                habit=habit,
                completed_at=toggle_date
            )
        return not existing_completion 