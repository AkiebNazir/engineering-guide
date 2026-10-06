"""
================================================================================
SOLUTION · LeetCode 327 · Count of Range Sum                              [Hard]
https://leetcode.com/problems/count-of-range-sum/
================================================================================

THE CORE IDEA
--------------
Reduce "count subarrays whose sum is in `[lower, upper]`" to "count pairs
of PREFIX-SUM indices `p < q` with `lower <= prefix[q] - prefix[p] <=
upper`" using topic 04's identity `S(i, j) = prefix[j+1] - prefix[i]`. That
turns this into a cross-index PAIR-COUNT problem over the `prefix` array —
the exact same shape 003 Reverse Pairs solves with a modified merge sort,
generalized from a single threshold to a RANGE. During each merge, for a
fixed `prefix[i]` in the (sorted) left half, the qualifying `prefix[j]`
values in the (sorted) right half form one CONTIGUOUS WINDOW, because
`prefix[j] - prefix[i]` increases monotonically as `j` increases within a
sorted right half. Track that window with two pointers — one for
"`>= lower`" and one for "`> upper`" — that both only move forward as `i`
advances across the left half, giving O(n) counting work per merge level
and O(n log n) total.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, CODED BELOW as a test oracle only):
precompute prefix sums, then check every `O(n^2)` pair `(p, q)` directly.
O(n^2) time, O(n) space (for the prefix array). At n = 10^5 this is up to
~5*10^9 pair checks — used here purely as a correctness oracle on small
inputs.

Approach 1 (chosen) — prefix sums + modified merge sort: O(n log n) time,
O(n) space. See THE CORE IDEA. Same skeleton as 003, generalized from one
moving pointer to two.

Approach 2 (alternative, not coded) — Fenwick tree (BIT) with coordinate
compression: compute all prefix sums, coordinate-compress them (and derive
the query thresholds `prefix[i] - upper` and `prefix[i] - lower` against
that same compressed rank space), walk left to right inserting each
prefix sum's rank into the BIT as you go, and for each `prefix[i]` query
"how many previously-inserted prefix sums fall in
`[prefix[i] - upper, prefix[i] - lower]`" via two BIT prefix queries. Also
O(n log n) and genuinely equivalent; needs an explicit compression pass
over `prefix[i]`, `prefix[i] - lower`, and `prefix[i] - upper` together
(the query bounds aren't necessarily values already present in `prefix`,
so they must be merged into the same sorted/ranked universe) before
counting can start. The merge-sort version needs no such setup step.


================================================================================
STEP BY STEP TRACE — nums = [-2, 5, -1], lower = -2, upper = 2
================================================================================
prefix = [0, -2, 3, 2]     (prefix[0]=0, prefix[1]=-2, prefix[2]=3, prefix[3]=2)
Indices into `prefix`: lo=0, hi=3 (4 elements)

merge_count(prefix, 0, 3, lower=-2, upper=2):
    mid = 0 + (3-0)//2 = 1

    LEFT  = merge_count(prefix, 0, 1, ...)   (covers prefix[0..1] = [0, -2])
        mid=0
        merge_count(0,0)=0 (single: [0]);  merge_count(1,1)=0 (single: [-2])
        cross-count: i=0 (val=0), lo_ptr=hi_ptr=1 (mid+1)
            lo_ptr: while prefix[lo_ptr]-0 < -2: prefix[1]-0=-2, is -2 < -2? no -> stop, lo_ptr=1
            hi_ptr: while prefix[hi_ptr]-0 <= 2: -2-0=-2<=2? yes -> hi_ptr=2 (out of range [1,1], stop)
            contributed = hi_ptr - lo_ptr = 2 - 1 = 1
        LEFT total = 1
        merge [0] & [-2] (sorted by VALUE, standard merge) -> prefix[0..1] becomes [-2, 0]

    RIGHT = merge_count(prefix, 2, 3, ...)   (covers prefix[2..3] = [3, 2])
        mid=2
        merge_count(2,2)=0 ([3]); merge_count(3,3)=0 ([2])
        cross-count: i=2 (val=3), lo_ptr=hi_ptr=3
            lo_ptr: prefix[3]-3 = 2-3 = -1 < -2? no -> stop, lo_ptr=3
            hi_ptr: prefix[3]-3 = -1 <= 2? yes -> hi_ptr=4 (out of range [3,3], stop)
            contributed = 4 - 3 = 1
        RIGHT total = 1
        merge [3] & [2] -> prefix[2..3] becomes [2, 3]

    Cross-count at THIS (top) level, using the now-sorted halves
    prefix[0..1] = [-2, 0] and prefix[2..3] = [2, 3]:
        lo_ptr = hi_ptr = 2 (mid+1), reset ONCE for this whole level
        i=0 (val=-2):
            lo_ptr: prefix[2]-(-2) = 2-(-2)=4 < -2? no -> stop, lo_ptr=2
            hi_ptr: prefix[2]-(-2) = 4 <= 2? no -> stop, hi_ptr=2
            contributed = 2 - 2 = 0
        i=1 (val=0):
            lo_ptr: prefix[2]-0 = 2 < -2? no -> stop, lo_ptr=2 (unchanged)
            hi_ptr: prefix[2]-0 = 2 <= 2? yes -> hi_ptr=3;
                    prefix[3]-0 = 3 <= 2? no -> stop, hi_ptr=3
            contributed = 3 - 2 = 1
        top-level cross count = 0 + 1 = 1
    merge [-2,0] & [2,3] -> prefix becomes [-2, 0, 2, 3]

GRAND TOTAL = LEFT(1) + RIGHT(1) + top-level cross(1) = 3     MATCHES expected 3

(The 3 counted subarrays: S(0,0)=-2, S(2,2)=-1, S(0,2)=2 — verified against
the brute-force oracle in the tests below.)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time         Space   Mutates input?
    --------------------------------------------------------------------
    Brute force pair check [priced]   O(n^2)       O(n)    no (read-only)
    Prefix sums + merge sort ✅       O(n log n)   O(n)    no (sorts a COPY of prefix sums)
    BIT + coordinate compression      O(n log n)   O(n)    no (read-only)


================================================================================
EDGE CASES
================================================================================
    n == 1                       Single element nums=[0]; prefix=[0,0].
                                  Only one candidate pair, S(0,0)=nums[0].
    lower == upper                Range collapses to counting EXACT sums,
                                  the tightest possible window per `i`.
    All negative / all positive   Prefix sums are strictly monotonic in
                                  that case, but the window-counting logic
                                  must not assume any particular sign
                                  pattern — it only relies on the RIGHT
                                  half being sorted, which merge sort
                                  guarantees regardless of sign.
    Answer requiring the full
    32-bit range                  Problem guarantees the count fits in a
                                  32-bit int even though intermediate sums
                                  can be large; Python needs no special
                                  handling, but a fixed-width implementation
                                  must use 64-bit accumulators for the
                                  prefix sums themselves.
    lower > any possible sum,
    or upper < any possible sum   Answer is 0; both pointers advance to the
                                  end of the right half without ever
                                  opening a nonempty window, or never move
                                  at all.


================================================================================
COMMON MISTAKES
================================================================================
1. Running the merge-sort counting directly on `nums` instead of on the
   PREFIX-SUM array — this problem is fundamentally about pairs of prefix
   sums, not pairs of raw elements (contrast with 003, which genuinely
   operates on the raw array).

2. Resetting the two window pointers back to `mid+1` for every `i` in the
   left half (instead of once per merge-level, letting them only advance)
   — turns O(n) counting per level back into O(n^2), same trap as 003.

3. Using ONE pointer instead of two — a single pointer can track "first
   index where `prefix[j]-prefix[i] >= lower`" but then still needs a
   SEPARATE scan (or second pointer) to find where the window ends at
   `upper`; conflating the two into one pointer silently either overcounts
   or undercounts the window width.

4. Off-by-one on inclusive vs exclusive bounds: the window is
   `[lower, upper]` INCLUSIVE on both ends — the "upper" pointer must stop
   at the first index where the difference EXCEEDS upper (`> upper`, not
   `>= upper`), while the "lower" pointer stops at the first index where
   the difference is AT LEAST lower (`>= lower`, not `> lower`).

5. Forgetting `prefix[0] = 0` as a real, countable prefix-sum entry — it
   represents "the empty prefix," and pairing it with any `prefix[k]`
   recovers `S(0, k-1)`, the sum of a subarray STARTING at index 0. Leaving
   it out of the array undercounts every subarray that starts at index 0.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
Q: How does this connect to Reverse Pairs (LC 493, this topic's 003)?
A: Identical divide-and-conquer skeleton; 003's counting condition is a
   single inequality (`nums[i] > 2*nums[j]`, one moving pointer), this
   problem's is a range (`lower <= prefix[j]-prefix[i] <= upper`, two
   moving pointers forming a window). Recognizing "cross-index pair/range
   count over a static array" as one reusable pattern with two variants is
   the actual transferable skill.

Q: Could you solve this with a BIT instead?
A: Yes — coordinate-compress the prefix sums and the two query offsets
   derived from each `prefix[i]`, then walk left to right maintaining a
   running BIT of inserted prefix sums and doing two prefix-range queries
   per element. See Approach 2 above; equivalent complexity, more setup.

Q: What if `nums` could be updated between queries (like 001/002 in this
   topic)?
A: Then the static merge-sort approach no longer applies cleanly (its
   O(n log n) bound assumes ONE full pass over a static array) — you'd
   need a Fenwick/segment-tree-backed structure that supports interleaved
   point updates and range counts, which is exactly why the BIT
   alternative generalizes better than merge sort for a "live" variant of
   this problem.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 493  Reverse Pairs                — this topic, 003, same merge-sort-counting family
    LC 315  Count of Smaller Numbers After Self — the single-pointer sibling
    LC 004  (topic 04) Range Sum Query family — the prefix-sum identity this reduction depends on
    Topic 15 Advanced Graphs / D&C       — same split-recurse-combine recursion shape
================================================================================
"""

