package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 70 · Climbing Stairs                             [Easy]
https://leetcode.com/problems/climbing-stairs/
================================================================================

PROBLEM
-------
You are climbing a staircase. It takes n steps to reach the top.

Each time you can either climb 1 or 2 steps. In how many distinct ways can
you climb to the top?


EXAMPLES
--------
Example 1:
    Input:  n = 2
    Output: 2
    Explanation: 1+1, 2

Example 2:
    Input:  n = 3
    Output: 3
    Explanation: 1+1+1, 1+2, 2+1


CONSTRAINTS
-----------
    1 <= n <= 45


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The last move to reach step n was either a single step from n-1, or a
double step from n-2. Those two sets of paths never overlap (they're
distinguished by their last move), so ways(n) = ways(n-1) + ways(n-2) --
literally the Fibonacci recurrence wearing a staircase costume. This is
the canonical worked example in `_TOPIC_GUIDE.md` Part 0 -- read that first
if the four-stage progression (naive -> memo -> tabulation -> rolling
variables) isn't automatic yet.

PROGRESSIVE HINTS
------------------
Hint 1: ways(1) = 1, ways(2) = 2. What is the last step taken to reach n?
Hint 2: Two candidates for the last step (1-step from n-1, 2-step from
        n-2) that never overlap -- so ADD their counts, don't choose one.
Hint 3: dp[i] only needs dp[i-1] and dp[i-2] -- fixed window of 2, so you
        can roll it down to two variables after tabulating once.

COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1)
================================================================================
*/

func main() {
	fmt.Println("Solution for Climbing Stairs not implemented yet")
}
