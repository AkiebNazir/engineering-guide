"""
================================================================================
SOLUTION · LeetCode 682 · Baseball Game                                  [Easy]
https://leetcode.com/problems/baseball-game/
================================================================================

THE CORE IDEA
--------------
This is topic 06's second pattern: DEFERRED EVALUATION on the most recently
recorded value(s). Every operation only ever looks at the top one or two
entries of the record, and "C" is literally "undo the last push" — that is
a stack by definition, not a coincidence of this problem's rules.

    stack = []
    for op in operations:
        if op == "+":
            stack.append(stack[-1] + stack[-2])
        elif op == "D":
            stack.append(stack[-1] * 2)
        elif op == "C":
            stack.pop()
        else:
            stack.append(int(op))
    return sum(stack)

O(n) time, O(n) space.


================================================================================
"+" ADDS A THIRD SCORE — IT DOES NOT REMOVE THE PREVIOUS TWO
================================================================================
The single most common misreading: "+" is often (wrongly) implemented as
"pop the top two, push their sum" — collapsing three scores into one. Re-read
example 1: after "5","2" the record is [5, 2]; after "+" it becomes
[5, 2, 7] — THREE scores, all counted in the final sum. "D" behaves the same
way: it records a NEW score (double the previous), it does not replace the
previous one. Only "C" actually removes anything.


================================================================================
WHY "C" NEEDS A TRUE STACK, NOT A RUNNING TOTAL
================================================================================
A tempting shortcut is to maintain a running `total` and adjust it in place
for "D" and "+" instead of keeping the whole list. That breaks on "C":
undoing the most recent score requires knowing its EXACT value to subtract
back out, and after several "D"/"+" operations you no longer have that value
unless you kept every individual score around. The stack IS the memory that
makes "C" possible — this is the same "deferred evaluation, most recent
result must be recoverable" idea RPN (problem 005) uses for operators.


================================================================================
STEP BY STEP TRACE
================================================================================
ops = ["5", "-2", "4", "C", "D", "9", "+", "+"]

    op    action                              stack (after)
    --    ------                              -------------
    "5"   number, push 5                      [5]
    "-2"  number, push -2                     [5, -2]
    "4"   number, push 4                      [5, -2, 4]
    "C"   invalidate previous (4) -> pop       [5, -2]
    "D"   double previous (-2) -> push -4      [5, -2, -4]
    "9"   number, push 9                       [5, -2, -4, 9]
    "+"   sum of previous two (-4 + 9 = 5)      [5, -2, -4, 9, 5]
    "+"   sum of previous two (9 + 5 = 14)      [5, -2, -4, 9, 5, 14]

    final sum: 5 + -2 + -4 + 9 + 5 + 14 = 27


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                           Time    Space   Mutates input?  Note
    ----------------------------------  ------  ------  ---------------  ----------------------
    Stack, running sum adjusted live    O(n)    O(n)    no               ✗ WRONG for "C" — see above,
                                                                          kept only as a broken oracle
    Stack, sum(stack) at the end ✅     O(n)    O(n)    no               the answer


================================================================================
EDGE CASES
================================================================================
    ["1"]                    -> 1    Single number, no operators at all.
    ["1", "C"]                -> 0    Everything gets invalidated; record
                                       ends empty, sum of nothing is 0.
    Negative numbers ("-2")   -> the record explicitly allows negative
                                       scores; "D" doubling a negative and
                                       "+" summing with one must both stay
                                       correct in sign.
    "D" applied to 0          -> 0, still a valid new score to record.
    Consecutive "C" ("1","2","3","C","C") -> removes 3, then removes 2,
                                       leaving [1] — tests that "C" pops
                                       from the CURRENT top, not a fixed
                                       position.
    "D" then "C" then "D" again ["5","D","C","D"] -> exercises push/undo/
                                       push against the SAME base value,
                                       confirming the stack top is always
                                       read fresh, never cached.


================================================================================
COMMON MISTAKES
================================================================================
1. Implementing "+" as "pop two, push their sum" instead of "peek two, push
   a THIRD value" — this silently deletes two real scores from the final
   sum. See the section above.

2. Implementing "D" as "double the top value IN PLACE" (`stack[-1] *= 2`)
   instead of pushing a NEW doubled score — same bug, one score short.

3. Maintaining a running total instead of the full stack, breaking "C"'s
   ability to undo an arbitrary earlier operation's exact contribution.

4. Converting `op` to `int` before checking whether it's actually "+", "D",
   or "C" — `int("+")` raises `ValueError`; check the three operator strings
   FIRST, and only attempt `int(op)` in the fallback branch.

5. Off-by-one in "+": using `stack[-2] + stack[-1]` is fine (addition is
   commutative), but reaching for `stack[-1] + stack[-3]` or similar under
   time pressure — always the two MOST RECENT, i.e. `stack[-1]` and
   `stack[-2]`.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if there were more operators, e.g. "M" for "multiply the previous
   TWO scores"?
A: Same pattern — peek `stack[-1]` and `stack[-2]`, push the new derived
   value, add one more `elif` branch. The stack shape doesn't change.

Q: Could you avoid re-summing the whole stack at the end by tracking a
   running total incrementally?
A: Yes, but "C" would need to know the exact popped value to subtract
   (`total -= stack.pop()`), which works fine — the running total isn't
   fundamentally incompatible with "C", it just needs the popped value fed
   back into it rather than being maintained blindly. Either approach is
   O(n); `sum(stack)` at the end is simpler to reason about and just as
   fast for this input size.

Q: What if the record could get very large (millions of operations) and you
   needed getScore-so-far queries interleaved with operations?
A: Track a running total AND update it correctly on every mutation
   (push adds, "C" subtracts the popped value) so each query is O(1)
   instead of re-summing — the same O(1)-aggregate idea as Min Stack
   (problem 004) applied to a sum instead of a min.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 150  Evaluate Reverse Polish Notation — problem 005 here: operators
                                                consume operands the same way
    LC 155  Min Stack                        — problem 004 here: a parallel
                                                aggregate maintained alongside
                                                a stack
    LC 71   Simplify Path                    — "C"-like undo via ".." popping
                                                a directory stack
================================================================================
"""

