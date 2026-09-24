"""
================================================================================
QUESTION · LeetCode 253 · Meeting Rooms II                            [Medium]
https://leetcode.com/problems/meeting-rooms-ii/
================================================================================

Given an array of meeting time intervals `intervals` where
`intervals[i] = [starti, endi]`, return the minimum number of conference
rooms required.

Example 1:
    Input:  intervals = [[0,30],[5,10],[15,20]]
    Output: 2

Example 2:
    Input:  intervals = [[7,10],[2,4]]
    Output: 1

Constraints:
    1 <= intervals.length <= 10^4
    0 <= starti < endi <= 10^6
"""

from typing import List


class Solution:
    def minMeetingRooms(self, intervals: List[List[int]]) -> int:
        # YOUR CODE HERE
        pass


def run_tests():
    sol = Solution()
    assert sol.minMeetingRooms([[0, 30], [5, 10], [15, 20]]) == 2
    assert sol.minMeetingRooms([[7, 10], [2, 4]]) == 1
    assert sol.minMeetingRooms([[1, 2], [2, 3]]) == 1  # touching -> 1 room
    assert sol.minMeetingRooms([[1, 10], [2, 6], [3, 8], [4, 7]]) == 4
    assert sol.minMeetingRooms([[5, 8]]) == 1
    assert sol.minMeetingRooms([]) == 0
    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
