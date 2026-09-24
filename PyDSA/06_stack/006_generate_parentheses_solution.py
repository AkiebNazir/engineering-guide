"""
================================================================================
SOLUTION · LeetCode 22 · Generate Parentheses                          [Medium]
https://leetcode.com/problems/generate-parentheses/
================================================================================

THE CORE IDEA
--------------
Problem 001 validated a fixed string with a real stack; this problem
generates every valid string by backtracking, but the quantity being
tracked at each decision is exactly what a stack of a SINGLE bracket type
degenerates to: an integer depth, `open_count - close_count`. A '(' is
legal to place whenever you haven't used all n opens; a ')' is legal only
when it wouldn't underflow that depth below zero — i.e. only when there
are more opens already placed than closes so far.

    def backtrack(path, open_count, close_count):
        if len(path) == 2 * n:
            result.append(''.join(path))
            return
        if open_count < n:
            path.append('(')
            backtrack(path, open_count + 1, close_count)
            path.pop()
        if close_count < open_count:
            path.append(')')
            backtrack(path, open_count, close_count + 1)
            path.pop()

O(4^n / sqrt(n)) time (the n-th Catalan number of valid outputs dominates),
O(n) auxiliary space beyond the output itself (recursion depth).


================================================================================
THE STACK IS THE COUNTER — connecting this to problem 001
================================================================================
Problem 001's rule for validity was "never let the stack go empty when a
close bracket wants to pop it" — equivalently, "close_count must never
exceed open_count at any prefix." This problem enforces the SAME invariant
proactively, by construction, instead of checking it after the fact:

    problem 001 (VALIDATE):  push on '(', pop-and-fail on ')' if stack
                              is already empty
    problem 006 (GENERATE):  only ever CHOOSE to place ')' when doing so
                              keeps close_count < open_count — i.e. never
                              construct a string that problem 001 would
                              reject

Because every character placed is guarded by these two conditions, every
string that reaches length `2n` is automatically balanced — there is no
separate final validity check needed, unlike a brute-force generate-then-
filter approach (see below).


================================================================================
THE BRUTE FORCE, AND WHY THE GUARDS ARE STRICTLY BETTER
================================================================================
A brute-force approach generates ALL 2^(2n) binary strings of '(' and ')'
and filters with problem 001's validator:

    for each of the 2^(2n) length-2n strings over {'(', ')'}:
        if is_valid(s):   # problem 001's stack check
            result.append(s)

This is correct but wasteful — most of the 2^(2n) candidates are invalid
and get generated and thrown away. The backtracking version with the two
guards NEVER visits an invalid branch at all: `open_count < n` and
`close_count < open_count` prune the search tree to visit only
prefixes that could still become valid. The runtime demo below is a
correctness cross-check, not a scaling benchmark — the C(2n,n)/2^(2n)
"wasted fraction" of brute force grows the gap fast enough that even
small n makes the difference obvious.


================================================================================
STEP BY STEP TRACE
================================================================================
n = 2 (the decision tree, showing only branches that survive):

    path=""        open=0 close=0
      -> '(' legal (open<2)         path="("       open=1 close=0
           -> '(' legal (open<2)          path="(("      open=2 close=0
                -> '(' illegal (open==n)
                -> ')' legal (close<open)      path="(()"    open=2 close=1
                     -> ')' legal (close<open)      path="(())"   open=2 close=2
                          len==4 -> EMIT "(())"
           -> ')' legal (close<open)      path="()"      open=1 close=1
                -> '(' legal (open<2)          path="()("    open=2 close=1
                     -> ')' legal (close<open)      path="()()"   open=2 close=2
                          len==4 -> EMIT "()()"
                -> ')' illegal (close==open)

    n=2 results: ["(())", "()()"]   (2 = the 2nd Catalan number, C2)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time              Space   Mutates input?  Note
    -------------------------------------  ----------------  ------  ---------------  ----------------------
    Generate all 2^(2n), filter valid      O(2^(2n) * n)     O(n)    no               validates every
                                                                                        candidate, most wasted
    Backtrack with open/close guards ✅   O(4^n / sqrt(n))  O(n)    no               the answer — only
                                                                                        visits valid prefixes


================================================================================
EDGE CASES
================================================================================
    n = 1     -> ["()"] . The smallest legal case; exercises the base
                          case and both guards exactly once each.
    n = 8     -> the largest n allowed by constraints (2^16 = 1430
                          results, the 8th Catalan number) — a correctness
                          stress test more than a performance one, since
                          n is capped intentionally small (output size
                          grows exponentially).
    Every generated string has EXACTLY 2n characters, n opens and n
                          closes — verified structurally, not just by
                          spot-checking a few strings.
    No duplicate strings in the output — the backtracking tree explores
                          each valid sequence exactly once (there is no
                          path that produces the same string twice, since
                          the choice of '(' vs ')' at each position is a
                          distinct branch).


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting to `path.pop()` after each recursive call — this is the
   backtracking bug: without undoing the choice, the SAME list object
   keeps growing across sibling branches and later strings are corrupted
   (this is Python's classic mutable-shared-state trap, restated for a
   list used as a string builder instead of an array).

2. Using `close_count <= open_count` instead of strictly `<` — allowing a
   close when counts are EQUAL lets close_count exceed open_count,
   producing an invalid, unbalanced string (a literal stack underflow).

3. Checking `open_count <= n` instead of `open_count < n` — off-by-one
   that allows placing an (n+1)-th open bracket, producing strings longer
   than 2n opens' worth of balance, or overrunning the length check
   entirely depending on implementation.

4. Adding a separate `is_valid()` check at the base case "just to be
   safe" — unnecessary once the two guards are correct; every string that
   reaches length 2n through legal moves IS balanced by construction.
   (Not wrong to double-check, but wastes time restating the argument
   from scratch rather than trusting the invariant.)

5. Using string concatenation (`path + '('`) instead of a mutable list
   with append/pop (or f-strings only at the leaf) inside the recursion —
   works correctly, but each concatenation copies the whole string,
   turning an already-exponential algorithm needlessly slower by an
   extra linear factor per node.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you generate them in a different order (e.g. lexicographic)?
A: Trying '(' before ')' at every branch (as above) already produces
   lexicographic order for this alphabet, since '(' < ')' in ASCII and the
   DFS naturally explores the '(' branch fully before the ')' branch.

Q: How would you count the number of valid combinations WITHOUT generating
   them?
A: The n-th Catalan number, `C(2n, n) / (n + 1)`, computable directly with
   no recursion at all — O(n) time via a factorial-based formula (or O(n)
   via the DP recurrence `C_0=1, C_{n+1} = sum(C_i * C_{n-i})`).

Q: How would you generate valid combinations with MULTIPLE bracket types
   (e.g. '()[]{}')? Would you still use just two counters?
A: No — with multiple bracket types you need the ORDER of currently-open
   brackets, not just a count, so an explicit list-based stack (like
   problem 001's) becomes necessary again: push the specific bracket type
   opened, and only allow closing the type currently on top.

Q: What's the actual asymptotic bound, and why "4^n / sqrt(n)"?
A: The n-th Catalan number is `C(2n,n)/(n+1)`, which is Θ(4^n / n^1.5) by
   Stirling's approximation; since building each string also costs O(n),
   total work is Θ(4^n / sqrt(n)). This is a standard fact worth citing
   rather than re-deriving under time pressure.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 20   Valid Parentheses           — problem 001 here: the validator
                                          this problem's guards are built
                                          to satisfy by construction
    LC 301  Remove Invalid Parentheses  — repair an invalid string with
                                          the minimum removals, BFS/DFS +
                                          the same balance-counting idea
    LC 32   Longest Valid Parentheses   — stack of indices tracking the
                                          longest balanced run
================================================================================
"""

