"""
================================================================================
LLD 012 · Rate Limiter Library                                     [Tier 1]
Time box: 45 minutes (5 clarify · 7 model · 5 API · 20 code · 8 extend)
================================================================================

PROBLEM
-------
Design and implement an in-process rate-limiting library that API handlers
can use per user, per IP, or per API key.

The interviewer says: "Design a rate limiter — as a library, not the whole
distributed system." These are the agreed requirements.

REQUIREMENTS
------------
  1. RateLimiter(algorithm, clock=time.monotonic, max_keys=100_000)
       allow(key, cost=1) -> Decision(allowed, remaining, retry_after_s)
     cost must be a positive int, else ValueError. Denied requests consume
     nothing. tracked_keys() -> number of keys with state; it must never
     exceed max_keys (drop least recently used keys).
  2. Algorithms (the clock value `now` is in seconds):
       TokenBucket(capacity, refill_per_s)
           starts full; refills continuously; tokens capped at capacity;
           a clock that goes backwards adds no tokens and removes none.
           remaining = int(tokens left); retry_after = (cost - tokens)/rate.
       FixedWindow(limit, window_s)
           windows are [k*W, (k+1)*W); retry_after = start of next window - now.
       SlidingWindowLog(limit, window_s)
           exact: a request at time t counts while now < t + W.
           retry_after = when enough old entries have expired for this cost.
       SlidingWindowCounter(limit, window_s)
           estimate = prev_window_count * (1 - fraction_of_current_window_elapsed)
                      + current_window_count;  allowed if estimate + cost <= limit.
     Any algorithm: cost > limit/capacity -> denied with retry_after = inf.
  3. Keys are independent.
  4. CompositeLimiter([limiter, ...]).allow(key, cost): allowed only if EVERY
     limiter allows; if any denies, NONE of them consume. retry_after = the
     largest among the denials; remaining = the smallest.
  5. @rate_limited(limiter, key=lambda *args, **kw: "global", cost=1) wraps a
     function; when denied it raises RateLimited(retry_after_s) without
     calling the function.
  6. Thread-safe: concurrent allow() on one key never over-admits.

WHAT THE INTERVIEWER IS LOOKING FOR
-----------------------------------
  * Trade-offs of the four algorithms (burstiness, accuracy, memory).
  * The fixed-window boundary problem.
  * Why inject the clock?
  * Where is the race and what's the lock granularity?
  * How to combine "10/second and 1000/day" correctly.
  * How it changes across 50 servers.

FOLLOW-UPS TO PREPARE
---------------------
  distributed (Redis + Lua) · per-tier limits · queue instead of reject ·
  adaptive limits · concurrency limits · rate-limit headers.

THE API BELOW IS FIXED so the tests at the bottom can run against your code.
Run this file: all checks should print PASS, then ALL PASSED.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Callable, Hashable


@dataclass(frozen=True, slots=True)
class Decision:
    allowed: bool
    remaining: int
    retry_after_s: float


class RateLimited(Exception):
    def __init__(self, retry_after_s: float) -> None:
        super().__init__(f"rate limited; retry after {retry_after_s:.3f}s")
        self.retry_after_s = retry_after_s


class TokenBucket:
    def __init__(self, capacity: int, refill_per_s: float) -> None:
        raise NotImplementedError


class FixedWindow:
    def __init__(self, limit: int, window_s: float) -> None:
        raise NotImplementedError


class SlidingWindowLog:
    def __init__(self, limit: int, window_s: float) -> None:
        raise NotImplementedError


class SlidingWindowCounter:
    def __init__(self, limit: int, window_s: float) -> None:
        raise NotImplementedError


class RateLimiter:
    def __init__(self, algorithm, clock: Callable[[], float] = time.monotonic,
                 max_keys: int = 100_000) -> None:
        # YOUR CODE HERE
        raise NotImplementedError

    def allow(self, key: Hashable, cost: int = 1) -> Decision:
        raise NotImplementedError

    def tracked_keys(self) -> int:
        raise NotImplementedError


class CompositeLimiter:
    def __init__(self, limiters: list[RateLimiter]) -> None:
        raise NotImplementedError

    def allow(self, key: Hashable, cost: int = 1) -> Decision:
        raise NotImplementedError


def rate_limited(limiter, key: Callable[..., Hashable] = lambda *a, **k: "global", cost: int = 1):
    raise NotImplementedError


# ===================================================================== TESTS ==
# Identical to the solution file's tests. Make them all PASS.
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


if __name__ == "__main__":
    ok = run_tests()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
