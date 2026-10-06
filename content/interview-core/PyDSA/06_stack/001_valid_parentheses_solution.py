"""
================================================================================
SOLUTION · LeetCode 20 · Valid Parentheses                               [Easy]
https://leetcode.com/problems/valid-parentheses/
================================================================================

THE CORE IDEA
--------------
A close bracket is valid only if it matches the bracket MOST RECENTLY still
open — that is a stack's defining property, "last in, first out." Push every
open bracket; on every close bracket, check it against the top of the stack
and pop if it matches, otherwise the string is immediately invalid.

    pairs = {')': '(', ']': '[', '}': '{'}
    stack = []
    for c in s:
        if c in pairs:                       # a CLOSE bracket
            if not stack or stack[-1] != pairs[c]:
                return False
            stack.pop()
        else:                                 # an OPEN bracket
            stack.append(c)
    return not stack                          # valid iff nothing left open

O(n) time, O(n) space.


================================================================================
WHY COUNTING ALONE FAILS — "([)]"
================================================================================
"([)]" has exactly two opens and two closes of each type — a naive
"count opens minus count closes" check would call it balanced. It is not:
the ')' arrives while '[' is the most recently opened bracket, and ')' does
not close a '['. Order, not count, is the actual constraint — which is
exactly what the stack enforces and a running counter cannot.


================================================================================
THE TWO WAYS A CLOSE BRACKET CAN FAIL
================================================================================
1. The stack is EMPTY — a close bracket with no open bracket at all waiting
   for it (e.g. the lone string ")").
2. The stack's top is the WRONG open bracket — the close doesn't match the
   most recent open (e.g. "(]": '(' is open, ']' wants '[').

Both must return False immediately; do not let either case fall through to
a `pop()` on an empty list, which raises IndexError rather than failing
cleanly. `if not stack or stack[-1] != pairs[c]:` guards both in one
short-circuited check — `not stack` is evaluated first, so `stack[-1]` is
never reached when the stack is empty.


================================================================================
FINAL CHECK — leftover opens
================================================================================
A string of all opens, e.g. "(((", never triggers a False return during the
loop — nothing ever fails to match, because nothing ever gets checked. It is
still invalid: every '(' is unclosed. The loop alone is not sufficient; the
function must also verify the stack is EMPTY at the end. This is the most
common one-line omission in a first attempt at this problem.


================================================================================
STEP BY STEP TRACE
================================================================================
s = "{[()]}"

    i  c    action                          stack (after)
    -  -    ------                          -------------
    0  {    open, push                      ['{']
    1  [    open, push                      ['{', '[']
    2  (    open, push                      ['{', '[', '(']
    3  )    close, top='(' matches -> pop    ['{', '[']
    4  ]    close, top='[' matches -> pop    ['{']
    5  }    close, top='{' matches -> pop    []

    end: stack is empty -> valid = True

s = "([)]"  (the classic trap)

    i  c    action                          stack (after)
    -  -    ------                          -------------
    0  (    open, push                      ['(']
    1  [    open, push                      ['(', '[']
    2  )    close, top='[' , pairs[')']='(' -> MISMATCH -> return False immediately


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time    Space   Mutates input?  Note
    ---------------------------------  ------  ------  ---------------  ----------------------
    Repeated string replacement        O(n^2)  O(n)    no               replace "()","[]","{}"
                                                                          with "" until stable
    Count opens/closes only            O(n)    O(1)    no               ✗ WRONG — ignores order
    Stack, push/pop/match ✅           O(n)    O(n)    no               the answer


================================================================================
EDGE CASES
================================================================================
    ""                    -> True    Vacuously valid — no unmatched bracket
                                      exists in an empty string.
    "("                   -> False   Unclosed open; caught by the final
                                      "stack must be empty" check, not the
                                      loop itself.
    ")"                   -> False   Close with nothing open; caught by the
                                      "stack is empty" branch of the failure
                                      check inside the loop.
    "([)]"                -> False   The canonical order trap — count-balanced,
                                      order-broken. See above.
    "(((((((((())))))))))" -> True   Deep nesting; the stack must hold up to
                                      n/2 entries at its peak — confirms
                                      O(n) space is actually used, not just
                                      theoretically possible.
    All six bracket types mixed -> exercises every entry of `pairs`.


================================================================================
COMMON MISTAKES
================================================================================
1. Checking count of '(' vs count of ')' (and similarly for the other pairs)
   instead of order. Fails on "([)]" and every order-scrambled string.

2. Calling `stack.pop()` or reading `stack[-1]` before checking `not stack`,
   raising IndexError on a close bracket that arrives with nothing open.
   Always check emptiness FIRST, short-circuited before the index access.

3. Forgetting the final `return not stack` and returning `True` as soon as
   the loop finishes without error — misses unclosed opens like "(((".

4. Building the open/close mapping backwards (`{'(' : ')'}` instead of
   `{')' : '('}`) and then comparing the wrong things — decide once whether
   you are mapping open->close or close->open and stay consistent.

5. Treating any non-bracket character as an error instead of the problem's
   actual guarantee (only bracket characters appear) — unnecessary
   defensive code that isn't wrong here, but wastes time under pressure if
   it isn't asked for.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if the string could ALSO contain other characters (letters, digits)
   that should be ignored?
A: Skip any character not in the open/close vocabulary — `continue` before
   the push/close logic. Still O(n).

Q: Can you do it in O(1) space?
A: Not in general — the stack can legitimately need to hold up to n/2
   entries (all opens, e.g. "((((("). O(n) space is the accepted answer;
   it's proportional to the maximum nesting depth, not always n, but n/2
   nesting depth is achievable and that is already Θ(n).

Q: What if you needed to report WHERE the first invalid bracket is, not
   just true/false?
A: Track the index alongside each pushed bracket (`stack.append((c, i))`),
   and return that index at the point of mismatch instead of False.

Q: How would you extend this to validate HTML/XML tags instead of brackets?
A: Same stack idea — push opening tags, and on a closing tag check it
   matches the top of the stack; the "pairs" map becomes tag-name equality
   instead of a fixed six-character table.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 22   Generate Parentheses          — problem 006 here: same nesting
                                            structure, generated instead of
                                            validated
    LC 32   Longest Valid Parentheses     — stack of INDICES, tracks length
                                            of longest valid run
    LC 1249 Minimum Remove to Make Valid
            Parentheses                   — stack tracks indices to delete
    LC 921  Minimum Add to Make Parentheses Valid — counting variant, no
                                            explicit stack needed
================================================================================
"""

