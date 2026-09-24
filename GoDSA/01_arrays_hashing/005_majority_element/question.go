package main

/*
================================================================================
LeetCode 169 · Majority Element                                          [Easy]
https://leetcode.com/problems/majority-element/
Topic: 01 · Arrays & Hashing
================================================================================

PROBLEM
-------
Given an array `nums` of size n, return the majority element.

The majority element is the element that appears more than ⌊n / 2⌋ times. You
may assume that the majority element always exists in the array.


EXAMPLES
--------
Example 1:
    Input:  nums = [3,2,3]
    Output: 3

Example 2:
    Input:  nums = [2,2,1,1,1,2,2]
    Output: 2


CONSTRAINTS
-----------
    n == len(nums)
    1 <= n <= 5 * 10^4
    -10^9 <= nums[i] <= 10^9

FOLLOW UP
---------
    Could you solve the problem in linear time and in O(1) space?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Read "more than ⌊n/2⌋ times" precisely. This is a STRICT majority, not just the
most common element — a far stronger guarantee than it looks, and the whole
trick depends on it:

    n = 7  ->  majority appears at least 4 times
               all other elements COMBINED appear at most 3 times

The majority outnumbers everything else put together. That single fact is what
makes an O(1)-space solution possible.

    [2, 2, 1, 1, 1, 2, 2]     n=7, need > 3 occurrences
     2 appears 4 times  -> majority ✓
     1 appears 3 times  -> not a majority


WHAT TO THINK ABOUT
-------------------
1. Easy answers first: count in a map (O(n) time, O(n) space), or sort and take
   the middle (O(n log n) time, O(1) space). Why does nums[n/2] work at all?

2. The follow-up wants O(n) time AND O(1) space — that rules out both. Suspect
   a cancellation trick rather than a data structure.

3. Think of it as a battle: when two DIFFERENT elements meet they annihilate
   each other. If one element holds more than half the population, can it ever
   be wiped out completely?


GO-SPECIFIC NOTES
-----------------
- `sort.Ints(nums)` MUTATES the caller's slice — slices are views onto a shared
  backing array, so there is no copy. Mention it if you use the sort approach.
- The vote algorithm needs no map at all, so no allocation, no comma-ok, no
  hashing. It is the rare problem where Go's simplest code is also the fastest.
- Integer division `n/2` truncates toward zero for positives, matching ⌊n/2⌋.


PROGRESSIVE HINTS
-----------------
Hint 1: Sorting works because a block longer than half the array must cover the
        middle index, wherever it starts.

Hint 2: For O(1) space keep ONE candidate and ONE counter. When the counter
        hits zero, adopt the current element as the new candidate.

Hint 3: +1 when the element equals the candidate, -1 when it differs. Because
        the majority outnumbers all others combined, it survives.


COMPLEXITY TARGET
-----------------
    Time:  O(n)
    Space: O(1)
================================================================================
*/

// YourMajorityElement is your attempt.
// Implement it, then run:  cd GoDSA && go run ./01_arrays_hashing/005_majority_element
func YourMajorityElement(nums []int) int {
	// YOUR CODE HERE
	return 0
}
