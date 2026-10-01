package main

/*
================================================================================
LeetCode 1 · Two Sum                                                     [Easy]
https://leetcode.com/problems/two-sum/
Topic: 01 · Arrays & Hashing
================================================================================

PROBLEM
-------
Given an array of integers `nums` and an integer `target`, return indices of the
two numbers such that they add up to `target`.

You may assume that each input would have exactly one solution, and you may not
use the same element twice.

You can return the answer in any order.


EXAMPLES
--------
Example 1:
    Input:  nums = [2,7,11,15], target = 9
    Output: [0,1]
    Explanation: nums[0] + nums[1] == 9, so we return [0, 1].

Example 2:
    Input:  nums = [3,2,4], target = 6
    Output: [1,2]

Example 3:
    Input:  nums = [3,3], target = 6
    Output: [0,1]


CONSTRAINTS
-----------
    2 <= len(nums) <= 10^4
    -10^9 <= nums[i] <= 10^9
    -10^9 <= target <= 10^9
    Only one valid answer exists.

FOLLOW UP
---------
    Can you come up with an algorithm that is less than O(n^2) time complexity?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

The most-asked interview question there is, because it is the smallest possible
demonstration of one idea:

    Turn "search for the thing I need" into "look up the thing I need."

Brute force asks, for every pair (i, j), "do these sum to target?" — n^2
questions. But once you fix nums[i], the partner is completely determined:

    complement = target - nums[i]

So the real question is "have I already seen `complement`?" That is a
membership question, and membership belongs in a map.

    nums = [2, 7, 11, 15], target = 9

    i=0, nums[0]=2  ->  need 9-2 = 7.  Seen 7? No.   Remember 2 -> 0.
    i=1, nums[1]=7  ->  need 9-7 = 2.  Seen 2? YES at index 0.
                        return [0, 1]

Two details make it correct:
  - store VALUE -> INDEX, because the problem wants indices back
  - CHECK before INSERT, which stops an element pairing with itself


WHAT TO THINK ABOUT (Go specifically)
-------------------------------------
1. Return type is []int of INDICES, not values.

2. Membership is the comma-ok idiom:
       if j, ok := seen[complement]; ok { return []int{j, i} }
   You cannot use `if seen[complement] != 0` — a missing key returns 0, which
   is also a perfectly valid index. This is exactly the bug comma-ok exists to
   prevent, and Two Sum is where it bites hardest.

3. Preallocate: make(map[int]int, len(nums)).

4. Integer overflow is real in Go. target - nums[i] with both near ±10^9 stays
   inside int64 comfortably, so this problem is safe — but form the habit of
   asking, because on a 32-bit int it would not be.


PROGRESSIVE HINTS
-----------------
Hint 1: For each element the number you need is forced: target - nums[i].
        You are searching for one value, not a pair.

Hint 2: map[int]int answers "have I seen this value, and at which index?"
        in O(1) average.

Hint 3: One pass. At each i: if (target - nums[i]) is already in the map, done.
        Otherwise record nums[i] -> i and continue.


COMPLEXITY TARGET
-----------------
    Time:  O(n)
    Space: O(n)
================================================================================
*/

// YourTwoSum is your attempt.
// Implement it, then run:  cd GoDSA && go run ./01_arrays_hashing/004_two_sum
func YourTwoSum(nums []int, target int) []int {
	// YOUR CODE HERE
	return nil
}
