"""
================================================================================
LLD 014 · Task / Job Scheduler (in-process)                        [Tier 2]
Time box: 45 minutes (5 clarify · 7 model · 5 API · 20 code · 8 extend)
================================================================================

PROBLEM
-------
Design and implement an in-process job scheduler library: run a function
later, periodically, with priorities and retries.

The interviewer says: "Design a task scheduler like cron / Celery beat, but as
a library in one process." These are the agreed requirements.

REQUIREMENTS
------------
  1. Scheduler(clock=time.monotonic, retry=None)
     schedule(fn, *, delay=None, at=None, every=None, priority=0, name="",
              key=None, retry=None) -> job id (int)
       * run_at = `at`, else now + (delay or 0). Giving both, delay < 0, or
         every <= 0 -> ValueError.
       * key: if a NON-FINISHED job with this key exists, return its id and
         schedule nothing. Once that job finishes (succeeded/dead/cancelled)
         the key can be used again.
  2. run_pending() -> int: on the caller's thread, run every job that is due
     now (run_at <= clock()), returns how many ran. Among due jobs, higher
     priority runs first; ties by earlier run_at, then submission order.
  3. cancel(id) -> True if the job was scheduled or running; False if unknown
     or already finished. Cancelled jobs never run (again).
  4. status(id) -> JobView(id, name, status, attempts, run_at, last_error, runs)
       runs = executions so far; attempts = FAILED executions so far;
       last_error = "ExceptionType: message" of the latest run, or None.
  5. Retries: when a one-off job raises an Exception, attempts += 1 and
     policy.delay(attempts) gives the seconds until the next try, or None to
     give up -> status DEAD, and the job appears in dead_letters().
        NoRetry()  (default) — always None
        ExponentialBackoff(base=1, factor=2, max_delay=60, max_attempts=5,
                           jitter=0.0, rng=None)
            delay(attempt) = None if attempt >= max_attempts, else
            min(max_delay, base * factor**(attempt-1)) * (1 - jitter * rng.random())
  6. Recurring (every=E): after each run the next run_at is the previous
     run_at + E, advanced by whole multiples of E until it's in the future
     (missed slots are skipped, not replayed). Failures don't use the retry
     policy. A recurring job never runs concurrently with itself.
  7. next_due() -> earliest run_at among scheduled jobs, or None.
  8. start(workers=4) / shutdown(wait=True): run jobs on worker threads,
     waking when the next job is due (no polling loop).

WHAT THE INTERVIEWER IS LOOKING FOR
-----------------------------------
  * Data structures: why one heap by run_at can't honour priority.
  * How workers sleep until the next job without polling.
  * Retry with backoff and jitter; dead letters.
  * Fixed-rate vs fixed-delay; what happens after a long pause.
  * Is the lock held while a job runs?

FOLLOW-UPS TO PREPARE
---------------------
  surviving restarts · exactly-once vs at-least-once · cron expressions ·
  job timeouts · DAG dependencies · rate-limited queues.

THE API BELOW IS FIXED so the tests at the bottom can run against your code.
Run this file: all checks should print PASS, then ALL PASSED.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Hashable


class JobStatus(Enum):
    SCHEDULED = "scheduled"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    DEAD = "dead"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class JobView:
    id: int
    name: str
    status: JobStatus
    attempts: int
    run_at: float
    last_error: str | None
    runs: int


class NoRetry:
    def delay(self, attempt: int) -> float | None:
        return None


class ExponentialBackoff:
    def __init__(self, base: float = 1.0, factor: float = 2.0, max_delay: float = 60.0,
                 max_attempts: int = 5, jitter: float = 0.0, rng: random.Random | None = None) -> None:
        raise NotImplementedError

    def delay(self, attempt: int) -> float | None:
        raise NotImplementedError


class Scheduler:
    def __init__(self, clock: Callable[[], float] = time.monotonic, retry=None) -> None:
        # YOUR CODE HERE
        raise NotImplementedError

    def schedule(self, fn: Callable[[], object], *, delay: float | None = None, at: float | None = None,
                 every: float | None = None, priority: int = 0, name: str = "",
                 key: Hashable | None = None, retry=None) -> int:
        raise NotImplementedError

    def cancel(self, job_id: int) -> bool: raise NotImplementedError
    def status(self, job_id: int) -> JobView: raise NotImplementedError
    def dead_letters(self) -> list[JobView]: raise NotImplementedError
    def next_due(self) -> float | None: raise NotImplementedError
    def run_pending(self) -> int: raise NotImplementedError
    def start(self, workers: int = 4) -> None: raise NotImplementedError
    def shutdown(self, wait: bool = True) -> None: raise NotImplementedError


# ===================================================================== TESTS ==
# Identical to the solution file's tests. Make them all PASS.
class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


def _check(label: str, ok: bool) -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    return ok


def _raises(exc, fn) -> bool:
    try:
        fn()
    except exc:
        return True
    return False


def run_tests() -> bool:
    all_ok = True
    print("--- ordering: time, then priority among due jobs ---")
    clock = FakeClock()
    s = Scheduler(clock)
    log: list[str] = []
    s.schedule(lambda: log.append("low@5"), delay=5, priority=0)
    s.schedule(lambda: log.append("high@6"), delay=6, priority=10)
    s.schedule(lambda: log.append("mid@1"), delay=1, priority=5)
    clock.t = 0.5
    all_ok &= _check("nothing runs before it's due", s.run_pending() == 0 and log == [])
    clock.t = 1
    s.run_pending()
    clock.t = 7                                         # both remaining jobs overdue
    s.run_pending()
    all_ok &= _check("overdue jobs run by priority, not by run_at",
                     log == ["mid@1", "high@6", "low@5"])
    all_ok &= _check("next_due is None when empty", s.next_due() is None)

    print("\n--- cancel and de-duplication ---")
    clock = FakeClock()
    s = Scheduler(clock)
    ran: list[int] = []
    a = s.schedule(lambda: ran.append(1), delay=1)
    b = s.schedule(lambda: ran.append(2), delay=2, key="daily-report")
    all_ok &= _check("same live key returns the same job", s.schedule(lambda: ran.append(3), delay=0, key="daily-report") == b)
    all_ok &= _check("cancel scheduled -> True; again -> False", s.cancel(a) and not s.cancel(a))
    clock.t = 5
    s.run_pending()
    all_ok &= _check("cancelled job never runs", ran == [2] and s.status(a).status is JobStatus.CANCELLED)
    all_ok &= _check("finished job can't be cancelled; its key is free again",
                     not s.cancel(b) and s.schedule(lambda: None, key="daily-report") != b)

    print("\n--- retries with exponential backoff ---")
    clock = FakeClock()
    s = Scheduler(clock)
    calls: list[float] = []

    def flaky():
        calls.append(clock.t)
        if len(calls) < 3:
            raise ConnectionError("db down")

    jid = s.schedule(flaky, retry=ExponentialBackoff(base=1, factor=2, max_attempts=5))
    for t in (0, 0.9, 1, 2.9, 3, 10):
        clock.t = t
        s.run_pending()
    v = s.status(jid)
    all_ok &= _check("runs at t=0, 1 (+1 s), 3 (+2 s) then succeeds",
                     calls == [0, 1, 3] and v.status is JobStatus.SUCCEEDED and v.attempts == 2)

    def always_fails():
        raise ValueError("bad input")

    dead = s.schedule(always_fails, retry=ExponentialBackoff(base=1, max_attempts=3))
    for t in range(10, 30):
        clock.t = t
        s.run_pending()
    all_ok &= _check("gives up after max_attempts -> DEAD, in dead letters with the error",
                     s.status(dead).status is JobStatus.DEAD and s.status(dead).runs == 3
                     and [d.last_error for d in s.dead_letters()] == ["ValueError: bad input"])
    jittered = ExponentialBackoff(base=4, jitter=0.5, rng=random.Random(1))
    all_ok &= _check("jitter keeps delay within [d*(1-j), d]",
                     all(2.0 <= jittered.delay(1) <= 4.0 for _ in range(200)))

    print("\n--- recurring jobs ---")
    clock = FakeClock()
    s = Scheduler(clock)
    ticks: list[float] = []
    rec = s.schedule(lambda: ticks.append(clock.t), every=10)
    for t in (0, 5, 10, 20):
        clock.t = t
        s.run_pending()
    clock.t = 45                                         # process paused: slots 30 and 40 missed
    s.run_pending()
    all_ok &= _check("fixed rate at 0, 10, 20; after a pause runs once at 45, not 3 times",
                     ticks == [0, 10, 20, 45] and s.status(rec).run_at == 50)
    s.cancel(rec)
    clock.t = 100
    all_ok &= _check("cancelled recurring job stops", s.run_pending() == 0)

    print("\n--- validation ---")
    s = Scheduler(FakeClock())
    all_ok &= _check("delay and at together", _raises(ValueError, lambda: s.schedule(lambda: 1, delay=1, at=2)))
    all_ok &= _check("every <= 0", _raises(ValueError, lambda: s.schedule(lambda: 1, every=0)))
    all_ok &= _check("negative delay", _raises(ValueError, lambda: s.schedule(lambda: 1, delay=-1)))
    return all_ok
# ================================================================= END TESTS ==


if __name__ == "__main__":
    ok = run_tests()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
