"""
================================================================================
SOLUTION · LeetCode 1005 · Maximize Sum Of Array After K Negations       [Easy]
https://leetcode.com/problems/maximize-sum-of-array-after-k-negations/
================================================================================

THE CORE IDEA
--------------
Sort the array. Walk left to right negating every negative number you meet
while k lasts — each such negation strictly increases the sum (flipping a
negative to positive adds `2*|x|`), and doing the MOST negative ones first is
never worse than doing a less-negative one first (see exchange argument
below). Once there are no more negatives to flip (or k runs out first), any
leftover k must be "spent" on some element:
- If k is now even, negate the same element an even number of times — net
  no-op — so just stop; the sum is already optimal.
- If k is odd, you must negate exactly one more element. Since negating
  strictly-positive-or-zero values LOWERS the sum by `2*value`, minimize the
  damage by negating the SMALLEST value currently present (after the flips
  above). Zero is special: negating it changes nothing (`-0 == 0`), so if a
  zero is present the odd-leftover case is free.

EXCHANGE ARGUMENT (why "negate the most negative first" is safe)
-------------------------------------------------------------------
Suppose an optimal plan negates some negative element `y` before a MORE
negative element `x` (`x < y < 0`), while both still have budget available.
Swap the order: negate `x` before `y` instead. Both are still negated exactly
once each — the final multiset of values, and therefore the final sum, is
IDENTICAL either way (negation only depends on how many times each element
is flipped, not the order). So "which negative gets flipped first" doesn't
even matter for elements that both get flipped — the real claim is narrower
and sharper:

**Claim that matters: you should never "waste" a negation on a non-negative
element while a negative element still has zero flips and budget remains.**
Proof: negating a negative element `x < 0` changes the sum by `+2|x| > 0`.
Negating a non-negative element `p >= 0` changes the sum by `-2p <= 0`. Doing
the first instead of the second is a strict (or non-strict, if p == 0)
improvement — a textbook exchange: take an optimal plan that flips some
non-negative `p` while a negative `x` sits unflipped with budget left, swap
that one flip from `p` to `x`; the sum does not decrease. Repeat until every
negative is flipped (or budget is exhausted) before any non-negative is
ever touched. That is the full argument for why "sort ascending, flip
negatives first" is provably safe, not just a heuristic.

A DIFFERENT (BROKEN) heuristic that looks equally plausible — "always negate
whichever element currently has the LARGEST value" (i.e. keep hitting the
biggest number) — has no such argument and the runtime demo below
constructs an input where it gives a strictly worse answer than the correct
rule.

================================================================================
APPROACH 0 · Brute force over all negation sequences (priced, not coded as
the answer — used below only as an exhaustive oracle for tiny inputs)
================================================================================
Try every possible sequence of k negations (any index, k times): a search
tree of branching factor `n` and depth `k`, i.e. O(n^k) leaves. Completely
infeasible for the real constraints (n, k up to 10^4) but useful as a
ground-truth oracle on tiny random inputs to prove the greedy rule live.

================================================================================
APPROACH 1 · Sort + greedy flip ✅ (the answer)
================================================================================
    def largestSumAfterKNegations(nums, k):
        nums.sort()
        i = 0
        n = len(nums)
        while i < n and k > 0 and nums[i] < 0:
            nums[i] = -nums[i]
            i += 1
            k -= 1
        total = sum(nums)
        if k % 2 == 1:
            total -= 2 * min(nums)
        return total

    Time:  O(n log n) — the sort dominates; the scan + sum are O(n)
    Space: O(1) extra (sort in place; O(log n) for Python's Timsort stack,
           conventionally reported as O(1) auxiliary)

================================================================================
APPROACH 2 · Min-heap instead of sort
================================================================================
Push all values onto a min-heap, pop-negate-push k times (or stop early once
the heap-min is non-negative and k is even). Same O(n log n) total in the
worst case (k can be up to n, each heap op is O(log n)) — no asymptotic win
over sorting once, and more code. Only worth it if k were guaranteed small
relative to n (then it's O(n + k log n)), which the constraints don't
promise here.

--------------------------------------------------------------------------------
STEP BY STEP TRACE
--------------------------------------------------------------------------------
nums = [2, -3, -1, 5, -4], k = 2

  sorted: [-4, -3, -1, 2, 5]
  i=0: nums[0]=-4 < 0, k=2>0 -> negate -> [4, -3, -1, 2, 5], k=1
  i=1: nums[1]=-3 < 0, k=1>0 -> negate -> [4, 3, -1, 2, 5], k=0
  k == 0 -> stop scanning
  total = 4+3-1+2+5 = 13
  k % 2 == 0 -> no further adjustment
  return 13   (matches expected output)

Second trace, showing the odd-leftover branch:
nums = [3, -1, 0, 2], k = 3

  sorted: [-1, 0, 2, 3]
  i=0: nums[0]=-1 < 0, k=3>0 -> negate -> [1, 0, 2, 3], k=2
  i=1: nums[1]=0, not < 0 -> loop stops (no more negatives)
  total = 1+0+2+3 = 6
  k=2, even -> no adjustment
  return 6   (matches expected output; the leftover 2 negations on the same
              zero-or-any element cancel out / are free on the zero)

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                    | Time         | Space | Mutates input?        |
|------------------------------|-------------|-------|------------------------|
| 0 · brute force (oracle only)| O(n^k)      | O(n^k)| No (fresh copies)      |
| 1 · sort + greedy flip ✅     | O(n log n)  | O(1)* | Yes — `nums.sort()` sorts in place, then flips elements in place |
| 2 · min-heap                 | O(n + k log n) | O(n)| No — heap is a separate list |

* O(log n) auxiliary for Timsort's internal stack, conventionally O(1).

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- A zero present when the odd-leftover branch triggers: `min(nums)` could be
  0 itself, so `total -= 2*0` is a no-op — correctly "free," matching the
  intuition that negating zero never costs anything.
- k larger than the count of negatives: the while loop naturally stops once
  `nums[i] >= 0`, leaving the correct remainder of k to fall through to the
  even/odd check.
- k == 0: loop body never executes (guarded by `k > 0`), `k % 2 == 0` is
  true, function just returns `sum(nums)` — correct, since LeetCode's stated
  constraint is k >= 1 but the code degrades correctly anyway.
- All elements already non-negative: no flips happen in the loop; if k is
  odd, the smallest non-negative element eats the leftover flip — correctly
  minimizes the damage.
- All elements negative and k exceeds the array length: every element gets
  flipped once (all become positive), remaining k is spent on the
  now-smallest (originally-largest-magnitude-negative) positive value if k
  is still odd.

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. **Looks-greedy-but-wrong: "always negate the current maximum"** — sounds
   like it should minimize damage, but it targets exactly the wrong end of
   the array; see the runtime demo below for a constructed counterexample
   where it strictly underperforms the correct minimum-targeting rule.
2. Sorting once up front and then negating in the ORIGINAL sorted order
   without re-checking after the loop — the leftover-k adjustment must use
   `min(nums)` on the ALREADY-negated array (post-loop), not the original
   pre-sort array, since the smallest value may have changed identity
   during the flip phase.
3. Applying the odd/even adjustment even when `k == 0` after the loop
   naturally exhausted itself on negatives (e.g. k was exactly the count of
   negatives) — the `k % 2` check handles this correctly on its own since
   `0 % 2 == 0`, but a common bug is a separate `if k > 0 and k % 2 == 1`
   that's redundant (harmless) or, worse, an `if k > 0` alone without the
   `% 2` that always burns a flip even when it should be a no-op.
4. Forgetting duplicates/ties don't need special handling — the rule only
   cares about value, not index identity, so `[−2, −2]` with k=1 correctly
   flips just one of the two equal minimums.
5. Using a heap but forgetting to re-push the negated value (silently
   dropping an element and corrupting the multiset / final sum).

--------------------------------------------------------------------------------
RUNTIME DEMO — provably-correct greedy vs. a plausible-but-broken heuristic
--------------------------------------------------------------------------------
See the code below: `largest_sum_wrong_heuristic` implements "always negate
the current maximum value" k times. On a constructed input it returns a sum
strictly lower than the correct algorithm — proof by counterexample that
"looks greedy" is not the same as "is provably greedy."

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "What if you could negate a contiguous subarray at once instead of a
  single element?" — different problem; would need to think about parity of
  negative counts per prefix, not a straightforward extension of this rule.
- "What if k could be less than the number of negatives and you had to
  MINIMIZE the sum instead?" — symmetric: flip the largest positives first.
- "Can you do it without sorting, faster than O(n log n)?" — yes, with a
  single pass to find the count of negatives, sum, and the minimum absolute
  value, but you must still identify "the min(nums) after flips" which
  needs either sorting or a second pass; still O(n) total in a two-pass
  version — a nice optimization to volunteer if asked for sub-O(n log n).

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- 18/007 Hand of Straights — another "sort, then a provably-safe greedy
  scan" problem in this topic.
- 06 Stack & Monotonic Stack topic's "next greater element" family — also
  relies on committing to a local decision that's provably never revisited.
================================================================================
"""

