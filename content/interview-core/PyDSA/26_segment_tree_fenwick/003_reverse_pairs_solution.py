"""
================================================================================
SOLUTION · LeetCode 493 · Reverse Pairs                                   [Hard]
https://leetcode.com/problems/reverse-pairs/
================================================================================

THE CORE IDEA
--------------
Reverse pairs is a CROSS-INDEX PAIR COUNT (`i < j`, `nums[i] > 2*nums[j]`)
over the whole array — the same shape as an inversion count, just with the
comparison doubled on one side. Merge sort already visits every possible
"left half / right half" split as it recurses, and right before merging
two ALREADY-SORTED halves it can count all qualifying cross-pairs between
them in O(n) using a two-pointer scan that never backtracks (both halves
are sorted, so as the left pointer advances, the right pointer only ever
needs to move forward to keep up). Do that counting at every level of the
recursion, sum the results, and you've counted every reverse pair exactly
once — each pair `(i, j)` is counted at the UNIQUE recursion level where
`i` and `j` first land in different halves.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, CODED BELOW as a test oracle only): the
literal double loop, `for i: for j > i: if nums[i] > 2*nums[j]: count++`.
O(n^2) time, O(1) extra space. At n = 5*10^4 this is up to ~1.25*10^9
comparisons — far too slow to ship, but perfect as an independent oracle
for the randomized cross-check below, since it directly encodes the
problem statement with nothing clever going on.

Approach 1 (chosen) — modified merge sort: O(n log n) time, O(n) auxiliary
space. See THE CORE IDEA. Counts cross-pairs during the natural merge-sort
recursion, with no separate data structure.

Approach 2 (alternative, not coded) — Fenwick tree (BIT) with coordinate
compression: sort and rank all values (and all `2*value`s that will be
queried) once, then walk the array from RIGHT to LEFT, and for each
`nums[i]`, query "how many values already inserted into the BIT are
STRICTLY LESS than `nums[i] / 2`" (equivalently: rank-query for values
`< nums[i]` after doubling everything, or use a fractional-safe comparison
`nums[i] > 2*nums[j]` reformulated on ranks) — that count is exactly the
number of `j > i` with `nums[j]` small enough to pair with `nums[i]` — then
insert `nums[i]`'s rank into the BIT and continue leftward. Also
O(n log n), genuinely equivalent, but needs an explicit compression pass
over BOTH `nums` and `2*nums` (since the query threshold isn't a value
that's necessarily itself present in the array) before any counting can
start. The merge-sort version needs no such setup, which is why it's
taught as primary here (topic guide Part 3).


================================================================================
STEP BY STEP TRACE — nums = [1, 3, 2, 3, 1]
================================================================================
Recursion splits (indices, 0-indexed, inclusive):
    [1,3,2,3,1]  (0..4)
    ├── [1,3]        (0..1)
    │   ├── [1]  (0..0) -> base case, 0 pairs, sorted: [1]
    │   └── [3]  (1..1) -> base case, 0 pairs, sorted: [3]
    │   merge [1] & [3]: count cross-pairs first --
    │       i=0 (val=1), j starts at right-half start (val=3):
    │           1 > 2*3=6? no -> 0 pairs contributed by nums[0]
    │       merged (sorted) = [1, 3], subtotal = 0
    ├── [2,3,1]      (2..4)
    │   ├── [2]      (2..2) -> base case, sorted: [2]
    │   └── [3,1]    (3..4)
    │       ├── [3] (3..3) sorted: [3]
    │       └── [1] (4..4) sorted: [1]
    │       merge [3] & [1]: i=0(val=3), j at val=1: 3 > 2*1=2? yes ->
    │           pairs contributed = (mid+1 index count) = 1
    │           (this is the (3,4) pair from the problem statement)
    │       merged (sorted) = [1, 3], subtotal = 1
    │   merge [2] & [1,3] (the just-merged sorted pair):
    │       left=[2], right=[1,3]
    │       i=0 (val=2), j starts at right index 0 (val=1):
    │           2 > 2*1=2? no (not STRICT) -> j does not advance past val=1
    │           j stays; contributed = j_offset = 0
    │       merged (sorted) = [1, 2, 3], subtotal = 1 (carried from below)
    total so far from right subtree ([2,3,1] -> [1,2,3]): 1

Merge the two top halves: left=[1,3] (sorted), right=[1,2,3] (sorted)
    i=0 (val=1) in left, j walks right while left[i] > 2*right[j]:
        j=0: 1 > 2*1=2? no -> stop.  contributed = 0
    i=1 (val=3) in left, j continues from where it left off (j=0):
        j=0: 3 > 2*1=2? yes -> j=1
        j=1: 3 > 2*2=4? no -> stop.  contributed = j - right_start = 1
        (this is the (1,4) pair: nums[1]=3, nums[4]=1)
    merge-step cross-pair subtotal at this level = 0 + 1 = 1
    merged (sorted) = [1, 1, 2, 3, 3]

GRAND TOTAL = 0 (level: [1,3]) + 1 (level: [3,1]) + 0 (level: [2] vs [1,3])
              + 1 (top level) = 2                          MATCHES expected 2


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time         Space   Mutates input?
    --------------------------------------------------------------------
    Brute force double loop [priced]  O(n^2)       O(1)    no (read-only)
    Modified merge sort ✅            O(n log n)   O(n)    no (sorts a COPY)
    BIT + coordinate compression      O(n log n)   O(n)    no (read-only)


================================================================================
EDGE CASES
================================================================================
    n == 1                       No possible pair; answer is trivially 0
                                  (base case of the recursion returns
                                  immediately).
    All elements equal            e.g. [2,2,2]: `nums[i] > 2*nums[j]`
                                  becomes `2 > 4`, always false -> answer 0.
                                  Exercises the STRICT inequality boundary.
    Strictly decreasing array     e.g. [5,4,3,2,1] maximizes reverse pairs
                                  for small values relative to n.
    Negative numbers               nums[i] can be negative; `2*nums[j]` for
                                  a very negative nums[j] makes the
                                  condition easy to satisfy — the algorithm
                                  must not assume non-negativity anywhere.
    Boundary at exact equality
    (nums[i] == 2*nums[j])         Must NOT count — the condition is
                                  strictly greater-than, not
                                  greater-or-equal. A common bug flips this.


================================================================================
COMMON MISTAKES
================================================================================
1. Using `nums[i] > 2 * nums[j]` (the counting condition) as the MERGE
   comparison too, instead of the standard `nums[i] <= nums[j]` — corrupts
   the sortedness the counting step at the NEXT level up depends on.

2. Resetting the right-half pointer `j` back to the start of the right half
   for every `i` in the left half during counting — turns the O(n)
   two-pointer counting step back into O(n^2) per merge, destroying the
   whole benefit of doing this during merge sort.

3. Counting the cross-pairs AFTER merging instead of BEFORE — once merged,
   the boundary between "was in the left half" and "was in the right half"
   is lost, so there's no way to correctly attribute which pairs came from
   crossing the split versus being entirely within one already-counted
   half.

4. Off-by-one in the midpoint calculation: `mid = int((l + r) / 2)` risks
   overflow in fixed-width languages for very large `l + r` (not a Python
   concern, but the muscle-memory habit matters); prefer
   `mid = l + (r - l) // 2`.

5. Forgetting the STRICT inequality — using `>=` instead of `>` in the
   pair condition silently overcounts whenever `nums[i] == 2 * nums[j]`
   exactly.

6. Mutating the CALLER's array in place while sorting during merge sort,
   surprising the caller when their list comes back reordered — this
   solution works on an internal COPY specifically to avoid that surprise,
   even though LeetCode itself doesn't penalize in-place mutation here.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
Q: How would you solve this with a Fenwick tree instead?
A: Coordinate-compress every value AND every value's double that will be
   queried, walk the array from the end, query "count of already-inserted
   ranks below the threshold," then insert the current element's rank —
   O(n log n), see Approach 2 above. Useful to know because it generalizes
   better if updates need to be interleaved with counting (this problem's
   array is static, so it doesn't need that generality).

Q: What's the difference between this and a plain inversion count
   (`nums[i] > nums[j]`, no doubling)?
A: Same merge-sort skeleton; only the two-pointer counting CONDITION
   changes (drop the `2 *`). The doubling here doesn't change the
   algorithm's shape at all, only the per-comparison predicate.

Q: How does this connect to Count of Range Sum (LC 327, this topic's 004)?
A: Same divide-and-conquer counting skeleton, generalized from a single
   moving threshold pointer to a WINDOW between two moving pointers (a
   lower-bound pointer and an upper-bound pointer), because 004 counts a
   RANGE condition instead of a single inequality. See 004's solution file.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 327  Count of Range Sum          — this topic, 004, same merge-sort-counting family
    LC 315  Count of Smaller Numbers After Self — the "pure" inversion-count sibling
    LC 493  (this problem)              — inversion count with a doubled threshold
    Topic 15 Advanced Graphs / D&C      — same split-recurse-combine recursion shape
================================================================================
"""

