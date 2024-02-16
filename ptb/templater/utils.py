from datetime import datetime, timedelta


def add_minutes_to_time(time_str, minutes):
    if type(time_str) is int:
        time_str, minutes = minutes, time_str

    datetime_obj = datetime.strptime(time_str, '%H:%M')
    new_datetime_obj = datetime_obj + timedelta(minutes=minutes)
    return new_datetime_obj.time().strftime('%H:%M')
def round_time(time_str, round_to=5, round_type='ceil'):
    datetime_obj = datetime.strptime(time_str, '%H:%M')
    minutes = datetime_obj.minute
    if round_type == 'ceil':
        diff = round_to - minutes % round_to
    else:
        diff = -(minutes % round_to)
    new_datetime_obj = datetime_obj + timedelta(minutes=diff)
    return new_datetime_obj.time().strftime('%H:%M')

def round_up_to_nearest_5_minutes(time_str):
    return round_time(time_str, 5, 'ceil')


def round_down_to_nearest_5_minutes(time_str):
    return round_time(time_str, 5, 'floor')

def is_number(x):
    return type(x) is int
