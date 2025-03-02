import json

class Result:
    complex_id: str
    user_id: int
    result: str
    is_reps: bool
    is_time: bool

def get_complex_messages_for_current_quarter():
    results = []
    with open('test_data/results.json') as f:
        for result_json in json.load(f):
            result = Result()
            result.complex_id = result_json['complex_id']
            result.user_id = result_json["user_id"]
            result.result = result_json["result"]
            result.is_reps = result_json["is_reps"]
            result.is_time = result_json["is_time"]
            results.append(result)
    return results


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


def calculate():
    score = {}
    complex_messages = get_complex_messages_for_current_quarter()
    complex_models = map_complex_messages_to_complex_models(complex_messages)
    all_results_messages = get_result_messages_for_each_complex(complex_messages)
    all_results_models = map_result_messages_to_result_models(all_results_messages)
    all_users = collect_users_with_results(all_results_models)
    complex_models = sort_complexes(complex_models)
    for idx, complex in enumerate(complex_models):
        process_single_complex(idx, complex, all_results_models, all_users, score)
    process_score(score, all_users)