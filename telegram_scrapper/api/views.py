from datetime import datetime, timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import JsonResponse

from telegram_scrapper.core.models import Message


_DEFAULT_DAYS = 30
_DEFAULT_LIMIT = 10


def messages_per_day(request):
    past_days = int(request.GET.get('days', _DEFAULT_DAYS))
    start_date = datetime.today() - timedelta(days=past_days)
    end_date = datetime.today()
    data = (
        Message.objects.filter(sent_at__range=[start_date.date(), end_date.date()])
        .annotate(date=TruncDate('sent_at'))
        .order_by('date')
        .values('date')
        .annotate(**{'total': Count('sent_at')})
    )

    return JsonResponse(list(data), safe=False)


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
