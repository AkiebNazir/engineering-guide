package implement_rand10_using_rand7

/*
================================================================================
QUESTION · LeetCode 470 · Implement Rand10() Using Rand7()          [Medium]
https://leetcode.com/problems/implement-rand10-using-rand7/
================================================================================

PROBLEM
-------
Given the API `rand7()` that generates a uniform random integer in the range
`[1, 7]`, write a function `rand10()` that generates a uniform random integer
in the range `[1, 10]`. You can only call the API `rand7()`, and you
shouldn't call any other API. Please do not use a language's built-in
random API.

Each integer should have equal probability of returning.

Follow up:
- What is the expected value for the number of calls to `rand7()`?
- Could you minimize the number of calls to `rand7()`?

EXAMPLE
-------
Input: n = 1
Output: [2]
Explanation: Calling rand10() once returns a random integer between 1 and 10.
*/

import "math/rand"

func rand7() int {
	return rand.Intn(7) + 1
}

func rand10() int {
	return 0 // TODO: Implement
}
