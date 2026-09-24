"""
LEVEL 10 (advanced) - Capstone: a small event-processing pipeline
=====================================================================
You will learn
  * combining namedtuple (structured records), deque (bounded recent-events
    ring buffer), defaultdict(list) (grouping), Counter (stats), and ChainMap
    (layered thresholds) in one realistic, small program

Run: python level_10_event_pipeline_capstone.py
"""
from collections import ChainMap, Counter, defaultdict, deque, namedtuple

Event = namedtuple("Event", ["type", "user", "value"])

DEFAULT_THRESHOLDS = {"purchase": 100, "click": 1}
ADMIN_OVERRIDES = {"purchase": 500}   # admins get a higher purchase-alert bar

RAW_EVENTS = [
    Event("click", "alice", 1),
    Event("purchase", "alice", 250),
    Event("click", "bob", 1),
    Event("purchase", "bob", 50),
    Event("login", "alice", 0),
    Event("purchase", "carol", 600),
    Event("click", "carol", 1),
]


def process(events: list[Event], recent_maxlen: int = 3):
    thresholds = ChainMap(ADMIN_OVERRIDES, DEFAULT_THRESHOLDS)
    recent = deque(maxlen=recent_maxlen)     # ring buffer: only the latest N events
    by_user: defaultdict[str, list[Event]] = defaultdict(list)
    type_counts: Counter[str] = Counter()
    alerts = []

    for event in events:
        recent.append(event)
        by_user[event.user].append(event)
        type_counts[event.type] += 1

        threshold = thresholds.get(event.type)
        if threshold is not None and event.value >= threshold:
            alerts.append(event)

    return recent, by_user, type_counts, alerts


if __name__ == "__main__":
    recent, by_user, type_counts, alerts = process(RAW_EVENTS)

    # the ring buffer only kept the LAST 3 events, oldest ones evicted
    assert len(recent) == 3
    assert [e.type for e in recent] == ["login", "purchase", "click"]

    # grouped by user via defaultdict(list) -- no manual setdefault anywhere
    assert len(by_user["alice"]) == 3
    assert len(by_user["bob"]) == 2
    assert len(by_user["carol"]) == 2
    assert "dave" not in by_user   # never touched -> never created (a real dict, checked with `in`)

    # Counter tallies event types
    assert type_counts["click"] == 3
    assert type_counts["purchase"] == 3
    assert type_counts.most_common(1) == [("click", 3)] or type_counts.most_common(1) == [("purchase", 3)]
    assert sum(type_counts.values()) == len(RAW_EVENTS)

    # ChainMap threshold: purchase alert bar is 500 (admin override), not 100 (default)
    alert_types_and_users = [(e.type, e.user, e.value) for e in alerts]
    assert ("purchase", "carol", 600) in alert_types_and_users   # 600 >= 500 -> alert
    assert ("purchase", "alice", 250) not in alert_types_and_users   # 250 < 500 -> no alert
    # every click alerts too, since the click threshold is 1
    assert sum(1 for t, _, _ in alert_types_and_users if t == "click") == 3

    print(f"recent ring buffer: {[e.type for e in recent]}")
    print(f"event counts: {dict(type_counts)}")
    print(f"alerts: {alert_types_and_users}")
    print("OK")
