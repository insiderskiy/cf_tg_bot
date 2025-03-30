import uuid
from asyncio import gather
from enum import Enum
from furl import furl
from telethon import Button
from session import create_complex_cache
import validators
import globals as g
from set_complex_result import parse_complex_from_msg


# region data
class CreateComplexStep(Enum):
    SET_ID = 1
    SET_NAME = 2
    SET_VIDEO = 3
    SET_RULES = 4
    SET_TYPE = 5


class CreateComplexModel:
    session_id: str = None
    user_id: int = -1
    complex_id: int = -1
    complex_name: str = None
    complex_video_url: str = None
    complex_rules: str = None
    is_time: bool = False
    is_reps: bool = False

    def all_fields_set(self) -> bool:
        return (self.session_id is not None
                and self.user_id != -1
                and self.complex_id != -1
                and self.complex_name is not None
                and self.complex_video_url is not None
                and self.complex_rules is not None
                and (self.is_time != False or self.is_reps != False))

    def get_next_step(self) -> CreateComplexStep:
        if self.complex_id == -1:
            return CreateComplexStep.SET_ID

        elif self.complex_name is None:
            return CreateComplexStep.SET_NAME

        elif self.complex_video_url is None:
            return CreateComplexStep.SET_VIDEO

        elif self.complex_rules is None:
            return CreateComplexStep.SET_RULES

        elif not self.is_reps and not self.is_time:
            return CreateComplexStep.SET_TYPE

        else:
            raise RuntimeError("Illegal CreateComplex state")

    def create_text(self):
        if self.is_reps:
            t = "reps"
        else:
            t = "time"
        return (f"ID: <b>{self.complex_id}</b>\u00A0\n\n"
                f"<b>{self.complex_name}</b>\u00A0\n\n"
                f"<a href='{self.complex_video_url}'>Видео</a>\u00A0\n\n"
                f"{self.complex_rules}\u00A0\n\n"
                f"{t}\u00A0\n\n"
                f"<a href='https://t.me/{g.BOT_NAME}?start=set_result_{self.complex_id}'>"
                f"Записать свой результат</a>\n")


# endregion

# region private
# region fields validation
async def ç(complex_id) -> bool:
    async for msg in g.app.iter_messages(g.CHANNEL_WITH_COMPLEXES, search=f'start=set_result_{complex_id}'):
        complex_model = parse_complex_from_msg(msg)
        if complex_model is not None and complex_model.complex_id == complex_id:
            return False
    return True


async def __validate_complex_id(user_id, complex_id) -> bool:
    if not complex_id.isdigit():
        await g.bot.send_message(
            user_id,
            "ID комплекса должно быть положительным числом. Введите повторно",
            buttons=Button.force_reply()
        )
        return False
    if not await __is_complex_id_unique(complex_id):
        await g.bot.send_message(
            user_id,
            "ID комплекса должен быть уникальным. Введите уникальный ID",
            buttons=Button.force_reply()
        )
        return False
    return True


async def __validate_session_id(create_complex_model, user_id, query) -> bool:
    session_id = furl(query.data.decode('utf-8')).args['sid']
    if session_id != create_complex_model.session_id:
        try:
            create_complex_cache.pop(create_complex_model.user_id)
        except Exception as e:
            print(e)
        finally:
            await g.bot.send_message(user_id, "Сессия устарела")
        return False
    return True


# endregion

async def __handle_create_complex(user_id):
    create_complex_model = CreateComplexModel()
    create_complex_model.user_id = user_id
    create_complex_model.session_id = str(uuid.uuid4())[:8]
    create_complex_cache[user_id] = create_complex_model
    await g.bot.send_message(
        user_id,
        "Введите ID комлекса. ID должен быть уникальным",
        buttons=Button.force_reply()
    )


async def __handle_set_id(create_complex_model, user_id, event):
    complex_id = event.message.text
    if await __validate_complex_id(user_id, complex_id):
        create_complex_model.complex_id = complex_id
        await g.bot.send_message(
            user_id,
            "Введите название комплекса",
            buttons=Button.force_reply())


async def __handle_set_name(create_complex_model, user_id, event):
    complex_name = event.message.text[:100]
    create_complex_model.complex_name = complex_name
    await g.bot.send_message(
        user_id,
        "Добавьте ссылку на видео",
        buttons=Button.force_reply()
    )


async def __handle_set_video(create_complex_model, user_id, event):
    video_url = event.message.text
    if validators.url(video_url):
        create_complex_model.complex_video_url = video_url
        await g.bot.send_message(
            user_id,
            "Введите правила выполнения комплекса",
            buttons=Button.force_reply()
        )
    else:
        await g.bot.send_message(
            user_id,
            "Некорректный url. Проверьте и введите повторно",
            buttons=Button.force_reply()
        )


def __get_time_data(create_complex_model):
    data = furl("/set_complex_result_type")
    data.add({'sid': create_complex_model.session_id})
    data.add({'type': 'time'})
    return data


def __get_reps_data(create_complex_model):
    data = furl("/set_complex_result_type")
    data.add({'sid': create_complex_model.session_id})
    data.add({'type': 'reps'})
    return data


async def __handle_set_rules(create_complex_model, user_id, event):
    rules = event.message.text[:2048]
    create_complex_model.complex_rules = rules
    await g.bot.send_message(
        user_id,
        "Выберите тип результата",
        buttons=[
            Button.inline(
                text="Время",
                data=__get_time_data(create_complex_model)
            ),
            Button.inline(
                text="Повторения",
                data=__get_reps_data(create_complex_model)
            ),
            Button.inline(
                text='Отменить создание комплекса',
                data='/cancel'
            )
        ]
    )


async def __handle_set_type(create_complex_model, user_id, query):
    if await __validate_session_id(create_complex_model, user_id, query):
        type = furl(query.data.decode('utf-8')).args['type']
        if type == "time":
            create_complex_model.is_time = True
        elif type == "reps":
            create_complex_model.is_reps = True
        await gather(
            g.bot.send_message(
                g.CHANNEL_WITH_COMPLEXES,
                create_complex_model.create_text(),
                parse_mode='html',
                link_preview=True
            ),
            g.bot.send_message(
                user_id,
                "Комплекс добавлен"
            )
        )
        del create_complex_cache[user_id]


# endregion

# region public
async def handle_next_step_create_complex(user_id, event, query):
    if user_id not in create_complex_cache:
        await __handle_create_complex(user_id)
    else:
        create_complex_model: CreateComplexModel = create_complex_cache[user_id]
        current_step = create_complex_model.get_next_step()

        if current_step == CreateComplexStep.SET_ID:
            await __handle_set_id(create_complex_model, user_id, event)

        elif current_step == CreateComplexStep.SET_NAME:
            await __handle_set_name(create_complex_model, user_id, event)

        elif current_step == CreateComplexStep.SET_VIDEO:
            await __handle_set_video(create_complex_model, user_id, event)

        elif current_step == CreateComplexStep.SET_RULES:
            await __handle_set_rules(create_complex_model, user_id, event)

        elif current_step == CreateComplexStep.SET_TYPE:
            await __handle_set_type(create_complex_model, user_id, query)

# endregion