import random
import time


class Solution:
    def isValid(self, s: str) -> bool:
        """Stack, push opens / match-and-pop closes. O(n) time, O(n) space.
        The answer. See THE CORE IDEA above."""
        pairs = {')': '(', ']': '[', '}': '{'}
        stack = []
        for c in s:
            if c in pairs:
                if not stack or stack[-1] != pairs[c]:
                    return False
                stack.pop()
            else:
                stack.append(c)
        return not stack

    # ------------------------------------------------------------------
    # Alternatives / oracles.
    # ------------------------------------------------------------------
    def isValid_replace(self, s: str) -> bool:
        """O(n^2) reference: repeatedly strip "()", "[]", "{}" until the
        string stops changing or is empty. Correct but quadratic."""
        prev = None
        while prev != s:
            prev = s
            s = s.replace("()", "").replace("[]", "").replace("{}", "")
        return s == ""

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def isValid_count_only(self, s: str) -> bool:
        """✗ BROKEN ON PURPOSE — counts opens vs closes per type, ignoring
        ORDER entirely. Passes "([)]" incorrectly."""
        counts = {'(': 0, '[': 0, '{': 0}
        closers = {')': '(', ']': '[', '}': '{'}
        for c in s:
            if c in counts:
                counts[c] += 1
            elif c in closers:
                counts[closers[c]] -= 1
        return all(v == 0 for v in counts.values())


# ==============================================================================
# TESTS — run:  python 001_valid_parentheses_solution.py
# ==============================================================================
CASES = [
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
    ("(((((((((())))))))))", True),
    ("((()", False),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: stack vs O(n^2) repeated-replace oracle ---")
    for text, expected in CASES:
        want = sol.isValid_replace(text)
        got = sol.isValid(text)
        ok = got == expected and want == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  s={text!r:<24} -> {got}  (want {expected})")

    # ----------------------------------------------------------------------
    # ⚠️  The count-only trap, demonstrated live.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  count-balanced vs order-correct: the '([)]' trap ---")
    trap_cases = ["([)]", "(]", "]}[{", "(]}["]
    trap_reproduced = False
    for text in trap_cases:
        correct = sol.isValid(text)
        broken = sol.isValid_count_only(text)
        mismatch = correct != broken
        trap_reproduced |= mismatch
        print(f"  s={text!r:<10} correct={correct!s:<6} count_only={broken!s:<6}  "
              f"{'<- MISMATCH, count-only wrongly says valid' if mismatch else ''}")
    print(f"  trap reproduced: {trap_reproduced}")
    all_ok &= trap_reproduced

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: s = '{[()]}' ---")
    pairs = {')': '(', ']': '[', '}': '{'}
    stack = []
    for i, c in enumerate("{[()]}"):
        if c in pairs:
            matched = bool(stack) and stack[-1] == pairs[c]
            if matched:
                stack.pop()
            print(f"  i={i} c={c!r}  close, {'matches, pop' if matched else 'MISMATCH'}"
                  f"  stack: {stack}")
        else:
            stack.append(c)
            print(f"  i={i} c={c!r}  open, push              stack: {stack}")
    print(f"  final stack empty: {not stack} -> valid = {not stack}")

    # ----------------------------------------------------------------------
    # Randomised cross-check vs the O(n^2) oracle.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n^2) replace oracle ---")
    random.seed(6)
    chars = "()[]{}"
    trials, mismatches = 5000, 0
    for _ in range(trials):
        n = random.randint(0, 12)
        s = "".join(random.choice(chars) for _ in range(n))
        if sol.isValid(s) != sol.isValid_replace(s):
            mismatches += 1
    print(f"  {trials} random strings (len 0-12, chars '()[]{{}}'): {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # O(n) stack vs O(n^2) repeated-replace: measured runtime.
    # ----------------------------------------------------------------------
    print("\n--- O(n) stack vs O(n^2) repeated-replace: measured runtime ---")
    print(f"  {'n':>7} {'stack O(n)':>12} {'replace O(n^2)':>16} {'ratio':>8}")
    for n in (2_000, 4_000, 8_000):
        s = "(" * (n // 2) + ")" * (n // 2)   # worst case: deep nesting, replace peels one layer at a time
        t0 = time.perf_counter(); sol.isValid(s)
        t1 = time.perf_counter(); sol.isValid_replace(s)
        t2 = time.perf_counter()
        st_ms = (t1 - t0) * 1000
        rp_ms = (t2 - t1) * 1000
        ratio = rp_ms / st_ms if st_ms > 0 else float("inf")
        print(f"  {n:>7} {st_ms:>10.2f}ms {rp_ms:>14.2f}ms {ratio:>7.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
