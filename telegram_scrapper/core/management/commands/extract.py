from tempfile import TemporaryDirectory

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from telethon import TelegramClient

from telegram_scrapper.core.models import MEDIAS, Message


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

    def messages_from(self, group, number):
        return self.telegram_client.get_messages(group, number)

    def save_message(self, message, group):
        obj = Message(
            message_id=message.id,
            group=group,
            sender=message.from_id.user_id if message.from_id else "channel",
            sent_at=message.date,
            forwarded=bool(message.forward),
        )

        with TemporaryDirectory() as tmp:
            for kind in MEDIAS:
                media = getattr(message, kind)
                if not media:
                    continue

                # TODO Mudar campos no modelo de JSONField para FileField e salvar
                # path = Path(tmp) / media.id
                # self.telegram_client.download_media(message=media, file=path)
                setattr(obj, kind, media.to_json())

            return obj
            obj.save()

    def update_group_messages(self, group, number):
        self.stdout.write(f"Fetching {group} messages…")
        for message in self.messages_from(group, number):
            try:
                self.save_message(message, group)
            except Exception as e:  # TODO que erros esperamos aqui?
                raise CommandError(f"Erro baixando mensagens de {group}: {e}")

    def handle(self, *args, **options):
        self.stdout.write(options["limit"])
        previous_count = Message.objects.count()
        for group in settings.TELEGRAM_GROUPS:
            self.update_group_messages(group)

        total = Message.objects.count()
        self.stdout.write(self.style.SUCCESS(f"{total - previous} new messages saved!"))
        self.stdout.write(self.style.SUCCESS(f"{total} messages stored!"))
