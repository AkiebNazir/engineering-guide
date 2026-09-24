"""
================================================================================
SOLUTION · LeetCode 150 · Evaluate Reverse Polish Notation              [Medium]
https://leetcode.com/problems/evaluate-reverse-polish-notation/
================================================================================

THE CORE IDEA
--------------
Postfix notation is designed around exactly what a stack gives you for
free: an operator's two operands are always the MOST RECENTLY produced
values, with no parentheses needed to say so. Push numbers; when an
operator arrives, pop the top two, compute, and push the result back —
this is topic 06's deferred-evaluation pattern (problem 002's sibling),
except here the operator REPLACES two values with one instead of adding a
third.

    stack = []
    for tok in tokens:
        if tok in ('+', '-', '*', '/'):
            b = stack.pop()          # pushed SECOND -> right operand
            a = stack.pop()          # pushed FIRST  -> left operand
            if tok == '+': stack.append(a + b)
            elif tok == '-': stack.append(a - b)
            elif tok == '*': stack.append(a * b)
            else: stack.append(int(a / b))     # truncate toward zero
        else:
            stack.append(int(tok))
    return stack[0]

O(n) time, O(n) space.


================================================================================
POP ORDER MATTERS FOR "-" AND "/" — a, then b, and a OP b (not b OP a)
================================================================================
Tokens ["4", "3", "-"] mean "4 - 3", not "3 - 4". When the operator
arrives, `stack.pop()` returns 3 FIRST (it was pushed last, LIFO), and the
second pop returns 4. The value pushed EARLIER (4) is the LEFT operand;
the value pushed LATER, popped FIRST, (3) is the RIGHT operand:

    b = stack.pop()   # 3  <- popped first, but semantically on the RIGHT
    a = stack.pop()   # 4  <- popped second, but semantically on the LEFT
    result = a - b    # 4 - 3 = 1   ✓

Swapping this (`b - a` instead of `a - b`) silently negates every
subtraction and inverts every division — a bug that only shows up on
non-commutative operators, so a test suite that only checks "+" and "*"
will pass with this bug hiding inside it. The demo below reproduces it.


================================================================================
TRUNCATION TOWARD ZERO — Python's `//` IS THE WRONG OPERATOR HERE
================================================================================
Python's `//` floors toward NEGATIVE INFINITY: `-7 // 2 == -4`. The
problem explicitly requires truncation TOWARD ZERO: `-7 / 2` should give
`-3`, not `-4`. The fix is `int(a / b)` — true division first (a float),
then `int()`, which truncates toward zero regardless of sign:

    -7 // 2      = -4    ✗ floors toward -infinity
    int(-7 / 2)  = -3    ✓ truncates toward zero — what the problem wants
     7 // -2     = -4    ✗ same issue, positive-over-negative
    int(7 / -2)  = -3    ✓

This is a genuine Python-specific gotcha — C, Java, and Go's `/` on
integers already truncates toward zero by default, so this bug is easy to
miss if you're translating intuition from those languages. State this out
loud: "Python's integer `//` floors; I need `int(a / b)` to truncate
toward zero as the problem requires."


================================================================================
STEP BY STEP TRACE
================================================================================
tokens = ["4", "13", "5", "/", "+"]

    tok   action                              stack (after)
    ---   ------                              -------------
    "4"   number, push 4                      [4]
    "13"  number, push 13                     [4, 13]
    "5"   number, push 5                       [4, 13, 5]
    "/"   pop b=5, pop a=13, int(13/5)=2, push  [4, 2]
    "+"   pop b=2, pop a=4, 4+2=6, push          [6]

    final: stack = [6] -> answer 6


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                           Time    Space   Mutates input?  Note
    -----------------------------------  ------  ------  ---------------  ----------------------
    Recursive tree-building then eval    O(n)    O(n)    no               builds an explicit
                                                                            expression tree first
    Stack, evaluate in one pass ✅      O(n)    O(n)    no               the answer, no tree
                                                                          needed at all


================================================================================
EDGE CASES
================================================================================
    Single number, e.g. ["18"]           -> 18. No operators at all; the
                                             loop pushes once and the stack
                                             already holds the answer.
    Negative operand tokens, e.g. "-11"   -> must be distinguished from the
                                             operator "-" by checking the
                                             FULL token against the set
                                             {'+','-','*','/'}, not by
                                             inspecting the first character.
    Division truncating toward zero for
        BOTH signs: -7/2 -> -3, 7/-2 -> -3, -7/-2 -> 3 -> exercises every
                                             sign combination against the
                                             `int(a/b)` fix.
    Result of an intermediate op is 0,
        e.g. ["5","0","*"]                 -> 0, and 0 must still push
                                             correctly (falsy value, not
                                             "no value").
    Deeply nested expression (example 3)  -> exercises the stack holding
                                             several pending intermediate
                                             results at once, not just a
                                             flat left-to-right chain.


================================================================================
COMMON MISTAKES
================================================================================
1. Popping operands in the wrong order for "-" and "/" (`b - a` instead of
   `a - b`) — silently wrong only on non-commutative operators. See above.

2. Using `a // b` for division instead of `int(a / b)` — Python's `//`
   floors toward negative infinity; the problem wants truncation toward
   zero. Wrong specifically (and only visibly) on negative results.

3. Checking `token[0] == '-'` to detect a negative NUMBER, which also
   matches the operator `'-'` itself if not compared against the full
   four-character operator set first — always check membership in
   `{'+','-','*','/'}` before falling through to `int(token)`.

4. Forgetting that division by a negative divisor changes the sign in a
   way that's easy to get backward when hand-verifying — trust the
   `int(a / b)` formula rather than trying to special-case signs manually.

5. Returning `stack.pop()` vs `stack[0]` — for a WELL-FORMED RPN
   expression there is exactly one value left, so both work, but
   `stack.pop()` is the more defensive choice if you ever want to assert
   the stack is empty afterward as a sanity check.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How would you evaluate a normal INFIX expression (with parentheses and
   operator precedence) instead?
A: Two-stack shunting-yard algorithm (one stack for operators/parentheses
   respecting precedence, one for operands), or convert infix to postfix
   first and then reuse this exact evaluator.

Q: What if the expression could contain variables, not just numbers?
A: Push a symbol table lookup instead of `int(tok)` when the token isn't a
   known operator and isn't parseable as a number.

Q: Could you evaluate this recursively instead of iteratively?
A: Yes — process tokens from the END backward, recursively consuming "two
   operands then an operator" isn't natural for postfix (that's prefix's
   shape); a genuinely recursive RPN evaluator would still need an
   explicit stack or equivalent state to track "what have I consumed so
   far," so the iterative stack version is the natural fit here, not a
   simplification of a recursive one.

Q: What's the maximum stack depth in the worst case?
A: A token list that is ALL numbers followed by ALL operators at the very
   end pushes every number before any operator fires — up to
   `ceil((n+1)/2)` numbers on the stack simultaneously for a valid
   expression of length n.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 682  Baseball Game              — problem 002 here: deferred
                                          evaluation on the most recent
                                          results, but ADDS a value instead
                                          of replacing two with one
    LC 224  Basic Calculator           — infix expression with parens,
                                          needs the shunting-yard idea above
    LC 227  Basic Calculator II        — infix with +,-,*,/ and precedence,
                                          no parens
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def evalRPN(self, tokens: List[str]) -> int:
        """Stack: push numbers, pop-compute-push on operators.
        O(n) time, O(n) space. The answer. See THE CORE IDEA above."""
        stack: List[int] = []
        ops = {'+', '-', '*', '/'}
        for tok in tokens:
            if tok in ops:
                b = stack.pop()
                a = stack.pop()
                if tok == '+':
                    stack.append(a + b)
                elif tok == '-':
                    stack.append(a - b)
                elif tok == '*':
                    stack.append(a * b)
                else:
                    stack.append(int(a / b))   # truncate toward zero
            else:
                stack.append(int(tok))
        return stack[0]

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def evalRPN_wrong_order(self, tokens: List[str]) -> int:
        """✗ BROKEN ON PURPOSE — swaps operand order (b OP a instead of
        a OP b). Correct on '+' and '*' (commutative), silently wrong on
        '-' and '/'."""
        stack: List[int] = []
        ops = {'+', '-', '*', '/'}
        for tok in tokens:
            if tok in ops:
                b = stack.pop()
                a = stack.pop()
                if tok == '+':
                    stack.append(b + a)
                elif tok == '-':
                    stack.append(b - a)          # WRONG: should be a - b
                elif tok == '*':
                    stack.append(b * a)
                else:
                    stack.append(int(b / a))     # WRONG: should be a / b
            else:
                stack.append(int(tok))
        return stack[0]

    def evalRPN_floor_division(self, tokens: List[str]) -> int:
        """✗ BROKEN ON PURPOSE — uses Python's `//` (floors toward -inf)
        instead of int(a/b) (truncates toward zero). Wrong for negative
        division results."""
        stack: List[int] = []
        ops = {'+', '-', '*', '/'}
        for tok in tokens:
            if tok in ops:
                b = stack.pop()
                a = stack.pop()
                if tok == '+':
                    stack.append(a + b)
                elif tok == '-':
                    stack.append(a - b)
                elif tok == '*':
                    stack.append(a * b)
                else:
                    stack.append(a // b)         # WRONG: floors, not truncates
            else:
                stack.append(int(tok))
        return stack[0]


# ==============================================================================
# TESTS — run:  python 005_evaluate_reverse_polish_notation_solution.py
# ==============================================================================
CASES = [
    (["2", "1", "+", "3", "*"], 9),
    (["4", "13", "5", "/", "+"], 6),
    (["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"], 22),
    (["18"], 18),
    (["4", "3", "-"], 1),
    (["3", "4", "-"], -1),
    (["7", "2", "/"], 3),
    (["-7", "2", "/"], -3),
    (["7", "-2", "/"], -3),
    (["-7", "-2", "/"], 3),
    (["5", "0", "*"], 0),
    (["2", "3", "*", "4", "-"], 2),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness ---")
    for tokens, expected in CASES:
        got = sol.evalRPN(list(tokens))
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  tokens={tokens!r:<55} -> {got}  (want {expected})")

    # ----------------------------------------------------------------------
    # ⚠️  Operand order swap, demonstrated live.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  correct operand order (a OP b) vs swapped (b OP a) ---")
    order_cases = [(["4", "3", "-"], 1), (["3", "4", "-"], -1),
                   (["7", "2", "/"], 3), (["10", "2", "/"], 5)]
    order_mismatch = False
    for tokens, want in order_cases:
        correct = sol.evalRPN(list(tokens))
        wrong = sol.evalRPN_wrong_order(list(tokens))
        mismatch = correct != wrong
        order_mismatch |= mismatch
        print(f"  tokens={tokens!r:<20} correct={correct:<5} swapped={wrong:<5}  "
              f"{'<- MISMATCH, swap negates non-commutative ops' if mismatch else '(commutative, no diff)'}")
    print(f"  order-swap trap reproduced: {order_mismatch}")
    all_ok &= order_mismatch

    # ----------------------------------------------------------------------
    # ⚠️  Floor division vs truncate-toward-zero, demonstrated live.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  int(a/b) truncate-toward-zero vs a//b floor: negative division ---")
    div_cases = [(["-7", "2", "/"], -3), (["7", "-2", "/"], -3), (["-7", "-2", "/"], 3)]
    div_mismatch = False
    for tokens, want in div_cases:
        correct = sol.evalRPN(list(tokens))
        floored = sol.evalRPN_floor_division(list(tokens))
        mismatch = correct != floored
        div_mismatch |= mismatch
        print(f"  tokens={tokens!r:<20} correct={correct:<5} floor-div={floored:<5}  "
              f"{'<- MISMATCH, // floors toward -inf' if mismatch else ''}")
    print(f"  floor-division trap reproduced: {div_mismatch}")
    all_ok &= div_mismatch

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: tokens = ['4','13','5','/','+'] ---")
    stack: List[int] = []
    ops = {'+', '-', '*', '/'}
    for tok in ["4", "13", "5", "/", "+"]:
        if tok in ops:
            b = stack.pop()
            a = stack.pop()
            if tok == '+':
                res = a + b
            elif tok == '-':
                res = a - b
            elif tok == '*':
                res = a * b
            else:
                res = int(a / b)
            stack.append(res)
            print(f"  tok={tok!r:<5} pop b={b}, a={a} -> {a}{tok}{b}={res}   stack: {stack}")
        else:
            stack.append(int(tok))
            print(f"  tok={tok!r:<5} number, push {tok}         stack: {stack}")
    print(f"  final answer: {stack[0]}")

    # ----------------------------------------------------------------------
    # O(n) timing sanity check (single-pass stack eval scales linearly).
    # ----------------------------------------------------------------------
    print("\n--- O(n) timing sanity check ---")
    print(f"  {'n tokens':>10} {'time':>10}")
    for n_nums in (1_000, 5_000, 20_000):
        # build a long left-associative chain: v1 v2 + v3 + v4 + ...
        toks = [str(random.randint(1, 5)) for _ in range(n_nums)]
        expr = [toks[0]]
        for t in toks[1:]:
            expr.append(t)
            expr.append('+')
        t0 = time.perf_counter()
        sol.evalRPN(expr)
        t1 = time.perf_counter()
        print(f"  {len(expr):>10} {((t1 - t0) * 1000):>8.2f}ms")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
