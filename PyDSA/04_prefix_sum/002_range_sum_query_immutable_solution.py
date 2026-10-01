"""
================================================================================
SOLUTION · LeetCode 303 · Range Sum Query - Immutable                   [Easy]
https://leetcode.com/problems/range-sum-query-immutable/
================================================================================

THE CORE IDEA
--------------
Precompute a prefix-sum array ONCE, in the constructor. Every `sumRange`
call afterward is a single subtraction, per the topic guide §1.0:

    sum(nums[l..r]) = prefix[r+1] - prefix[l]

    class NumArray:
        def __init__(self, nums):
            self.prefix = [0] * (len(nums) + 1)
            for i, x in enumerate(nums):
                self.prefix[i + 1] = self.prefix[i] + x

        def sumRange(self, left, right):
            return self.prefix[right + 1] - self.prefix[left]

O(n) once in `__init__`, O(1) per `sumRange` call forever after. This is THE
flagship demonstration of the topic's central trade: pay preprocessing cost
once, amortize it across many cheap queries. The array name is "Immutable"
in the problem title for a reason — `nums` never changes after construction,
so a precomputed prefix array never goes stale. (Contrast: LC 307 "Range Sum
Query - Mutable" needs a Fenwick tree / segment tree instead, because a
plain prefix array would need a full O(n) rebuild after every update — out
of scope for this topic, see topic 26.)


================================================================================
MULTIPLE APPROACHES
================================================================================

APPROACH 0 · NAIVE — RE-SUM EVERY QUERY (priced, then coded and benchmarked)
    Store `nums` as-is. Each `sumRange(left, right)` call does
    `sum(nums[left:right+1])`, which is O(right - left) — worst case O(n).
    Cheap to build (`__init__` is O(1) or O(n) just to copy the list), but
    every query re-does work the array never changes between calls. Over Q
    queries this is O(n * Q) in the worst case. It is trivial to code, so we
    code it and MEASURE the gap against the prefix version below — this is
    the demo the topic guide calls "the trap" in Part 4's complexity table
    ("Recompute sum(a[l:r+1]) per query — O(r-l) — the trap: O(nq) over q
    queries").

APPROACH 1 · PREFIX SUM ARRAY ✅ (the answer)
    Build `prefix` once in `__init__` (O(n)), answer every `sumRange` in
    O(1). See THE CORE IDEA above.


================================================================================
STEP BY STEP TRACE — nums = [-2, 0, 3, -5, 2, -1]
================================================================================
Building the prefix array in `__init__`:

    i        0    1    2    3    4    5
    nums[i] -2    0    3   -5    2   -1

    prefix[0] = 0
    prefix[1] = prefix[0] + nums[0] =  0 + (-2) = -2
    prefix[2] = prefix[1] + nums[1] = -2 +   0  = -2
    prefix[3] = prefix[2] + nums[2] = -2 +   3  =  1
    prefix[4] = prefix[3] + nums[3] =  1 + (-5) = -4
    prefix[5] = prefix[4] + nums[4] = -4 +   2  = -2
    prefix[6] = prefix[5] + nums[5] = -2 + (-1) = -3

    prefix = [0, -2, -2, 1, -4, -2, -3]
    index     0   1   2  3   4   5   6

Answering queries, each O(1):

    sumRange(0, 2) = prefix[3] - prefix[0] =  1 -  0 =  1
    sumRange(2, 5) = prefix[6] - prefix[2] = -3 - (-2) = -1
    sumRange(0, 5) = prefix[6] - prefix[0] = -3 -  0 = -3


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach              __init__      sumRange (each)     Over Q queries     Mutates input?
    ---------------------  -----------   -----------------   -----------------  ---------------
    Naive re-sum           O(1)/O(n)*    O(right - left)      O(n) worst case    no
                                                               per query, so
                                                               O(n * Q) total
    Prefix sum array ✅     O(n)          O(1)                 O(n + Q) total     no

    * O(1) if you keep a reference to the caller's list, O(n) if you defensively
      copy it. Either way it does not change the per-query cost, which is the
      part that dominates as Q grows.

    Neither approach mutates the caller's `nums` — this problem's array is
    read-only after construction (hence "Immutable" in the title), so there
    is no in-place-accumulation trick like problem 001's Approach 2 to
    consider here; both approaches only ever READ `nums`.

    The crossover: for a SINGLE query, naive can even be marginally faster
    (no prefix array to build). But this class is built once and queried up
    to 10^4 times per LeetCode's own constraint — and the runtime demo below
    measures the real divergence as query count grows on this machine.


================================================================================
EDGE CASES
================================================================================
    nums = [1], sumRange(0,0) -> 1     Single-element array. The only legal
                                        query is left==right==0. Exercises
                                        prefix[1] - prefix[0] with nothing
                                        else in the array.

    left == right                      Single element, e.g. sumRange(3,3).
                                        prefix[4] - prefix[3] must equal
                                        exactly nums[3], not an off-by-one
                                        neighbor.

    left == 0                          Sum from the very start. Exercises
                                        prefix[0] = 0 as a real operand, not
                                        a special case — this is exactly the
                                        sentinel the topic guide's §1.3
                                        generalizes for the hashmap variant.

    right == len(nums) - 1             Sum to the very end, the WHOLE array.
                                        prefix[right+1] must be prefix[n],
                                        the last entry, reachable without
                                        any bounds special-casing.

    All negative numbers                Running total must go negative and
                                        stay negative; no assumption that
                                        prefix is monotone increasing.


================================================================================
COMMON MISTAKES
================================================================================
1. Building `prefix` of length `n` instead of `n+1`, forgetting the leading
   `prefix[0] = 0` sentinel. Then `sumRange(0, r)` has no clean formula and
   needs a special case — exactly the bug the sentinel exists to avoid
   (topic guide §1.0, §1.3).

2. Off-by-one on the query: `prefix[right] - prefix[left]` (drops `nums[right]`)
   or `prefix[right+1] - prefix[left+1]` (also drops `nums[left]`). The
   correct formula is `prefix[right+1] - prefix[left]` — draw the picture in
   the topic guide §1.0 if unsure.

3. Recomputing the prefix array (or re-summing from scratch) INSIDE
   `sumRange` instead of once in `__init__`. This defeats the entire point
   of the design — it is Approach 0 wearing Approach 1's method name.

4. Treating `nums.length == 1` as needing special handling. It doesn't: a
   length-2 prefix array (`[0, nums[0]]`) and the same formula work
   unmodified.

5. Doing the O(n) prefix-array build INSIDE the constructor but then also
   copying `nums` defensively AND building a second structure from the
   copy — unnecessary double O(n) work when one pass suffices.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if `nums` could change between queries (LC 307, "Mutable")?
A: A plain prefix array breaks — one `update` would force an O(n) rebuild
   of every prefix entry after it. You need a Fenwick tree (Binary Indexed
   Tree) or segment tree instead: O(log n) update, O(log n) query. That is
   topic 26 in this curriculum, not this topic — the plain prefix array's
   entire value proposition depends on the array being immutable, which is
   why LeetCode split it into two separate problems.

Q: What if queries arrive as a huge batch, all known up front?
A: Same prefix array — you'd still build it once in O(n) and answer every
   query in the batch in O(1), so total cost is O(n + Q) regardless of
   whether queries are interactive or batched.

Q: Can you avoid the extra O(n) space for the prefix array?
A: Not while keeping O(1) queries for ARBITRARY (non-sequential) ranges —
   you need random access to every historical prefix. If queries were
   guaranteed to arrive with non-decreasing `left` and `right` (a very
   different problem), you could get away with O(1) space and a moving
   running total, but that is not this problem's contract.

Q: How would you extend this to 2D (a matrix, LC 304)?
A: Same trade, one more inclusion-exclusion term — see the topic guide
   Part 2. Build a 2D prefix matrix once in O(m*n), then each rectangle
   query is O(1) via four array reads. Problem 006 in this folder.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 1480  Running Sum of 1d Array        — problem 001: the prefix array
                                                itself, with no query layer
    LC 724   Find Pivot Index               — problem 003: a running total
                                                comparison, no random-access
                                                queries needed
    LC 304   Range Sum Query 2D - Immutable — problem 006: the 2D version
                                                (topic guide Part 2)
    LC 307   Range Sum Query - Mutable      — the Fenwick-tree version of
                                                this exact problem (topic 26)
================================================================================
"""

