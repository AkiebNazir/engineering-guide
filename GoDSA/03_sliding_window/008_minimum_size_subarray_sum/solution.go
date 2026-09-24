package main

import "fmt"

/*
================================================================================
LeetCode 209 · Minimum Size Subarray Sum                                [Medium]
https://leetcode.com/problems/minimum-size-subarray-sum/
Topic: 03 · Sliding Window
================================================================================

PROBLEM
-------
Given an array of POSITIVE INTEGERS `nums` and a positive integer `target`,
return the MINIMAL LENGTH of a subarray whose sum is greater than or equal to
`target`. If there is no such subarray, return 0 instead.


EXAMPLES
--------
Example 1:
    Input:  target = 7, nums = [2,3,1,2,4,3]
    Output: 2
    Explanation: The subarray [4,3] has the minimal length under the problem
                 constraint.

Example 2:
    Input:  target = 4, nums = [1,4,4]
    Output: 1

Example 3:
    Input:  target = 11, nums = [1,1,1,1,1,1,1,1]
    Output: 0
    Explanation: The whole array sums to 8 < 11, so no subarray qualifies.


CONSTRAINTS
-----------
    1 <= target <= 10^9
    1 <= nums.length <= 10^5
    1 <= nums[i] <= 10^4       <- READ THIS LINE TWICE. All values are POSITIVE.

FOLLOW UP
---------
    If you have figured out the O(n) solution, try coding another solution of
    which the time complexity is O(n log n).


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Every window so far in this folder has asked for the LONGEST valid window. This
one asks for the SHORTEST, and that flips the template inside out.

    LONGEST (Shape B)                    SHORTEST (Shape C)
      while INVALID:  shrink               while VALID:  record, then shrink
      record AFTER the loop                record INSIDE the loop
      best = max(...)                      best = min(...)
      initialise best = 0                  initialise best = infinity

Think about why. For "longest", a valid window might get better by growing, so
you record once it is repaired and keep expanding. For "shortest", a valid
window might get better by SHRINKING, so you keep shrinking while it stays
valid, recording each time, and stop the moment it breaks.

    target = 7,  nums = [2,3,1,2,4,3]

    [2]                sum 2   < 7
    [2 3]              sum 5   < 7
    [2 3 1]            sum 6   < 7
    [2 3 1 2]          sum 8  >= 7   record len 4, shrink
     [3 1 2]           sum 6   < 7   stop shrinking
     [3 1 2 4]         sum 10 >= 7   record len 4, shrink
      [1 2 4]          sum 7  >= 7   record len 3, shrink
        [2 4]          sum 6   < 7   stop
        [2 4 3]        sum 9  >= 7   record len 3, shrink
          [4 3]        sum 7  >= 7   record len 2, shrink   <- best
            [3]        sum 3   < 7   stop
                                                             answer 2


⚠️  THE CONSTRAINT THAT MAKES THIS LEGAL — do not skip this
-----------------------------------------------------------
`1 <= nums[i]`. All values are POSITIVE. The sliding window depends on it
completely:

    Growing the window can only INCREASE the sum.
    Shrinking the window can only DECREASE the sum.

That monotonicity is what makes `l += 1` a safe, permanent decision: once
`sum < target`, no amount of further shrinking will fix it, so you must grow.

Now consider LC 862 — "Shortest Subarray with Sum at Least K" — which is WORD
FOR WORD the same question but allows NEGATIVE values. There, growing a window
can DECREASE its sum, so a window that is currently too small might be repaired
by extending it, and moving `l` forward throws away real answers. The sliding
window is not slow on LC 862; it is WRONG. LC 862 needs prefix sums plus a
monotonic deque, and it is rated Hard for exactly that reason.

    BEFORE YOU WRITE A SUM-BASED WINDOW, CHECK THE SIGN CONSTRAINT.

The solution file demonstrates the failure empirically — the same code, run on
arrays containing negatives, disagreeing with brute force on ~40% of inputs.


WHAT TO THINK ABOUT
-------------------
1. What do you initialise `best` to, and what do you return when nothing was
   found? (The problem says 0, which is NOT a valid length — so it cannot be
   your initial value.)

2. `while` or `if` for the shrink? Unlike problems 006 and 007, here you really
   do need to shrink as far as possible. Why?

3. Where exactly does the `record` go — before or after `l += 1`? Trace
   target=4, nums=[1,4,4] and see which ordering gives 1 rather than 2.

4. The follow-up asks for O(n log n). What structure do positive values give
   the prefix-sum array, and what does that let you binary search for?

5. Is the O(n log n) solution better or worse than the O(n) one? Why would
   anyone want it?

6. What happens when a single element already exceeds `target`? Does your loop
   handle a window of length 1 correctly?


PROGRESSIVE HINTS
-----------------
Hint 1: Two pointers, both moving right. Grow `r` and add to a running sum.

Hint 2: The template:
            l = 0; total = 0; best = float('inf')
            for r, x in enumerate(nums):
                total += x                            # ENTER
                while total >= target:                # while STILL VALID
                    best = min(best, r - l + 1)       # RECORD first
                    total -= nums[l]; l += 1          # then SHRINK
            return 0 if best == float('inf') else best

Hint 3: Record BEFORE shrinking. If you shrink first you measure a window that
        may no longer be valid.

Hint 4 (follow-up): With all-positive values the prefix-sum array is STRICTLY
        INCREASING. For each right end `r`, you want the largest `l` with
        `pre[l] <= pre[r+1] - target`. A sorted array plus a search for a bound
        is `bisect`.


COMPLEXITY TARGET
-----------------
    Time:  O(n)        — each pointer advances at most n times
           O(n log n)  for the follow-up (prefix sums + binary search)
    Space: O(1)        — one running sum
           O(n)        for the follow-up (the prefix array)
================================================================================
*/

func main() {
	fmt.Println("Solution for Minimum Size Subarray Sum not implemented yet")
}
