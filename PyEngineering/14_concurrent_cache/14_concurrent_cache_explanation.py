"""
14 · Concurrent cache
=====================

WHAT WE'RE BUILDING
--------------------
A thread-safe, in-process cache with TTL eviction and single-flight
de-duplication: `get_or_compute(key, compute)` returns a cached value if
fresh, else computes it exactly once even when many threads race to
compute the same missing key at the same moment. This is the shape behind
`functools.lru_cache` in production services that actually need
expiration and cross-thread safety — a config cache, a per-request
memoized DB lookup, a computed-feature cache in front of a slow model.

WHY THREADS, NOT ASYNCIO, FOR THIS ONE
-----------------------------------------
Every other concurrency problem in this curriculum (12, 13, 15, 16) is
`asyncio`-native, because the concurrency is I/O-bound and single-threaded
cooperative scheduling is the right tool. A cache is different: it is
routinely called from **synchronous code paths** that have no event loop
at all — a Django/Flask request handler, a Celery task, a plain function
deep in a call stack that an `asyncio` service calls via
`run_in_executor`. Locking primitives don't cross the async/sync boundary
cleanly (`asyncio.Lock` only works correctly when awaited from inside the
same running event loop — a `threading.Lock`-protected structure is
usable from any thread, sync or async-via-executor, with no ownership
constraints). So: `threading.Lock` here, deliberately, because the real
in-production version of this exact component overwhelmingly is a plain
thread-safe class, not an asyncio primitive.

WHY THIS MATTERS IN REAL SYSTEMS
---------------------------------
- **The thundering herd problem.** Without single-flight, N threads that
  all miss the cache for the same key at the same moment each independently
  call the (possibly expensive/rate-limited/billed-per-call) `compute`
  function — N calls instead of 1. This is a classic real incident:
  a cache entry expires under load, and the recompute stampede takes down
  the backing database/API it was protecting. Single-flight collapses the
  N racing callers onto exactly one in-flight computation; every caller
  (including the N-1 that didn't win the race) gets the same result.
- **TTL eviction has a lazy-vs-eager trade-off.** Pure lazy expiry (check
  the timestamp on every `get`, evict then) never wastes CPU cleaning
  entries nobody's asking for, but a cache that's mostly cold-written and
  rarely re-read leaks expired entries in memory forever. An optional
  background sweep thread trades a small constant CPU/wakeup cost for a
  bounded memory ceiling — the right choice depends on the access pattern,
  and real systems often ship both (lazy expiry for correctness, periodic
  sweep for memory bounds), which is what this problem does.
- **Lock scope is the whole game.** Holding the cache's lock while calling
  `compute()` (which the caller supplies and may be slow/network-bound)
  would serialize *every* cache access — hits included — behind the
  slowest in-flight miss. Correct single-flight needs a lock per *key*
  during computation, held only long enough to register/await the
  in-flight computation, not the cache's single global lock held for the
  duration of the call.

CONCEPTS COVERED
-----------------
- `threading.Lock` for structure integrity vs. a hand-rolled single-flight
  mechanism (a per-key `threading.Event`-gated slot, not a library)
- Lazy TTL expiry (checked on read) + an optional daemon background sweep
  thread for proactive cleanup
- Why holding a lock across a slow/user-supplied call is a bug, and how to
  avoid it while still guaranteeing exactly-once computation

THE SPEC
--------
Build `ConcurrentCache[K, V]` (PEP 695 generic class):

    class ConcurrentCache[K, V]:
        def __init__(
            self,
            *,
            ttl_seconds: float | None = None,
            sweep_interval_seconds: float | None = None,
        ) -> None: ...
        def get_or_compute(self, key: K, compute: Callable[[], V]) -> V: ...
        def get(self, key: K) -> V | None: ...
        def invalidate(self, key: K) -> None: ...
        def __len__(self) -> int: ...
        def close(self) -> None: ...
            # stops the background sweep thread if one was started

Behavior:
    - `get_or_compute(key, compute)`: return the cached value if present
      and unexpired. Otherwise, ensure `compute()` runs *exactly once*
      across however many threads concurrently miss on the same key —
      every caller (the one that ran `compute` and every other one that
      raced it) receives the same computed value. If `compute()` raises,
      every waiting caller sees that same exception re-raised (the failure
      is not cached — the next call retries).
    - `ttl_seconds=None` means entries never expire.
    - `get(key)` is a read-only lookup: returns `None` on miss/expiry,
      never triggers computation, never blocks on an in-flight computation
      for that key (it should not wait for another thread's `compute`).
    - `invalidate(key)` removes an entry (no-op if absent).
    - If `sweep_interval_seconds` is set, a daemon background thread
      periodically scans and evicts expired entries (in addition to the
      lazy check every `get`/`get_or_compute` already does). `close()`
      stops it deterministically (joinable, no lingering thread after
      `close()` returns).

ACCEPTANCE CRITERIA
--------------------
1. Sequential correctness: cached values round-trip; TTL expiry causes a
   miss (and recompute) after the TTL elapses, verified with a fake/
   monkeypatched clock (not a real `time.sleep`, to keep tests fast and
   non-flaky).
2. **Single-flight, proven directly**: spin up many threads all calling
   `get_or_compute` on the same missing key simultaneously (synchronized
   via a `threading.Barrier`); assert the compute function's call count is
   exactly 1 and every thread receives the identical result.
3. A `compute()` exception is propagated to every racing caller and is
   NOT cached — the next `get_or_compute` call retries computation.
4. `get()` never blocks on another thread's in-flight `get_or_compute` for
   the same key.
5. With `sweep_interval_seconds` set, expired entries are removed by the
   background thread even without any `get` calls touching them; `close()`
   leaves no running non-daemon thread behind.
6. mypy-clean, black-formatted, ruff-clean.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class ConcurrentCache(Generic[K, V]):
    """Thread-safe cache: TTL eviction (lazy + optional sweep) + single-flight."""

    def __init__(
        self,
        *,
        ttl_seconds: float | None = None,
        sweep_interval_seconds: float | None = None,
    ) -> None:
        # TODO: self._ttl = ttl_seconds
        # TODO: self._lock = threading.Lock()  # protects the entries dict
        #       and the in-flight-computation registry, briefly, per call
        # TODO: self._entries: dict[K, tuple[V, float]] = {}  # value, expires_at
        # TODO: self._inflight: dict[K, "_SingleFlight[V]"] = {}
        # TODO: if sweep_interval_seconds is set, start a daemon
        #       threading.Thread running a sweep loop; store a
        #       threading.Event to signal it to stop, and the Thread
        #       object itself so close() can join() it.
        raise NotImplementedError("TODO: implement ConcurrentCache.__init__")

    def get(self, key: K) -> V | None:
        """Read-only lookup. Never computes, never blocks on another
        thread's in-flight computation for this key."""
        # TODO: under self._lock, look up key; if present and unexpired,
        # return the value; if present and expired, delete it and fall
        # through to return None.
        raise NotImplementedError("TODO: implement ConcurrentCache.get")

    def get_or_compute(self, key: K, compute: Callable[[], V]) -> V:
        """Return the cached value, or compute it exactly once under
        concurrent callers racing on the same missing key."""
        # TODO: this is the core of the problem. Sketch:
        # 1. Fast path: under the lock, if key present+unexpired, return it.
        # 2. Still under the lock: check self._inflight for key. If another
        #    thread is already computing this key, grab its _SingleFlight
        #    handle and release the lock, then WAIT on it (outside the
        #    lock!) and return/raise based on its outcome.
        # 3. Otherwise, still under the lock, create a fresh _SingleFlight
        #    and register it in self._inflight[key] — this "reserves" the
        #    key for this thread before releasing the lock, which is what
        #    makes step 2 correct for every thread that arrives after this
        #    point but before the computation finishes.
        # 4. Release the lock, then actually call compute() OUTSIDE the
        #    lock (never hold the cache lock across caller-supplied code).
        # 5. On success: store the value+expiry under the lock, remove the
        #    inflight entry, and wake every waiter with the result.
        #    On exception: remove the inflight entry (do NOT cache the
        #    failure) and wake every waiter with the exception re-raised.
        raise NotImplementedError("TODO: implement ConcurrentCache.get_or_compute")

    def invalidate(self, key: K) -> None:
        # TODO: under the lock, self._entries.pop(key, None).
        raise NotImplementedError("TODO: implement ConcurrentCache.invalidate")

    def __len__(self) -> int:
        # TODO: under the lock, return len(self._entries).
        raise NotImplementedError("TODO: implement ConcurrentCache.__len__")

    def close(self) -> None:
        """Stop the background sweep thread, if any, deterministically."""
        # TODO: if a sweep thread was started, set its stop-Event and
        # thread.join() it. Idempotent — safe to call twice.
        raise NotImplementedError("TODO: implement ConcurrentCache.close")


