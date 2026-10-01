package main

import "fmt"

/*
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
*/

func main() {
	fmt.Println("Solution for Perfect Squares not implemented yet")
}
