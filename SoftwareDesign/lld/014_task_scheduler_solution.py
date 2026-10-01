"""
================================================================================
SOLUTION · LLD 014 · Task / Job Scheduler (in-process)             [Tier 2]
================================================================================

THE CORE IDEA
--------------
"Run this function later / every N seconds / retry it if it fails" — the
design is two queues and a small lifecycle:

    TIMER QUEUE   min-heap by run_at          "when is it due?"
    READY QUEUE   heap by (-priority, run_at)  "of the due jobs, which first?"

A single-heap design ordered by run_at can't honour priority: a low-priority
job due at 10:00:00.000 would run before a high-priority job due 1 ms later
even when both are overdue. Moving due jobs into a priority-ordered ready queue
fixes it.

The threaded runner must not POLL ("sleep 50 ms, check the heap"). The
dispatcher waits on a Condition with timeout = time until the earliest job;
schedule() notifies it when a new job becomes the earliest. Demo 1 measures
lateness for both.

Lifecycle and the policies around it:

    SCHEDULED ──due──▶ RUNNING ──ok──▶ SUCCEEDED
        ▲                 │ raises
        │   retry policy  ▼
        └──── delay ◀── attempts < max ──no──▶ DEAD (dead-letter list)
    SCHEDULED/RUNNING ──cancel──▶ CANCELLED
    recurring: RUNNING ──done──▶ SCHEDULED at the next slot (never overlaps itself)

Retries use exponential backoff WITH JITTER: without jitter, a thousand clients
that failed together retry together, forever (demo 2).


================================================================================
REQUIREMENTS (agreed in the first 5 minutes)
================================================================================
  1. schedule(fn, delay= | at=, every=None, priority=0, key=None, retry=None) -> id
  2. cancel(id) -> bool; status(id) -> JobView.
  3. Due jobs run highest priority first; ties by run_at, then submission order.
  4. Retry policy per job (default none): exponential backoff, max attempts,
     jitter; exhausted jobs go to a dead-letter list.
  5. Recurring jobs at a fixed rate; missed slots are skipped, not piled up; a
     recurring job never runs concurrently with itself.
  6. De-duplication key: scheduling an existing live key returns its id.
  7. Deterministic mode run_pending() for tests; threaded mode with N workers.
  Out of scope: persistence across restarts, distributed workers, cron syntax.


================================================================================
ENTITIES AND INVARIANTS
================================================================================
    JobStatus        enum
    Job (internal)   id, fn, run_at, every, priority, retry, attempts, status, key
    JobView          immutable snapshot for callers
    RetryPolicy      delay(attempt) -> seconds | None
       NoRetry, ExponentialBackoff(base, factor, max_delay, max_attempts, jitter)
    Scheduler
       INVARIANT: a job id is in the timer heap or ready heap AT MOST ONCE while
                  SCHEDULED, and in neither while RUNNING
       INVARIANT: a live dedupe key maps to exactly one non-terminal job
       all state guarded by one Condition (lock + wait/notify)


================================================================================
KEY FLOW · threaded mode (every idle worker runs this loop)
================================================================================
    with cond:
        loop:
            move every timer entry with run_at <= now into the ready heap
            ready heap has a SCHEDULED job?  -> pop it, mark RUNNING, leave the loop
            else: cond.wait(timeout = earliest run_at - now, or None)
    run fn OUTSIDE the lock
    with cond: finish(job, error) (succeed / retry / dead / next slot); notify_all

    schedule(): push to timer heap; cond.notify_all()   (wakes waiting workers
    so a job that is now the earliest is seen at once — no polling interval)


================================================================================
DESIGN DECISIONS AND ALTERNATIVES
================================================================================
  * Two heaps (delay queue -> ready queue) — the same split as Java's
    ScheduledThreadPoolExecutor + priority work queues, and as Kubernetes /
    Celery "eta" handling.
  * Lazy cancel: mark CANCELLED, skip when popped. O(1) cancel.
  * Fixed-rate with skip: next = previous slot + every, advanced past now.
    Alternative fixed-delay: next = finish time + every. Say which you picked.
  * Recurring job failures don't use the retry policy; the next slot is the retry.
  * Only an idle worker takes a job, so a burst of due jobs waits in the READY
    heap (priority still applies) rather than in a FIFO hand-off queue.
  * Timing wheel is the alternative for millions of timers with coarse precision.


================================================================================
COMPLEXITY
================================================================================
    schedule        O(log n)
    cancel          O(1) (lazy)
    dispatch one    O(log n)
    n = scheduled jobs


================================================================================
EDGE CASES
================================================================================
  * delay=0 / run_at in the past -> due immediately.
  * Both at= and delay= given, every <= 0, negative delay -> ValueError.
  * Cancel a RUNNING recurring job -> current run finishes, no next slot.
  * Cancel a finished job -> False.
  * Clock jumps far ahead -> a recurring job runs once, next slot in the future.
  * Job raises BaseException subclasses like KeyboardInterrupt -> not swallowed.
  * shutdown(wait=True) lets running jobs finish; queued jobs stay SCHEDULED.


================================================================================
COMMON MISTAKES
================================================================================
  1. A thread per job with time.sleep(delay).
  2. Polling loop with a fixed sleep (latency floor + wasted wakeups).
  3. Holding the lock while running the job.
  4. One heap ordered by run_at claiming to support priority.
  5. Retrying immediately / without jitter / forever.
  6. Recurring job re-queued BEFORE it finishes -> overlapping runs.
  7. Catching up every missed slot after a pause (thundering backlog).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
  * Survive restarts -> jobs table (id, run_at, status, lease_until); workers
    claim with UPDATE ... WHERE status='SCHEDULED' AND run_at<=now (SKIP LOCKED).
  * Exactly-once? -> at-least-once + idempotent jobs; lease + heartbeat.
  * Cron expressions -> a NextRunCalculator strategy replacing `every`.
  * Timeouts -> run in a worker with a deadline; cooperative cancellation token.
  * Job dependencies (DAG) -> in-degree counts; release children on success.
  * Rate-limited queues -> token bucket before dispatch (lld/012).


================================================================================
RELATED
================================================================================
  SystemDesign/problems/012_workflow_scheduler (the distributed version)
  CSFundamentals/05_concurrency_deep_dive.md (condition variables)
  PyEngineering/12_worker_pool
  lld/012_rate_limiter · lld/002_elevator_system (discrete-time testing)
"""

