package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 377 · Combination Sum IV                          [Medium]
https://leetcode.com/problems/combination-sum-iv/
================================================================================

PROBLEM
-------
Given an array of DISTINCT integers nums and a target integer target,
return the number of possible combinations that add up to target.

The answer is guaranteed to fit in a 32-bit integer.

IMPORTANT: order matters here despite the name "combination" -- (1,1,2)
and (1,2,1) and (2,1,1) are counted as three DIFFERENT combinations.


EXAMPLES
--------
Example 1:
    Input:  nums = [1,2,3], target = 4
    Output: 7
    Explanation: the possible combinations are (1,1,1,1), (1,1,2), (1,2,1),
                 (1,3), (2,1,1), (2,2), (3,1).

Example 2:
    Input:  nums = [9], target = 3
    Output: 0


CONSTRAINTS
-----------
    1 <= nums.length <= 200
    1 <= nums[i] <= 1000
    All the elements of nums are UNIQUE.
    1 <= target <= 1000

FOLLOW-UP: What if negative numbers are allowed in the given array? How
does it change the problem? What limitation do we need to add to
consider negative numbers?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
dp[t] MEANS "the number of ORDERED combinations (i.e. sequences) that sum
to exactly t". Numbers are reusable (unbounded, like Coin Change), and
because order matters, the correct loop structure puts the TARGET in the
OUTER loop and the numbers in the INNER loop -- the opposite of Coin
Change II's "count unordered combinations" (where numbers go outer,
target inner, to avoid counting permutations of the same multiset):

    dp[0] = 1
    for t in range(1, target + 1):
        for num in nums:
            if num <= t:
                dp[t] += dp[t - num]

This is Trap A from `_TOPIC_GUIDE.md` in a DIFFERENT costume: not "which
direction to scan the sum axis" (that's 014's trap, 0/1 vs unbounded) but
"which axis goes on the OUTSIDE" (that's THIS problem's trap: permutations
vs combinations).

PROGRESSIVE HINTS
------------------
Hint 1: dp[0] = 1 -- there's exactly one way to make target 0 (use no
        numbers at all).
Hint 2: For each target value t, the LAST number placed could be ANY
        num in nums (as long as num <= t) -- so dp[t] sums dp[t-num] over
        every valid choice of "last number used."
Hint 3: Because the SAME multiset in different orders counts separately,
        put the TARGET in the outer loop and NUMS in the inner loop --
        this lets the "last number" vary freely at every position,
        generating every ORDERING, not just every combination.
Hint 4: Contrast directly with Coin Change (010): same unbounded-reuse
        DP shape, target-outer here vs the (order doesn't matter for
        min-coins) any-order-works there.

COMPLEXITY TARGET
------------------
    Time:  O(target * len(nums))
    Space: O(target)
================================================================================
*/

func main() {
	fmt.Println("Solution for Combination Sum IV not implemented yet")
}
