"""
================================================================================
QUESTION · LeetCode 279 · Perfect Squares                             [Medium]
https://leetcode.com/problems/perfect-squares/
================================================================================

PROBLEM
-------
Given an integer n, return the LEAST number of perfect square numbers
(1, 4, 9, 16, ...) that sum to n.


EXAMPLES
--------
Example 1:
    Input:  n = 12
    Output: 3
    Explanation: 12 = 4 + 4 + 4.

Example 2:
    Input:  n = 13
    Output: 2
    Explanation: 13 = 4 + 9.


CONSTRAINTS
-----------
    1 <= n <= 10^4


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is Coin Change (problem 010) wearing a different costume: dp[i]
MEANS "the minimum count of perfect squares summing to EXACTLY i", and the
"coins" are the perfect squares <= n (1, 4, 9, 16, ...) -- unlimited
reuse, value-indexed 1D DP:

    dp[0] = 0
    dp[i] = 1 + min(dp[i - k*k] for k*k <= i)

PROGRESSIVE HINTS
------------------
Hint 1: dp[0] = 0 (zero squares needed to make 0).
Hint 2: For each target i, try EVERY perfect square k*k <= i as the LAST
        square used: candidate = 1 + dp[i - k*k].
Hint 3: This is exactly Coin Change (010) with the coin set replaced by
        {1, 4, 9, 16, ...} -- same recurrence, same iteration direction
        (low to high, since squares are reusable).
Hint 4: Precompute the list of perfect squares up to n once, rather than
        recomputing k*k inside the inner loop every time.

COMPLEXITY TARGET
------------------
    Time:  O(n * sqrt(n))
    Space: O(n)
================================================================================
"""


class Solution:
    def numSquares(self, n: int) -> int:
        # YOUR CODE HERE
        pass


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        (12, 3),
        (13, 2),
        (1, 1),
        (2, 2),
        (4, 1),
        (7, 4),   # 4+1+1+1
        (100, 1),  # 10^2
    ]
    for n, want in cases:
        got = sol.numSquares(n)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n:3d}  -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
