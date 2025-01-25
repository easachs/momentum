from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import render
from .models import Friendship
from tracker.models import Habit, HabitCompletion, Badge, AIHabitSummary
from django.urls import reverse
from django.db.models import Q, Count, Sum, Case, When, F, FloatField, IntegerField, Prefetch, Exists, OuterRef
from django.db.models.functions import Now, Cast, Trunc, ExtractWeek
from tracker.services.badges.badge_service import BadgeService
from django.views.generic import TemplateView, DetailView
from jobhunt.models import Application
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import HttpResponse
from django.db.models import Count, Q, F, Case, When, IntegerField, DateField
from django.db.models.functions import Cast

@login_required
def send_friend_request(request, username):
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
            # Allow new friend request if:
            # 1. The request was rejected by the current user, OR
            # 2. The rejected_by field is null (old records)
            if friendship.rejected_by is None or friendship.rejected_by == request.user:
                # Create a new friendship request with reversed roles
                friendship.delete()  # Delete the old declined friendship
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

@login_required
def handle_friend_request(request, friendship_id, action):
    friendship = get_object_or_404(Friendship, id=friendship_id)
    
    # Only the receiver can handle the request
    if request.user != friendship.receiver:
        messages.error(request, "You cannot handle this friend request.")
        return redirect('social:dashboard', username=request.user.username)
    
    if action == 'accept':
        friendship.status = 'accepted'
        friendship.save()
        messages.success(request, f"You are now friends with {friendship.sender.username}")
        
        # Check for first friend badge for both users
        BadgeService(request.user).check_social_badges()
        BadgeService(friendship.sender).check_social_badges()
    elif action == 'decline':
        friendship.status = 'declined'
        friendship.save()
        messages.info(request, f"Friend request from {friendship.sender.username} declined")
    
    return redirect('social:dashboard', username=request.user.username)

@login_required
def unfriend(request, friendship_id):
    friendship = get_object_or_404(Friendship, id=friendship_id)
    
    if request.user not in [friendship.sender, friendship.receiver]:
        messages.error(request, "You don't have permission to do this!")
        return redirect('social:friends_list')
    
    friendship.delete()
    other_user = friendship.receiver if request.user == friendship.sender else friendship.sender
    messages.success(request, f"You are no longer friends with {other_user.username}")
    
    return redirect('social:friends_list')

@login_required
def friends_list(request):
    # Get accepted friendships
    friends = Friendship.objects.filter(
        (Q(sender=request.user) | Q(receiver=request.user)),
        status='accepted'
    )
    
    # Get pending incoming requests
    incoming_requests = Friendship.objects.filter(
        receiver=request.user,
        status='pending'
    )
    
    # Get pending outgoing requests
    outgoing_requests = Friendship.objects.filter(
        sender=request.user,
        status='pending'
    )
    
    return render(request, 'social/friends_list.html', {
        'friends': friends,
        'incoming_requests': incoming_requests,
        'outgoing_requests': outgoing_requests,
    })

@login_required
def leaderboard(request):
    User = get_user_model()
    users = User.objects.all()
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
    
    return render(request, 'social/leaderboard.html', {
        'leaderboard_data': leaderboard_data,
        'selected_category': selected_category,
        'categories': ['all'] + [c[0] for c in Habit.CATEGORY_CHOICES]
    })

@login_required
def dashboard(request, username):
    User = get_user_model()
    viewed_user = get_object_or_404(User, username=username)
    context = {
        'is_own_profile': request.user == viewed_user,
        'viewed_user': viewed_user
    }

    # Add friendship context if viewing another user's dashboard
    if request.user != viewed_user:
        context['friendship'] = Friendship.objects.select_related('sender', 'receiver').filter(
            (Q(sender=request.user) & Q(receiver=viewed_user)) |
            (Q(sender=viewed_user) & Q(receiver=request.user))
        ).first()

    # Add friend requests if viewing own dashboard
    if request.user == viewed_user:
        context['friend_requests'] = Friendship.objects.select_related('sender', 'receiver').filter(
            receiver=request.user,
            status='pending'
        )

    # Add habit analytics context
    if request.user == viewed_user or (context.get('friendship') and context['friendship'].status == 'accepted'):
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)

        # Optimize habit completion queries
        habits = Habit.objects.filter(user=viewed_user).annotate(
            completions_count=Count('completions', filter=Q(completions__completed_at__lte=today)),
            week_count=Count('completions', filter=Q(completions__completed_at__gte=start_of_week, completions__completed_at__lte=today)),
            month_count=Count('completions', filter=Q(completions__completed_at__gte=start_of_month, completions__completed_at__lte=today))
        ).prefetch_related(
            Prefetch('completions', queryset=HabitCompletion.objects.order_by('-completed_at')
            )
        )

        # Keep the rest of the context updates unchanged
        context.update(get_habit_analytics(habits))
        context['badges'] = Badge.objects.filter(user=viewed_user)
        context['recent_applications'] = Application.objects.filter(
            user=viewed_user
        ).order_by('-updated_at')[:5]
        context['latest_summary'] = AIHabitSummary.objects.filter(
            user=viewed_user
        ).first()
        context['application_analytics'] = Application.get_analytics(viewed_user)

    return render(request, 'social/dashboard.html', context)

def get_habit_analytics(habits):
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)

    habits_data = []
    for habit in habits:
        completions = list(habit.completions.all())  # Use prefetched data
        completions_count = len([c for c in completions if c.completed_at <= today])
        week_count = len([c for c in completions if start_of_week <= c.completed_at <= today])
        month_count = len([c for c in completions if start_of_month <= c.completed_at <= today])

        # Calculate streak in memory
        completion_dates = sorted({c.completed_at for c in completions}, reverse=True)
        streak = 0

        if completion_dates and completion_dates[0] == today:
            streak = 1
            for i in range(len(completion_dates) - 1):
                if (completion_dates[i] - completion_dates[i + 1]).days == 1:
                    streak += 1
                else:
                    break

        habits_data.append({
            'name': habit.name,
            'category': habit.category,
            'frequency': habit.frequency,
            'completions_count': completions_count,
            'possible_completions': habit.get_total_possible_completions(),
            'week_count': week_count,
            'month_count': month_count,
            'streak_days': streak
        })

    # Calculate totals and category stats as before
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

    return {
        'habit_analytics': {
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
    }
