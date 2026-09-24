package main

/*
================================================================================
LeetCode 1929 · Concatenation of Array                                   [Easy]
https://leetcode.com/problems/concatenation-of-array/
Topic: 01 · Arrays & Hashing
================================================================================

PROBLEM
-------
Given an integer array `nums` of length n, you want to create an array `ans` of
length 2n where `ans[i] == nums[i]` and `ans[i + n] == nums[i]` for
0 <= i < n (0-indexed).

Specifically, `ans` is the concatenation of two `nums` arrays.

Return the array `ans`.


EXAMPLES
--------
Example 1:
    Input:  nums = [1,2,1]
    Output: [1,2,1,1,2,1]
    Explanation: ans = [nums[0],nums[1],nums[2],nums[0],nums[1],nums[2]]
                     = [1,2,1,1,2,1]

Example 2:
    Input:  nums = [1,3,2,1]
    Output: [1,3,2,1,1,3,2,1]


CONSTRAINTS
-----------
    n == len(nums)
    1 <= n <= 1000
    1 <= nums[i] <= 1000


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

The gentlest problem in the set. Its job is to make you write a slice-building
loop deliberately, and to introduce the `i + n` offset arithmetic that recurs in
circular-array problems later.

Read the requirement literally:

    ans[i]     == nums[i]        <- first copy, at offset 0
    ans[i + n] == nums[i]        <- second copy, at offset n

    nums  = [1, 2, 1]                n = 3
             0  1  2

    ans   = [1, 2, 1, 1, 2, 1]
             0  1  2  3  4  5
             └──first──┘ └─second─┘
                          i+n where i = 0,1,2


WHAT TO THINK ABOUT (Go specifically)
-------------------------------------
1. You know the output length up front. Use make([]int, 2*n) — do NOT start
   from a nil slice and append 2n times.

2. Go's `append` with the spread operator can concatenate:
       ans := append(nums, nums...)
   ⚠️ This is a TRAP. If `nums` has spare capacity, append writes INTO the
   caller's backing array and mutates their data. Work out why before you use
   it. (The solution file explains this in full — it is the single most
   important Go lesson in this problem.)

3. `copy(dst, src)` copies min(len(dst), len(src)) elements and is a memmove.
   Two copy calls can build the whole answer.


PROGRESSIVE HINTS
-----------------
Hint 1: The output has exactly 2*len(nums) elements. Preallocate.

Hint 2: A single loop over i in [0, n) can write both copies per iteration:
        one at index i, one at index i+n.

Hint 3: Or: make the slice, then `copy(ans, nums)` and `copy(ans[n:], nums)`.


COMPLEXITY TARGET
-----------------
    Time:  O(n)
    Space: O(n) for the output (required; "O(1) extra" means beyond the output).
================================================================================
*/

// YourGetConcatenation is your attempt.
// Implement it, then run:  cd GoDSA && go run ./01_arrays_hashing/001_concatenation_of_array
//
// Unused functions are legal in Go, so this stub compiles as-is.
func YourGetConcatenation(nums []int) []int {
	// YOUR CODE HERE
	return nil
}