import random
import time


class Solution:
    def reversePairs(self, nums: list[int]) -> int:
        arr = list(nums)  # work on a copy; never mutate the caller's list
        return self._merge_count(arr, 0, len(arr) - 1)

    def _merge_count(self, arr: list[int], lo: int, hi: int) -> int:
        if lo >= hi:
            return 0

        mid = lo + (hi - lo) // 2
        count = self._merge_count(arr, lo, mid) + self._merge_count(arr, mid + 1, hi)

        # Count cross-pairs BEFORE merging, while both halves are sorted.
        j = mid + 1
        for i in range(lo, mid + 1):
            while j <= hi and arr[i] > 2 * arr[j]:
                j += 1
            count += j - (mid + 1)

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
def _brute_force_reverse_pairs(nums: list[int]) -> int:
    """✗ Priced-not-shipped: O(n^2) double loop. Correctness oracle."""
    n = len(nums)
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            if nums[i] > 2 * nums[j]:
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
        ([1, 3, 2, 3, 1], 2),
        ([2, 4, 3, 5, 1], 3),
    ]
    for nums, expected in cases:
        original = list(nums)
        got = sol.reversePairs(nums)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  reversePairs({original}) -> {got} (want {expected})")

    # ------------------------------------------------------------------
    # Edge cases.
    # ------------------------------------------------------------------
    print("\n--- edge cases ---")
    ok = sol.reversePairs([5]) == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  n=1 -> 0")

    ok = sol.reversePairs([2, 2, 2]) == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  all equal, boundary nums[i]==2*nums[j] not counted -> 0")

    ok = sol.reversePairs([5, 4, 3, 2, 1]) == _brute_force_reverse_pairs([5, 4, 3, 2, 1])
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  strictly decreasing matches brute force")

    ok = sol.reversePairs([-5, -1, -3, 4]) == _brute_force_reverse_pairs([-5, -1, -3, 4])
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  negative numbers matches brute force")

    # ------------------------------------------------------------------
    # Input not mutated for the caller.
    # ------------------------------------------------------------------
    caller_array = [3, 1, 2]
    sol.reversePairs(caller_array)
    ok = caller_array == [3, 1, 2]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  caller's array left untouched (internal copy used)")

    # ------------------------------------------------------------------
    # Randomized cross-check vs the O(n^2) brute-force oracle.
    # ------------------------------------------------------------------
    print("\n--- randomized cross-check vs brute-force oracle (100 trials, n<=60) ---")
    rng = random.Random(493)
    mismatch = 0
    for _ in range(100):
        n = rng.randint(1, 60)
        arr = [rng.randint(-50, 50) for _ in range(n)]
        fast = sol.reversePairs(arr)
        slow = _brute_force_reverse_pairs(arr)
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
        arr = [rng.randint(-10_000, 10_000) for _ in range(n)]

        t0 = time.perf_counter()
        sol.reversePairs(arr)
        fast_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        _brute_force_reverse_pairs(arr)
        slow_ms = (time.perf_counter() - t0) * 1000

        speedup = slow_ms / fast_ms if fast_ms > 0 else float("inf")
        print(f"  {n:>8} {fast_ms:>18.2f} {slow_ms:>18.2f} {speedup:>9.1f}x")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
