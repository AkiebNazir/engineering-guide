package main

/*
================================================================================
LeetCode 992 · Subarrays with K Different Integers                        [Hard]
https://leetcode.com/problems/subarrays-with-k-different-integers/
Topic: 03 · Sliding Window
================================================================================

PROBLEM
-------
Given an integer array `nums` and an integer `k`, return the number of GOOD
SUBARRAYS of `nums`.

A good array is an array where the number of DIFFERENT integers in that array
is EXACTLY `k`.

    For example, [1,2,3,1,2] has 3 different integers: 1, 2, and 3.

A subarray is a contiguous part of an array.


EXAMPLES
--------
Example 1:
    Input:  nums = [1,2,1,2,3], k = 2
    Output: 7
    Explanation: Subarrays formed with exactly 2 different integers:
        [1,2], [2,1], [1,2], [2,3], [1,2,1], [2,1,2], [1,2,1,2]

Example 2:
    Input:  nums = [1,2,1,3,4], k = 3
    Output: 3
    Explanation: Subarrays formed with exactly 3 different integers:
        [1,2,1,3], [2,1,3], [1,3,4]


CONSTRAINTS
-----------
    1 <= nums.length <= 2 * 10^4
    1 <= nums[i], k <= nums.length


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is rated Hard, but if you have done problems 009 and 012 it is a
COMPOSITION of the two, with nothing new invented:

    from 009 (Fruit Into Baskets):
        the "at most K distinct" window, with a Counter and `del` on zero so
        that `len(count)` really is the number of distinct values in the window

    from 012 (Binary Subarrays With Sum):
        the counting substitution  `count += r - l + 1`
        and the identity           exactly(k) = atMost(k) − atMost(k−1)

Put them together:

    def atMostK(k):                       # <- problem 009's window
        count = Counter(); l = res = 0
        for r, x in enumerate(nums):
            count[x] += 1
            while len(count) > k:
                count[nums[l]] -= 1
                if count[nums[l]] == 0:
                    del count[nums[l]]    # <- 009's mandatory line
                l += 1
            res += r - l + 1              # <- 012's counting substitution
        return res

    return atMostK(k) - atMostK(k - 1)    # <- 012's identity

O(n) time, O(k) space.

That is the whole solution. The "Hard" rating is really about whether you can
SEE the decomposition — the individual pieces are Medium at most.


WHY "EXACTLY k DISTINCT" HAS NO DIRECT WINDOW
---------------------------------------------
Same reason as in problem 012. Fix the right end r and ask which left ends give
a valid subarray:

    nums = [1,2,1,2,3], k = 2, r = 4
        l=0  [1,2,1,2,3]  3 distinct   invalid
        l=1    [2,1,2,3]  3 distinct   invalid
        l=2      [1,2,3]  3 distinct   invalid
        l=3        [2,3]  2 distinct   VALID
        l=4          [3]  1 distinct   invalid

The valid left endpoints form a BAND in the middle, not a suffix. A single
pointer `l` cannot describe a band — it can only describe "everything from here
rightwards". "At most k" gives a suffix (one boundary); "exactly k" needs two
boundaries, which is precisely what subtracting two at-most counts provides.


⚠️  THE `del` IS NOT OPTIONAL
-----------------------------
Your loop condition is `len(count) > k`. A Counter keeps keys whose value has
dropped to 0, so without the delete `len(count)` never decreases, the `while`
can never exit, and `l` runs off the end of the array — an IndexError, not a
wrong answer. (Problem 009 demonstrates this in detail.)


WHAT TO THINK ABOUT
-------------------
1. Write `atMostK` first and test it on its own. What should `atMostK(0)`
   return, and does your code produce it without a special case?

2. Why is "at most k distinct" hereditary while "exactly k" is not? One line.

3. What is the space complexity? The Counter is bounded — by what?

4. The answer can be large. How large, roughly, and does that matter in Python?

5. Can you do it in one pass? (Two left pointers, as in problem 012.) What do
   the two pointers mean here?

6. What changes if the question asks for the LONGEST subarray with exactly k
   distinct, rather than the count? (Careful — this is a trap; the at-most
   trick does not transfer.)


PROGRESSIVE HINTS
-----------------
Hint 1: You cannot window "exactly k" directly. Write `atMostK(k)` instead.

Hint 2: `atMostK` is problem 009's window with `count += r - l + 1` in place of
        the `max`.

Hint 3: `del count[x]` when the count reaches 0, or `len(count)` lies and the
        loop never terminates.

Hint 4: `exactly(k) = atMostK(k) - atMostK(k-1)`. Check it by hand on
        [1,2,1,2,3] with k=2: atMostK(2) = 12, atMostK(1) = 5, 12 - 5 = 7 ✓


COMPLEXITY TARGET
-----------------
    Time:  O(n)   — two linear passes
    Space: O(k)   — the Counter never holds more than k+1 keys
================================================================================
*/

// TODO: Implement the stub
