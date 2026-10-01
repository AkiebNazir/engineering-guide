package main

/*
================================================================================
LeetCode 282 · Expression Add Operators                                  [Hard]
https://leetcode.com/problems/expression-add-operators/
Topic: 28 · Recursion Mastery
================================================================================
PROBLEM
-------
Given a string `num` that contains only digits and an integer `target`,
return ALL possibilities to insert the binary operators '+', '-', and/or '*'
between the digits of `num` so that the resulting expression evaluates to
`target`.

Note that operands in the returned expressions should not contain leading
zeros.

EXAMPLES
--------
Example 1:
    Input:  num = "123", target = 6
    Output: ["1*2*3","1+2+3"]

Example 2:
    Input:  num = "232", target = 8
    Output: ["2*3+2","2+3*2"]

Example 3:
    Input:  num = "105", target = 5
    Output: ["1*0+5","10-5"]

Example 4:
    Input:  num = "00", target = 0
    Output: ["0+0","0-0","0*0"]
    Explanation: "00" is a valid operand ONLY if it's the single-character
    prefix; a multi-digit operand starting with '0' (like the whole "00" as
    one operand) is NOT allowed, so "0" and "0" must be treated as two
    separate single-digit operands here.

CONSTRAINTS
-----------
    1 <= num.length <= 10
    num consists of only digits.
    -2^31 <= target <= 2^31 - 1

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is BACKTRACKING with a nasty extra wrinkle: multiplication binds
tighter than +/-, so you cannot just track "running total so far" the way
you would for a pure +/- expression. The standard trick is to track the
PREVIOUS OPERAND as a separate value alongside the running total, so that
when the next operator chosen is '*', you can UNDO the previous operand's
contribution and redo it multiplied:

    running_total_so_far = eval - prev_operand           # undo
    new_prev_operand = prev_operand * next_chunk
    running_total_so_far += new_prev_operand              # redo, multiplied

This is exactly why a naive "just track eval-so-far" approach breaks for
multiplication and why `prev` must be threaded through the recursion as its
own piece of state.

The recursion walks `num` left to right, at each position trying every
possible NEXT OPERAND length (1 digit, 2 digits, ... up to the rest of the
string), and for each operand, trying all three operators against the
running state — except at the very first position, where there is no
operator yet (the first chunk is just the starting operand).

A LEADING-ZERO GUARD is required: once an operand's first digit is '0', it
cannot be extended to more digits (no "05", no "00" as a two-digit operand)
— but a single "0" character alone IS a valid operand.

WHAT TO THINK ABOUT
--------------------
1. Why can't a single "running total" variable capture enough state to
   handle '*' correctly, when it already works fine for '+' and '-'?
2. What exactly does "undo, then redo multiplied" mean in terms of the
   `eval` and `prev` values you're carrying? Trace it by hand for
   "1+2*3" arriving at the '*' step.
3. Why must the leading-zero guard check happen on the OPERAND STRING before
   converting to an int (`"05"` looks fine as an int, `5`, but is invalid as
   written), not after?
4. At the very first operand (no operator chosen yet), what should `eval`
   and `prev` be initialized to, so the general-case recursive step still
   works correctly without a special first-iteration branch inside the loop?

PROGRESSIVE HINTS
------------------
Hint 1: Recurse with signature `backtrack(index, path, eval_so_far, prev)`.
        Base case: `index == len(num)` — if `eval_so_far == target`, record
        `path` as one answer.
Hint 2: At each call, try every operand length `L` from 1 up to
        `len(num) - index`. Skip `L > 1` if `num[index] == '0'` (leading-zero
        guard). Let `chunk = num[index:index+L]`, `val = int(chunk)`.
Hint 3: At `index == 0` (no operator yet, first operand): recurse once with
        `eval_so_far = val`, `prev = val`.
Hint 4: Otherwise try three branches: `'+' -> eval+val, prev=val`;
        `'-' -> eval-val, prev=-val`; `'*' -> eval-prev+prev*val,
        prev=prev*val` (the undo-then-redo-multiplied trick, where `prev` is
        stored SIGNED so `-` and `*` compose correctly across further steps).

COMPLEXITY TARGET
------------------
    O(4^n) time in the worst case (3 operator choices + implicitly choosing
    operand length at each of up to n positions; more precisely it's bounded
    by the number of ways to place operators between n-1 gaps, times operand
    lengths, i.e. exponential in n), O(n) space per path plus the recursion
    stack. n <= 10 keeps this tractable.
================================================================================
*/

// TODO: Implement the stub
