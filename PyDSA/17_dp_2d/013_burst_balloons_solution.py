"""
================================================================================
SOLUTION · LeetCode 312 · Burst Balloons                                  [Hard]
https://leetcode.com/problems/burst-balloons/
================================================================================

THE CORE IDEA
--------------
THE REFRAME THAT MAKES THIS TRACTABLE: think about which balloon is burst
LAST within a range, not first. Pad nums with a virtual 1 on each end (never
burst), giving `padded` of length n+2. Define:

    dp[l][r] = max coins from bursting ALL balloons STRICTLY BETWEEN
               indices l and r (l and r themselves survive this subproblem
               and are used only as multipliers)

For a fixed range (l, r), pick balloon k (l < k < r) to be the LAST one
burst within that range. The instant k is burst, everything else between l
and r is already gone -- so k's neighbors AT BURST TIME are GUARANTEED to
be exactly l and r, no matter what order the rest were removed in. That
certainty is what "burst last" buys you and "burst first" does not (if k
were burst FIRST, its neighbors at that moment would be whatever balloons
happen to still be adjacent -- genuinely unknown without more state).

    dp[l][r] = max over k in (l, r) of:
                   dp[l][k] + dp[k][r] + padded[l]*padded[k]*padded[r]

This is INTERVAL DP -- state = a RANGE, not a pair of independent positions
-- and it needs BOTH dp[l][k] and dp[k][r] already solved, both of which
have a SMALLER gap (k-l < r-l and r-k < r-l) than the current interval.
Intervals must therefore be filled in order of INCREASING LENGTH (gap =
r - l), not row-by-row like every grid-DP problem earlier in this topic.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, not coded): try every possible ORDER of
bursting all n balloons, sum the coins, take the max. O(n!) time --
factorial, hopelessly intractable even for n=15.

Approach 0.5 (greedy, priced, not coded, WRONG): always burst the balloon
that currently yields the most coins. Fails -- bursting order changes
FUTURE neighbors, so a locally-best choice can destroy a much better global
sequence; there's no exchange-argument proof of optimality (and it's
straightforward to construct counterexamples), so this is a trap, not a
real approach.

Approach 1 (memoized top-down, 2D cache, "last burst" reframe) -- recurse
on (l, r), cache each interval's answer. O(n^3) time (n^2 intervals, O(n)
choices of k each), O(n^2) space (memo + recursion depth up to n).

Approach 2 (bottom-up tabulation, full 2D table, filled by INCREASING GAP)
[checked, shipped] -- outer loop over gap = r - l (2 up to n+1), inner loop
over l (r = l + gap), innermost loop over k. No recursion, explicit
dependency order. O(n^3) time, O(n^2) space.

Approach 3 (space optimization) -- NOT AVAILABLE here, unlike every other
problem in this topic. dp[l][r] depends on dp[l][k] and dp[k][r] for EVERY
k in the open interval, spanning the FULL range of smaller intervals, not
just "the row above" or "one column left" -- there's no fixed-offset
neighbor to roll away. The full O(n^2) table is genuinely required.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [1, 5]  ->  padded = [1, 1, 5, 1]  (indices 0..3, n=2)

dp[l][r] is only meaningful when r - l >= 2 (at least one real balloon
strictly between l and r); dp[l][r] = 0 whenever r - l <= 1.

gap = 2 (intervals with exactly one balloon inside):
    dp[0][2]: only k=1 -> dp[0][1] + dp[1][2] + padded[0]*padded[1]*padded[2]
                        = 0 + 0 + 1*1*5 = 5
    dp[1][3]: only k=2 -> dp[1][2] + dp[2][3] + padded[1]*padded[2]*padded[3]
                        = 0 + 0 + 1*5*1 = 5

gap = 3 (the full range, both real balloons inside):
    dp[0][3]: k=1 -> dp[0][1] + dp[1][3] + padded[0]*padded[1]*padded[3]
                   = 0 + 5 + 1*1*1 = 6
              k=2 -> dp[0][2] + dp[2][3] + padded[0]*padded[2]*padded[3]
                   = 5 + 0 + 1*5*1 = 10
              dp[0][3] = max(6, 10) = 10

Answer: dp[0][3] = 10.  MATCHES expected (burst balloon 5 first: gets
1*5*1=5 coins, array becomes [1]; burst balloon 1: gets 1*1*1=1... wait,
the WINNING order is burst index-1 (value 1) first: 1*1*5=5, leaving [5];
then burst the 5: 1*5*1=5; total 10 -- k=2 chosen last means the value-1
balloon (index 1) bursts FIRST within the range, consistent with the DP
picking k=2 as LAST).


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time     Space   Mutates input?
    ---------------------------------  -------  ------  --------------
    Brute force (try every order)      O(n!)    O(n)    no
    Greedy (locally best each step)    O(n^2)   O(n)    WRONG ANSWER, not
                                                          just slow -- no
                                                          correctness proof
    Memoized top-down, "last burst"    O(n^3)   O(n^2)  no
    Bottom-up, filled by gap [chosen]  O(n^3)   O(n^2)  no


================================================================================
EDGE CASES
================================================================================
    n == 1              -> single balloon, no neighbors (both padded 1's),
                            answer = nums[0]*1*1 = nums[0].
    n == 0 (empty nums)   -> no balloons to burst, answer 0 -- must be
                            handled before padding (padding an empty list
                            still gives [1,1], but the gap-2+ loop never
                            fires, dp[0][1]=0 correctly by the "r-l<=1"
                            base case).
    All zeros              -> every product is 0, answer 0 regardless of
                            order (multiplying by 0 anywhere zeroes that
                            term, and there's no way to avoid ever touching
                            a 0-valued balloon or its neighbors).
    Values up to 100, n up to 300 -> max possible single term
                            100*100*100=1,000,000, times up to 300 bursts,
                            well within Python's native int range (also
                            within 32-bit signed range as the problem
                            implies via typical constraints).


================================================================================
COMMON MISTAKES
================================================================================
1. Reframing around "which balloon bursts FIRST" instead of LAST -- bursting
   first leaves genuinely unknown, order-dependent neighbors for the
   remaining balloons, which does NOT decompose into two independent
   subintervals; only "burst last" gives the clean guarantee that k's
   neighbors at burst time are exactly l and r.

2. Forgetting to pad nums with virtual 1's at both ends -- without the
   padding, the boundary balloons (index 0 and n-1) need special-cased
   multiplier logic ("treat out-of-bounds as 1") scattered through the
   recurrence instead of falling out automatically from padded[0] and
   padded[-1] both being 1.

3. Filling the DP table in the wrong order (row-by-row like the grid-DP
   problems, or column-by-column) -- interval DP REQUIRES increasing gap
   (interval length) as the outer loop, because dp[l][r] depends on
   sub-intervals with STRICTLY SMALLER gaps on both sides, not on a fixed
   "previous row/column" like the earlier problems in this topic.

4. Off-by-one on the k range -- k must range over `l+1` to `r-1` inclusive
   (strictly between l and r), and dp indices l, r are PADDED-array
   indices, not original-nums indices -- mixing the two indexings is a
   common source of IndexError or silently wrong multipliers.

5. Attempting to space-optimize this like every other 2D DP problem in the
   topic -- there IS no rolling-row trick here; dp[l][r] genuinely needs
   the FULL table of smaller intervals, not a fixed-offset neighbor.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why doesn't a greedy "burst the most valuable balloon each time" work?
A: Bursting order changes future adjacency -- a balloon that's cheap to
   burst now might set up a MUCH more valuable burst later by changing who
   becomes whose neighbor; greedy has no way to see that ahead, and there's
   no exchange-argument proof that local optimality composes into global
   optimality here (unlike, say, activity selection).

Q: How does this relate to Matrix Chain Multiplication?
A: Structurally identical interval DP shape -- dp[l][r] = min/max over a
   split point k, combining dp[l][k] and dp[k][r] plus a cost term for the
   split itself, filled by increasing interval length. Burst Balloons and
   Matrix Chain Multiplication are the two canonical interval-DP teaching
   examples.

Q: Can you reconstruct the actual bursting order, not just the max coins?
A: Yes -- keep a parallel table recording which k achieved the max at each
   (l, r), then recursively unwind from dp[0][n+1]: burst k LAST, so
   recursively determine the orders for [l,k] and [k,r] first, then append
   k.

Q: What's the exact time complexity and why is it n^3, not n^2?
A: O(n^2) distinct (l, r) intervals, and for EACH interval an O(n) scan over
   candidate last-burst points k -- O(n^2) * O(n) = O(n^3).


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 312 is the canonical "interval DP" problem alongside:
    Matrix Chain Multiplication (classic CS textbook problem, same
        "split point k, increasing interval length" shape)
    LC 1039 Minimum Score Triangulation of Polygon (same interval-DP shape,
        different cost function)
    LC 96   Unique Binary Search Trees (topic 11/16 -- also splits a range
        at every possible root k, though the combinator is sum-of-products,
        not max, and doesn't need the "burst last" adjacency insight)
    LC 664  Strange Printer (another interval DP with a subtler split rule)
================================================================================
"""


