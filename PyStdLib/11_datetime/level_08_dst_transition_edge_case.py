"""
LEVEL 08 (advanced) - a real DST transition: the ambiguous "fall back" hour
==============================================================================
You will learn
  * during "fall back", one local wall-clock hour occurs TWICE (the clock
    repeats 1:00-1:59 AM); during "spring forward", one hour is skipped
  * ZoneInfo lets you construct the ambiguous local time, and Python
    disambiguates it with the datetime.fold attribute (0 = first
    occurrence, 1 = second)
  * converting both fold values to UTC proves they are genuinely different
    real-world instants, even though the local wall-clock string is identical

Run: python level_08_dst_transition_edge_case.py
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def main() -> None:
    ny = ZoneInfo("America/New_York")

    # US DST ended Nov 3, 2024 at 2:00 AM local (clocks fall back to 1:00 AM),
    # so local times "1:30 AM" on that date happened twice.
    first_1_30 = datetime(2024, 11, 3, 1, 30, tzinfo=ny, fold=0)  # before the fall-back
    second_1_30 = datetime(2024, 11, 3, 1, 30, tzinfo=ny, fold=1)  # after the fall-back

    # --- the wall-clock string is IDENTICAL for both -------------------------
    assert first_1_30.strftime("%Y-%m-%d %H:%M") == second_1_30.strftime("%Y-%m-%d %H:%M")
    assert first_1_30.hour == second_1_30.hour == 1
    assert first_1_30.minute == second_1_30.minute == 30

    # --- but they are DIFFERENT real-world instants, exactly 1 hour apart ---
    first_utc = first_1_30.astimezone(timezone.utc)
    second_utc = second_1_30.astimezone(timezone.utc)
    assert first_utc != second_utc
    assert (second_utc - first_utc) == timedelta(hours=1)

    # --- the utcoffset differs even though local wall-clock time doesn't ----
    assert first_1_30.utcoffset() == timedelta(hours=-4)   # still EDT (fold=0)
    assert second_1_30.utcoffset() == timedelta(hours=-5)  # now EST (fold=1)

    # --- comparing them directly: Python uses fold-aware comparison ---------
    # second_1_30 is objectively LATER in absolute time, even though its
    # naive wall-clock fields are equal to first_1_30's.
    assert second_utc > first_utc

    # --- the "spring forward" gap: a local time that never existed ----------
    # US DST began March 10, 2024 at 2:00 AM local (clocks jump to 3:00 AM),
    # so "2:30 AM" on that date never happened on the wall clock at all.
    # ZoneInfo does NOT raise for this by default -- it silently normalizes
    # the offset, which is itself worth knowing rather than assuming an error.
    imaginary_time = datetime(2024, 3, 10, 2, 30, tzinfo=ny)
    # It resolves to SOME valid instant rather than raising -- confirm it is
    # at least internally consistent (round-trips through UTC and back).
    resolved_utc = imaginary_time.astimezone(timezone.utc)
    back_to_ny = resolved_utc.astimezone(ny)
    assert back_to_ny.astimezone(timezone.utc) == resolved_utc

    print("OK")


if __name__ == "__main__":
    main()
