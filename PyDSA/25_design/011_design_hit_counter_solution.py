"""
================================================================================
SOLUTION · LeetCode 362 · Design Hit Counter                            [Medium]
https://leetcode.com/problems/design-hit-counter/
================================================================================

THE CORE IDEA
--------------
A sliding window over time, (timestamp - 300, timestamp]. The obvious design,
a queue of hit timestamps, costs memory per HIT. The scalable design keeps 300
circular buckets, one per second, each tagged with the second it belongs to;
stale buckets are reset on write and ignored on read. Memory is fixed at 300
slots regardless of traffic. This is exactly the shape of a real rate limiter
or metrics counter.


================================================================================
APPROACH 1 · Queue of timestamps
================================================================================
    hit(t):      queue.append(t)
    getHits(t):  while queue and queue[0] <= t - 300: queue.popleft()
                 return len(queue)

    hit O(1), getHits O(1) amortized (each hit popped once)
    Memory: O(hits in the last 300 s) — unbounded under heavy traffic


================================================================================
APPROACH 2 · Queue of (second, count) pairs
================================================================================
Collapse hits in the same second into one entry: if the last entry's second is
t, increment its count. Memory becomes O(distinct seconds in window) <= 300,
and getHits keeps a running total. A good middle ground.


================================================================================
APPROACH 3 · 300 circular buckets ✅ (the answer to the follow-up)
================================================================================
    times  = [0] * 300          # which second each slot currently represents
    counts = [0] * 300

    hit(t):
        i = t % 300
        if times[i] != t:       # slot holds an older second: recycle it
            times[i] = t
            counts[i] = 0
        counts[i] += 1

    getHits(t):
        return sum(c for s, c in zip(times, counts) if t - s < 300)

WHY `t - s < 300`. The window is (t - 300, t], i.e. s > t - 300, i.e.
t - s < 300. A slot from exactly 300 seconds ago is OUT.

WHY RESETTING ON WRITE IS SAFE. Slot i represents seconds congruent to i mod
300. If it holds second s != t with the same residue, then s <= t - 300, so its
hits are already outside every future window.

    hit O(1), getHits O(300) = O(1) for a fixed window
    Memory: O(300), independent of traffic


================================================================================
STEP BY STEP TRACE · hits at 1, 2, 3, 300; queries at 4, 300, 301 (buckets)
================================================================================
    hit(1)   slot 1:   times=1   count=1
    hit(2)   slot 2:   times=2   count=1
    hit(3)   slot 3:   times=3   count=1
    getHits(4):   slots 1,2,3 have 4 - s < 300                  -> 3
    hit(300) slot 0:   times=300 count=1
    getHits(300): slots 0,1,2,3: 300-300, 300-1=299 < 300 ...    -> 4
    getHits(301): slot 1: 301 - 1 = 300, NOT < 300 -> excluded   -> 3


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                   hit     getHits          Memory               Mutates input?
    -------------------------  ------  ---------------  -------------------  --------------
    Queue of timestamps        O(1)    O(1) amortized   O(hits in window)    n/a
    Queue of (second, count)   O(1)    O(1) amortized   O(<= 300)            n/a
    Circular buckets ✅        O(1)    O(300)           O(300)               n/a


================================================================================
EDGE CASES
================================================================================
    Many hits in one second     Buckets: one slot, count grows.
    Hit exactly 300 s ago       Excluded (half-open window).
    Long idle gap               Every slot is stale; getHits returns 0 without
                                clearing anything.
    getHits before any hit      0.
    Same-second hit after query Still counted (queries don't mutate buckets).


================================================================================
COMMON MISTAKES
================================================================================
1. Off-by-one on the window: counting hits with t - s <= 300. getHits(301)
   returns 4 instead of 3 in the LC example. Demo below.

2. In the bucket design, forgetting to compare the slot's second on READ, so
   hits from 300+ seconds ago with the same residue get counted. Demo below.

3. Resetting all 300 buckets on every call ("clean up old data"). Correct but
   O(300) per hit for no reason.

4. Assuming "at most 300 calls" means the queue is fine for the follow-up. The
   follow-up explicitly asks about huge hit rates.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Hits arrive out of order (up to a few seconds late)?
A: Buckets handle it naturally as long as the late hit is still inside the
   window: find slot t % 300, check its time tag. Queues need insertion.

Q: Thread safety?
A: A single lock around hit/getHits, or per-slot atomic counters with a
   compare-and-swap on the time tag. Readers can tolerate slight staleness.

Q: Distributed: many servers count hits for the same key?
A: Per-server bucket counters aggregated periodically, or a shared store with
   INCR on a key like "hits:{key}:{second}" and EXPIRE 300, summing the last
   300 keys. This is the sliding-window counter from the rate limiter design.

Q: Window of 1 hour at millisecond granularity?
A: Don't keep 3.6 million buckets: use coarser buckets (e.g. 1 second) and
   accept approximation at the edges, or a two-level scheme.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 359   Logger Rate Limiter (003)
    LC 933   Number of Recent Calls           — the queue version exactly
    LC 1604  Alert Using Same Key-Card Three or More Times in a One Hour Period
    SystemDesign/problems/002 Rate Limiter    — the distributed version
================================================================================
"""

