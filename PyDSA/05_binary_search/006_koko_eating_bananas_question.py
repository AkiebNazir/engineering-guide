"""
================================================================================
QUESTION · LeetCode 875 · Koko Eating Bananas                          [Medium]
https://leetcode.com/problems/koko-eating-bananas/
================================================================================
Koko loves to eat bananas. There are `n` piles of bananas, the i-th pile has
`piles[i]` bananas. The guards have gone and will come back in `h` hours.

Koko can decide her bananas-per-hour eating speed of `k`. Each hour, she
chooses some pile of bananas and eats `k` bananas from that pile. If the pile
has less than `k` bananas, she eats all of them instead, and will not eat any
more bananas during this hour.

Koko likes to eat slowly but still wants to finish eating all the bananas
before the guards return.

Return the minimum integer `k` such that she can eat all the bananas within
`h` hours.

Example 1:
    Input:  piles = [3,6,7,11], h = 8
    Output: 4

Example 2:
    Input:  piles = [30,11,23,4,20], h = 5
    Output: 30

Example 3:
    Input:  piles = [30,11,23,4,20], h = 6
    Output: 23

Constraints:
    1 <= piles.length <= 10^4
    piles.length <= h <= 10^9
    1 <= piles[i] <= 10^9
================================================================================
"""

from typing import List


class Solution:
    def minEatingSpeed(self, piles: List[int], h: int) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 006_koko_eating_bananas_question.py
# ==============================================================================
CASES = [
    ([3, 6, 7, 11], 8, 4),
    ([30, 11, 23, 4, 20], 5, 30),
    ([30, 11, 23, 4, 20], 6, 23),
    ([1], 1, 1),
    ([1000000000], 2, 500000000),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for piles, h, expected in CASES:
        got = sol.minEatingSpeed(piles, h)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  piles={piles!r:<24} h={h:<6} -> {got}  (want {expected})")
    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
