from django.core.management.base import BaseCommand
from django.contrib.postgres.search import SearchVector

from telegram_scrapper.models import Message


class Command(BaseCommand):
    def handle(self, *args, **options):
        qs = Message.objects.all()
        self.stdout.write("Creating search vector for {qs.count()} messages…")
        self.stdout.write("This takes several minutes/hours.")

        search_vector = (
            SearchVector("message", config="portuguese", weight="A")
            + SearchVector("group", config="portuguese", weight="B")
            + SearchVector("sender", config="portuguese", weight="C")
        )

        qs.update(search_vector=search_vector)
        self.stdout.write(self.style.SUCCESS("Done!"))
