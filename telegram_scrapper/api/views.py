from datetime import datetime, timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.forms.models import model_to_dict

from telegram_scrapper.core.models import Message, TelegramUser

from .services import ReportsService


_DEFAULT_DAYS = 30
_DEFAULT_LIMIT = 10


def messages_per_day(request):
    past_days = int(request.GET.get('days', _DEFAULT_DAYS))
    data = ReportsService().messages_per_day(past_days)
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


def top_users(request):
    past_days = int(request.GET.get('days', _DEFAULT_DAYS))
    limit = int(request.GET.get('limit', _DEFAULT_LIMIT))
    start_date = datetime.today() - timedelta(days=past_days)
    end_date = datetime.today() + timedelta(days=1)
    data = (
        Message.objects.filter(sent_at__range=[start_date.date(), end_date.date()])
        .exclude(sender='channel')
        .annotate(count=Count('sender'))
        .order_by('-count')
        .values('sender')
        .annotate(**{'total': Count('sender')})[:limit]
    )

    # Que presepada, preciso botar uma FK nesse negócio logo
    result_data = list(data)
    for entry in result_data:
        try:
            entry['user'] = model_to_dict(
                TelegramUser.objects.get(user_id=entry['sender'])
            )
        except Exception as e:
            pass

    return JsonResponse(result_data, safe=False)
