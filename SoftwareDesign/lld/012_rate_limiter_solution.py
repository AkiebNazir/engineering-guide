"""
================================================================================
SOLUTION · LLD 012 · Rate Limiter Library                          [Tier 1]
================================================================================

THE CORE IDEA
--------------
A rate limiter library is "per-key state + an algorithm + a clock". Keep the
algorithm a STRATEGY so the rest (key storage, locking, eviction of idle keys,
decorators, composition) is written once:

    Algorithm              state per key          accuracy / cost
    FixedWindow            (window id, count)     2x burst at window edges (demo 1)
    SlidingWindowLog       deque of timestamps    exact; O(limit) memory per key (demo 2)
    SlidingWindowCounter   (window id, prev, cur) approximate; O(1) memory
    TokenBucket            (tokens, last refill)  allows bursts up to capacity,
                                                  smooth long-run rate; O(1)

Every algorithm implements two methods:
    check(state, now, cost) -> Decision   (may lazily refill/expire, never admits)
    consume(state, now, cost)             (called only if check allowed)
Splitting them lets a CompositeLimiter ("10/second AND 1000/day") admit a
request only if EVERY rule allows it, without burning quota in the first rule
when the second rejects.

Library-quality details interviewers look for:
    * INJECTED CLOCK -> every test below runs instantly and deterministically.
    * Decision carries remaining and retry_after (-> HTTP 429 Retry-After header).
    * The check-and-consume is atomic per key (lock striping: 16 locks, not one
      global lock and not one lock object per key). Demo 3 shows over-admission
      without it.
    * Idle keys are evicted (LRU cap) so a key-spraying client can't exhaust memory.
    * Cost > capacity can never succeed -> retry_after = inf, not a busy loop.


================================================================================
REQUIREMENTS (agreed in the first 5 minutes)
================================================================================
  1. RateLimiter(algorithm, clock).allow(key, cost=1) -> Decision.
  2. Algorithms: token bucket, fixed window, sliding log, sliding counter.
  3. Decision(allowed, remaining, retry_after_s).
  4. Thread-safe; many keys; bounded memory.
  5. Compose several limits on the same key.
  6. A decorator for functions.
  Out of scope: distributed limiting (follow-up), config reloading.


================================================================================
ENTITIES AND INVARIANTS
================================================================================
    Decision             value object
    Algorithm            new_state(now) / check / consume
       INVARIANT: in ANY window of length W, admitted cost <= limit
                  (exact for SlidingWindowLog; FixedWindow only per aligned window;
                   TokenBucket: <= capacity + rate * W)
    RateLimiter          stripes: [(lock, OrderedDict key -> state)]
       INVARIANT: at most max_keys states retained (LRU eviction)
    CompositeLimiter     all-or-nothing across limiters (locks in a fixed order)
    RateLimited          exception raised by the decorator


================================================================================
TOKEN BUCKET TRACE · capacity 5, refill 1 token/s
================================================================================
    t     tokens before   request   tokens after   decision
    0.0   5.0             cost 5    0.0            allowed, remaining 0
    0.5   0.5             cost 1    0.5            denied, retry_after 0.5
    1.0   1.0             cost 1    0.0            allowed
    10.0  5.0 (capped)    cost 6    5.0            denied, retry_after inf (> capacity)


================================================================================
DESIGN DECISIONS AND ALTERNATIVES
================================================================================
  * Lazy refill (compute tokens from elapsed time on each call) — no timer
    thread per bucket.
  * Clock going backwards (NTP) -> elapsed clamped to 0; never negative tokens.
  * Lock striping: hash(key) % 16 picks a lock. Two hot keys rarely contend;
    memory is 16 locks regardless of key count.
  * Composite acquires stripe locks in limiter order (a fixed global order), so
    two composites can never deadlock.
  * Denied requests don't consume (the common choice). Some APIs charge denied
    calls too — a policy flag if asked.
  * Distributed version: same algorithms in Redis via a Lua script (atomic
    read-modify-write) or a GCRA single-timestamp variant; accept slight
    over-admission across regions, or route each key to one limiter shard.


================================================================================
COMPLEXITY (per allow)
================================================================================
    TokenBucket, FixedWindow, SlidingWindowCounter   O(1) time, O(1) memory/key
    SlidingWindowLog                                 O(expired) amortised O(1),
                                                     O(limit) memory/key


================================================================================
EDGE CASES
================================================================================
  * cost <= 0 -> ValueError.  cost > limit/capacity -> denied, retry inf.
  * First request for a new key starts with a full bucket / empty window.
  * Requests exactly at the window boundary belong to the NEW window.
  * Sliding log: a timestamp exactly W old has expired (half-open window).
  * Clock steps backwards.
  * max_keys reached -> least recently used key's state dropped (it simply
    starts fresh next time — fail-open for that key, documented).


================================================================================
COMMON MISTAKES
================================================================================
  1. time.time() called inside the algorithm — untestable, and wall-clock jumps.
  2. Fixed window presented as "the" solution without the boundary burst.
  3. check-then-increment without a lock (over-admission, demo 3).
  4. One global lock (all keys serialise) or a dict of per-key locks that
     grows forever.
  5. Composite limits that consume from rule 1 before rule 2 rejects.
  6. A background thread refilling every bucket every second.
  7. Unbounded per-key state.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
  * Distributed across 50 API servers -> central Redis with Lua, or local
    limiters with limit/N each plus periodic rebalancing; discuss accuracy.
  * Different limits per customer tier -> key_fn + limit lookup per key.
  * Queue instead of reject (leaky bucket as a meter) -> delay = retry_after.
  * Adaptive limiting -> reduce limits when downstream latency rises (AIMD).
  * Concurrency limit (max in-flight) -> semaphore per key, not a rate.
  * Headers -> X-RateLimit-Limit / Remaining / Reset, Retry-After.


================================================================================
RELATED
================================================================================
  SystemDesign building blocks: rate limiting at scale (API gateway)
  SoftwareDesign/04_design_patterns_in_practice.md  §3 Strategy, §10 Decorator
  lld/009_lru_lfu_cache (bounded per-key state, lock striping follow-up)
"""

