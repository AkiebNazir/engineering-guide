"""
14 · Concurrent cache — solution.

See `14_concurrent_cache_explanation.py` for the full spec, rationale, and
acceptance criteria. This file is the complete, idiomatic implementation.

DESIGN DECISION: threading.Lock, not asyncio, and why
--------------------------------------------------------
See the module docstring in the explanation file for the full argument;
in short, this component is called from synchronous code paths with no
event loop, so a `threading.Lock`-protected structure (usable from any
thread with no ownership/loop constraints) is the correct default, not an
`asyncio.Lock` (which only works correctly awaited from within its owning
event loop).

DESIGN DECISION: hand-rolled single-flight via a per-key Event
-------------------------------------------------------------------
The single-flight mechanism is a small state machine per missing key:

1. The first thread to miss registers a `_SingleFlight` placeholder in
   `self._inflight[key]` **while still holding the structural lock** —
   this is the "reservation" that makes every subsequent racing thread
   see the placeholder instead of also deciding it's the one to compute.
2. That thread releases the lock, then calls `compute()` with no lock
   held at all — so hits and misses on *other* keys, and even `get()`
   calls on this key... no, `get()` on the still-inflight key correctly
   returns `None` per the spec (it must not block), which is naturally
   true here since nothing is written to `self._entries` until step 3.
3. Every other thread that reaches step "check inflight" while the
   computation is running gets the *same* `_SingleFlight` object, releases
   the lock, and blocks on its `threading.Event` outside the lock — so
   N-1 threads are simply parked on an Event, consuming no CPU, holding no
   lock, for the duration of the 1 real computation.
4. The computing thread stores the result (or exception) on the
   `_SingleFlight` object, removes it from `self._inflight`, writes the
   cache entry (success only), and calls `event.set()` — waking every
   parked thread at once, each of which reads the shared result/exception
   off the same object.

The critical invariant: the lock is held only for O(1) dict operations
(check entries, check/register inflight, on completion swap inflight for
a cache entry) — never across `compute()` itself and never across an
Event `.wait()`. That's what keeps hits, and misses on unrelated keys,
fully concurrent with a slow miss in progress on one key.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class _SingleFlight(Generic[V]):
    """One in-flight computation's shared result slot + completion signal.

    Exactly one thread (the "leader") calls `compute()` and calls
    `resolve`/`fail`; every other thread ("follower") blocks on `done`
    and then reads `value`/`error`.
    """

    __slots__ = ("done", "value", "error")

    def __init__(self) -> None:
        self.done = threading.Event()
        self.value: V | None = None
        self.error: BaseException | None = None

    def resolve(self, value: V) -> None:
        self.value = value
        self.done.set()

    def fail(self, error: BaseException) -> None:
        self.error = error
        self.done.set()

    def wait_result(self) -> V:
        self.done.wait()
        if self.error is not None:
            raise self.error
        # mypy can't see that done implies exactly one of value/error is
        # set; value is only None here if the leader legitimately computed
        # None, which is a valid cached value.
        return self.value  # type: ignore[return-value]


class ConcurrentCache(Generic[K, V]):
    """Thread-safe cache: TTL eviction (lazy + optional sweep) + single-flight."""

    def __init__(
        self,
        *,
        ttl_seconds: float | None = None,
        sweep_interval_seconds: float | None = None,
        now: Callable[[], float] = time.monotonic,
    ) -> None:
        self._ttl = ttl_seconds
        self._now = now
        # Step 1: one lock protects both the entries table and the
        # in-flight registry. Both are plain dict operations (fast,
        # non-blocking work) — the lock is never held across compute() or
        # an Event.wait(), so this single lock does not become a
        # throughput bottleneck under concurrent misses on different keys.
        self._lock = threading.Lock()
        self._entries: dict[K, tuple[V, float | None]] = {}  # value, expires_at
        self._inflight: dict[K, _SingleFlight[V]] = {}

        self._sweep_thread: threading.Thread | None = None
        self._sweep_stop = threading.Event()
        if sweep_interval_seconds is not None:
            self._sweep_thread = threading.Thread(
                target=self._sweep_loop,
                args=(sweep_interval_seconds,),
                daemon=True,  # never blocks process exit even if close()
                # is forgotten, though close() is still the correct way
                # to stop it deterministically (see close()).
                name="ConcurrentCache-sweep",
            )
            self._sweep_thread.start()

    def _is_expired(self, expires_at: float | None) -> bool:
        return expires_at is not None and self._now() >= expires_at

    def get(self, key: K) -> V | None:
        """Read-only lookup: never computes, never blocks on an in-flight
        computation for this key (returns None if one is in progress)."""
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if self._is_expired(expires_at):
                del self._entries[key]
                return None
            return value

    def get_or_compute(self, key: K, compute: Callable[[], V]) -> V:
        """Return the cached value, or compute it exactly once under
        concurrent callers racing on the same missing key."""
        # Fast path + reservation, both under the lock so they're atomic
        # with respect to every other thread calling get_or_compute.
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None:
                value, expires_at = entry
                if not self._is_expired(expires_at):
                    return value
                del self._entries[key]  # lazily evict, fall through to miss

            existing = self._inflight.get(key)
            if existing is not None:
                # A follower: someone else is already computing this key.
                is_leader = False
                flight = existing
            else:
                # The leader: reserve the key for this thread BEFORE
                # releasing the lock, so every thread that arrives after
                # this point (however soon) sees `existing is not None`
                # above and becomes a follower instead of a second leader.
                is_leader = True
                flight = _SingleFlight()
                self._inflight[key] = flight

        if not is_leader:
            # Block outside the lock — a follower parked here holds no
            # lock and consumes no CPU; unrelated cache traffic proceeds
            # freely while this waits.
            return flight.wait_result()

        # Leader path: call the caller-supplied compute() with NO lock
        # held at all. This is the single most important line in the
        # file — holding self._lock here would serialize every other
        # thread's cache access (hits included) behind this one call.
        try:
            value = compute()
        except BaseException as exc:  # noqa: BLE001 - must propagate ANY
            # compute() failure to every follower, not just Exception
            # subclasses, then re-raise it ourselves too.
            with self._lock:
                del self._inflight[key]
            flight.fail(exc)
            raise
        else:
            expires_at = None if self._ttl is None else self._now() + self._ttl
            with self._lock:
                self._entries[key] = (value, expires_at)
                del self._inflight[key]
            flight.resolve(value)
            return value

    def invalidate(self, key: K) -> None:
        with self._lock:
            self._entries.pop(key, None)

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)

    def _sweep_loop(self, interval: float) -> None:
        # Runs on the daemon sweep thread. wait() with a timeout doubles
        # as both the sleep and the stop signal — close() sets the event
        # to end this loop immediately instead of waiting out the full
        # interval.
        while not self._sweep_stop.wait(timeout=interval):
            with self._lock:
                expired = [
                    k for k, (_, exp) in self._entries.items() if self._is_expired(exp)
                ]
                for k in expired:
                    del self._entries[k]

    def close(self) -> None:
        """Stop the background sweep thread, if any, deterministically.

        Idempotent: safe to call more than once.
        """
        if self._sweep_thread is not None:
            self._sweep_stop.set()
            self._sweep_thread.join()
            self._sweep_thread = None


# ---------------------------------------------------------------------------
# Best practices demonstrated here
# ---------------------------------------------------------------------------
# - Never hold a lock across a caller-supplied callback (`compute()`) or a
#   blocking wait (`Event.wait()`) — both must happen with the lock
#   released, or the entire cache serializes behind the slowest miss.
# - "Reserve, then release, then do the slow thing" is the general pattern
#   for hand-rolled single-flight/de-duplication: the reservation must be
#   atomic with the check that decides "am I the leader," which is exactly
#   what doing both under one lock acquisition guarantees.
# - Don't cache failures. A cache is a performance optimization over a
#   presumed-idempotent, presumed-eventually-successful computation; an
#   exception is information about *this* attempt, not a fact about the
#   key that deserves to be memoized.
# - Inject the clock (`now: Callable[[], float]`) for TTL tests — a real
#   `time.sleep()`-based TTL test is slow and flaky under CI load; a fake
#   clock makes expiry assertions instant and deterministic.
# - Make the background thread a daemon AND give `close()` a real, joined
#   shutdown path — belt and suspenders. The daemon flag prevents an
#   at-exit hang if a caller forgets `close()`; the explicit join makes
#   "no leftover thread" a testable, deterministic guarantee for callers
#   who do the right thing.
#
# Alternative approaches
# -----------------------
# - Per-key locks (`dict[K, threading.Lock]`) instead of one structural
#   lock — reduces contention between unrelated keys' reservation step,
#   but that step is already O(1) dict work under the GIL, so it rarely
#   matters in practice; it adds real complexity (locks-for-locks: you now
#   need to synchronize creation/cleanup of the per-key lock dict itself).
# - `functools.lru_cache` / `cachetools.TTLCache` for the non-single-flight
#   subset of this problem — neither offers single-flight de-duplication
#   or a background sweep out of the box; both are good choices when
#   thundering-herd protection genuinely doesn't matter for the workload.
# - A read-write lock (no stdlib primitive; would need a third-party
#   package or a hand-rolled one) to let concurrent `get()` reads proceed
#   without even the brief exclusive lock used here — usually not worth
#   the complexity given how short the critical sections already are.
#
# Testing/benchmarking notes
# ----------------------------
# - The single-flight property is only provable under genuine concurrent
#   contention: use `threading.Barrier` to line up N threads and release
#   them at the same instant, then assert `compute` was called exactly
#   once — sequential calls to `get_or_compute` (even in a tight loop)
#   cannot expose a broken single-flight implementation, because the race
#   window is a handful of instructions wide.
# - TTL tests should control time explicitly via the injected `now`
#   callable rather than `time.sleep`, both for speed and to eliminate
#   scheduler-jitter flakiness near the expiry boundary.
