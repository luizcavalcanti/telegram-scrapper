import json
import re

from unidecode import unidecode
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand, CommandError
from telegram_scrapper.core.models import Message

SANITIZIATION_PATTERN = re.compile(r"[\W_]")
URL_PATTERN = re.compile(r"http[Ss]")
EMOJI_PATTERN = re.compile(
    pattern="["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "]+",
    flags=re.UNICODE,
)

EXCLUDED_GROUPS = [
    "epochtimeschat",
    "ConservativeNewsToday",
    "TrumpJrChat",
    "bioevoluciongrupo",
    "KanekoaChat",
    "PagsChat",
]


class TrendsService:

    def __init__(self):
        with open('stopwords.txt') as f:
            lines = f.read().splitlines()
            self.stopwords = set(map(str.strip(), lines))

    def word_frequency(self, top_terms_count=10, past_days=1):
        words = self._generate_word_frequency(past_days)
        sorted_words = {
            k: v
            for k, v in sorted(words.items(), key=lambda item: item[1], reverse=True)[
                :top_terms_count
            ]
        }
        return sorted_words

    def _generate_word_frequency(self, past_days=1):
        words = {}

        start_date = datetime.today() - timedelta(days=past_days)

        messages = (
            Message.objects.filter(sent_at__gte=start_date, message__isnull=False)
            .exclude(message="")
            .exclude(group__in=EXCLUDED_GROUPS)
        )

        for message in messages.iterator():
            pieces = re.split(r"[\s]", message.message)

            for word in pieces:
                word = self._sanitize(word)
                if self._is_valid_word(word):
                    if word not in words:
                        words[word] = 0
                    words[word] += 1

        return words

    def _sanitize(self, word):
        word = unidecode(word).lower()
        word = re.sub(r"[áãâä]", "a", word)
        word = re.sub(r"[ç]", "c", word)
        word = re.sub(r"[êéë]", "e", word)
        word = re.sub(r"[íï]", "i", word)
        word = re.sub(r"[õóôö]", "o", word)
        word = re.sub(r"[úûü']", "u", word)
        word = re.sub(r"[^\w]", "", word)
        return re.sub(SANITIZIATION_PATTERN, "", word)

    def _is_valid_word(self, word):
        return (
            len(word) > 1
            and not self._is_stopword(word)
            and not self._is_url(word)
            and not word.isdigit()
        )

    def _is_stopword(self, word):
        return word in self.stopwords

    def _is_url(self, word):
        return word.find("http") >= 0

    def _remove_emojis(self, word):
        return re.sub(EMOJI_PATTERN, "", word)
