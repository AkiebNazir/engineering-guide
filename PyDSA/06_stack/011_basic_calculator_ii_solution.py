"""
================================================================================
SOLUTION · LeetCode 227 · Basic Calculator II                           [Medium]
https://leetcode.com/problems/basic-calculator-ii/
================================================================================

THE CORE IDEA
--------------
Treat the expression as a sum of signed TERMS. Scan left to right, holding the
operator that came BEFORE the current number. When a number ends:

    '+'  push  num                (start a new term)
    '-'  push -num                (start a new negative term)
    '*'  push  pop() * num        (grow the current term)
    '/'  push  trunc(pop() / num) (grow the current term)

Precedence falls out for free: * and / only ever touch the top of the stack,
and + / - only ever push. The answer is sum(stack).


================================================================================
APPROACH 1 · Two passes (priced, not coded)
================================================================================
Tokenize, evaluate all * and / left to right collapsing tokens, then evaluate
+ and -. Correct and easy to reason about; allocates token lists twice.

    Time: O(n)    Space: O(n)


================================================================================
APPROACH 2 · Stack of terms ✅ (the answer)
================================================================================
    stack, num, op = [], 0, '+'
    for i, ch in enumerate(s):
        if ch.isdigit():
            num = num * 10 + int(ch)
        if ch in '+-*/' or i == len(s) - 1:
            if   op == '+': stack.append(num)
            elif op == '-': stack.append(-num)
            elif op == '*': stack.append(stack.pop() * num)
            else:           stack.append(trunc_div(stack.pop(), num))
            op, num = ch, 0
    return sum(stack)

Note the two `if`s are not an if/elif: the LAST character is usually a digit
and must also flush the final number.

TRUNCATION. A term can be negative (it was pushed as -num), so division can
see a negative dividend. Python's `//` floors: -3 // 2 == -2. The problem wants
-1. Use sign-aware division:

    def trunc_div(a, b):
        q = abs(a) // abs(b)
        return q if (a >= 0) == (b > 0) else -q

    Time: O(n)    Space: O(n)


================================================================================
APPROACH 3 · O(1) space: running total + last term
================================================================================
The stack is only ever touched at the top, and everything below the top is
just summed at the end. So keep `total` (sum of finished terms) and `last`
(the term still growing):

    '+'  total += last; last =  num
    '-'  total += last; last = -num
    '*'  last = last * num
    '/'  last = trunc_div(last, num)
    end: return total + last

    Time: O(n)    Space: O(1)


================================================================================
STEP BY STEP TRACE · s = "14-3/2"
================================================================================
    i  ch  num after  flush?  op applied  stack after   next op
    -  --  ---------  ------  ----------  ------------  -------
    0  1   1          no                  []            +
    1  4   14         no                  []            +
    2  -   14         yes     '+' push 14 [14]          -
    3  3   3          no                  [14]          -
    4  /   3          yes     '-' push -3 [14, -3]      /
    5  2   2          yes     '/' trunc(-3/2) = -1
                              (floor would be -2)  [14, -1]

    sum = 13


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time   Space   Mutates input?
    ---------------------------  -----  ------  --------------------------
    Two passes over tokens       O(n)   O(n)    No (strings immutable)
    Stack of terms ✅            O(n)   O(n)    No
    Running total + last term    O(n)   O(1)    No


================================================================================
EDGE CASES
================================================================================
    Single number "42"         Flushed by the i == len(s) - 1 check.
    Spaces everywhere          Ignored: not a digit, not an operator.
    Trailing spaces "3/2 "     Flush happens at the last index even though it's
                                a space — num still holds 2.
    Negative dividend          "14-3/2": needs truncation, not floor.
    Multi-digit numbers        Accumulate num = num * 10 + digit.
    Zero                       "0-0" is fine; division by zero can't occur in
                                valid input.


================================================================================
COMMON MISTAKES
================================================================================
1. Using `//`. Matches truncation only for non-negative operands. "14-3/2"
   returns 12 instead of 13. Demo below.

2. Using `int(a / b)` without thinking. Works here because |values| < 2^31 fit
   exactly in a float, but for big integers float division loses precision.
   The demo shows it failing on a 10^20-sized dividend.

3. Writing `elif` for the flush branch, so a digit at the end of the string
   never gets flushed.

4. Applying the operator AFTER the number instead of BEFORE it. The operator
   you just read decides what happens to the NEXT number.

5. Calling eval(). Explicitly banned, and a security hole in real code.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Add parentheses (Basic Calculator III, LC 772)?
A: Recurse on '(' (evaluate the inside with the same routine, returning the
   index where ')' ended) and treat the result as a number. Or use two stacks
   (shunting-yard).

Q: Add unary minus ("-3+2", "2*-1")?
A: Treat '-' that appears at the start or right after another operator as part
   of the number's sign.

Q: Variables and a symbol table?
A: Tokenize first, look up identifiers when a number is expected. At that
   point build a real parser (recursive descent with one function per
   precedence level).

Q: Why not convert to Reverse Polish Notation first?
A: That's shunting-yard, and then 06_stack/005 (Evaluate RPN) evaluates it.
   Correct, general, and more code than this problem needs.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 150  Evaluate Reverse Polish Notation (005)
    LC 224  Basic Calculator                — + - and parentheses
    LC 772  Basic Calculator III            — all four ops and parentheses
    LC 282  Expression Add Operators        — backtracking with the same "last term" trick
================================================================================
"""

import random
import time
from typing import List


def trunc_div(a: int, b: int) -> int:
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


