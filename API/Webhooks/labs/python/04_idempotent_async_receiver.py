"""
LAB 04 (advanced) - A production-grade receiver: verify, acknowledge fast, deduplicate, process async
=====================================================================================================
Senders deliver AT LEAST once. That means your endpoint WILL receive:
    * duplicates            (a retry after your slow response, or a sender bug)
    * out-of-order events   (retries reorder: "updated" can arrive before "created")
    * bursts                (10,000 events after an outage)
You will build the standard architecture that survives all three:

    POST /webhook --> [ verify signature ] --> [ INSERT event into inbox, UNIQUE(event_id) ] --> 200 (fast!)
                                                              |
                                                     background WORKER reads the inbox
                                                     processes each event exactly-once-in-effect

  * ACK FAST: do only the cheap, durable thing (store the raw event) before answering.
    Senders time out at ~5-30s; slow processing => retries => more duplicates => more load.
  * IDEMPOTENCY: a UNIQUE constraint on event id makes "have I seen this?" atomic. A check-then-insert
    in application code has a race; the database does not.  (SQLite here, any SQL DB works.)
  * a REAL race: 12 threads deliver the SAME event at once; exactly one is processed.
  * ORDERING: never assume order. Compare a version / timestamp and ignore stale updates.
  * FAILURE: a crashing worker leaves the row pending; it is retried later. Nothing is lost.

Run it  python 04_idempotent_async_receiver.py
"""
import json
import os
import queue
import sqlite3
import tempfile
import threading
import time

DB_PATH = os.path.join(tempfile.mkdtemp(), "inbox.db")     # a FILE, so every thread gets its own real connection
_local = threading.local()


def db() -> sqlite3.Connection:
    """One connection per thread, exactly like a connection pool. The DATABASE arbitrates concurrency."""
    if not hasattr(_local, "conn"):
        _local.conn = sqlite3.connect(DB_PATH, timeout=10, isolation_level=None)     # autocommit
    return _local.conn


db().executescript("""
CREATE TABLE inbox (
    event_id   TEXT PRIMARY KEY,              -- <- the idempotency key: UNIQUE by construction
    type       TEXT NOT NULL,
    payload    TEXT NOT NULL,
    received_at REAL NOT NULL,
    status     TEXT NOT NULL DEFAULT 'pending',   -- pending | done | failed
    attempts   INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE orders (id TEXT PRIMARY KEY, status TEXT, version INTEGER);   -- our domain state
""")

WORK = queue.Queue()
processed_effects: list[str] = []            # observable side effects, to prove exactly-once-in-effect


# ------------------------------------------------------------ the HTTP handler ---
def receive(event_json: str) -> int:
    """What your POST handler does AFTER signature verification (lab 01). Returns the HTTP status."""
    try:
        event = json.loads(event_json)
        event_id, etype = event["id"], event["type"]
    except (json.JSONDecodeError, KeyError):
        return 400
    cur = db().execute("INSERT INTO inbox(event_id, type, payload, received_at) VALUES (?,?,?,?) "
                       "ON CONFLICT(event_id) DO NOTHING", (event_id, etype, event_json, time.time()))
    is_new = cur.rowcount == 1                           # atomic: exactly ONE concurrent inserter sees 1
    if is_new:
        WORK.put(event_id)                               # hand off; do not process inline
    return 200                                           # duplicates ALSO get 200: "yes, I have it, stop retrying"


# ------------------------------------------------------------------ the worker ---
crash_once = {"evt_crash"}


def handle(event: dict):
    """Business logic. Must itself tolerate being run twice (defence in depth)."""
    data = event["data"]
    if event["id"] in crash_once:
        crash_once.discard(event["id"])
        raise RuntimeError("simulated crash / deploy in the middle of processing")
    # One atomic statement: apply the update only if it is NEWER than what we hold (no read-then-write race).
    cur = db().execute("INSERT INTO orders(id, status, version) VALUES (?,?,?) "
                       "ON CONFLICT(id) DO UPDATE SET status=excluded.status, version=excluded.version "
                       "WHERE excluded.version > orders.version", (data["order_id"], data["status"], data["version"]))
    if cur.rowcount == 0:
        processed_effects.append(f"IGNORED stale {event['type']} v{data['version']} for {data['order_id']}")
        return                                            # an OLDER update arrived late: do not overwrite newer state
    processed_effects.append(f"APPLIED {event['type']} v{data['version']} for {data['order_id']} -> {data['status']}")


