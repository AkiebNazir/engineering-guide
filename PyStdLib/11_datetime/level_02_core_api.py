"""
LEVEL 02 (basic) - the core datetime API surface
===================================================
You will learn
  * .replace() for producing a modified copy without mutating the original
  * .weekday() / .isoweekday() for day-of-week, and .isoformat() for a
    standard string form
  * comparing datetimes/dates directly with <, <=, ==, > (they're ordered)
  * min()/max()/sorted() work on dates and datetimes out of the box
  * datetime objects are immutable: every "modification" returns a new one

Run: python level_02_core_api.py
"""
from datetime import date, datetime


def main() -> None:
    d = date(2024, 3, 15)  # a Friday

    # --- immutability: .replace() returns a NEW object ----------------------
    next_year = d.replace(year=2025)
    assert next_year == date(2025, 3, 15)
    assert d == date(2024, 3, 15)  # the original is untouched

    # --- day-of-week -----------------------------------------------------------
    # weekday(): Monday=0 .. Sunday=6.  isoweekday(): Monday=1 .. Sunday=7.
    assert d.weekday() == 4       # Friday
    assert d.isoweekday() == 5    # Friday, ISO numbering

    # --- ISO string form ---------------------------------------------------
    assert d.isoformat() == "2024-03-15"

    dt = datetime(2024, 3, 15, 14, 30, 45)
    assert dt.isoformat() == "2024-03-15T14:30:45"
    assert dt.weekday() == 4  # datetime has the same weekday methods as date

    # --- fromisoformat is the round-trip partner of isoformat --------------
    assert date.fromisoformat("2024-03-15") == d
    assert datetime.fromisoformat("2024-03-15T14:30:45") == dt

    # --- ordering: dates and datetimes compare like any other value --------
    earlier = date(2024, 1, 1)
    later = date(2024, 12, 31)
    assert earlier < d < later
    assert sorted([later, earlier, d]) == [earlier, d, later]
    assert min(later, earlier, d) == earlier
    assert max(later, earlier, d) == later

    # --- .replace() also works for partial updates on datetime --------------
    same_day_midnight = dt.replace(hour=0, minute=0, second=0)
    assert same_day_midnight == datetime(2024, 3, 15, 0, 0, 0)
    assert dt.hour == 14  # dt itself is still untouched

    print("OK")


if __name__ == "__main__":
    main()
