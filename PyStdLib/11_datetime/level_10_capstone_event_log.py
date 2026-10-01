"""
LEVEL 10 (advanced) - capstone: a small timezone-aware event-log processor
==============================================================================
You will learn
  * how construction, strftime/strptime, timezone-aware conversion,
    timedelta accounting and monotonic timing combine in one realistic task
  * parsing per-region local log lines, normalizing them to UTC with the
    correct real IANA zone, computing session durations correctly, and
    timing the whole pipeline with time.monotonic()

Run: python level_10_capstone_event_log.py
"""
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

LOG_FORMAT = "%Y-%m-%d %H:%M:%S"

# (local timestamp string, region's IANA zone, user, event)
RAW_EVENTS = [
    ("2024-03-15 09:00:00", "America/New_York", "alice", "login"),
    ("2024-03-15 14:45:00", "America/New_York", "alice", "logout"),
    ("2024-03-15 20:10:00", "Europe/Lisbon", "bob", "login"),
    ("2024-03-15 21:40:00", "Europe/Lisbon", "bob", "logout"),
]


def normalize_to_utc(local_str: str, zone_name: str) -> datetime:
    """Parse a naive local timestamp string and correctly tag + convert it."""
    naive = datetime.strptime(local_str, LOG_FORMAT)
    aware_local = naive.replace(tzinfo=ZoneInfo(zone_name))
    return aware_local.astimezone(timezone.utc)


def main() -> None:
    pipeline_start = time.monotonic()

    normalized = [
        (normalize_to_utc(ts, zone), user, event)
        for ts, zone, user, event in RAW_EVENTS
    ]

    # --- pair each user's login with their logout, compute session length --
    sessions: dict[str, dict] = {}
    for utc_time, user, event in normalized:
        if event == "login":
            sessions[user] = {"login": utc_time}
        elif event == "logout" and user in sessions:
            sessions[user]["logout"] = utc_time

    durations = {}
    for user, session in sessions.items():
        if "login" in session and "logout" in session:
            durations[user] = (session["logout"] - session["login"]).total_seconds()

    pipeline_elapsed = time.monotonic() - pipeline_start

    # --- verify the timezone conversion actually happened correctly --------
    # Alice: 09:00-14:45 EDT (UTC-4) -> 13:00-18:45 UTC -> 5h45m session
    assert durations["alice"] == (5 * 3600 + 45 * 60)

    # Bob: 20:10-21:40 in Lisbon. On March 15, EU summer time hasn't started
    # yet (2024's change is March 31), so Lisbon is WET = UTC+0 -> the UTC
    # timestamps are numerically identical to the local ones -> 1h30m session
    assert durations["bob"] == (1 * 3600 + 30 * 60)

    # --- both sessions normalized to real, comparable UTC instants ---------
    alice_login_utc = sessions["alice"]["login"]
    bob_login_utc = sessions["bob"]["login"]
    assert alice_login_utc.tzinfo is timezone.utc
    assert bob_login_utc.tzinfo is timezone.utc
    assert alice_login_utc < bob_login_utc  # Alice logged in first, in absolute time

    # --- total time accounted for across all sessions -----------------------
    total_session_seconds = sum(durations.values())
    assert total_session_seconds == durations["alice"] + durations["bob"]

    # --- the pipeline itself ran fast; monotonic time cannot be negative ---
    assert pipeline_elapsed >= 0
    assert pipeline_elapsed < 1.0  # trivially fast for 4 log lines

    print(f"alice session: {durations['alice'] / 3600:.2f}h")
    print(f"bob session:   {durations['bob'] / 3600:.2f}h")
    print(f"pipeline processed {len(RAW_EVENTS)} events in {pipeline_elapsed * 1000:.3f} ms")
    print("OK")


if __name__ == "__main__":
    main()
