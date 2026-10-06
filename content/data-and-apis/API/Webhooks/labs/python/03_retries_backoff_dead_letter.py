"""
LAB 03 (advanced) - A reliable delivery engine: retries, backoff, Retry-After, dead letters, auto-disable
=========================================================================================================
Receivers are down for deploys, overloaded, buggy, or just slow. A sender that fires once and forgets
loses events. You will build the core of what Stripe/GitHub/Shopify run for every event:

  * AT-LEAST-ONCE delivery: retry until the receiver returns 2xx  (=> receivers WILL see duplicates)
  * a retry schedule with exponential backoff + JITTER, spanning hours or days
  * classifying responses:
        2xx                         delivered
        410 Gone                    the endpoint asked to be removed: disable it, stop retrying
        429 + Retry-After           obey the receiver's own pacing
        5xx / timeout / conn refused  transient: retry
        other 4xx                   still retried (the receiver may fix a bug and redeploy) but noted
  * a DEAD-LETTER queue for events that exhausted their attempts, with manual REPLAY after a fix
  * auto-DISABLE for endpoints that fail continuously (protects your workers; notifies the owner)
  * time is virtual (a fake clock), so days of retries run in milliseconds and the test is exact

    attempt 1 -> 503 -> wait ~10s -> attempt 2 -> 503 -> wait ~1m -> attempt 3 -> 200  DELIVERED
    attempt 1..7 all fail  ->  DEAD LETTER  ->  (receiver fixed)  ->  replay  ->  DELIVERED

Run it  python 03_retries_backoff_dead_letter.py
"""
import heapq
import random
from dataclasses import dataclass, field

random.seed(11)

SCHEDULE = [0, 10, 60, 300, 1800, 7200, 18000]            # seconds to wait BEFORE attempt 1, 2, 3, ... (7 attempts, ~7h)
MAX_ATTEMPTS = len(SCHEDULE)
DISABLE_AFTER_CONSECUTIVE_FAILURES = 12


def with_jitter(seconds: float, fraction: float = 0.2) -> float:
    """+/-20%: retries from many events spread out instead of arriving in lockstep."""
    return seconds * random.uniform(1 - fraction, 1 + fraction)


def fmt(seconds: float) -> str:
    if seconds < 90:
        return f"{seconds:.0f}s"
    if seconds < 5400:
        return f"{seconds / 60:.0f}m"
    return f"{seconds / 3600:.1f}h"


@dataclass
class Response:
    status: int | None                       # None = no response (timeout / refused)
    retry_after: float | None = None


@dataclass(order=True)
class Job:
    due: float
    seq: int
    event_id: str = field(compare=False)
    endpoint: str = field(compare=False)
    attempt: int = field(compare=False, default=0)


@dataclass
class Endpoint:
    name: str
    handler: callable                          # (event_id, attempt) -> Response
    enabled: bool = True
    consecutive_failures: int = 0
    disabled_reason: str = ""


class Engine:
    def __init__(self):
        self.now = 0.0                          # virtual clock
        self.q: list[Job] = []
        self.seq = 0
        self.endpoints: dict[str, Endpoint] = {}
        self.dead_letters: list[Job] = []
        self.delivered: dict[str, float] = {}
        self.history: dict[tuple[str, str], list[str]] = {}

    def add_endpoint(self, ep: Endpoint):
        self.endpoints[ep.name] = ep

    def enqueue(self, event_id: str, endpoint: str, delay: float = 0.0, attempt: int = 0):
        self.seq += 1
        heapq.heappush(self.q, Job(self.now + delay, self.seq, event_id, endpoint, attempt))

    def run_until_idle(self, horizon: float = 10 ** 7):
        while self.q and self.q[0].due <= self.now + horizon:
            job = heapq.heappop(self.q)
            self.now = max(self.now, job.due)               # jump the clock to the next due job
            self.attempt(job)

    def attempt(self, job: Job):
        ep = self.endpoints[job.endpoint]
        log = self.history.setdefault((job.event_id, job.endpoint), [])
        if not ep.enabled:
            log.append(f"t={fmt(self.now)} skipped: endpoint disabled")
            return
        resp = ep.handler(job.event_id, job.attempt + 1)
        outcome = "no response" if resp.status is None else str(resp.status)
        log.append(f"t={fmt(self.now)} attempt {job.attempt + 1}: {outcome}")

        if resp.status is not None and 200 <= resp.status < 300:
            ep.consecutive_failures = 0
            self.delivered[f"{job.event_id}@{job.endpoint}"] = self.now
            return
        ep.consecutive_failures += 1
        if resp.status == 410:                                # explicit "stop sending me these"
            ep.enabled, ep.disabled_reason = False, "endpoint returned 410 Gone"
            log.append("  -> 410 Gone: endpoint disabled, no more retries")
            return
        if ep.consecutive_failures >= DISABLE_AFTER_CONSECUTIVE_FAILURES:
            ep.enabled, ep.disabled_reason = False, f"{ep.consecutive_failures} consecutive failures"
            log.append(f"  -> {ep.consecutive_failures} failures in a row: endpoint auto-disabled, owner notified")
            self.dead_letters.append(job)
            return
        nxt = job.attempt + 1
        if nxt >= MAX_ATTEMPTS:
            log.append("  -> attempts exhausted: moved to the DEAD-LETTER queue")
            self.dead_letters.append(job)
            return
        wait = with_jitter(SCHEDULE[nxt])
        if resp.status == 429 and resp.retry_after:            # obey the receiver's pacing if it is LONGER
            wait = max(wait, resp.retry_after)
            log.append(f"  -> 429: honouring Retry-After {resp.retry_after:.0f}s")
        self.enqueue(job.event_id, job.endpoint, wait, nxt)

    def replay_dead_letters(self):
        jobs, self.dead_letters = self.dead_letters, []
        for j in jobs:
            if self.endpoints[j.endpoint].enabled:
                self.enqueue(j.event_id, j.endpoint, 0, 0)     # a fresh start: attempt counter reset


