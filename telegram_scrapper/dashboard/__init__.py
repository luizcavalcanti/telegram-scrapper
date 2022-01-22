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


def message_search(request):
    query = request.GET.get('query')
    page_number = request.GET.get('page', 1)
    search_query = SearchQuery(query, config="portuguese")
    results = Message.objects.filter(search_vector=search_query).order_by("-sent_at")
    occurency = _occurency_for_messages(results)

    paginator = Paginator(results, 100)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'message_search.html',
        {
            'query': query,
            'results': page_obj,
            'results_count': paginator.count,
            'occurency': occurency
        }
    )


urls = (
    [
        path('', home, name='dashboard'),
        path('message_search/', message_search, name='message_search')
    ],
    '',
    '',
)
