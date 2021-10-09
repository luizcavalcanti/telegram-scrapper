from django.urls import path

from .views import messages_per_day, top_images

urls = (
    [
        path('messages_per_day', views.messages_per_day, name='messages_per_day'),
        path('top_images', views.top_images, name='top_images'),
        path('top_users', views.top_users, name='top_users'),
        path('top_videos', views.top_videos, name='top_videos'),
    ],
    'api',
    'api',
)
