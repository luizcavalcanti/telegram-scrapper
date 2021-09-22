from django.urls import path

from .views import messages_per_day

urls = (
    [path('messages_per_day', views.messages_per_day, name='messages_per_day')],
    'api',
    'api',
)
