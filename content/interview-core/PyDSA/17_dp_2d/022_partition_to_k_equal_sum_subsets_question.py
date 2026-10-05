"""
================================================================================
LeetCode 698 · Partition to K Equal Sum Subsets                         [Medium]
https://leetcode.com/problems/partition-to-k-equal-sum-subsets/
Topic: 17 · Dynamic Programming (2D)
================================================================================

PROBLEM
-------
Given an integer array nums and an integer k, return true if it is possible to
divide this array into k non-empty subsets whose sums are all equal.


EXAMPLES
--------
Example 1:   nums = [4, 3, 2, 3, 5, 2, 1], k = 4   ->  true
    (5), (1, 4), (2, 3), (2, 3) each sum to 5.

Example 2:   nums = [1, 2, 3, 4], k = 3            ->  false


CONSTRAINTS
-----------
    1 <= k <= nums.length <= 16
    1 <= nums[i] <= 10^4
    The frequency of each element is in the range [1, 4].


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Every subset must sum to target = sum(nums) / k, so two quick checks come
first: the total must divide by k, and no number may exceed target.

n <= 16 is the signal. 2^16 = 65,536 subsets is small, so the STATE can be
"which numbers have been used" — a bitmask. That is BITMASK DP:

    dp[mask] = reachable?  and if so, how full the current bucket is

The key insight that makes it fast: fill buckets ONE AT A TIME. If the used
numbers in `mask` sum to S, then S // target buckets are complete and the
current bucket holds S % target — so the bucket state is determined by the
mask. Each mask needs to be solved only once.


WHAT TO THINK ABOUT
--------------------
1. Why does "put the largest number into the emptiest bucket" fail?
   Try nums = [2, 2, 3, 3, 4], k = 2.

2. For a set of used numbers, is the current bucket's fill ever ambiguous?

3. If you use backtracking instead, which symmetries make it re-do the same
   work (empty buckets, equal numbers)?


PROGRESSIVE HINTS
------------------
Hint 1: Return False early if sum % k != 0 or max(nums) > target.

Hint 2: dp[mask] = fill of the current bucket (-1 = unreachable). From a
        reachable mask, add any unused number i with dp[mask] + nums[i] <= target;
        the new fill is (dp[mask] + nums[i]) % target.

Hint 3: The answer is dp[full mask] == 0.


COMPLEXITY TARGET
------------------
    Time:  O(n * 2^n)
    Space: O(2^n)
================================================================================
"""
from typing import List


class Solution:
    def canPartitionKSubsets(self, nums: List[int], k: int) -> bool:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 022_partition_to_k_equal_sum_subsets_question.py
# ==============================================================================
def run_tests() -> None:
    cases = [
        ([4, 3, 2, 3, 5, 2, 1], 4, True),
        ([1, 2, 3, 4], 3, False),
        ([2, 2, 3, 3, 4], 2, True),
        ([5], 1, True),
        ([1, 1, 1, 1, 2, 2, 2, 2], 4, True),
        ([2, 2, 2, 2, 3, 4, 5], 4, False),
        ([10, 10, 10, 7, 7, 7, 7, 7, 7, 6, 6, 6], 3, True),
    ]
    all_ok = True
    for nums, k, want in cases:
        got = Solution().canPartitionKSubsets(list(nums), k)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums} k={k}  got={got}  want={want}")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
