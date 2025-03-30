import json
import os

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


async def __post_complexes():
    with open("test_data/complexes.json") as f:
        complexes = json.load(f)
        for complex in complexes:#[0:1]
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


def __get_results():
    with open('test_data/results.json') as f:
        results = json.load(f)
        return results


async def __get_complex_messages(results):
    complex_message_dict = {}
    complex_ids = list(set(map(lambda r: r['complex_id'], results)))
    async for msg in g.app.iter_messages(g.CHANNEL_WITH_COMPLEXES):
        try:
            parts = msg.text.split("\u00A0\n\n")
            complex_id_in_msg = int(parts[0].replace('ID: **', '').replace('**', ''))
            if complex_id_in_msg in complex_ids:
                complex_message_dict[complex_id_in_msg] = msg
                if len(complex_message_dict) == len(complex_ids):
                    break
        except Exception as e:
            print(e)
    return complex_message_dict


async def __post_results_by_complex_id(complex_id, complex_message, results):
    complex_results = filter(lambda r: int(r['complex_id']) == complex_id, results)
    for complex_result in complex_results:
        text = (f"\n[{complex_result['username']}](t.me/{complex_result['username']})\u00A0\n\n"
         f"Результат: {complex_result['result']}")

        await g.app.send_file(
            entity=g.CHANNEL_WITH_COMPLEXES,
            file=f"{os.getcwd()}/test_data/test_video.mp4",
            caption=text,
            parse_mode='markdown',
            comment_to=complex_message.id
        )


async def generate_complexes_with_results():
    await __post_complexes()
    results = __get_results()#[0:1]
    complex_messages = await __get_complex_messages(results)
    for complex_id in complex_messages:
        await __post_results_by_complex_id(complex_id, complex_messages[complex_id], results)
