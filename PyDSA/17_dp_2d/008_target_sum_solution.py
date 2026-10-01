"""
================================================================================
SOLUTION · LeetCode 494 · Target Sum                                  [Medium]
https://leetcode.com/problems/target-sum/
================================================================================

THE CORE IDEA
--------------
Reframe "assign +/- to each number" as "partition nums into a POSITIVE
subset P and a NEGATIVE subset N." Then:

    sum(P) - sum(N) = target
    sum(P) + sum(N) = total          (every number is in exactly one subset)

Adding the two equations eliminates N: 2*sum(P) = target + total, so

    sum(P) = (target + total) / 2

This turns "count sign assignments" into "count SUBSETS summing to exactly
sum(P)" -- classic 0/1 KNAPSACK COUNTING: dp[i][s] = number of subsets of
the first i numbers that sum to exactly s, each number used AT MOST ONCE
(unlike 007's unbounded coin reuse):

    dp[i][s] = dp[i-1][s]                  # exclude num i from the subset
             + dp[i-1][s - nums[i-1]]      # include num i (dp[i-1]: can't
                                            #   reuse it -- 0/1, not unbounded)

If (target + total) is odd, or |target| > total, NO partition can possibly
work -- return 0 immediately without running the DP at all.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, not coded): try both signs for every
number recursively, count paths that sum to target. O(2^n) time -- correct
(this IS a valid solution for n<=20 per constraints) but doesn't exploit
that many sign-assignment PATHS reach the same "numbers used so far, running
sum" state.

Approach 1 (memoized top-down, on the ORIGINAL sign-assignment recursion) --
cache (index, running_sum) pairs directly, no subset-sum reframing needed.
O(n * range_of_sums) time and space -- functionally the same DP as the
reframed version, just derived without the algebra step.

Approach 2 (bottom-up tabulation, full 2D table, subset-sum reframing)
[checked] -- fill dp[i][s] row by row (row = how many numbers considered),
using the exclude/include recurrence. O(n * sum(P)) time and space.

Approach 3 (space-optimized, rolling 1D row, sums HIGH to LOW) [checked,
shipped] -- dp[i][s] only reads the row above (dp[i-1][s], exclude) and the
row above's SMALLER sum (dp[i-1][s-num], include). Sweeping sums HIGH to LOW
in place guarantees dp[s-num] hasn't been touched yet this pass -- it still
holds last row's (dp[i-1]) value when read, which is exactly the 0/1
(use-at-most-once) semantics. O(n * sum(P)) time, O(sum(P)) space.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [1, 1, 1, 1, 1], target = 3
total = 5, sum(P) = (3 + 5) / 2 = 4  (need subsets of nums summing to 4)

Full 2D table (rows = numbers considered 0..5, cols = subset sum 0..4):

              s=0 s=1 s=2 s=3 s=4
    (none) :   1   0   0   0   0
    +1     :   1   1   0   0   0
    +1     :   1   2   1   0   0
    +1     :   1   3   3   1   0
    +1     :   1   4   6   4   1
    +1     :   1   5  10  10   5

Answer: dp[5][4] = 5.  MATCHES expected (choosing exactly 4 of the 5 ones to
be '+' and 1 to be '-' -- C(5,4) = 5 ways -- confirms the subset-sum count
directly equals a binomial coefficient here since all values are 1).

Rolling-row version, same data, one array updated per number (HIGH to LOW):
    start:              dp = [1,0,0,0,0]
    after num=1 (#1):   dp = [1,1,0,0,0]   (dp[s]+=dp[s-1], s=4..1 desc)
    after num=1 (#2):   dp = [1,2,1,0,0]
    after num=1 (#3):   dp = [1,3,3,1,0]
    after num=1 (#4):   dp = [1,4,6,4,1]
    after num=1 (#5):   dp = [1,5,10,10,5]
    return dp[4] = 5.  MATCHES.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time              Space   Mutates input?
    ---------------------------------  ----------------  ------  --------------
    Brute force recursion (no memo)    O(2^n)            O(n)    no
    Memoized top-down (direct)         O(n*range)        O(n*range)  no
    Bottom-up tabulation, full table   O(n*sum(P))        O(n*sum(P))  no
    Rolling row [chosen]               O(n*sum(P))        O(sum(P))    no


================================================================================
EDGE CASES
================================================================================
    (target + total) is ODD -> no integer sum(P) exists, no partition can
                                work -- return 0 immediately (e.g. nums=[1],
                                target=2: total=1, (2+1)=3 is odd).
    abs(target) > total     -> even assigning every number the SAME favorable
                                sign can't reach target -- return 0 (e.g.
                                nums=[1], target=5).
    nums contains 0's       -> a 0 can go in EITHER subset without changing
                                the sum, so it DOUBLES the number of ways for
                                every valid partition of the nonzero numbers
                                -- correctly falls out of the DP automatically
                                since dp[s] and dp[s-0]=dp[s] both contribute.
    target == total (or == -total) -> exactly 1 way: all '+' (or all '-').


================================================================================
COMMON MISTAKES
================================================================================
1. Sweeping the rolling-array sums LOW to HIGH (007's unbounded-coin
   direction) instead of HIGH to LOW -- this is 0/1 knapsack, so going low
   to high would let a single number contribute to its own count twice
   within the same pass, effectively treating it as reusable. This is the
   #1 confusable mistake between 007 and 008 -- same loop skeleton, OPPOSITE
   required direction, because one is unbounded and one is 0/1.

2. Skipping the "is (target+total) odd, or |target|>total" guard and
   letting `sum(P)` be computed as a non-integer or negative array size --
   crashes or silently returns a nonsensical dp table instead of the
   correct answer of 0.

3. Forgetting nums can contain 0 -- a naive reading of "assign +/- to each
   number" might assume nonzero values; the DP handles zeros correctly
   automatically, but a hand-rolled combinatorial shortcut (e.g. assuming
   all nums are distinct/positive) would not.

4. Solving via brute-force 2^n recursion without memoization and assuming
   it's "fine because n<=20" -- 2^20 ~ 1M is survivable here, but the
   INTERVIEWER is testing whether you recognize the subset-sum reduction,
   not whether brute force technically passes small constraints.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why does this reduce to 0/1 knapsack and not unbounded (007's shape)?
A: Each number in nums is used EXACTLY ONCE (it gets exactly one sign) --
   there's no "reuse a value multiple times" concept here, unlike coins
   which have unlimited supply. That's precisely 0/1 knapsack's defining
   trait, and it's why the sweep direction flips versus 007.

Q: What if you needed to enumerate all sign assignments, not just count?
A: Fall back to backtracking (topic 09) -- the DP formulation only tracks
   counts, not which specific numbers went where; reconstructing all
   assignments from the DP table is possible but strictly more complex than
   just re-running the backtracking search with early pruning.

Q: How would negative numbers in nums change this?
A: They don't change the algebra (sum(P) formula still holds), but the
   subset-sum DP's sum axis would need to range over negative values too,
   shifting all indices by an offset -- constraints here guarantee
   0 <= nums[i], so this doesn't arise, but it's the natural follow-up.

Q: Relationship to Partition Equal Subset Sum (topic 16, 014)?
A: Structurally identical 0/1 knapsack DP -- that problem asks "does ANY
   subset sum to total/2" (existence, boolean), this one asks "HOW MANY
   subsets sum to (target+total)/2" (count, integer). Same recurrence
   shape, different combinator (OR vs +).


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 416  Partition Equal Subset Sum (topic 16 -- same 0/1 knapsack DP,
            existence instead of count)
    LC 518  Coin Change II (007 -- unbounded knapsack counting, OPPOSITE
            sweep direction)
    LC 39   Combination Sum (topic 09 -- backtracking enumeration, no DP,
            because it needs the actual combinations, not just a count)
    LC 474  Ones and Zeroes (0/1 knapsack with TWO capacity dimensions
            instead of one)
================================================================================
"""


