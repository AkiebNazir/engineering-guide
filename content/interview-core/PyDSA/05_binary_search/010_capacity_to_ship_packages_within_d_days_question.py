"""
================================================================================
QUESTION · LeetCode 1011 · Capacity To Ship Packages Within D Days     [Medium]
https://leetcode.com/problems/capacity-to-ship-packages-within-d-days/
================================================================================
A conveyor belt has packages that must be shipped from one port to another
within `days` days.

The i-th package on the conveyor belt has a weight of `weights[i]`. Each day,
we load the ship with packages on the conveyor belt (in the order given by
`weights`). We may not load more weight than the maximum weight capacity of
the ship.

Return the least weight capacity of the ship that will result in all the
packages on the conveyor belt being shipped within `days` days.

Example 1:
    Input:  weights = [1,2,3,4,5,6,7,8,9,10], days = 5
    Output: 15
    Explanation: A ship capacity of 15 is the minimum to ship all the packages
    in 5 days like this:
        1st day: 1, 2, 3, 4, 5
        2nd day: 6, 7
        3rd day: 8
        4th day: 9
        5th day: 10

Example 2:
    Input:  weights = [3,2,2,4,1,4], days = 3
    Output: 6

Example 3:
    Input:  weights = [1,2,3,1,1], days = 4
    Output: 3

Constraints:
    1 <= days <= weights.length <= 5 * 10^4
    1 <= weights[i] <= 500
================================================================================
"""

from typing import List


class Solution:
    def shipWithinDays(self, weights: List[int], days: int) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 010_capacity_to_ship_packages_within_d_days_question.py
# ==============================================================================
CASES = [
    ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5, 15),
    ([3, 2, 2, 4, 1, 4], 3, 6),
    ([1, 2, 3, 1, 1], 4, 3),
    ([1], 1, 1),
    ([5, 5, 5, 5], 4, 5),
    ([5, 5, 5, 5], 2, 10),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for weights, days, expected in CASES:
        got = sol.shipWithinDays(weights, days)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  weights={weights!r:<28} days={days:<4} -> {got}  (want {expected})")
    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
