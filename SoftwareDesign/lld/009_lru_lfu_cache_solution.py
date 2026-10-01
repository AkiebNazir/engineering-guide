"""
================================================================================
SOLUTION · LLD 009 · LRU / LFU Cache with Pluggable Eviction       [Tier 1]
================================================================================

THE CORE IDEA
--------------
A cache is a dict plus a DECISION: when full, whom to evict. Keep them apart:

    Cache           owns the key -> entry map, capacity, TTL, stats, callbacks
    EvictionPolicy  owns only the ORDER: on_insert / on_access / on_remove /
                    victim() — every method O(1)

    LRU  hash map + doubly linked list with sentinels. Access = unlink + append
         at the tail; victim = head.next. (OrderedDict.move_to_end is the same
         structure in C — say so, then write the list if asked.)

    LFU  key -> freq, freq -> insertion-ordered bucket of keys, min_freq.
         Access moves a key from bucket f to f+1 in O(1); the victim is the
         OLDEST key in the min_freq bucket (LRU breaks ties). The naive LFU
         scans for the minimum: O(n) per eviction (demo 2).

    FIFO insertion order only; access changes nothing.

Two senior-level additions interviewers love:
    * Thread safety as a PROXY (LockedCache) — the single-threaded cache stays
      simple and fast; the wrapper serialises access. Demo 3 shows an unlocked
      linked list getting corrupted under thread preemption.
    * get_or_load with SINGLE-FLIGHT: when 50 requests miss the same hot key at
      once, the loader (a DB query) runs ONCE and the rest wait for its result.
      Without it you get a cache stampede.


================================================================================
REQUIREMENTS (agreed in the first 5 minutes)
================================================================================
  1. get(key, default=None), put(key, value), delete(key) -> bool, len().
  2. Capacity >= 1; eviction policy pluggable: LRU (default), LFU, FIFO.
  3. Optional TTL per cache; expired entries are misses and are removed.
  4. Stats: hits, misses, evictions, expirations.
  5. on_evict(key, value) callback (write-behind, metrics).
  6. All operations O(1) average.
  7. Thread-safe variant with get_or_load(key, loader) calling the loader at
     most once per key concurrently.
  Out of scope: size-in-bytes limits, distributed caching, persistence.


================================================================================
ENTITIES AND INVARIANTS
================================================================================
    Cache                 INVARIANT: set(data keys) == set(policy keys);
                          len(data) <= capacity
    _Entry                value, expires_at
    EvictionPolicy        LRUPolicy / LFUPolicy / FIFOPolicy
       LFU INVARIANT: every key is in exactly the bucket of its freq;
                      buckets are never empty; min_freq <= every freq
                      (repaired lazily after arbitrary deletes)
    LockedCache (proxy)   one lock around a Cache + in-flight loads per key
    Stats                 counters


================================================================================
LFU TRACE · capacity 2
================================================================================
    op        freq            buckets                       min   evicted
    put a     {a:1}           {1:[a]}                       1
    put b     {a:1,b:1}       {1:[a,b]}                     1
    get a     {a:2,b:1}       {1:[b], 2:[a]}                1
    get a     {a:3,b:1}       {1:[b], 3:[a]}                1
    get b     {a:3,b:2}       {2:[b], 3:[a]}                2     (bucket 1 emptied -> min 2)
    put c     {a:3,c:1}       {1:[c], 3:[a]}                1     b (freq 2 < 3)


================================================================================
DESIGN DECISIONS AND ALTERNATIVES
================================================================================
  * Policy as strategy with four O(1) hooks — the Cache never branches on
    policy type, and a new policy (e.g. LRU-K, ARC) is one class.
  * put() on an existing key counts as an access (refreshes recency/frequency)
    and never evicts.
  * Lazy TTL (checked on get). A sweeper or "evict expired first" is a
    follow-up; lazy expiry is always correct, the sweeper only frees memory.
  * Locking in a proxy, not sprinkled through Cache. Coarse lock is right here:
    every get mutates the order (even reads write!), so a RW lock buys nothing.
  * Single-flight: in-flight map key -> Event; the loader runs OUTSIDE the lock.
    If the loader raises, waiters see the miss and one of them retries.


================================================================================
COMPLEXITY
================================================================================
    Operation        LRU     LFU     FIFO    Naive LFU (scan)
    get              O(1)    O(1)    O(1)    O(1)
    put (no evict)   O(1)    O(1)    O(1)    O(1)
    put (evict)      O(1)    O(1)*   O(1)    O(n)
    * amortised; a lazy min_freq repair after deletes is O(#distinct freqs)


================================================================================
EDGE CASES
================================================================================
  * Capacity 1: every new key evicts the previous one.
  * put existing key when full -> update, no eviction.
  * LFU tie on frequency -> least recently used of those.
  * delete() or expiry removes the only key in the min_freq bucket.
  * Expired key counts as a miss AND an expiration, not a hit.
  * on_evict raising must not corrupt the cache (callback runs after removal).
  * Loader raises -> exception reaches that caller, nothing cached.


================================================================================
COMMON MISTAKES
================================================================================
  1. LRU with a list and list.remove(key) -> O(n).
  2. LFU with a heap of (freq, key) -> O(log n) and stale entries.
  3. LFU forgetting the LRU tie-break, or min_freq not updated on access.
  4. Treating get() as read-only under a reader lock (it reorders!).
  5. Calling the loader while holding the cache lock (every other key blocks).
  6. No single-flight -> stampede on a hot key after expiry.
  7. Cache class with `if self.policy == "LRU": ... elif "LFU"` everywhere.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
  * Bounded by bytes, not count -> entry weight; evict until total fits.
  * High concurrency -> lock striping (N shards, each its own LRU); or
    approximate LRU (CLOCK / sampled eviction like Redis).
  * Distributed cache -> consistent hashing over nodes; invalidation via TTL +
    pub/sub; see SystemDesign building blocks.
  * Refresh-ahead -> reload hot keys shortly before expiry in the background.
  * Negative caching -> cache "not found" with a short TTL.
  * Stale-while-revalidate -> serve expired value while one loader refreshes.


================================================================================
RELATED
================================================================================
  PyDSA 25_design  LC 146 LRU Cache, LC 460 LFU Cache
  SoftwareDesign/04_design_patterns_in_practice.md  §3 Strategy, §10 Proxy/Decorator
  lld/012_rate_limiter (same per-key state + injected clock shape)
"""

