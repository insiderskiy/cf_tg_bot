import logging
import os
import uuid

from cachetools import LRUCache
from dotenv import load_dotenv
from furl import furl
from telethon import TelegramClient, Button
from telethon.events import NewMessage, Raw, CallbackQuery
from telethon.tl.types import ChannelParticipantsAdmins

logging.basicConfig(level=logging.DEBUG)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
CHANNEL_WITH_COMPLEXES_ID = os.getenv("CHANNEL_WITH_COMPLEXES")

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

uuid_cache = LRUCache(maxsize=100)

async def can_add_new_complex(id) -> bool:
    async for user in bot.iter_participants(CHANNEL_WITH_COMPLEXES_ID, filter=ChannelParticipantsAdmins()):
        if user.id == id:
            return True
    return False


@bot.on(NewMessage(incoming=True, pattern='/start'))
async def handle_start(event: NewMessage):
    sender = await event.get_sender()
    sender_id = sender.id
    if await can_add_new_complex(sender_id):

        data = furl("/create_complex")
        complex_uuid = str(uuid.uuid4())
        data.add({'uuid':complex_uuid})
        uuid_cache[complex_uuid] = True

        await bot.send_message(
            sender_id,
            "Выберите действие",
            buttons=[
                Button.inline(
                    text="Добавить комплекс",
                    data=data
                ),
            ],
        )


@bot.on(CallbackQuery(pattern="/create_complex"))
async def handle_create_complex(query):
    sender_id = (await query.get_sender()).id
    complex_uuid = furl(query.data.decode('utf-8')).args['uuid']
    if complex_uuid in uuid_cache:
        pass

@bot.on(Raw())
async def handle_raw(raw):
    print(raw)


bot.start()
bot.run_until_disconnected()
