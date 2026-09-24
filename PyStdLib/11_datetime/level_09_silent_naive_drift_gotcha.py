"""
LEVEL 09 (advanced) - production trap: naive datetimes silently misclassified as UTC
========================================================================================
You will learn
  * a very common real bug: a system captures LOCAL naive timestamps
    (datetime.now() with no tzinfo), and a downstream consumer assumes
    "naive must mean UTC" and just slaps tzinfo=timezone.utc onto it
  * this does NOT raise -- it silently produces a wrong instant, offset by
    exactly the source's real UTC offset, and every downstream calculation
    built on it is quietly wrong
  * the fix: never assume a naive datetime's zone; know and attach the
    TRUE source zone, then convert explicitly

Run: python level_09_silent_naive_drift_gotcha.py
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def classify_utc_hour_bucket(moment_utc: datetime) -> int:
    """A stand-in for real logic: which UTC hour did this event fall in."""
    assert moment_utc.tzinfo is not None
    return moment_utc.astimezone(timezone.utc).hour


def main() -> None:
    # --- the source of the bug: a New York server logs a NAIVE local time ---
    # It is really 9:00 AM Eastern Daylight Time (UTC-4) on March 15, 2024.
    server_logged_naive = datetime(2024, 3, 15, 9, 0, 0)  # no tzinfo at all!

    # --- the buggy downstream assumption: "naive must mean UTC" -------------
    buggy_as_utc = server_logged_naive.replace(tzinfo=timezone.utc)
    buggy_bucket = classify_utc_hour_bucket(buggy_as_utc)
    assert buggy_bucket == 9  # it runs fine, no exception -- and it's WRONG

    # --- the true instant, using the REAL source timezone --------------------
    true_source_zone = ZoneInfo("America/New_York")
    correctly_tagged = server_logged_naive.replace(tzinfo=true_source_zone)
    correct_bucket = classify_utc_hour_bucket(correctly_tagged)
    assert correct_bucket == 13  # 9 AM EDT (UTC-4) is 13:00 UTC

    # --- the silent damage: two different, both "successful", answers -------
    assert buggy_bucket != correct_bucket, (
        "this IS the bug: no exception was raised, but the two answers disagree "
        "by exactly the source's UTC offset (4 hours here)"
    )
    hours_of_silent_drift = correct_bucket - buggy_bucket
    assert hours_of_silent_drift == 4

    # --- the fix, applied consistently: never fabricate a timezone -----------
    # If you don't know the true source zone, the honest options are:
    #   (a) fix the upstream system to log aware timestamps in the first place
    #   (b) explicitly document and attach the KNOWN true source zone
    # Never (c): assume naive == UTC without verifying it.
    def ingest_event(naive_local_timestamp: datetime, source_zone: ZoneInfo) -> datetime:
        """The correct ingestion boundary: tag with the TRUE zone, then normalize."""
        aware_local = naive_local_timestamp.replace(tzinfo=source_zone)
        return aware_local.astimezone(timezone.utc)

    normalized = ingest_event(server_logged_naive, true_source_zone)
    assert normalized == datetime(2024, 3, 15, 13, 0, 0, tzinfo=timezone.utc)
    assert normalized.hour == 13  # matches the correct bucket computed above

    print("OK")


if __name__ == "__main__":
    main()
