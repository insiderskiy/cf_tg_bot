import collections
import datetime
from itertools import groupby

import pytz
import globals as g

ComplexModel = collections.namedtuple("complex", ["complex_id",
                                                  "complex_name", "complex_video_url",
                                                  "complex_rules", "is_time", "is_reps", "msg"])

ResultModel = collections.namedtuple("result", ["username", "result", "msg"])

ScoreRecord = collections.namedtuple("score_record",
                                     field_names=["complex_id", "username", "result", "points"])

empty_record = '¯\_(ツ)_/¯'


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
    start = pytz.utc.localize(datetime.datetime(date.year, start_month, 1))
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
        username = parts[0].split('t.me/')[1][:-1]
        result = parts[1].split('Результат: ')[1]
        return ResultModel(username, result, msg)
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
    return dict(sorted(complexes.items(), key=lambda item: item[1].msg.date))


async def __get_results(complexes, start, end):
    results = {}
    for complex_id in complexes:
        async for reply in g.app.iter_messages(g.CHANNEL_WITH_COMPLEXES, reply_to=complexes[complex_id].msg.id):
            if start <= reply.date <= end:
                result = __try_map_result_msg(reply)
                if result is not None:
                    if complex_id in results:
                        results[complex_id].append(result)
                    else:
                        results[complex_id] = [result]
    return results


def __get_all_users(all_results):
    users = set()
    for complex_results in all_results.values():
        for result in complex_results:
            users.add(result.username)
    return users


def __to_seconds(result):
    time_arr = result.split(':')
    if len(time_arr) == 2:
        hours = 0
        minutes = time_arr[0]
        seconds = time_arr[1]
    elif len(time_arr) == 3:
        hours = time_arr[0]
        minutes = time_arr[1]
        seconds = time_arr[2]
    else:
        return None
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)


def __fuck_python_group_by(result_models, key_lambda):
    grouped_dict = {}
    for m in result_models:
        key = key_lambda(m.result)
        if key_lambda(m.result) in grouped_dict:
            grouped_dict[key].append(m)
        else:
            grouped_dict[key] = []
            grouped_dict[key].append(m)
    return grouped_dict


def __process_single_complex(complex, all_results_models, all_users, score_list):
    complex_id = complex[0]
    complex_model: ComplexModel = complex[1]
    if complex_id not in all_results_models:
        return
    complex_results = all_results_models[complex_id]
    if complex_model.is_reps:
        results_grouped = {int(k): list(v) for k, v in groupby(complex_results, key=lambda i: i.result)}
        results_grouped_sorted = sorted(results_grouped.items(), reverse=True)
    else:
        results_grouped = __fuck_python_group_by(complex_results, lambda i: __to_seconds(i))
        results_grouped_sorted = sorted(results_grouped.items())
    points = 5
    users_left = all_users.copy()
    for result_group in results_grouped_sorted:
        for result in result_group[1]:
            score_list.append(ScoreRecord(complex_id, result.username, result.result, points))
            if result.username in users_left:
                users_left.remove(result.username)
        points -= len(result_group[1])
        if points <= 0:
            points = 0
    for username in users_left:
        score_list.append(ScoreRecord(complex_id, username, empty_record, 0))


def __group_scores_by_user(score_list):
    score_dict = {}
    for score_record in score_list:
        if score_record.username in score_dict:
            curr_item = score_dict[score_record.username]
            new_points = curr_item[0] + score_record.points
            curr_item[1].append(score_record)
            score_dict[score_record.username] = (new_points, curr_item[1])
        else:
            score_dict[score_record.username] = (score_record.points, [score_record])
    return dict(sorted(score_dict.items(), key=lambda i: i[1][0], reverse=True))


async def __send_result_msg(scores_grouped_by_user, start, end):
    result = ''
    for idx, item in enumerate(scores_grouped_by_user.items()):
        result += f"{idx + 1}. [{item[0]}](t.me/{item[0]}) – {item[1][0]} баллов"
        if idx != len(scores_grouped_by_user) - 1:
            result += "\n"

    await g.bot.send_message(
        entity=g.CHANNEL_WITH_COMPLEXES,
        message=f"**Турнирная таблица за период {start.strftime('%d.%m.%Y')}-{end.strftime('%d.%m.%Y')}**"
                f"\n\n"
                f"{result}",
        parse_mode='markdown',
        link_preview=False,
    )
    pass


async def publish_results():
    score_list = []
    start, end = __get_quarter_bounds(datetime.datetime.now())
    all_complexes = await __get_complexes(start, end)
    all_results = await __get_results(all_complexes, start, end)
    all_users = __get_all_users(all_results)
    for complex in all_complexes.items():
        __process_single_complex(complex, all_results, all_users, score_list)
    scores_grouped_by_user = __group_scores_by_user(score_list)
    await __send_result_msg(scores_grouped_by_user, start, end)
