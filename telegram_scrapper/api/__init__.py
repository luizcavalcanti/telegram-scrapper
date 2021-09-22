from django.urls import path

from .views import messages_per_day, top_images

urls = (
    [
        path('messages_per_day', views.messages_per_day, name='messages_per_day'),
        path('top_images', views.top_images, name='top_images'),
    ],
    'api',
    'api',
)