# ---------------------------------------------------------------------------
# HINTS
# -----
# - The single-flight handle needs exactly one thing beyond storage for
#   the result/exception: a way for N-1 threads to block until the 1
#   computing thread is done. `threading.Event` is the natural fit —
#   `.wait()` for waiters, `.set()` by the computing thread when finished.
# - The trickiest correctness property: the "reservation" (registering the
#   in-flight handle) must happen BEFORE the lock is released, and the
#   actual `compute()` call must happen AFTER the lock is released. Get
#   this ordering wrong in either direction and you either serialize all
#   cache access behind slow computes, or open a race window where two
#   threads both think they're the one computing.
# - For the fake-clock TTL test, inject a callable (`now: Callable[[],
#   float] = time.monotonic`) as a constructor parameter so tests can pass
#   a controllable fake instead of sleeping in real time.
#
# COMMON PITFALLS
# ---------------
# - Holding `self._lock` while calling `compute()` — this serializes the
#   entire cache (even unrelated keys, even pure hits) behind one slow
#   miss. The lock must be released before calling into caller code.
# - Caching a `compute()` exception as if it were a valid value — a
#   transient failure (a downstream timeout, say) must not permanently
#   poison the cache entry; the next call should retry.
# - A single-flight implementation that only de-duplicates *within* one
#   call to `get_or_compute` (e.g. a naive check-then-act with no
#   registration step) rather than truly across concurrently racing
#   threads — this is the bug the barrier-synchronized test is designed to
#   catch, and it's easy to write a version that passes a casual manual
#   test but fails under a real race.
# - Forgetting the sweep thread must be a daemon thread (or explicitly
#   joined in `close()`) — a non-daemon thread that's never stopped keeps
#   the whole process alive past `main()` returning, which is exactly the
#   kind of "leaked resource" this curriculum's problems keep testing for.
#
# STRETCH GOALS
# --------------
# - Add a maximum size with LRU eviction (an `OrderedDict` with
#   `move_to_end` on access, evicting from the front when over capacity)
#   and measure hit rate under a Zipfian access pattern.
# - Add per-key locks (a `dict[K, threading.Lock]`) instead of one global
#   structural lock, and measure whether it actually helps throughput at
#   realistic key cardinalities (Python's GIL means pure-CPU compute won't
#   benefit; I/O-bound compute — the realistic case — might).
# - Add `async def aget_or_compute` as a thin asyncio-facing wrapper via
#   `loop.run_in_executor`, and explain in comments why this is usually
#   the right integration point rather than rewriting the cache itself in
#   `asyncio` primitives.
