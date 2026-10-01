"""
LEVEL 01 (basic) - date, time, datetime and timedelta: the four building blocks
==================================================================================
You will learn
  * date holds a calendar day; time holds a clock time; datetime combines both
  * timedelta represents a DURATION, and adding one to a date/datetime shifts it
  * basic arithmetic: datetime - datetime = timedelta; datetime + timedelta = datetime
  * datetime.now() vs date.today() for "right now"

Run: python level_01_construction_and_arithmetic.py
"""
from datetime import date, datetime, time, timedelta


def main() -> None:
    # --- date: a calendar day, no time-of-day -------------------------------
    launch_day = date(2024, 3, 15)
    assert launch_day.year == 2024
    assert launch_day.month == 3
    assert launch_day.day == 15

    # --- time: a clock time, no calendar day --------------------------------
    lunch = time(12, 30, 0)
    assert lunch.hour == 12
    assert lunch.minute == 30

    # --- datetime: date + time combined -------------------------------------
    launch_moment = datetime(2024, 3, 15, 9, 0, 0)
    assert launch_moment.date() == launch_day
    assert launch_moment.time() == time(9, 0, 0)

    # combine() builds a datetime from a separate date and time explicitly
    combined = datetime.combine(launch_day, lunch)
    assert combined == datetime(2024, 3, 15, 12, 30, 0)

    # --- timedelta: a duration, not a point in time -------------------------
    one_week = timedelta(weeks=1)
    assert one_week.days == 7

    ninety_minutes = timedelta(hours=1, minutes=30)
    assert ninety_minutes == timedelta(minutes=90)

    # --- arithmetic: point +/- duration = point -----------------------------
    one_week_later = launch_day + one_week
    assert one_week_later == date(2024, 3, 22)

    meeting_end = launch_moment + ninety_minutes
    assert meeting_end == datetime(2024, 3, 15, 10, 30, 0)

    # --- arithmetic: point - point = duration --------------------------------
    gap = meeting_end - launch_moment
    assert gap == ninety_minutes

    # --- "right now" ----------------------------------------------------------
    today = date.today()
    now = datetime.now()
    assert isinstance(today, date)
    assert isinstance(now, datetime)
    assert now.date() == today  # both agree on the calendar day "right now"

    print("OK")


if __name__ == "__main__":
    main()