from __future__ import annotations

import random
import sys
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Callable, Hashable, Protocol

Clock = Callable[[], float]
_MISSING = object()


# ----------------------------------------------------------------------------
# Eviction policies
# ----------------------------------------------------------------------------
class EvictionPolicy(Protocol):
    def on_insert(self, key: Hashable) -> None: ...
    def on_access(self, key: Hashable) -> None: ...
    def on_remove(self, key: Hashable) -> None: ...
    def victim(self) -> Hashable: ...


class _Node:
    __slots__ = ("key", "prev", "next")

    def __init__(self, key: Hashable = None) -> None:
        self.key = key
        self.prev: _Node = self
        self.next: _Node = self


class LRUPolicy:
    """Hash map + doubly linked list with one sentinel. Head side = least recent."""

    def __init__(self) -> None:
        self._sentinel = _Node()
        self._nodes: dict[Hashable, _Node] = {}

    def _append(self, node: _Node) -> None:
        last = self._sentinel.prev
        last.next = node
        node.prev = last
        node.next = self._sentinel
        self._sentinel.prev = node

    @staticmethod
    def _unlink(node: _Node) -> None:
        node.prev.next = node.next
        node.next.prev = node.prev

    def on_insert(self, key):
        node = _Node(key)
        self._nodes[key] = node
        self._append(node)

    def on_access(self, key):
        node = self._nodes[key]
        self._unlink(node)
        self._append(node)

    def on_remove(self, key):
        self._unlink(self._nodes.pop(key))

    def victim(self):
        return self._sentinel.next.key

    def order(self) -> list:
        out, node = [], self._sentinel.next
        while node is not self._sentinel:
            out.append(node.key)
            node = node.next
        return out