from __future__ import annotations

import functools
import math
import random
import sys
import threading
import time
from collections import OrderedDict, deque
from dataclasses import dataclass
from typing import Callable, Hashable, Protocol

Clock = Callable[[], float]


@dataclass(frozen=True, slots=True)
class Decision:
    allowed: bool
    remaining: int
    retry_after_s: float


class RateLimited(Exception):
    def __init__(self, retry_after_s: float) -> None:
        super().__init__(f"rate limited; retry after {retry_after_s:.3f}s")
        self.retry_after_s = retry_after_s


# ----------------------------------------------------------------------------
# Algorithms (strategies). State objects are plain lists for speed.
# ----------------------------------------------------------------------------
class Algorithm(Protocol):
    def new_state(self, now: float) -> object: ...
    def check(self, state, now: float, cost: int) -> Decision: ...
    def consume(self, state, now: float, cost: int) -> None: ...


class TokenBucket:
    def __init__(self, capacity: int, refill_per_s: float) -> None:
        if capacity < 1 or refill_per_s <= 0:
            raise ValueError("capacity >= 1 and refill_per_s > 0 required")
        self.capacity, self.rate = capacity, refill_per_s

    def new_state(self, now):
        return [float(self.capacity), now]

    def check(self, state, now, cost):
        elapsed = max(0.0, now - state[1])
        state[0] = min(self.capacity, state[0] + elapsed * self.rate)
        state[1] = max(state[1], now)
        tokens = state[0]
        if cost > self.capacity:
            return Decision(False, int(tokens), math.inf)
        if tokens >= cost:
            return Decision(True, int(tokens - cost), 0.0)
        return Decision(False, int(tokens), (cost - tokens) / self.rate)

    def consume(self, state, now, cost):
        state[0] -= cost