def worker_once() -> bool:
    try:
        event_id = WORK.get_nowait()
    except queue.Empty:
        return False
    payload, = db().execute("SELECT payload FROM inbox WHERE event_id=?", (event_id,)).fetchone()
    db().execute("UPDATE inbox SET attempts = attempts + 1 WHERE event_id=?", (event_id,))
    try:
        handle(json.loads(payload))
        db().execute("UPDATE inbox SET status='done' WHERE event_id=?", (event_id,))
    except Exception:
        WORK.put(event_id)                                # in production: leave 'pending'; a sweeper re-enqueues it
    return True


def drain():
    while worker_once():
        pass


def evt(event_id: str, etype: str, order_id: str, status: str, version: int) -> str:
    return json.dumps({"id": event_id, "type": etype, "data": {"order_id": order_id, "status": status, "version": version}})


if __name__ == "__main__":
    print("== 1. a duplicate is acknowledged but processed once ==")
    body = evt("evt_1", "order.created", "o_1", "created", 1)
    print("  first delivery :", receive(body), "| second delivery (a retry):", receive(body))
    drain()
    inbox = db().execute("SELECT COUNT(*) FROM inbox").fetchone()[0]
    print("  inbox rows:", inbox, "| effects:", processed_effects)
    assert inbox == 1 and len(processed_effects) == 1

    print("\n== 2. a REAL race: 12 threads deliver the same event simultaneously ==")
    racy = evt("evt_race", "order.created", "o_2", "created", 1)
    statuses: list[int] = []
    barrier = threading.Barrier(12)
    def hit():
        barrier.wait()                                    # release all threads at the same instant
        statuses.append(receive(racy))
    ts = [threading.Thread(target=hit) for _ in range(12)]
    [t.start() for t in ts]; [t.join() for t in ts]
    drain()
    applied = [e for e in processed_effects if "o_2" in e]
    print(f"  all 12 got HTTP {set(statuses)} | inbox rows for evt_race: "
          f"{db().execute('SELECT COUNT(*) FROM inbox WHERE event_id=?', ('evt_race',)).fetchone()[0]} | times applied: {len(applied)}")
    assert set(statuses) == {200} and len(applied) == 1
    print("  (each thread has its OWN connection; a Python `if event_id in seen_set:` check-then-add would let")
    print("   several through, the database's UNIQUE key cannot)")

    print("\n== 3. out-of-order delivery: v2 arrives BEFORE v1 ==")
    receive(evt("evt_o2", "order.updated", "o_3", "shipped", 2))
    receive(evt("evt_o1", "order.created", "o_3", "created", 1))       # the late, older one
    drain()
    state = db().execute("SELECT status, version FROM orders WHERE id='o_3'").fetchone()
    for e in [e for e in processed_effects if "o_3" in e]:
        print("  ", e)
    print("  final state of o_3:", state)
    assert state == ("shipped", 2)

    print("\n== 4. the worker crashes mid-event: nothing is lost ==")
    receive(evt("evt_crash", "order.created", "o_4", "created", 1))
    drain()
    row = db().execute("SELECT status, attempts FROM inbox WHERE event_id='evt_crash'").fetchone()
    print(f"  after the crash + retry: status={row[0]} attempts={row[1]}; order o_4 =",
          db().execute("SELECT status FROM orders WHERE id='o_4'").fetchone())
    assert row == ("done", 2)

    print("\n== 5. ack speed: the handler only does an INSERT ==")
    t0 = time.perf_counter()
    for i in range(2000):
        receive(evt(f"evt_burst_{i}", "order.created", f"o_b{i}", "created", 1))
    dt = time.perf_counter() - t0
    print(f"  accepted 2000 events in {dt * 1000:.0f} ms ({dt / 2000 * 1e6:.0f} us each) - a burst never times out the sender")
    t0 = time.perf_counter(); drain(); print(f"  the worker then drained them in {(time.perf_counter() - t0) * 1000:.0f} ms, at its own pace")
    assert db().execute("SELECT COUNT(*) FROM inbox WHERE status!='done'").fetchone()[0] == 0
    print("\nOK")
