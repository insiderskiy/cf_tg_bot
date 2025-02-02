import uuid
from enum import Enum
from uuid import UUID

from session import create_complex_cache


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
    session_id: UUID = None
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


async def is_complex_id_unique(complex_id) -> bool:
    # TODO parse channel messages and check uniqueness
    return True


async def handle_next_step_create_complex(bot, user_id, event):
    create_complex: CreateComplexModel = create_complex_cache[user_id]
    current_step = create_complex.get_next_step()
    if current_step == CreateComplexStep.SET_ID:
        pass


async def handle_create_complex(bot, user_id):
    if user_id not in create_complex_cache:
        create_complex_model = CreateComplexModel()
        create_complex_model.user_id = user_id
        create_complex_model.session_id = uuid.uuid4()
        await bot.send_message(
            user_id,
            "Введите ID комлекса. ID должен быть уникальным"
        )
    else:
        await handle_next_step_create_complex(bot, user_id, None)
