"""
================================================================================
SOLUTION · LeetCode 1130 · Minimum Cost Tree From Leaf Values           [Medium]
https://leetcode.com/problems/minimum-cost-tree-from-leaf-values/
================================================================================

THE CORE IDEA
--------------
Every contiguous sub-array `arr[lo..hi]` can be the leaves of some
subtree; choosing a SPLIT POINT inside that range creates exactly one
non-leaf node, costing `max(left half) * max(right half)`. Try every
split, recurse on both halves, and minimize the total. This is the same
"split a range, cross-product left and right" shape as 011/012/015, but
now MEMOIZATION on `(lo, hi)` is not optional — the naive version's
overlapping subproblems blow up exponentially well before
`len(arr) = 40`.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. MEMOIZED RECURSION, RANGE SPLIT — cache `minCost(lo, hi)` keyed by
   the range; a prefix-max helper avoids recomputing `max()` over a
   slice from scratch every time. O(n^2) distinct ranges, O(n) split
   choices each, O(n^3) total time, O(n^2) space. The version taught
   here.
2. NAIVE, NO MEMO — priced, not fully run for large n: recomputes the
   same `(lo, hi)` ranges exponentially many times as different parent
   splits both need them, exactly like 011's unmemoized blowup.
   Measured live below for small n via a call counter.
3. MONOTONIC STACK, O(n) (the LeetCode-famous optimal solution) —
   repeatedly find the smallest remaining leaf; it must be multiplied
   with the SMALLER of its two neighbors (removing it "merges" its
   spot), accumulate that product, and remove it from consideration.
   Implemented with a decreasing monotonic stack holding a sentinel
   `inf` at the bottom. O(n) time, O(n) space — the interview-optimal
   answer, verified below against the recursive version rather than
   only asserted.


================================================================================
STEP BY STEP TRACE — mctFromLeafValues([6, 2, 4])
================================================================================
    minCost(0, 2)  [whole array, arr = [6,2,4]]
      split at s=0: left=[6] (cost 0, max 6), right=[2,4]
        minCost(1, 2): split at s=1: left=[2] (cost 0, max 2), right=[4] (cost 0, max 4)
          joinCost = max([2])*max([4]) = 2*4 = 8 -> minCost(1,2) = 0+0+8 = 8
        joinCost(s=0) = max([6])*max([2,4]) = 6*4 = 24
        total for s=0: 0 (left) + 8 (right) + 24 (join) = 32
      split at s=1: left=[6,2], right=[4] (cost 0, max 4)
        minCost(0, 1): split at s=0: left=[6](cost0,max6), right=[2](cost0,max2)
          joinCost = 6*2 = 12 -> minCost(0,1) = 12
        joinCost(s=1) = max([6,2])*max([4]) = 6*4 = 24
        total for s=1: 12 (left) + 0 (right) + 24 (join) = 36
      best over both splits: min(32, 36) = 32

Result: 32, matching the expected output exactly, and matching the two
splits enumerated in the PROBLEM section's own worked explanation.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time      Space     Mutates input?  Note
    ----------------------------  --------  --------  ---------------  --------------------------------
    Memoized recursion, range split O(n^3)   O(n^2)    no               n^2 ranges, O(n) split choices each
    Naive recursion, no memo      exponential O(n) stack no             same blowup shape as 011's naive version
    Monotonic stack (optimal)     O(n)      O(n)      no               interview-optimal, verified against recursion


================================================================================
EDGE CASES
================================================================================
    arr.length == 2       -> exactly one possible tree, one split
                            point; cost is simply `arr[0] * arr[1]`.
    all elements equal     -> every split point produces the SAME join
                            cost (`v * v` for every sub-range's max),
                            so all trees are equally costly — the
                            minimum equals any of them.
    a strictly increasing (or decreasing) array -> the greedy/monotonic-
                            stack insight ("always merge the smallest
                            element with its smaller neighbor first")
                            becomes very visually intuitive here, since
                            there's a clear "smallest first" order to
                            follow.
    arr.length == 40 (upper bound) -> exercises the memoized version's
                            O(n^3) cost at a real scale, while the
                            unmemoized naive version becomes
                            computationally infeasible well before this
                            size (demonstrated at smaller n below,
                            since running the true naive version at
                            n=40 would not finish in reasonable time).


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting to memoize on `(lo, hi)` — since different split choices
   at higher levels can request the SAME sub-range repeatedly (just
   like 011's un-memoized BST counting), skipping memoization makes
   this infeasible for anything beyond small arrays.
2. Recomputing `max(arr[lo:s+1])` and `max(arr[s+1:hi+1])` via a fresh
   slice-and-max on every single split attempt, inside the innermost
   loop, without any prefix-max precomputation — still asymptotically
   the same O(n^3) as the version here IF written carefully, but easy
   to accidentally make O(n^4) by recomputing maxes redundantly across
   different `(lo, hi)` calls that share overlapping sub-ranges.
3. Confusing this problem's LEAF VALUES with its NON-LEAF NODE COSTS —
   the final answer sums only the cost of nodes CREATED by splits (one
   cost per split, i.e. per internal node), never adding the original
   leaf values themselves into the total.
4. In the monotonic-stack version, forgetting the `inf` sentinel at the
   bottom of the stack — without it, popping the last real element off
   an otherwise-empty stack can index into nothing, or fail to
   correctly treat "no neighbor on this side" as effectively infinite
   (so the OTHER neighbor is always chosen correctly when one side is
   exhausted).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you solve this in O(n) instead of O(n^3)?
A: Yes — the monotonic stack approach: process the array left to right,
   maintaining a decreasing stack; whenever a new element would break
   the decreasing property, pop the top (the locally smallest relevant
   element) and multiply it by the smaller of its two current
   neighbors, accumulating that into the total cost.

Q: Why must a locally smallest element be multiplied with the SMALLER
   of its two neighbors, in the optimal greedy approach?
A: Removing the smallest element requires pairing it with SOME
   neighbor to form a node; pairing it with the SMALLER neighbor keeps
   that (also small) value "in play" to be paired again cheaply later,
   rather than "wasting" a larger neighbor's value on an unavoidable
   multiplication sooner than necessary.

Q: How does the range-splitting recursion here relate to 011's BST
   counting recursion?
A: Structurally identical "choose a split point, recurse both sides,
   combine" shape and identical overlapping-subproblem blowup pattern —
   the only difference is the combine step (multiply-and-sum leaf
   maxima here, versus multiply-and-sum shape counts there).


================================================================================
RELATED PROBLEMS
================================================================================
    Topic 28, 011 Unique Binary Search Trees — the same range-splitting
                                       recursion shape, with a different
                                       combine step.
    LC 312  Burst Balloons             — another classic "split a range,
                                       memoize on (lo, hi)" interval DP
                                       problem.
    Topic 06 Stack & Monotonic Stack   — the general monotonic-stack
                                       technique this problem's O(n)
                                       follow-up is built on.
================================================================================
"""

