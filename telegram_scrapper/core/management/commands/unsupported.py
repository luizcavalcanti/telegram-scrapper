from tempfile import TemporaryDirectory

from datetime import datetime, date
from django.utils import timezone
from django.conf import settings
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

        groups = Group.objects.filter(active=True).order_by('-id')
        for group in groups:
            self._update_group_messages(group.id, query_size)

        total = Message.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f"{total - previous_count} new messages saved!")
        )
        self.stdout.write(self.style.SUCCESS(f"{total} messages stored!"))
        self.telegram_client.disconnect()

    def _update_group_messages(self, group, query_size):
        self.stdout.write(f"Fetching {group} messages…")
        messages = self.telegram_client.get_messages(group, query_size)
        for message in messages:
            try:
                self._save_message(message, group)
            except Message.DoesNotExist as e:
                pass
            except Exception as e:  # TODO que erros esperamos aqui?
                raise CommandError(f"Erro baixando mensagens de {group}: {type(e)} {e}")

    def _save_message(self, message, group):
        old_msg = Message.objects.get(message_id=message.id, group=group)
        if old_msg and old_msg.sender=='1926801217':
            print(f"Mensagem antiga não suportada! {old_msg.message_id}")
            old_msg.sender = self._get_sender(message)
            old_msg.save()
            return

    def _get_sender(self, message):
        return (
            message.from_id.user_id if type(message.from_id) is PeerUser else "channel"
        )
