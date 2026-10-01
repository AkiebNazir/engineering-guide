"""
================================================================================
QUESTION · LeetCode 986 · Interval List Intersections                 [Medium]
https://leetcode.com/problems/interval-list-intersections/
================================================================================

You are given two lists of closed intervals, `firstList` and `secondList`,
where `firstList[i] = [starti, endi]` and `secondList[j] = [startj, endj]`.
Each list of intervals is pairwise disjoint and in sorted order.

Return the intersection of these two interval lists.

A closed interval `[a, b]` (with `a <= b`) denotes the set of real numbers x
with `a <= x <= b`. The intersection of two closed intervals is a set of
real numbers that are either empty or represented as a closed interval. For
example, the intersection of `[1, 3]` and `[2, 4]` is `[2, 3]`.

Example 1:
    Input:  firstList = [[0,2],[5,10],[13,23],[24,25]]
            secondList = [[1,5],[8,12],[15,24],[25,26]]
    Output: [[1,2],[5,5],[8,10],[15,23],[24,24],[25,25]]

Example 2:
    Input:  firstList = [], secondList = [[1,5]]
    Output: []

Constraints:
    0 <= firstList.length, secondList.length <= 1000
    firstList.length + secondList.length >= 1
    0 <= starti < endi <= 10^9
    endi < starti+1 for all valid i
    0 <= startj < endj <= 10^9
    endj < startj+1 for all valid j
"""

from typing import List


class Solution:
    def intervalIntersection(
        self, firstList: List[List[int]], secondList: List[List[int]]
    ) -> List[List[int]]:
        # YOUR CODE HERE
        pass


def run_tests():
    sol = Solution()
    assert sol.intervalIntersection(
        [[0, 2], [5, 10], [13, 23], [24, 25]], [[1, 5], [8, 12], [15, 24], [25, 26]]
    ) == [[1, 2], [5, 5], [8, 10], [15, 23], [24, 24], [25, 25]]
    assert sol.intervalIntersection([], [[1, 5]]) == []
    assert sol.intervalIntersection([[1, 5]], []) == []
    assert sol.intervalIntersection([[1, 3]], [[2, 4]]) == [[2, 3]]
    assert sol.intervalIntersection([[1, 3]], [[4, 6]]) == []  # no overlap
    assert sol.intervalIntersection([[1, 5]], [[2, 3]]) == [[2, 3]]  # fully nested
    assert sol.intervalIntersection([[1, 3]], [[3, 5]]) == [[3, 3]]  # touching -> point
    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
