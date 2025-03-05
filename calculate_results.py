import datetime
import pytz
import globals as g


def __get_quarter_bounds(date: datetime.datetime):
    utc_date = pytz.utc.localize(date)
    if utc_date.month <= 3:
        start_month = 1
        end_month = 3
        end_day = 31
    elif utc_date.month <= 6:
        start_month = 4
        end_month = 6
        end_day = 30
    elif utc_date.month <= 9:
        start_month = 7
        end_month = 9
        end_day = 30
    else:
        start_month = 10
        end_month = 12
        end_day = 31
    start = pytz.utc.localize(datetime.datetime(date.year, start_month,1))
    end = pytz.utc.localize(datetime.datetime(date.year, end_month, end_day))
    return start, end


def __is_complex_msg(msg):
    return True


async def __get_complex_messages_for_current_quarter():
    start, end = __get_quarter_bounds(datetime.datetime.now())
    messages = []
    async for msg in g.app.iter_messages(
            g.CHANNEL_WITH_COMPLEXES,
            offset_date=start,
            reverse=True
    ):
        if start <= msg.date <= end and __is_complex_msg(msg):
            messages.append(msg)
        if msg.date > end:
            return messages
    return messages


def map_complex_messages_to_complex_models(complex_messages):
    return []


def get_result_messages_for_each_complex(complex_messages):
    return []


def map_result_messages_to_result_models(result_messages):
    return []


def collect_users_with_results(results):
    return []


def sort_complexes(complexes):
    return []


def get_results_by_complex(complex, results):
    return []


def sort_results(results):
    # TODO Учесть, что результат может быть одинаковым у нескольких человек
    return []


def get_user_by_result(result_model, all_users):
    return None


def get_score_by_idx(idx):
    return max(0, 5 - idx)


def get_user_by_id(user_id, all_users):
    return None


def process_single_complex(complex_idx, complex, all_results_models, all_users, score):
    complex_results = get_results_by_complex(complex, all_results_models)
    complex_results = sort_results(complex_results)
    for idx, result_model in enumerate(complex_results):
        user = get_user_by_result(result_model, all_users)
        score[user.id] = score.get(user.id, 0) + get_score_by_idx(idx)


def process_score(score, all_users):
    for user_id, points in score.items():
        user = get_user_by_id(user_id)
        pass


async def publish_results():
    score = {}
    complex_messages = await __get_complex_messages_for_current_quarter()
    complex_models = map_complex_messages_to_complex_models(complex_messages)
    all_results_messages = get_result_messages_for_each_complex(complex_messages)
    all_results_models = map_result_messages_to_result_models(all_results_messages)
    all_users = collect_users_with_results(all_results_models)
    complex_models = sort_complexes(complex_models)
    for idx, complex in enumerate(complex_models):
        process_single_complex(idx, complex, all_results_models, all_users, score)
    process_score(score, all_users)
