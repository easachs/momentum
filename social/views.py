from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import render
from .models import Friendship
from django.urls import reverse
from django.db.models import Q

@login_required
def send_friend_request(request, username):
    receiver = get_object_or_404(get_user_model(), username=username)
    
    if receiver == request.user:
        messages.error(request, "You can't send a friend request to yourself!")
        return redirect('tracker:habit_list', username=username)
        
    friendship, created = Friendship.objects.get_or_create(
        sender=request.user,
        receiver=receiver,
        defaults={'status': 'pending'}
    )
    
    if created:
        messages.success(request, f"Friend request sent to {receiver.username}! 🤝")
    else:
        if friendship.status == 'pending':
            messages.info(request, f"You already have a pending request to {receiver.username}")
        elif friendship.status == 'accepted':
            messages.info(request, f"You're already friends with {receiver.username}! 🎉")
        elif friendship.status == 'declined':
            friendship.status = 'pending'
            friendship.save()
            messages.success(request, f"Friend request sent to {receiver.username}! 🤝")
    
    return redirect('tracker:habit_list', username=username)

@login_required
def handle_friend_request(request, friendship_id, action):
    friendship = get_object_or_404(
        Friendship,
        id=friendship_id,
        receiver=request.user,
        status='pending'
    )
    
    if action == 'accept':
        friendship.status = 'accepted'
        friendship.save()
        messages.success(request, f"You're now friends with {friendship.sender.username}! 🎉")
    elif action == 'decline':
        friendship.status = 'declined'
        friendship.save()
        messages.info(request, f"Friend request from {friendship.sender.username} declined")
        
    return redirect('tracker:habit_list', username=request.user.username)

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
    
    # Calculate stats for each user
    leaderboard_data = []
    for user in users:
        habits = user.habits.all()
        if not habits:  # Skip users with no habits
            continue
            
        total_completions = sum(habit.completions.count() for habit in habits)
        total_possible = sum(habit.get_total_possible_completions() for habit in habits)
        
        # Calculate completion rate, handling division by zero
        completion_rate = (total_completions / total_possible * 100) if total_possible > 0 else 0
        
        # Get the highest streak among all habits
        current_streak = max((habit.current_streak() for habit in habits), default=0)
        
        leaderboard_data.append({
            'user': user,
            'total_completions': total_completions,
            'completion_rate': completion_rate,
            'current_streak': current_streak,
            'total_habits': habits.count(),
        })
    
    # Sort by completion rate (you could add different sorting options later)
    leaderboard_data.sort(key=lambda x: (-x['completion_rate'], -x['total_completions']))
    
    return render(request, 'social/leaderboard.html', {
        'leaderboard_data': leaderboard_data
    }) 