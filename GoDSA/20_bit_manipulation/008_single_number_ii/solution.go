package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 137 · Single Number II                           [Medium]
https://leetcode.com/problems/single-number-ii/
================================================================================

PROBLEM
-------
Given an integer array `nums` where every element appears THREE times
except for one, which appears exactly once. Find the single element and
return it.

You must implement a solution with linear runtime complexity and use only
constant extra space.


EXAMPLES
--------
Example 1:
    Input:  nums = [2,2,3,2]
    Output: 3

Example 2:
    Input:  nums = [0,1,0,1,0,1,99]
    Output: 99


CONSTRAINTS
-----------
    1 <= nums.length <= 3 * 10^4
    -2^31 <= nums[i] <= 2^31 - 1
    Each element in nums appears exactly three times except for one
    element which appears once.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Plain XOR-folding (001's trick) only cancels values that appear an EVEN
number of times -- three occurrences do NOT cancel under XOR (`x^x^x ==
x`, not 0), so 001's approach gives a wrong, nonsensical answer here.

The generalization: count how many numbers have a 1 bit at EACH of the 32
bit positions, independently. For any bit position, if every number
except the singleton appears 3 times, that position's total count across
all numbers is a MULTIPLE OF 3 contributed by the repeated numbers, plus
either 0 or 1 from the singleton. So `(bit count at position i) % 3`
recovers exactly the singleton's bit at position i.

This ALSO needs the topic's 32-bit masking discipline: nums[i] can be a
genuinely negative Python int (constraints allow the full signed 32-bit
range), and the final reconstructed value must be reinterpreted from an
unsigned 32-bit pattern back to Python's native negative-int
representation if bit 31 ends up set.

PROGRESSIVE HINTS
------------------
Hint 1: For each of the 32 bit positions, sum how many numbers in nums
        have that bit set.
Hint 2: Each sum mod 3 is exactly the singleton's bit at that position
        (since every OTHER number contributes a multiple of 3 to the sum).
Hint 3: Reassemble the 32 recovered bits into a result, then handle sign:
        if bit 31 is set, the true value is negative --
        `result -= (1 << 32)` if `result & (1 << 31)`.

COMPLEXITY TARGET
------------------
    Time:  O(32n) = O(n)
    Space: O(1)
================================================================================
*/

func main() {
	fmt.Println("Solution for Single Number II not implemented yet")
}
