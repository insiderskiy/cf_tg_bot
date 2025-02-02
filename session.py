from enum import Enum
from cachetools import TTLCache

create_complex_cache = TTLCache(ttl=3600, maxsize=100)

class CurrentInteraction(Enum):
    NONE = 0
    COMPLEX_CREATION = 1

def get_interaction_in_progress(user_id) -> CurrentInteraction:
    if user_id in create_complex_cache is not None:
        return CurrentInteraction.COMPLEX_CREATION
    else:
        return CurrentInteraction.NONE