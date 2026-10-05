package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 1137 · N-th Tribonacci Number                    [Easy]
https://leetcode.com/problems/n-th-tribonacci-number/
================================================================================

PROBLEM
-------
The Tribonacci sequence Tn is defined as follows:

    T0 = 0, T1 = 1, T2 = 1
    Tn+3 = Tn + Tn+1 + Tn+2 for n >= 0

Given n, return the value of Tn.


EXAMPLES
--------
Example 1:
    Input:  n = 4
    Output: 4
    Explanation: T3 = 0 + 1 + 1 = 2, T4 = 1 + 1 + 2 = 4

Example 2:
    Input:  n = 25
    Output: 1389537


CONSTRAINTS
-----------
    0 <= n <= 37
    The answer is guaranteed to fit within a 32-bit integer, ie. answer <= 2^31 - 1


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is the simplest possible 1D DP: a fixed-window linear recurrence,
exactly like Fibonacci but reaching back THREE cells instead of two.
`dp[i]` MEANS "the tribonacci value at index i". Base cases dp[0]=0,
dp[1]=1, dp[2]=1 are given directly by the problem; every dp[i] for i>=3
is dp[i-1]+dp[i-2]+dp[i-3].

PROGRESSIVE HINTS
------------------
Hint 1: Write the naive recursion straight from the recurrence -- it will
        be exponential, same shape as fib(n). Don't ship it, but understand
        why it's slow (draw the call tree for n=6, count repeated calls).
Hint 2: Cache each n the first time you compute it (memoization) -- collapses
        the exponential tree down to O(n) distinct computations.
Hint 3: Since dp[i] only ever needs the THREE cells right before it, you
        never need a whole array -- three rolling variables suffice.
Hint 4: Handle n=0 and n=1 as direct lookups before entering any loop.

COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1)
================================================================================
*/

func main() {
	fmt.Println("Solution for N-th Tribonacci Number not implemented yet")
}
