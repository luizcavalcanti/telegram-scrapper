import json

from django.contrib.postgres.search import SearchQuery
from django.core.paginator import Paginator
from django.db.models import Count, F
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.urls import path

from telegram_scrapper.core.models import Group, Message, TelegramUser


def home(request):
    context_data = {
        'total_messages': Message.objects.count(),
        'total_groups': Group.objects.count(),
        'total_users': TelegramUser.objects.count()
    }    
    return render(request, 'dashboard.html', context_data)


def _occurency_for_messages(queryset):
    return queryset.annotate(date=TruncDate('sent_at')).order_by('date').values('date').annotate(**{'total': Count('sent_at')})


def messages(request):
    query = request.GET.get('query')
    page_number = request.GET.get('page', 1)

    if query:
        search_query = SearchQuery(query, config="portuguese")
        results = Message.objects.filter(search_vector=search_query).order_by("-sent_at")
        occurency = _occurency_for_messages(results)
    else:
        results = Message.objects.all().order_by("-sent_at")
        occurency = None

    paginator = Paginator(results, 100)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'messages.html',
        {
            'query': query,
            'results': page_obj,
            'results_count': paginator.count,
            'occurency': occurency
        }
    )


def groups(request):
    page_number = request.GET.get('page', 1)

    results = Group.objects.all()
    paginator = Paginator(results, 100)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'groups.html',
        {
            'results': page_obj,
            'results_count': paginator.count
        }
    )


def group(request, group_id):
    group = Group.objects.get(id=group_id)
    queryset = Message.objects.filter(group=group_id).order_by('-sent_at')
    last_messages = queryset[:30]
    total_messages = queryset.count()
    activity = _occurency_for_messages(queryset)

    return render(
        request,
        'group.html',
        {
            'group': group,
            'total_messages': total_messages,
            'last_messages': last_messages,
            'activity': activity
        }
    )


def users(request):
    page_number = request.GET.get('page', 1)

    results = TelegramUser.objects.all()
    paginator = Paginator(results, 100)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'users.html',
        {
            'results': page_obj,
            'results_count': paginator.count
        }
    )


def user(request, user_id):
    user = TelegramUser.objects.get(user_id=user_id)
    last_messages =  Message.objects.filter(sender=user_id).order_by('-sent_at')[:30]
    groups = list(map(
        lambda m: m['group'],
        Message.objects.filter(sender=user_id).values('group').distinct('group').order_by('group')
    ))

    return render(request, 'user.html', { 'user': user, 'last_messages': last_messages, 'groups': groups })


urls = (
    [
        path('', home, name='dashboard'),
        path('messages/', messages, name='messages'),
        path('groups/', groups, name='groups'),
        path('groups/<str:group_id>', group, name='group'),
        path('users/', users, name='users'),
        path('users/<int:user_id>/', user, name='user')
    ],
    '',
    '',
)