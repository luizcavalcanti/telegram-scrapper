import boto3
import hashlib

from datetime import date, timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from telethon import TelegramClient, sync
from telethon.tl.types import (
    InputMessagesFilterChatPhotos,
    InputMessagesFilterMusic,
    InputMessagesFilterPhotos,
    InputMessagesFilterUrl,
    InputMessagesFilterVideo,
)
from telegram_scrapper.core.models import Message, Group

MAX_AUDIO_SIZE = 250 * 1024 * 1024  # 250MB
MAX_VIDEO_SIZE = 150 * 1024 * 1024  # 150MB
MAX_MEDIA_AGE = 90 # in days

extension_to_mime = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.mp3': 'audio/mpeg',
    '.mp4': 'video/mp4',
}

image_filters = [
    InputMessagesFilterPhotos,
    InputMessagesFilterChatPhotos,
    InputMessagesFilterUrl,
]

video_filters = [InputMessagesFilterVideo]


class Command(BaseCommand):
    help = "Scrap Telegram media from saved messages"

    @property
    def telegram_client(self):
        if not getattr(self, "_telegram_client", None):
            self._telegram_client = TelegramClient(
                "media_scrapping", settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH
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
        parser.add_argument(
            "media_type",
            type=str,
            help="Media type to scrap [all, photo, video, audio]",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        media_type = options["media_type"]

        self.date_limit = date.today() - timedelta(days=MAX_MEDIA_AGE)

        groups = Group.objects.filter(active=True)
        for group in groups:
            try:
                self.stdout.write(f"Fetching {group.id}...")
                self._download_media_for_group(group.id, limit, media_type)
            except Exception as e:  # Unpredicted errors trap :/
                self.stderr.write(f"Error fetching media from {group.id}: {e}")

        self.telegram_client.disconnect()

    def _download_media_for_group(self, group, limit, media_type):
        if media_type in ['all', 'photo']:
            for media_filter in image_filters:
                self._download_images_for_group(media_filter, group, limit)

        if media_type in ['all', 'video']:
            for media_filter in video_filters:
                self._download_videos_for_group(media_filter, group, limit)

        if media_type in ['all', 'audio']:
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

    def _download_videos_for_group(self, media_filter, group, limit):
        video_messages = self.telegram_client.get_messages(
            group, limit, filter=media_filter
        )
        for message in video_messages:
            self._download_video(message, group)

    def _download_video(self, message, group):
        local_message = Message.objects.filter(
            message_id=message.id, group=group
        ).first()

        media = message.video

        if media and self._should_download_video(local_message):
            if media.size > MAX_VIDEO_SIZE:
                self.stdout.write(
                    f"[{group}] Skipping video for {local_message.id}. Too large"
                    f" ({media.size/(1024*1024):.2f} MB)"
                )
                return

            try:
                self.stdout.write(f"[{group}] Downloading media for {local_message.id}")
                local_message.video_url = self._upload_media(media, message.file.ext)
                local_message.save()
                self.stdout.write(f"[{group}] Uploaded {local_message.video_url}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Untreated error: {e}"))

    def _download_music_for_group(self, group, limit):
        audio_messages = self.telegram_client.get_messages(
            group, limit, filter=InputMessagesFilterMusic
        )

        for msg in audio_messages:
            local_message = Message.objects.filter(
                message_id=msg.id, group=group
            ).first()

            if self._should_download_audio(local_message):
                if not msg.audio:
                    self.stdout.write(f"[{group}] Message {local_message.id} has no audio content")
                    continue
                if msg.audio.size > MAX_AUDIO_SIZE:
                    self.stdout.write(
                        f"[{group}] Skipping audio for {local_message.id}. Too large"
                        f" ({msg.audio.size/(1024*1024):.2f} MB)"
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

    def _should_download_image(self, message):
        return message and message.sent_at.date() > self.date_limit and not bool(message.photo_url)

    def _should_download_video(self, message):
        return message and message.sent_at.date() > self.date_limit and not bool(message.video_url)

    def _should_download_audio(self, message):
        return message and message.sent_at.date() > self.date_limit and not bool(message.audio_url)

    def _duplicate_media_url(self, media):
        urls = Message.objects.filter(media_id=media.id).values_list('photo_url', 'video_url', 'audio_url').distinct()
        if urls:
            for url in urls[0]:
                if url:
                    return url
        return None

    def _upload_media(self, media, extension):
        if not extension:
            raise CommandError(f"Media has no extension")

        downloaded_media_url = self._duplicate_media_url(media)
        if downloaded_media_url:
            print("Media already downloaded, reusing...")
            return downloaded_media_url
        else:
            file_bytes = self.telegram_client.download_media(media, file=bytes)

            file_hash = hashlib.md5()
            file_hash.update(file_bytes)

            file_name = f"{file_hash.hexdigest()}{extension}"
            mime_type = extension_to_mime.get(extension, 'binary/octet-stream')
            bucket_name = f"{settings.AWS_STORAGE_BUCKET_NAME}"

            try:
                # do nothing if file exists in bucket
                self.s3_client.head_object(Bucket=bucket_name, Key=file_name)
            except Exception as e:
                self.s3_client.put_object(
                    Body=file_bytes,
                    Bucket=bucket_name,
                    Key=file_name,
                    ACL='public-read',
                    CacheControl='max-age=31556926',
                    ContentType=mime_type,
                )

            return f"{self.s3_base_public_url}/{file_name}"
