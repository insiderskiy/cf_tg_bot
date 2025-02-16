import uuid
from enum import Enum
from telethon import Button
import globals as g
from session import set_complex_result_cache


# region data
class SetResultStep(Enum):
    SET_REPS_OR_TIME = 1
    SET_VIDEO = 2
    APPROVE_DATA = 3
    ALL_SET = 4


class SetResultModel:
    session_id: str = None
    user_id: int = -1
    complex_model = None
    msg = None,
    result: str = None
    video = None
    result_approved: bool = False

    def get_next_step(self) -> SetResultStep:
        if self.result is None:
            return SetResultStep.SET_REPS_OR_TIME
        elif self.video is None:
            return SetResultStep.SET_VIDEO
        elif not self.result_approved:
            return SetResultStep.APPROVE_DATA
        else:
            return SetResultStep.ALL_SET


class ComplexModel:
    complex_id: int = -1
    complex_name: str = None
    complex_video = None
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
        model.complex_video = parts[2].split('](')[1][:-1]
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
    async for msg in g.app.iter_messages(g.CHANNEL_WITH_COMPLEXES_ID):
        complex_model = __parse_complex_from_msg(msg)
        if complex_model is not None and complex_model.complex_id == complex_id:
            set_result_model = SetResultModel()
            set_result_model.session_id = str(uuid.uuid4())[:8]
            set_result_model.user_id = user_id
            set_result_model.complex_model = complex_model
            set_result_model.msg = msg
            return set_result_model


async def __process_set_result_init(user_id, result_model):
    if result_model.complex_model.is_time:
        msg = "Укажите время выполнения комплекса. Формат - минуты:секунды"
    else:
        msg = "Укажите количество повторений"
    await g.bot.send_message(
        user_id,
        msg,
        buttons=Button.force_reply()
    )


async def __send_incorrect_result(user_id):
    await g.bot.send_message(
        user_id,
        "Неверный формат. Повторите ввод"
    )


async def __send_set_video(user_id):
    await g.bot.send_message(
        user_id,
        "Введите ссылку на видео выполнения комплекса либо отправьте видео"
    )


async def __process_set_time_or_reps(user_id, result_model, event):
    if result_model.is_time:
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


async def __process_set_video(user_id, result_model, event):
    pass


# endregion


async def handle_next_step_set_complex_result(
        user_id,
        complex_id=None,
        event=None,
        query=None):

    if user_id in set_complex_result_cache:
        result_model = set_complex_result_cache[user_id]
        next_step = result_model.get_next_step()
        if next_step is SetResultStep.SET_REPS_OR_TIME:
            await __process_set_time_or_reps(user_id, result_model, event)
        elif next_step is SetResultStep.SET_VIDEO:
            await __process_set_video(user_id, result_model, event)
    else:
        result_model = await __create_result_model(user_id, complex_id)
        if result_model is not None:
            set_complex_result_cache[user_id] = result_model
            await __process_set_result_init(user_id, result_model)
        else:
            await g.bot.send_message(
                user_id,
                "Комплекс не найден"
            )
