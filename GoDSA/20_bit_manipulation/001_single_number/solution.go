package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 136 · Single Number                              [Easy]
https://leetcode.com/problems/single-number/
================================================================================

PROBLEM
-------
Given a non-empty array of integers `nums`, every element appears TWICE
except for one. Find that single one.

You must implement a solution with linear runtime complexity and use only
constant extra space.


EXAMPLES
--------
Example 1:
    Input:  nums = [2,2,1]
    Output: 1

Example 2:
    Input:  nums = [4,1,2,1,2]
    Output: 4

Example 3:
    Input:  nums = [1]
    Output: 1


CONSTRAINTS
-----------
    1 <= nums.length <= 3 * 10^4
    -3 * 10^4 <= nums[i] <= 3 * 10^4
    Each element in the array appears twice except for one element which
    appears only once.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
"Constant extra space" rules out a hash-set frequency count (O(n) space).
The "twice" constraint is the tell: XOR is the operation where a value
cancels itself out (x ^ x == 0) and is a no-op against zero (x ^ 0 == x).
XOR every element together and every paired value cancels, leaving only
the singleton.

PROGRESSIVE HINTS
------------------
Hint 1: What operation, applied to the same value twice, gives 0?
Hint 2: XOR is commutative and associative -- order doesn't matter.
Hint 3: `result = 0; for x in nums: result ^= x`.

COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1)
================================================================================
*/

func main() {
	fmt.Println("Solution for Single Number not implemented yet")
}
