import boto3

from datetime import date, timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from telegram_scrapper.core.models import Message

class Command(BaseCommand):
    help = "Clean stored media older than x days"

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
            "days", type=int, help="Number of days old a media should be kept"
        )

    def handle(self, *args, **options):
        days = options["days"]
        end_date = date.today() - timedelta(days=days)
        self.stdout.write(f"Deleting media up to {end_date}...")
        self._delete_old_photos(end_date);
        self._delete_old_videos(end_date);
        self._delete_old_audios(end_date);


    def _delete_old_photos(self, end_date):
        messages = Message.objects.filter(photo_url__isnull=False, sent_at__lte=end_date)
        for message in messages.iterator():
            print(f"Removing {message.photo_url}...")
            self._delete_media(message.photo_url)
            message.photo_url = None
            message.save()

    def _delete_old_videos(self, end_date):
        messages = Message.objects.filter(video_url__isnull=False, sent_at__lte=end_date)
        for message in messages.iterator():
            print(f"Removing {message.video_url}...")
            self._delete_media(message.video_url)
            message.video_url = None
            message.save()

    def _delete_old_audios(self, end_date):
        messages = Message.objects.filter(audio_url__isnull=False, sent_at__lte=end_date)
        for message in messages.iterator():
            print(f"Removing {message.audio_url}...")
            self._delete_media(message.audio_url)
            message.audio_url = None
            message.save()

    def _delete_media(self, media_url):
        file_name = media_url.split('/')[-1]
        bucket_name = f"{settings.AWS_STORAGE_BUCKET_NAME}"
        self.s3_client.delete_object(Bucket=bucket_name, Key=file_name)