class FixedWindow:
    def __init__(self, limit: int, window_s: float) -> None:
        if limit < 1 or window_s <= 0:
            raise ValueError("limit >= 1 and window_s > 0 required")
        self.limit, self.window = limit, window_s

    def new_state(self, now):
        return [math.floor(now / self.window), 0]

    def check(self, state, now, cost):
        idx = math.floor(now / self.window)
        if idx > state[0]:
            state[0], state[1] = idx, 0
        if cost > self.limit:
            return Decision(False, self.limit - state[1], math.inf)
        if state[1] + cost <= self.limit:
            return Decision(True, self.limit - state[1] - cost, 0.0)
        return Decision(False, self.limit - state[1], (state[0] + 1) * self.window - now)

    def consume(self, state, now, cost):
        state[1] += cost


class SlidingWindowLog:
    def __init__(self, limit: int, window_s: float) -> None:
        if limit < 1 or window_s <= 0:
            raise ValueError("limit >= 1 and window_s > 0 required")
        self.limit, self.window = limit, window_s

    def new_state(self, now):
        return deque()

    def check(self, log, now, cost):
        while log and log[0] <= now - self.window:
            log.popleft()
        if cost > self.limit:
            return Decision(False, self.limit - len(log), math.inf)
        if len(log) + cost <= self.limit:
            return Decision(True, self.limit - len(log) - cost, 0.0)
        must_expire = len(log) + cost - self.limit           # this many oldest entries
        return Decision(False, self.limit - len(log), log[must_expire - 1] + self.window - now)

    def consume(self, log, now, cost):
        log.extend([now] * cost)


class SlidingWindowCounter:
    """Weighted previous window + current window: O(1) memory approximation."""

    def __init__(self, limit: int, window_s: float) -> None:
        if limit < 1 or window_s <= 0:
            raise ValueError("limit >= 1 and window_s > 0 required")
        self.limit, self.window = limit, window_s

    def new_state(self, now):
        return [math.floor(now / self.window), 0, 0]           # idx, prev, cur

    def _estimate(self, state, now) -> float:
        idx = math.floor(now / self.window)
        if idx == state[0] + 1:
            state[0], state[1], state[2] = idx, state[2], 0
        elif idx > state[0] + 1:
            state[0], state[1], state[2] = idx, 0, 0
        into = (now - state[0] * self.window) / self.window
        return state[1] * (1 - into) + state[2]

    def check(self, state, now, cost):
        used = self._estimate(state, now)
        if cost > self.limit:
            return Decision(False, max(0, int(self.limit - used)), math.inf)
        if used + cost <= self.limit:
            return Decision(True, max(0, int(self.limit - used - cost)), 0.0)
        return Decision(False, max(0, int(self.limit - used)), (state[0] + 1) * self.window - now)

    def consume(self, state, now, cost):
        state[2] += cost