from __future__ import annotations

import heapq
import itertools
import random
import statistics
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Hashable, Protocol

Clock = Callable[[], float]


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


# ----------------------------------------------------------------------------
# Retry policies
# ----------------------------------------------------------------------------
class RetryPolicy(Protocol):
    def delay(self, attempt: int) -> float | None: ...


class NoRetry:
    def delay(self, attempt):
        return None


class ExponentialBackoff:
    """delay = min(max_delay, base * factor^(attempt-1)), minus up to `jitter` fraction."""

    def __init__(self, base: float = 1.0, factor: float = 2.0, max_delay: float = 60.0,
                 max_attempts: int = 5, jitter: float = 0.0, rng: random.Random | None = None) -> None:
        if not 0 <= jitter <= 1:
            raise ValueError("jitter is a fraction in [0, 1]")
        self.base, self.factor, self.max_delay = base, factor, max_delay
        self.max_attempts, self.jitter = max_attempts, jitter
        self._rng = rng or random.Random()

    def delay(self, attempt):
        if attempt >= self.max_attempts:
            return None
        d = min(self.max_delay, self.base * self.factor ** (attempt - 1))
        return d * (1 - self.jitter * self._rng.random())


# ----------------------------------------------------------------------------
# Scheduler
# ----------------------------------------------------------------------------
@dataclass(slots=True, eq=False)
class _Job:
    id: int
    name: str
    fn: Callable[[], object]
    run_at: float
    every: float | None
    priority: int
    retry: RetryPolicy
    key: Hashable | None
    seq: int
    status: JobStatus = JobStatus.SCHEDULED
    attempts: int = 0
    runs: int = 0
    last_error: str | None = None

    def view(self) -> JobView:
        return JobView(self.id, self.name, self.status, self.attempts, self.run_at, self.last_error, self.runs)


_TERMINAL = (JobStatus.SUCCEEDED, JobStatus.DEAD, JobStatus.CANCELLED)


