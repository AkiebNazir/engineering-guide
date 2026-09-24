package main

/*
================================================================================
LeetCode 217 · Contains Duplicate                                        [Easy]
https://leetcode.com/problems/contains-duplicate/
Topic: 01 · Arrays & Hashing
================================================================================

PROBLEM
-------
Given an integer array `nums`, return true if any value appears at least twice
in the array, and return false if every element is distinct.


EXAMPLES
--------
Example 1:
    Input:  nums = [1,2,3,1]
    Output: true
    Explanation: The element 1 occurs at indices 0 and 3.

Example 2:
    Input:  nums = [1,2,3,4]
    Output: false

Example 3:
    Input:  nums = [1,1,1,3,3,4,3,2,4,2]
    Output: true


CONSTRAINTS
-----------
    1 <= len(nums) <= 10^5
    -10^9 <= nums[i] <= 10^9


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

THE canonical "reach for a hash set" problem — except Go has no set type, so
this is also where you learn the `map[T]struct{}` idiom.

Note the constraint: n up to 10^5. From the constraints table in
_TOPIC_GUIDE.md, 10^5 means O(n log n) is comfortable and O(n) is ideal, but
O(n^2) is ~10^10 operations and will time out. That rules out the double loop
before you write a line.


WHAT TO THINK ABOUT (Go specifically)
-------------------------------------
1. Go has no `set`. Your options are:
       map[int]struct{}   — zero bytes per value, the idiomatic choice
       map[int]bool       — 1 byte per value, but reads nicer: `if seen[x]`
   Both are fine in an interview. Say which tradeoff you picked.

2. Go has no `in` operator. Membership is the comma-ok idiom:
       _, exists := seen[x]
   Remember WHY you need comma-ok: a missing key returns the zero value, so
   `seen[x]` alone cannot distinguish "absent" from "present and false".

3. Preallocate the map when you know roughly how big it gets:
       seen := make(map[int]struct{}, len(nums))
   This avoids repeated incremental growth + evacuation.

4. `sort.Ints` mutates in place. If the caller still needs the original order,
   that is a real cost you must mention.


PROGRESSIVE HINTS
-----------------
Hint 1: Walk the slice once, keeping a set of values seen so far.

Hint 2: Check membership BEFORE inserting, or you will match the element
        against itself and always return true.

Hint 3: Return as soon as you find a repeat — do not finish the scan.


COMPLEXITY TARGET
-----------------
    Time:  O(n)
    Space: O(n)
    (If asked for O(1) space: sort, then compare neighbours. O(n log n) time,
     and it reorders the caller's slice.)
================================================================================
*/

// YourContainsDuplicate is your attempt.
// Implement it, then run:  cd GoDSA && go run ./01_arrays_hashing/002_contains_duplicate
func YourContainsDuplicate(nums []int) bool {
	// YOUR CODE HERE
	return false
}
