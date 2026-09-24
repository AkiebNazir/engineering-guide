"""
================================================================================
QUESTION · LeetCode 252 · Meeting Rooms                                 [Easy]
https://leetcode.com/problems/meeting-rooms/
================================================================================

Given an array of meeting time intervals `intervals` where
`intervals[i] = [starti, endi]`, determine if a person could attend all
meetings.

Example 1:
    Input:  intervals = [[0,30],[5,10],[15,20]]
    Output: false
    Explanation: [0,30] overlaps both [5,10] and [15,20].

Example 2:
    Input:  intervals = [[7,10],[2,4]]
    Output: true

Constraints:
    0 <= intervals.length <= 10^4
    intervals[i].length == 2
    0 <= starti < endi <= 10^6
"""

from typing import List


class Solution:
    def canAttendMeetings(self, intervals: List[List[int]]) -> bool:
        # YOUR CODE HERE
        pass


def run_tests():
    sol = Solution()
    assert sol.canAttendMeetings([[0, 30], [5, 10], [15, 20]]) is False
    assert sol.canAttendMeetings([[7, 10], [2, 4]]) is True
    assert sol.canAttendMeetings([]) is True
    assert sol.canAttendMeetings([[5, 8]]) is True
    # touching endpoints: NOT a conflict for this problem
    assert sol.canAttendMeetings([[1, 2], [2, 3]]) is True
    # true overlap
    assert sol.canAttendMeetings([[1, 5], [4, 8]]) is False
    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
