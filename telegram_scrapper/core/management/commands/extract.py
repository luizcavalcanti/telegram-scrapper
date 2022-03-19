from tempfile import TemporaryDirectory

from datetime import datetime, date
from django.utils import timezone
from django.conf import settings
from django.contrib.postgres.search import SearchVector
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.db.utils import IntegrityError
from telethon import TelegramClient, sync
from telethon.tl.types import PeerUser
from telegram_scrapper.core.models import MEDIAS, Message, Group, Report

import glob
import json


MESSAGES_PER_QUERY = 1000


class Command(BaseCommand):
    help = "Scrap Telegram messages"

    @property
    def telegram_client(self):
        if not getattr(self, "_telegram_client", None):
            self._telegram_client = TelegramClient(
                "message_scrapping", settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH
            ).start()

        return self._telegram_client

    def add_arguments(self, parser):
        parser.add_argument(
            "limit",
            type=int,
            help="Number of messages to retrieve in each query",
            default=MESSAGES_PER_QUERY,
        )

    def handle(self, *args, **options):
        query_size = options["limit"]
        previous_count = Message.objects.count()

        self._fetch_new_messages(query_size)
        self._update_search_vector()
        self.telegram_client.disconnect()

        total = Message.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f"{total - previous_count} new messages saved!")
        )
        self.stdout.write(self.style.SUCCESS(f"{total} messages stored!"))

    def _fetch_new_messages(self, query_size):
        groups = Group.objects.filter(active=True)
        for group in groups:
            self._update_group_messages(group.id, query_size)
            self._update_group_reports(group.id)

    def _update_search_vector(self):
        messages = Message.objects.filter(search_vector=None)
        self.stdout.write(f"Creating search vector for {messages.count()} messages…")

        search_vector = (
            SearchVector("message", config="portuguese", weight="A")
            + SearchVector("group", config="portuguese", weight="B")
            + SearchVector("sender", config="portuguese", weight="C")
        )

        messages.update(search_vector=search_vector)
        self.stdout.write(self.style.SUCCESS("Done!"))

    def _update_group_messages(self, group, query_size):
        self.stdout.write(f"Fetching {group} messages…")
        messages = self.telegram_client.get_messages(group, query_size)
        for message in messages:
            try:
                self._save_message(message, group)
            except IntegrityError as e:
                pass
            except Exception as e:  # Unpredicted errors trap :/
                raise CommandError(f"Erro baixando mensagens de {group}: {e}")

    def _save_message(self, message, group):
        obj = Message(
            message_id=message.id,
            message=message.message if message.message else '',
            group=group,
            sender=self._get_sender(message),
            sent_at=message.date,
            forwarded=bool(message.forward),
        )

        for kind in MEDIAS:
            media = getattr(message, kind)
            if not media:
                continue

            setattr(obj, kind, media.to_json())

        obj.save()

    def _get_sender(self, message):
        return (
            message.from_id.user_id if type(message.from_id) is PeerUser else "channel"
        )

    def _update_group_reports(self, group_id):
        self.stdout.write("Updating reports...")

        self._update_messages_count(group_id)
        self._update_group_activity(group_id)

        self.stdout.write("done.")

    def _update_messages_count(self, group_id):
        group = Group.objects.get(id=group_id)
        group.messages_count = Message.objects.filter(group=group_id).count()
        group.save()

    def _update_group_activity(self, group_id):
        activity = list(Message.objects.filter(group=group_id).order_by('-sent_at').annotate(date=TruncDate('sent_at')).order_by('date').values('date').annotate(**{'total': Count('sent_at')}))
        Report.objects.update_or_create(
            id=f"group_activity_{group_id}",
            defaults={'report_data': json.dumps(activity, default=_parse_date_to_json), 'updated_at': timezone.now()}
        )


def _parse_date_to_json(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    return str(obj)