class Solution:
    def calculate(self, s: str) -> int:
        stack: List[int] = []
        num = 0
        op = "+"
        last_index = len(s) - 1
        for i, ch in enumerate(s):
            if ch.isdigit():
                num = num * 10 + (ord(ch) - 48)
            if ch in "+-*/" or i == last_index:
                if op == "+":
                    stack.append(num)
                elif op == "-":
                    stack.append(-num)
                elif op == "*":
                    stack.append(stack.pop() * num)
                else:
                    stack.append(trunc_div(stack.pop(), num))
                op = ch
                num = 0
        return sum(stack)


# ------------------------------------------------------------------------
# Alternatives / oracle / broken versions for the demos.
# ------------------------------------------------------------------------
def calc_o1(s: str) -> int:
    total = last = num = 0
    op = "+"
    last_index = len(s) - 1
    for i, ch in enumerate(s):
        if ch.isdigit():
            num = num * 10 + (ord(ch) - 48)
        if ch in "+-*/" or i == last_index:
            if op == "+":
                total += last; last = num
            elif op == "-":
                total += last; last = -num
            elif op == "*":
                last *= num
            else:
                last = trunc_div(last, num)
            op = ch
            num = 0
    return total + last


def calc_floor_bug(s: str) -> int:
    """Mistake 1: floor division instead of truncation."""
    stack: List[int] = []
    num, op = 0, "+"
    for i, ch in enumerate(s):
        if ch.isdigit():
            num = num * 10 + int(ch)
        if ch in "+-*/" or i == len(s) - 1:
            if op == "+": stack.append(num)
            elif op == "-": stack.append(-num)
            elif op == "*": stack.append(stack.pop() * num)
            else: stack.append(stack.pop() // num)      # BUG
            op, num = ch, 0
    return sum(stack)


def calc_float_div(s: str) -> int:
    """Mistake 2: int(a / b) — fine for 32-bit values, wrong for huge ones."""
    stack: List[int] = []
    num, op = 0, "+"
    for i, ch in enumerate(s):
        if ch.isdigit():
            num = num * 10 + int(ch)
        if ch in "+-*/" or i == len(s) - 1:
            if op == "+": stack.append(num)
            elif op == "-": stack.append(-num)
            elif op == "*": stack.append(stack.pop() * num)
            else: stack.append(int(stack.pop() / num))   # float round trip
            op, num = ch, 0
    return sum(stack)


def oracle(s: str) -> int:
    """Independent check: Python evaluates the same grammar, with // replaced by
    truncating division through a tiny wrapper class. Test-only; never in a
    real solution."""
    class T(int):
        def __truediv__(self, other):
            return T(trunc_div(int(self), int(other)))
        def __mul__(self, other): return T(int(self) * int(other))
        def __add__(self, other): return T(int(self) + int(other))
        def __sub__(self, other): return T(int(self) - int(other))
    import re
    expr = re.sub(r"(\d+)", r"T(\1)", s)
    return int(eval(expr, {"T": T}))   # noqa: S307 — oracle only


# ==============================================================================
# TESTS — run:  python 011_basic_calculator_ii_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: stack vs O(1) variant ---")
    cases = [
        ("3+2*2", 7),
        (" 3/2 ", 1),
        (" 3+5 / 2 ", 5),
        ("14-3/2", 13),
        ("42", 42),
        ("1-1+1", 1),
        ("2*3*4-10/3", 21),
        ("0-2147483647", -2147483647),
        ("1000000*2/3", 666666),
    ]
    for s, want in cases:
        a, b = sol.calculate(s), calc_o1(s)
        ok = a == b == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  s={s!r:<18} stack={a}  O(1)={b}  want={want}")

    print("\n--- randomized cross-check vs an independent evaluator (1000 expressions) ---")
    rng = random.Random(227)
    bad = 0
    for _ in range(1000):
        parts = [str(rng.randint(0, 50))]
        for _ in range(rng.randint(0, 6)):
            parts.append(rng.choice(" + - * / ".split()))
            parts.append(str(rng.randint(1, 50)))
        s = " ".join(parts)
        want = oracle(s)
        if sol.calculate(s) != want or calc_o1(s) != want:
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  1000 random expressions agree")

    print("\n--- mistake 1 LIVE: floor division on a negative term ---")
    wrong, right = calc_floor_bug("14-3/2"), sol.calculate("14-3/2")
    ok = wrong == 12 and right == 13
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  '14-3/2': // gives {wrong}, truncation gives {right}   (-3 // 2 = {-3 // 2})")

    print("\n--- mistake 2 LIVE: int(a / b) loses precision past 2^53 ---")
    big = "0-123456789012345678901/7"
    wrong, right = calc_float_div(big), sol.calculate(big)
    ok = wrong != right and right == -(123456789012345678901 // 7)
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  {big}: float route {wrong}, integer route {right}")
    print("      (the LeetCode constraints keep values < 2^31, so int(a / b) passes there,")
    print("       but it is not a correct truncating division in general)")

    print("\n--- benchmark: n ≈ 300,000 characters ---")
    parts = [str(rng.randint(0, 999))]
    while sum(map(len, parts)) < 300_000:
        parts.append(rng.choice("+-*/"))
        parts.append(str(rng.randint(1, 999)))
    s = "".join(parts)
    for name, fn in (("stack       ", sol.calculate), ("O(1) space  ", calc_o1)):
        t0 = time.perf_counter(); r = fn(s); dt = time.perf_counter() - t0
        print(f"      {name} {dt * 1000:7.1f} ms")
    all_ok &= sol.calculate(s) == calc_o1(s)

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
