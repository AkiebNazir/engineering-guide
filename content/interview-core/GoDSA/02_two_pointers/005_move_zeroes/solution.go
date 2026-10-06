package main

import "fmt"

/*
================================================================================
LeetCode 283 · Move Zeroes                                               [Easy]
https://leetcode.com/problems/move-zeroes/
Topic: 02 · Two Pointers
================================================================================

PROBLEM
-------
Given an integer array `nums`, move all 0's to the END of it while maintaining
the RELATIVE ORDER of the non-zero elements.

Note that you must do this IN PLACE without making a copy of the array.


EXAMPLES
--------
Example 1:
    Input:  nums = [0,1,0,3,12]
    Output: [1,3,12,0,0]

Example 2:
    Input:  nums = [0]
    Output: [0]


CONSTRAINTS
-----------
    1 <= nums.length <= 10^4
    -2^31 <= nums[i] <= 2^31 - 1


FOLLOW UP
---------
    Could you minimise the total number of operations done?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Read the two requirements carefully, because together they rule out the trick
you just learned in LC 27:

    "maintaining the RELATIVE ORDER of the non-zero elements"
        -> you may NOT swap in an element from the back. Order is required.

    "IN PLACE without making a copy"
        -> no list comprehension into a new list.

So this is LC 27's read/write skeleton with `val = 0`... plus one extra step.
LC 27 was allowed to leave garbage past index k. Here the array must be FULLY
correct: the tail has to actually contain zeroes.

    nums = [0, 1, 0, 3, 12]

    Phase 1 — compact the non-zeroes forward (order preserved):
        [1, 3, 12, 3, 12]
                  └── stale leftovers, w = 3

    Phase 2 — fill from w to the end with 0:
        [1, 3, 12, 0, 0]                                              ✓

That is the whole algorithm. It is worth noticing WHY the fill is safe: after
phase 1, exactly (n − w) elements were zeroes, so writing zeroes into exactly
those (n − w) tail slots restores the correct multiset.


THE FOLLOW-UP IS THE INTERESTING PART

"Minimise the total number of operations" points at a real improvement. The
two-phase version writes to every slot: w writes in phase 1 (many of them
`nums[i] = nums[i]` self-assignments) plus (n − w) in phase 2.

A single-pass SWAP version does better:

    for r in range(len(nums)):
        if nums[r] != 0:
            nums[w], nums[r] = nums[r], nums[w]
            w += 1

Each swap moves a non-zero left AND carries a zero right, doing both phases at
once. Think about how many swaps actually happen on an array with no zeroes at
all, and whether you can avoid even those.


WHAT TO THINK ABOUT
-------------------
1. Write the two-phase version first — compact, then fill. It is obviously
   correct and easy to explain.

2. Now the swap version. When `w == r` (no zeroes seen yet), the swap is
   `nums[r], nums[r] = nums[r], nums[r]` — a no-op that still costs work. Can
   you guard it? Is the guard worth a branch per element?

3. Why does the swap version preserve the relative order of the non-zeroes?
   Convince yourself the zero being carried rightward is always the LEFTMOST
   remaining zero.

4. What breaks if you use LC 27's "pull from the back" trick here?

5. Does `nums = [x for x in nums if x] + [0]*zeros` satisfy "in place"?


PROGRESSIVE HINTS
-----------------
Hint 1: Two phases. Phase 1 is exactly LC 27 with val = 0: a write pointer `w`,
        copy every non-zero forward. Phase 2: `for i in range(w, len(nums)):
        nums[i] = 0`.

Hint 2: One pass instead: keep `w` as "the index of the leftmost zero (or the
        next slot to fill)". For each non-zero at `r`, SWAP nums[w] and nums[r],
        then advance `w`.

Hint 3: To minimise operations, skip the swap when `w == r` — there is nothing
        to exchange. That makes an array with no zeroes cost zero writes.


COMPLEXITY TARGET
-----------------
    Time:  O(n)
    Space: O(1)
    Follow-up: minimise WRITES, not just the asymptotic bound.
================================================================================
*/

func main() {
	fmt.Println("Solution for Move Zeroes not implemented yet")
}
