import json
import re
import sqlite3

from unidecode import unidecode

SANITIZIATION_PATTERN = re.compile(r"[\W_]")
URL_PATTERN = re.compile(r"http[Ss]")
EMOJI_PATTERN = re.compile(pattern = "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags = re.UNICODE)


def is_stopword(word):
	return word in ['a', 'à', 'e', 'o', 'é', 'os', 'as', 
	'que', 'do', 'da', 'dos', 'das', 'de', 'para', 
	'no', 'em', 'não', 'nao', 'se', 'por', 'mais', 
	'um', 'uma', 'como', 'foi', 'com', 'na', 'ao', 
	'tem', 'está', 'esta', 'são']


def is_url(word):
	return word.find('http') >= 0


def sanitize(word):
	word = unidecode(word).lower()
	word = re.sub(r"[áãâä]", 'a', word)
	word = re.sub(r"[ç]", 'c', word)
	word = re.sub(r"[êéë]", 'e', word)
	word = re.sub(r"[íï]", 'i', word)
	word = re.sub(r"[õóôö]", 'o', word)
	word = re.sub(r"[úûü']", 'u', word)
	return re.sub(SANITIZIATION_PATTERN, '', word)


def remove_emojis(word):
	return re.sub(EMOJI_PATTERN, '', word)


def is_valid_word(word):
	return \
		len(word) > 0 and \
		not is_stopword(word) and \
	 	not is_url(word) and \
	 	not word.isdigit()

def create_words_freq_list():
	conn = sqlite3.connect('messages.db')

	cursor = conn.execute("SELECT message, date(send_date) FROM messages ORDER BY send_date")
	rows = cursor.fetchall()

	words = {}
	for row in rows:
		if (row[0]):
			date = row[1]
			split = re.split(r"[\s]", row[0])

			for word in split:
				word = sanitize(word)
				if is_valid_word(word):
					if word not in words:
						words[word] = {}
					words[word][date] = words[word].get(date, 0) + 1

	return words


########################

words = create_words_freq_list()

json = json.dumps(words)
f = open("words.json","w")
f.write(json)
f.close()