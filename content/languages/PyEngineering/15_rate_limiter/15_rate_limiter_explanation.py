"""
15 — Rate Limiter
==================

WHAT
----
A hand-rolled, per-key **token-bucket** rate limiter for an `asyncio`
service -- the algorithm behind most API quotas you will integrate against
(AWS API throttling, Stripe and GitHub document token-bucket-shaped limits)
or build yourself -- plus a deliberately naive **fixed-window** counter to
show the bug token buckets exist to avoid.

    - `KeyedRateLimiter.allow(key, n=1)`: non-blocking "may I, right now?"
      (the shape an HTTP middleware needs to answer with 429).
    - `await KeyedRateLimiter.wait(key, n=1)`: block until the tokens are
      yours, cancellable with `asyncio.timeout(...)` or task cancellation
      (the shape a client needs to *respect* someone else's limit).
    - `retry_after(key, n=1)`: seconds until `n` tokens will be available,
      for a `Retry-After` header computed from the same state `allow` uses.
    - Idle-bucket eviction so memory doesn't grow with every key ever seen.

WHY THIS MATTERS
-----------------
Rate limiting shows up at every layer of a backend:

    - Protecting a dependency from your own retry storms (see problem 03).
    - Per-tenant / per-API-key quotas so one noisy customer can't starve
      everyone sharing the service.
    - Client side: pacing calls to a third-party API instead of discovering
      its limit through 429s and backoff.

Two design questions dominate:

    1. **Algorithm.** A fixed window ("100 requests per minute, counter
       resets on the minute") is trivial but lets through 2x the limit
       around a boundary: 100 requests at 0:59.9 and 100 more at 1:00.0.
       A token bucket refills continuously at `rate` tokens/second up to a
       capacity of `burst`, so there is no boundary to exploit, and short
       legitimate spikes up to `burst` are absorbed. `burst` is therefore a
       real design parameter: it is the largest spike you allow, not a
       detail of the steady-state rate.
    2. **Per-key state.** One global bucket lets one client eat everyone's
       budget. One bucket per key is fair but makes memory proportional to
       the number of distinct keys (IPs, API keys) seen -- unbounded for a
       long-running service unless idle buckets are evicted.

THE CORE TRICKS
----------------
    - **Lazy refill.** Never run a timer per bucket. Store `tokens` and the
      time of the last update; when the bucket is touched, add
      `elapsed * rate` (capped at `burst`). Work happens only for buckets in
      use, so 1 million idle keys cost memory but zero CPU.
    - **Fractional tokens.** Keep `tokens` a float. Truncating to int on each
      refill silently lowers the effective rate (a caller arriving every
      0.9 token-intervals would never get a token).
    - **Reservation-style wait.** `wait` takes the tokens *immediately*, even
      if that drives the balance negative (a debt), then sleeps exactly
      `debt / rate` seconds. Waiters are served in arrival order with one
      sleep each -- no polling loop, no thundering herd of re-checks. If
      the wait is cancelled, the tokens are given back. This is how Go's
      `golang.org/x/time/rate` implements `Wait` (`Reserve` + `Cancel`).
    - **Atomicity for free in asyncio.** `allow` contains no `await`, so no
      other coroutine can run between "refill" and "consume": the event
      loop only switches tasks at `await` points. No lock is needed. (From
      multiple *threads* that is no longer true -- see Pitfalls.)
    - **Lossless eviction.** A bucket that has been idle long enough to
      refill completely is indistinguishable from a brand-new bucket, so
      evicting it changes no decision. Evicting a bucket that is still in
      debt would hand a fresh full burst to the very client being limited.

CONCEPTS EXERCISED
-------------------
    - Token-bucket arithmetic with an injectable monotonic clock
      (`time.monotonic`, never `time.time`, which jumps with NTP/DST).
    - Non-blocking vs blocking acquisition APIs.
    - `asyncio` cancellation: `CancelledError` must be re-raised after
      cleanup, never swallowed.
    - Why code between two `await`s is atomic with respect to other tasks.
    - Bounded per-key state and amortised sweeping without a background task.
    - The fixed-window boundary burst, demonstrated by a test.

SPEC
----
    class KeyedRateLimiter:
        def __init__(self, rate: float, burst: int, *, idle_ttl: float = 60.0,
                     clock: Callable[[], float] = time.monotonic) -> None:
            "rate > 0 tokens/second, burst >= 1, idle_ttl > 0 seconds;
             otherwise ValueError. `clock` is injectable for tests."

        def allow(self, key: Hashable, n: int = 1) -> bool:
            "All-or-nothing: consume n tokens if available and return True,
             else consume nothing and return False. A fresh key starts full.
             n < 1 -> ValueError; n > burst -> always False."

        async def wait(self, key: Hashable, n: int = 1) -> None:
            "Reserve n tokens now and sleep until the reservation is covered.
             Exactly one asyncio.sleep per call at most (none if the tokens
             are available). On cancellation, return the n tokens to the
             bucket and re-raise. n > burst -> ValueError (it could never be
             satisfied)."

        def retry_after(self, key: Hashable, n: int = 1) -> float:
            "Seconds until n tokens are available (0.0 if they are now).
             Does not consume anything."

        def sweep(self) -> int:
            "Evict buckets that are full AND unused for >= idle_ttl; return
             how many were evicted. Also run automatically, at most once per
             idle_ttl, from allow()/wait()."

        def __len__(self) -> int: "number of tracked keys"

    class FixedWindowLimiter:
        def __init__(self, limit: int, window: float, *, clock=time.monotonic)
        def allow(self, key: Hashable) -> bool:
            "At most `limit` calls per key per aligned window
             [k*window, (k+1)*window)."

ACCEPTANCE CRITERIA
--------------------
    - A fresh key allows exactly `burst` calls, then refuses.
    - Refill is continuous: after 1/rate seconds exactly one more call is
      allowed; half of that is not enough (fractional tokens are kept).
    - A key idle for hours still only gets `burst` (tokens are capped).
    - allow(key, n) with too few tokens consumes nothing.
    - Keys are independent.
    - wait() returns immediately when tokens are available, otherwise sleeps
      once for the right duration; N concurrent waiters on one key finish
      spaced 1/rate apart, in arrival order.
    - Cancelling wait() (e.g. asyncio.timeout) refunds the tokens.
    - Over any sequence of calls, tokens granted <= burst + rate * elapsed
      (property-tested with hypothesis).
    - Idle full buckets are evicted; indebted or recently used ones are not.
    - The fixed-window limiter admits 2 * limit calls across a boundary in
      an interval much shorter than one window; the token bucket does not.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Hashable


class KeyedRateLimiter:
    def __init__(
        self,
        rate: float,
        burst: int,
        *,
        idle_ttl: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        # TODO: validate arguments; store them; buckets: dict[key, _Bucket]
        #  where a bucket holds `tokens: float`, `updated: float` (last
        #  refill time) and `last_used: float`; remember when you last swept.
        raise NotImplementedError

    def _bucket(self, key: Hashable, now: float) -> object:
        # TODO: get-or-create (a new bucket starts with tokens=burst), then
        #  lazy refill: tokens = min(burst, tokens + (now - updated) * rate);
        #  updated = now; last_used = now.
        raise NotImplementedError

    def allow(self, key: Hashable, n: int = 1) -> bool:
        # TODO: validate n; maybe sweep; refill; if tokens >= n: subtract,
        #  return True; else return False WITHOUT subtracting.
        raise NotImplementedError

    async def wait(self, key: Hashable, n: int = 1) -> None:
        # TODO:
        #  - validate n (n > burst -> ValueError)
        #  - refill, then tokens -= n (may go negative: that's the debt)
        #  - if tokens >= 0: return
        #  - try: await asyncio.sleep(-tokens / rate)
        #    except asyncio.CancelledError: refill, give back n (cap at
        #    burst), raise
        raise NotImplementedError

    def retry_after(self, key: Hashable, n: int = 1) -> float:
        # TODO: refill; return max(0.0, (n - tokens) / rate)
        raise NotImplementedError

    def sweep(self) -> int:
        # TODO: remove buckets idle >= idle_ttl whose refilled balance would
        #  be full. Build the list of victims first, then delete (never
        #  mutate a dict while iterating it).
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError


class FixedWindowLimiter:
    def __init__(
        self, limit: int, window: float, *, clock: Callable[[], float] = time.monotonic
    ) -> None:
        # TODO: store; counts: dict[key, tuple[window_index, count]]
        raise NotImplementedError

    def allow(self, key: Hashable) -> bool:
        # TODO: idx = int(clock() // window); reset the count when idx
        #  changes; allow while count < limit.
        raise NotImplementedError


if __name__ == "__main__":
    print("Implement the TODOs, then run the tests: pytest 15_rate_limiter/")


# ---------------------------------------------------------------------------
# Hints
# ---------------------------------------------------------------------------
# - Seconds until n tokens exist: (n - tokens) / rate. With a reservation the
#   balance is already `tokens - n`, so the sleep is `-balance / rate`.
# - `asyncio.sleep` is cancelled by `asyncio.timeout(...)`, `task.cancel()`
#   and TaskGroup sibling failures alike: one `except CancelledError:`
#   handler (refund, then bare `raise`) covers all of them.
# - A fake clock for tests is just `class Clock: t = 0.0; def __call__(self):
#   return self.t`. Use times that are exact in binary floating point (0.25,
#   0.125) so assertions don't hinge on rounding.
# - Amortised sweeping: in allow(), `if now - self._last_sweep >= idle_ttl:
#   self.sweep()`. Cost is O(keys) once per idle_ttl, i.e. O(1) amortised
#   per call at any realistic request rate; no background task to start,
#   stop and leak.
#
# Pitfalls
# --------
# - `time.time()` for rate math: wall-clock steps (NTP, manual changes) make
#   elapsed time negative or huge. Use `time.monotonic()`.
# - Refill without the `min(burst, ...)` cap: a key idle overnight arrives
#   with 30,000 tokens and bursts straight through your downstream.
# - Partially consuming on a failed allow(n): corrupts the balance for
#   every later caller.
# - A polling wait (`while not allow(): await asyncio.sleep(0.01)`): burns
#   wake-ups, adds up to 10 ms of latency, and gives no ordering -- a newly
#   arrived caller can beat one that has been waiting for seconds.
# - Swallowing `CancelledError` in wait(): the caller's timeout never
#   fires, and TaskGroup/`asyncio.timeout` semantics break.
# - Assuming "no lock needed" survives threads. The no-await argument is
#   about coroutines on ONE event loop. If the same limiter is called from
#   sync code in worker threads (`run_in_executor`, a threaded WSGI app),
#   refill-then-consume is a read-modify-write race: wrap the arithmetic in
#   a `threading.Lock` (never held across an await).
# - Using one limiter per process and calling it "the" limit: with 8 uvicorn
#   workers x 4 pods, a limit of 100/s per process is 3,200/s in total. A
#   cluster-wide limit needs shared state (see stretch goals).
#
# Stretch goals
# -------------
# - A FastAPI dependency that calls `allow(api_key)` and raises
#   HTTPException(429, headers={"Retry-After": ...}) using retry_after(),
#   plus `RateLimit-*` headers (IETF httpapi "RateLimit header fields"
#   draft; widely deployed as X-RateLimit-Limit/-Remaining/-Reset).
# - Distributed limiting: the same lazy-refill state (tokens, updated)
#   stored in Redis per key and updated by one Lua script (EVAL runs
#   atomically), with the Redis server's TIME as the clock. Or GCRA (the
#   generic cell rate algorithm), which stores a single timestamp per key
#   ("theoretical arrival time") and is what redis-cell and several
#   API gateways use.
# - A sliding-window-log limiter (deque of timestamps per key) and a
#   sliding-window-counter (weighted previous + current window). Compare
#   memory per key and boundary behaviour with the token bucket.
# - Compare with a library: `aiolimiter.AsyncLimiter` (leaky bucket, one
#   limiter, not keyed) or `limits` (fixed/moving windows, pluggable
#   Redis/Memcached storage). What does each give up?
