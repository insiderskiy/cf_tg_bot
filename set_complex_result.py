import datetime
import os
import uuid
from enum import Enum
from telethon import Button
from telethon.tl.types import PeerChannel

import globals as g
from session import set_complex_result_cache


# region data
class SetResultStep(Enum):
    SET_REPS_OR_TIME = 1
    SET_VIDEO = 2
    ALL_SET = 3


class SetResultModel:
    session_id: str = None
    start_time: datetime.datetime = None
    user_id: int = -1
    complex = None
    msg = None,
    result: str = None
    video = None

    def get_next_step(self) -> SetResultStep:
        if self.result is None:
            return SetResultStep.SET_REPS_OR_TIME
        elif self.video is None:
            return SetResultStep.SET_VIDEO
        else:
            return SetResultStep.ALL_SET


class ComplexModel:
    complex_id: int = -1
    complex_name: str = None
    complex_video_url = None
    complex_rules: str = None
    is_time: bool = False
    is_reps: bool = False


# endregion


# region private
def __parse_complex_from_msg(msg):
    try:
        parts = msg.text.split("\u00A0\n\n")
        model = ComplexModel()
        model.complex_id = parts[0].replace('ID: **', '').replace('**', '')
        model.complex_name = parts[1].replace('**', '')
        model.complex_video_url = parts[2].split('](')[1][:-1]
        model.complex_rules = parts[3]
        if parts[4] == 'time':
            model.is_time = True
        else:
            model.is_reps = True
        return model
    except:
        pass
    return None


async def __create_result_model(user_id, complex_id):
    async for msg in g.app.iter_messages(g.CHANNEL_WITH_COMPLEXES):
        complex_model = __parse_complex_from_msg(msg)
        if complex_model is not None and complex_model.complex_id == complex_id:
            set_result_model = SetResultModel()
            set_result_model.session_id = str(uuid.uuid4())[:8]
            set_result_model.user_id = user_id
            set_result_model.complex = complex_model
            set_result_model.msg = msg
            return set_result_model


async def __handle_set_result_init(user_id, complex_id, event):
    result_model = await __create_result_model(user_id, complex_id)
    if result_model is not None:
        result_model.start_time = event.message.date
        set_complex_result_cache[user_id] = result_model
        if result_model.complex.is_time:
            msg = "Укажите время выполнения комплекса. Формат - минуты:секунды"
        else:
            msg = "Укажите количество повторений"
        await g.bot.send_message(
            user_id,
            msg,
            buttons=Button.force_reply()
        )
    else:
        await g.bot.send_message(
            user_id,
            "Комплекс не найден"
        )


async def __send_incorrect_result(user_id):
    await g.bot.send_message(
        user_id,
        "Неверный формат. Повторите ввод",
        buttons=Button.inline("Отменить ввод результата", '/cancel')
    )


async def __send_set_video(user_id):
    await g.bot.send_message(
        user_id,
        "Введите ссылку на видео выполнения комплекса либо отправьте видео"
    )


async def __process_set_time_or_reps(user_id, result_model, event):
    if result_model.complex.is_time:
        time = event.text
        time_splitted = time.split(':')
        if (len(time_splitted) != 2
                or not time_splitted[0].isdigit()
                or not time_splitted[1].isdigit()):
            await __send_incorrect_result(user_id)
        else:
            result_model.result = time
            await __send_set_video(user_id)
    else:
        reps = event.text
        if not reps.isdigit():
            await __send_incorrect_result(user_id)
        else:
            result_model.result = reps
            await __send_set_video(user_id)


async def __get_title():
    # TODO Мотивирующий заголовок, что-то вроде мастер спорта по всем видам спорта
    return 'Поздравляем, чемпион! '


async def __remove_prev_result_if_set(user_id, msg_id):
    async for reply in g.app.iter_messages(g.CHANNEL_WITH_COMPLEXES, reply_to=msg_id):
        if (f"id={user_id}" in reply.text
                and isinstance(reply.peer_id, PeerChannel)
                and reply.peer_id.channel_id == g.CHAT_WITH_RESULTS_ID):
            await g.app.delete_messages(reply.chat.id, reply.id)


async def __process_set_video(user_id, user_name, result_model, event):
    await __remove_prev_result_if_set(user_id, result_model.msg.id)
    tg_username = (await g.bot.get_entity(user_id)).username
    if tg_username is None:
        link = f"\n[{user_name}](tg:user?id={user_id})\u00A0\n\n"
    else:
        link = f"\n[{user_name}](t.me/{tg_username})\u00A0\n\n"
    video = await g.bot.download_media(event.message.video)
    if video is None:
        await g.bot.send_message(
            user_id,
            'Не удалось загрузить видео',
            buttons=Button.inline('Отменить добавление результата', '/cancel')
        )
        return
    text = (f"{link}"
            f"Результат: {result_model.result}")
    title = await __get_title()
    await g.app.send_file(
        entity=g.CHANNEL_WITH_COMPLEXES,
        file=video,
        caption=text,
        parse_mode='markdown',
        comment_to=result_model.msg.id
    )
    await g.bot.send_message(
        user_id,
        f'{title}Результат отправлен'
    )
    os.remove(video)
    del set_complex_result_cache[user_id]


# endregion


async def handle_next_step_set_complex_result(
        user_id,
        user_name,
        complex_id=None,
        event=None
):
    if user_id not in set_complex_result_cache:
        await __handle_set_result_init(user_id, complex_id, event)
    else:
        result_model = set_complex_result_cache[user_id]

        if (event.message.date - result_model.start_time).seconds < 1:
            return

        next_step = result_model.get_next_step()
        if next_step is SetResultStep.SET_REPS_OR_TIME:
            await __process_set_time_or_reps(user_id, result_model, event)
        elif next_step is SetResultStep.SET_VIDEO:
            await __process_set_video(user_id, user_name, result_model, event)