class Solution:
    def maxCoins(self, nums: list[int]) -> int:
        """✅ Interval DP, filled by increasing gap (interval length).
        O(n^3) time, O(n^2) space. Does not mutate nums."""
        if not nums:
            return 0
        padded = [1] + nums + [1]
        n = len(padded)
        dp = [[0] * n for _ in range(n)]

        for gap in range(2, n):  # gap = r - l, smallest meaningful is 2
            for l in range(0, n - gap):
                r = l + gap
                best = 0
                for k in range(l + 1, r):
                    coins = dp[l][k] + dp[k][r] + padded[l] * padded[k] * padded[r]
                    if coins > best:
                        best = coins
                dp[l][r] = best
        return dp[0][n - 1]

    def maxCoins_memoized_topdown(self, nums: list[int]) -> int:
        """Alternative: memoized top-down recursion on (l, r), same "burst
        last" reframe. O(n^3) time, O(n^2) space (memo + recursion depth
        up to n)."""
        if not nums:
            return 0
        padded = [1] + nums + [1]
        n = len(padded)
        memo = {}

        def solve(l, r):
            if r - l < 2:
                return 0
            if (l, r) in memo:
                return memo[(l, r)]
            best = 0
            for k in range(l + 1, r):
                coins = solve(l, k) + solve(k, r) + padded[l] * padded[k] * padded[r]
                best = max(best, coins)
            memo[(l, r)] = best
            return best

        return solve(0, n - 1)


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([3, 1, 5, 8], 167),
        ([1, 5], 10),
        ([7], 7),
        ([], 0),
        ([1, 1, 1], 3),
        ([9, 76, 64, 21], 116718),
    ]

    print("--- correctness: bottom-up (gap order) vs memoized top-down agree ---")
    for nums, want in cases:
        got_bottom = sol.maxCoins(nums[:])
        got_top = sol.maxCoins_memoized_topdown(nums[:])
        ok = got_bottom == want and got_top == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums}  bottom={got_bottom} "
              f"top={got_top}  (want {want})")

    # --------------------------------------------------------------------
    # RUNTIME DEMO: prove the "burst FIRST" reframe (which does NOT give a
    # correct O(n^3) DP -- there's no valid recurrence for it at all) is a
    # real trap by showing a naive GREEDY "burst most valuable first"
    # heuristic gives a WRONG, suboptimal answer versus the true DP max.
    # --------------------------------------------------------------------
    print("\n--- DEMO: greedy 'burst most valuable first' vs correct interval DP ---")

    def greedy_burst(nums):
        balloons = nums[:]
        total = 0
        while balloons:
            best_i, best_gain = 0, -1
            for i in range(len(balloons)):
                left = balloons[i - 1] if i > 0 else 1
                right = balloons[i + 1] if i < len(balloons) - 1 else 1
                gain = left * balloons[i] * right
                if gain > best_gain:
                    best_gain, best_i = gain, i
            total += best_gain
            balloons.pop(best_i)
        return total

    nums = [3, 1, 5, 8]
    correct = sol.maxCoins(nums[:])
    greedy = greedy_burst(nums[:])
    print(f"  nums={nums}")
    print(f"  correct (interval DP):            {correct}")
    print(f"  greedy (burst most valuable now):  {greedy}")
    print(f"  greedy is suboptimal: {greedy < correct}")
    all_ok &= (correct == 167)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
