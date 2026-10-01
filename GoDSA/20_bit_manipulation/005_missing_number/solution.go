package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 268 · Missing Number                             [Easy]
https://leetcode.com/problems/missing-number/
================================================================================

PROBLEM
-------
Given an array `nums` containing n distinct numbers in the range
[0, n], return the only number in the range that is missing from the
array.


EXAMPLES
--------
Example 1:
    Input:  nums = [3,0,1]
    Output: 2
    (n = 3, range is [0,3], numbers are [0,1,3], 2 is missing)

Example 2:
    Input:  nums = [0,1]
    Output: 2
    (n = 2, range is [0,2], numbers are [0,1], 2 is missing)

Example 3:
    Input:  nums = [9,6,4,2,3,5,7,0,1]
    Output: 8


CONSTRAINTS
-----------
    n == nums.length
    1 <= n <= 10^4
    0 <= nums[i] <= n
    All the numbers of nums are unique.

Follow up: Could you implement a solution using only O(1) extra space
complexity and O(n) runtime complexity?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Two O(n) time / O(1) space tricks both work here:

    1. Gauss sum: expected sum of 0..n minus actual sum of nums = the
       missing number. Clean, but risks integer overflow in languages
       with fixed-width ints (not a concern in Python).

    2. XOR: XOR every index 0..n together with every value in nums.
       Every number in [0, n] that IS present cancels against its own
       index-visit (x ^ x == 0); only the missing number and the "extra"
       index n (since indices only go 0..n-1 but the range is 0..n)
       survive. This is the "topic 20" way to solve it, and it sidesteps
       overflow entirely since XOR never grows the bit width.

PROGRESSIVE HINTS
------------------
Hint 1: There are n numbers in nums but n+1 possible values in [0, n] --
        exactly one is missing.
Hint 2: XOR-ing a number with itself is 0; XOR-ing every value in [0,n]
        with every value actually present cancels all PRESENT numbers.
Hint 3: `result = n; for i, x in enumerate(nums): result ^= i ^ x`
        (start result at n to cover the one index that has no array
        position, then XOR in each index/value pair).

COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1)
================================================================================
*/

func main() {
	fmt.Println("Solution for Missing Number not implemented yet")
}
