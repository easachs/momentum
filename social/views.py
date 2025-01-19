from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Friendship
from django.urls import reverse

@login_required
def send_friend_request(request, username):
    receiver = get_object_or_404(get_user_model(), username=username)
    
    if receiver == request.user:
        messages.error(request, "You cannot send a friend request to yourself.")
        return redirect('tracker:habit_list', username=username)
        
    friendship, created = Friendship.objects.get_or_create(
        sender=request.user,
        receiver=receiver,
        defaults={'status': 'pending'}
    )
    
    if created:
        messages.success(request, f"Friend request sent to {receiver.username}")
    else:
        messages.info(request, "Friend request already exists")
        
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
        messages.success(request, f"You are now friends with {friendship.sender.username}")
    elif action == 'decline':
        friendship.status = 'declined'
        friendship.save()
        messages.info(request, "Friend request declined")
        
    return redirect('tracker:habit_list', username=request.user.username)

@login_required
def leaderboard(request):
    # Implementation coming in next message...
    pass 