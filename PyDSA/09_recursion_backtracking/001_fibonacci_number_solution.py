"""
================================================================================
SOLUTION · LeetCode 509 · Fibonacci Number                               [Easy]
https://leetcode.com/problems/fibonacci-number/
================================================================================

THE CORE IDEA
--------------
Naive recursion recomputes the same subproblem exponentially many times because
the call TREE has massive overlap that a plain function call cannot see across
branches. Memoization caches each result the first time it is computed, turning
every later call for the same input into an O(1) lookup — collapsing the
exponential call tree into a linear number of DISTINCT subproblems solved once
each. This file measures both, with actual call counts, not assertions.

    naive:     fib(n) = fib(n-1) + fib(n-2), no memory        -> O(2^n) calls
    memoized:  same recursion, but check/populate a cache      -> O(n) calls
    iterative: no recursion, two rolling variables              -> O(n), O(1) space


================================================================================
MULTIPLE APPROACHES
================================================================================
1. NAIVE RECURSION — O(2^n) time, O(n) space (call stack). Priced, not the
   answer: correct but the call count explodes past n ~ 35 into seconds.
2. MEMOIZED (TOP-DOWN) — O(n) time, O(n) space (cache + stack). The direct fix.
3. ITERATIVE / TABULATION (BOTTOM-UP) — O(n) time, O(n) space for a full array,
   or O(1) with two rolling variables since only the last two values are ever
   needed. This is the one to actually write in an interview.
4. MATRIX EXPONENTIATION / Binet's FORMULA — O(log n) time. Priced for
   completeness (a real follow-up answer), not needed for n <= 30.


================================================================================
STEP BY STEP TRACE — memoized fib(5)
================================================================================
    call fib(5)
      memo miss -> need fib(4) + fib(3)
      call fib(4)
        memo miss -> need fib(3) + fib(2)
        call fib(3)
          memo miss -> need fib(2) + fib(1)
          call fib(2)
            memo miss -> need fib(1) + fib(0)
            call fib(1) -> base case, return 1, memo[1] = 1
            call fib(0) -> base case, return 0, memo[0] = 0
          fib(2) = 1, memo[2] = 1
          call fib(1) -> memo HIT, return 1 instantly, no further recursion
        fib(3) = 2, memo[3] = 2
        call fib(2) -> memo HIT, return 1 instantly
      fib(4) = 3, memo[4] = 3
      call fib(3) -> memo HIT, return 2 instantly
    fib(5) = 5

Every distinct n is computed exactly once; every repeat request is a dict
lookup, not a re-descent into the tree. Compare this to the naive trace in the
question file's docstring, where fib(3) and fib(2) are each recomputed from
scratch.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time      Space         Mutates input?  Note
    ---------------------------  --------  -------------  ---------------  ----------------------------
    Naive recursion              O(2^n)    O(n) stack     no               priced, not written for n>30
    Memoized (top-down)          O(n)      O(n)           no               cache + call stack
    Iterative array (bottom-up)  O(n)      O(n)           no               same numbers, no recursion
    Iterative rolling (2 vars)   O(n)      O(1)            no               the answer to write
    Matrix exponentiation        O(log n)  O(1)            no               follow-up, not needed here

    WHERE O(2^n) comes from: let T(n) = calls to compute fib(n). T(n) =
    T(n-1) + T(n-1) + O(1). Solving this recurrence gives T(n) = O(phi^n),
    phi ~ 1.618 (the golden ratio) — commonly rounded up to "O(2^n)" since
    phi < 2 and the loose bound is what interviewers expect you to say, with
    the tighter phi^n as the precise follow-up answer.


================================================================================
EDGE CASES
================================================================================
    n = 0     -> 0    base case; anything that assumes n >= 1 up front breaks.
    n = 1     -> 1    the other base case; F(1) = 1, not F(1) = F(0) + F(-1).
    n = 30    -> 832040   the constraint's upper bound; naive recursion is
                          still fast enough here (~2.7M calls), but the demo
                          below shows it is already visibly slower than the
                          memoized/iterative versions at this size.


================================================================================
COMMON MISTAKES
================================================================================
1. Off-by-one on the base cases — treating F(0) = F(1) = 1 (both 1) instead of
   F(0) = 0, F(1) = 1. Shifts every subsequent value by one index.
2. Memoizing but keying the cache incorrectly across multiple calls to `fib`
   from a class instance — e.g. resetting `self.memo = {}` inside every call,
   which defeats memoization's entire purpose (still O(2^n) across a SINGLE
   top-level call, since the cache never survives past the first branch that
   populates it... actually it does survive within one call if declared
   outside the recursive helper. The bug is declaring the cache INSIDE the
   recursive function itself, so it resets on every call).
3. Using naive recursion for a large `n` in a context where it will actually
   be called many times (e.g. as a subroutine in a loop) — the constraint here
   caps n at 30, but this reasoning does not generalize past that bound.
4. Reaching for recursion at all in an interview when O(1) space, no stack,
   two-variable iteration solves it just as easily — always mention the
   iterative version even if the interviewer initially asked for "recursive."
5. Forgetting that this is NOT a decision tree / backtracking problem, and
   trying to apply choose/explore/unchoose machinery to something that is a
   single computed value per input, with no leaves to collect.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Compute fib(n) for very large n (billions) — can you beat O(n)?
A: Matrix exponentiation: [[1,1],[1,0]]^n gives F(n) via fast exponentiation by
   squaring, O(log n) time. Priced above, implemented below for completeness.

Q: What if you need F(0..n), the whole sequence, not just F(n)?
A: Bottom-up array (or even just print while rolling two variables) is exactly
   as fast as memoized top-down and avoids recursion depth entirely — the
   natural choice when you need every value anyway.

Q: Why does memoization work here but NOT for problems like Subsets (topic 09
   problem 002)?
A: Memoization exploits OVERLAPPING subproblems reachable via different paths
   (fib(2) is needed by both the fib(4) and fib(3) branches). Subsets/
   permutations/combinations build a DISTINCT partial path at every node — no
   two nodes represent "the same subproblem," so there is nothing to cache.
   This is the exact fork in the topic guide's Part 6 decision tree.

Q: What is the recursion depth of the naive version, and could it stack
   overflow?
A: O(n) depth — one frame per level down the LEFT spine (fib(n-1) branch) at
   any moment. For n <= 30 this is trivial; Python's default recursion limit
   (1000) would only become relevant far beyond this problem's constraints.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 70   Climbing Stairs                — identical recurrence, different
                                             story (f(n) = f(n-1) + f(n-2))
    LC 1137 N-th Tribonacci Number         — same idea, three terms instead
                                             of two
    LC 322  Coin Change                    — the next step: memoization over
                                             a recurrence with CHOICES (topic
                                             16/17 territory)
    LC 62   Unique Paths                   — 2D version of the same
                                             overlapping-subproblem structure
================================================================================
"""

