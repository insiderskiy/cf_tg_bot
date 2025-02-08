import logging
import os
from dotenv import load_dotenv
from furl import furl
from telethon import TelegramClient, Button
from telethon.events import NewMessage, Raw, CallbackQuery
from telethon.tl.types import ChannelParticipantsAdmins
from set_complex_result import process_set_complex_result
from create_complex import handle_next_step_create_complex
from session import get_interaction_in_progress, CurrentInteraction
import globals as g

logging.basicConfig(level=logging.DEBUG)

load_dotenv()

g.BOT_TOKEN = os.getenv("BOT_TOKEN")
g.API_ID = os.getenv("API_ID")
g.API_HASH = os.getenv("API_HASH")
g.CHANNEL_WITH_COMPLEXES_ID = os.getenv("CHANNEL_WITH_COMPLEXES")
g.BOT_NAME = os.getenv("BOT_NAME")

g.bot = TelegramClient('bot', g.API_ID, g.API_HASH).start(bot_token=g.BOT_TOKEN)

async def is_admin(id) -> bool:
    async for user in g.bot.iter_participants(g.CHANNEL_WITH_COMPLEXES_ID, filter=ChannelParticipantsAdmins()):
        if user.id == id:
            return True
    return False


async def is_participant(id) -> bool:
    async for user in g.bot.iter_participants(g.CHANNEL_WITH_COMPLEXES_ID):
        if user.id == id:
            return True
    return False


def get_start_action(event):
    arr = event.message.text.split(' ')
    if len(arr) > 1:
        action = arr[1]
        if action.startswith("set_result_"):
            complex_id = action.split('_')[-1]
            return 'set_result', complex_id
    else:
        return None

async def handle_interaction_none(event, sender_id):
    start_action = get_start_action(event)
    if start_action is None:
        if await is_admin(sender_id):
            data = furl("/create_complex")
            await g.bot.send_message(
                sender_id,
                "Выберите действие",
                buttons=[
                    Button.inline(
                        text="Добавить комплекс",
                        data=data
                    ),
                ],
            )
    elif start_action[0] == 'set_result':
        if await is_participant(sender_id):
            await process_set_complex_result(sender_id, start_action[1])


@g.bot.on(NewMessage(incoming=True, pattern='/start'))
async def handle_start(event: NewMessage):
    sender_id = (await event.get_sender()).id
    current_interaction = get_interaction_in_progress(sender_id)
    if current_interaction is CurrentInteraction.NONE:
        await handle_interaction_none(event, sender_id)
    elif current_interaction is CurrentInteraction.COMPLEX_CREATION:
        await handle_next_step_create_complex(sender_id, event, None)


@g.bot.on(CallbackQuery(pattern="/create_complex"))
async def handle_create_complex_callback(query):
    sender_id = (await query.get_sender()).id
    await handle_next_step_create_complex(sender_id, None, None)


@g.bot.on(CallbackQuery(pattern="/approve_complex_id"))
async def handle_approve_complex_id_callback(query):
    sender_id = (await query.get_sender()).id
    await handle_next_step_create_complex(sender_id, None, query)


@g.bot.on(CallbackQuery(pattern="/approve_complex_name"))
async def handle_approve_complex_name_callback(query):
    sender_id = (await query.get_sender()).id
    await handle_next_step_create_complex(sender_id, None, query)


@g.bot.on(CallbackQuery(pattern="/approve_complex_video"))
async def handle_approve_complex_video_callback(query):
    sender_id = (await query.get_sender()).id
    await handle_next_step_create_complex(sender_id, None, query)


@g.bot.on(CallbackQuery(pattern="/approve_complex_rules"))
async def handle_approve_complex_rules_callback(query):
    sender_id = (await query.get_sender()).id
    await handle_next_step_create_complex(sender_id, None, query)


@g.bot.on(CallbackQuery(pattern="/set_complex_result_type"))
async def handle_set_complex_result_type_callback(query):
    sender_id = (await query.get_sender()).id
    await handle_next_step_create_complex(sender_id, None, query)


@g.bot.on(NewMessage(incoming=True))
async def handle_message(event: NewMessage):
    sender_id = (await event.get_sender()).id
    current_interaction = get_interaction_in_progress(sender_id)
    if current_interaction is CurrentInteraction.NONE:
        # TODO show help
        pass
    elif current_interaction is CurrentInteraction.COMPLEX_CREATION:
        await handle_next_step_create_complex(sender_id, event, None)
    else:
        # TODO show help
        pass


@g.bot.on(Raw())
async def handle_raw(raw):
    print(raw)


g.bot.start()
g.bot.run_until_disconnected()
