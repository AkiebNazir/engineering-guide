package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 213 · House Robber II                            [Medium]
https://leetcode.com/problems/house-robber-ii/
================================================================================

PROBLEM
-------
You are a professional robber planning to rob houses along a street. Each
house has money stashed, all houses at this place are arranged in a
CIRCLE -- that means the first house is the neighbor of the last one.
Meanwhile, adjacent houses have a connected security system, and it will
automatically contact the police if two adjacent houses were broken into
on the same night.

Given an integer array nums representing the amount of money of each
house, return the maximum amount of money you can rob tonight WITHOUT
alerting the police.


EXAMPLES
--------
Example 1:
    Input:  nums = [2,3,2]
    Output: 3
    Explanation: robbing house 0 (2) and house 2 (2) is forbidden -- they
                 are adjacent because the street is circular. Best is
                 robbing house 1 alone: 3.

Example 2:
    Input:  nums = [1,2,3,1]
    Output: 4
    Explanation: rob house 0 (1) and house 2 (3): 1+3=4. House 3 and
                 house 0 are adjacent (circular) so can't also take house 3.

Example 3:
    Input:  nums = [1,2,3]
    Output: 3


CONSTRAINTS
-----------
    1 <= nums.length <= 100
    0 <= nums[i] <= 1000


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This LOOKS like it needs 2D state ("am I still allowed to rob the last
house because I didn't rob the first one?") but it decomposes into TWO
independent instances of plain House Robber (problem 005):

    - Any valid robbery plan either EXCLUDES house 0, or EXCLUDES house
      n-1 (it cannot include both, since they're adjacent in a circle --
      and if it excludes NEITHER trivially by robbing neither, that's
      covered as a subcase of both runs anyway).
    - So: run House Robber on nums[0 : n-1] (drop the last house) and on
      nums[1 : n] (drop the first house), and take the max of the two.

Special-case n == 1: there is only one house, and "first == last" would
otherwise make both slices empty.

PROGRESSIVE HINTS
------------------
Hint 1: The circular constraint only ever matters for the PAIR (house 0,
        house n-1) -- every other adjacency is identical to the linear
        problem.
Hint 2: Any valid selection either skips house 0 entirely, or skips house
        n-1 entirely (both is also fine, it's dominated by one of the two
        runs). Solve the linear problem on each slice, take the max.
Hint 3: Reuse your House Robber solution as a helper function on a
        sub-slice -- don't rewrite the DP from scratch.
Hint 4: n == 1 is a special case: there's no "circle" with one house.

COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1)
================================================================================
*/

func main() {
	fmt.Println("Solution for House Robber II not implemented yet")
}