import time
from functools import lru_cache


class Solution:
    def fib(self, n: int) -> int:
        """Iterative, two rolling variables. O(n) time, O(1) space.
        The version to actually write."""
        if n < 2:
            return n
        a, b = 0, 1                       # F(0), F(1)
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def fib_naive_recursive(self, n: int) -> int:
        """The textbook recursive translation. Correct, O(2^n) (really
        O(phi^n)) calls — DO NOT call this with large n in a loop."""
        if n < 2:
            return n
        return self.fib_naive_recursive(n - 1) + self.fib_naive_recursive(n - 2)

    def fib_memoized(self, n: int, memo: dict | None = None) -> int:
        """Top-down memoization: same recursion, cache checked first.
        O(n) time, O(n) space (cache is declared OUTSIDE the recursive
        step — see Common Mistake #2)."""
        if memo is None:
            memo = {}
        if n < 2:
            return n
        if n in memo:
            return memo[n]
        memo[n] = self.fib_memoized(n - 1, memo) + self.fib_memoized(n - 2, memo)
        return memo[n]

    @lru_cache(maxsize=None)
    def fib_lru_cache(self, n: int) -> int:
        """Same idea as fib_memoized, using the stdlib's cache decorator."""
        if n < 2:
            return n
        return self.fib_lru_cache(n - 1) + self.fib_lru_cache(n - 2)

    def fib_bottom_up_array(self, n: int) -> int:
        """Tabulation: build F(0..n) in a loop, no recursion at all.
        O(n) time, O(n) space — the array is kept for clarity/debugging;
        fib() above drops it to O(1) since only the last two matter."""
        if n < 2:
            return n
        dp = [0] * (n + 1)
        dp[1] = 1
        for i in range(2, n + 1):
            dp[i] = dp[i - 1] + dp[i - 2]
        return dp[n]

    def fib_matrix_power(self, n: int) -> int:
        """O(log n) via fast matrix exponentiation of [[1,1],[1,0]].
        Follow-up answer for very large n; not needed for n <= 30."""
        if n < 2:
            return n

        def mat_mult(A, B):
            return [
                [A[0][0] * B[0][0] + A[0][1] * B[1][0],
                 A[0][0] * B[0][1] + A[0][1] * B[1][1]],
                [A[1][0] * B[0][0] + A[1][1] * B[1][0],
                 A[1][0] * B[0][1] + A[1][1] * B[1][1]],
            ]

        def mat_pow(M, p):
            result = [[1, 0], [0, 1]]     # identity
            base = M
            while p:
                if p & 1:
                    result = mat_mult(result, base)
                base = mat_mult(base, base)
                p >>= 1
            return result

        M = mat_pow([[1, 1], [1, 0]], n)
        return M[0][1]


