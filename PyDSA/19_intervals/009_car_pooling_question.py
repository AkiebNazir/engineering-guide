"""
================================================================================
QUESTION · LeetCode 1094 · Car Pooling                                [Medium]
https://leetcode.com/problems/car-pooling/
================================================================================

There is a car with `capacity` empty seats. The vehicle only drives east
(i.e., it cannot turn around and drive west).

You are given the integer `capacity` and an array `trips` where
`trips[i] = [numPassengersi, fromi, toi]` indicates that the ith trip has
`numPassengersi` passengers and the locations to pick them up and drop
them off are `fromi` and `toi` respectively. The locations are given as the
number of kilometers due east from the car's initial location.

Return true if it is possible to pick up and drop off all passengers for
all the given trips, or false otherwise.

Example 1:
    Input:  trips = [[2,1,5],[3,3,7]], capacity = 4
    Output: false

Example 2:
    Input:  trips = [[2,1,5],[3,3,7]], capacity = 5
    Output: true

Constraints:
    1 <= trips.length <= 1000
    trips[i].length == 3
    1 <= numPassengersi <= 100
    0 <= fromi < toi <= 1000
    1 <= capacity <= 10^5
"""

from typing import List


class Solution:
    def carPooling(self, trips: List[List[int]], capacity: int) -> bool:
        # YOUR CODE HERE
        pass


def run_tests():
    sol = Solution()
    assert sol.carPooling([[2, 1, 5], [3, 3, 7]], 4) is False
    assert sol.carPooling([[2, 1, 5], [3, 3, 7]], 5) is True
    assert sol.carPooling([[2, 1, 5], [3, 5, 7]], 3) is True  # touching -> no overlap
    assert sol.carPooling([[3, 2, 7], [3, 7, 9], [8, 3, 9]], 11) is True
    assert sol.carPooling([[10, 0, 1]], 9) is False
    assert sol.carPooling([[10, 0, 1]], 10) is True
    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
