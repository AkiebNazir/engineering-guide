"""
================================================================================
SOLUTION · LeetCode 933 · Number of Recent Calls                        [Easy]
https://leetcode.com/problems/number-of-recent-calls/
================================================================================

THE CORE IDEA
--------------
A queue used as a sliding COUNT (topic guide §5): every ping enqueues its
timestamp, and before answering, evict everything from the FRONT that has
aged out of the [t - 3000, t] window.

    q = deque()

    def ping(t):
        q.append(t)
        while q and q[0] < t - 3000:
            q.popleft()
        return len(q)

Because ping() is guaranteed to be called with STRICTLY INCREASING `t`, the
front of the queue is always the oldest surviving timestamp — there's never
a need to look past the front, because everything behind it is even newer
and therefore even more clearly still in-window. This is what licenses
checking only `q[0]` rather than scanning the whole queue.


================================================================================
THE AMORTIZED ARGUMENT — same shape as topic 03's sliding window
================================================================================
Each timestamp is APPENDED to the queue exactly once (when its own ping()
call happens) and POPPED from the queue AT MOST once (when it eventually
ages out, if ever). So across n total calls to ping(), the total number of
enqueue + dequeue operations is at most 2n — O(n) over the WHOLE run, i.e.
O(1) amortized per call. Any individual ping() might evict several stale
timestamps at once (if there's a long gap since the last call), but that
cost is paid for by calls that AREN'T doing any eviction — exactly topic
03's "bounded total movement across the whole run, not per iteration"
argument, restated for a queue instead of two pointers into an array.


================================================================================
STEP BY STEP TRACE
================================================================================
ping(1), ping(100), ping(3001), ping(3002)

    call         window            queue before evict      evict?          queue after      return
    ping(1)      [-2999, 1]        []                       -               [1]              1
    ping(100)    [-2900, 100]      [1]                       1 >= -2900, no  [1, 100]         2
    ping(3001)   [1, 3001]         [1, 100]                   1 >= 1, no      [1,100,3001]     3
    ping(3002)   [2, 3002]         [1,100,3001,3002]           1 < 2, EVICT 1  [100,3001,3002]  3

At ping(3002), timestamp 1 falls out because 1 < 3002 - 3000 = 2 — the
window's lower bound moved past it. 100 survives because 100 >= 2.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                                Time/call         Total (n calls)  Space   Mutates input?
    ---------------------------------------  ----------------  ---------------  ------  ---------------
    List, scan+count every call               O(n)               O(n^2)           O(n)    n/a
    List, evict with list.pop(0)                O(1) amortized*    O(n) total*      O(n)    n/a  — correct
                                                (but pop(0) itself                            but O(n) per
                                                is O(n) per call it                            eviction call
                                                DOES evict)
    Deque, evict with popleft() (answer) ✅    O(1) amortized      O(n) total       O(n)    n/a


================================================================================
EDGE CASES
================================================================================
    First call ever                     -> queue starts empty; nothing to
                                            evict; returns 1.
    t exactly at the boundary           -> [t-3000, t] is INCLUSIVE; a
                                            timestamp equal to t-3000 must
                                            be KEPT, not evicted. Eviction
                                            condition must be strict `<`,
                                            not `<=`.
    Many calls within one window        -> queue only grows, no eviction;
                                            exercises the "no-op while loop"
                                            path repeatedly.
    Large gap between two calls          -> one call may evict MANY
                                            timestamps at once (the `while`,
                                            not `if`, matters here).
    t values spanning > 10^9              -> plain int arithmetic in Python
                                            has no overflow concern, unlike
                                            fixed-width integer languages.


================================================================================
COMMON MISTAKES
================================================================================
1. Using `<=` instead of `<` for the eviction condition — incorrectly
   evicts a timestamp that is exactly at the window's inclusive lower
   bound, undercounting.

2. Using `if` instead of `while` for the eviction loop — only evicts (at
   most) one stale timestamp per call, leaving multiple stale entries
   behind after a large gap between calls.

3. Scanning the entire queue/list to COUNT matches on every call instead of
   maintaining the queue as exactly "the current window's contents" —
   correct but O(n) per call instead of O(1) amortized.

4. Using `list.pop(0)` for eviction instead of `collections.deque.popleft()`
   — still correct, but O(n) per eviction instead of O(1), reintroducing a
   quadratic total cost. See the benchmark below.

5. Reaching for `deque(maxlen=k)` — this bounds the number of ELEMENTS, not
   a time WINDOW. Since ping() intervals are irregular (arbitrary gaps
   between calls), a fixed element count doesn't correspond to a fixed time
   span; this problem genuinely needs value-based eviction, not
   count-based.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if timestamps could arrive OUT OF ORDER (not strictly increasing)?
A: The front-only eviction check breaks — an out-of-order insert could
   leave a stale timestamp buried behind a newer one at the front. You'd
   need either a sorted structure (e.g. a balanced BST / sorted list with
   bisect for O(log n) insert) or to fall back to scanning.

Q: What if you needed to support REMOVING a specific past call, not just
   querying counts?
A: A plain queue doesn't support arbitrary removal in O(1); you'd need an
   indexed structure (e.g. a doubly linked list with a hashmap of node
   references, the mechanism behind LC 146 LRU Cache) to remove by key
   in O(1).

Q: How would you generalize this to "count requests in the last W
   milliseconds" for a caller-supplied W per query, not a fixed 3000?
A: The same queue + front-eviction mechanism works verbatim — just pass W
   into each call and evict while `q[0] < t - W`. The amortized argument is
   unaffected by W being fixed or variable per call.

Q: Could you use `deque(maxlen=...)` at all here in a clever way?
A: Not directly, because the window is time-bounded, not count-bounded —
   but if the problem instead asked "count requests among the last N
   calls" (a count-based window, not a time-based one), `maxlen=N` would
   be exactly the right tool and would need zero manual eviction logic.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 239  Sliding Window Maximum        — topic 03 problem 014, a
                                            monotonic deque over VALUES
                                            rather than a FIFO count
    LC 862  Shortest Subarray Sum >= K    — problem 006 here, prefix sums +
                                            a monotonic deque, the hard
                                            capstone of this topic
    LC 346  Moving Average from Data Stream — nearly identical shape:
                                            fixed-size window (count-based,
                                            not time-based), a natural fit
                                            for deque(maxlen=size)
================================================================================
"""

