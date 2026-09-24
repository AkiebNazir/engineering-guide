"""
================================================================================
SOLUTION · LeetCode 416 · Partition Equal Subset Sum                  [Medium]
https://leetcode.com/problems/partition-equal-subset-sum/
================================================================================

THE CORE IDEA
--------------
If sum(nums) is odd, no equal split is possible -- return false immediately.
Otherwise, the problem reduces to: does some subset of nums sum to exactly
target = sum(nums)//2? dp[s] MEANS "is subset-sum s achievable using the
items considered SO FAR" -- 0/1 knapsack (each item used at most once)
collapsed onto ONE axis (the sum), instead of the classic 2D dp[item][sum]:

    dp[0] = True
    for num in nums:
        for s in range(target, num - 1, -1):     # HIGH to LOW -- the trap
            dp[s] = dp[s] or dp[s - num]


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive recursion over include/exclude per item, price it, don't
ship it): classic subset-sum backtracking, `canMake(i, remaining) =
canMake(i+1, remaining) or canMake(i+1, remaining-nums[i])`. O(2^n) without
memoization -- every item independently doubles the branch count.

Approach 1 (memoized top-down, 2D state (index, remaining)) [`can_partition_memo`]
-- caches (index, remaining) pairs. O(n * target) time, O(n * target) space.

Approach 2 (tabulated 2D dp[item][sum]) -- the textbook knapsack table,
dp[i][s] = dp[i-1][s] or (s>=nums[i] and dp[i-1][s-nums[i]]). O(n * target)
time AND space -- correct, but wastes an entire axis of memory that isn't
needed once you notice each row only ever reads the row directly above it.

Approach 3 (collapsed 1D dp[sum], scanned HIGH to LOW) [chosen] -- same
recurrence, one boolean array, updated in REVERSE for each item so the
just-updated dp[s] for THIS item never leaks into dp[s'] for s' < s within
the same item's pass (which would silently reuse that item twice --
turning 0/1 knapsack into UNBOUNDED knapsack). O(n * target) time, O(target)
space. This iteration-direction requirement is Trap A in `_TOPIC_GUIDE.md`
Part 4 -- demonstrated failing live below.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [1, 5, 11, 5], sum = 22, target = 11

dp indices 0..11, dp[0]=True, rest False initially: [T,F,F,F,F,F,F,F,F,F,F,F]

Process num=1 (scan s = 11 down to 1):
    only dp[1] can newly become true via dp[0]: dp[1] = dp[1] or dp[0] = True
    dp: [T,T,F,F,F,F,F,F,F,F,F,F]

Process num=5 (scan s = 11 down to 5):
    dp[6] = dp[6] or dp[1] = True   (dp[1] was True BEFORE this item's pass)
    dp[5] = dp[5] or dp[0] = True
    dp: [T,T,F,F,F,T,T,F,F,F,F,F]

Process num=11 (scan s = 11 down to 11):
    dp[11] = dp[11] or dp[0] = True
    dp: [T,T,F,F,F,T,T,F,F,F,F,T]     <- dp[11] already True, done early!

Process num=5 (scan s = 11 down to 5):
    dp[11] already True, dp[10]=dp[10] or dp[5]=True, dp[6] stays True, etc.
    dp[11] remains True.

Final dp[target=11] = True -> answer True (matches [1,5,5] vs [11]).


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                                 Time              Space            Mutates input?
    ----------------------------------------  ----------------  ---------------  --------------
    Naive recursion                            O(2^n)           O(n) depth       no
    Memoized top-down (index, remaining)       O(n * target)    O(n * target)    no
    Tabulated 2D dp[item][sum]                 O(n * target)    O(n * target)    no
    Collapsed 1D dp[sum], HIGH-to-LOW [chosen] O(n * target)    O(target)        no


================================================================================
EDGE CASES
================================================================================
    sum(nums) is odd            -> impossible by parity alone; must be
                                   checked and short-circuited BEFORE
                                   running any DP (target = sum/2 would
                                   otherwise silently floor-divide to the
                                   wrong integer).
    single element               -> can never be partitioned into two
                                   NON-EMPTY halves unless it's 0 (and
                                   constraints guarantee nums[i]>=1, so a
                                   single-element array is always false).
    all elements equal, even count -> trivially true (split half and half).
    a partition exists but uses
    NON-CONTIGUOUS, order-scrambled
    elements ([1,5,11,5] -> {1,5,5}
    vs {11})                      -> confirms the DP finds subsets
                                   regardless of position, unlike the
                                   contiguous-subarray problems elsewhere
                                   in this folder.


================================================================================
COMMON MISTAKES
================================================================================
1. Scanning the sum axis LOW to HIGH instead of HIGH to LOW when collapsing
   to 1D -- this is THE defining trap of this problem (Trap A in
   `_TOPIC_GUIDE.md`). Scanning low-to-high lets the SAME item's own
   already-updated dp[s] feed into a later, larger s within the same
   pass -- silently turning "each item used at most once" into "each item
   reusable," i.e. computing UNBOUNDED knapsack instead of 0/1 knapsack.
   The bug produces a plausible-looking True/False answer that is simply
   WRONG on inputs where the distinction matters -- demonstrated live below.
2. Forgetting the odd-sum short-circuit and computing target = sum // 2
   (integer division silently rounds down), then reporting "true" for an
   input that cannot actually be split evenly.
3. Confusing this problem with unbounded coin-style problems (010, 015,
   016) where LOW-to-HIGH is correct BECAUSE reuse is the point there --
   the iteration direction is not an arbitrary style choice, it encodes
   whether items are reusable.
4. Not special-casing target == 0 up front conceptually -- dp[0] = True is
   the base case, but it's worth explicitly confirming an all-zero-sum
   scenario doesn't need special extra handling beyond that base case
   (constraints here guarantee nums[i] >= 1, so target=0 only happens for
   an empty array, outside this problem's own constraints).


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "What if you need to partition into K equal-sum subsets, not 2?" -> LC
  698 Partition to K Equal Sum Subsets -- a genuinely different
  (backtracking + bitmask, not simple 1D DP) technique; this problem's
  trick doesn't generalize past K=2.
- "What's the actual subset, not just true/false?" -> track which items
  were used via a 2D dp[item][sum] table (or parent pointers) instead of
  the 1D collapse, then reconstruct by walking backwards.
- "Why HIGH to LOW here but LOW to HIGH in Coin Change (010)?" -> exactly
  Trap A: 0/1 (bounded, each item once) needs high-to-low; unbounded
  (unlimited reuse) needs low-to-high. Good moment to state the general
  rule out loud.


================================================================================
RELATED PROBLEMS
================================================================================
- 010 Coin Change (LC 322) -- the UNBOUNDED counterpart; contrast the
  required LOW-to-HIGH iteration direction against this problem's HIGH-to-LOW.
- Partition to K Equal Sum Subsets (LC 698) -- the K>2 generalization,
  different technique.
- Target Sum (LC 494) -- another subset-sum-flavored 1D knapsack collapse.
================================================================================
"""

