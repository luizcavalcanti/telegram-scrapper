from datetime import datetime, timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import JsonResponse

from telegram_scrapper.core.models import Message, TelegramUser

from .services import ReportsService


_DEFAULT_DAYS = 30
_DEFAULT_LIMIT = 10


def messages_per_day(request):
    past_days = int(request.GET.get('days', _DEFAULT_DAYS))
    data = ReportsService().messages_per_day(past_days)
    return JsonResponse(data, safe=False)


def top_users(request):
    past_days = int(request.GET.get('days', _DEFAULT_DAYS))
    limit = int(request.GET.get('limit', _DEFAULT_LIMIT))
    data = ReportsService().top_users(past_days, limit)
    return JsonResponse(data, safe=False)


def top_images(request):
    past_days = int(request.GET.get('days', _DEFAULT_DAYS))
    limit = int(request.GET.get('limit', _DEFAULT_LIMIT))
    start_date = datetime.today() - timedelta(days=past_days)
    end_date = datetime.today()
    data = (
        Message.objects.filter(
            sent_at__range=[start_date.date(), end_date.date()], video={}, document={}
        )
        .annotate(count=Count('photo_url'))
        .order_by('-count')
        .values('photo_url')
        .annotate(**{'total': Count('photo_url')})[:limit]
    )

    return JsonResponse(list(data), safe=False)


def top_videos(request):
    past_days = int(request.GET.get('days', _DEFAULT_DAYS))
    limit = int(request.GET.get('limit', _DEFAULT_LIMIT))
    start_date = datetime.today() - timedelta(days=past_days)
    end_date = datetime.today()
    data = (
        Message.objects.filter(sent_at__range=[start_date.date(), end_date.date()])
        .annotate(count=Count('video_url'))
        .order_by('-count')
        .values('video_url')
        .annotate(**{'total': Count('video_url')})[:limit]
    )

    return JsonResponse(list(data), safe=False)
