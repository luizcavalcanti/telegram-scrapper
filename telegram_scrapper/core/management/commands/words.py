import json
import re

from unidecode import unidecode

from django.core.management.base import BaseCommand, CommandError
from telegram_scrapper.core.models import Message

SANITIZIATION_PATTERN = re.compile(r"[\W_]")
URL_PATTERN = re.compile(r"http[Ss]")
EMOJI_PATTERN = re.compile(
    pattern="["
    u"\U0001F600-\U0001F64F"  # emoticons
    u"\U0001F300-\U0001F5FF"  # symbols & pictographs
    u"\U0001F680-\U0001F6FF"  # transport & map symbols
    u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "]+",
    flags=re.UNICODE,
)
STOPWORDS = [
    'a',
    'à',
    'e',
    'o',
    'é',
    'os',
    'as',
    'que',
    'do',
    'da',
    'dos',
    'das',
    'de',
    'para',
    'no',
    'em',
    'não',
    'nao',
    'se',
    'por',
    'mais',
    'um',
    'uma',
    'como',
    'foi',
    'com',
    'na',
    'ao',
    'tem',
    'está',
    'esta',
    'são',
]


class Command(BaseCommand):
    help = "Generate a dataset with words frequency by date"

    def add_arguments(self, parser):
        parser.add_argument(
            "term", type=str, help="Termo a ser contabilizado", default=None
        )

    def handle(self, *args, **options):
        term = options["term"]
        if term:
            words = self._generate_single_term_frequency(term)
        else:
            words = self._generate_word_frequency()

        self.stdout.write(f"{len(words)} unique words found")

        json_file = json.dumps(words)
        f = open("words.json", "w")
        f.write(json_file)
        f.close()
        self.stdout.write(self.style.SUCCESS("done"))

    def _generate_single_term_frequency(self, term):
        words = {}

        sanitized_term = self.sanitize(term)
        words[sanitized_term] = {}

        self.stdout.write("Fetching all text messages")
        messages = Message.objects.exclude(message='')

        for message in messages.iterator(chunk_size=100):
            pieces = re.split(r"[\s]", message.message)
            date = f"{message.sent_at:%Y-%m-%d}"

            for word in pieces:
                sanitized_word = self.sanitize(word)
                if sanitized_word == sanitized_term:
                    words[sanitized_term][date] = words[sanitized_term].get(date, 0) + 1

        return words

    def _generate_word_frequency(self):
        words = {}

        self.stdout.write("Fetching all text messages")
        messages = Message.objects.exclude(message='')

        for message in messages.iterator(100):
            pieces = re.split(r"[\s]", message.message)
            date = f"{message.sent_at:%Y-%m-%d}"

            for word in pieces:
                word = self.sanitize(word)
                if self.is_valid_word(word):
                    if word not in words:
                        words[word] = {}
                    words[word][date] = words[word].get(date, 0) + 1

        return words

    def sanitize(self, word):
        word = unidecode(word).lower()
        word = re.sub(r"[áãâä]", 'a', word)
        word = re.sub(r"[ç]", 'c', word)
        word = re.sub(r"[êéë]", 'e', word)
        word = re.sub(r"[íï]", 'i', word)
        word = re.sub(r"[õóôö]", 'o', word)
        word = re.sub(r"[úûü']", 'u', word)
        word = re.sub(r"[^\w]", '', word)
        return re.sub(SANITIZIATION_PATTERN, '', word)

    def is_stopword(self, word):
        return word in STOPWORDS

    def is_url(self, word):
        return word.find('http') >= 0

    def remove_emojis(self, word):
        return re.sub(EMOJI_PATTERN, '', word)

    def is_valid_word(self, word):
        return (
            len(word) > 0
            and not self.is_stopword(word)
            and not self.is_url(word)
            and not word.isdigit()
        )
