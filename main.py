import os
from dotenv import load_dotenv
from telethon import TelegramClient
import telethon
import logging

logging.basicConfig(level=logging.DEBUG)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(telethon.events.NewMessage(pattern='/start'))
async def handle_start(event: telethon.events.NewMessage):
    pass

bot.start()
bot.run_until_disconnected()