import itertools
import random
from functools import lru_cache


class Solution:
    def largestSumAfterKNegations(self, nums: list[int], k: int) -> int:
        nums = nums[:]
        nums.sort()
        i, n = 0, len(nums)
        while i < n and k > 0 and nums[i] < 0:
            nums[i] = -nums[i]
            i += 1
            k -= 1
        total = sum(nums)
        if k % 2 == 1:
            total -= 2 * min(nums)
        return total


# --------------------------------------------------------------------------
# Broken heuristic used only in the runtime demo below: always negate the
# CURRENT maximum, k times. Looks plausible ("keep the biggest number from
# dominating"), has no exchange argument, and can be beaten.
# --------------------------------------------------------------------------
def largest_sum_wrong_heuristic(nums: list[int], k: int) -> int:
    nums = nums[:]
    for _ in range(k):
        j = max(range(len(nums)), key=lambda idx: nums[idx])
        nums[j] = -nums[j]
    return sum(nums)


# --------------------------------------------------------------------------
# Exhaustive oracle (tiny inputs only): tries every sequence of k
# negations. Memoized on the sorted multiset + remaining k, since the
# achievable maximum only depends on which VALUES are still unflipped, not
# on index identity.
# --------------------------------------------------------------------------
def brute_force_oracle(nums: list[int], k: int) -> int:
    @lru_cache(maxsize=None)
    def best(state: tuple, k_left: int) -> int:
        if k_left == 0:
            return sum(state)
        options = []
        for idx in range(len(state)):
            new_state = list(state)
            new_state[idx] = -new_state[idx]
            options.append(best(tuple(sorted(new_state)), k_left - 1))
        return max(options)

    result = best(tuple(sorted(nums)), k)
    best.cache_clear()
    return result


