from datetime import datetime, timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import JsonResponse

from telegram_scrapper.core.models import Message


_DEFAULT_DAYS = 30


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
