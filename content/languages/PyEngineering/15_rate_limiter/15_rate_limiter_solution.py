"""
15 — Rate Limiter — Reference Solution
=======================================

See `15_rate_limiter_explanation.py` for the full spec, rationale and
acceptance criteria. Design summary:

    - Token bucket with lazy refill and float tokens; one small bucket per
      key, created on first use.
    - `allow` is synchronous and await-free, which makes it atomic with
      respect to every other coroutine on the event loop -- no lock.
    - `wait` is a reservation: take the tokens now (possibly into debt),
      sleep once for exactly the debt, refund on cancellation. FIFO by
      construction, one wake-up per waiter.
    - Eviction only removes buckets that are idle AND full, so it is
      invisible to callers; it runs amortised from allow()/wait() instead of
      from a background task, so there is no lifecycle to manage.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable, Hashable
from dataclasses import dataclass


@dataclass(slots=True)
class _Bucket:
    tokens: float
    updated: float  # clock time `tokens` was last brought up to date
    last_used: float  # clock time of the last allow/wait/retry_after


class KeyedRateLimiter:
    """Per-key token-bucket limiter for use from one asyncio event loop."""

    def __init__(
        self,
        rate: float,
        burst: int,
        *,
        idle_ttl: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not rate > 0:  # also rejects NaN
            raise ValueError("rate must be > 0 tokens/second")
        if burst < 1:
            raise ValueError("burst must be >= 1")
        if not idle_ttl > 0:
            raise ValueError("idle_ttl must be > 0 seconds")
        self.rate = float(rate)
        self.burst = burst
        self.idle_ttl = float(idle_ttl)
        # monotonic, never time.time(): wall-clock jumps would make elapsed
        # time negative (tokens vanish) or huge (tokens appear).
        self._clock = clock
        self._buckets: dict[Hashable, _Bucket] = {}
        self._last_sweep = clock()

    # -- internals ----------------------------------------------------------

    def _refilled(self, b: _Bucket, now: float) -> float:
        # max(0, ...) guards against a clock that goes backwards (a buggy
        # fake, or a different clock source): never *remove* tokens.
        elapsed = max(0.0, now - b.updated)
        return min(float(self.burst), b.tokens + elapsed * self.rate)

    def _bucket(self, key: Hashable, now: float) -> _Bucket:
        b = self._buckets.get(key)
        if b is None:
            # A new key starts full: the first `burst` requests go through.
            b = _Bucket(tokens=float(self.burst), updated=now, last_used=now)
            self._buckets[key] = b
        else:
            b.tokens = self._refilled(b, now)
            b.updated = now
            b.last_used = now
        return b

    def _maybe_sweep(self, now: float) -> None:
        # Amortised: O(keys) work at most once per idle_ttl. Cheaper and
        # simpler than a background task, which would need start/stop, would
        # have to be tied to a running loop, and could leak if never stopped.
        if now - self._last_sweep >= self.idle_ttl:
            self.sweep()

    def _check_n(self, n: int) -> None:
        if n < 1:
            raise ValueError("n must be >= 1")

    # -- public API ---------------------------------------------------------

    def allow(self, key: Hashable, n: int = 1) -> bool:
        """Consume n tokens for `key` if all n are available right now."""
        self._check_n(n)
        now = self._clock()
        self._maybe_sweep(now)
        b = self._bucket(key, now)
        # No `await` between the refill above and the check-and-subtract
        # below: the event loop cannot switch tasks here, so this is atomic
        # with respect to every other coroutine.
        if b.tokens >= n:
            b.tokens -= n
            return True
        return False  # all-or-nothing: nothing consumed

    async def wait(self, key: Hashable, n: int = 1) -> None:
        """Take n tokens, sleeping (once) until they are covered.

        Cancellation (asyncio.timeout, task.cancel, a failing TaskGroup
        sibling) refunds the tokens and propagates CancelledError.
        """
        self._check_n(n)
        if n > self.burst:
            # The bucket can never hold n tokens, so this would wait forever
            # (x/time/rate returns an error for the same case).
            raise ValueError(f"n={n} exceeds burst={self.burst}")
        now = self._clock()
        self._maybe_sweep(now)
        b = self._bucket(key, now)
        b.tokens -= n  # reserve: may go negative; the debt orders waiters
        if b.tokens >= 0:
            return
        delay = -b.tokens / self.rate
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            # Give the reservation back so the tokens aren't lost. Re-fetch
            # through _bucket (refills, and re-creates if it was swept).
            # Later waiters already sleep as if our debt existed; refunding
            # only makes them conservative, never over the limit.
            b = self._bucket(key, self._clock())
            b.tokens = min(float(self.burst), b.tokens + n)
            raise

    def retry_after(self, key: Hashable, n: int = 1) -> float:
        """Seconds until n tokens are available; 0.0 if they are now.

        Computed from the same bucket `allow` uses, so a 429's Retry-After
        can't disagree with the decision that produced the 429.
        """
        self._check_n(n)
        b = self._bucket(key, self._clock())
        return max(0.0, (n - b.tokens) / self.rate)

    def sweep(self) -> int:
        """Evict buckets idle for >= idle_ttl that have refilled to full.

        A full bucket behaves exactly like a missing one (a new bucket starts
        full), so eviction never changes a decision. Buckets in debt or not
        yet full stay, otherwise a limited client could get a fresh burst
        just by pausing.
        """
        now = self._clock()
        self._last_sweep = now
        victims = [
            key
            for key, b in self._buckets.items()
            if now - b.last_used >= self.idle_ttl and self._refilled(b, now) >= self.burst
        ]
        for key in victims:  # never mutate a dict while iterating it
            del self._buckets[key]
        return len(victims)

    def __len__(self) -> int:
        return len(self._buckets)


class FixedWindowLimiter:
    """At most `limit` calls per key per aligned window. Kept for contrast.

    Simple and cheap (one int per key) -- and it admits up to 2 * limit
    calls in a short interval straddling a window boundary, which is why
    it is rarely the right choice for protecting a downstream.
    """

    def __init__(
        self, limit: int, window: float, *, clock: Callable[[], float] = time.monotonic
    ) -> None:
        if limit < 1 or not window > 0:
            raise ValueError("limit must be >= 1 and window > 0")
        self.limit = limit
        self.window = float(window)
        self._clock = clock
        self._counts: dict[Hashable, tuple[int, int]] = {}  # key -> (window idx, count)

    def allow(self, key: Hashable) -> bool:
        idx = int(self._clock() // self.window)
        cur_idx, count = self._counts.get(key, (idx, 0))
        if cur_idx != idx:
            count = 0  # new window: the counter resets all at once
        if count >= self.limit:
            self._counts[key] = (idx, count)
            return False
        self._counts[key] = (idx, count + 1)
        return True


async def _demo() -> None:
    limiter = KeyedRateLimiter(rate=5, burst=2)
    start = time.monotonic()
    for i in range(5):
        await limiter.wait("client-a")
        print(f"call {i} at +{time.monotonic() - start:.2f}s")
    allowed = limiter.allow("client-a")
    print("allow now?", allowed, "retry after", round(limiter.retry_after("client-a"), 2))


if __name__ == "__main__":
    asyncio.run(_demo())


# ---------------------------------------------------------------------------
# Best practices
# ---------------------------------------------------------------------------
# - Inject the clock. Every time-based component (limiter, cache TTL,
#   circuit breaker) becomes deterministic to test and immune to wall-clock
#   jumps in production.
# - Make both acquisition shapes available: servers reject (allow + 429 +
#   Retry-After), clients pace (wait).
# - Size `burst` on purpose: it is the spike your downstream must absorb.
#   rate=100/s with burst=1000 means 1,000 requests can arrive at once.
# - Choose the key deliberately: API key or tenant ID for fairness, client
#   IP only as a fallback (NAT/CGNAT puts thousands of users behind one IP;
#   IPv6 lets one user rotate through a /64). Rate-limit before expensive
#   work (auth DB lookups, body parsing) but after cheap identification.
# - Emit metrics on rejections per key class; a limiter that silently
#   rejects is indistinguishable from an outage to the people it throttles.
#
# Alternative approaches
# -----------------------
# - Leaky bucket (as a queue): requests enter a FIFO drained at a fixed
#   rate; smooths output completely but adds queueing latency. As a meter
#   it is mathematically equivalent to a token bucket.
# - GCRA: stores one float per key (the theoretical arrival time) instead
#   of (tokens, updated); same behaviour as a token bucket, less state, and
#   the usual choice for Redis-backed limiters.
# - Sliding-window log: exact "N in any window of length W", O(N) memory
#   per key. Sliding-window counter: approximate, two ints per key.
# - Libraries: `aiolimiter` (asyncio, leaky bucket, single limiter),
#   `limits` (windows, Redis/Memcached storage, used by slowapi for
#   FastAPI/Starlette). For a fleet, enforce at the edge (API gateway, Envoy
#   global rate limit service, cloud WAF) and keep an in-process limiter as
#   a second line of defence.
