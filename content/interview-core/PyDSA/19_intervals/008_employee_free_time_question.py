"""
================================================================================
QUESTION · LeetCode 759 · Employee Free Time                             [Hard]
https://leetcode.com/problems/employee-free-time/
================================================================================

We are given a list `schedule` of employees, which represents the working
time for each employee. Each employee has a list of non-overlapping
Intervals, and these intervals are in sorted order.

Return the list of finite intervals representing common, positive-length
free time for ALL employees, also in sorted order. (Even though we
require finite intervals, the inputs to this problem are guaranteed to
fit in 32-bit integers; and your answer should also be represented as
finite intervals.)

For this problem, `schedule` is given as a list of lists of `[start, end]`
pairs (one inner list per employee) rather than LeetCode's `Interval`
objects — this keeps the Python signature simple while preserving the
exact same logic.

Example 1:
    Input:  schedule = [[[1,2],[5,6]],[[1,3]],[[4,10]]]
    Output: [[3,4]]
    Explanation: flattened busy time is [1,2],[1,3],[4,10],[5,6]; merged
    busy union is [1,3],[4,10]; the only gap between merged blocks is
    [3,4].

Example 2:
    Input:  schedule = [[[1,3],[6,7]],[[2,4]],[[2,5],[9,12]]]
    Output: [[5,6],[7,9]]

Constraints:
    1 <= schedule.length, schedule[i].length <= 50
    0 <= schedule[i][j].start < schedule[i][j].end <= 10^8
"""

from typing import List


class Solution:
    def employeeFreeTime(self, schedule: List[List[List[int]]]) -> List[List[int]]:
        # YOUR CODE HERE
        pass


def run_tests():
    sol = Solution()
    assert sol.employeeFreeTime([[[1, 2], [5, 6]], [[1, 3]], [[4, 10]]]) == [[3, 4]]
    assert sol.employeeFreeTime(
        [[[1, 3], [6, 7]], [[2, 4]], [[2, 5], [9, 12]]]
    ) == [[5, 6], [7, 9]]
    assert sol.employeeFreeTime([[[1, 5]], [[2, 3]]]) == []  # fully covered
    assert sol.employeeFreeTime([[[1, 2]]]) == []  # single employee, no gap possible
    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