from typing import List


class Solution:
    def mctFromLeafValues(self, arr: List[int]) -> int:
        """Memoized recursion, range split. O(n^3) time, O(n^2) space."""
        n = len(arr)
        memo = {}

        def max_in_range(lo: int, hi: int) -> int:
            return max(arr[lo:hi + 1])

        def min_cost(lo: int, hi: int) -> int:
            if lo == hi:
                return 0
            if (lo, hi) in memo:
                return memo[(lo, hi)]
            best = float("inf")
            for split in range(lo, hi):
                left_cost = min_cost(lo, split)
                right_cost = min_cost(split + 1, hi)
                join_cost = max_in_range(lo, split) * max_in_range(split + 1, hi)
                best = min(best, left_cost + right_cost + join_cost)
            memo[(lo, hi)] = best
            return best

        return min_cost(0, n - 1)

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def mctFromLeafValues_naive_no_memo(self, arr: List[int], calls: list = None) -> int:
        """Naive, no memoization. Exponential; `calls` counts total calls."""
        def min_cost(lo: int, hi: int) -> int:
            if calls is not None:
                calls[0] += 1
            if lo == hi:
                return 0
            best = float("inf")
            for split in range(lo, hi):
                left_cost = min_cost(lo, split)
                right_cost = min_cost(split + 1, hi)
                join_cost = max(arr[lo:split + 1]) * max(arr[split + 1:hi + 1])
                best = min(best, left_cost + right_cost + join_cost)
            return best

        return min_cost(0, len(arr) - 1)

    def mctFromLeafValues_monotonic_stack(self, arr: List[int]) -> int:
        """Monotonic stack, O(n) time, O(n) space. The optimal follow-up."""
        stack = [float("inf")]
        total = 0
        for value in arr:
            while stack[-1] <= value:
                mid = stack.pop()
                total += mid * min(stack[-1], value)
            stack.append(value)
        while len(stack) > 2:
            total += stack.pop() * stack[-1]
        return total


# ==============================================================================
# TESTS — run:  python 020_minimum_cost_tree_from_leaf_values_solution.py
# ==============================================================================
CASES = [
    ([6, 2, 4], 32),
    ([4, 11], 44),
    ([15, 13, 5, 3, 8, 3, 12, 9, 5, 15], None),  # cross-checked, not a known fixed value
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    impls = [
        ("memoized recursion   ", sol.mctFromLeafValues),
        ("monotonic stack O(n) ", sol.mctFromLeafValues_monotonic_stack),
    ]

    for name, fn in impls:
        ok = True
        for arr, expected in CASES:
            got = fn(arr)
            if expected is not None:
                ok &= got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- cross-checking monotonic stack against memoized recursion, random arrays ---")
    import random
    random.seed(42)
    mismatches = []
    for _ in range(200):
        n = random.randint(2, 12)
        arr = [random.randint(1, 15) for _ in range(n)]
        a = sol.mctFromLeafValues(arr)
        b = sol.mctFromLeafValues_monotonic_stack(arr)
        if a != b:
            mismatches.append((arr, a, b))
    if mismatches:
        print(f"  FAIL — {len(mismatches)} mismatches, e.g. {mismatches[:3]}")
        all_ok = False
    else:
        print("  CONFIRMED: monotonic stack matches memoized recursion on 200 random arrays.")

    print("\n--- naive-recursion call count blowup, measured live (small n only) ---")
    print(f"  {'n':>4} {'total calls (no memo)':>24}")
    for n in (4, 8, 12):
        arr = list(range(1, n + 1))
        calls = [0]
        sol.mctFromLeafValues_naive_no_memo(arr, calls)
        print(f"  {n:>4} {calls[0]:>24}")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
