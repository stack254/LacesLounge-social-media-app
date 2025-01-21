from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('follow/<str:username>/', views.follow_unfollow, name='follow_unfollow'),
    path('create_post/', views.create_post, name='create_post'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('like/<int:post_id>/', views.like_post, name='like_post'),
    path('logout/', views.custom_logout, name='logout'),
    path('feed/', views.feed, name='feed'),
    path('inbox/', views.inbox, name='inbox'),
    path('send_message/<str:username>/', views.send_message, name='send_message'),
    path('view_message/<int:message_id>/', views.view_message, name='view_message'),
    path('follow/', views.follow_user, name='follow_user'),
    path('unfollow/', views.unfollow_user, name='unfollow_user'),
    path('hashtags/<str:hashtag_name>/', views.hashtag_posts, name='hashtag_posts'),
]