class LFUPolicy:
    """key -> freq, freq -> insertion-ordered keys, min_freq. All O(1)."""

    def __init__(self) -> None:
        self._freq: dict[Hashable, int] = {}
        self._buckets: dict[int, dict[Hashable, None]] = {}
        self._min = 0

    def _detach(self, key) -> int:
        f = self._freq[key]
        bucket = self._buckets[f]
        del bucket[key]
        if not bucket:
            del self._buckets[f]
        return f

    def on_insert(self, key):
        self._freq[key] = 1
        self._buckets.setdefault(1, {})[key] = None
        self._min = 1

    def on_access(self, key):
        f = self._detach(key)
        if self._min == f and f not in self._buckets:
            self._min = f + 1
        self._freq[key] = f + 1
        self._buckets.setdefault(f + 1, {})[key] = None

    def on_remove(self, key):
        self._detach(key)
        del self._freq[key]

    def victim(self):
        if self._min not in self._buckets:          # repair after delete/expiry
            self._min = min(self._buckets)
        return next(iter(self._buckets[self._min]))

    def frequency(self, key) -> int:
        return self._freq[key]


class FIFOPolicy:
    def __init__(self) -> None:
        self._order: dict[Hashable, None] = {}

    def on_insert(self, key):
        self._order[key] = None

    def on_access(self, key):
        pass

    def on_remove(self, key):
        del self._order[key]

    def victim(self):
        return next(iter(self._order))


# ----------------------------------------------------------------------------
# Cache
# ----------------------------------------------------------------------------
@dataclass(slots=True)
class Stats:
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0


@dataclass(slots=True)
class _Entry:
    value: object
    expires_at: float


class Cache:
    def __init__(self, capacity: int, policy: EvictionPolicy | None = None,
                 ttl_s: float | None = None, clock: Clock = time.monotonic,
                 on_evict: Callable[[Hashable, object], None] | None = None) -> None:
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self._policy = policy or LRUPolicy()
        self._ttl = ttl_s
        self._clock = clock
        self._on_evict = on_evict
        self._data: dict[Hashable, _Entry] = {}
        self.stats = Stats()

    def get(self, key, default=None):
        entry = self._data.get(key)
        if entry is None:
            self.stats.misses += 1
            return default
        if self._clock() >= entry.expires_at:
            self._remove(key)
            self.stats.expirations += 1
            self.stats.misses += 1
            return default
        self.stats.hits += 1
        self._policy.on_access(key)
        return entry.value

    def put(self, key, value) -> None:
        expires = self._clock() + self._ttl if self._ttl is not None else float("inf")
        if key in self._data:
            self._data[key] = _Entry(value, expires)
            self._policy.on_access(key)
            return
        evicted = None
        if len(self._data) >= self.capacity:
            victim = self._policy.victim()
            evicted = (victim, self._data[victim].value)
            self._remove(victim)
            self.stats.evictions += 1
        self._data[key] = _Entry(value, expires)
        self._policy.on_insert(key)
        if evicted and self._on_evict:
            self._on_evict(*evicted)                    # after the cache is consistent

    def delete(self, key) -> bool:
        if key not in self._data:
            return False
        self._remove(key)
        return True

    def __contains__(self, key) -> bool:
        return key in self._data

    def __len__(self) -> int:
        return len(self._data)

    def _remove(self, key) -> None:
        del self._data[key]
        self._policy.on_remove(key)


# ----------------------------------------------------------------------------
# Thread-safe proxy with single-flight loading
# ----------------------------------------------------------------------------
class LockedCache:
    def __init__(self, cache: Cache) -> None:
        self._cache = cache
        self._lock = threading.Lock()
        self._inflight: dict[Hashable, threading.Event] = {}

    def get(self, key, default=None):
        with self._lock:
            return self._cache.get(key, default)

    def put(self, key, value) -> None:
        with self._lock:
            self._cache.put(key, value)

    def delete(self, key) -> bool:
        with self._lock:
            return self._cache.delete(key)

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)

    @property
    def stats(self) -> Stats:
        return self._cache.stats

    def get_or_load(self, key, loader: Callable[[Hashable], object]):
        while True:
            with self._lock:
                value = self._cache.get(key, _MISSING)
                if value is not _MISSING:
                    return value
                event = self._inflight.get(key)
                if event is None:                          # I am the loader
                    event = self._inflight[key] = threading.Event()
                    break
            event.wait()                                   # someone else is loading; re-check
        try:
            value = loader(key)                            # outside the lock
            with self._lock:
                self._cache.put(key, value)
            return value
        finally:
            with self._lock:
                del self._inflight[key]
            event.set()


# ===================================================================== TESTS ==
class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


def _check(label: str, ok: bool) -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    return ok


