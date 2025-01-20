from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import render
from .models import Friendship
from tracker.models import Habit, HabitCompletion, Badge, AIHabitSummary
from django.urls import reverse
from django.db.models import Q, Count
from tracker.services.badges.badge_service import BadgeService
from django.views.generic import TemplateView, DetailView
from jobhunt.models import Application
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import HttpResponse

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
    """Display a user's dashboard with their habits and analytics"""
    User = get_user_model()
    viewed_user = get_object_or_404(User, username=username)
    context = {
        'profile_user': viewed_user,
        'is_own_profile': request.user == viewed_user,
        'viewed_user': viewed_user  # Keep this for backward compatibility
    }
    
    # Add friendship context if viewing another user's dashboard
    if request.user != viewed_user:
        context['friendship'] = Friendship.objects.filter(
            (Q(sender=request.user) & Q(receiver=viewed_user)) |
            (Q(sender=viewed_user) & Q(receiver=request.user))
        ).first()

    # Add friend requests if viewing own dashboard
    if request.user == viewed_user:
        context['friend_requests'] = Friendship.objects.filter(
            receiver=request.user,
            status='pending'
        )

    # Add analytics and data if user has permission
    if request.user == viewed_user or (context.get('friendship') and context['friendship'].status == 'accepted'):
        # Add analytics context
        context.update(_get_analytics_context(viewed_user))
        
        # Add habits and completions
        context['habits'] = Habit.objects.filter(user=viewed_user)
        context['recent_completions'] = HabitCompletion.objects.filter(
            habit__user=viewed_user
        ).select_related('habit').order_by('-completed_at')[:5]
        context['badges'] = Badge.objects.filter(user=viewed_user)
        
        # Add application data
        context['recent_applications'] = Application.objects.filter(
            user=viewed_user
        ).order_by('-updated_at')[:5]
        
        # Add latest AI summary
        context['latest_summary'] = AIHabitSummary.objects.filter(
            user=viewed_user
        ).first()

    return render(request, 'social/dashboard.html', context)

def _get_analytics_context(user):
    """Helper function to get analytics data for the dashboard"""
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)

    # Get all habits and completions
    habits = Habit.objects.filter(user=user)
    completions = HabitCompletion.objects.filter(habit__user=user)

    # Calculate completion rates and stats
    total_completions = completions.count()
    total_possible = sum(
        (today - habit.created_at.date()).days + 1 if habit.frequency == 'daily'
        else ((today - habit.created_at.date()).days + 7) // 7
        for habit in habits
    )

    # Get category stats
    category_stats = []
    for category, label in Habit.CATEGORY_CHOICES:
        category_habits = habits.filter(category=category)
        if category_habits.exists():
            completed = completions.filter(habit__category=category).count()
            total = sum(
                (today - habit.created_at.date()).days + 1 if habit.frequency == 'daily'
                else ((today - habit.created_at.date()).days + 7) // 7
                for habit in category_habits
            )
            category_stats.append({
                'category': category,
                'completed': completed,
                'total': total,
                'habit_count': category_habits.count(),
                'percentage': round(completed / total * 100 if total > 0 else 0, 1)
            })

    # Calculate best streak
    best_streak = max((habit.current_streak() for habit in habits), default=0)

    return {
        'analytics': {
            'total_habits': habits.count(),
            'completion_rate': round(total_completions / total_possible * 100 if total_possible > 0 else 0, 1),
            'this_week_completions': completions.filter(completed_at__gte=start_of_week).count(),
            'this_month_completions': completions.filter(completed_at__gte=start_of_month).count(),
            'category_stats': category_stats,
            'best_streak': best_streak
        }
    }