from enum import Enum
from cachetools import TTLCache

create_complex_cache = TTLCache(ttl=3600, maxsize=100)
set_complex_result_cache = TTLCache(ttl=3600, maxsize=100)

class CurrentInteraction(Enum):
    NONE = 0
    COMPLEX_CREATION = 1
    SET_COMPLEX_RESULT = 2

def get_interaction_in_progress(user_id) -> CurrentInteraction:
    if user_id in create_complex_cache is not None:
        return CurrentInteraction.COMPLEX_CREATION
    elif user_id in set_complex_result_cache:
        return CurrentInteraction.SET_COMPLEX_RESULT
    else:
        return CurrentInteraction.NONE