def run_tests() -> bool:
    all_ok = True
    print("--- LRU ---")
    c = Cache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")
    c.put("c", 3)
    all_ok &= _check("get(a) makes b the least recent -> b evicted", "b" not in c and c.get("a") == 1)
    c.put("a", 10)
    c.put("d", 4)
    all_ok &= _check("put on existing key refreshes it and doesn't evict; c evicted next",
                     c.get("a") == 10 and "c" not in c and len(c) == 2)
    one = Cache(1)
    one.put("x", 1)
    one.put("y", 2)
    all_ok &= _check("capacity 1", "x" not in one and one.get("y") == 2)

    print("\n--- LFU (the docstring trace) ---")
    lfu = LFUPolicy()
    c = Cache(2, lfu)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a"); c.get("a"); c.get("b")
    c.put("c", 3)
    all_ok &= _check("b (freq 2) evicted, a (freq 3) kept", "b" not in c and "a" in c and lfu.frequency("a") == 3)
    c = Cache(2, LFUPolicy())
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)
    all_ok &= _check("frequency tie -> least recently used (a) evicted", "a" not in c and "b" in c)
    lfu = LFUPolicy()
    c = Cache(3, lfu)
    for k in "xyz":
        c.put(k, k)
    c.get("y"); c.get("z")
    c.delete("x")                                     # empties the min_freq bucket
    c.put("w", "w")
    c.put("v", "v")
    all_ok &= _check("min_freq repaired after deleting the only freq-1 key", "w" not in c and len(c) == 3)

    print("\n--- FIFO ---")
    c = Cache(2, FIFOPolicy())
    c.put("a", 1); c.put("b", 2); c.get("a"); c.put("c", 3)
    all_ok &= _check("access doesn't matter: a (first in) evicted", "a" not in c and "b" in c)

    print("\n--- TTL, stats, callbacks ---")
    clock = FakeClock()
    evicted = []
    c = Cache(2, ttl_s=10, clock=clock, on_evict=lambda k, v: evicted.append((k, v)))
    c.put("a", 1)
    clock.t = 9.9
    hit = c.get("a")
    clock.t = 10.0
    miss = c.get("a")
    all_ok &= _check("alive at 9.9 s, expired at exactly 10 s", hit == 1 and miss is None and "a" not in c)
    c.put("b", 2); c.put("c", 3); c.put("d", 4)
    all_ok &= _check("stats count hits, misses, expirations, evictions",
                     (c.stats.hits, c.stats.misses, c.stats.expirations, c.stats.evictions) == (1, 1, 1, 1))
    all_ok &= _check("on_evict receives the evicted pair", evicted == [("b", 2)])
    all_ok &= _check("delete returns whether the key existed", c.delete("c") is True and c.delete("c") is False)
    all_ok &= _check("default returned on miss", c.get("nope", "dflt") == "dflt")
    try:
        Cache(0)
        ok = False
    except ValueError:
        ok = True
    all_ok &= _check("capacity 0 rejected", ok)

    print("\n--- LockedCache.get_or_load ---")
    lc = LockedCache(Cache(10))
    calls = []
    all_ok &= _check("loads on miss, cached afterwards",
                     lc.get_or_load("k", lambda k: calls.append(k) or "v") == "v"
                     and lc.get_or_load("k", lambda k: calls.append(k) or "other") == "v" and calls == ["k"])

    def failing(k):
        raise RuntimeError("db down")
    try:
        lc.get_or_load("bad", failing)
        ok = False
    except RuntimeError:
        ok = True
    all_ok &= _check("loader error reaches the caller; nothing cached; key loadable later",
                     ok and lc.get("bad") is None and lc.get_or_load("bad", lambda k: 1) == 1)
    return all_ok
# ================================================================= END TESTS ==


class NaiveLFU:
    """O(n) eviction: scan for the smallest (freq, last_used)."""

    def __init__(self) -> None:
        self.meta: dict[Hashable, list[int]] = {}
        self.tick = 0

    def on_insert(self, key):
        self.tick += 1
        self.meta[key] = [1, self.tick]

    def on_access(self, key):
        self.tick += 1
        m = self.meta[key]
        m[0] += 1
        m[1] = self.tick

    def on_remove(self, key):
        del self.meta[key]

    def victim(self):
        return min(self.meta, key=lambda k: self.meta[k])


