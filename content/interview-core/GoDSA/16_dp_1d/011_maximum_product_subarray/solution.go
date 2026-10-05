package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 152 · Maximum Product Subarray                    [Medium]
https://leetcode.com/problems/maximum-product-subarray/
================================================================================

PROBLEM
-------
Given an integer array nums, find a subarray that has the largest product,
and return the product.

The test cases are generated so that the answer will fit in a 32-bit
integer.


EXAMPLES
--------
Example 1:
    Input:  nums = [2,3,-2,4]
    Output: 6
    Explanation: [2,3] has the largest product 6.

Example 2:
    Input:  nums = [-2,0,-1]
    Output: 0
    Explanation: the result cannot be 2, because [-2,-1] is not a
                 contiguous subarray (0 is between them).


CONSTRAINTS
-----------
    1 <= nums.length <= 2 * 10^4
    -10 <= nums[i] <= 10
    The product of any subarray of nums is guaranteed to fit in a 32-bit
    integer.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This looks like House Robber's "max ending here" pattern, but PRODUCT
breaks the naive version of that idea: a NEGATIVE number can turn the
smallest (most negative) running product into the LARGEST one with one
more multiplication. So track TWO rolling states per index instead of
one: maxEnd[i] = max product of a subarray ENDING exactly at i, AND
minEnd[i] = min product of a subarray ending exactly at i (the one that
might flip into the new max when multiplied by a negative num[i]):

    candidates = (nums[i], maxEnd[i-1] * nums[i], minEnd[i-1] * nums[i])
    maxEnd[i] = max(candidates)
    minEnd[i] = min(candidates)
    answer = max(maxEnd[i] for all i)

PROGRESSIVE HINTS
------------------
Hint 1: For SUM (Kadane's algorithm), only a running max is needed because
        adding a negative number never turns a small sum into a large one
        faster than starting over. Multiplication breaks this: verify with
        [2,3,-2,4] -- what does -2 do to the running product?
Hint 2: Track BOTH a running max product and a running min product ending
        at each position -- the min can become the max after one more
        negative multiplication.
Hint 3: At each index, the new max is the best of: nums[i] alone,
        prevMax*nums[i], prevMin*nums[i] -- try all three, don't guess
        which one wins without checking (the sign of nums[i] decides it).
Hint 4: A zero resets both running products to 0 (any subarray "through"
        the zero contributes a product of 0, breaking the chain) --
        nums[i] alone as a candidate handles this correctly if included
        in the max() and min() every iteration.

COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1)
================================================================================
*/

func main() {
	fmt.Println("Solution for Maximum Product Subarray not implemented yet")
}
