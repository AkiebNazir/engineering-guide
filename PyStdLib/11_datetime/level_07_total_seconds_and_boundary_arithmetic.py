"""
LEVEL 07 (advanced) - timedelta.total_seconds() and month/year boundary arithmetic
======================================================================================
You will learn
  * timedelta.total_seconds() collapses days+seconds+microseconds into one
    float -- the correct way to get "how many seconds is this duration",
    NOT `td.seconds` (which discards the days component!)
  * date/datetime arithmetic correctly rolls over month and year boundaries,
    including leap years, because timedelta operates in whole days
  * accumulating many small durations safely with total_seconds()

Run: python level_07_total_seconds_and_boundary_arithmetic.py
"""
from datetime import date, datetime, timedelta


def main() -> None:
    # --- the total_seconds() gotcha: td.seconds is NOT the full duration ---
    long_duration = timedelta(days=1, hours=1)  # 25 hours total
    assert long_duration.seconds == 3600           # only the "hours" remainder!
    assert long_duration.days == 1
    assert long_duration.total_seconds() == 25 * 3600  # the CORRECT total

    short_duration = timedelta(minutes=90)
    assert short_duration.total_seconds() == 5400.0

    # --- accumulating durations: sum a list correctly with total_seconds ---
    call_durations = [timedelta(minutes=12), timedelta(minutes=45), timedelta(hours=1, minutes=3)]
    total = sum(call_durations, timedelta())  # timedelta supports sum() with a start
    assert total.total_seconds() == (12 + 45 + 63) * 60

    # --- date arithmetic crossing a MONTH boundary --------------------------
    end_of_january = date(2024, 1, 31)
    ten_days_later = end_of_january + timedelta(days=10)
    assert ten_days_later == date(2024, 2, 10)  # correctly rolled into February

    # --- date arithmetic crossing a YEAR boundary ---------------------------
    end_of_december = date(2024, 12, 20)
    two_weeks_later = end_of_december + timedelta(weeks=2)
    assert two_weeks_later == date(2025, 1, 3)  # correctly rolled into next year

    # --- leap year correctness: Feb 29 exists in 2024, not in 2025 ----------
    assert date(2024, 2, 29).day == 29  # 2024 is a leap year
    try:
        date(2025, 2, 29)  # 2025 is NOT a leap year
        raised = False
    except ValueError:
        raised = True
    assert raised, "Feb 29 must not exist in a non-leap year"

    # one year after Feb 29, 2024 is NOT Feb 29 (it doesn't exist) -- you
    # must decide the policy yourself; naive +365 days lands on Feb 28.
    leap_day = date(2024, 2, 29)
    naive_one_year_later = leap_day + timedelta(days=365)
    assert naive_one_year_later == date(2025, 2, 28)  # NOT Feb 29 -- it can't be

    # --- datetime arithmetic across a boundary preserves time-of-day --------
    new_years_eve_night = datetime(2024, 12, 31, 23, 30)
    two_hours_later = new_years_eve_night + timedelta(hours=2)
    assert two_hours_later == datetime(2025, 1, 1, 1, 30)  # rolled into next year

    print("OK")


if __name__ == "__main__":
    main()
