import json

import globals as g


async def __get_all_msgs(from_id):
    msgs = []
    async for msg in g.app.iter_messages(from_id):
        msgs.append(msg.id)
    return msgs

async def clear_all():
    await g.app.delete_messages(
        g.CHANNEL_WITH_COMPLEXES,
        message_ids=await __get_all_msgs(g.CHANNEL_WITH_COMPLEXES)
    )
    await g.app.delete_messages(
        g.CHAT_WITH_RESULTS_ID,
        message_ids=await __get_all_msgs(g.CHAT_WITH_RESULTS_ID)
    )

async def generate_complexes_with_results():
    with open("test_data/complexes.json") as f:
        complexes = json.load(f)
        for complex in complexes:
            if complex.get('is_time', False):
                t = "time"
            else:
                t = "reps"
            await g.bot.send_message(
                entity = g.CHANNEL_WITH_COMPLEXES,
                message = f"ID: <b>{complex['id']}</b>\u00A0\n\n"
                f"<b>{complex['name']}</b>\u00A0\n\n"
                f"<a href='{complex['video_url']}'>Видео</a>\u00A0\n\n"
                f"{complex['complex_rules']}\u00A0\n\n"
                f"{t}\u00A0\n\n"
                f"<a href='https://t.me/{g.BOT_NAME}?start=set_result_{complex['id']}'>"
                f"Записать свой результат</a>\n",
                parse_mode='html',
                link_preview=True
            )