import datetime
import os
import uuid
from enum import Enum
from telethon import Button
from telethon.tl.types import PeerChannel
import validators
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
    is_time_min: bool = False
    is_time_max: bool = False
    is_reps: bool = False


# endregion


# region private
def parse_complex_from_msg(msg):
    try:
        parts = msg.text.split("\u00A0\n\n")
        model = ComplexModel()
        model.complex_id = parts[0].replace('ID: **', '').replace('**', '')
        model.complex_name = parts[1].replace('**', '')
        model.complex_video_url = parts[2].split('](')[1][:-1]
        model.complex_rules = parts[3]
        if parts[4] == 'time' or parts[4] == 'time_min':
            model.is_time_min = True
        elif parts[4] == 'time_max':
            model.is_time_max = True
        else:
            model.is_reps = True
        return model
    except:
        pass
    return None


async def __create_result_model(user_id, complex_id):
    async for msg in g.app.iter_messages(g.CHANNEL_WITH_COMPLEXES):
        complex_model = parse_complex_from_msg(msg)
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
        if result_model.complex.is_time_min or result_model.complex.is_time_max:
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
        "Отправьте видео выполнения комплекса"
    )


async def __process_set_time_or_reps(user_id, result_model, event):
    if result_model.complex.is_time_min or result_model.complex.is_time_max:
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
    return 'Поздравляем, чемпион! '


# TODO Не сработало какого-то хера
async def __remove_prev_result_if_set(user_id, msg_id):
    async for reply in g.app.iter_messages(g.CHANNEL_WITH_COMPLEXES, reply_to=msg_id):
        if (f"id={user_id}" in reply.text
                and isinstance(reply.peer_id, PeerChannel)
                and reply.peer_id.channel_id == g.CHAT_WITH_RESULTS_ID):
            await g.app.delete_messages(reply.chat.id, reply.id)


async def __process_set_video(user_id, user_name, result_model, event):
    await g.bot.send_message(user_id, 'Обработка видео займёт некоторое время')
    # Закомментил удаление предыдущего результата. При подсчёте баллов просто берём последний результат
    # await __remove_prev_result_if_set(user_id, result_model.msg.id)
    tg_username = (await g.bot.get_entity(user_id)).username
    if tg_username is None:
        link = f"\n[{user_name}](tg:user?id={user_id})\u00A0\n\n"
    else:
        link = f"\n[{user_name}](t.me/{tg_username})\u00A0\n\n"
    if event.message.video is not None:
        video = await g.bot.download_media(event.message.video)
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
    elif validators.url(event.message.text):
        title = await __get_title()
        text = (f"{link}"
                f"Результат: {result_model.result}\u00A0\n\n"
                f"Ссылка на видео с выполнением: {event.message.text}")
        await g.app.send_message(
            entity=g.CHANNEL_WITH_COMPLEXES,
            message=text,
            parse_mode='markdown',
            comment_to=result_model.msg.id
        )
        await g.bot.send_message(
            user_id,
            f'{title}Результат отправлен'
        )
        del set_complex_result_cache[user_id]
    else:
        await g.bot.send_message(
            user_id,
            'Не удалось найти видео. Загрузите как файл или добавьте корректную ссылку',
            buttons=Button.inline('Отменить добавление результата', '/cancel')
        )
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