import time
from typing import List


class Solution:
    def generateParenthesis(self, n: int) -> List[str]:
        """Backtracking with open/close counters as an implicit stack
        depth. O(4^n / sqrt(n)) time, O(n) auxiliary space.
        The answer. See THE CORE IDEA above."""
        result: List[str] = []
        path: List[str] = []

        def backtrack(open_count: int, close_count: int) -> None:
            if len(path) == 2 * n:
                result.append(''.join(path))
                return
            if open_count < n:
                path.append('(')
                backtrack(open_count + 1, close_count)
                path.pop()
            if close_count < open_count:
                path.append(')')
                backtrack(open_count, close_count + 1)
                path.pop()

        backtrack(0, 0)
        return result

    # ------------------------------------------------------------------
    # Alternatives / oracles.
    # ------------------------------------------------------------------
    @staticmethod
    def _is_valid(s: str) -> bool:
        """Problem 001's validator, reused as the brute-force filter."""
        depth = 0
        for c in s:
            depth += 1 if c == '(' else -1
            if depth < 0:
                return False
        return depth == 0

    def generateParenthesis_brute(self, n: int) -> List[str]:
        """O(2^(2n) * n) reference: generate ALL binary strings over
        {'(',')'} of length 2n, filter with problem 001's validator. Only
        usable for small n."""
        from itertools import product
        result = []
        for combo in product('()', repeat=2 * n):
            s = ''.join(combo)
            if self._is_valid(s):
                result.append(s)
        return result


