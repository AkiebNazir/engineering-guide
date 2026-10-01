package main

/*
================================================================================
LeetCode 150 · Evaluate Reverse Polish Notation                        [Medium]
https://leetcode.com/problems/evaluate-reverse-polish-notation/
Topic: 06 · Stack
================================================================================

PROBLEM
-------
You are given an array of strings `tokens` that represents an arithmetic
expression in Reverse Polish Notation (postfix notation).

Evaluate the expression. Return an integer that represents the value of the
expression.

Note that:
    - The valid operators are '+', '-', '*', and '/'.
    - Each operand may be an integer or another expression.
    - The division between two integers always truncates TOWARD ZERO.
    - There will not be any division by zero.
    - The input represents a valid arithmetic expression in a reverse polish
      notation.
    - The answer and all the intermediate calculations can be represented in
      a 32-bit integer.


EXAMPLES
--------
Example 1:
    Input:  tokens = ["2","1","+","3","*"]
    Output: 9
    Explanation: ((2 + 1) * 3) = 9

Example 2:
    Input:  tokens = ["4","13","5","/","+"]
    Output: 6
    Explanation: (4 + (13 / 5)) = 6

Example 3:
    Input:  tokens = ["10","6","9","3","+","-11","*","/","*","17","+","5","+"]
    Output: 22
    Explanation:
        ((10 * (6 / ((9 + 3) * -11))) + 17) + 5
        = ((10 * (6 / (12 * -11))) + 17) + 5
        = ((10 * (6 / -132)) + 17) + 5
        = ((10 * 0) + 17) + 5
        = (0 + 17) + 5
        = 22


CONSTRAINTS
-----------
    1 <= tokens.length <= 10^4
    tokens[i] is either an operator: "+", "-", "*", or "/", or an integer
    in the range [-200, 200].


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Postfix notation puts every operator AFTER its two operands, and RPN's
whole point is that it never needs parentheses to disambiguate order —
whatever two values are MOST RECENTLY on the stack when an operator arrives
are exactly the operands it consumes. That "most recent two, consumed by
whatever comes next" is deferred evaluation, the same pattern as problem
002 (Baseball Game), but here the operator REPLACES its two operands with
one result instead of adding a third value.

    number    -> push it
    operator  -> pop the top TWO (b = pop, a = pop — note the ORDER),
                 compute a OP b, push the result


WHAT TO THINK ABOUT
--------------------
1. When you pop two operands for "-" or "/", which one was pushed first —
   and does that mean it should be the LEFT or RIGHT side of the operation?
2. Python's `//` rounds toward NEGATIVE INFINITY, not toward zero
   (`-7 // 2 == -4`, but the problem wants `-3`). How do you truncate
   toward zero for negative results in Python?
3. After processing every token, how many values should remain on the
   stack, and where is the answer?


PROGRESSIVE HINTS
------------------
Hint 1: `stack = []`. Check `token in {"+","-","*","/"}` to distinguish an
        operator from a number string (numbers may start with "-", so don't
        just check `token[0] == '-'`).

Hint 2: On an operator: `b = stack.pop(); a = stack.pop()`. The operand
        pushed FIRST (further from the top) is `a`, the LEFT operand;
        the one pushed SECOND (closer to the top) is `b`, the RIGHT operand.
        `a - b`, not `b - a`.

Hint 3: For division, use `int(a / b)` (true division then truncate via
        `int()`, which truncates toward zero) rather than `a // b` (which
        floors toward negative infinity and gives the wrong answer for
        negative results).

Hint 4: At the end, `stack[0]` (or `stack.pop()`) is the final answer — a
        valid RPN expression always leaves exactly one value on the stack.


COMPLEXITY TARGET
------------------
    Time:  O(n) — one pass, O(1) work per token
    Space: O(n) — the stack can hold up to n operands in the worst case
================================================================================
*/

// TODO: Implement the stub
