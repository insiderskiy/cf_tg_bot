import uuid
from enum import Enum
from furl import furl
from telethon import Button
from session import create_complex_cache

# region data
class CreateComplexStep(Enum):
    SET_ID = 1
    APPROVE_ID = 2
    SET_NAME = 3
    APPROVE_NAME = 4
    SET_VIDEO = 5
    APPROVE_VIDEO = 6
    SET_RULES = 7
    APPROVE_RULES = 8
    SET_TYPE = 9
    APPROVE_TYPE = 10
    ALL_SET = 11


class CreateComplexModel:
    session_id: str = None
    user_id: int = -1
    complex_id: int = -1
    complex_id_approved: bool = False
    complex_name: str = None
    complex_name_approved: bool = False
    complex_video_url: str = None
    complex_video_url_approved: bool = False
    complex_rules: str = None
    complex_rules_approved: bool = False
    is_time: bool
    is_reps: bool
    is_type_set: bool = False
    is_type_set_approved: bool = False

    def all_fields_set(self) -> bool:
        return (self.session_id is not None
                and self.user_id != -1

                and self.complex_id != -1
                and self.complex_id_approved

                and self.complex_name is not None
                and self.complex_name_approved

                and self.complex_video_url is not None
                and self.complex_video_url_approved

                and self.complex_rules is not None
                and self.complex_rules_approved

                and self.is_type_set

                and self.is_type_set_approved
                and (self.is_time != False or self.is_reps != False))

    def get_next_step(self) -> CreateComplexStep:
        if self.complex_id == -1:
            return CreateComplexStep.SET_ID
        elif not self.complex_id_approved:
            return CreateComplexStep.APPROVE_ID

        elif self.complex_name is None:
            return CreateComplexStep.SET_NAME
        elif not self.complex_name_approved:
            return CreateComplexStep.APPROVE_NAME

        elif self.complex_video_url is None:
            return CreateComplexStep.SET_VIDEO
        elif not self.complex_video_url_approved:
            return CreateComplexStep.APPROVE_VIDEO

        elif self.complex_rules is None:
            return CreateComplexStep.SET_RULES
        elif not self.complex_rules_approved:
            return CreateComplexStep.APPROVE_RULES

        elif not self.is_type_set:
            return CreateComplexStep.SET_TYPE
        elif not self.is_type_set_approved:
            return CreateComplexStep.APPROVE_TYPE

        elif self.all_fields_set():
            return CreateComplexStep.ALL_SET
        else:
            raise RuntimeError("Illegal CreateComplex state")
# endregion

# region private
# region fields validation
async def __is_complex_id_unique(bot, complex_id) -> bool:
    # TODO parse channel messages and check uniqueness
    return True


async def __validate_complex_id(bot, user_id, complex_id) -> bool:
    if not complex_id.is_digit():
        await bot.send_message(user_id, "ID комплекса должно быть положительным числом")
        return False
    elif not await __is_complex_id_unique(bot, complex_id):
        await bot.send_message(user_id, "ID комплекса должен быть уникальным")
        return False
    return True


async def __validate_session_id(bot, create_complex_model, user_id, query) -> bool:
    session_id = furl(query.data.decode('utf-8')).args['sid']
    if session_id != create_complex_model.session_id:
        try:
            create_complex_cache.pop(create_complex_model.user_id)
        except Exception as e:
            print(e)
        finally:
            await bot.send_message(user_id, "Сессия устарела")
        return False
    return True
# endregion

async def __handle_create_complex(bot, user_id):
    create_complex_model = CreateComplexModel()
    create_complex_model.user_id = user_id
    create_complex_model.session_id = str(uuid.uuid4())[:8]
    create_complex_cache[user_id] = create_complex_model
    await bot.send_message(
        user_id,
        "Введите ID комлекса. ID должен быть уникальным",
        buttons = Button.force_reply()
    )


async def __handle_set_id(bot, create_complex_model, user_id, event):
    complex_id = event.message.text
    if __validate_complex_id(bot, user_id, complex_id):
        create_complex_model.complex_id = complex_id
        data = furl("/approve_complex_id")
        data.add({'sid': create_complex_model.session_id})
        await bot.send_message(
            user_id,
            f"ID комплекса - <b>{complex_id}</b>",
            parse_mode = 'html',
            buttons=[
                Button.inline(
                    text="Подтвердить",
                    data=data
                )
            ]
        )


async def __handle_approve_id(bot, create_complex_model, user_id, query):
    if await __validate_session_id(bot, create_complex_model, user_id, query):
        create_complex_model.complex_id_approved = True
        await bot.send_message(user_id, "Введите название комплекса", buttons = Button.force_reply())


async def __handle_set_name(bot, create_complex_model, user_id, event):
    complex_name = event.message.text[:30]
    create_complex_model.complex_name = complex_name
    data = furl("/approve_complex_name")
    data.add({'sid': create_complex_model.session_id})
    await bot.send_message(
        user_id,
        f"Название комплекса - <b>{complex_name}</b>",
        parse_mode = 'html',
        buttons=[
            Button.inline(
                text="Подтвердить",
                data=data
            ),
        ],
    )


async def __handle_approve_name(bot, create_complex_model, user_id, query):
    if await __validate_session_id(bot, create_complex_model, user_id, query):
        create_complex_model.complex_name_approved = True
        await bot.send_message(user_id, "Добавьте ссылку на видео", buttons = Button.force_reply())
# endregion

# region public
async def handle_next_step_create_complex(bot, user_id, event, query):
    if user_id not in create_complex_cache:
        await __handle_create_complex(bot, user_id)
    else:
        create_complex_model: CreateComplexModel = create_complex_cache[user_id]
        current_step = create_complex_model.get_next_step()

        if current_step == CreateComplexStep.SET_ID:
            await __handle_set_id(bot, create_complex_model, user_id, event)
        elif current_step == CreateComplexStep.APPROVE_ID:
            if query is not None:
                await __handle_approve_id(bot, create_complex_model, user_id, query)
            else:
                await __handle_set_id(bot, create_complex_model, user_id, event)

        elif current_step == CreateComplexStep.SET_NAME:
            await __handle_set_name(bot, create_complex_model, user_id, event)
        elif current_step == CreateComplexStep.APPROVE_NAME:
            if query is not None:
                await __handle_approve_name(bot, create_complex_model, user_id, query)
            else:
                await __handle_set_name(bot, create_complex_model, user_id, event)

# endregion
