package main

/*
================================================================================
LeetCode 15 · 3Sum                                                     [Medium]
https://leetcode.com/problems/3sum/
Topic: 02 · Two Pointers
================================================================================

PROBLEM
-------
Given an integer array `nums`, return all the triplets
`[nums[i], nums[j], nums[k]]` such that `i != j`, `i != k`, and `j != k`, and
`nums[i] + nums[j] + nums[k] == 0`.

Notice that the solution set must NOT CONTAIN DUPLICATE TRIPLETS.


EXAMPLES
--------
Example 1:
    Input:  nums = [-1,0,1,2,-1,-4]
    Output: [[-1,-1,2],[-1,0,1]]
    Explanation:
        nums[0] + nums[1] + nums[2] = (-1) + 0 + 1 = 0.
        nums[1] + nums[2] + nums[4] = 0 + 1 + (-1) = 0.
        nums[0] + nums[3] + nums[4] = (-1) + 2 + (-1) = 0.
        The distinct triplets are [-1,0,1] and [-1,-1,2].
        Notice that the order of the output and the order of the triplets
        does not matter.

Example 2:
    Input:  nums = [0,1,1]
    Output: []
    Explanation: The only possible triplet does not sum up to 0.

Example 3:
    Input:  nums = [0,0,0]
    Output: [[0,0,0]]
    Explanation: The only possible triplet sums up to 0.


CONSTRAINTS
-----------
    3 <= nums.length <= 3000
    -10^5 <= nums[i] <= 10^5


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

The algorithm is a straightforward extension of Two Sum II (LC 167):

    SORT the array. Then FIX the first element with an outer loop, and run the
    converging two-pointer scan on everything to its right, looking for the
    pair that sums to -nums[i].

    O(n) outer × O(n) inner = O(n²), plus O(n log n) to sort.

    nums = [-1,0,1,2,-1,-4]   ->  sorted  [-4,-1,-1,0,1,2]

    i=0, nums[i]=-4  ->  find a pair summing to  4  in [-1,-1,0,1,2]
    i=1, nums[i]=-1  ->  find a pair summing to  1  in [-1,0,1,2]  -> (-1,2) ✓
                                                                   -> (0,1)  ✓
    i=2, nums[i]=-1  ->  SAME VALUE as i=1, would re-find the same triplets
    ...

That last line is the actual problem. 3Sum is not hard because of the third
pointer — it is hard because of **duplicate triplets**, and the note
"must not contain duplicate triplets" is doing all the work.

    WHY SORTING IS THE RIGHT FIRST MOVE
    It buys you two separate things at once:
      1. The converging two-pointer scan needs sortedness (the elimination
         argument from LC 167 depends on it).
      2. Duplicates become ADJACENT, which makes them cheap to skip.
    One O(n log n) purchase, two payoffs. It also destroys the original
    indices — which is fine here, because the problem asks for VALUES.


WHAT TO THINK ABOUT
-------------------
1. After sorting, when should the outer loop SKIP an anchor value? Write the
   condition. Careful: `nums[i] == nums[i-1]` at i=0 reads `nums[-1]`, which
   in Python is the LAST element and does not raise.

2. After you record a valid triplet, both pointers must move. But if you just
   do `l += 1; r -= 1`, the next iteration may find the very same triplet
   again (when there are repeated values). What extra skipping is needed?

3. Do you need to skip duplicates on BOTH the left and the right side after a
   hit, or is one enough? Try to reason it out rather than doing both
   defensively.

4. There is a cheap early exit: once `nums[i] > 0`, can any triplet starting
   there sum to zero? What does that let you do?

5. The alternative to skipping is collecting everything and deduping with a
   `set` of sorted tuples. Why is that a worse answer even though it works?


PROGRESSIVE HINTS
-----------------
Hint 1: `nums.sort()`. Then `for i in range(len(nums) - 2)`, and inside, run
        LC 167's two-pointer scan over `l = i+1`, `r = len(nums)-1` looking for
        the sum `-nums[i]`.

Hint 2: SKIP DUPLICATE ANCHORS. `if i > 0 and nums[i] == nums[i-1]: continue`.
        The `i > 0` guard is mandatory — without it, i=0 compares against
        `nums[-1]`.

Hint 3: SKIP DUPLICATE PARTNERS after recording a hit:
            l += 1
            while l < r and nums[l] == nums[l-1]: l += 1
        Do this AFTER appending the triplet, never before.


COMPLEXITY TARGET
-----------------
    Time:  O(n²)   — dominated by the nested scan, not the O(n log n) sort
    Space: O(1) extra beyond the output (plus whatever sort uses)
================================================================================
*/

// TODO: Implement the stub
