"""
LEVEL 03 (basic) - strftime/strptime round trip: a small log-parsing idiom
=============================================================================
You will learn
  * strftime(): datetime -> formatted string, using % directives
  * strptime(): formatted string -> datetime, the exact inverse
  * a realistic idiom: parse a batch of log lines with an embedded
    timestamp, extract structured data, then reformat for a report
  * common directives: %Y %m %d %H %M %S and the combined %c-style patterns

Run: python level_03_strftime_strptime_roundtrip.py
"""
from datetime import datetime

LOG_FORMAT = "%Y-%m-%d %H:%M:%S"

RAW_LOG_LINES = [
    "2024-03-15 09:02:11 | user_login | alice",
    "2024-03-15 09:05:44 | user_login | bob",
    "2024-03-15 10:14:02 | user_logout | alice",
]


def parse_log_line(line: str) -> tuple[datetime, str, str]:
    ts_str, event, user = (part.strip() for part in line.split("|"))
    timestamp = datetime.strptime(ts_str, LOG_FORMAT)
    return timestamp, event, user


def main() -> None:
    # --- strftime: format a known datetime and check exact output ----------
    moment = datetime(2024, 3, 15, 9, 2, 11)
    assert moment.strftime(LOG_FORMAT) == "2024-03-15 09:02:11"
    assert moment.strftime("%Y") == "2024"
    assert moment.strftime("%A") == "Friday"       # full weekday name
    assert moment.strftime("%B %d, %Y") == "March 15, 2024"

    # --- strptime: the exact inverse of strftime for the same format -------
    parsed = datetime.strptime("2024-03-15 09:02:11", LOG_FORMAT)
    assert parsed == moment

    # --- round trip: format then parse gets back the original ---------------
    round_tripped = datetime.strptime(moment.strftime(LOG_FORMAT), LOG_FORMAT)
    assert round_tripped == moment

    # --- realistic idiom: parse a small batch of log lines ------------------
    parsed_events = [parse_log_line(line) for line in RAW_LOG_LINES]
    assert len(parsed_events) == 3
    assert parsed_events[0][1] == "user_login"
    assert parsed_events[0][2] == "alice"
    assert parsed_events[0][0] == datetime(2024, 3, 15, 9, 2, 11)

    # --- reformat parsed timestamps for a human-readable report -------------
    report_lines = [
        f"{user} - {event} at {ts.strftime('%I:%M %p')}"
        for ts, event, user in parsed_events
    ]
    assert report_lines[0] == "alice - user_login at 09:02 AM"
    assert report_lines[2] == "alice - user_logout at 10:14 AM"

    # --- events are already chronologically parseable and sortable ----------
    events_sorted_by_time = sorted(parsed_events, key=lambda e: e[0])
    assert events_sorted_by_time == parsed_events  # log was already in order

    print("OK")


if __name__ == "__main__":
    main()
