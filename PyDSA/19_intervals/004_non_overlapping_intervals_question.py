"""
================================================================================
QUESTION · LeetCode 435 · Non-overlapping Intervals                   [Medium]
https://leetcode.com/problems/non-overlapping-intervals/
================================================================================

Given an array of intervals `intervals` where `intervals[i] = [starti, endi]`,
return the minimum number of intervals you need to remove to make the rest
of the intervals non-overlapping.

Example 1:
    Input:  intervals = [[1,2],[2,3],[3,4],[1,3]]
    Output: 1
    Explanation: [1,3] can be removed and the rest are non-overlapping.

Example 2:
    Input:  intervals = [[1,2],[1,2],[1,2]]
    Output: 2
    Explanation: remove two [1,2] to leave only one.

Example 3:
    Input:  intervals = [[1,2],[2,3]]
    Output: 0
    Explanation: touching intervals are already non-overlapping.

Constraints:
    1 <= intervals.length <= 10^5
    intervals[i].length == 2
    -5 * 10^4 <= starti < endi <= 5 * 10^4
"""

from typing import List


class Solution:
    def eraseOverlapIntervals(self, intervals: List[List[int]]) -> int:
        # YOUR CODE HERE
        pass


def run_tests():
    sol = Solution()
    assert sol.eraseOverlapIntervals([[1, 2], [2, 3], [3, 4], [1, 3]]) == 1
    assert sol.eraseOverlapIntervals([[1, 2], [1, 2], [1, 2]]) == 2
    assert sol.eraseOverlapIntervals([[1, 2], [2, 3]]) == 0
    assert sol.eraseOverlapIntervals([[1, 100], [11, 22], [1, 11], [2, 12]]) == 2
    assert sol.eraseOverlapIntervals([[1, 10], [2, 3], [4, 5]]) == 1
    assert sol.eraseOverlapIntervals([[1, 2]]) == 0
    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