# ----------------------------------------------------------------------------
# RateLimiter — per-key state, lock striping, bounded memory
# ----------------------------------------------------------------------------
class RateLimiter:
    STRIPES = 16

    def __init__(self, algorithm: Algorithm, clock: Clock = time.monotonic,
                 max_keys: int = 100_000) -> None:
        self.algorithm = algorithm
        self.clock = clock
        self._per_stripe = max(1, max_keys // self.STRIPES)
        self._locks = [threading.Lock() for _ in range(self.STRIPES)]
        self._states: list[OrderedDict] = [OrderedDict() for _ in range(self.STRIPES)]

    def allow(self, key: Hashable, cost: int = 1) -> Decision:
        _validate(cost)
        i = hash(key) % self.STRIPES
        with self._locks[i]:
            now = self.clock()
            state = self._state(i, key, now)
            decision = self.algorithm.check(state, now, cost)
            if decision.allowed:
                self.algorithm.consume(state, now, cost)
            return decision

    def tracked_keys(self) -> int:
        return sum(len(s) for s in self._states)

    # used by CompositeLimiter
    def _stripe(self, key: Hashable) -> int:
        return hash(key) % self.STRIPES

    def _state(self, stripe: int, key: Hashable, now: float):
        states = self._states[stripe]
        state = states.get(key)
        if state is None:
            state = states[key] = self.algorithm.new_state(now)
            if len(states) > self._per_stripe:
                states.popitem(last=False)                     # evict least recently used key
        else:
            states.move_to_end(key)
        return state


class CompositeLimiter:
    """Admit only if every limiter allows; consume from all or none."""

    def __init__(self, limiters: list[RateLimiter]) -> None:
        if not limiters:
            raise ValueError("need at least one limiter")
        self._limiters = list(limiters)

    def allow(self, key: Hashable, cost: int = 1) -> Decision:
        _validate(cost)
        stripes = [lim._stripe(key) for lim in self._limiters]
        locks = [lim._locks[s] for lim, s in zip(self._limiters, stripes)]
        for lock in locks:                                    # fixed order: limiter list order
            lock.acquire()
        try:
            checks = []
            for lim, s in zip(self._limiters, stripes):
                now = lim.clock()
                state = lim._state(s, key, now)
                checks.append((lim, state, now, lim.algorithm.check(state, now, cost)))
            allowed = all(d.allowed for *_, d in checks)
            if allowed:
                for lim, state, now, _ in checks:
                    lim.algorithm.consume(state, now, cost)
            return Decision(allowed,
                            min(d.remaining for *_, d in checks),
                            0.0 if allowed else max(d.retry_after_s for *_, d in checks if not d.allowed))
        finally:
            for lock in reversed(locks):
                lock.release()


def rate_limited(limiter: RateLimiter | CompositeLimiter,
                 key: Callable[..., Hashable] = lambda *a, **k: "global",
                 cost: int = 1):
    """Decorator: raise RateLimited instead of calling the function when denied."""
    def wrap(fn):
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            decision = limiter.allow(key(*args, **kwargs), cost)
            if not decision.allowed:
                raise RateLimited(decision.retry_after_s)
            return fn(*args, **kwargs)
        return inner
    return wrap


def _validate(cost: int) -> None:
    if not isinstance(cost, int) or cost <= 0:
        raise ValueError("cost must be a positive int")


# ===================================================================== TESTS ==
class FakeClock:
    def __init__(self, t: float = 0.0) -> None:
        self.t = t

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
    print("--- token bucket (the docstring trace) ---")
    clock = FakeClock()
    tb = RateLimiter(TokenBucket(5, 1.0), clock)
    d0 = tb.allow("u", 5)
    clock.t = 0.5
    d1 = tb.allow("u")
    clock.t = 1.0
    d2 = tb.allow("u")
    clock.t = 10.0
    d3 = tb.allow("u", 6)
    all_ok &= _check("t=0 cost 5 allowed, remaining 0", d0 == Decision(True, 0, 0.0))
    all_ok &= _check("t=0.5 denied, retry after 0.5 s", not d1.allowed and abs(d1.retry_after_s - 0.5) < 1e-9)
    all_ok &= _check("t=1.0 allowed after refill", d2.allowed)
    all_ok &= _check("cost above capacity -> retry_after inf", not d3.allowed and d3.retry_after_s == math.inf)
    all_ok &= _check("keys are independent", tb.allow("other", 5).allowed)
    clock.t = 5.0
    all_ok &= _check("clock going backwards never yields negative tokens",
                     tb.allow("u", 5).allowed and not tb.allow("u").allowed)

    print("\n--- fixed window ---")
    clock = FakeClock()
    fw = RateLimiter(FixedWindow(3, 10), clock)
    results = [fw.allow("u").allowed for _ in range(4)]
    clock.t = 9.0
    denied = fw.allow("u")
    clock.t = 10.0
    all_ok &= _check("3 allowed then denied", results == [True, True, True, False])
    all_ok &= _check("retry_after = time to the next window", abs(denied.retry_after_s - 1.0) < 1e-9)
    all_ok &= _check("request exactly at the boundary belongs to the new window", fw.allow("u").allowed)

    print("\n--- sliding window log ---")
    clock = FakeClock()
    sl = RateLimiter(SlidingWindowLog(3, 10), clock)
    for t in (0, 2, 4):
        clock.t = t
        sl.allow("u")
    clock.t = 9
    d = sl.allow("u")
    all_ok &= _check("4th request at t=9 denied; retry when t=0 entry expires (1 s)",
                     not d.allowed and abs(d.retry_after_s - 1.0) < 1e-9)
    clock.t = 10
    all_ok &= _check("entry exactly W old has expired -> allowed at t=10", sl.allow("u").allowed)
    clock.t = 10
    d = sl.allow("u", 2)
    all_ok &= _check("cost 2 needs two expiries: t=2 and t=4 -> retry after 4 s",
                     not d.allowed and abs(d.retry_after_s - 4.0) < 1e-9)

    print("\n--- sliding window counter ---")
    clock = FakeClock()
    sc = RateLimiter(SlidingWindowCounter(10, 10), clock)
    for _ in range(10):
        sc.allow("u")
    clock.t = 15.0                                 # halfway: previous window weighs 50%
    allowed = sum(sc.allow("u").allowed for _ in range(10))
    all_ok &= _check("halfway into the next window ~5 more requests fit", allowed == 5)

    print("\n--- composite, decorator, validation, memory bound ---")
    clock = FakeClock()
    per_sec = RateLimiter(TokenBucket(2, 2.0), clock)
    per_min = RateLimiter(FixedWindow(3, 60), clock)
    both = CompositeLimiter([per_sec, per_min])
    first = [both.allow("u").allowed for _ in range(3)]
    all_ok &= _check("2/s AND 3/min: third call at t=0 denied by the per-second rule", first == [True, True, False])
    clock.t = 1.0
    all_ok &= _check("t=1: third allowed; per-minute rule now exhausted",
                     both.allow("u").allowed and not both.allow("u").allowed)
    all_ok &= _check("denied composite call did NOT burn per-second tokens",
                     per_sec.allow("u").allowed)

    calls = []

    @rate_limited(RateLimiter(FixedWindow(2, 1), FakeClock()), key=lambda user: user)
    def fetch(user):
        calls.append(user)
        return "ok"

    fetch("ann"); fetch("ann")
    all_ok &= _check("decorator raises RateLimited and skips the call",
                     _raises(RateLimited, lambda: fetch("ann")) and fetch("bob") == "ok" and len(calls) == 3)
    all_ok &= _check("cost must be positive", _raises(ValueError, lambda: tb.allow("u", 0)))
    small = RateLimiter(TokenBucket(1, 1), FakeClock(), max_keys=32)
    for i in range(10_000):
        small.allow(f"spray-{i}")
    all_ok &= _check("key spraying can't grow state beyond max_keys", small.tracked_keys() <= 32)
    return all_ok
# ================================================================= END TESTS ==


class UnlockedTokenBucket:
    """GET tokens, then SET tokens - 1: the sleep(0) stands in for the round trip
    between two separate cache commands (e.g. Redis GET then SET without Lua)."""

    def __init__(self, capacity: int) -> None:
        self.tokens = capacity

    def allow(self) -> bool:
        tokens = self.tokens
        time.sleep(0)
        if tokens >= 1:
            self.tokens = tokens - 1
            return True
        return False


def run_demos() -> bool:
    all_ok = True
    print("\n--- DEMO 1: limit 100/min; a client sends 100 at t=59.9 and 100 at t=60.1 ---")
    admitted = {}
    for name, algo in (("fixed window", FixedWindow(100, 60)), ("sliding log", SlidingWindowLog(100, 60)),
                       ("sliding counter", SlidingWindowCounter(100, 60)), ("token bucket", TokenBucket(100, 100 / 60))):
        clock = FakeClock()
        lim = RateLimiter(algo, clock)
        n = 0
        for t in (59.9, 60.1):
            clock.t = t
            n += sum(lim.allow("c").allowed for _ in range(100))
        admitted[name] = n
        print(f"      {name:<16}: {n} requests admitted within 0.2 s")
    all_ok &= _check("fixed window doubles the burst at the edge; sliding log holds the limit",
                     admitted["fixed window"] == 200 and admitted["sliding log"] == 100)

    print("\n--- DEMO 2: memory per key at limit 10,000/hour after a busy hour ---")
    clock = FakeClock()
    log_lim = RateLimiter(SlidingWindowLog(10_000, 3600), clock)
    ctr_lim = RateLimiter(SlidingWindowCounter(10_000, 3600), clock)
    for i in range(10_000):
        clock.t = i * 0.3
        log_lim.allow("k")
        ctr_lim.allow("k")
    log_items = len(log_lim._states[log_lim._stripe("k")]["k"])
    ctr_items = len(ctr_lim._states[ctr_lim._stripe("k")]["k"])
    print(f"      sliding log stores {log_items} timestamps; sliding counter stores {ctr_items} numbers")
    all_ok &= _check("log memory grows with the limit, counter is constant", log_items == 10_000 and ctr_items == 3)

    print("\n--- DEMO 3: 16 threads race for a 5,000-token bucket (no refill) ---")
    old = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    try:
        for name, make_allow in (
            ("unlocked", lambda: UnlockedTokenBucket(5000).allow),
            ("RateLimiter", lambda: (lambda lim: (lambda: lim.allow("k").allowed))(
                RateLimiter(TokenBucket(5000, 1e-9), FakeClock()))),
        ):
            allow = make_allow()
            count = [0]
            guard = threading.Lock()

            def worker() -> None:
                local = 0
                for _ in range(1000):
                    if allow():
                        local += 1
                with guard:
                    count[0] += local

            ts = [threading.Thread(target=worker) for _ in range(16)]
            for t in ts:
                t.start()
            for t in ts:
                t.join()
            print(f"      {name:<12}: admitted {count[0]} (capacity 5000)")
            if name == "unlocked":
                unlocked = count[0]
            else:
                locked = count[0]
    finally:
        sys.setswitchinterval(old)
    all_ok &= _check("atomic check-and-consume admits exactly capacity", locked == 5000)
    all_ok &= _check("unlocked version over-admits", unlocked > 5000)

    print("\n--- DEMO 4: sliding counter accuracy on bursty random traffic ---")
    rng = random.Random(12)
    clock = FakeClock()
    exact = RateLimiter(SlidingWindowLog(50, 10), clock)
    approx = RateLimiter(SlidingWindowCounter(50, 10), clock)
    worst = 0
    admitted_times: list[float] = []
    t = 0.0
    for _ in range(50_000):
        t += rng.expovariate(8.0)
        clock.t = t
        exact.allow("k")
        if approx.allow("k").allowed:
            admitted_times.append(t)
    j = 0
    for i, ti in enumerate(admitted_times):          # max admitted in any true 10 s window
        while admitted_times[j] <= ti - 10:
            j += 1
        worst = max(worst, i - j + 1)
    print(f"      worst true 10 s window under the counter: {worst} admitted (limit 50)")
    all_ok &= _check("counter's over-admission is bounded (< 2x limit)", 50 <= worst < 100)
    return all_ok


if __name__ == "__main__":
    ok = run_tests()
    ok &= run_demos()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
