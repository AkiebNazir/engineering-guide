"""
================================================================================
SOLUTION · LeetCode 528 · Random Pick with Weight                   [Medium]
https://leetcode.com/problems/random-pick-with-weight/
================================================================================

THE CORE IDEA
--------------
Build a prefix-sum array of the weights: `prefix[i] = w[0] + w[1] + ... +
w[i]`. Because every weight is positive, `prefix` is strictly increasing --
it partitions the range [1, total] into n consecutive, non-overlapping
"buckets," where bucket i is exactly the w[i] integers
(prefix[i-1]+1 .. prefix[i]) (with prefix[-1] treated as 0). Draw ONE
uniform random integer `target` in [1, total], then binary search for the
first bucket boundary >= target -- that bucket's index is the answer.
Since bucket i's WIDTH is exactly w[i], and target is drawn uniformly over
the whole [1, total] line, P(land in bucket i) = w[i] / total exactly.

O(n) time to build the prefix sums once in __init__, O(log n) time per
pickIndex() call via binary search (`bisect_left`).


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (linear scan per pick, price it): draw target in [1, total],
then walk the prefix array left to right until you find the first entry
>= target. Also correct -- same partitioning logic -- but O(n) time PER
pickIndex() call instead of O(log n), since prefix is sorted and a linear
scan throws that away. See the runtime demo below for exactly how much
slower this becomes as n and the number of pick() calls both grow.

Approach 1 (chosen) -- prefix sum + binary search (`bisect_left`). O(n)
one-time preprocessing, O(log n) per call. This is what `pickIndex()`
implements; `_pick_linear_scan` exists only to power the timing comparison.


================================================================================
STEP BY STEP TRACE
================================================================================
w = [1, 3, 2]. prefix = [1, 4, 6]. total = 6.

Bucket boundaries on the line [1, 6]:
    index 0: [1, 1]        width 1  (w[0] = 1)
    index 1: [2, 4]        width 3  (w[1] = 3)
    index 2: [5, 6]        width 2  (w[2] = 2)

pickIndex() draws target = random.randint(1, 6), say target = 3.
bisect_left(prefix, 3) on prefix=[1, 4, 6]:
    prefix[0]=1 < 3, prefix[1]=4 >= 3 -> insertion point 1
    return index 1

target=3 falls inside bucket 1's range [2,4], correctly landing on
index 1 (which has bucket width 3, i.e. P(index 1) = 3/6 = 1/2).

A few more draws to see the mapping:
    target=1 -> bisect_left([1,4,6], 1) = 0   -> index 0
    target=5 -> bisect_left([1,4,6], 5) = 2   -> index 2
    target=6 -> bisect_left([1,4,6], 6) = 2   -> index 2


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time (per call)   Space   Mutates input?
    ----------------------------  ----------------  ------  --------------
    Linear scan [priced]           O(n)              O(n)    no
    Binary search [chosen]         O(log n)          O(n)    no
    (both pay O(n) once in __init__ for the prefix array itself)


================================================================================
EDGE CASES
================================================================================
    single weight (w = [x])   -> total = x, every draw in [1, x] maps to
                                 index 0, always returns 0.
    all weights equal          -> degenerates to uniform random pick,
                                 same as problem 002's uniform case.
    one weight vastly larger than the rest -> its bucket dominates the
                                 [1, total] line; correctness still holds,
                                 just a skewed but CORRECT distribution.
    w[i] up to 10^5, n up to 10^4 -> total can reach ~10^9, still well
                                 within Python's unbounded int range and
                                 random.randint's supported range.


================================================================================
COMMON MISTAKES
================================================================================
1. Using `bisect_right` instead of `bisect_left` (or vice versa) without
   checking which one is consistent with your bucket convention
   (prefix[i-1]+1 .. prefix[i], 1-indexed target) -- either can be made to
   work, but MIXING conventions (e.g. 0-indexed target with bisect_left)
   silently shifts every bucket boundary by one and biases small weights.
2. Drawing a fresh random number per WEIGHT and doing independent coin
   flips per index instead of ONE draw over the total -- does not produce
   the correct joint distribution (weights don't compose that way).
3. Forgetting weights are guaranteed POSITIVE (not just non-negative) --
   the strictly-increasing-prefix assumption that binary search relies on
   would break silently if a zero weight were allowed to create a
   zero-width "bucket" that binary search could still (correctly) skip,
   but the reasoning is worth re-checking if constraints ever changed.
4. Re-summing the weights (or re-building the prefix array) on every
   pickIndex() call instead of once in __init__ -- turns O(log n) per call
   back into O(n) per call, defeating the whole point of precomputing.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Why binary search instead of a linear scan?" -> prefix is sorted by
  construction (weights are positive), so binary search is a strict
  improvement with no downside -- O(log n) vs O(n) per call, see the
  measured demo below.
- "What if weights could be updated dynamically?" -> a Fenwick tree
  (binary indexed tree) supports O(log n) weight updates AND O(log n)
  weighted picks, trading a bit of complexity for that flexibility (this
  curriculum's topic 26 covers Fenwick trees).
- "What if w[i] could be a float?" -> same algorithm; prefix sums and
  binary search don't care whether entries are ints or floats, just that
  they're positive and the array is sorted.


================================================================================
RELATED PROBLEMS
================================================================================
- 002 Random Pick Index (LC 398) -- uniform sampling, the degenerate
  equal-weights case of this problem.
- 001 Shuffle an Array (LC 384) -- a different randomized technique
  (Fisher-Yates) with its own uniformity proof.
- 04_prefix_sum topic -- the general prefix-sum pattern this problem reuses
  for a NEW purpose (partitioning a probability line, not range-sum queries).
================================================================================
"""

