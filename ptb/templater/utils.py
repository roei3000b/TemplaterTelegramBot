from datetime import datetime, timedelta


def add_minutes_to_time(time_str, minutes):
    if type(time_str) is int:
        time_str, minutes = minutes, time_str

    datetime_obj = datetime.strptime(time_str, '%H:%M')
    new_datetime_obj = datetime_obj + timedelta(minutes=minutes)
    return new_datetime_obj.time().strftime('%H:%M')


def round_up_to_nearest_5_minutes(time_str):
    datetime_obj = datetime.strptime(time_str, '%H:%M')
    minutes = datetime_obj.minute
    if minutes % 5 != 0:
        minutes = minutes + (5 - minutes % 5)
    new_datetime_obj = datetime_obj.replace(minute=minutes)
    return new_datetime_obj.time().strftime('%H:%M')


def round_down_to_nearest_5_minutes(time_str):
    datetime_obj = datetime.strptime(time_str, '%H:%M')
    minutes = datetime_obj.minute
    if minutes % 5 != 0:
        minutes = minutes - minutes % 5
    new_datetime_obj = datetime_obj.replace(minute=minutes)
    return new_datetime_obj.time().strftime('%H:%M')

def is_number(x):
    return type(x) is int