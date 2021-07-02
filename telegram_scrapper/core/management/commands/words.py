# TODO migrar extrac.py para cá
#  Referêcia https://docs.djangoproject.com/en/3.2/howto/custom-management-commands/

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Word help message"

    def handle(self, *args, **options):
        raise CommandError("TODO")
