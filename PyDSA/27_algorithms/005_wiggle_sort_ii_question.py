"""
================================================================================
QUESTION · LeetCode 324 · Wiggle Sort II                            [Medium]
https://leetcode.com/problems/wiggle-sort-ii/
================================================================================

PROBLEM
-------
Given an integer array `nums`, reorder it such that
    nums[0] < nums[1] > nums[2] < nums[3] ...

You may assume the input array always has a valid answer.


EXAMPLES
--------
Example 1:
    Input:  nums = [1, 5, 1, 1, 6, 4]
    Output: [1, 6, 1, 5, 1, 4]
    Explanation: [1, 4, 1, 5, 1, 6] is also accepted.

Example 2:
    Input:  nums = [1, 3, 2, 2, 3, 1]
    Output: [2, 3, 1, 3, 1, 2]


CONSTRAINTS
-----------
    1 <= nums.length <= 5 * 10^4
    0 <= nums[i] <= 5000
    It is guaranteed that there will be an answer for the given input nums.

FOLLOW-UP: Can you do it in O(n) time and/or in-place with O(1) extra space?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The "obvious" approach -- sort nums, then interleave the two halves -- works
and is O(n log n). The interviewer wants to see whether you reach for the
right tool: since the only thing you actually need from a full sort is the
MEDIAN (to split the array into "small half" and "large half" before
interleaving them), Quickselect finds it in O(n) EXPECTED time without
fully ordering anything. Then a single O(n) three-way, virtual-index
partition pass reorders the array around that median so the wiggle
property holds -- no second array needed.

PROGRESSIVE HINTS
------------------
Hint 1: If you sort nums and split into "smaller half" + "larger half",
        interleaving small[k-1-i] then large[k-1-i] for descending order
        within each half (to avoid adjacent duplicates landing next to
        each other) gives a valid wiggle. That's the O(n log n) baseline
        -- state it, but the target is better.
Hint 2: You only need the MEDIAN to define "smaller half" vs "larger
        half" -- Quickselect finds the k-th order statistic in O(n)
        expected time without sorting everything.
Hint 3: After finding the median, a three-way partition (values > median,
        == median, < median) run over VIRTUAL indices (an index-mapping
        trick that places larger values at even positions and smaller
        values at odd positions, working from the ends inward) reorders
        the array in a single O(n) pass with O(1) extra space.
Hint 4: The virtual index mapping for n elements is typically
        `(1 + 2*i) % (n | 1)` -- it deliberately scatters values so equal
        elements don't end up adjacent, which a naive middle-out split
        can get wrong when there are many duplicates.

COMPLEXITY TARGET
------------------
    Time:  O(n) expected (Quickselect + one partition pass)
    Space: O(1) extra (in-place)
================================================================================
"""

import random


class Solution:
    def wiggleSort(self, nums: list[int]) -> None:
        """
        Do not return anything, modify nums in-place instead.
        """
        # YOUR CODE HERE
        pass


def _is_valid_wiggle(nums: list[int]) -> bool:
    for i in range(len(nums) - 1):
        if i % 2 == 0:
            if not (nums[i] < nums[i + 1]):
                return False
        else:
            if not (nums[i] > nums[i + 1]):
                return False
    return True


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        [1, 5, 1, 1, 6, 4],
        [1, 3, 2, 2, 3, 1],
        [4, 5, 5, 6],
        [1],
        [1, 2],
        [2, 1],
    ]
    for nums in cases:
        original = list(nums)
        arr = list(nums)
        sol.wiggleSort(arr)
        ok = sorted(arr) == sorted(original) and (len(arr) == 1 or _is_valid_wiggle(arr))
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  wiggleSort({original}) -> {arr}")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