import random
import time
from typing import List


class NumArray:
    """Precomputes a prefix-sum array once; each sumRange is O(1)."""

    def __init__(self, nums: List[int]):
        self.prefix = [0] * (len(nums) + 1)
        for i, x in enumerate(nums):
            self.prefix[i + 1] = self.prefix[i] + x

    def sumRange(self, left: int, right: int) -> int:
        return self.prefix[right + 1] - self.prefix[left]


class _NumArrayBrute:
    """Naive oracle: re-sum nums[left:right+1] from scratch every call.
    O(right-left) per query, O(1) (reference) construction."""

    def __init__(self, nums: List[int]):
        self.nums = nums

    def sumRange(self, left: int, right: int) -> int:
        return sum(self.nums[left:right + 1])


# ==============================================================================
# TESTS — run:  python 002_range_sum_query_immutable_solution.py
# ==============================================================================
CASES = [
    ([-2, 0, 3, -5, 2, -1], [(0, 2), (2, 5), (0, 5), (1, 1), (4, 4)]),
    ([1], [(0, 0)]),
    ([5, 5, 5, 5], [(0, 0), (1, 1), (0, 3), (2, 3)]),
    ([-1, -1, -1], [(0, 2), (0, 0), (1, 2)]),
    ([0, 0, 0], [(0, 1), (1, 2), (0, 2)]),
    ([7, -3, 4, -8, 2, 9], [(0, 5), (3, 3), (1, 4), (0, 0), (5, 5)]),
]