class Solution:
    def findTargetSumWays(self, nums: list[int], target: int) -> int:
        """✅ Subset-sum reframing + 0/1 knapsack, rolling 1D row over sums
        swept HIGH to LOW. O(n * sum(P)) time, O(sum(P)) space."""
        total = sum(nums)
        if (target + total) % 2 != 0 or abs(target) > total:
            return 0
        target_sum = (target + total) // 2  # sum(P), guaranteed >= 0

        dp = [0] * (target_sum + 1)
        dp[0] = 1
        for num in nums:
            for s in range(target_sum, num - 1, -1):
                dp[s] += dp[s - num]
        return dp[target_sum]

    def findTargetSumWays_full_table(self, nums: list[int], target: int) -> int:
        """Alternative: full 2D tabulation, O(n * sum(P)) time and space --
        useful for tracing the exclude/include decomposition explicitly."""
        total = sum(nums)
        if (target + total) % 2 != 0 or abs(target) > total:
            return 0
        target_sum = (target + total) // 2

        n = len(nums)
        dp = [[0] * (target_sum + 1) for _ in range(n + 1)]
        for i in range(n + 1):
            dp[i][0] = 1
        for i in range(1, n + 1):
            num = nums[i - 1]
            for s in range(target_sum + 1):
                dp[i][s] = dp[i - 1][s]
                if s >= num:
                    dp[i][s] += dp[i - 1][s - num]
        return dp[n][target_sum]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([1, 1, 1, 1, 1], 3, 5),
        ([1], 1, 1),
        ([1], 2, 0),
        ([0, 0, 0, 0, 0, 0, 0, 0, 1], 1, 256),
        ([100], -100, 1),
        ([1, 0], 1, 2),
    ]

    print("--- correctness: rolling row vs full table agree ---")
    for nums, target, want in cases:
        got_roll = sol.findTargetSumWays(nums, target)
        got_full = sol.findTargetSumWays_full_table(nums, target)
        ok = got_roll == want and got_full == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums} target={target} "
              f"roll={got_roll} full={got_full}  (want {want})")

    # --------------------------------------------------------------------
    # RUNTIME DEMO: prove sweeping LOW-to-HIGH (007's unbounded direction)
    # on this 0/1 problem actually overcounts, live.
    # --------------------------------------------------------------------
    print("\n--- DEMO: HIGH-to-LOW (correct, 0/1) vs LOW-to-HIGH (buggy, unbounded) ---")

    def target_sum_buggy_low_to_high(nums, target):
        total = sum(nums)
        if (target + total) % 2 != 0 or abs(target) > total:
            return 0
        target_sum = (target + total) // 2
        dp = [0] * (target_sum + 1)
        dp[0] = 1
        for num in nums:
            for s in range(num, target_sum + 1):  # BUG: wrong direction
                dp[s] += dp[s - num]
        return dp[target_sum]

    nums, target = [1, 1, 1, 1, 1], 3
    correct = sol.findTargetSumWays(nums, target)
    buggy = target_sum_buggy_low_to_high(nums, target)
    print(f"  nums={nums}, target={target}")
    print(f"  correct (HIGH-to-LOW, 0/1 knapsack):    {correct}")
    print(f"  buggy   (LOW-to-HIGH, unbounded reuse):  {buggy}")
    print(f"  buggy diverges from correct: {buggy != correct}")
    all_ok &= (correct == 5)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
