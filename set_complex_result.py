from enum import Enum
import globals as g


#region data
class AddResultStep(Enum):
    SET_RESULT = 1
    SET_VIDEO = 2
    APPROVE_DATA = 3
    ALL_SET = 4


class SetResultModel:
    session_id: str = None
    user_id: int = -1
    complex_id: int = -1
    tg_msg_id: int = -1
    result: str = None
    video_url: str = None
    result_approved: bool = False

    def get_next_step(self) -> AddResultStep:
        if self.complex_id == -1:
            return AddResultStep.SET_RESULT
        elif self.video_url == -1:
            return AddResultStep.SET_VIDEO
        elif not self.result_approved:
            return AddResultStep.APPROVE_DATA
        else:
            return AddResultStep.ALL_SET


class ComplexModel:
    complex_id: int = -1
    complex_name: str = None
    complex_video_url: str = None
    complex_rules: str = None
    is_time: bool = False
    is_reps: bool = False

#endregion


def parse_complex_from_msg(msg) -> ComplexModel:
    pass


async def get_msg_by_complex_id(complex_id):
    async for msg in g.bot.iter_messages(g.CHANNEL_WITH_COMPLEXES_ID, from_user=g.BOT_NAME):
        complex = parse_complex_from_msg(msg)
        if complex is not None and complex.complex_id == complex_id:
            return msg, complex
    return None


async def process_set_complex_result(user_id, complex_id):
    complex_msg, complex = await get_msg_by_complex_id(complex_id)
    if complex_msg is not None and complex is not None:
        pass
    else:
        pass