import random
import time
import tracemalloc
from collections import deque
from typing import Deque, List


class HitCounter:
    """300 circular buckets tagged with their second."""

    WINDOW = 300

    def __init__(self):
        self.times: List[int] = [0] * self.WINDOW
        self.counts: List[int] = [0] * self.WINDOW

    def hit(self, timestamp: int) -> None:
        i = timestamp % self.WINDOW
        if self.times[i] != timestamp:
            self.times[i] = timestamp
            self.counts[i] = 0
        self.counts[i] += 1

    def getHits(self, timestamp: int) -> int:
        total = 0
        for s, c in zip(self.times, self.counts):
            if timestamp - s < self.WINDOW:
                total += c
        return total


# ------------------------------------------------------------------------
# Alternatives / broken versions for the demos.
# ------------------------------------------------------------------------
class HitCounterQueue:
    def __init__(self):
        self.q: Deque[int] = deque()

    def hit(self, timestamp: int) -> None:
        self.q.append(timestamp)

    def getHits(self, timestamp: int) -> int:
        while self.q and self.q[0] <= timestamp - 300:
            self.q.popleft()
        return len(self.q)


class HitCounterPairs:
    def __init__(self):
        self.q: Deque[List[int]] = deque()     # [second, count]
        self.total = 0

    def hit(self, timestamp: int) -> None:
        if self.q and self.q[-1][0] == timestamp:
            self.q[-1][1] += 1
        else:
            self.q.append([timestamp, 1])
        self.total += 1

    def getHits(self, timestamp: int) -> int:
        while self.q and self.q[0][0] <= timestamp - 300:
            self.total -= self.q.popleft()[1]
        return self.total


class HitCounterOffByOneBug(HitCounterQueue):
    """Mistake 1: keeps hits exactly 300 seconds old."""

    def getHits(self, timestamp: int) -> int:
        while self.q and self.q[0] < timestamp - 300:        # BUG: should be <=
            self.q.popleft()
        return len(self.q)


class HitCounterNoReadCheckBug(HitCounter):
    """Mistake 2: sums every bucket without checking its time tag."""

    def getHits(self, timestamp: int) -> int:
        return sum(self.counts)                               # BUG


# ==============================================================================
# TESTS — run:  python 011_design_hit_counter_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    print("--- correctness: buckets vs queue vs (second, count) queue ---")
    for cls in (HitCounter, HitCounterQueue, HitCounterPairs):
        hc = cls()
        hc.hit(1); hc.hit(2); hc.hit(3)
        got = [hc.getHits(4)]
        hc.hit(300)
        got += [hc.getHits(300), hc.getHits(301)]
        hc2 = cls()
        for _ in range(5):
            hc2.hit(100)
        got2 = [hc2.getHits(100), hc2.getHits(399), hc2.getHits(400), hc2.getHits(10_000)]
        ok = got == [3, 4, 3] and got2 == [5, 5, 0, 0]
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {cls.__name__:<16} LC example {got}  burst {got2}")

    print("\n--- randomized cross-check (300 scripts, chronological) ---")
    rng = random.Random(362)
    bad = 0
    for _ in range(300):
        impls = (HitCounter(), HitCounterQueue(), HitCounterPairs())
        t = rng.randint(1, 1000)
        for _ in range(rng.randint(1, 300)):
            t += rng.choice((0, 0, 1, 5, 60, 299, 300, 301, 900))
            if rng.random() < 0.6:
                for impl in impls:
                    impl.hit(t)
            else:
                if len({impl.getHits(t) for impl in impls}) != 1:
                    bad += 1
                    break
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  all three designs agree on 300 random scripts")

    print("\n--- mistakes LIVE ---")
    bug = HitCounterOffByOneBug()
    bug.hit(1); bug.hit(2); bug.hit(3); bug.hit(300)
    w = bug.getHits(301)
    ok = w == 4
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  window [t-300, t] instead of (t-300, t]: getHits(301) -> {w} (want 3)")
    bug2 = HitCounterNoReadCheckBug()
    bug2.hit(5)
    w2 = bug2.getHits(1000)
    ok = w2 == 1
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  no time-tag check on read: hit(5), getHits(1000) -> {w2} (want 0)")

    print("\n--- the follow-up: 1,000,000 hits in one window ---")
    for name, cls in (("queue of timestamps ", HitCounterQueue), ("(second, count) pairs", HitCounterPairs),
                      ("300 buckets          ", HitCounter)):
        tracemalloc.start()
        hc = cls()
        t0 = time.perf_counter()
        for i in range(1_000_000):
            hc.hit(1_000 + i // 5_000)          # 5,000 hits per second for 200 seconds
        dt = time.perf_counter() - t0
        n = hc.getHits(1_199)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        all_ok &= n == 1_000_000
        print(f"      {name}  peak memory {peak / 1024:10.1f} KiB   1M hits in {dt * 1000:6.0f} ms   getHits={n:,}")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
