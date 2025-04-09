import collections
import datetime
import itertools
import os
from itertools import groupby
import pytz
from PIL import Image, ImageDraw, ImageFont
from dateutil.relativedelta import relativedelta
from telethon import Button

import globals as g

ComplexModel = collections.namedtuple("complex", ["complex_id",
                                                  "complex_name", "complex_video_url",
                                                  "complex_rules", "is_time", "is_reps", "msg"])

ResultModel = collections.namedtuple("result", ["username", "result", "msg"])

ScoreRecord = collections.namedtuple("score_record",
                                     field_names=["complex_id", "username", "result", "points"])

empty_result = '¯\_(ツ)_/¯'

measure_draw = ImageDraw.Draw(Image.new('RGBA', (0, 0)))


def __get_quarter_bounds(dt: datetime.datetime):
    utc_date = pytz.utc.localize(dt)
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
    start = pytz.utc.localize(datetime.datetime(dt.year, start_month, 1))
    end = pytz.utc.localize(datetime.datetime(dt.year, end_month, end_day) + datetime.timedelta(days=1, microseconds=-1))
    return start, end


def __get_week_bounds(dt):
    utc_date = pytz.utc.localize(dt)
    start = pytz.utc.localize(dt - datetime.timedelta(
        days=dt.weekday(),
        hours=utc_date.hour,
        minutes=utc_date.minute,
        seconds=utc_date.second,
        microseconds=utc_date.microsecond
    ))
    end = start + datetime.timedelta(days=7, microseconds=-1)
    return start, end


def __get_month_bounds(dt):
    utc_date = pytz.utc.localize(dt)
    start = pytz.utc.localize(datetime.datetime(year=utc_date.year, month=utc_date.month, day=1))
    end = start + relativedelta(day=31) + datetime.timedelta(days=1, microseconds=-1)
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
                        prev_result = next(filter(lambda x: x.username == result.username, results[complex_id]), None)
                        if prev_result is None:
                            results[complex_id].append(result)
                        elif prev_result.msg.date < result.msg.date:
                            results[complex_id].remove(prev_result)
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
        score_list.append(ScoreRecord(complex_id, username, empty_result, 0))

# TODO Проверить наличие дублей, убирать предыдущие результаты, если есть более новые
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


async def __create_results_table(scores_grouped_by_user, all_complexes, start, end):
    data = []
    rows = []
    columns = list(map(
        lambda x: f'{all_complexes[x.complex_id].complex_name}\nID {x.complex_id}',
        scores_grouped_by_user[list(scores_grouped_by_user.keys())[0]][1]
    ))
    columns.append('Total')

    for item in scores_grouped_by_user.items():
        rows.append(item[0])
        total_points = item[1][0]
        records = item[1][1]
        row = list(map(lambda x: f"{x.result} ({x.points})", records))
        row.append(total_points)
        data.append(row)

    # font = ImageFont.truetype(font='Roboto-Regular.ttf', size=16)
    font = ImageFont.truetype(font='NotoSansJP-Regular.ttf', size=16)

    title = f"Турнирная таблица за период {start.strftime('%d.%m.%Y')}-{end.strftime('%d.%m.%Y')}"
    title_bounds = measure_draw.multiline_textbbox(xy=(0, 0), text=str(title), font=font)
    title_bounds = (title_bounds[2], title_bounds[3])

    columns_bounds = __get_text_bounds(font, columns)
    max_col_width, max_col_height = __get_max_width_height(columns_bounds)

    rows_bounds = __get_text_bounds(font, rows)
    max_row_width, max_row_height = __get_max_width_height(rows_bounds)

    data_1d = list(itertools.chain.from_iterable(data))
    data_bounds = __get_text_bounds(font, data_1d)
    max_data_width, max_data_height = __get_max_width_height(data_bounds)
    data_bounds = [data_bounds[i: i + len(columns)] for i in range(0, len(data_bounds), len(columns))]

    max_text_width = max(max_col_width, max_row_width, max_data_width)
    max_text_height = max(max_col_height, max_row_height, max_data_height)

    text_padding_hor = 8
    text_padding_vert = 4
    cell_width = max_text_width + 2 * text_padding_hor
    cell_height = max_text_height + 2 * text_padding_vert

    img_padding = 10
    title_padding = 20

    image_width = max(cell_width * (len(columns) + 1), title_bounds[0]) + img_padding * 2
    image_height = cell_height * (len(rows) + 1) + img_padding * 2 + (title_bounds[1] + title_padding)

    image = Image.new(mode='RGBA', size=(image_width, image_height), color='white')
    draw = ImageDraw.Draw(image)

    def color_by_idx(idx):
        if idx == 0:
            return '#FFD700'
        elif idx == 1:
            return '#C0C0C0'
        elif idx == 2:
            return '#CD7F32'
        else:
            return '#FFFFFF'

    # draw columns
    for idx, column in enumerate(columns):
        x = img_padding + cell_width + idx * cell_width
        y = img_padding + (title_bounds[1] + title_padding)
        shape = [
            (x, y),
            (x + cell_width, y + cell_height)
        ]
        draw.rectangle(shape, fill='white', outline='black', width=1)
        text_x = x + ((cell_width - columns_bounds[idx][0]) / 2)
        text_y = y + ((cell_height - columns_bounds[idx][1]) / 2)
        draw.text(xy=(text_x, text_y), text=column, font=font, fill='black', align='center')

    # draw rows
    for idx, row in enumerate(rows):
        x = img_padding
        y = img_padding + (title_bounds[1] + title_padding) + cell_height + idx * cell_height
        shape = [
            (x, y),
            (x + cell_width, y + cell_height)
        ]
        draw.rectangle(shape, outline='black', width=1, fill=color_by_idx(idx))
        text_x = x + ((cell_width - rows_bounds[idx][0]) / 2)
        text_y = y + ((cell_height - rows_bounds[idx][1]) / 2)
        draw.text(xy=(text_x, text_y), text=row, font=font, fill='black', align='center')

    # draw data
    for row_idx, data_row in enumerate(data):
        y = img_padding + (title_bounds[1] + title_padding) + cell_height + row_idx * cell_height
        for col_idx, data_item in enumerate(data_row):
            x = img_padding + cell_width + col_idx * cell_width
            shape = [
                (x, y),
                (x + cell_width, y + cell_height)
            ]
            draw.rectangle(shape, outline='black', width=1, fill=color_by_idx(row_idx))
            text_x = x + ((cell_width - data_bounds[row_idx][col_idx][0]) / 2)
            text_y = y + ((cell_height - data_bounds[row_idx][col_idx][1]) / 2)
            draw.text(xy=(text_x, text_y), text=str(data_item), font=font, fill='black', align='center')

    # draw title
    draw.text(
        xy=((image_width - title_bounds[0]) / 2, img_padding),
        text=title,
        font=font,
        fill='black',
        align='center'
    )

    image.save('table.png', quality=100)
    await g.bot.send_file(
        g.CHANNEL_WITH_COMPLEXES,
        'table.png'
    )
    os.remove('table.png')


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