import time
from collections import deque
from typing import List


class RecentCounter:
    """Queue as a sliding time window. See THE CORE IDEA above.
    O(1) amortized per call; O(n) total across n calls."""

    def __init__(self):
        self.q: deque = deque()

    def ping(self, t: int) -> int:
        self.q.append(t)
        while self.q and self.q[0] < t - 3000:
            self.q.popleft()
        return len(self.q)


class RecentCounterScanBrute:
    """O(n) per call: keep every timestamp, COUNT matches with a full scan
    on every ping(). Correct, but O(n^2) total across n calls. Used only as
    the oracle and the benchmark baseline."""

    def __init__(self):
        self.calls: List[int] = []

    def ping(self, t: int) -> int:
        self.calls.append(t)
        return sum(1 for x in self.calls if x >= t - 3000)


class RecentCounterListPop0:
    """✗ Deliberately using list.pop(0) instead of deque.popleft() for
    eviction. Still correct — evicts the same elements — but each eviction
    itself is O(n), reintroducing a quadratic total. Used only in the
    benchmark below."""

    def __init__(self):
        self.calls: List[int] = []

    def ping(self, t: int) -> int:
        self.calls.append(t)
        while self.calls and self.calls[0] < t - 3000:
            self.calls.pop(0)                     # O(n) shift, every eviction
        return len(self.calls)


