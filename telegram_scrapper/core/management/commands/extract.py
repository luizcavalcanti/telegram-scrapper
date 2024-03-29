from tempfile import TemporaryDirectory

from datetime import datetime, date
from django.utils import timezone
from django.conf import settings
from django.contrib.postgres.search import SearchVector
from django.core.management.base import BaseCommand, CommandError
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.db.utils import IntegrityError
from telethon import TelegramClient, sync
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import PeerUser, MessageActionChatAddUser

from telegram_scrapper.api.services import ReportsService
from telegram_scrapper.core.models import MEDIAS, Message, Group, Report

import glob
import json
import warnings


MESSAGES_PER_QUERY = 1000


class Command(BaseCommand):
    help = "Scrap Telegram messages"

    @property
    def telegram_client(self):
        if not getattr(self, "_telegram_client", None):
            self._telegram_client = TelegramClient(
                "message_scrapping",
                settings.TELEGRAM_API_ID,
                settings.TELEGRAM_API_HASH,
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

        self._fetch_new_messages(query_size)
        self.telegram_client.disconnect()

        self._update_search_vector()
        self._update_general_reports()

        self.stdout.write(self.style.SUCCESS(f"OK"))

    def _fetch_new_messages(self, query_size):
        groups = Group.objects.filter(active=True)
        for group in groups:
            try:
                self.stdout.write(f"Fetching {group.id} messages…")
                if self._update_group_messages(group.id, query_size):
                    self._update_group_reports(group.id)
            except Exception as e:  # Unpredicted errors trap :/
                self.stderr.write(f"Error fetching messages from {group.id}: {e}")

    def _update_search_vector(self):
        messages = Message.objects.filter(search_vector=None)
        self.stdout.write(
            f"Creating search vector for {messages.count()} messages… ", ending=""
        )

        search_vector = (
            SearchVector("message", config="portuguese", weight="A")
            + SearchVector("group", config="portuguese", weight="B")
            + SearchVector("sender", config="portuguese", weight="C")
        )

        messages.update(search_vector=search_vector)
        self.stdout.write("done")

    def _update_group_messages(self, group, query_size):
        messages_saved = False
        messages = self.telegram_client.get_messages(group, query_size)
        for message in messages:
            if type(message.action) is not MessageActionChatAddUser:
                try:
                    self._save_message(message, group)
                    messages_saved = True
                except IntegrityError as e:
                    self.stderr.write(f"{e}")

        return messages_saved

    def _save_message(self, message, group):
        if Message.objects.filter(message_id=message.id, group=group).exists():
            return

        obj = Message(
            message_id=message.id,
            message=message.message if message.message else "",
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
            obj.media_id = media.id

        obj.save()

    def _get_sender(self, message):
        return (
            message.from_id.user_id if type(message.from_id) is PeerUser else "channel"
        )

    def _update_group_reports(self, group_id):
        warnings.filterwarnings("ignore")
        self.stdout.write("Updating reports… ", ending="")

        self._update_group_info(group_id)
        service = ReportsService()
        service.group_activity(group_id, force_generation=True)

        self.stdout.write("done")

    def _update_group_info(self, group_id):
        group_info = self.telegram_client(GetFullChannelRequest(channel=group_id))

        group = Group.objects.get(id=group_id)
        group.title = group_info.chats[0].title
        group.about = group_info.full_chat.about
        group.group_type = (
            "chat" if group_info.full_chat.can_view_participants else "channel"
        )
        group.messages_count = Message.objects.filter(group=group_id).count()
        group.save()

    def _update_group_activity(self, group_id):
        activity = list(
            Message.objects.filter(group=group_id)
            .order_by("-sent_at")
            .annotate(date=TruncDate("sent_at"))
            .order_by("date")
            .values("date")
            .annotate(**{"total": Count("sent_at")})
        )

        Report.objects.update_or_create(
            id=f"group_activity_{group_id}",
            defaults={
                "report_data": json.dumps(activity, cls=DjangoJSONEncoder),
                "updated_at": timezone.now(),
            },
        )

    def _update_general_reports(self):
        warnings.filterwarnings("ignore")

        self.stdout.write(f"Creating general reports… ")
        self.stdout.write(f"Summarization… ")

        Report.objects.update_or_create(
            id=f"general_messages",
            defaults={
                "report_data": json.dumps({"count": Message.objects.count()}),
                "updated_at": timezone.now(),
            },
        )

        service = ReportsService()

        self.stdout.write(f"Trending topics… ")
        service.trends(1, 20, force_generation=True)

        days = [7, 15, 30, 60, 90, 120, 180, 365]
        self.stdout.write(f"Messages per day and rankings… ")
        for days_count in days:
            service.messages_per_day(days_count, force_generation=True)
            service.top_users(days_count, 10, force_generation=True)

        self.stdout.write("done")