def show(engine: Engine, event_id: str, endpoint: str):
    for line in engine.history[(event_id, endpoint)]:
        print("   ", line)


if __name__ == "__main__":
    e = Engine()

    # ---- receivers with different personalities --------------------------------
    e.add_endpoint(Endpoint("healthy", lambda ev, n: Response(200)))
    e.add_endpoint(Endpoint("flaky", lambda ev, n: Response(503) if n <= 2 else Response(200)))          # recovers on attempt 3
    e.add_endpoint(Endpoint("down", lambda ev, n: Response(None)))                                       # connection refused forever
    e.add_endpoint(Endpoint("ratelimited", lambda ev, n: Response(429, retry_after=900) if n == 1 else Response(200)))
    e.add_endpoint(Endpoint("gone", lambda ev, n: Response(410)))
    fixed = {"yes": False}
    e.add_endpoint(Endpoint("buggy", lambda ev, n: Response(200) if fixed["yes"] else Response(500)))

    for name in e.endpoints:
        e.enqueue("evt_1", name)
    e.run_until_idle()

    print("== healthy: first try ==");                        show(e, "evt_1", "healthy")
    assert "evt_1@healthy" in e.delivered and e.delivered["evt_1@healthy"] == 0

    print("\n== flaky: fails twice, then succeeds (backoff with jitter) ==");  show(e, "evt_1", "flaky")
    assert len(e.history[("evt_1", "flaky")]) == 3 and "evt_1@flaky" in e.delivered

    print("\n== ratelimited: the receiver says 'come back in 15 minutes' ==");  show(e, "evt_1", "ratelimited")
    assert e.delivered["evt_1@ratelimited"] >= 900

    print("\n== gone: 410 disables the endpoint immediately ==");  show(e, "evt_1", "gone")
    assert not e.endpoints["gone"].enabled and "evt_1@gone" not in e.delivered

    print("\n== down: 7 attempts over ~7 hours, then the dead-letter queue ==");  show(e, "evt_1", "down")
    assert any(j.endpoint == "down" for j in e.dead_letters)
    print("    the whole retry window lasted", fmt(e.now), "of virtual time (executed instantly)")

    print("\n== buggy: 500s until the customer deploys a fix; then a manual REPLAY from the dead-letter queue ==")
    assert any(j.endpoint == "buggy" for j in e.dead_letters)
    print("    dead letters before fix:", sorted(j.endpoint for j in e.dead_letters))
    fixed["yes"] = True
    e.replay_dead_letters()
    e.run_until_idle()
    assert "evt_1@buggy" in e.delivered
    print("    after replay, buggy delivered:", "evt_1@buggy" in e.delivered, "| still dead-lettered:",
          sorted(j.endpoint for j in e.dead_letters))
    assert [j.endpoint for j in e.dead_letters] == ["down"]

    print("\n== auto-disable: an endpoint that fails continuously stops consuming your workers ==")
    e2 = Engine()
    e2.add_endpoint(Endpoint("zombie", lambda ev, n: Response(503)))
    for i in range(30):
        e2.enqueue(f"evt_{i}", "zombie")
    e2.run_until_idle()
    z = e2.endpoints["zombie"]
    attempts = sum(1 for h in e2.history.values() for l in h if "attempt" in l)
    print(f"    30 events queued; the endpoint was disabled after {z.consecutive_failures} consecutive failures "
          f"({z.disabled_reason}); total attempts made: {attempts}")
    print(f"    without auto-disable: 30 events x {MAX_ATTEMPTS} attempts = {30 * MAX_ATTEMPTS} attempts")
    assert not z.enabled and attempts < 30 * MAX_ATTEMPTS

    print("\nWhat receivers must remember: this engine delivers AT LEAST once and in NO guaranteed order.")
    print("Duplicates and reordering are expected - lab 04 shows how to handle both.")
    print("\nOK")