def __get_text_bounds(font, text_list):
    bounds = list(map(lambda x: measure_draw.multiline_textbbox(xy=(0, 0), text=str(x), font=font), text_list))
    bounds = list(map(lambda x: (x[2], x[3]), bounds))
    return bounds


def __get_max_width_height(bounds):
    max_width = 0
    max_height = 0
    for b in bounds:
        if b[0] > max_width:
            max_width = b[0]
        if b[1] > max_height:
            max_height = b[1]
    return max_width, max_height


async def publish_results(user_id):
    await g.bot.send_message(
        user_id,
        'Выберите период',
        buttons=[
            Button.inline(
                "PW",
                '/gnr_prev_week'
            ),
            Button.inline(
                "CW",
                '/gnr_curr_week'
            ),
            Button.inline(
                "PM",
                '/gnr_prev_month'
            ),
            Button.inline(
                "CM",
                '/gnr_curr_month'
            ),
            Button.inline(
                "PQ",
                '/gnr_prev_quarter'
            ),
            Button.inline(
                "CQ",
                '/gnr_curr_quarter'
            ),
        ]
    )


async def generate_results(query):
    score_list = []
    date_mark = query.data.decode('utf-8')
    now = datetime.datetime.now()
    if 'prev_week' in date_mark:
        start, end = __get_week_bounds(now - datetime.timedelta(days=7))
    elif 'curr_week' in date_mark:
        start, end = __get_week_bounds(now)
    elif 'prev_month' in date_mark:
        start, end = __get_month_bounds(now - relativedelta(month=1))
    elif 'curr_month' in date_mark:
        start, end = __get_month_bounds(now)
    elif 'prev_quarter' in date_mark:
        start, end = __get_quarter_bounds(now - relativedelta(month=3))
    else:
        start, end = __get_quarter_bounds(now)
    all_complexes = await __get_complexes(start, end)
    all_results = await __get_results(all_complexes, start, end)
    all_users = __get_all_users(all_results)
    for complex in all_complexes.items():
        __process_single_complex(complex, all_results, all_users, score_list)
    scores_grouped_by_user = __group_scores_by_user(score_list)
    await __create_results_table(scores_grouped_by_user, all_complexes, start, end)
    await __send_result_msg(scores_grouped_by_user, start, end)
