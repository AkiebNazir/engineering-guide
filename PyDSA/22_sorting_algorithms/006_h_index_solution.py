"""
================================================================================
SOLUTION · LeetCode 274 · H-Index                                     [Medium]
https://leetcode.com/problems/h-index/
================================================================================

THE CORE IDEA
--------------
The h-index is the largest `h` such that at least `h` papers each have at
least `h` citations. That definition is naturally checked once the
citations are SORTED descending: after sorting, `citations[i]` (0-indexed)
is the `(i+1)`-th largest citation count. The paper at position `i`
qualifies to be counted toward an h-index of `i+1` exactly when
`citations[i] >= i + 1` -- because sorting descending guarantees every
paper BEFORE it has at least as many citations too, so there really are
`i+1` papers with `>= i+1` citations the moment that single condition
holds. Walk the sorted array from the front; the answer is the largest
`i+1` for which the condition still holds. Because citations are
non-increasing while `i+1` is strictly increasing, `citations[i] - (i+1)`
is non-increasing across the scan -- the condition can only flip from true
to false ONCE, so the scan can stop at the first failure.

    citations.sort(reverse=True)
    h = 0
    for i, c in enumerate(citations):
        if c >= i + 1:
            h = i + 1
        else:
            break
    return h

A second, faster shape exploits a bound the problem doesn't advertise but
is always true: `h` can never exceed `n` (the number of papers) -- you
can't have more than `n` papers with `>= h` citations if there are only
`n` papers total. That turns this into a COUNTING/bucket problem over a
KNOWN, bounded range `[0, n]` instead of a general sort (see Approach 2).


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, don't code it): for every candidate `h` from `n`
down to `0`, count how many papers have `>= h` citations by scanning the
WHOLE array, and return the first `h` for which that count is `>= h`.
O(n^2) time (n candidates, each an O(n) scan), O(1) extra space. Correct
but quadratic -- exactly the naive approach a bounded counting/sorting
insight is meant to beat.

Approach 1 (chosen) -- sort descending, single linear scan with the
early-stop condition above. O(n log n) time (dominated by the sort), O(1)
extra space beyond the sort itself (or O(log n)/O(n) depending on the sort
algorithm's own space, e.g. Timsort). The answer; shown above and coded
below.

Approach 2 -- bucket / counting sort over the bounded range `[0, n]`.
Since `h <= n` always, cap every citation count at `n` (anything citing
more than `n` times is "at least n," which is all that matters), bucket
counts by (capped) citation value, then sweep buckets from `n` down to `0`
accumulating a running total of "papers with at least this many
citations," returning the first `h` where that running total is `>= h`.
O(n) time, O(n) space -- strictly faster than the general sort because the
value range is bounded by `n` itself (an even tighter bound than the
problem's own `citations[i] <= 1000` constraint), the same "exploit a
bounded domain" idea as this topic's counting-sort variant in 002 and
Maximum Gap's bucketing in 007. Coded below and benchmarked against
Approach 1.


================================================================================
STEP BY STEP TRACE
================================================================================
citations = [3, 0, 6, 1, 5]

Approach 1 (sort descending, scan):
    sorted descending: [6, 5, 3, 1, 0]
    i=0: c=6 >= 1? yes -> h=1
    i=1: c=5 >= 2? yes -> h=2
    i=2: c=3 >= 3? yes -> h=3
    i=3: c=1 >= 4? no  -> STOP (early break)
    h = 3  ✓

Approach 2 (bucket sweep, n=5):
    cap each citation at n=5: [3, 0, 5, 1, 5]   (the 6 becomes 5)
    buckets[0..5] = counts of each capped value:
        buckets = [1, 1, 0, 1, 0, 2]
        (one 0, one 1, zero 2s, one 3, zero 4s, two 5s)
    sweep h from 5 down to 0, running total of "papers with >= h citations":
        h=5: total += buckets[5] = 2   -> total=2, 2 >= 5? no
        h=4: total += buckets[4] = 0   -> total=2, 2 >= 4? no
        h=3: total += buckets[3] = 1   -> total=3, 3 >= 3? YES -> return 3
    h = 3  ✓ (matches Approach 1)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time      Space    Mutates input?
    -----------------------------------------------------------------------
    Brute force [priced]              O(n^2)    O(1)      no
    Sort descending + scan ✅         O(n log n) O(1)*     yes (sorts citations)
    Bucket sweep over [0, n] ✅       O(n)      O(n)      no

    * or O(log n)/O(n) depending on the sort algorithm's own auxiliary space.


================================================================================
EDGE CASES
================================================================================
    all zero citations         -> every citations[i] < i+1 immediately at
                                 i=0 (0 >= 1 is false); h stays 0, the loop
                                 breaks on the very first element.
    single paper                -> n=1; h is 1 if citations[0] >= 1, else 0
                                 -- a single highly-cited paper still only
                                 earns h=1 (h can never exceed paper count).
    all citations >= n          -> e.g. citations=[10,10,10], n=3: every
                                 position satisfies c >= i+1, loop runs to
                                 completion without ever breaking, h ends
                                 at n itself -- the maximum possible h-index.
    citations already sorted
    ascending (worst case for
    the naive early exit
    intuition)                  -> sorting handles this identically to any
                                 other order; the O(n log n) sort dominates
                                 regardless of input order (except for an
                                 adaptive sort like Timsort, which can be
                                 faster on already-sorted input).
    n == 0 (per this problem's
    constraints n >= 1, but
    worth naming)                -> h trivially 0, no papers to have any
                                 citations at all.


================================================================================
COMMON MISTAKES
================================================================================
1. Sorting ASCENDING and then indexing incorrectly (off-by-one on whether
   position `i` from the end represents `n - i` remaining papers) --
   ascending sort is usable (LeetCode's own official "Follow up" variant,
   LC 275, assumes sorted-ascending input) but requires the condition
   `citations[i] >= n - i`, easy to get backwards versus the descending
   version's `citations[i] >= i + 1`.
2. Not capping citation counts at `n` in the bucket approach -- citations
   can be as large as 1000 per this problem's constraints while `n` (paper
   count) can be much smaller; an uncapped bucket array sized to the max
   citation value wastes space and, worse, an index `>` the array bound
   crashes if you bucket by RAW value instead of capped value.
3. Continuing the linear scan past the first failure instead of breaking
   early -- still produces the correct answer (since later positions can't
   help), just wastes O(n) extra work; more importantly, forgetting WHY
   the break is safe (the monotonic non-increasing `citations[i]-(i+1)`
   argument) is the actual interview signal being tested, not just getting
   the right final number.
4. Confusing the h-index condition (`>= h` papers with `>= h` citations
   EACH) with a simpler wrong condition like "sum of citations >= h" or
   "average citations >= h" -- the h-index is about a COUNT of qualifying
   papers, not an aggregate statistic.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "What if citations is already sorted (LC 275)?" -> Then don't re-sort --
  binary search directly on the sorted array for the boundary index where
  `citations[i] >= n - i` first becomes true, O(log n) time instead of
  O(n log n) or O(n). This is exactly topic 05's "search on the answer /
  search on the array" binary-search-on-a-monotone-predicate pattern.
- "Can this be maintained under a stream of NEW citation counts (an
  online h-index)?" -> Yes, with a bucket/count array kept incrementally:
  each new citation event increments one bucket and the running h-index
  can be adjusted by re-sweeping only the small neighborhood around the
  current h, rather than recomputing from scratch -- an amortized approach
  worth sketching if asked, not required for this exact problem.
- "Why is the bucket approach O(n) instead of O(n log n)?" -> Because it
  never does a general comparison sort at all -- it exploits the fact that
  the ANSWER itself (h) is bounded by n, converting an unbounded-range sort
  into a bounded-range count-and-sweep, the same trade this topic makes in
  002's counting-sort variant and in 007's bucket sort for Maximum Gap.


================================================================================
RELATED PROBLEMS
================================================================================
- H-Index II (LC 275) -- the sorted-input variant, solved with binary
  search on the answer instead of a fresh sort (topic 05 territory).
- Sort an Array (LC 912, this topic, 002) -- the counting-sort idea reused
  here as a bucket sweep over a value range bounded by n.
- Maximum Gap (LC 164, this topic, 007) -- another bucket/pigeonhole
  argument: here the bound is "h <= n," there it's "the max gap can't be
  smaller than a derived bucket width."
- Kth Largest Element (topic 27, Quickselect) -- a different way to avoid
  a full sort when only ONE rank/threshold of the data is actually needed.
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def hIndex(self, citations: List[int]) -> int:
        """Sort descending, single linear scan with early stop. O(n log n)
        time, O(1) extra space (beyond the sort). The answer. See THE
        CORE IDEA above."""
        citations = sorted(citations, reverse=True)
        h = 0
        for i, c in enumerate(citations):
            if c >= i + 1:
                h = i + 1
            else:
                break
        return h

    # ------------------------------------------------------------------
    # Variant: bucket sweep over the bounded range [0, n]. O(n) time,
    # O(n) space -- faster than any comparison sort because h can never
    # exceed n.
    # ------------------------------------------------------------------
    def hIndex_bucket(self, citations: List[int]) -> int:
        n = len(citations)
        buckets = [0] * (n + 1)
        for c in citations:
            buckets[min(c, n)] += 1

        total = 0
        for h in range(n, -1, -1):
            total += buckets[h]
            if total >= h:
                return h
        return 0

    # ------------------------------------------------------------------
    # Naive baseline -- priced, not the answer.
    # ------------------------------------------------------------------
    def hIndex_brute_force(self, citations: List[int]) -> int:
        """✗ NAIVE -- O(n^2): for every candidate h from n down to 0,
        rescan the whole array to count qualifying papers."""
        n = len(citations)
        for h in range(n, -1, -1):
            count = sum(1 for c in citations if c >= h)
            if count >= h:
                return h
        return 0


# ==============================================================================
# TESTS -- run:  python 006_h_index_solution.py
# ==============================================================================
CASES = [
    ([3, 0, 6, 1, 5], 3),
    ([1, 3, 1], 1),
    ([0, 0, 0], 0),
    ([100], 1),
    ([0], 0),
    ([10, 10, 10], 3),
    ([1, 2], 1),
    ([25, 8, 5, 3, 3], 3),
    ([1, 1], 1),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: sort descending + scan ---")
    for citations, expected in CASES:
        got = sol.hIndex(list(citations))
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  hIndex({citations}) -> {got} (expected {expected})")

    print("\n--- correctness: bucket sweep, cross-checked ---")
    for citations, expected in CASES:
        got = sol.hIndex_bucket(list(citations))
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  bucket({citations}) -> {got} (expected {expected})")

    print("\n--- correctness: brute force, cross-checked ---")
    for citations, expected in CASES:
        got = sol.hIndex_brute_force(list(citations))
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  brute({citations}) -> {got} (expected {expected})")

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: [3, 0, 6, 1, 5] ---")
    c_sorted = sorted([3, 0, 6, 1, 5], reverse=True)
    print(f"  sorted descending: {c_sorted}")
    h = 0
    for i, c in enumerate(c_sorted):
        cond = c >= i + 1
        print(f"  i={i}: citations[i]={c} >= i+1={i+1}? {'yes -> h='+str(i+1) if cond else 'no -> STOP'}")
        if cond:
            h = i + 1
        else:
            break
    print(f"  final h = {h}")

    # ----------------------------------------------------------------------
    # Randomised cross-check.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check (sort+scan vs bucket vs brute force), 1000 trials ---")
    random.seed(274)
    mismatches = 0
    for _ in range(1000):
        n = random.randint(0, 25)
        citations = [random.randint(0, 1000) for _ in range(n)]
        r1 = sol.hIndex(list(citations))
        r2 = sol.hIndex_bucket(list(citations))
        r3 = sol.hIndex_brute_force(list(citations))
        if not (r1 == r2 == r3):
            mismatches += 1
    print(f"  1000 random arrays: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # Benchmark: O(n) bucket sweep vs O(n log n) sort+scan.
    # ----------------------------------------------------------------------
    print("\n--- O(n) bucket sweep vs O(n log n) sort+scan: measured runtime ---")
    print(f"  {'n':>10} {'sort+scan':>12} {'bucket':>12} {'ratio':>8}")
    random.seed(9)
    for n in (20_000, 80_000, 320_000):
        citations = [random.randint(0, 1000) for _ in range(n)]
        t0 = time.perf_counter(); sol.hIndex(list(citations)); t1 = time.perf_counter()
        sol.hIndex_bucket(list(citations)); t2 = time.perf_counter()
        ss_ms = (t1 - t0) * 1000
        bk_ms = (t2 - t1) * 1000
        ratio = ss_ms / bk_ms if bk_ms > 0 else float("inf")
        print(f"  {n:>10} {ss_ms:>10.2f}ms {bk_ms:>10.2f}ms {ratio:>7.2f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
