from datetime import datetime, timedelta


def add_minutes_to_time(time_str, minutes):
    if type(time_str) is int:
        time_str, minutes = minutes, time_str

    datetime_obj = datetime.strptime(time_str, '%H:%M')
    new_datetime_obj = datetime_obj + timedelta(minutes=minutes)
    return new_datetime_obj.time().strftime('%H:%M')

def is_number(x):
    return type(x) is int