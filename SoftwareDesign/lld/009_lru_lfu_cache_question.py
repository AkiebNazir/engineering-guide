"""
================================================================================
LLD 009 · LRU / LFU Cache with Pluggable Eviction                  [Tier 1]
Time box: 45 minutes (5 clarify · 7 model · 5 API · 20 code · 8 extend)
================================================================================

PROBLEM
-------
Design and implement an in-process cache library with pluggable eviction.

The interviewer starts with "implement an LRU cache" and, once that works,
asks "now make eviction pluggable, add LFU, TTL, and make it thread-safe."
These are the agreed requirements.

REQUIREMENTS
------------
  1. Cache(capacity, policy=None, ttl_s=None, clock=time.monotonic, on_evict=None)
     capacity < 1 -> ValueError. Default policy: LRUPolicy().
  2. get(key, default=None), put(key, value), delete(key) -> bool,
     `key in cache`, len(cache). All O(1).
  3. put() on an existing key updates the value, counts as an access, and
     never evicts. put() of a new key into a full cache first evicts
     policy's victim, then calls on_evict(key, value) for it.
  4. Policies (each hook O(1)): on_insert(key), on_access(key),
     on_remove(key), victim() -> key.
        LRUPolicy   least recently used (write your own doubly linked list)
        LFUPolicy   least frequently used; ties -> least recently used.
                    frequency(key) -> int. put counts 1, each get/put +1.
        FIFOPolicy  oldest insertion; accesses don't matter.
     LFU must stay correct when delete() removes the only key with the
     current minimum frequency.
  5. TTL: an entry expires at put_time + ttl_s. get() at or after that time is
     a miss; the entry is removed.
  6. cache.stats has hits, misses, evictions, expirations. An expired get
     counts as a miss AND an expiration.
  7. LockedCache(cache): thread-safe get/put/delete/len, plus
     get_or_load(key, loader): on a miss calls loader(key), caches and returns
     the result. Concurrent callers for the same missing key must call the
     loader ONCE (the others wait). If the loader raises, the exception
     reaches the caller and nothing is cached.

  Out of scope: byte-size limits, distributed caching.

WHAT THE INTERVIEWER IS LOOKING FOR
-----------------------------------
  * Which structure gives O(1) LRU? O(1) LFU (not a heap)?
  * Where does the eviction decision live so the cache doesn't branch on type?
  * Is get() a read operation for locking purposes?
  * What is a cache stampede and how do you prevent it?

FOLLOW-UPS TO PREPARE
---------------------
  byte-weighted capacity · lock striping · CLOCK / sampled LRU · distributed
  cache · refresh-ahead · negative caching · stale-while-revalidate.

THE API BELOW IS FIXED so the tests at the bottom can run against your code.
Run this file: all checks should print PASS, then ALL PASSED.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable, Hashable


class LRUPolicy:
    def __init__(self) -> None:
        raise NotImplementedError


class LFUPolicy:
    def __init__(self) -> None:
        raise NotImplementedError

    def frequency(self, key: Hashable) -> int:
        raise NotImplementedError


class FIFOPolicy:
    def __init__(self) -> None:
        raise NotImplementedError


@dataclass(slots=True)
class Stats:
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0


class Cache:
    def __init__(self, capacity: int, policy=None, ttl_s: float | None = None,
                 clock: Callable[[], float] = time.monotonic, on_evict=None) -> None:
        self.stats = Stats()
        # YOUR CODE HERE
        raise NotImplementedError

    def get(self, key, default=None): raise NotImplementedError
    def put(self, key, value) -> None: raise NotImplementedError
    def delete(self, key) -> bool: raise NotImplementedError
    def __contains__(self, key) -> bool: raise NotImplementedError
    def __len__(self) -> int: raise NotImplementedError


class LockedCache:
    def __init__(self, cache: Cache) -> None:
        raise NotImplementedError

    def get(self, key, default=None): raise NotImplementedError
    def put(self, key, value) -> None: raise NotImplementedError
    def delete(self, key) -> bool: raise NotImplementedError
    def __len__(self) -> int: raise NotImplementedError

    def get_or_load(self, key, loader: Callable[[Hashable], object]):
        raise NotImplementedError


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


if __name__ == "__main__":
    ok = run_tests()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