# ==============================================================================
# TESTS — run:  python 001_fibonacci_number_solution.py
# ==============================================================================
CASES = [
    (0, 0), (1, 1), (2, 1), (3, 2), (4, 3), (5, 5), (6, 8), (7, 13),
    (10, 55), (15, 610), (20, 6765), (25, 75025), (30, 832040),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    impls = [
        ("iterative rolling ", sol.fib),
        ("naive recursive    ", sol.fib_naive_recursive),
        ("memoized top-down  ", lambda n: sol.fib_memoized(n)),
        ("lru_cache          ", sol.fib_lru_cache),
        ("bottom-up array    ", sol.fib_bottom_up_array),
        ("matrix power       ", sol.fib_matrix_power),
    ]

    for name, fn in impls:
        ok = all(fn(n) == expected for n, expected in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # ----------------------------------------------------------------------
    # The call-count explosion, MEASURED — not asserted.
    # ----------------------------------------------------------------------
    print("\n--- naive recursion's call count, measured live ---")

    def fib_counted(n, counter):
        counter[0] += 1
        if n < 2:
            return n
        return fib_counted(n - 1, counter) + fib_counted(n - 2, counter)

    def fib_memo_counted(n, memo, counter):
        counter[0] += 1
        if n < 2:
            return n
        if n in memo:
            return memo[n]
        memo[n] = fib_memo_counted(n - 1, memo, counter) + fib_memo_counted(n - 2, memo, counter)
        return memo[n]

    print(f"  {'n':>3} {'naive calls':>13} {'memoized calls':>15} {'ratio':>10}")
    for n in (5, 10, 15, 20, 25, 30):
        c1 = [0]
        fib_counted(n, c1)
        c2 = [0]
        fib_memo_counted(n, {}, c2)
        ratio = c1[0] / c2[0]
        print(f"  {n:>3} {c1[0]:>13,} {c2[0]:>15,} {ratio:>9.1f}x")
    print("  Naive calls roughly DOUBLE per +1 in n (O(phi^n) ~ O(2^n));")
    print("  memoized calls grow LINEARLY (each distinct n computed once, 2n-1 calls).")

    # ----------------------------------------------------------------------
    # Real wall-clock time, naive vs memoized vs iterative.
    # ----------------------------------------------------------------------
    print("\n--- measured wall-clock time ---")
    print(f"  {'n':>3} {'naive (ms)':>12} {'memoized (ms)':>14} {'iterative (ms)':>15}")
    for n in (20, 25, 30, 32):
        t0 = time.perf_counter()
        sol.fib_naive_recursive(n)
        t1 = time.perf_counter()
        sol.fib_memoized(n)
        t2 = time.perf_counter()
        sol.fib(n)
        t3 = time.perf_counter()
        print(f"  {n:>3} {(t1 - t0) * 1000:>10.2f}ms {(t2 - t1) * 1000:>12.4f}ms "
              f"{(t3 - t2) * 1000:>13.5f}ms")
    print("  The naive version visibly slows down as n grows past ~25-30; the")
    print("  memoized and iterative versions stay essentially instantaneous.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
