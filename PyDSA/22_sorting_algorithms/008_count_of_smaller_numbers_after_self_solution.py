"""
================================================================================
SOLUTION · LeetCode 315 · Count of Smaller Numbers After Self          [Hard]
https://leetcode.com/problems/count-of-smaller-numbers-after-self/
================================================================================

THE CORE IDEA
--------------
"How many elements to the right of index i are smaller than nums[i]" is
exactly an INVERSION COUNT, computed per-element instead of as one global
total -- and the classic way to count inversions in O(n log n) is to
AUGMENT merge sort's merge step, not to compare every pair (which is the
O(n^2) brute force). Sort INDICES (not values) by their values using merge
sort; during each merge, whenever the merge takes an element from the
RIGHT half, remember that it's smaller than everything still waiting in
the LEFT half at that moment. When you finally take a LEFT element, every
right-half element already consumed so far is smaller than it AND
originally sat to its right in the array (because a merge-sort split
always keeps left-half indices strictly before right-half indices in the
ORIGINAL array) -- so add the running "right elements consumed" counter to
that left element's answer.

    def merge(left_idxs, right_idxs):
        merged = []
        i = j = right_count = 0
        while i < len(left_idxs) and j < len(right_idxs):
            if nums[left_idxs[i]] <= nums[right_idxs[j]]:
                counts[left_idxs[i]] += right_count   # <- the augmentation
                merged.append(left_idxs[i]); i += 1
            else:
                right_count += 1
                merged.append(right_idxs[j]); j += 1
        while i < len(left_idxs):
            counts[left_idxs[i]] += right_count       # leftover left elems
            merged.append(left_idxs[i]); i += 1
        merged.extend(right_idxs[j:])
        return merged

Everything else is plain merge sort (problem 002's skeleton), just sorting
a permutation of INDICES by `nums[index]` instead of sorting values
directly, so the original position is never lost.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, don't code it): for every index i, scan every
j > i and count `nums[j] < nums[i]`. O(n^2) time, O(1) extra space
(besides output). Correct, and the direct translation of the problem
statement -- but at n up to 10^5, O(n^2) is 10^10 operations, far too slow.

Approach 1 (chosen) -- merge sort augmented with a right-side counter, as
above. O(n log n) time, O(n) extra space (the recursive merge buffers,
same as any array merge sort). The textbook answer; shown above and coded
below.

Approach 2 -- Binary Indexed Tree (Fenwick tree) over coordinate-compressed
values. Coordinate-compress `nums` to dense ranks 1..k (k = number of
distinct values), then walk the array RIGHT TO LEFT: for each `nums[i]`,
query "how many values strictly less than nums[i] have I already
inserted" (a prefix sum over ranks `1..rank-1`), record that as the
answer for i, then insert `rank(nums[i])` into the Fenwick tree. O(n log n)
time (n queries/updates, each O(log k)), O(n) space for the tree and rank
map. A genuinely different route to the same complexity class -- this is
the DIRECT bridge to topic 26's Binary Indexed Tree / Segment Tree
material: "count of elements already seen that are less than X" is a
canonical BIT/Fenwick use case (a dynamic prefix-sum-over-ranks query),
independent of the merge-sort augmentation trick. Coded below and
cross-checked.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [5, 2, 6, 1]   indices = [0, 1, 2, 3]   counts = [0, 0, 0, 0]

Merge sort on indices, split [0,1,2,3] -> [0,1] | [2,3]:

    merge_sort([0,1]) -> split [0] | [1] -> merge([0],[1]):
        nums[0]=5 vs nums[1]=2: 5<=2? no -> take right(1), right_count=1
        left exhausted next: counts[0] += right_count(1) -> counts[0]=1
        merged = [1, 0]

    merge_sort([2,3]) -> split [2] | [3] -> merge([2],[3]):
        nums[2]=6 vs nums[3]=1: 6<=1? no -> take right(3), right_count=1
        left exhausted next: counts[2] += right_count(1) -> counts[2]=1
        merged = [3, 2]

    merge([1,0], [3,2])  (left values: idx1->2, idx0->5; right: idx3->1, idx2->6)
        nums[1]=2 vs nums[3]=1: 2<=1? no -> take right(3), right_count=1
        nums[1]=2 vs nums[2]=6: 2<=6? yes -> counts[1] += right_count(1) -> counts[1]=1
                                take left(1)
        nums[0]=5 vs nums[2]=6: 5<=6? yes -> counts[0] += right_count(1) -> counts[0]=1+1=2
                                take left(0)
        left exhausted -> append remaining right: [2]
        merged = [3, 1, 0, 2]

    final counts = [2, 1, 1, 0]  ✓ matches expected output


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time          Space    Mutates input?
    ---------------------------------------------------------------------------
    Brute force [priced]              O(n^2)        O(1)*    no
    Merge sort, right-count aug. ✅   O(n log n)    O(n)     no
    Fenwick tree (coordinate comp.)   O(n log n)    O(n)     no

    * beyond the O(n) output array itself.


================================================================================
EDGE CASES
================================================================================
    n == 1                    -> merge_sort's base case returns immediately;
                                 counts = [0], no merge ever runs.
    all elements equal         -> the `<=` tie-break in the merge means an
                                 equal right-side element is NEVER counted
                                 as "smaller" (the problem wants strictly
                                 smaller) -- using `<` there instead of
                                 `<=` would incorrectly count equal values
                                 as smaller too.
    strictly decreasing array   -> e.g. [4,3,2,1]: every element has every
                                 later element smaller -- counts should be
                                 [3,2,1,0], the maximum possible inversion
                                 pattern, exercising every merge's "take
                                 from right, then discharge to left" path
                                 heavily.
    strictly increasing array   -> e.g. [1,2,3,4]: counts all 0 -- no merge
                                 step ever increments right_count before a
                                 left element is taken.
    negative numbers            -> no special handling in the merge-sort
                                 version (plain numeric `<=`); the Fenwick
                                 version must coordinate-compress correctly
                                 across negative AND positive values, which
                                 `sorted(set(nums))` handles for free since
                                 Python's sort is value-correct for
                                 negatives.


================================================================================
COMMON MISTAKES
================================================================================
1. Using `<` instead of `<=` in the merge comparison -- flips which side
   wins on a tie, which can double-count or under-count equal values
   depending on which direction the mistake goes; `<=` (take left on ties)
   is what correctly avoids counting equal elements as "smaller."
2. Incrementing `right_count` (or its Fenwick-tree equivalent) at the
   wrong moment -- e.g. discharging the counter to the LEFT element before
   deciding whether to take left or right this iteration, rather than
   after, silently off-by-one's every count.
3. Forgetting the "leftover left elements" pass after the right half
   exhausts (`while i < len(left_idxs): counts[left_idxs[i]] +=
   right_count`) -- every remaining left element is smaller than or equal
   to nothing further on the right at this point, wait -- they're actually
   compared to ALL of `right_count` consumed so far, and skipping this
   loop silently leaves those counts un-added.
4. Sorting the VALUES directly instead of a permutation of INDICES --
   loses track of which original position each value came from, making it
   impossible to attribute the count back to the correct output slot.
5. In the Fenwick variant, forgetting to coordinate-compress before
   indexing the tree (nums can be as extreme as -10^4..10^4, but the tree
   should be sized to the number of DISTINCT values, not the raw value
   range) -- works either way here given the modest constraint, but is the
   wrong habit for larger value ranges.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "This is basically counting inversions -- can you state that
  connection explicitly?" -> Yes: `counts[i]` is precisely the number of
  inversions `(i, j)` with `i < j` and `nums[i] > nums[j]` for that FIXED
  i. Summing all of `counts` gives the TOTAL inversion count of the array
  in one pass of this same algorithm -- the per-element version is a
  strict generalization of the classic "count total inversions via merge
  sort" exercise.
- "Could you use a Binary Search Tree (order-statistics tree) instead?" ->
  Yes -- walk right to left inserting into a BST augmented with subtree
  sizes (an "order statistic tree"), and each insertion can report how
  many existing nodes are less than the value being inserted in O(log n)
  amortized (O(n) worst case on a degenerate/unbalanced tree, hence why a
  BIT or a self-balancing tree, not a plain BST, is preferred in practice).
- "Why does the Fenwick tree need coordinate compression?" -> A Fenwick
  tree's size must match the RANGE of possible values (or ranks), not the
  count of elements; without compression, indexing directly by raw value
  would need an array sized to `max(nums) - min(nums)`, which could be
  enormous or (for non-integer values) impossible -- compressing to dense
  integer ranks bounds the tree size to exactly the number of distinct
  values actually present.


================================================================================
RELATED PROBLEMS
================================================================================
- Sort an Array (LC 912, this topic, 002) -- the base merge sort this
  problem augments; the augmentation (`right_count` tracking) is the
  entire delta between the two.
- Reverse Pairs (LC 493) -- a close cousin: count pairs `(i, j)` with
  `i < j` and `nums[i] > 2 * nums[j]`, solved with the SAME merge-sort
  augmentation pattern, just a different comparison inside the merge.
- Binary Indexed Tree / Segment Tree topics (topic 26) -- Approach 2 here
  is the canonical "count of elements less than X seen so far" BIT
  application; topic 26 develops the Fenwick tree itself in depth.
- Maximum Gap (LC 164, this topic, 007) -- a different non-comparison
  technique (pigeonhole bucketing) for a different kind of "beat O(n log
  n) or exploit structure" problem.
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def countSmaller(self, nums: List[int]) -> List[int]:
        """Merge sort over indices, augmented with a running right-side
        counter. O(n log n) time, O(n) extra space. The answer. See THE
        CORE IDEA above."""
        n = len(nums)
        counts = [0] * n
        indices = list(range(n))
        self._merge_sort(nums, indices, counts)
        return counts

    def _merge_sort(self, nums: List[int], idxs: List[int], counts: List[int]) -> List[int]:
        if len(idxs) <= 1:
            return idxs
        mid = len(idxs) // 2
        left = self._merge_sort(nums, idxs[:mid], counts)
        right = self._merge_sort(nums, idxs[mid:], counts)
        return self._merge(nums, left, right, counts)

    @staticmethod
    def _merge(
        nums: List[int], left: List[int], right: List[int], counts: List[int]
    ) -> List[int]:
        merged = []
        i = j = right_count = 0
        while i < len(left) and j < len(right):
            if nums[left[i]] <= nums[right[j]]:
                counts[left[i]] += right_count
                merged.append(left[i])
                i += 1
            else:
                right_count += 1
                merged.append(right[j])
                j += 1
        while i < len(left):
            counts[left[i]] += right_count
            merged.append(left[i])
            i += 1
        merged.extend(right[j:])
        return merged

    # ------------------------------------------------------------------
    # Variant: Binary Indexed Tree (Fenwick tree) over coordinate-
    # compressed values, walked right to left. Cross-ref topic 26.
    # ------------------------------------------------------------------
    def countSmaller_bit(self, nums: List[int]) -> List[int]:
        if not nums:
            return []
        sorted_unique = sorted(set(nums))
        rank = {v: i + 1 for i, v in enumerate(sorted_unique)}  # 1-indexed
        size = len(sorted_unique)
        tree = [0] * (size + 1)

        def update(i: int) -> None:
            while i <= size:
                tree[i] += 1
                i += i & (-i)

        def query(i: int) -> int:
            s = 0
            while i > 0:
                s += tree[i]
                i -= i & (-i)
            return s

        result = [0] * len(nums)
        for i in range(len(nums) - 1, -1, -1):
            r = rank[nums[i]]
            result[i] = query(r - 1)
            update(r)
        return result

    # ------------------------------------------------------------------
    # Naive baseline -- priced, not the answer.
    # ------------------------------------------------------------------
    def countSmaller_brute_force(self, nums: List[int]) -> List[int]:
        """✗ NAIVE -- O(n^2): for every i, scan every j > i directly."""
        n = len(nums)
        counts = [0] * n
        for i in range(n):
            for j in range(i + 1, n):
                if nums[j] < nums[i]:
                    counts[i] += 1
        return counts


# ==============================================================================
# TESTS -- run:  python 008_count_of_smaller_numbers_after_self_solution.py
# ==============================================================================
CASES = [
    ([5, 2, 6, 1], [2, 1, 1, 0]),
    ([-1], [0]),
    ([-1, -1], [0, 0]),
    ([1, 2, 3, 4], [0, 0, 0, 0]),
    ([4, 3, 2, 1], [3, 2, 1, 0]),
    ([2, 0, 1], [2, 0, 0]),
    ([1, 1, 1, 1], [0, 0, 0, 0]),
    ([5, -7, 9, 1, 3, 5, -2, 1], None),  # verified via brute-force cross-check below
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: merge sort with right-side counter ---")
    for nums, expected in CASES:
        if expected is None:
            continue
        got = sol.countSmaller(list(nums))
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  countSmaller({nums}) -> {got} (expected {expected})")

    print("\n--- correctness: Fenwick tree (BIT), cross-checked against merge sort ---")
    for nums, _ in CASES:
        want = sol.countSmaller(list(nums))
        got = sol.countSmaller_bit(list(nums))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  bit({nums}) -> {got}  (want {want})")

    print("\n--- correctness: brute force, cross-checked ---")
    for nums, _ in CASES:
        want = sol.countSmaller(list(nums))
        got = sol.countSmaller_brute_force(list(nums))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  brute({nums}) -> {got}  (want {want})")

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: [5, 2, 6, 1] ---")
    nums = [5, 2, 6, 1]
    counts = [0] * len(nums)

    def traced_merge_sort(idxs, depth=0):
        indent = "  " * depth
        if len(idxs) <= 1:
            print(f"{indent}base case: idxs={idxs} vals={[nums[i] for i in idxs]}")
            return idxs
        mid = len(idxs) // 2
        left = traced_merge_sort(idxs[:mid], depth + 1)
        right = traced_merge_sort(idxs[mid:], depth + 1)
        merged = []
        i = j = right_count = 0
        while i < len(left) and j < len(right):
            if nums[left[i]] <= nums[right[j]]:
                print(f"{indent}take left idx={left[i]} (val={nums[left[i]]}); "
                      f"counts[{left[i]}] += right_count({right_count})")
                counts[left[i]] += right_count
                merged.append(left[i]); i += 1
            else:
                print(f"{indent}take right idx={right[j]} (val={nums[right[j]]}); right_count -> {right_count+1}")
                right_count += 1
                merged.append(right[j]); j += 1
        while i < len(left):
            print(f"{indent}(leftover) take left idx={left[i]}; counts[{left[i]}] += right_count({right_count})")
            counts[left[i]] += right_count
            merged.append(left[i]); i += 1
        merged.extend(right[j:])
        print(f"{indent}merged: {merged} -> vals {[nums[k] for k in merged]}")
        return merged

    traced_merge_sort(list(range(len(nums))))
    print(f"  final counts = {counts}")

    # ----------------------------------------------------------------------
    # Randomised cross-check, all three implementations.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check (merge sort vs BIT vs brute force), 500 trials ---")
    random.seed(315)
    mismatches = 0
    for _ in range(500):
        n = random.randint(0, 30)
        nums = [random.randint(-50, 50) for _ in range(n)]
        r1 = sol.countSmaller(list(nums))
        r2 = sol.countSmaller_bit(list(nums))
        r3 = sol.countSmaller_brute_force(list(nums))
        if not (r1 == r2 == r3):
            mismatches += 1
    print(f"  500 random arrays: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # Benchmark: O(n log n) merge sort / BIT vs O(n^2) brute force.
    # ----------------------------------------------------------------------
    print("\n--- O(n log n) merge sort vs O(n^2) brute force: measured runtime ---")
    print(f"  {'n':>8} {'merge sort':>12} {'BIT':>10} {'brute force':>14}")
    random.seed(15)
    for n in (200, 800, 3_200):
        nums = [random.randint(-10**4, 10**4) for _ in range(n)]
        t0 = time.perf_counter(); sol.countSmaller(list(nums)); t1 = time.perf_counter()
        sol.countSmaller_bit(list(nums)); t2 = time.perf_counter()
        sol.countSmaller_brute_force(list(nums)); t3 = time.perf_counter()
        ms_ms = (t1 - t0) * 1000
        bit_ms = (t2 - t1) * 1000
        bf_ms = (t3 - t2) * 1000
        print(f"  {n:>8} {ms_ms:>10.2f}ms {bit_ms:>8.2f}ms {bf_ms:>12.2f}ms")
    print("  (as n grows, brute force's O(n^2) cost should pull away from both")
    print("   O(n log n) approaches -- the ratio growth is the complexity gap")
    print("   made visible, not merely asserted.)")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