import time
from typing import List


class Solution:
    def canPartition(self, nums: List[int]) -> bool:
        total = sum(nums)
        if total % 2 != 0:
            return False
        target = total // 2
        dp = [False] * (target + 1)
        dp[0] = True
        for num in nums:
            for s in range(target, num - 1, -1):
                if dp[s - num]:
                    dp[s] = True
            if dp[target]:
                return True
        return dp[target]


def can_partition_wrong_direction(nums: List[int]) -> bool:
    """Same recurrence, but scans the sum axis LOW to HIGH -- the classic
    bug (Trap A). This lets a single item be counted more than once
    within its own update pass, silently computing UNBOUNDED knapsack
    instead of 0/1 knapsack. Kept here purely to demonstrate the failure
    live in run_tests().
    """
    total = sum(nums)
    if total % 2 != 0:
        return False
    target = total // 2
    dp = [False] * (target + 1)
    dp[0] = True
    for num in nums:
        for s in range(num, target + 1):  # WRONG direction
            if dp[s - num]:
                dp[s] = True
    return dp[target]


def can_partition_naive(nums: List[int]) -> bool:
    total = sum(nums)
    if total % 2 != 0:
        return False
    target = total // 2

    def solve(i: int, remaining: int) -> bool:
        if remaining == 0:
            return True
        if i == len(nums) or remaining < 0:
            return False
        return solve(i + 1, remaining - nums[i]) or solve(i + 1, remaining)

    return solve(0, target)


