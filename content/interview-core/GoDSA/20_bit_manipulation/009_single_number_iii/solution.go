package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 260 · Single Number III                          [Medium]
https://leetcode.com/problems/single-number-iii/
================================================================================

PROBLEM
-------
Given an integer array `nums` in which exactly two elements appear only
once and all the other elements appear exactly twice, find the two
elements that appear only once. You can return the answer in any order.

You must write an algorithm that runs in linear runtime complexity and
uses only constant extra space.


EXAMPLES
--------
Example 1:
    Input:  nums = [1,2,1,3,2,5]
    Output: [3,5]
    (3 and 5 are the only single elements, order doesn't matter)

Example 2:
    Input:  nums = [-1,0]
    Output: [-1,0]

Example 3:
    Input:  nums = [0,1]
    Output: [1,0]


CONSTRAINTS
-----------
    2 <= nums.length <= 3 * 10^4
    -2^31 <= nums[i] <= 2^31 - 1
    Each integer in nums will appear twice, except for two integers which
    will appear once.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
XOR-folding the WHOLE array (001's trick) cancels every pair and leaves
`a ^ b`, where a and b are the two singletons -- not either one
individually. The key second step: `a ^ b` is nonzero (a != b, since
they're distinct elements), so it has AT LEAST ONE set bit. Pick any set
bit of `a ^ b` (conventionally the LOWEST, via `diff & -diff`, the
isolate-lowest-set-bit identity from the topic guide) -- a and b MUST
differ at that bit position (that's exactly why it's set in the XOR), so
partitioning every number in nums by "is this bit set or not" puts a and
b into DIFFERENT groups, and every PAIRED value into the SAME group as
its twin (since a pair's two copies are identical and can't be split by
any bit test). XOR-folding each group in isolation now recovers a and b
separately, using 001's trick twice on the two partitions.

PROGRESSIVE HINTS
------------------
Hint 1: XOR-fold everything first. What do you get, and why isn't it
        the final answer?
Hint 2: `diff = a ^ b` must have at least one set bit, since a != b.
        `diff & -diff` isolates its lowest set bit.
Hint 3: Split nums into two groups by that one bit; XOR-fold each group
        independently to recover a and b.

COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1)
================================================================================
*/

func main() {
	fmt.Println("Solution for Single Number III not implemented yet")
}
