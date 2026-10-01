package main

import "fmt"

/*
================================================================================
LeetCode 167 · Two Sum II - Input Array Is Sorted                      [Medium]
https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/
Topic: 02 · Two Pointers
================================================================================

PROBLEM
-------
Given a 1-INDEXED array of integers `numbers` that is already sorted in
NON-DECREASING ORDER, find two numbers such that they add up to a specific
`target` number. Let these two numbers be numbers[index1] and numbers[index2]
where 1 <= index1 < index2 <= numbers.length.

Return the indices of the two numbers, index1 and index2, ADDED BY ONE, as an
integer array [index1, index2] of length 2.

The tests are generated such that there is EXACTLY ONE SOLUTION. You may not
use the same element twice.

Your solution must use only CONSTANT EXTRA SPACE.


EXAMPLES
--------
Example 1:
    Input:  numbers = [2,7,11,15], target = 9
    Output: [1,2]
    Explanation: 2 + 7 == 9. Return [1, 2].

Example 2:
    Input:  numbers = [2,3,4], target = 6
    Output: [1,3]
    Explanation: 2 + 4 == 6. Return [1, 3].

Example 3:
    Input:  numbers = [-1,0], target = -1
    Output: [1,2]


CONSTRAINTS
-----------
    2 <= numbers.length <= 3 * 10^4
    -1000 <= numbers[i] <= 1000
    numbers is sorted in NON-DECREASING order.
    -1000 <= target <= 1000
    The tests are generated such that there is exactly one solution.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Compare this to LC 1 (Two Sum), which you already solved in topic 01:

                     LC 1                        LC 167 (this one)
    input            UNSORTED                    SORTED
    return           original indices            1-based positions
    space allowed    O(n)                        O(1) — REQUIRED
    right answer     hash map                    two pointers

Those are the same question with two constraints flipped, and the flips change
the answer completely. That pairing is deliberate — interviewers use it to see
whether you pattern-match on the surface ("two sum!") or on the constraints.

A hash map still WORKS here, and it is O(n) time. But it uses O(n) space, and
the problem explicitly forbids that. The sortedness is being handed to you as
a gift; the O(1) requirement is the instruction to use it.


THE ELIMINATION ARGUMENT — this is the whole problem

Put one pointer at each end and look at the sum:

    numbers = [2, 7, 11, 15]   target = 18
               l           r    sum = 2 + 15 = 17  <  18

The array is sorted, so numbers[l] is the SMALLEST value still in play.
It is currently paired with numbers[r], the LARGEST value still in play.
That pairing produces the biggest sum that numbers[l] can possibly reach —
and it still falls short of the target.

Therefore numbers[l] cannot be part of ANY valid pair. Discard it: l += 1.

Symmetrically, if the sum is too BIG, numbers[r] paired with the smallest
available value still overshoots, so numbers[r] is impossible. Discard it:
r -= 1.

Each comparison permanently removes one element from consideration, so the
loop runs at most n times. O(n) time, O(1) space, and no hashing.

That argument — "one endpoint is provably impossible, so throw it away" — is
the engine behind every converging two-pointer solution. Learn to say it out
loud; "I move the pointer because the sum is too small" is a description, not
a justification.


WHAT TO THINK ABOUT
-------------------
1. Write out why moving `l` when the sum is too small is SAFE. What exactly
   are you proving about numbers[l]?

2. Why can you never need to move BOTH pointers at once? Why is it never
   correct to move the "wrong" one?

3. The problem says 1-INDEXED. Where exactly does the +1 go, and how many of
   them are there?

4. Values can be negative and duplicated. Does either break the argument?
   (Test [-1,0] with target -1, and [0,0,3,4] with target 0.)

5. Since exactly one solution is guaranteed, do you need a "not found" branch?
   What would you return if the guarantee were removed?


PROGRESSIVE HINTS
-----------------
Hint 1: `l, r = 0, len(numbers) - 1`. Loop `while l < r`.

Hint 2: Compute `s = numbers[l] + numbers[r]`. Three cases: `s == target`
        (done), `s < target` (need more, so move `l` up), `s > target` (need
        less, so move `r` down).

Hint 3: Return `[l + 1, r + 1]` — both indices need the +1 because the answer
        is 1-indexed.


COMPLEXITY TARGET
-----------------
    Time:  O(n)
    Space: O(1)   — required by the problem, so no hash map
================================================================================
*/

func main() {
	fmt.Println("Solution for Two Sum II - Input Array Is Sorted not implemented yet")
}