def run_tests():
    sol = Solution()
    assert sol.largestSumAfterKNegations([4, 2, 3], 1) == 5
    assert sol.largestSumAfterKNegations([3, -1, 0, 2], 3) == 6
    assert sol.largestSumAfterKNegations([2, -3, -1, 5, -4], 2) == 13

    # k larger than count of negatives, forcing the odd/even leftover branch
    assert sol.largestSumAfterKNegations([-2, -3, -1, -5, -4], 6) == 15 - 2 * 1
    assert sol.largestSumAfterKNegations([-2, -3, -1, -5, -4], 5) == 15

    # does not mutate caller's list
    original = [4, 2, 3]
    sol.largestSumAfterKNegations(original, 1)
    assert original == [4, 2, 3], "must not mutate caller's list"

    # --- Property test: greedy matches an exhaustive oracle -----------------
    random.seed(7)
    for _ in range(200):
        n = random.randint(1, 5)
        arr = [random.randint(-6, 6) for _ in range(n)]
        k = random.randint(0, 4)
        assert sol.largestSumAfterKNegations(arr, k) == brute_force_oracle(arr, k), (
            f"mismatch on {arr}, k={k}"
        )

    # --- Counterexample demo: correct greedy vs. broken "negate-max" rule ---
    # Construct an input where repeatedly negating the current maximum is
    # strictly worse than negating the most negative values first.
    trap = [-10, 1, 1, 1, 1]
    k = 1
    correct = sol.largestSumAfterKNegations(trap, k)
    wrong = largest_sum_wrong_heuristic(trap, k)
    print(f"trap={trap}, k={k}")
    print(f"  correct (negate most-negative first): {correct}")
    print(f"  broken heuristic (always negate max):  {wrong}")
    assert correct > wrong, "expected the correct rule to strictly beat the broken one"
    assert correct == brute_force_oracle(trap, k)

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
