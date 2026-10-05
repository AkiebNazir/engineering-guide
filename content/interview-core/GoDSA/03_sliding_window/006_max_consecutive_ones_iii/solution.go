package main

import "fmt"

/*
================================================================================
LeetCode 1004 · Max Consecutive Ones III                                [Medium]
https://leetcode.com/problems/max-consecutive-ones-iii/
Topic: 03 · Sliding Window
================================================================================

PROBLEM
-------
Given a binary array `nums` and an integer `k`, return the maximum number of
consecutive 1's in the array if you can flip at most `k` 0's.


EXAMPLES
--------
Example 1:
    Input:  nums = [1,1,1,0,0,0,1,1,1,1,0], k = 2
    Output: 6
    Explanation: [1,1,1,0,0,1,1,1,1,1,1]
                          ^   ^
                 Bolded numbers were flipped from 0 to 1.
                 The longest subarray of 1s is underlined: indices 5..10.

Example 2:
    Input:  nums = [0,0,1,1,0,0,1,1,1,0,1,1,0,0,0,1,1,1,1], k = 3
    Output: 10


CONSTRAINTS
-----------
    1 <= nums.length <= 10^5
    nums[i] is either 0 or 1.
    0 <= k <= nums.length             <- NOTE: k may be 0, and k may equal n


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

THE REFRAME — do this first, and the problem dissolves.

"Flip at most k zeros to make the longest run of ones" sounds like a decision
problem: WHICH zeros do you flip? It is not. Flipping is a red herring. Any
subarray you choose becomes all-ones exactly when it contains at most k zeros,
and flipping the zeros inside your chosen subarray is always the best use of
your budget. So the question is really:

    FIND THE LONGEST SUBARRAY CONTAINING AT MOST k ZEROS.

That is a plain Shape-B window (topic guide §1.4). The aggregate is a single
integer — the number of zeros currently inside — and the validity condition is
`zeros <= k`.

    nums = [1,1,1,0,0,0,1,1,1,1,0],  k = 2

    [1 1 1 0 0] 0 1 1 1 1 0        zeros=2  ok      len 5
    [1 1 1 0 0 0]1 1 1 1 0         zeros=3  BROKEN -> shrink from the left
     1[1 1 0 0 0]1 1 1 1 0         zeros=3  still broken
     ...
     1 1 1 0[0 0 1 1 1 1]0         zeros=2  ok      len 6   <- best
     1 1 1 0 0[0 1 1 1 1 0]        zeros=2  ok      len 6   (tie)


WHY THE WINDOW IS LEGAL HERE
----------------------------
"contains at most k zeros" is HEREDITARY: removing elements from a subarray can
only reduce its zero count, never increase it. So if a window is broken
(zeros > k), every WIDER window containing it is broken too, and shrinking from
the left is the only possible repair. That is exactly the precondition from
Part 1.2 of the topic guide.

Note what is NOT required: the values are 0/1 here, but the argument never used
that. The same window works for "at most k elements failing ANY predicate P" —
that is the general form, and it is worth writing your solution so the
substitution is visible.


THE SECOND IDEA — the window that never shrinks
-----------------------------------------------
Once the reframe is done, there is a further simplification specific to
"maximise the length" questions. Instead of

    while zeros > k:   shrink        (window may shrink a lot)

you can write

    if zeros > k:      shrink ONCE   (window slides, keeping its width)

and simply return `n - l` at the end, with no `max` anywhere. Work out why that
is correct before you look it up — the reasoning is short, and it is the whole
idea behind problem 007 in this folder.

Hint towards it: what happens to the window's WIDTH on a step where the window
was already invalid? Can the width ever decrease?


WHAT TO THINK ABOUT
-------------------
1. What is the aggregate, and can you update it in O(1) when an element enters
   and when one leaves? (If not, you do not have a window.)

2. `zeros += 1 - nums[r]` versus `if nums[r] == 0: zeros += 1`. Both work. Is
   the arithmetic version clearer here than it was for the vowels problem?

3. What does k = 0 mean? What should the answer be, and does your code produce
   it without a special case?

4. What if k >= the number of zeros in the whole array? What is the answer?

5. Order of operations: enter, restore, record. Which comes first, and what
   goes wrong if you record before restoring?

6. Can you return the actual subarray bounds rather than the length? What
   changes?


PROGRESSIVE HINTS
-----------------
Hint 1: Stop thinking about flipping. Count zeros in the window instead.

Hint 2: The template:
            l = zeros = best = 0
            for r, x in enumerate(nums):
                zeros += (x == 0)              # ENTER
                while zeros > k:               # RESTORE
                    zeros -= (nums[l] == 0); l += 1
                best = max(best, r - l + 1)    # RECORD
            return best

Hint 3: `r - l + 1`, not `r - l`.

Hint 4: For the never-shrinking form, replace the `while` with `if` and return
        `len(nums) - l`. Convince yourself the width is non-decreasing.


COMPLEXITY TARGET
-----------------
    Time:  O(n)   — l and r each advance at most n times in total
    Space: O(1)   — one counter
================================================================================
*/

func main() {
	fmt.Println("Solution for Max Consecutive Ones III not implemented yet")
}
