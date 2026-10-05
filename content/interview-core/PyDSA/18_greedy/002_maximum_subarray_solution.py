"""
================================================================================
SOLUTION · LeetCode 53 · Maximum Subarray                              [Medium]
https://leetcode.com/problems/maximum-subarray/
================================================================================

THE CORE IDEA
--------------
Kadane's algorithm: walk left to right keeping a running sum `curr` of "the
best subarray sum ending exactly at the current index." At each index, make
one greedy decision — extend the running subarray by including `nums[i]`, or
abandon everything before it and restart fresh at `nums[i]` alone. Take
whichever is bigger: `curr = max(nums[i], curr + nums[i])`. Track the best
`curr` seen across all indices as the answer.

EXCHANGE ARGUMENT (why "drop a negative running prefix" is safe)
-------------------------------------------------------------------
Claim: if `curr < 0` at some index, no optimal subarray that starts before
this index and extends past it can be better than one that just starts
here. Proof: let `S` be any subarray ending at index i or later that
includes the negative-summing prefix `P` (with `sum(P) < 0`) as its
beginning. Removing `P` from the front of `S` strictly increases its sum
(you're subtracting a negative number). So `S` was NOT optimal — the
subarray `S` minus that negative prefix is strictly better. Hence any
optimal subarray never carries a negative-summing prefix; resetting `curr`
to `nums[i]` whenever the running sum would go negative loses nothing. This
is the complete exchange argument — not just "seems reasonable."

Optimal substructure: the best subarray ending at i is either (a) the best
subarray ending at i-1, extended by `nums[i]`, or (b) `nums[i]` alone
starting fresh — and the overall answer is the max over all i of "best
subarray ending at i." Each subproblem ("best ending exactly here") only
needs ONE number of state (the previous `curr`) to solve the next one —
that collapsibility to O(1) state is exactly what makes this greedy instead
of a full DP table.

================================================================================
APPROACH 0 · Brute force — all O(n^2) subarrays (priced, not coded as the
answer)
================================================================================
For every pair (i, j) with i <= j, sum `nums[i..j]` and track the max.
Naively summing each subarray from scratch is O(n^3); accumulating the sum
as j grows for a fixed i brings it to O(n^2). Correct, and fine for a first
pass in an interview to show you understand the brute force before
optimizing — but should not be the final coded answer given the constraints
(n up to 10^5 would time out).

================================================================================
APPROACH 1 · Kadane's algorithm ✅ (the answer)
================================================================================
    def maxSubArray(nums):
        best = curr = nums[0]
        for x in nums[1:]:
            curr = max(x, curr + x)
            best = max(best, curr)
        return best

    Time:  O(n) — single pass
    Space: O(1) — two running scalars

================================================================================
APPROACH 2 · Divide and conquer, O(n log n)
================================================================================
Split the array in half. The max subarray either lies entirely in the left
half, entirely in the right half, or CROSSES the midpoint. Recurse on the
two halves; for the "crosses the midpoint" case, greedily extend left from
mid and right from mid+1 independently (each is itself a small Kadane-style
scan) and add the two best extensions together. `T(n) = 2T(n/2) + O(n)` =>
O(n log n) by the Master theorem. Strictly worse than Approach 1 here, but
worth knowing as the classic interviewer follow-up ("can you do it without
the linear scan trick") and because the same divide-and-conquer shape
reappears in other problems (closest pair of points, inversions count).

================================================================================
APPROACH 3 (for contrast, not this problem) · DP table
================================================================================
You COULD write `dp[i] = max(nums[i], dp[i-1] + nums[i])` as an explicit
array and take `max(dp)` — this is literally Kadane's algorithm with the
O(1) rolling state promoted to a full O(n) table. It is correct but wastes
O(n) space for information that never needs more than the single previous
value — a clean illustration of "when the DP state collapses to O(1) history,
you don't need the table; that's what makes it greedy," per the topic guide
§1.

--------------------------------------------------------------------------------
STEP BY STEP TRACE
--------------------------------------------------------------------------------
nums = [-2, 1, -3, 4, -1, 2, 1, -5, 4]

  i=0: curr=-2, best=-2
  i=1 (x=1):  curr = max(1, -2+1=-1) = 1     best = max(-2, 1) = 1
  i=2 (x=-3): curr = max(-3, 1-3=-2) = -2    best = max(1, -2) = 1
  i=3 (x=4):  curr = max(4, -2+4=2) = 4      best = max(1, 4) = 4
  i=4 (x=-1): curr = max(-1, 4-1=3) = 3      best = max(4, 3) = 4
  i=5 (x=2):  curr = max(2, 3+2=5) = 5       best = max(4, 5) = 5
  i=6 (x=1):  curr = max(1, 5+1=6) = 6       best = max(5, 6) = 6
  i=7 (x=-5): curr = max(-5, 6-5=1) = 1      best = max(6, 1) = 6
  i=8 (x=4):  curr = max(4, 1+4=5) = 5       best = max(6, 5) = 6

  return best = 6   (the subarray [4,-1,2,1], matching the expected answer)

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                        | Time         | Space  | Mutates input? |
|-----------------------------------|-------------|--------|-----------------|
| 0 · brute force (all subarrays)  | O(n^2)       | O(1)   | No              |
| 1 · Kadane's ✅                   | O(n)         | O(1)   | No              |
| 2 · divide and conquer            | O(n log n)   | O(log n) recursion stack | No |
| 3 · explicit DP table (for contrast) | O(n)      | O(n)   | No              |

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- Single element: `best = curr = nums[0]`, loop body never runs — correct.
- All negative numbers: the "restart fresh" branch never actually helps
  since every option is negative, so the algorithm correctly returns the
  LARGEST (least negative) single element, not 0 — the problem requires at
  least one number, so an empty subarray is never a valid alternative.
- All positive numbers: `curr` never resets, algorithm degenerates to a
  running total across the whole array — correct, the whole array is the
  answer.
- Two elements where the sum is worse than either alone (e.g. `[5, -20]`):
  correctly returns `5`, not `-15`, since `curr = max(-20, 5-20) = -15` is
  still less than the max of `5`, so `best` stays `5`.

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. Initializing `best = 0` instead of `best = nums[0]` — silently wrong on
   all-negative arrays, since it would incorrectly allow the "empty
   subarray" answer of 0 even though the problem requires at least one
   element.
2. Resetting `curr = 0` whenever `curr` goes negative, but forgetting to
   still compare `curr` against `nums[i]` alone at that same index — the
   compact form `curr = max(x, curr + x)` already does both in one
   expression; a common bug is writing `curr = max(0, curr) + x`, which
   silently breaks on an all-negative array (best would end up 0-ish).
3. **Looks-greedy-but-wrong: tracking only the running sum without ever
   comparing it to `best`** — someone might assume "the final curr is the
   answer" since Kadane's IS a single running variable, but the maximum can
   occur mid-array before a big negative drop at the end (see index 6 in
   the trace above: `best` locks in 6 even though `curr` later drops to 1
   and 5) — you must track `best` separately from `curr`.
4. Off-by-one in the divide-and-conquer "crossing" case — forgetting the
   crossing subarray must include BOTH `mid` and `mid+1`, or double-counting
   `mid`.

--------------------------------------------------------------------------------
RUNTIME DEMO — O(n) Kadane's vs. O(n²) brute force, measured on this machine
--------------------------------------------------------------------------------
See the code below.

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "Return the actual subarray, not just the sum" — track `start`/`end`
  indices alongside `curr`, resetting `start = i` whenever you restart.
- "What if you need the max sum of a CIRCULAR subarray?" (LC 918) — either
  the max subarray is the normal Kadane's answer, or it wraps around, in
  which case `total - min_subarray` (via Kadane's on negated values) is the
  wrap-around candidate; take the max of the two (careful with the
  all-negative edge case where wrapping would wrongly produce an empty
  array).
- "O(n log n) alternative?" — divide and conquer, Approach 2 above.
- "What if elements can be 0-weighted or you want the max subarray PRODUCT
  instead of sum?" — different problem (LC 152): product's sign flips
  matter, so you must track both a running max AND running min at each
  step, since a very negative running product can become the best positive
  one after one more negative multiply.

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- LC 918 Maximum Sum Circular Subarray — direct extension, see follow-ups.
- LC 152 Maximum Product Subarray — same running-window idea, but needs a
  running min AND max because of sign flips.
- 18/003 Jump Game, 18/005 Gas Station — same "single left-to-right scan
  with a running best-so-far" pattern family (topic guide §2.1).
================================================================================
"""

