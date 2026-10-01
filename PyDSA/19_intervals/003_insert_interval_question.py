"""
================================================================================
QUESTION · LeetCode 57 · Insert Interval                              [Medium]
https://leetcode.com/problems/insert-interval/
================================================================================

You are given an array of non-overlapping intervals `intervals` where
`intervals[i] = [starti, endi]` represent the start and the end of the ith
interval, and `intervals` is sorted in ascending order by `starti`. You are
also given an interval `newInterval = [start, end]` that represents the
start and end of another interval.

Insert `newInterval` into `intervals` such that `intervals` is still sorted
in ascending order by `starti` and `intervals` still does not have any
overlapping intervals (merge overlapping intervals if necessary).

Return `intervals` after the insertion.

Example 1:
    Input:  intervals = [[1,3],[6,9]], newInterval = [2,5]
    Output: [[1,5],[6,9]]

Example 2:
    Input:  intervals = [[1,2],[3,5],[6,7],[8,10],[12,16]], newInterval = [4,8]
    Output: [[1,2],[3,10],[12,16]]
    Explanation: newInterval = [4,8] overlaps with [3,5],[6,7],[8,10].

Constraints:
    0 <= intervals.length <= 10^4
    intervals[i].length == 2
    0 <= starti <= endi <= 10^5
    intervals is sorted by starti in ascending order.
    newInterval.length == 2
    0 <= start <= end <= 10^5
"""

from typing import List


class Solution:
    def insert(
        self, intervals: List[List[int]], newInterval: List[int]
    ) -> List[List[int]]:
        # YOUR CODE HERE
        pass


def run_tests():
    sol = Solution()
    assert sol.insert([[1, 3], [6, 9]], [2, 5]) == [[1, 5], [6, 9]]
    assert sol.insert(
        [[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]
    ) == [[1, 2], [3, 10], [12, 16]]
    assert sol.insert([], [5, 7]) == [[5, 7]]
    assert sol.insert([[1, 5]], [2, 3]) == [[1, 5]]  # fully absorbed
    assert sol.insert([[1, 5]], [6, 8]) == [[1, 5], [6, 8]]  # no overlap, after
    assert sol.insert([[3, 5]], [1, 2]) == [[1, 2], [3, 5]]  # no overlap, before
    assert sol.insert([[1, 5]], [0, 10]) == [[0, 10]]  # new swallows all
    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