# ==============================================================================
# TESTS — run:  python 006_generate_parentheses_solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: backtracking vs brute-force generate-and-filter ---")
    catalan = [1, 2, 5, 14, 42]   # C1..C5
    for n in (1, 2, 3, 4, 5):
        got = sol.generateParenthesis(n)
        want = sol.generateParenthesis_brute(n) if n <= 5 else None
        expected_count = catalan[n - 1]
        all_valid = all(sol._is_valid(s) and len(s) == 2 * n for s in got)
        all_unique = len(set(got)) == len(got)
        matches_brute = (sorted(got) == sorted(want)) if want is not None else True
        ok = len(got) == expected_count and all_valid and all_unique and matches_brute
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n}  count={len(got):<5} (want {expected_count})"
              f"  all_valid={all_valid}  all_unique={all_unique}  matches_brute={matches_brute}")

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: n = 2, full decision tree ---")
    n = 2
    path: List[str] = []

    def backtrack_trace(open_count, close_count, depth=0):
        indent = "  " * depth
        if len(path) == 2 * n:
            print(f"{indent}EMIT {''.join(path)!r}")
            return
        if open_count < n:
            path.append('(')
            print(f"{indent}try '(' -> path={''.join(path)!r}")
            backtrack_trace(open_count + 1, close_count, depth + 1)
            path.pop()
        if close_count < open_count:
            path.append(')')
            print(f"{indent}try ')' -> path={''.join(path)!r}")
            backtrack_trace(open_count, close_count + 1, depth + 1)
            path.pop()

    backtrack_trace(0, 0)

    # ----------------------------------------------------------------------
    # Backtracking pruning vs brute force generate-then-filter: measured.
    # ----------------------------------------------------------------------
    print("\n--- pruned backtracking vs generate-2^(2n)-then-filter: measured runtime ---")
    print(f"  {'n':>4} {'output size':>12} {'backtrack':>12} {'brute filter':>14} {'ratio':>8}")
    for n in (6, 8, 10):
        t0 = time.perf_counter()
        out = sol.generateParenthesis(n)
        t1 = time.perf_counter()
        out_brute = sol.generateParenthesis_brute(n)
        t2 = time.perf_counter()
        bt_ms = (t1 - t0) * 1000
        br_ms = (t2 - t1) * 1000
        ratio = br_ms / bt_ms if bt_ms > 0 else float("inf")
        assert sorted(out) == sorted(out_brute)
        print(f"  {n:>4} {len(out):>12} {bt_ms:>10.2f}ms {br_ms:>12.2f}ms {ratio:>7.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
