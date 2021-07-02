# TODO migrar extrac.py para cá
#  Referêcia https://docs.djangoproject.com/en/3.2/howto/custom-management-commands/

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Plot help message"

    def add_arguments(self, parser):
        parser.add_argument("term", metavar="term", help="Term to plot")

    def handle(self, *args, **options):
        print(options["term"])
        raise CommandError("TODO")
