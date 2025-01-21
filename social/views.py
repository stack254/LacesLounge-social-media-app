from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from .models import *
from .forms import PostForm, CommentForm, UserRegisterForm, ProfileForm, MessageForm
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.db.models import Q
def home(request):
    posts = Post.objects.all().order_by('-created_at')
    if request.user.is_authenticated:
        followed_users = Follow.objects.filter(follower=request.user).values_list('followed', flat=True)
        followed_posts = Post.objects.filter(user__in=followed_users).order_by('-created_at')
    else:
        followed_posts = Post.objects.none()
    return render(request, 'social/home.html', { 'followed_posts': followed_posts, 'posts': posts})

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'social/register.html', {'form': form})

@login_required
def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(user=user).order_by('-created_at')
    is_following = request.user.is_authenticated and Follow.objects.filter(follower=request.user, followed=user).exists()
    try:
        profile = user.profile
        avatar_url = profile.avatar.url if profile.avatar else None
    except ObjectDoesNotExist:
        profile = Profile.objects.create(user=user)
        avatar_url = None
    
    follower_count = Follow.objects.filter(followed=user).count()
    following_count = Follow.objects.filter(follower=user).count()
    
    context = {
        'profile_user': user,
        'avatar_url': avatar_url,
        'posts': posts,
        'is_own_profile': request.user == user,
        'is_following': is_following,
        'follower_count': follower_count,
        'following_count': following_count,
    }
    return render(request, 'social/profile.html', context)
@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('profile', username=request.user.username)
    else:
        form = ProfileForm(instance=request.user.profile)
    return render(request, 'social/edit_profile.html', {'form': form})
@login_required
def follow_unfollow(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    if request.user == user_to_follow:
        return HttpResponseRedirect(reverse('profile', args=[username]))
    
    if request.method == 'POST':
        follow, created = Follow.objects.get_or_create(follower=request.user, followed=user_to_follow)
        
        if not created:
            follow.delete()
    
    return HttpResponseRedirect(reverse('profile', args=[username]))


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            post.process_hashtags()
            return redirect('home')
    else:
        form = PostForm()
    return render(request, 'social/create_post.html', {'form': form})

def hashtag_posts(request, hashtag_name):
    hashtag = get_object_or_404(Hashtag, name=hashtag_name.lower())
    posts = Post.objects.filter(hashtags=hashtag).order_by('-created_at')
    return render(request, 'social/hashtags.html', {'hashtag': hashtag, 'posts': posts})


@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.user = request.user
            comment.post = post
            comment.save()
            return redirect('post_detail', post_id=post.id)
    else:
        comment_form = CommentForm()
    return render(request, 'social/post_detail.html', {'post': post, 'comments': comments, 'comment_form': comment_form})

@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
        is_liked = False
    else:
        is_liked = True
        return JsonResponse({'likes_count': post.likes.count(), 'is_liked': is_liked})
    return redirect('post_detail', post_id=post.id)

def custom_logout(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('social/home')

@login_required
def feed(request):
    followed_users = Follow.objects.filter(follower=request.user).values_list('followed', flat=True)
    followed_posts = Post.objects.filter(user__in=followed_users).order_by('-created_at')
    all_posts = Post.objects.exclude(user=request.user).order_by('-created_at')

    context = {
        'followed_posts': followed_posts,
        'all_posts': all_posts,
    }
    return render(request, 'social/feed.html', context)

@login_required
def inbox(request):
    messages_received = Message.objects.filter(recipient=request.user)
    messages_sent = Message.objects.filter(sender=request.user)
    return render(request, 'social/inbox.html', {
        'messages_received': messages_received,
        'messages_sent': messages_sent
    })

@login_required
def send_message(request, username):
    recipient = get_object_or_404(User, username=username)
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient = recipient
            message.save()
            return redirect('profile', username=username)
    else:
        form = MessageForm()
    
    return render(request, 'social/send_message.html', {'form': form, 'recipient': recipient})
@login_required
def view_message(request, message_id):
    message = get_object_or_404(Q(recipient=request.user) | Q(sender=request.user),Message, id=message_id, )
    if message.recipient == request.user and not message.is_read:
        message.is_read = True
        message.save()
    return render(request, 'social/view_message.html', {'message': message})
@require_POST
def follow_user(request):
    user_to_follow = get_object_or_404(User, username=request.POST.get('username'))
    follow, created = Follow.objects.get_or_create(follower=request.user, followed=user_to_follow)
    follower_count = Follow.objects.filter(followed=user_to_follow).count()
    return JsonResponse({
        'status': 'success',
        'follower_count': follower_count
    })

@require_POST
def unfollow_user(request):
    user_to_unfollow = get_object_or_404(User, username=request.POST.get('username'))
    Follow.objects.filter(follower=request.user, followed=user_to_unfollow).delete()
    follower_count = Follow.objects.filter(followed=user_to_unfollow).count()
    return JsonResponse({
        'status': 'success',
        'follower_count': follower_count
    })