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
STOPWORDS = [
    "a",
    "a",
    "agora",
    "ao",
    "aos",
    "aquela",
    "aquelas",
    "aquele",
    "aqueles",
    "aquilo",
    "as",
    "as",
    "ate",
    "bem",
    "bom",
    "ciao",
    "com",
    "como",
    "da",
    "das",
    "de",
    "dela",
    "delas",
    "dele",
    "deles",
    "depois",
    "dia",
    "do",
    "dos",
    "e",
    "e",
    "ela",
    "elas",
    "ele",
    "eles",
    "em",
    "entre",
    "era",
    "eram",
    "eramos",
    "essa",
    "essas",
    "esse",
    "esses",
    "esta",
    "esta",
    "estamos",
    "estao",
    "estar",
    "estas",
    "estava",
    "estavam",
    "estavamos",
    "este",
    "esteja",
    "estejam",
    "estejamos",
    "estes",
    "esteve",
    "estive",
    "estivemos",
    "estiver",
    "estivera",
    "estiveram",
    "estiverem",
    "estivermos",
    "estivesse",
    "estivessem",
    "estivessemos",
    "estivéramos",
    "estou",
    "eu",
    "fazer",
    "foi",
    "fomos",
    "for",
    "fora",
    "foram",
    "foramos",
    "forem",
    "formos",
    "fosse",
    "fossem",
    "fossemos",
    "fui",
    "ha",
    "haja",
    "hajam",
    "hajamos",
    "hao",
    "havemos",
    "haver",
    "hei",
    "houve",
    "houvemos",
    "houver",
    "houvera",
    "houvera",
    "houveram",
    "houveramos",
    "houverao",
    "houverei",
    "houverem",
    "houveremos",
    "houveria",
    "houveriam",
    "houveriamos",
    "houvermos",
    "houvesse",
    "houvessem",
    "houvessemos",
    "isso",
    "isto",
    "ja",
    "la",
    "lhe",
    "lhes",
    "mais",
    "mas",
    "me",
    "mesmo",
    "meu",
    "meus",
    "minha",
    "minhas",
    "muito",
    "na",
    "nao",
    "nas",
    "nem",
    "no",
    "nos",
    "nos",
    "nossa",
    "nossas",
    "nosso",
    "nossos",
    "num",
    "numa",
    "o",
    "os",
    "ou",
    "para",
    "pela",
    "pelas",
    "pelo",
    "pelos",
    "pode",
    "por",
    "pra",
    "qual",
    "quando",
    "que",
    "quem",
    "sao",
    "se",
    "seja",
    "sejam",
    "sejamos",
    "sem",
    "ser",
    "sera",
    "serao",
    "serei",
    "seremos",
    "seria",
    "seriam",
    "seriamos",
    "seu",
    "seus",
    "so",
    "sobre",
    "somos",
    "sou",
    "sua",
    "suas",
    "tambem",
    "te",
    "tem",
    "tem",
    "temos",
    "tenha",
    "tenham",
    "tenhamos",
    "tenho",
    "tera",
    "terao",
    "terei",
    "teremos",
    "teria",
    "teriam",
    "teriamos",
    "teu",
    "teus",
    "teve",
    "tinha",
    "tinham",
    "tinhamos",
    "tive",
    "tivemos",
    "tiver",
    "tivera",
    "tiveram",
    "tiveramos",
    "tiverem",
    "tivermos",
    "tivesse",
    "tivessem",
    "tivessemos",
    "tu",
    "tua",
    "tuas",
    "tudo",
    "um",
    "uma",
    "vai",
    "vamos",
    "video",
    "voce",
    "voces",
    "vos",
]
EXCLUDED_GROUPS = [
    "epochtimeschat",
    "ConservativeNewsToday",
    "TrumpJrChat",
    "bioevoluciongrupo",
    "KanekoaChat",
    "PagsChat",
]


class TrendsService:
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

        print("Fetching all text messages")
        messages = (
            Message.objects.filter(sent_at__gte=start_date, message__isnull=False)
            .exclude(message="")
            .exclude(group__in=EXCLUDED_GROUPS)
        )
        print(f"{messages.count()} messages found")

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
        return word in STOPWORDS

    def _is_url(self, word):
        return word.find("http") >= 0

    def _remove_emojis(self, word):
        return re.sub(EMOJI_PATTERN, "", word)