import random
import time


class Solution:
    def countRangeSum(self, nums: list[int], lower: int, upper: int) -> int:
        prefix = [0] * (len(nums) + 1)
        for i, v in enumerate(nums):
            prefix[i + 1] = prefix[i] + v
        return self._merge_count(prefix, 0, len(prefix) - 1, lower, upper)

    def _merge_count(self, arr: list[int], lo: int, hi: int, lower: int, upper: int) -> int:
        if lo >= hi:
            return 0

        mid = lo + (hi - lo) // 2
        count = self._merge_count(arr, lo, mid, lower, upper) + self._merge_count(
            arr, mid + 1, hi, lower, upper
        )

        # Count cross-pairs BEFORE merging: for each i in the (sorted) left
        # half, the qualifying j's in the (sorted) right half form one
        # contiguous window [lo_ptr, hi_ptr) that only moves forward.
        lo_ptr = hi_ptr = mid + 1
        for i in range(lo, mid + 1):
            while lo_ptr <= hi and arr[lo_ptr] - arr[i] < lower:
                lo_ptr += 1
            while hi_ptr <= hi and arr[hi_ptr] - arr[i] <= upper:
                hi_ptr += 1
            count += hi_ptr - lo_ptr

        # Merge the two sorted halves in place (standard merge-sort merge,
        # a DIFFERENT comparison than the counting step above).
        merged = []
        left, right = lo, mid + 1
        while left <= mid and right <= hi:
            if arr[left] <= arr[right]:
                merged.append(arr[left])
                left += 1
            else:
                merged.append(arr[right])
                right += 1
        merged.extend(arr[left : mid + 1])
        merged.extend(arr[right : hi + 1])
        arr[lo : hi + 1] = merged

        return count