def run_demos() -> bool:
    all_ok = True
    print("\n--- DEMO 1: 200,000 random ops vs reference models ---")
    rng = random.Random(4)
    ref_lru: OrderedDict = OrderedDict()
    lru = Cache(50)
    lfu, naive = Cache(50, LFUPolicy()), Cache(50, NaiveLFU())
    bad = 0
    for _ in range(200_000):
        k = rng.randrange(120)
        if rng.random() < 0.5:
            v = rng.random()
            lru.put(k, v); lfu.put(k, v); naive.put(k, v)
            if k in ref_lru:
                ref_lru.move_to_end(k)
            elif len(ref_lru) >= 50:
                ref_lru.popitem(last=False)
            ref_lru[k] = v
        else:
            got = lru.get(k)
            want = ref_lru.get(k)
            if k in ref_lru:
                ref_lru.move_to_end(k)
            bad += got != want
            bad += lfu.get(k) != naive.get(k)
    bad += list(ref_lru) != lru._policy.order()
    all_ok &= _check(f"LRU == OrderedDict model; O(1) LFU == O(n) scanning LFU ({bad} mismatches)", bad == 0)

    print("\n--- DEMO 2: eviction-heavy workload, capacity 20,000 ---")
    for name, policy in (("O(1) LFU buckets", LFUPolicy()), ("O(n) scanning LFU", NaiveLFU())):
        c = Cache(20_000, policy)
        for i in range(20_000):
            c.put(i, i)
        start = time.perf_counter()
        for i in range(20_000, 22_000):
            c.put(i, i)                                   # every put evicts
        ms = (time.perf_counter() - start) * 1000
        print(f"      {name:<18}: 2,000 evicting puts in {ms:8.1f} ms")
        if name.startswith("O(1)"):
            fast = ms
        else:
            slow = ms
    all_ok &= _check(f"bucketed LFU is {slow / fast:.0f}x faster at eviction", fast * 10 < slow)

    print("\n--- DEMO 3: 8 threads hammer one cache ---")
    old = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)                           # force frequent preemption

    def hammer(cache) -> tuple[int, str]:
        errors = []

        def worker(seed: int) -> None:
            rng = random.Random(seed)
            try:
                for _ in range(20_000):
                    k = rng.randrange(300)
                    if rng.random() < 0.5:
                        cache.put(k, k)
                    else:
                        cache.get(k)
            except Exception as e:                          # corrupted structure blew up
                errors.append(type(e).__name__)

        ts = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        inner = cache._cache if isinstance(cache, LockedCache) else cache
        order = inner._policy.order()
        consistent = len(order) == len(set(order)) == len(inner) and set(order) == set(inner._data)
        return len(errors), "consistent" if consistent else "CORRUPTED"

    try:
        raw_err, raw_state = hammer(Cache(100))
        locked_err, locked_state = hammer(LockedCache(Cache(100)))
    finally:
        sys.setswitchinterval(old)
    print(f"      unlocked: {raw_err} threads crashed, structure {raw_state}")
    print(f"      locked  : {locked_err} threads crashed, structure {locked_state}")
    all_ok &= _check("locked cache stays consistent", locked_err == 0 and locked_state == "consistent")
    all_ok &= _check("unlocked cache broke", raw_err > 0 or raw_state == "CORRUPTED")

    print("\n--- DEMO 4: 50 concurrent misses on one hot key ---")
    for label, single_flight in (("naive get-then-put", False), ("single-flight", True)):
        lc = LockedCache(Cache(10))
        loads = []
        barrier = threading.Barrier(50)

        def loader(k):
            loads.append(k)
            time.sleep(0.05)                                # slow DB query
            return "row"

        def request() -> None:
            barrier.wait()
            if single_flight:
                lc.get_or_load("hot", loader)
            elif lc.get("hot") is None:
                lc.put("hot", loader("hot"))

        ts = [threading.Thread(target=request) for _ in range(50)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        print(f"      {label:<20}: loader ran {len(loads)} times")
        if single_flight:
            all_ok &= _check("single-flight runs the loader exactly once", len(loads) == 1)
        else:
            naive_loads = len(loads)
    all_ok &= _check("naive version stampedes", naive_loads > 1)
    return all_ok


if __name__ == "__main__":
    ok = run_tests()
    ok &= run_demos()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
