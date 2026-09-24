"""
================================================================================
LeetCode 22 · Generate Parentheses                                     [Medium]
https://leetcode.com/problems/generate-parentheses/
Topic: 06 · Stack
================================================================================

PROBLEM
-------
Given `n` pairs of parentheses, write a function to generate all
combinations of well-formed parentheses.


EXAMPLES
--------
Example 1:
    Input:  n = 3
    Output: ["((()))","(()())","(())()","()(())","()()()"]

Example 2:
    Input:  n = 1
    Output: ["()"]


CONSTRAINTS
-----------
    1 <= n <= 8


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Problem 001 (Valid Parentheses) VALIDATES a fixed string with a real stack.
This problem GENERATES every valid string of a given size, which means
building strings via backtracking — but the thing being tracked, at every
step, is exactly what problem 001's stack would contain: how many opens
are currently unmatched.

You never need an actual `list`-based stack here, because with only one
bracket type, the "stack" degenerates to a single number:

    open_count - close_count  =  current stack depth (how many '(' are
                                  still waiting to be closed)

A partial string is EXTENDABLE with '(' only if you haven't used all n
opens yet, and extendable with ')' only if doing so wouldn't close a
bracket that was never opened — i.e. only if `close_count < open_count`
(there must be more opens placed than closes so far, otherwise the
"stack" would go negative — an invalid state, exactly like problem 001's
mismatch check).


WHAT TO THINK ABOUT
--------------------
1. If you always try '(' before ')' at each step, and backtrack when a
   choice leads nowhere, what two conditions let you legally place each
   character?
2. Why can you never place ')' when `close_count == open_count`? Connect
   this to problem 001's stack-underflow check.
3. When is a partial string COMPLETE (a valid answer to add to the
   result)?
4. What is the maximum recursion depth, and does it relate to `n`?


PROGRESSIVE HINTS
------------------
Hint 1: Backtrack with `path` (a list of characters, or build a string),
        `open_count`, `close_count`. Base case: `len(path) == 2 * n`.

Hint 2: You may append '(' whenever `open_count < n`. You may append ')'
        whenever `close_count < open_count` (never more closes than opens
        placed so far — that's the "stack depth must stay non-negative"
        rule from problem 001, expressed as a counter instead of a list).

Hint 3: At the base case, `open_count == close_count == n` is guaranteed
        by the two guards above — you never need to check it separately;
        every path that reaches length 2n through legal moves is already
        balanced.


COMPLEXITY TARGET
------------------
    Time:  O(4^n / sqrt(n)) — the n-th Catalan number, the exact count of
           valid sequences, dominates the work (this is output-bound: you
           cannot do better than the size of the answer itself).
    Space: O(n) for the recursion depth / current path, not counting the
           O(4^n / sqrt(n)) needed to store the output itself.
================================================================================
"""

from typing import List


class Solution:
    def generateParenthesis(self, n: int) -> List[str]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 006_generate_parentheses_question.py
# ==============================================================================
def _is_valid(s: str) -> bool:
    depth = 0
    for c in s:
        depth += 1 if c == '(' else -1
        if depth < 0:
            return False
    return depth == 0


def run_tests() -> None:
    sol = Solution()
    cases = [1, 2, 3, 4]

    passed = 0
    for n in cases:
        got = sol.generateParenthesis(n)
        expected_count = [1, 2, 5, 14][n - 1]   # Catalan numbers C1..C4
        all_valid = all(_is_valid(s) and len(s) == 2 * n for s in got)
        all_unique = len(set(got)) == len(got)
        ok = len(got) == expected_count and all_valid and all_unique
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n}  count={len(got)} (want {expected_count})"
              f"  all_valid={all_valid}  all_unique={all_unique}")

    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