# ------------------------------------------------------------------------
# Oracle used only for the tests and benchmark below.
# ------------------------------------------------------------------------
def _brute_force_count_range_sum(nums: list[int], lower: int, upper: int) -> int:
    """✗ Priced-not-shipped: O(n^2) pair check over prefix sums. Oracle."""
    n = len(nums)
    prefix = [0] * (n + 1)
    for i, v in enumerate(nums):
        prefix[i + 1] = prefix[i] + v
    count = 0
    for p in range(n + 1):
        for q in range(p + 1, n + 1):
            if lower <= prefix[q] - prefix[p] <= upper:
                count += 1
    return count


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    # ------------------------------------------------------------------
    # LeetCode's examples.
    # ------------------------------------------------------------------
    print("--- LeetCode examples ---")
    cases = [
        ([-2, 5, -1], -2, 2, 3),
        ([0], 0, 0, 1),
    ]
    for nums, lower, upper, expected in cases:
        got = sol.countRangeSum(list(nums), lower, upper)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  countRangeSum({nums}, {lower}, {upper}) -> {got} (want {expected})")

    # ------------------------------------------------------------------
    # Edge cases.
    # ------------------------------------------------------------------
    print("\n--- edge cases ---")
    ok = sol.countRangeSum([5], -10, 10) == 1
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  n=1, wide range -> 1")

    ok = sol.countRangeSum([1, 1, 1], 3, 3) == 1  # only S(0,2)=3 qualifies
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  lower==upper, exact-sum matching")

    ok = sol.countRangeSum([-1, -2, -3], -100, -100) == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  range with no possible matches -> 0")

    ok = sol.countRangeSum([-1, -2, -3], -6, -1) == _brute_force_count_range_sum(
        [-1, -2, -3], -6, -1
    )
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  all-negative array matches brute force")

    # ------------------------------------------------------------------
    # Input not mutated for the caller.
    # ------------------------------------------------------------------
    caller_array = [3, -1, 2]
    sol.countRangeSum(caller_array, 0, 5)
    ok = caller_array == [3, -1, 2]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  caller's array left untouched")

    # ------------------------------------------------------------------
    # Randomized cross-check vs the O(n^2) brute-force oracle.
    # ------------------------------------------------------------------
    print("\n--- randomized cross-check vs brute-force oracle (100 trials, n<=50) ---")
    rng = random.Random(327)
    mismatch = 0
    for _ in range(100):
        n = rng.randint(1, 50)
        arr = [rng.randint(-20, 20) for _ in range(n)]
        lower, upper = sorted((rng.randint(-50, 50), rng.randint(-50, 50)))
        fast = sol.countRangeSum(list(arr), lower, upper)
        slow = _brute_force_count_range_sum(arr, lower, upper)
        if fast != slow:
            mismatch += 1
    ok = mismatch == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  {100 - mismatch}/100 random trials agree with brute force")

    # ------------------------------------------------------------------
    # BENCHMARK — O(n log n) merge sort vs O(n^2) brute force, measured live.
    # ------------------------------------------------------------------
    print("\n--- benchmark: O(n log n) merge sort vs O(n^2) brute force ---")
    print(f"  {'n':>8} {'merge sort (ms)':>18} {'brute force (ms)':>18} {'speedup':>10}")
    for n in (200, 800, 1600):
        rng = random.Random(1)
        arr = [rng.randint(-1000, 1000) for _ in range(n)]
        lower, upper = -500, 500

        t0 = time.perf_counter()
        sol.countRangeSum(list(arr), lower, upper)
        fast_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        _brute_force_count_range_sum(arr, lower, upper)
        slow_ms = (time.perf_counter() - t0) * 1000

        speedup = slow_ms / fast_ms if fast_ms > 0 else float("inf")
        print(f"  {n:>8} {fast_ms:>18.2f} {slow_ms:>18.2f} {speedup:>9.1f}x")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
