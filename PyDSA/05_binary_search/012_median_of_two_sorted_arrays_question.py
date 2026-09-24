"""
================================================================================
QUESTION · LeetCode 4 · Median of Two Sorted Arrays                      [Hard]
https://leetcode.com/problems/median-of-two-sorted-arrays/
================================================================================
Given two sorted arrays `nums1` and `nums2` of size m and n respectively,
return THE MEDIAN of the two sorted arrays.

The overall run time complexity should be O(log (m+n)).

Example 1:
    Input:  nums1 = [1,3], nums2 = [2]
    Output: 2.00000
    Explanation: merged array = [1,2,3] and median is 2.

Example 2:
    Input:  nums1 = [1,2], nums2 = [3,4]
    Output: 2.50000
    Explanation: merged array = [1,2,3,4] and median is (2 + 3) / 2 = 2.5.

Constraints:
    nums1.length == m
    nums2.length == n
    0 <= m <= 1000
    0 <= n <= 1000
    1 <= m + n <= 2000
    -10^6 <= nums1[i], nums2[i] <= 10^6
================================================================================
"""

from typing import List


class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 012_median_of_two_sorted_arrays_question.py
# ==============================================================================
CASES = [
    ([1, 3], [2], 2.0),
    ([1, 2], [3, 4], 2.5),
    ([], [1], 1.0),
    ([2], [], 2.0),
    ([1, 2, 3], [], 2.0),
    ([1, 3], [2, 7], 2.5),
    ([0, 0], [0, 0], 0.0),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for nums1, nums2, expected in CASES:
        got = sol.findMedianSortedArrays(nums1, nums2)
        ok = got is not None and abs(got - expected) < 1e-5
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums1={nums1!r:<14} nums2={nums2!r:<14} -> {got}  (want {expected})")
    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
