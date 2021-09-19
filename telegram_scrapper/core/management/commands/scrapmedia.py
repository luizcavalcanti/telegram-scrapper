import boto3
import hashlib

from django.conf import settings
from django.core.management.base import BaseCommand
from telethon import TelegramClient, sync
from telethon.tl.types import (
    InputMessagesFilterChatPhotos,
    InputMessagesFilterMusic,
    InputMessagesFilterPhotos,
    InputMessagesFilterPhotoVideo,
)
from telegram_scrapper.core.models import Message, Group

MAX_MEDIA_SIZE = 250 * 1024 * 1024  # 250MB


class Command(BaseCommand):
    help = "Scrap Telegram media from saved messages"

    @property
    def telegram_client(self):
        if not getattr(self, "_telegram_client", None):
            self._telegram_client = TelegramClient(
                "session_name", settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH
            ).start()

        return self._telegram_client

    @property
    def s3_client(self):
        if not getattr(self, "_s3_client", None):
            self._s3_client = boto3.client(
                's3',
                region_name=settings.AWS_S3_REGION_NAME,
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
        return self._s3_client

    @property
    def s3_base_public_url(self):
        if not getattr(self, "_s3_base_public_url", None):
            self._s3_base_public_url = settings.AWS_S3_PUBLIC_BASE_URL
        return self._s3_base_public_url

    def add_arguments(self, parser):
        parser.add_argument(
            "limit", type=int, help="Max number of media messages in each query"
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        groups = Group.objects.filter(active=True)
        for group in groups:
            self._download_media_for_group(group.id, limit)

    def _download_media_for_group(self, group, limit):
        self._download_images_for_group(InputMessagesFilterPhotos, group, limit)
        self._download_images_for_group(InputMessagesFilterPhotoVideo, group, limit)
        self._download_images_for_group(InputMessagesFilterChatPhotos, group, limit)
        self._download_music_for_group(group, limit)

    def _download_images_for_group(self, media_filter, group, limit):
        image_messages = self.telegram_client.get_messages(
            group, limit, filter=media_filter
        )
        for message in image_messages:
            self._download_image(message, group)

    def _download_image(self, message, group):
        local_message = Message.objects.filter(
            message_id=message.id, group=group
        ).first()

        media = message.photo if message.photo else None

        if media and self._should_download_image(local_message):
            try:
                self.stdout.write(f"[{group}] Downloading media for {local_message.id}")
                local_message.photo_url = self._upload_media(media, message.file.ext)
                local_message.save()
                self.stdout.write(f"[{group}] Uploaded {local_message.photo_url}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Untreated error: {e}"))

    def _should_download_image(self, message):
        return message and not bool(message.photo_url)

    def _download_music_for_group(self, group, limit):
        audio_messages = self.telegram_client.get_messages(
            group, limit, filter=InputMessagesFilterMusic
        )

        for msg in audio_messages:
            local_message = Message.objects.filter(
                message_id=msg.id, group=group
            ).first()

            if self._should_download_audio(local_message):
                if msg.audio.size > MAX_MEDIA_SIZE:
                    self.stdout.write(
                        f"[{group}] Skipping media for {local_message.id}. Too large"
                        f" ({msg.audio.size}b)"
                    )
                    continue

                try:
                    self.stdout.write(
                        f"[{group}] Downloading media for {local_message.id}"
                    )
                    local_message.audio_url = self._upload_media(msg.audio, ".mp3")
                    local_message.save()
                    self.stdout.write(f"[{group}] Uploaded {local_message.audio_url}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Untreated error: {e}"))

    def _should_download_audio(self, message):
        return message and not bool(message.audio_url)

    def _upload_media(self, media, extension):
        if not extension:
            raise CommandError(f"Media has no extension")

        file_bytes = self.telegram_client.download_media(media, file=bytes)

        file_hash = hashlib.md5()
        file_hash.update(file_bytes)

        file_name = f"{file_hash.hexdigest()}{extension}"
        self.s3_client.put_object(
            Body=file_bytes,
            Bucket=f"{settings.AWS_STORAGE_BUCKET_NAME}",
            Key=file_name,
            ACL='public-read',
            CacheControl='max-age=31556926',
        )

        return f"{self.s3_base_public_url}/{file_name}"