import time
from typing import List


class Solution:
    def calPoints(self, operations: List[str]) -> int:
        """Stack: push scores, "+"/"D" push derived scores, "C" pops.
        O(n) time, O(n) space. The answer. See THE CORE IDEA above."""
        stack: List[int] = []
        for op in operations:
            if op == "+":
                stack.append(stack[-1] + stack[-2])
            elif op == "D":
                stack.append(stack[-1] * 2)
            elif op == "C":
                stack.pop()
            else:
                stack.append(int(op))
        return sum(stack)

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def calPoints_wrong_plus(self, operations: List[str]) -> int:
        """✗ BROKEN ON PURPOSE — treats "+" as "pop two, push their sum,"
        deleting two real scores instead of adding a third. Also treats "D"
        as doubling in place instead of pushing a new score."""
        stack: List[int] = []
        for op in operations:
            if op == "+":
                a = stack.pop()
                b = stack.pop()
                stack.append(a + b)          # collapses 2 scores into 1
            elif op == "D":
                stack[-1] *= 2               # mutates in place, no new score
            elif op == "C":
                stack.pop()
            else:
                stack.append(int(op))
        return sum(stack)


# ==============================================================================
# TESTS — run:  python 002_baseball_game_solution.py
# ==============================================================================
CASES = [
    (["5", "2", "C", "D", "+"], 30),
    (["5", "-2", "4", "C", "D", "9", "+", "+"], 27),
    (["1"], 1),
    (["1", "C"], 0),
    (["1", "2", "+"], 6),
    (["3", "D", "D"], 21),
    (["-1", "-2", "+"], -6),
    (["0", "0", "+", "D"], 0),
    (["1", "2", "3", "C", "C"], 1),
    (["5", "D", "C", "D"], 15),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness ---")
    for ops, expected in CASES:
        got = sol.calPoints(list(ops))
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  ops={ops!r:<45} -> {got}  (want {expected})")

    # ----------------------------------------------------------------------
    # ⚠️  "+" collapsing two scores instead of adding a third, live.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  correct '+'/'D' (push new score) vs broken (pop/mutate in place) ---")
    trap_cases = [
        ["5", "2", "C", "D", "+"],
        ["5", "-2", "4", "C", "D", "9", "+", "+"],
        ["3", "D", "D"],
    ]
    trap_reproduced = False
    for ops in trap_cases:
        correct = sol.calPoints(list(ops))
        try:
            broken = sol.calPoints_wrong_plus(list(ops))
            broken_str = str(broken)
            mismatch = correct != broken
        except IndexError:
            broken_str = "IndexError"
            mismatch = True
        trap_reproduced |= mismatch
        print(f"  ops={ops!r:<45} correct={correct:<5} broken={broken_str:<10}  "
              f"{'<- MISMATCH/CRASH, broken version drops or corrupts scores' if mismatch else ''}")
    print(f"  trap reproduced: {trap_reproduced}")
    all_ok &= trap_reproduced

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: ops = ['5','-2','4','C','D','9','+','+'] ---")
    stack: List[int] = []
    for op in ["5", "-2", "4", "C", "D", "9", "+", "+"]:
        if op == "+":
            stack.append(stack[-1] + stack[-2])
            desc = f"'+' -> push {stack[-1]}"
        elif op == "D":
            stack.append(stack[-1] * 2)  # note: append happens after we already
            desc = f"'D' -> push {stack[-1]}"
        elif op == "C":
            removed = stack.pop()
            desc = f"'C' -> remove {removed}"
        else:
            stack.append(int(op))
            desc = f"number -> push {op}"
        print(f"  op={op!r:<5} {desc:<20} stack: {stack}")
    print(f"  final sum: {sum(stack)}")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
