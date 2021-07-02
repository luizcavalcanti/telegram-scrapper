from telethon import TelegramClient, sync
import sqlite3
import os
import glob

MEDIA_DIR='media'

INSERT_MESSAGE_SQL = '''
INSERT INTO messages (message_id, group_id, sender_id, send_date, message, video, audio, document, photo, forward)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
'''

def create_database(conn):
    conn.execute('''
    CREATE TABLE IF NOT EXISTS messages(
         message_id  INT PRIMARY KEY NOT NULL,
         group_id    TEXT NOT NULL,
         sender_id   TEXT NOT NULL,
         send_date   DATETIME NOT NULL,
         message     TEXT,
         video       TEXT,
         audio       TEXT,
         document    TEXT,
         photo       TEXT,
         forward     BOOLEAN
     );
     ''')


def message_count(conn):
    result = conn.execute("SELECT COUNT(*) FROM messages;")
    for row in result:
        return row[0]


def insert_message(conn, group_name, message):
    video = message.video.to_json() if message.video else None
    audio = message.audio.to_json() if message.audio else None
    document = message.document.to_json() if message.document else None
    photo = message.photo.to_json() if message.photo else None
    forward = True if message.forward else False

    user_id = message.from_id.user_id if message.from_id else 'channel'

    cur = conn.cursor()
    cur.execute(
        INSERT_MESSAGE_SQL, 
        (message.id, group_name, user_id, message.date, message.message, video, audio, document, photo, forward, )
    )
    conn.commit()


def create_telegram_client():
    api_id = os.environ['TELEGRAM_API_ID']
    api_hash = os.environ['TELEGRAM_API_HASH']
    return TelegramClient('session_name', api_id, api_hash).start()


def get_messages(client, group_name, message_number):
    return client.get_messages(group_name, message_number)


def download_media(media):
    file_id = media.id
    file_name = f"{MEDIA_DIR}/{file_id}"
    if not glob.glob(f"{file_name}*"):
        print(f"\tdownloading media {media.id}...")
        client.download_media(message=media, file=file_name)


def download_media_from_message(message):
    if message.photo:
        download_media(message.photo)

    if message.audio:
        download_media(message.audio)

    if message.video:
        download_media(message.video)

    if message.document:
        download_media(message.document)


def update_group_messages(client, conn, group_name, message_number):
    print(f"Fetching {group_name} messages")
    messages = get_messages(client, group_name, messages_per_query)

    for message in messages:
        try:
            download_media_from_message(message)
            insert_message(conn, group_name, message)
        except Exception as e:
            # print(e)
            pass


############################################# 

messages_per_query = 1000

conn = sqlite3.connect('messages.db')
create_database(conn)
client = create_telegram_client()

groups = [
    'drmarcelofrazao38', 'direitaRiodedejaneiro', 
    'SomosAlianca', 'aliancapelobrasil', 
    'aliancacombolsonaro', 'derrubandoaspedrasguiasdageorgia',
    'ucranizabrasil', 'censuralivrebr', 'BOLSONARO_APB',
    'MATRIX_A_TOCA_DO_COELHO', 'despertareinevitavel'
]

for group in groups:
    update_group_messages(client, conn, group, messages_per_query)

print(f"{message_count(conn)} messages stored") 