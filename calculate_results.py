import collections
import datetime
import pytz
import globals as g


ComplexModel = collections.namedtuple("complex", ["complex_id",
                                       "complex_name", "complex_video_url",
                                       "complex_rules", "is_time", "is_reps", "msg"])


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


def __try_map_complex_msg(msg):
    try:
        parts = msg.text.split("\u00A0\n\n")
        complex_id = parts[0].replace('ID: **', '').replace('**', '')
        complex_name = parts[1].replace('**', '')
        complex_video_url = parts[2].split('](')[1][:-1]
        complex_rules = parts[3]
        is_time = False
        is_reps = False
        if parts[4] == 'time':
            is_time = True
        else:
            is_reps = True
        return ComplexModel(complex_id, complex_name, complex_video_url, complex_rules, is_time, is_reps, msg)
    except:
        return None


def __try_map_result_msg(msg):
    try:
        parts = msg.text.split("\u00A0\n\n")
    except:
        return None


async def __get_complexes(start, end):
    complexes = {}
    async for msg in g.app.iter_messages(
            g.CHANNEL_WITH_COMPLEXES,
            offset_date=start,
            reverse=True
    ):
        if start <= msg.date <= end:
            complex_model = __try_map_complex_msg(msg)
            if complex_model is not None:
                complexes[complex_model.complex_id] = complex_model
        if msg.date > end:
            return complexes
    return complexes


async def __get_results(complexes, start, end):
    results = {}
    for complex in complexes:
        async for reply in g.app.iter_messages(g.CHANNEL_WITH_COMPLEXES, reply_to=complex.msg.id):
            pass


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
    start, end = __get_quarter_bounds(datetime.datetime.now())
    all_complexes = await __get_complexes(start, end)
    all_results = await __get_results(all_complexes, start, end)
    all_results_models = map_result_messages_to_result_models(all_results)
    all_users = collect_users_with_results(all_results_models)
    complex_models = sort_complexes(all_complexes)
    for idx, complex in enumerate(complex_models):
        process_single_complex(idx, complex, all_results_models, all_users, score)
    process_score(score, all_users)
