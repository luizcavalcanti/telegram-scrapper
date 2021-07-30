from tempfile import TemporaryDirectory

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
from telethon import TelegramClient, sync
from telethon.tl.types import PeerUser
from telegram_scrapper.core.models import MEDIAS, Message, Group

import glob


MESSAGES_PER_QUERY = 1000


class Command(BaseCommand):
    help = "Scrap Telegram messages"

    @property
    def telegram_client(self):
        if not getattr(self, "_telegram_client", None):
            self._telegram_client = TelegramClient(
                "session_name", settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH
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

        groups = Group.objects.filter(active=True)
        for group in groups:
            self.update_group_messages(group.id, query_size)

        total = Message.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f"{total - previous_count} new messages saved!")
        )
        self.stdout.write(self.style.SUCCESS(f"{total} messages stored!"))

    def update_group_messages(self, group, query_size):
        self.stdout.write(f"Fetching {group} messages…")
        messages = self.telegram_client.get_messages(group, query_size)
        for message in messages:
            try:
                self.save_message(message, group)
            except IntegrityError as e:
                pass
            except Exception as e:  # TODO que erros esperamos aqui?
                raise CommandError(f"Erro baixando mensagens de {group}: {e}")

    def save_message(self, message, group):
        obj = Message(
            message_id=message.id,
            message=message.message,
            group=group,
            sender=self.get_sender(message),
            sent_at=message.date,
            forwarded=bool(message.forward),
        )

        for kind in MEDIAS:
            media = getattr(message, kind)
            if not media:
                continue

            setattr(obj, kind, media.to_json())

        # TODO: move to a separated command
        # with TemporaryDirectory() as tmp:
        #     # TODO Mudar campos no modelo de JSONField para FileField e salvar
        #     path = f"{tmp}/{media.id}"
        #     if not glob.glob(f"{path}*"):
        #         self.stdout.write(f"\tdownloading media {media.id}...")
        #         self.telegram_client.download_media(message=media, file=path)
        #     return obj

        obj.save()

    def get_sender(self, message):
        return (
            message.from_id.user_id if type(message.from_id) is PeerUser else "channel"
        )
