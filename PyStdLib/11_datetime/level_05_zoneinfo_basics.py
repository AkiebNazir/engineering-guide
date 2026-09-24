"""
LEVEL 05 (core) - zoneinfo.ZoneInfo: real IANA timezones
============================================================
You will learn
  * datetime.timezone only models a FIXED UTC offset; zoneinfo.ZoneInfo
    models a real, named place with its historical/DST-aware rules
  * attaching a ZoneInfo to a datetime makes it aware, with a correct
    utcoffset() for that specific date
  * .astimezone() converts an aware datetime to a different zone, keeping
    the same absolute instant
  * the same wall-clock hour has a DIFFERENT UTC offset depending on the
    time of year in a DST-observing zone

Run: python level_05_zoneinfo_basics.py
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def main() -> None:
    lisbon = ZoneInfo("Europe/Lisbon")
    new_york = ZoneInfo("America/New_York")
    tokyo = ZoneInfo("Asia/Tokyo")

    # --- attaching a ZoneInfo makes a datetime aware -------------------------
    winter_in_lisbon = datetime(2024, 1, 15, 12, 0, tzinfo=lisbon)
    assert winter_in_lisbon.tzinfo is lisbon
    assert winter_in_lisbon.utcoffset() == timedelta(hours=0)  # WET, winter

    # --- a fixed timezone can NOT know about DST -----------------------------
    summer_in_lisbon = datetime(2024, 7, 15, 12, 0, tzinfo=lisbon)
    assert summer_in_lisbon.utcoffset() == timedelta(hours=1)  # WEST, summer DST

    # A fixed-offset timezone gives the same offset year round -- it cannot
    # reproduce the winter/summer difference ZoneInfo just showed.
    fixed_utc_plus_1 = timezone(timedelta(hours=1))
    always_plus_one = datetime(2024, 1, 15, 12, 0, tzinfo=fixed_utc_plus_1)
    assert always_plus_one.utcoffset() == timedelta(hours=1)  # never changes

    # --- astimezone(): same instant, different wall-clock representation ----
    meeting_ny = datetime(2024, 3, 15, 9, 0, tzinfo=new_york)  # 9 AM in NY
    meeting_tokyo = meeting_ny.astimezone(tokyo)
    # NY (EDT, UTC-4 in March) 9 AM == Tokyo (UTC+9) 22:00 the same day
    assert meeting_tokyo.hour == 22
    assert meeting_tokyo.day == meeting_ny.day

    # converting preserves the absolute instant: both represent the same UTC moment
    assert meeting_ny.astimezone(timezone.utc) == meeting_tokyo.astimezone(timezone.utc)

    # --- comparing across zones works because both are aware -----------------
    later_meeting = datetime(2024, 3, 15, 10, 0, tzinfo=new_york)
    assert meeting_ny < later_meeting
    assert meeting_tokyo < later_meeting.astimezone(tokyo)

    # --- ZoneInfo objects for the same key are cached/equal ------------------
    assert ZoneInfo("Europe/Lisbon") == lisbon

    print("OK")


if __name__ == "__main__":
    main()