import bisect
import random
import time


class Solution:
    def __init__(self, w: list[int]):
        self.prefix = []
        running = 0
        for weight in w:
            running += weight
            self.prefix.append(running)
        self.total = running

    def pickIndex(self) -> int:
        target = random.randint(1, self.total)
        return bisect.bisect_left(self.prefix, target)


def _pick_linear_scan(prefix: list[int], total: int) -> int:
    """The O(n)-per-call alternative: walk the prefix array linearly
    instead of binary searching it."""
    target = random.randint(1, total)
    for i, p in enumerate(prefix):
        if p >= target:
            return i
    return len(prefix) - 1


def run_tests() -> None:
    all_ok = True

    sol = Solution([1])
    for _ in range(5):
        got = sol.pickIndex()
        ok = got == 0
        all_ok &= ok
        if not ok:
            print(f"FAIL  single-weight pickIndex() -> {got}  (want 0)")
            break
    else:
        print("PASS  single-weight list always returns index 0")

    sol2 = Solution([1, 3])
    valid = {0, 1}
    for _ in range(30):
        got = sol2.pickIndex()
        if got not in valid:
            all_ok = False
            print(f"FAIL  pickIndex() -> {got} not in {valid}")
            break
    else:
        print(f"PASS  30 pickIndex() calls all in {valid}")

    # Weighted frequency check: [1, 3] over many trials should land on
    # index 1 roughly 3x as often as index 0 (weights 1 and 3, total 4).
    from collections import Counter
    trials = 40_000
    counts = Counter(sol2.pickIndex() for _ in range(trials))
    ratio = counts[1] / counts[0]
    ratio_ok = 2.5 < ratio < 3.5  # expect ~3.0
    all_ok &= ratio_ok
    print(f"{'PASS' if ratio_ok else 'FAIL'}  index1/index0 frequency ratio "
          f"= {ratio:.2f}  (want ~3.0 for weights [1, 3])")

    print()
    print("RUNTIME DEMO -- binary search vs linear scan pick, measured live")
    print("-" * 72)
    n = 5000
    weights = [random.randint(1, 100) for _ in range(n)]
    sol_big = Solution(weights)
    calls = 20_000

    t0 = time.perf_counter()
    for _ in range(calls):
        sol_big.pickIndex()
    bsearch_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    for _ in range(calls):
        _pick_linear_scan(sol_big.prefix, sol_big.total)
    linear_ms = (time.perf_counter() - t0) * 1000

    print(f"n={n} weights, {calls} pick calls each:")
    print(f"  binary search (bisect_left): {bsearch_ms:8.2f} ms")
    print(f"  linear scan:                 {linear_ms:8.2f} ms")
    print(f"  ratio: linear scan is {linear_ms / bsearch_ms:.1f}x slower")

    speedup_confirmed = linear_ms > bsearch_ms
    all_ok &= speedup_confirmed
    print(f"{'PASS' if speedup_confirmed else 'FAIL'}  "
          f"binary search measurably faster than linear scan at this scale")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