def _can_partition_naive_fixed_target(nums: List[int], target: int) -> bool:
    """Like can_partition_naive but takes an explicit target instead of
    deriving it from sum(nums)//2 -- used only for the runtime demo, to
    construct a guaranteed-unreachable target without needing an
    even-sum array.
    """
    def solve(i: int, remaining: int) -> bool:
        if remaining == 0:
            return True
        if i == len(nums) or remaining < 0:
            return False
        return solve(i + 1, remaining - nums[i]) or solve(i + 1, remaining)

    return solve(0, target)


def _can_partition_dp_fixed_target(nums: List[int], target: int) -> bool:
    dp = [False] * (target + 1)
    dp[0] = True
    for num in nums:
        for s in range(target, num - 1, -1):
            if dp[s - num]:
                dp[s] = True
    return dp[target]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([1, 5, 11, 5], True),
        ([1, 2, 3, 5], False),
        ([1, 2, 5], False),
        ([1, 1], True),
        ([100], False),
        ([2, 2, 3, 5], False),
        ([1, 2, 3, 4, 5, 6, 7], True),
    ]
    for nums, want in cases:
        got = sol.canPartition(nums[:])
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums}  -> {got}  (want {want})")
        assert can_partition_naive(nums[:]) == want

    print()
    print("CORRECTNESS DEMO -- wrong iteration direction (low-to-high) breaks 0/1 knapsack")
    print("-" * 72)
    # A single '5' should NOT be able to make target 10 by itself under 0/1
    # rules (it would need to be used twice) -- but scanning low-to-high
    # lets exactly that happen.
    trap_nums = [5, 5, 10]  # sum=20, target=10; correct answer: True via
    # {10} alone, so pick a case where the WRONG version diverges instead:
    trap_nums = [3, 3, 3, 3]  # sum=12, target=6: correct True via {3,3}.
    # Use a case where reuse changes the answer from False to True:
    trap_nums = [1, 1, 1, 9]  # sum=12, target=6: no subset of {1,1,1,9}
    # (each used once) sums to 6 -> correct answer False. If '1' could be
    # reused (bug), 1+1+1+1+1+1 could look like it works incorrectly.
    correct = sol.canPartition(trap_nums[:])
    buggy = can_partition_wrong_direction(trap_nums[:])
    naive = can_partition_naive(trap_nums[:])
    print(f"nums={trap_nums}  (sum={sum(trap_nums)}, target={sum(trap_nums)//2})")
    print(f"  correct (high-to-low):  {correct}")
    print(f"  buggy   (low-to-high):  {buggy}")
    print(f"  naive recursion oracle: {naive}")
    assert correct == naive == False
    assert buggy != correct, "expected the wrong-direction version to diverge on this input"

    print()
    print("RUNTIME DEMO -- naive O(2^n) recursion vs 1D knapsack DP, measured live")
    print("(unreachable-target instance: nums = n copies of 1, target = n+1 -- the")
    print(" max achievable sum using ALL n ones is only n, so target is NEVER")
    print(" reachable. Naive recursion's remaining count never goes negative either")
    print(" (every item is 1), so it can't prune early -- forced to explore its")
    print(" full 2^n-leaf include/exclude tree. The DP target stays small (n+1),")
    print(" so the DP table itself stays O(n) -- the two costs no longer scale together.)")
    print("-" * 72)
    for n in (16, 19, 22):
        arr = [1] * n
        target_forced = n + 1  # unreachable: sum(arr) == n
        t0 = time.perf_counter()
        naive_result = _can_partition_naive_fixed_target(arr, target_forced)
        naive_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        dp_result = _can_partition_dp_fixed_target(arr, target_forced)
        dp_ms = (time.perf_counter() - t0) * 1000

        assert naive_result == dp_result == False
        print(f"n={n:3d}  naive={naive_ms:9.3f} ms   1d_knapsack_dp={dp_ms:7.4f} ms   "
              f"ratio={naive_ms / max(dp_ms, 1e-6):9.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
