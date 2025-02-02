import logging
import os
from dotenv import load_dotenv
from furl import furl
from telethon import TelegramClient, Button
from telethon.events import NewMessage, Raw, CallbackQuery
from telethon.tl.types import ChannelParticipantsAdmins
from create_complex import handle_next_step_create_complex, handle_create_complex
from session import get_interaction_in_progress, CurrentInteraction

logging.basicConfig(level=logging.DEBUG)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
CHANNEL_WITH_COMPLEXES_ID = os.getenv("CHANNEL_WITH_COMPLEXES")

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

async def is_admin(id) -> bool:
    async for user in bot.iter_participants(CHANNEL_WITH_COMPLEXES_ID, filter=ChannelParticipantsAdmins()):
        if user.id == id:
            return True
    return False


async def handle_interaction_none(sender_id):
    if await is_admin(sender_id):
        data = furl("/create_complex")
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


@bot.on(NewMessage(incoming=True, pattern='/start'))
async def handle_start(event: NewMessage):
    sender_id = (await event.get_sender()).id
    current_interaction = get_interaction_in_progress(sender_id)
    if current_interaction is CurrentInteraction.NONE:
        await handle_interaction_none(sender_id)
    elif current_interaction is CurrentInteraction.COMPLEX_CREATION:
        await handle_next_step_create_complex(bot, sender_id, event)


@bot.on(CallbackQuery(pattern="/create_complex"))
async def handle_create_complex_callback(query):
    sender_id = (await query.get_sender()).id
    await handle_create_complex(bot, sender_id)


@bot.on(NewMessage(incoming=True))
async def handle_message(event: NewMessage):
    sender_id = (await event.get_sender()).id
    current_interaction = get_interaction_in_progress(sender_id)
    if current_interaction is CurrentInteraction.NONE:
        # TODO show help
        pass
    elif current_interaction is CurrentInteraction.COMPLEX_CREATION:
        await handle_next_step_create_complex(bot, sender_id, event)
    else:
        # TODO show help
        pass


@bot.on(Raw())
async def handle_raw(raw):
    print(raw)


bot.start()
bot.run_until_disconnected()