# ==============================================================================
# TESTS — run:  python 003_number_of_recent_calls_solution.py
# ==============================================================================
def run_tests() -> None:
    passed = 0
    total = 0

    def check(name, got, want):
        nonlocal passed, total
        total += 1
        ok = got == want
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {name:<48} got={got!r}  want={want!r}")

    print("--- correctness ---")
    rc = RecentCounter()
    check("ping(1)", rc.ping(1), 1)
    check("ping(100)", rc.ping(100), 2)
    check("ping(3001)", rc.ping(3001), 3)
    check("ping(3002)", rc.ping(3002), 3)

    rc2 = RecentCounter()
    check("inclusive boundary: ping(3000)", rc2.ping(3000), 1)
    check("inclusive boundary: ping(6000)", rc2.ping(6000), 2)
    check("exclusive boundary: ping(6001)", rc2.ping(6001), 2)

    # ----------------------------------------------------------------------
    # Randomised cross-check vs the scan-brute oracle.
    # ----------------------------------------------------------------------
    import random
    print("\n--- randomised cross-check vs O(n) scan-brute oracle ---")
    random.seed(5)
    mismatches = 0
    trials = 300
    for _ in range(trials):
        rc = RecentCounter()
        brute = RecentCounterScanBrute()
        t = 0
        for _ in range(random.randint(1, 30)):
            t += random.randint(1, 5000)          # strictly increasing
            got = rc.ping(t)
            want = brute.ping(t)
            if got != want:
                mismatches += 1
    print(f"  {trials} randomised sequences: {mismatches} mismatches")
    all_ok = passed == total and mismatches == 0

    # ----------------------------------------------------------------------
    # Trace, printed.
    # ----------------------------------------------------------------------
    print("\n--- trace: ping(1), ping(100), ping(3001), ping(3002) ---")
    rc = RecentCounter()
    for t in (1, 100, 3001, 3002):
        before = list(rc.q)
        result = rc.ping(t)
        print(f"  ping({t:>5}) window=[{t-3000},{t}]  before={before}  "
              f"after={list(rc.q)}  -> {result}")

    # ----------------------------------------------------------------------
    # Runtime demo: deque O(n) total vs list-scan O(n^2) total.
    # ----------------------------------------------------------------------
    print("\n--- deque sliding window (amortized O(1)/call) vs O(n) scan/call: measured ---")
    print(f"  {'n calls':>8} {'deque ms':>10} {'scan ms':>10} {'ratio':>8}")
    for n in (1_000, 4_000, 10_000):
        # All calls within a dense enough range that the queue holds many
        # elements at once (worst case for both approaches: nothing evicts).
        times = list(range(1, n + 1))              # 1ms apart, all within 3000ms of each other eventually

        rc = RecentCounter()
        t0 = time.perf_counter()
        for t in times:
            rc.ping(t)
        t1 = time.perf_counter()

        brute = RecentCounterScanBrute()
        t2 = time.perf_counter()
        for t in times:
            brute.ping(t)
        t3 = time.perf_counter()

        d_ms = (t1 - t0) * 1000
        s_ms = (t3 - t2) * 1000
        ratio = s_ms / d_ms if d_ms > 0 else float("inf")
        print(f"  {n:>8} {d_ms:>9.2f}  {s_ms:>9.2f}  {ratio:>7.1f}x")

    # ----------------------------------------------------------------------
    # deque.popleft() vs list.pop(0) for eviction specifically.
    #
    # Workload: repeated "burst then flush" rounds. Each round pings B times
    # 1ms apart (grows the window to B elements), then one ping 3001ms later
    # that evicts almost the whole burst in a single call's while loop. This
    # is exactly where list.pop(0)'s O(current length) cost per individual
    # pop matters: within one flush call, the list SHRINKS by one each
    # pop(0), and each of those pops still shifts the remaining elements.
    # ----------------------------------------------------------------------
    print("\n--- deque.popleft() vs list.pop(0) for eviction: measured ---")
    print(f"  {'rounds x burst':>16} {'deque ms':>10} {'list.pop(0) ms':>16} {'ratio':>8}")
    for rounds, burst in ((20, 1_000), (20, 2_000), (20, 4_000)):
        times = []
        t = 0
        for _ in range(rounds):
            for _ in range(burst):
                t += 1
                times.append(t)
            t += 3001                          # flush ping: evicts the whole burst
            times.append(t)

        rc = RecentCounter()
        t0 = time.perf_counter()
        for x in times:
            rc.ping(x)
        t1 = time.perf_counter()

        rc_slow = RecentCounterListPop0()
        t2 = time.perf_counter()
        for x in times:
            rc_slow.ping(x)
        t3 = time.perf_counter()

        d_ms = (t1 - t0) * 1000
        l_ms = (t3 - t2) * 1000
        ratio = l_ms / d_ms if d_ms > 0 else float("inf")
        print(f"  {f'{rounds}x{burst}':>16} {d_ms:>9.2f}  {l_ms:>15.2f}  {ratio:>7.1f}x")
    print("  Both approaches still evict each timestamp exactly once overall")
    print("  (O(n) TOTAL pops either way), but list.pop(0) costs O(current")
    print("  length) PER pop within a flush's while loop, so a burst of size")
    print("  B costs list ~O(B^2) for that one flush call vs deque's O(B).")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
