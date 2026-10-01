package main

import "fmt"

/*
================================================================================
LeetCode 930 · Binary Subarrays With Sum                                [Medium]
https://leetcode.com/problems/binary-subarrays-with-sum/
Topic: 03 · Sliding Window
================================================================================

PROBLEM
-------
Given a binary array `nums` and an integer `goal`, return the NUMBER OF
NON-EMPTY SUBARRAYS with a sum equal to `goal`.

A subarray is a contiguous part of the array.


EXAMPLES
--------
Example 1:
    Input:  nums = [1,0,1,0,1], goal = 2
    Output: 4
    Explanation: The 4 subarrays are bolded and underlined below:
        [1,0,1,_,_]   indices 0..2
        [1,0,1,0,_]   indices 0..3
        [_,0,1,0,1]   indices 1..4
        [_,_,1,0,1]   indices 2..4

Example 2:
    Input:  nums = [0,0,0,0,0], goal = 0
    Output: 15
    Explanation: Every one of the 15 non-empty subarrays sums to 0.


CONSTRAINTS
-----------
    1 <= nums.length <= 3 * 10^4
    nums[i] is either 0 or 1.
    0 <= goal <= nums.length          <- NOTE: goal may be 0


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Two new ideas, and both generalise far beyond this problem.

IDEA 1 · COUNTING WITH A WINDOW
--------------------------------
Every window problem so far returned a LENGTH. This one returns a COUNT of
subarrays. The substitution is one line.

If the validity property is hereditary and `l` is the SMALLEST left index for
which `nums[l..r]` is still valid, then the valid subarrays ENDING AT r are
exactly

    nums[l..r], nums[l+1..r], ..., nums[r..r]

— that is `r - l + 1` of them, and every one is valid because shrinking a valid
window keeps it valid. So:

    best = max(best, r - l + 1)      becomes      count += r - l + 1

That single substitution converts any Shape-B window into a subarray counter.


IDEA 2 · "EXACTLY k" IS NOT A WINDOW — BUT IT IS A DIFFERENCE OF TWO
-------------------------------------------------------------------
Try to write a window for "sum EXACTLY equal to goal" and you will get stuck,
for a precise reason:

    "sum <= k"        is HEREDITARY  (dropping a 0/1 element cannot raise
                                      the sum)               -> window works
    "sum == goal"     is NOT         (shrink a window summing to 2 and you
                                      may land on 1)         -> no window

There is no single `l` boundary to maintain, because validity is not an
interval in `l` — it turns on and off. The standard repair is
inclusion-exclusion:

    exactly(goal)  =  atMost(goal)  −  atMost(goal − 1)

Each half IS hereditary, so each is a plain counting window, and the whole
thing stays O(n) — two linear passes.

    nums = [1,0,1,0,1], goal = 2

        atMost(2) = 14          (all subarrays with sum <= 2)
        atMost(1) = 10          (all subarrays with sum <= 1)
        exactly(2) = 14 - 10 = 4   ✓


⚠️  THE TRAP: goal = 0
----------------------
Then you need `atMost(-1)`, which must be 0 — there are no subarrays with a
negative sum. If your `atMost` does not handle k < 0 it will either return a
nonsense positive number or loop `l` off the end of the array. Guard it
explicitly:

    if k < 0: return 0

Example 2 (goal = 0, answer 15) is precisely the test for this.


WHAT TO THINK ABOUT
-------------------
1. Convince yourself of the counting identity. For nums = [1,0,1] and r = 2
   with l = 0, list the subarrays ending at index 2 and check there are
   r - l + 1 = 3 of them.

2. Why is "sum <= k" hereditary here but "sum == k" not? Say it in one line.

3. What must `atMost(k)` return when k is negative, and where does that come
   up?

4. Is `atMost` a Shape-B (`while invalid: shrink`) window or a Shape-C one?
   What is the validity condition you restore?

5. There is a completely different O(n) solution using PREFIX SUMS and a hash
   map (the LC 560 technique). Write it too — it is the one that survives when
   the array can contain negative numbers.

6. Could you do it in ONE pass instead of two? (Hint: maintain two left
   pointers.) Is it worth it?


PROGRESSIVE HINTS
-----------------
Hint 1: Write a helper `atMost(k)` = the number of subarrays with sum <= k.

Hint 2: `atMost` is the standard window:
            if k < 0: return 0
            l = total = count = 0
            for r, x in enumerate(nums):
                total += x
                while total > k:
                    total -= nums[l]; l += 1
                count += r - l + 1          # <- the counting substitution
            return count

Hint 3: The answer is `atMost(goal) - atMost(goal - 1)`.

Hint 4 (the other solution): running prefix sum `p`, and a Counter of how many
        times each prefix value has been seen. At each step add
        `seen[p - goal]` to the answer, then record `seen[p] += 1`. Start with
        `seen = {0: 1}` for the empty prefix.


COMPLEXITY TARGET
-----------------
    Time:  O(n)   — two linear passes (or one, with prefix sums)
    Space: O(1)   for the window version
           O(n)   for the prefix-sum + hash map version
================================================================================
*/

func main() {
	fmt.Println("Solution for Binary Subarrays With Sum not implemented yet")
}
