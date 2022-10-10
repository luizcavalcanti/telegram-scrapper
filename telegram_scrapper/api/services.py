import json

from datetime import datetime, timedelta
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.forms.models import model_to_dict
from django.utils import timezone


from telegram_scrapper.core.models import Message, Report, TelegramUser

class ReportsService:
    MESSAGES_PER_DAY_CACHE_IN_HOURS = 6
    TOP_USERS_CACHE_IN_HOURS = 6

    def __init__(self):
        pass

    def messages_per_day(self, past_days, force_generation=False):
        report_id = f"general_messages_per_day_{past_days}"
        try:
            report = Report.objects.get(id=report_id)
            if force_generation or (datetime.now(timezone.utc) - report.updated_at > timedelta(hours=ReportsService.MESSAGES_PER_DAY_CACHE_IN_HOURS)):
                data = self._generate_messages_per_day_report(report_id, past_days)
            else:
                data = json.loads(report.report_data)
        except Report.DoesNotExist:
            data = self._generate_messages_per_day_report(report_id, past_days)

        return data

    def top_users(self, past_days, limit, force_generation=False):
        report_id = f"general_top_users_{past_days}_{limit}"
        try:
            report = Report.objects.get(id=report_id)
            if force_generation or (datetime.now(timezone.utc) - report.updated_at > timedelta(hours=ReportsService.TOP_USERS_CACHE_IN_HOURS)):
                data = self._generate_top_users_report(report_id, past_days, limit)
            else:
                data = json.loads(report.report_data)
        except Report.DoesNotExist:
            data = self._generate_top_users_report(report_id, past_days, limit)

        return data

    def group_activity(self, group_id, past_days=90, force_generation=False):
        report_id = f"group_activity_{group_id}"
        try:
            report = Report.objects.get(id=report_id)
            if force_generation or (datetime.now(timezone.utc) - report.updated_at > timedelta(hours=ReportsService.MESSAGES_PER_DAY_CACHE_IN_HOURS)):
                data = self._generate_group_activity_report(report_id, group_id, past_days)
            else:
                data = json.loads(report.report_data)
        except Report.DoesNotExist:
            data = self._generate_group_activity_report(report_id, group_id, past_days)

        return data

    def _generate_messages_per_day_report(self, report_id, past_days):
        start_date = datetime.today() - timedelta(days=past_days)
        data = list(
            Message.objects.filter(sent_at__gte=start_date.date())
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

    def _generate_group_activity_report(self, report_id, group_id, past_days):
        start_date = datetime.today() - timedelta(days=past_days)
        activity = list(Message.objects.filter(group=group_id, sent_at__gte=start_date.date())
                        .order_by('-sent_at')
                        .annotate(date=TruncDate('sent_at'))
                        .order_by('date')
                        .values('date')
                        .annotate(**{'total': Count('sent_at')}))

        Report.objects.update_or_create(
            id=report_id,
            defaults={
                'report_data': json.dumps(activity, cls=DjangoJSONEncoder),
                'updated_at': timezone.now()
            }
        )

    def _generate_top_users_report(self, report_id, past_days, limit):
        start_date = datetime.today() - timedelta(days=past_days)
        data = (
            Message.objects.filter(sent_at__gte=start_date.date())
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
                print(e)
                pass

        Report.objects.update_or_create(
            id=report_id,
            defaults={'report_data': json.dumps(result_data, cls=DjangoJSONEncoder),
                      'updated_at': timezone.now()}
        )

        return result_data
