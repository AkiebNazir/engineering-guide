package main

/*
================================================================================
LeetCode 287 · Find the Duplicate Number                               [Medium]
https://leetcode.com/problems/find-the-duplicate-number/
Topic: 08 · Linked List
================================================================================

PROBLEM
-------
Given an array of integers `nums` of length n+1 where every integer is in
the range [1, n] inclusive, there is exactly ONE repeated number (it may
repeat more than twice). Find that number.

You must solve it WITHOUT modifying nums and using only O(1) extra space.


EXAMPLES
--------
Example 1:
    Input:  nums = [1,3,4,2,2]
    Output: 2

Example 2:
    Input:  nums = [3,1,3,4,2]
    Output: 3


CONSTRAINTS
-----------
    1 <= n <= 10^5
    nums.length == n + 1
    1 <= nums[i] <= n
    All integers appear once except one, which appears two or more times.

FOLLOW UP
---------
    Prove at least one duplicate must exist. Solve in O(n) time, O(1) extra
    space, without modifying nums.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

nums[i] is always a valid index (values in [1,n], slots 0..n), so treat the
array as a function next(i) = nums[i] and walk it starting at index 0 — this
is a linked list in disguise. Pigeonhole guarantees the walk enters a cycle,
and the cycle's ENTRANCE is exactly the duplicate value. Reuse Floyd's cycle
detection (problem 003 in this folder) verbatim, with nums[i] standing in
for .Next.


PROGRESSIVE HINTS
------------------
Hint 1: nums[i] is a pointer: i -> nums[i]. Walking from index 0 must enter
        a cycle (pigeonhole: n+1 values, n possible slots).
Hint 2: The duplicate is the cycle's entrance, not the meeting point.
Hint 3: Floyd's phase 1 finds a meeting point; phase 2 (reset one pointer to
        0, advance both one step at a time) finds the entrance.


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1), nums not modified
================================================================================
*/

// YourFindDuplicate is your attempt.
// Implement it, then run: cd GoDSA && go run ./08_linked_list/012_find_the_duplicate_number
func YourFindDuplicate(nums []int) int {
	// YOUR CODE HERE
	return -1
}
