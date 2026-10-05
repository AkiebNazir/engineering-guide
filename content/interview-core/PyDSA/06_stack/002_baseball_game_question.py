"""
================================================================================
LeetCode 682 · Baseball Game                                             [Easy]
https://leetcode.com/problems/baseball-game/
Topic: 06 · Stack
================================================================================

PROBLEM
-------
You are keeping the scores for a baseball game with strange rules. At the
beginning of the game, you start with an empty record. You are given a list
of strings `operations`, where `operations[i]` is the i-th operation you
must apply to the record, and is one of the following:

    An integer `x`   -> Record a new score of x.
    "+"               -> Record a new score that is the SUM of the previous
                          two scores.
    "D"               -> Record a new score that is DOUBLE the previous score.
    "C"               -> INVALIDATE the previous score, removing it from the
                          record.

Return the sum of all the scores on the record after applying all the
operations.


EXAMPLES
--------
Example 1:
    Input:  ops = ["5","2","C","D","+"]
    Output: 30
    Explanation:
        "5"  -> record: [5]
        "2"  -> record: [5, 2]
        "C"  -> invalidate previous score -> record: [5]
        "D"  -> double previous score -> record: [5, 10]
        "+"  -> sum of previous two -> record: [5, 10, 15]
        sum = 5 + 10 + 15 = 30

Example 2:
    Input:  ops = ["5","-2","4","C","D","9","+","+"]
    Output: 27


CONSTRAINTS
-----------
    1 <= operations.length <= 1000
    operations[i] is "C", "D", "+", or a string representing an integer in
    the range [-3 * 10^4, 3 * 10^4].
    For "+", there will always be at least two previous scores on the record.
    For "C" and "D", there will always be at least one previous score.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Every operation depends ONLY on the one or two MOST RECENT scores, and "C"
literally means "undo the last thing" — this is deferred evaluation on the
most-recently-recorded value, the definition of a stack's top.

    number -> push it
    "+"    -> peek the top TWO, push their sum (both originals stay too)
    "D"    -> peek the top ONE, push double it
    "C"    -> pop (remove) the top ONE, nothing pushed

At the end, sum everything still on the stack.


WHAT TO THINK ABOUT
--------------------
1. For "+", do the two previous scores get REMOVED, or do they stay on the
   record and a THIRD score (their sum) gets added? Re-read example 1.
2. Does "D" remove the previous score, or also keep it and add a new one?
3. Why does the problem guarantee "at least two previous scores" for "+" and
   "at least one" for "C"/"D" — what would break without that guarantee?


PROGRESSIVE HINTS
------------------
Hint 1: `stack = []`. Try converting each op string to see if it's an
        integer first (`op.lstrip('-').isdigit()` or a try/except).

Hint 2: "+"  -> `stack.append(stack[-1] + stack[-2])`
        "D"  -> `stack.append(stack[-1] * 2)`
        "C"  -> `stack.pop()`
        number -> `stack.append(int(op))`

Hint 3: The final answer is `sum(stack)` — not a running total maintained
        alongside, since "C" needs to be able to remove a score cleanly.


COMPLEXITY TARGET
------------------
    Time:  O(n) — one pass, O(1) work per operation
    Space: O(n) — the stack can hold up to n scores
================================================================================
"""


class Solution:
    def calPoints(self, operations: list[str]) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 002_baseball_game_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        (["5", "2", "C", "D", "+"], 30),
        (["5", "-2", "4", "C", "D", "9", "+", "+"], 27),
        (["1"], 1),
        (["1", "C"], 0),
        (["1", "2", "+"], 6),            # [1,2,3] -> sum 6
        (["3", "D", "D"], 21),          # 3, 6, 12 -> sum 21
        (["-1", "-2", "+"], -6),         # [-1,-2,-3] -> sum -6
        (["0", "0", "+", "D"], 0),
        (["1", "2", "3", "C", "C"], 1),  # remove 3, then 2 -> [1]
        (["5", "D", "C", "D"], 15),      # 5,10 -> remove 10 -> [5] -> D -> [5,10]
    ]

    passed = 0
    for ops, expected in cases:
        got = sol.calPoints(list(ops))
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  ops={ops!r:<45} -> {got}  (want {expected})")

    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
