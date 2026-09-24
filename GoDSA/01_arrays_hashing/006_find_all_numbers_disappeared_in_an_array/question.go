package main

/*
================================================================================
LeetCode 448 · Find All Numbers Disappeared in an Array                  [Easy]
https://leetcode.com/problems/find-all-numbers-disappeared-in-an-array/
Topic: 01 · Arrays & Hashing
================================================================================

PROBLEM
-------
Given an array `nums` of n integers where nums[i] is in the range [1, n],
return an array of all the integers in the range [1, n] that do not appear in
`nums`.


EXAMPLES
--------
Example 1:
    Input:  nums = [4,3,2,7,8,2,3,1]
    Output: [5,6]

Example 2:
    Input:  nums = [1,1]
    Output: [2]


CONSTRAINTS
-----------
    n == len(nums)
    1 <= n <= 10^5
    1 <= nums[i] <= n

FOLLOW UP
---------
    Could you do it without extra space and in O(n) runtime? You may assume the
    returned list does not count as extra space.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

The constraint that makes this problem special:

    1 <= nums[i] <= n        every value is a valid INDEX (after a -1 shift)

That is the entire problem. When values span exactly the index range, the array
can serve as its own hash table — you record "I saw value v" inside the slot
that v points to, instead of in a separate structure.

    nums = [4, 3, 2, 7, 8, 2, 3, 1]      n = 8, all values in [1, 8]
            0  1  2  3  4  5  6  7       so value v ↔ index v-1

    Present: 1,2,3,4,7,8      Missing: 5, 6   ->  output [5, 6]


WHAT TO THINK ABOUT (Go specifically)
-------------------------------------
1. Value v maps to index v-1. What can you write into nums[v-1] that means
   "seen" without destroying the magnitude you still need to read later?

2. All values are positive, so the SIGN is a free spare bit.

3. ⚠️ If you mark by negating and then use that value as an index without
   taking the absolute value, Go PANICS:
       panic: runtime error: index out of range [-3]
   Python would silently index from the end and give a wrong answer. Go's
   crash is the friendlier failure — but design for it, don't rely on it.

4. Preallocate the result: make([]int, 0, ...) — you cannot know the exact
   count up front, but capacity 0 forces repeated regrowth.

5. Alternative family: physically SWAP each value into its home slot (cyclic
   sort). Then any index i with nums[i] != i+1 is missing.


PROGRESSIVE HINTS
-----------------
Hint 1: Use the SIGN of nums[v-1] as a one-bit "seen" marker.

Hint 2: Pass 1 — for each value v, negate nums[abs(v)-1]. Go has no builtin
        integer abs; write one, or use `if v < 0 { v = -v }`.

Hint 3: Pass 2 — any index still holding a POSITIVE value was never marked,
        so i+1 never appeared.


COMPLEXITY TARGET
-----------------
    Time:  O(n)
    Space: O(1) extra, excluding the output slice
================================================================================
*/

// YourFindDisappearedNumbers is your attempt.
// Implement it, then run:
//
//	cd GoDSA && go run ./01_arrays_hashing/006_find_all_numbers_disappeared_in_an_array
func YourFindDisappearedNumbers(nums []int) []int {
	// YOUR CODE HERE
	return nil
}
