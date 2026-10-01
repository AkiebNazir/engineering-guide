"""
================================================================================
QUESTION · LeetCode 56 · Merge Intervals                              [Medium]
https://leetcode.com/problems/merge-intervals/
================================================================================

Given an array of intervals where `intervals[i] = [starti, endi]`, merge all
overlapping intervals, and return an array of the non-overlapping intervals
that cover all the intervals in the input.

Example 1:
    Input:  intervals = [[1,3],[2,6],[8,10],[15,18]]
    Output: [[1,6],[8,10],[15,18]]
    Explanation: [1,3] and [2,6] overlap, merge into [1,6].

Example 2:
    Input:  intervals = [[1,4],[4,5]]
    Output: [[1,5]]
    Explanation: intervals [1,4] and [4,5] are considered overlapping (they
    touch at 4).

Constraints:
    1 <= intervals.length <= 10^4
    intervals[i].length == 2
    0 <= starti <= endi <= 10^4
"""

from typing import List


class Solution:
    def merge(self, intervals: List[List[int]]) -> List[List[int]]:
        # YOUR CODE HERE
        pass


def run_tests():
    sol = Solution()
    assert sol.merge([[1, 3], [2, 6], [8, 10], [15, 18]]) == [
        [1, 6],
        [8, 10],
        [15, 18],
    ]
    assert sol.merge([[1, 4], [4, 5]]) == [[1, 5]]
    assert sol.merge([[1, 4]]) == [[1, 4]]
    assert sol.merge([[1, 4], [2, 3]]) == [[1, 4]]  # fully nested
    assert sol.merge([[1, 4], [0, 4]]) == [[0, 4]]  # unsorted input
    assert sol.merge([[1, 4], [5, 6]]) == [[1, 4], [5, 6]]  # no overlap
    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
