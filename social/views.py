from datetime import timedelta
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.db.models import Q, Count, Prefetch, OuterRef, Subquery
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import DetailView, View
from habits.models import Habit, HabitCompletion, AIHabitSummary
from social.services.badges.badge_service import BadgeService
from social.models import Friendship, Badge
from applications.models import Application

class DashboardView(LoginRequiredMixin, DetailView):
    model = get_user_model()
    template_name = 'social/dashboard.html'
    context_object_name = 'viewed_user'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        viewed_user = self.object

        # Add is_own_profile to context
        context['is_own_profile'] = self.request.user == viewed_user

        # Get friendship status
        friendship = Friendship.objects.select_related('sender', 'receiver').filter(
            (Q(sender=self.request.user) & Q(receiver=viewed_user)) |
            (Q(sender=viewed_user) & Q(receiver=self.request.user))
        ).first()

        context['friendship'] = friendship

        # Add friend requests if viewing own dashboard
        if self.request.user == viewed_user:
            context['friend_requests'] = Friendship.objects.select_related('sender', 'receiver').filter(
                receiver=self.request.user,
                status='pending'
            )

        # Only include analytics if viewing own profile or is friend
        if self.request.user == viewed_user or (friendship and friendship.status == 'accepted'):
            habits = Habit.objects.filter(user=viewed_user).select_related('user').prefetch_related(
                Prefetch(
                    'completions',
                    queryset=HabitCompletion.objects.order_by('-completed_at')
                )
            )

            # Wrap analytics in habit_analytics key
            context['habit_analytics'] = get_habit_analytics(habits)
            context.update({
                'badges': Badge.objects.filter(user=viewed_user),
                'recent_applications': Application.objects.filter(
                    user=viewed_user
                ).order_by('-updated_at')[:5],
                'latest_summary': AIHabitSummary.objects.filter(
                    user=viewed_user
                ).first(),
                'application_analytics': Application.get_analytics(viewed_user)
            })

        # If user doesn't have wishlist badge yet, check for expired items
        if viewed_user == self.request.user:
            badge_service = BadgeService(viewed_user)
            badge_service.check_application_badges()  # This will check wishlist expired among others

        return context

class FriendRequestView(LoginRequiredMixin, View):
    def get(self, request, username):
        receiver = get_object_or_404(get_user_model(), username=username)

        if receiver == request.user:
            messages.error(request, "You can't send a friend request to yourself!")
            return redirect('social:dashboard', username=username)

        friendship = Friendship.objects.filter(
            (Q(sender=request.user, receiver=receiver) |
             Q(sender=receiver, receiver=request.user))
        ).first()

        if friendship:
            if friendship.status == 'pending':
                messages.info(request, f"You already have a pending request with {receiver.username}")
            elif friendship.status == 'accepted':
                messages.info(request, f"You're already friends with {receiver.username}! 🎉")
            elif friendship.status == 'declined':
                if friendship.rejected_by is None or friendship.rejected_by == request.user:
                    friendship.delete()
                    Friendship.objects.create(
                        sender=request.user,
                        receiver=receiver,
                        status='pending'
                    )
                    messages.success(request, f"Friend request sent to {receiver.username}! 🤝")
                else:
                    messages.error(request, f"Cannot send friend request to {receiver.username}")
        else:
            Friendship.objects.create(sender=request.user, receiver=receiver, status='pending')
            messages.success(request, f"Friend request sent to {receiver.username}! 🤝")

        return redirect('social:dashboard', username=username)

class HandleFriendRequestView(LoginRequiredMixin, View):
    def get(self, request, friendship_id, action):
        friendship = get_object_or_404(Friendship, id=friendship_id)

        if friendship.receiver != request.user:
            messages.error(request, "You cannot handle this friend request!")
            return redirect('social:dashboard', username=request.user.username)

        if action == 'accept':
            friendship.status = 'accepted'
            friendship.save()

            # Check for first friend badge
            BadgeService(request.user).check_social_badges()
            BadgeService(friendship.sender).check_social_badges()

            messages.success(request, f"You are now friends with {friendship.sender.username}! 🎉")
        elif action == 'decline':
            friendship.status = 'declined'
            friendship.rejected_by = request.user
            friendship.save()
            messages.info(request, f"Friend request from {friendship.sender.username} declined")

        return redirect('social:dashboard', username=request.user.username)

