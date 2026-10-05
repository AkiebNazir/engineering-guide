"""
================================================================================
QUESTION · LeetCode 1046 · Last Stone Weight                            [Easy]
https://leetcode.com/problems/last-stone-weight/
================================================================================

You are given an array of integers `stones` where stones[i] is the weight of
the i-th stone.

We are playing a game with the stones. On each turn, we choose the two
HEAVIEST stones and smash them together. Suppose the two stones have weights
x and y with x <= y. The result of this smash is:

    - If x == y, both stones are totally destroyed.
    - If x != y, the stone of weight x is totally destroyed, and the stone of
      weight y has new weight y - x.

At the end of the game there is at most one stone left. Return the weight of
the last remaining stone, or 0 if there are no stones left.

Example 1:
    Input:  stones = [2,7,4,1,8,1]
    Output: 1
    Explanation:
        combine 7,8 -> 1, array becomes [2,4,1,1,1]
        combine 2,4 -> 2, array becomes [2,1,1,1]
        combine 2,1 -> 1, array becomes [1,1,1]
        combine 1,1 -> 0, array becomes [1]
        1 is the final weight.

Example 2:
    Input:  stones = [1]
    Output: 1

Constraints:
    1 <= stones.length <= 30
    1 <= stones[i] <= 1000
"""

from typing import List


class Solution:
    def lastStoneWeight(self, stones: List[int]) -> int:
        # YOUR CODE HERE
        pass


def run_tests():
    sol = Solution()
    assert sol.lastStoneWeight([2, 7, 4, 1, 8, 1]) == 1
    assert sol.lastStoneWeight([1]) == 1
    assert sol.lastStoneWeight([1, 1]) == 0
    assert sol.lastStoneWeight([2, 2]) == 0
    assert sol.lastStoneWeight([1, 3]) == 2
    assert sol.lastStoneWeight([10, 4, 2, 10]) == 2
    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
