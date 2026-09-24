package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 134 · Gas Station                                  [Medium]
https://leetcode.com/problems/gas-station/
================================================================================

There are n gas stations along a circular route, where the amount of gas at
the ith station is `gas[i]`. You have a car with an unlimited gas tank and
it costs `cost[i]` of gas to travel from the ith station to its next (i+1)th
station. You begin the journey with an empty tank at one of the gas
stations.

Given two integer arrays `gas` and `cost`, return the starting gas station's
index if you can travel around the circuit once in the clockwise direction,
otherwise return -1. If there exists a solution, it is guaranteed to be
unique.

--------------------------------------------------------------------------------
EXAMPLES
--------------------------------------------------------------------------------
Input: gas = [1,2,3,4,5], cost = [3,4,5,1,2]
Output: 3
Explanation: Start at station 3 (index 3) and fill up with 4 gas. Your tank
= 0 + 4 = 4. Travel to station 4 (cost 1), tank = 4 - 1 + 5 = 8. Travel to
station 0 (cost 2), tank = 8 - 2 + 1 = 7. Travel to station 1 (cost 3), tank
= 7 - 3 + 2 = 6. Travel to station 2 (cost 4), tank = 6 - 4 + 3 = 5. You
arrived back at station 3 with 5 extra gas, having used only as much as you
had. So starting at 3 works.

Input: gas = [2,3,4], cost = [3,4,3]
Output: -1
Explanation: You can't start at station 0, 1, or 2 and travel around the
circuit once before running out of gas.

--------------------------------------------------------------------------------
CONSTRAINTS
--------------------------------------------------------------------------------
- n == gas.length == cost.length
- 1 <= n <= 10^5
- 0 <= gas[i], cost[i] <= 10^4
*/

func main() {
	fmt.Println("Solution for Gas Station not implemented yet")
}
