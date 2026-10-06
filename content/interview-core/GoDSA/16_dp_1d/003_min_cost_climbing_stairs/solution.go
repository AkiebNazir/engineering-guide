package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 746 · Min Cost Climbing Stairs                   [Easy]
https://leetcode.com/problems/min-cost-climbing-stairs/
================================================================================

PROBLEM
-------
You are given an integer array cost where cost[i] is the cost of ith step
on a staircase. Once you pay the cost, you can either climb one or two
steps.

You can either start from the step with index 0, or the step with index 1.

Return the minimum cost to reach the top of the floor (one step PAST the
last index of cost).


EXAMPLES
--------
Example 1:
    Input:  cost = [10,15,20]
    Output: 15
    Explanation: start at index 1, pay 15, climb two steps to reach the top.

Example 2:
    Input:  cost = [1,100,1,1,1,100,1,1,100,1]
    Output: 6
    Explanation: start at index 0, pay 1, then take steps
                 0 -> 2 -> 4 -> 6 -> 7 -> 9 -> top, paying 1 each time
                 except the free final jump from 9 to top; total 6.


CONSTRAINTS
-----------
    2 <= cost.length <= 1000
    0 <= cost[i] <= 999


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
dp[i] MEANS "the minimum cost to REACH step i" (you have not yet paid to
LEAVE it). To reach step i you must have come from i-1 (pay cost[i-1]) or
i-2 (pay cost[i-2]) -- take whichever is cheaper:

    dp[i] = min(dp[i-1] + cost[i-1], dp[i-2] + cost[i-2])

The "top" is one past the last index, so the answer is dp[len(cost)].
Same fixed-window-of-2 shape as Climbing Stairs (problem 002), but MIN
instead of SUM, and reaching one step further past the array.

PROGRESSIVE HINTS
------------------
Hint 1: You can start free at index 0 OR index 1 -- so dp[0] = dp[1] = 0
        (reaching either starting step costs nothing until you leave it).
Hint 2: The "top" is index len(cost), one past the last real step.
Hint 3: dp[i] = min(dp[i-1] + cost[i-1], dp[i-2] + cost[i-2]) -- you pay
        for the step you're LEAVING, not the one you land on.
Hint 4: Same fixed window of 2 as climbing stairs -- roll it to O(1) space.

COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1)
================================================================================
*/

func main() {
	fmt.Println("Solution for Min Cost Climbing Stairs not implemented yet")
}
