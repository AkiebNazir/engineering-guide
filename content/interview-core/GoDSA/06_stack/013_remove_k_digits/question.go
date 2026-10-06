package main

/*
================================================================================
LeetCode 402 · Remove K Digits                                          [Medium]
https://leetcode.com/problems/remove-k-digits/
Topic: 06 · Stack & Monotonic Stack
================================================================================

PROBLEM
-------
Given a string `num` representing a non-negative integer and an integer k,
return the SMALLEST possible integer after removing exactly k digits from
num.


EXAMPLES
--------
Example 1:   num = "1432219", k = 3  ->  "1219"
             Remove 4, 3, and 2.

Example 2:   num = "10200", k = 1    ->  "200"
             Remove the leading 1. The result must not have leading zeros.

Example 3:   num = "10", k = 2       ->  "0"
             Remove everything; the empty result is "0".


CONSTRAINTS
-----------
    1 <= k <= num.length <= 10^5
    num consists of only digits.
    num does not have any leading zeros except for the zero itself.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Remaining digits keep their order, and every result has the same length
(n - k). Among numbers of equal length, the smaller one is the one with the
smaller digit at the FIRST position where they differ.

So make the leftmost digit as small as possible, then the next, and so on.
Whenever a digit is bigger than the digit right after it (a "peak"), deleting
that peak makes the number smaller at that position. Delete the LEFTMOST peak,
repeat k times.

Doing that literally is O(n * k). A stack does all k deletions in one pass.


WHAT TO THINK ABOUT
--------------------
1. Why remove the leftmost peak and not, say, the biggest digit?
   (Try "1432219": removing the 9 gives 143221, removing 4 gives 132219.)

2. What does the stack look like if you pop every digit that's bigger than
   the incoming digit (while deletions remain)?

3. What if the digits are increasing and nothing gets popped?

4. What about leading zeros and an empty result?


PROGRESSIVE HINTS
------------------
Hint 1: Monotonic non-decreasing stack of digits.

Hint 2: For each digit d: while k > 0 and stack and stack[-1] > d: pop, k -= 1.
        Then push d.

Hint 3: If k is still > 0, chop k digits off the END. Strip leading zeros.
        Return "0" if nothing is left.


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(n)
================================================================================
*/

// TODO: Implement the stub
