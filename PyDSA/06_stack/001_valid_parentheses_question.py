"""
================================================================================
LeetCode 20 · Valid Parentheses                                          [Easy]
https://leetcode.com/problems/valid-parentheses/
Topic: 06 · Stack
================================================================================

PROBLEM
-------
Given a string `s` containing just the characters '(', ')', '{', '}', '[' and
']', determine if the input string is valid.

An input string is valid if:
    1. Open brackets must be closed by the same type of bracket.
    2. Open brackets must be closed in the correct ORDER.
    3. Every close bracket has a corresponding open bracket of the same type.


EXAMPLES
--------
Example 1:
    Input:  s = "()"
    Output: true

Example 2:
    Input:  s = "()[]{}"
    Output: true

Example 3:
    Input:  s = "(]"
    Output: false

Example 4:
    Input:  s = "([)]"
    Output: false
    Explanation: brackets are individually balanced in count, but the ORDER
                 is wrong — ')' closes before '[' does, even though '[' opened
                 more recently.


CONSTRAINTS
-----------
    1 <= s.length <= 10^4
    s consists of parentheses only '()[]{}'.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

The word that matters is ORDER, not count. "([)]" has two '(' /')' and two
'[' /']' — perfectly balanced in count — and is still invalid, because the
close that arrives (')') does not match the bracket that is MOST RECENTLY
still open ('[').

"Most recently still open" is exactly the definition of the top of a stack.
So: push every open bracket. On every close bracket, it must match whatever
is currently on top of the stack — if it does, pop; if it doesn't (wrong
type, or nothing on the stack at all), the string is invalid immediately.


WHAT TO THINK ABOUT
--------------------
1. What do you push — the bracket itself, or something else?
2. When you see a close bracket, what are the TWO ways it can fail to match
   (think about what happens with an empty stack)?
3. After the whole string is processed, is an empty string automatically
   valid? Is a string like "(((" (all opens, no closes) valid?
4. How would you check "does this close bracket match this open bracket"
   without writing a long if/elif chain for six characters?


PROGRESSIVE HINTS
------------------
Hint 1: `stack = []`. For an open bracket, push it. For a close bracket, you
        need to look at (and remove) whatever is on top.

Hint 2: Build a mapping from close bracket -> its matching open bracket:
        `pairs = {')': '(', ']': '[', '}': '{'}`. On a close bracket `c`,
        check `stack and stack[-1] == pairs[c]`; if so pop, else return False.

Hint 3: Two distinct failure modes for a close bracket: the stack is EMPTY
        (a close with nothing open to match), or the stack's top is the
        WRONG open bracket. Both should return False immediately.

Hint 4: At the very end, the string is valid only if the stack is EMPTY —
        any leftover unclosed opens make it invalid.


COMPLEXITY TARGET
------------------
    Time:  O(n) — one pass, O(1) work per character
    Space: O(n) worst case — a string of all opens pushes everything
================================================================================
"""


class Solution:
    def isValid(self, s: str) -> bool:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 001_valid_parentheses_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ("()", True),
        ("()[]{}", True),
        ("(]", False),
        ("([)]", False),
        ("{[]}", True),
        ("", True),
        ("(", False),
        (")", False),
        ("(((", False),
        (")))", False),
        ("([{}])", True),
        ("([{}()])", True),
        ("]", False),
        ("(){}}{", False),
        ("(((((((((())))))))))" , True),
        ("((()", False),
    ]

    passed = 0
    for text, expected in cases:
        got = sol.isValid(text)
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  s={text!r:<24} -> {got}  (want {expected})")

    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
