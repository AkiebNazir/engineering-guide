package main

import "fmt"

/*
================================================================================
LeetCode 128 · Longest Consecutive Sequence                            [Medium]
https://leetcode.com/problems/longest-consecutive-sequence/
Topic: 01 · Arrays & Hashing
================================================================================

PROBLEM
-------
Given an unsorted array of integers `nums`, return the length of the longest
consecutive elements sequence.

You must write an algorithm that runs in O(n) time.


EXAMPLES
--------
Example 1:
    Input:  nums = [100,4,200,1,3,2]
    Output: 4
    Explanation: The longest consecutive elements sequence is [1,2,3,4].
                 Therefore its length is 4.

Example 2:
    Input:  nums = [0,3,7,2,5,8,4,6,0,1]
    Output: 9
    Explanation: The sequence is [0,1,2,3,4,5,6,7,8].


CONSTRAINTS
-----------
    0 <= nums.length <= 10^5
    -10^9 <= nums[i] <= 10^9


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

"Consecutive" means values that differ by exactly 1 — NOT adjacent positions in
the array. Order in the input is irrelevant:

    nums = [100, 4, 200, 1, 3, 2]

    scattered across the array:      100 . 4 . 200 . 1 . 3 . 2
    what matters is the number line:

        1   2   3   4               100             200
        ●───●───●───●                ●               ●
        └─── run of 4 ───┘         run of 1       run of 1

    answer: 4

Note also that duplicates must not inflate the count: [1,2,2,3] is a run of 3,
not 4.

THE OBVIOUS SOLUTION IS SORTING. Sort, then walk, counting runs and skipping
equal neighbours. That is correct, about eight lines, and O(n log n).

Read the requirement again: **O(n) time**. That single line forbids sorting and
is the entire difficulty of the problem. You have to get "what number comes
next" without ever putting the numbers in order.

The enabling observation: a set gives you O(1) answers to "is x present?". So
you can walk a run on the number line — x, x+1, x+2, ... — without any sorted
structure. But if you start walking from EVERY element, you re-walk the same
run over and over and it degenerates to O(n²).


WHAT TO THINK ABOUT
-------------------
1. Put everything in a set. Now `x + 1 in seen` is O(1). Given a starting
   number, how do you measure the run that begins there?

2. The cost problem: for [1,2,3,...,n] starting at every element walks
   n + (n-1) + (n-2) + ... = O(n²). You must only walk each run ONCE.

3. So: which element of a run should be allowed to do the walking? Every run
   has exactly one element with a special property that no other element in
   that run has. What is it? (Think about what is true of 1 in [1,2,3,4] that
   is not true of 2, 3, or 4.)

4. Once you have that test, prove the total work is O(n): how many times in
   total, across the whole algorithm, is any single number visited by an inner
   walk?

5. What does a set do about duplicates? Is that convenient or a problem here?


PROGRESSIVE HINTS
-----------------
Hint 1: `seen = set(nums)` — membership is now O(1), and duplicates collapse
        for free.

Hint 2: Only START counting at a number that begins a run. `x` begins a run
        exactly when `x - 1` is NOT in the set. Every other member of the run
        is skipped instantly by that one check.

Hint 3: For each such start, walk `x, x+1, x+2, ...` while the next value is in
        the set, counting length; keep the maximum. The `x-1 not in seen` guard
        is what makes the total O(n) — each number is walked by at most one
        run.


COMPLEXITY TARGET
-----------------
    Time:  O(n)
    Space: O(n) for the set
================================================================================
*/

func main() {
	fmt.Println("Solution for Longest Consecutive Sequence not implemented yet")
}