class Scheduler:
    def __init__(self, clock: Clock = time.monotonic, retry: RetryPolicy | None = None) -> None:
        self._clock = clock
        self._default_retry = retry or NoRetry()
        self._cond = threading.Condition()
        self._jobs: dict[int, _Job] = {}
        self._keys: dict[Hashable, int] = {}
        self._timers: list[tuple[float, int, int]] = []          # (run_at, seq, id)
        self._ready: list[tuple[int, float, int, int]] = []      # (-priority, run_at, seq, id)
        self._ids = itertools.count(1)
        self._seq = itertools.count()
        self._dead: list[int] = []
        # threaded mode
        self._running = False
        self._threads: list[threading.Thread] = []

    # -- public API ----------------------------------------------------------------
    def schedule(self, fn: Callable[[], object], *, delay: float | None = None, at: float | None = None,
                 every: float | None = None, priority: int = 0, name: str = "",
                 key: Hashable | None = None, retry: RetryPolicy | None = None) -> int:
        if delay is not None and at is not None:
            raise ValueError("give delay or at, not both")
        if (delay is not None and delay < 0) or (every is not None and every <= 0):
            raise ValueError("delay must be >= 0 and every > 0")
        with self._cond:
            if key is not None and key in self._keys:
                return self._keys[key]
            now = self._clock()
            run_at = at if at is not None else now + (delay or 0.0)
            job = _Job(next(self._ids), name or getattr(fn, "__name__", "job"), fn, run_at, every,
                       priority, retry or self._default_retry, key, next(self._seq))
            self._jobs[job.id] = job
            if key is not None:
                self._keys[key] = job.id
            self._push_timer(job)
            self._cond.notify_all()
            return job.id

    def cancel(self, job_id: int) -> bool:
        with self._cond:
            job = self._jobs.get(job_id)
            if job is None or job.status in _TERMINAL:
                return False
            job.status = JobStatus.CANCELLED                     # lazy: skipped when popped
            self._release_key(job)
            self._cond.notify_all()
            return True

    def status(self, job_id: int) -> JobView:
        with self._cond:
            return self._jobs[job_id].view()

    def dead_letters(self) -> list[JobView]:
        with self._cond:
            return [self._jobs[i].view() for i in self._dead]

    def next_due(self) -> float | None:
        with self._cond:
            self._drop_cancelled_timers()
            if self._ready:
                return self._ready[0][1]
            return self._timers[0][0] if self._timers else None

    # -- deterministic mode --------------------------------------------------------
    def run_pending(self) -> int:
        """Run every job that is due now, on the caller's thread. Returns jobs run."""
        ran = 0
        while True:
            with self._cond:
                job = self._take_ready(self._clock())
            if job is None:
                return ran
            self._execute(job)
            ran += 1

    # -- threaded mode -------------------------------------------------------------
    def start(self, workers: int = 4) -> None:
        with self._cond:
            if self._running:
                raise RuntimeError("already started")
            self._running = True
        self._threads = [threading.Thread(target=self._worker, name=f"sched-worker-{i}", daemon=True)
                         for i in range(workers)]
        for t in self._threads:
            t.start()

    def shutdown(self, wait: bool = True) -> None:
        with self._cond:
            self._running = False
            self._cond.notify_all()
        if wait:
            for t in self._threads:
                t.join()

    def _worker(self) -> None:
        while True:
            with self._cond:
                job = None
                while self._running:
                    job = self._take_ready(self._clock())
                    if job is not None:
                        break
                    timeout = None
                    if self._timers:
                        timeout = max(0.0, self._timers[0][0] - self._clock())
                    self._cond.wait(timeout)
                if job is None:
                    return
            self._execute(job)

    # -- internals -------------------------------------------------------------------
    def _push_timer(self, job: _Job) -> None:
        heapq.heappush(self._timers, (job.run_at, job.seq, job.id))

    def _drop_cancelled_timers(self) -> None:
        while self._timers and self._jobs[self._timers[0][2]].status is JobStatus.CANCELLED:
            heapq.heappop(self._timers)

    def _take_ready(self, now: float) -> _Job | None:
        while self._timers and self._timers[0][0] <= now:
            run_at, seq, jid = heapq.heappop(self._timers)
            job = self._jobs[jid]
            if job.status is JobStatus.SCHEDULED:
                heapq.heappush(self._ready, (-job.priority, run_at, seq, jid))
        while self._ready:
            *_, jid = heapq.heappop(self._ready)
            job = self._jobs[jid]
            if job.status is JobStatus.SCHEDULED:
                job.status = JobStatus.RUNNING
                return job
        return None

    def _execute(self, job: _Job) -> None:
        error: str | None = None
        try:
            job.fn()
        except Exception as e:                                   # BaseException propagates
            error = f"{type(e).__name__}: {e}"
        with self._cond:
            self._finish(job, error)
            self._cond.notify_all()

    def _finish(self, job: _Job, error: str | None) -> None:
        now = self._clock()
        job.runs += 1
        job.last_error = error
        if job.status is JobStatus.CANCELLED:                    # cancelled while running
            return
        if job.every is not None:
            next_slot = job.run_at + job.every
            if next_slot <= now:                                 # skip missed slots
                missed = int((now - next_slot) // job.every) + 1
                next_slot += missed * job.every
            job.run_at, job.status, job.seq = next_slot, JobStatus.SCHEDULED, next(self._seq)
            self._push_timer(job)
            return
        if error is None:
            job.status = JobStatus.SUCCEEDED
            self._release_key(job)
            return
        job.attempts += 1
        delay = job.retry.delay(job.attempts)
        if delay is None:
            job.status = JobStatus.DEAD
            self._dead.append(job.id)
            self._release_key(job)
        else:
            job.run_at, job.status, job.seq = now + delay, JobStatus.SCHEDULED, next(self._seq)
            self._push_timer(job)

    def _release_key(self, job: _Job) -> None:
        if job.key is not None and self._keys.get(job.key) == job.id:
            del self._keys[job.key]


# ===================================================================== TESTS ==
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


class PollingScheduler:
    """The anti-pattern: wake every `interval` and look for due jobs."""

    def __init__(self, interval: float) -> None:
        self.interval = interval
        self.jobs: list[tuple[float, Callable]] = []
        self.lock = threading.Lock()
        self.stop = False

    def schedule(self, fn, delay):
        with self.lock:
            self.jobs.append((time.monotonic() + delay, fn))

    def loop(self):
        while not self.stop:
            now = time.monotonic()
            with self.lock:
                due = [j for j in self.jobs if j[0] <= now]
                self.jobs = [j for j in self.jobs if j[0] > now]
            for _, fn in due:
                fn()
            time.sleep(self.interval)


def run_demos() -> bool:
    all_ok = True
    print("\n--- DEMO 1: lateness of 300 jobs due within 0.4 s ---")
    rng = random.Random(1)
    delays = [rng.uniform(0.0, 0.4) for _ in range(300)]

    def measure(kind: str) -> list[float]:
        lateness: list[float] = []
        counts: dict[int, int] = {}
        guard = threading.Lock()

        def make(i: int, due: float):
            def job():
                with guard:
                    lateness.append((time.monotonic() - due) * 1000)
                    counts[i] = counts.get(i, 0) + 1
            return job

        if kind == "condition":
            s = Scheduler()
            s.start(workers=8)
            base = time.monotonic()
            for i, d in enumerate(delays):
                s.schedule(make(i, base + d), at=base + d)
            time.sleep(0.6)
            s.shutdown()
        else:
            p = PollingScheduler(0.05)
            t = threading.Thread(target=p.loop)
            t.start()
            base = time.monotonic()
            for i, d in enumerate(delays):
                p.schedule(make(i, base + d), d)
            time.sleep(0.6)
            p.stop = True
            t.join()
        assert sorted(counts) == list(range(300)) and set(counts.values()) == {1}
        return sorted(lateness)

    cond = measure("condition")
    poll = measure("polling")
    p50 = lambda xs: statistics.median(xs)
    p99 = lambda xs: xs[int(len(xs) * 0.99) - 1]
    print(f"      condition-wait : p50 {p50(cond):5.1f} ms   p99 {p99(cond):5.1f} ms")
    print(f"      50 ms polling  : p50 {p50(poll):5.1f} ms   p99 {p99(poll):5.1f} ms")
    all_ok &= _check("every job ran exactly once in both; condition wait is far less late",
                     p50(cond) * 5 < p50(poll))

    print("\n--- DEMO 2: 1,000 clients fail at t=0 and retry (base 1 s, x2, 4 attempts) ---")
    for label, jitter in (("no jitter", 0.0), ("full jitter", 1.0)):
        rng = random.Random(2)
        buckets: dict[int, int] = {}
        for _ in range(1000):
            policy = ExponentialBackoff(base=1, factor=2, max_attempts=5, jitter=jitter, rng=rng)
            t = 0.0
            for attempt in range(1, 5):
                t += policy.delay(attempt)
                b = int(t * 10)                         # 100 ms buckets
                buckets[b] = buckets.get(b, 0) + 1
        peak = max(buckets.values())
        print(f"      {label:<11}: busiest 100 ms window receives {peak} retries")
        if jitter:
            jitter_peak = peak
        else:
            flat_peak = peak
    all_ok &= _check("jitter flattens the synchronized retry spikes", jitter_peak * 5 < flat_peak)

    print("\n--- DEMO 3: a 50 ms recurring job scheduled every 20 ms, 4 workers ---")
    s = Scheduler()
    active = [0]
    peak = [0]
    runs = [0]
    guard = threading.Lock()

    def slow_job():
        with guard:
            active[0] += 1
            peak[0] = max(peak[0], active[0])
        time.sleep(0.05)
        with guard:
            active[0] -= 1
            runs[0] += 1

    s.start(workers=4)
    s.schedule(slow_job, every=0.02)
    time.sleep(0.4)
    s.shutdown()
    print(f"      runs: {runs[0]}, max concurrent executions of the job: {peak[0]}")
    all_ok &= _check("recurring job never overlaps itself, and missed slots don't pile up",
                     peak[0] == 1 and 4 <= runs[0] <= 9)
    return all_ok


if __name__ == "__main__":
    ok = run_tests()
    ok &= run_demos()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