import random
import time


class Solution:
    def maxSubArray(self, nums: list[int]) -> int:
        best = curr = nums[0]
        for x in nums[1:]:
            curr = max(x, curr + x)
            best = max(best, curr)
        return best


def max_subarray_brute_force(nums: list[int]) -> int:
    n = len(nums)
    best = nums[0]
    for i in range(n):
        running = 0
        for j in range(i, n):
            running += nums[j]
            if running > best:
                best = running
    return best


def run_tests():
    sol = Solution()
    assert sol.maxSubArray([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6
    assert sol.maxSubArray([1]) == 1
    assert sol.maxSubArray([5, 4, -1, 7, 8]) == 23
    assert sol.maxSubArray([-1]) == -1
    assert sol.maxSubArray([-3, -2, -1]) == -1
    assert sol.maxSubArray([5, -20]) == 5
    assert sol.maxSubArray([1, 2, 3, 4]) == 10

    # cross-check against brute force on random arrays
    random.seed(3)
    for _ in range(200):
        arr = [random.randint(-20, 20) for _ in range(random.randint(1, 30))]
        assert sol.maxSubArray(arr) == max_subarray_brute_force(arr)

    # does not mutate input
    original = [-2, 1, -3, 4]
    sol.maxSubArray(original)
    assert original == [-2, 1, -3, 4]

    # --- Runtime demo: O(n) Kadane's vs O(n^2) brute force, measured -------
    random.seed(11)
    big = [random.randint(-1000, 1000) for _ in range(4000)]

    t0 = time.perf_counter()
    fast_result = sol.maxSubArray(big)
    fast_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    slow_result = max_subarray_brute_force(big)
    slow_time = time.perf_counter() - t0

    assert fast_result == slow_result
    print(f"n=4000: Kadane's O(n) took {fast_time*1000:.2f} ms")
    print(f"n=4000: brute O(n^2) took {slow_time*1000:.2f} ms")
    print(f"Kadane's is {slow_time / fast_time:.1f}x faster on this run")
    assert fast_time < slow_time

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
