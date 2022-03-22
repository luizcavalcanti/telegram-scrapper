import json

from datetime import datetime, timedelta
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from telegram_scrapper.core.models import Message, Report

class ReportsService:
    MESSAGES_PER_DAY_CACHE_IN_HOURS = 6

    def __init__(self):
        pass

    def messages_per_day(self, past_days):
        report_id = f"general_messages_per_dat_{past_days}"
        try:
            report = Report.objects.get(id=report_id)
            if datetime.now(timezone.utc) - report.updated_at > timedelta(hours=ReportsService.MESSAGES_PER_DAY_CACHE_IN_HOURS):
                data = self._generate_messages_per_day_report(report_id, past_days)
            else:
                data = json.loads(report.report_data)
        except Report.DoesNotExist:
            data = self._generate_messages_per_day_report(report_id, past_days)
            
        return data

    def _generate_messages_per_day_report(self, report_id, past_days):
        start_date = datetime.today() - timedelta(days=past_days)
        end_date = datetime.today()
        data = list(
            Message.objects.filter(sent_at__range=[start_date.date(), end_date.date()])
            .annotate(date=TruncDate('sent_at'))
            .order_by('date')
            .values('date')
            .annotate(**{'total': Count('sent_at')})
        )
        Report.objects.update_or_create(
            id=report_id,
            defaults={'report_data': json.dumps(data, cls=DjangoJSONEncoder),
                      'updated_at': timezone.now()}
        )
        return data