class UnfriendView(LoginRequiredMixin, View):
    def post(self, request, friendship_id):
        return self.handle_unfriend(request, friendship_id)

    def get(self, request, friendship_id):
        return self.handle_unfriend(request, friendship_id)

    def handle_unfriend(self, request, friendship_id):
        friendship = get_object_or_404(
            Friendship,
            id=friendship_id,
            status='accepted'
        )

        if request.user not in [friendship.sender, friendship.receiver]:
            messages.error(request, "You cannot unfriend these users!")
            return redirect('social:dashboard', username=request.user.username)

        other_user = friendship.receiver if request.user == friendship.sender else friendship.sender

        friendship.delete()
        messages.success(request, f"You are no longer friends with {other_user.username}")
        return redirect('social:dashboard', username=request.user.username)

class FriendsListView(LoginRequiredMixin, View):
    template_name = 'social/friends_list.html'

    def get(self, request):
        context = {
            'friends': Friendship.objects.filter(
                (Q(sender=request.user) | Q(receiver=request.user)),
                status='accepted'
            ),
            'incoming_requests': Friendship.objects.filter(
                receiver=request.user,
                status='pending'
            ),
            'outgoing_requests': Friendship.objects.filter(
                sender=request.user,
                status='pending'
            )
        }
        return render(request, self.template_name, context)

class LeaderboardView(LoginRequiredMixin, View):
    template_name = 'social/leaderboard.html'

    def get(self, request):
        user = get_user_model()
        users = user.objects.all()
        selected_category = request.GET.get('category', 'all')

        # Calculate stats for each user
        leaderboard_data = []
        for user in users:
            habits = user.habits.all()
            if selected_category != 'all':
                habits = habits.filter(category=selected_category)

            if not habits:  # Skip users with no habits in this category
                continue

            total_completions = sum(habit.completions.count() for habit in habits)
            total_possible = sum(habit.get_total_possible_completions() for habit in habits)

            completion_rate = (total_completions / total_possible * 100) if total_possible > 0 else 0
            current_streak = max((habit.current_streak() for habit in habits), default=0)

            # Get user's badges
            badges = Badge.get_user_highest_badges(user)
            badge_count = sum(1 for badge in badges.values() if badge is not None)

            leaderboard_data.append({
                'user': user,
                'total_completions': total_completions,
                'completion_rate': completion_rate,
                'current_streak': current_streak,
                'total_habits': habits.count(),
                'badges': badges,
                'badge_count': badge_count
            })

        leaderboard_data.sort(key=lambda x: (-x['completion_rate'], -x['total_completions']))

        context = {
            'leaderboard_data': leaderboard_data,
            'selected_category': selected_category,
            'categories': ['all'] + [c[0] for c in Habit.CATEGORY_CHOICES]
        }

        return render(request, self.template_name, context)

def get_habit_analytics(habits):
    today = timezone.localtime(timezone.now()).date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)

    habits = habits.annotate(
        completions_count=Count('completions',
            filter=Q(completions__completed_at__lte=today)),
        week_count=Count('completions',
            filter=Q(
                completions__completed_at__gte=start_of_week,
                completions__completed_at__lte=today
            )),
        month_count=Count('completions',
            filter=Q(
                completions__completed_at__gte=start_of_month,
                completions__completed_at__lte=today
            )),
        streak_days=Subquery(
            HabitCompletion.objects.filter(
                habit=OuterRef('pk'),
                completed_at__lte=today
            ).values('habit')
            .annotate(
                streak=Count('id')
            ).values('streak')[:1]
        )
    )

    habits_data = []
    for habit in habits:
        habits_data.append({
            'name': habit.name,
            'category': habit.category,
            'frequency': habit.frequency,
            'completions_count': habit.completions_count,
            'possible_completions': habit.get_total_possible_completions(),
            'week_count': habit.week_count,
            'month_count': habit.month_count,
            'streak_days': habit.streak_days or 0
        })

    # Calculate totals using annotated values
    total_completions = sum(h['completions_count'] for h in habits_data)
    total_possible = sum(h['possible_completions'] for h in habits_data)

    by_category = {}
    for habit in habits_data:
        cat = habit['category']
        if cat not in by_category:
            by_category[cat] = {'completed': 0, 'possible': 0, 'count': 0, 'streak': 0}
        by_category[cat]['completed'] += habit['completions_count']
        by_category[cat]['possible'] += habit['possible_completions']
        by_category[cat]['count'] += 1
        by_category[cat]['streak'] = max(by_category[cat]['streak'], habit['streak_days'])

    category_stats = []
    for category, data in by_category.items():
        if data['possible'] > 0:
            category_stats.append({
                'category': category,
                'completed': data['completed'],
                'total': data['possible'],
                'habit_count': data['count'],
                'percentage': round(data['completed'] * 100 / data['possible'], 1)
            })

    # Return all required analytics fields
    return {
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
