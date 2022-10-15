from django.conf import settings
from django.core.management.base import BaseCommand
from telethon import TelegramClient, sync
from telethon.errors.rpcerrorlist import ChatAdminRequiredError
from telegram_scrapper.core.models import Group, TelegramUser
from telethon.tl.types import ChannelParticipantsRecent
from telethon.tl.functions.channels import GetFullChannelRequest


class Command(BaseCommand):
    help = "Scrap Telegram users from saved messages"

    @property
    def telegram_client(self):
        if not getattr(self, "_telegram_client", None):
            self._telegram_client = TelegramClient(
                "user_scrapping", settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH
            ).start()

        return self._telegram_client

    def handle(self, *args, **options):
        previous_count = TelegramUser.objects.count()

        self._get_from_groups()

        total = TelegramUser.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f"{total - previous_count} new users found!")
        )
        self.stdout.write(f"{total} users stored!")
        self.telegram_client.disconnect()

    def _get_from_groups(self):
        groups = Group.objects.filter(active=True)
        for group in groups:
            self.stdout.write(f"Retrieving users from {group.id}...")
            try:
                group_info = self.telegram_client(GetFullChannelRequest(channel=group.id))
                group.users_count = group_info.full_chat.participants_count
                group.save()

                [self._save_user(p) for p in self.telegram_client.iter_participants(group.id, filter=ChannelParticipantsRecent)]

            except ChatAdminRequiredError as e:
                self.stdout.write("Cannot check user list, skipping.")
            except TypeError as e:
                self.stdout.write(f"Type error, probably a Telethon bug. Try to update the library => {e}.")
            except Exception as e:  # Unpredicted errors trap :/
                self.stderr.write(f"Error fetching users from {group.id}: {e}")

    def _save_user(self, user):
        obj = TelegramUser(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            photo=user.photo.to_json() if user.photo else None,
            fake=bool(user.fake),
            deleted=bool(user.deleted),
            verified=bool(user.verified),
        )

        obj.save()