def run_tests() -> None:
    all_ok = True

    for nums, queries in CASES:
        oracle = _NumArrayBrute(list(nums))
        na = NumArray(list(nums))
        ok = all(na.sumRange(l, r) == oracle.sumRange(l, r) for l, r in queries)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums!r:<28} "
              f"({len(queries)} queries)")

    # ----------------------------------------------------------------------
    # Randomised cross-check.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the naive oracle ---")
    random.seed(6)
    trials, mismatches = 2000, 0
    for _ in range(trials):
        n = random.randint(1, 40)
        arr = [random.randint(-100_000, 100_000) for _ in range(n)]
        na = NumArray(list(arr))
        oracle = _NumArrayBrute(list(arr))
        for _ in range(10):
            l = random.randint(0, n - 1)
            r = random.randint(l, n - 1)
            if na.sumRange(l, r) != oracle.sumRange(l, r):
                mismatches += 1
    print(f"  {trials} random arrays x 10 random queries each: "
          f"{mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # The trace.
    # ----------------------------------------------------------------------
    nums = [-2, 0, 3, -5, 2, -1]
    print(f"\n--- building the prefix array over {nums} ---")
    prefix = [0] * (len(nums) + 1)
    print(f"  {'i':>2} {'nums[i]':>8} {'prefix[i]':>10} {'prefix[i+1]':>12}")
    for i, x in enumerate(nums):
        before = prefix[i]
        prefix[i + 1] = prefix[i] + x
        print(f"  {i:>2} {x:>8} {before:>10} {prefix[i+1]:>12}")
    print(f"  prefix = {prefix}")
    for l, r in [(0, 2), (2, 5), (0, 5)]:
        print(f"  sumRange({l},{r}) = prefix[{r+1}] - prefix[{l}] "
              f"= {prefix[r+1]} - {prefix[l]} = {prefix[r+1] - prefix[l]}")

    # ----------------------------------------------------------------------
    # THE FLAGSHIP DEMO: O(1) prefix queries vs O(n) naive re-sum, at scale.
    # ----------------------------------------------------------------------
    print("\n--- FLAGSHIP DEMO: O(1) queries vs O(right-left) re-sum, at scale ---")
    print("  (many repeated queries against a FIXED array — exactly this")
    print("   problem's contract: build once, query up to 10^4 times)")
    random.seed(0)
    print(f"  {'array n':>8} {'#queries':>9} {'prefix total':>13} "
          f"{'naive total':>13} {'naive / prefix':>15}")
    for n in (1_000, 5_000):
        arr = [random.randint(-1000, 1000) for _ in range(n)]
        for num_queries in (5_000, 20_000, 50_000):
            queries = []
            for _ in range(num_queries):
                l = random.randint(0, n - 1)
                r = random.randint(l, n - 1)
                queries.append((l, r))

            t0 = time.perf_counter()
            na = NumArray(list(arr))
            for l, r in queries:
                na.sumRange(l, r)
            t1 = time.perf_counter()

            oracle = _NumArrayBrute(list(arr))
            for l, r in queries:
                oracle.sumRange(l, r)
            t2 = time.perf_counter()

            prefix_ms = (t1 - t0) * 1000
            naive_ms = (t2 - t1) * 1000
            ratio = naive_ms / prefix_ms if prefix_ms > 0 else float("inf")
            print(f"  {n:>8} {num_queries:>9} {prefix_ms:>11.1f}ms "
                  f"{naive_ms:>11.1f}ms {ratio:>13.1f}x")
    print("  The prefix version's total includes the O(n) build; the naive")
    print("  version's total is pure per-query re-summing. As query count")
    print("  grows, the naive total grows with it while the prefix total")
    print("  stays essentially flat — this is the O(n*Q) vs O(n+Q) split")
    print("  from the complexity table, made visible.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
