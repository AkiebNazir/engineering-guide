"""
================================================================================
SOLUTION · LeetCode 374 · Guess Number Higher or Lower                  [Easy]
https://leetcode.com/problems/guess-number-higher-or-lower/
================================================================================

THE CORE IDEA
--------------
`guess(num)` is a 3-way oracle (-1 / 0 / 1) instead of 003's boolean, but it
collapses to the exact same leftmost-True search (topic guide §1.6) once you
define the predicate as "have I gone far enough":

    f(mid) = (guess(mid) <= 0)     # True means "pick <= mid"

`guess(mid) == 1` means mid is too low (pick is higher) -> f(mid) is False.
`guess(mid) == -1` means mid is too high (pick is lower) -> f(mid) is True.
`guess(mid) == 0` means mid IS the pick -> f(mid) is True (and we're done).

    lo, hi = 1, n
    while lo < hi:
        mid = (lo + hi) // 2
        if guess(mid) <= 0:
            hi = mid              # pick is at or below mid
        else:
            lo = mid + 1          # pick is strictly above mid
    return lo                     # the picked number

Same template as 002 and 003, character for character — only the predicate
expression changed. Recognising that a 3-outcome oracle is still a boolean
predicate in disguise is the actual skill being tested.


================================================================================
AN ALTERNATIVE FRAMING: THREE-WAY BRANCHING (also correct, more literal)
================================================================================
You don't have to collapse to a single predicate — branching directly on the
three return values also works and may read more naturally:

    lo, hi = 1, n
    while lo <= hi:
        mid = (lo + hi) // 2
        r = guess(mid)
        if r == 0: return mid
        elif r == 1: lo = mid + 1      # pick is higher
        else: hi = mid - 1              # pick is lower

This is 001's exact-match template (`lo <= hi`, `hi = mid - 1`) instead of
002/003's leftmost-True template (`lo < hi`, `hi = mid`) — both are correct
here because the problem guarantees a pick exists in [1, n], so either
framing terminates with the right answer. The solution below uses the
leftmost-True form for consistency with 003, and the three-way form is kept
as an explicit alternative to make the equivalence concrete.


================================================================================
STEP BY STEP TRACE
================================================================================
n = 10, pick = 6

    lo=1  hi=10  mid=5   guess(5)=1 (too low)   -> lo = 6
    lo=6  hi=10  mid=8   guess(8)=-1 (too high)  -> hi = 8
    lo=6  hi=8   mid=7   guess(7)=-1 (too high)  -> hi = 7
    lo=6  hi=7   mid=6   guess(6)=0  (exact)     -> hi = 6   (0 <= 0, so hi=mid)
    lo=6  hi=6   loop ends -> return 6   ✓

    1  2  3  4  5 [6] 7  8  9  10
                  ^pick


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time      Space   Mutates input?  Note
    ---------------------------  --------  ------  ---------------  --------------------
    Linear scan (call 1..n)      O(n)      O(1)    no               correct, too many calls
    Binary search (leftmost) ✅  O(log n)  O(1)    no               minimizes guess() calls


================================================================================
EDGE CASES
================================================================================
    n == 1, pick == 1           -> lo == hi == 1 immediately, loop body never runs.
    pick == 1 (lowest possible)  -> every mid above 1 returns -1 (too high);
                                    hi shrinks all the way down to 1.
    pick == n (highest possible) -> every mid below n returns 1 (too low);
                                    lo grows all the way up to n.
    n huge (near 2^31 - 1)       -> Python's ints handle (lo+hi) with no
                                    overflow risk (topic guide §1.2b); still
                                    only ~31 iterations.


================================================================================
COMMON MISTAKES
================================================================================
1. Treating `guess(mid) <= 0` and `guess(mid) < 0` as interchangeable — they
   are NOT: `<= 0` correctly folds in the exact-match case (0) into "go left
   or stay", `< 0` would treat an exact match the same as "too low" and push
   `lo` past the answer, an off-by-one that returns the wrong number.
2. Mixing the leftmost-True template's loop/shrink pairing with the
   exact-match template's (e.g. `while lo < hi` combined with `hi = mid - 1`)
   — see topic guide §1.2 for why this either infinite-loops or skips the
   answer.
3. Calling `guess()` more than once per iteration (e.g. once for logging,
   once for the branch) — doubles the call count the problem is testing you
   to minimize.
4. Assuming `guess()`'s return convention without checking — some versions
   of this problem (and adjacent ones) flip the sign convention; always
   verify against the problem statement's exact examples before coding.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How is this different from problem 003 (First Bad Version)?
A: Mechanically identical after collapsing the 3-way oracle to a boolean
   predicate — see THE CORE IDEA above. The only real difference is the
   oracle's return type, not the search algorithm.

Q: What if guess() could be wrong occasionally (a noisy oracle)?
A: Standard binary search breaks — a single bad answer misdirects the whole
   search. This becomes "Guess Number Higher or Lower II" (LC 375, a
   different, DP-based problem) or, for a genuinely noisy channel, requires
   redundant queries / a randomized approach — worth naming as a real,
   different problem rather than a variant of this one.

Q: Can you avoid recomputing (lo + hi) // 2 as a potential trap in other
   languages?
A: Yes — `lo + (hi - lo) // 2` avoids any risk of `lo + hi` overflowing a
   fixed-width integer type in Java/C/Go. Not required in Python (topic
   guide §1.2b), but worth naming if the interviewer asks about porting.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 278  First Bad Version                — the boolean-oracle sibling (003)
    LC 375  Guess Number Higher or Lower II  — a different, DP/minimax problem,
                                                not a binary-search variant
    LC 704  Binary Search                    — the array-backed original (001)
================================================================================
"""

import sys
import time


def guess(num: int) -> int:
    raise NotImplementedError  # replaced per-test-case / per-demo below


class Solution:
    def guessNumber(self, n: int) -> int:
        """Leftmost-True binary search over the collapsed predicate
        guess(mid) <= 0. O(log n) calls, O(1) space. See THE CORE IDEA above."""
        lo, hi = 1, n
        while lo < hi:
            mid = (lo + hi) // 2
            if guess(mid) <= 0:
                hi = mid
            else:
                lo = mid + 1
        return lo

    def guessNumber_three_way(self, n: int) -> int:
        """The literal three-way-branch alternative (see ALTERNATIVE FRAMING
        above). Same asymptotics, different template shape (001's, not
        002/003's)."""
        lo, hi = 1, n
        while lo <= hi:
            mid = (lo + hi) // 2
            r = guess(mid)
            if r == 0:
                return mid
            elif r == 1:
                lo = mid + 1
            else:
                hi = mid - 1
        return -1  # not reached under this problem's guarantees


class CountingOracle:
    """Wraps the guess() convention and counts calls, for the runtime demo."""
    def __init__(self, pick: int):
        self.pick = pick
        self.calls = 0

    def __call__(self, num: int) -> int:
        self.calls += 1
        if num > self.pick:
            return -1
        if num < self.pick:
            return 1
        return 0


# ==============================================================================
# TESTS — run:  python 004_guess_number_higher_or_lower_solution.py
# ==============================================================================
CASES = [
    (10, 6),
    (1, 1),
    (2, 1),
    (2, 2),
    (2126753390, 1702766719),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    module = sys.modules[__name__]

    def install(pick):
        oracle = CountingOracle(pick)
        module.guess = oracle
        return oracle

    print("--- correctness ---")
    for n, pick in CASES:
        install(pick)
        got = sol.guessNumber(n)
        ok = got == pick
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n:<12} pick={pick:<12} -> {got}  (want {pick})")

    print("\n--- cross-check: leftmost-True template vs three-way-branch template ---")
    for n, pick in CASES:
        install(pick)
        a = sol.guessNumber(n)
        install(pick)
        b = sol.guessNumber_three_way(n)
        ok = a == b == pick
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n:<12} pick={pick:<12} leftmost={a} three_way={b}")

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: n=10, pick=6 ---")
    n, pick = 10, 6
    oracle = install(pick)
    lo, hi = 1, n
    print(f"  {'lo':>3} {'hi':>3} {'mid':>4} {'guess(mid)':>11}")
    while lo < hi:
        mid = (lo + hi) // 2
        r = oracle(mid)
        print(f"  {lo:>3} {hi:>3} {mid:>4} {r:>11}")
        if r <= 0:
            hi = mid
        else:
            lo = mid + 1
    print(f"  final lo == hi == {lo} -> picked number is {lo}")

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: call counts, binary search vs a linear guess-from-1 scan.
    # ----------------------------------------------------------------------
    print("\n--- guess() call count: binary search vs linear scan ---")
    print(f"  {'n':>12} {'pick':>12} {'binary calls':>13} {'linear calls':>13} {'ratio':>10}")
    for n, pick in ((100, 91), (100_000, 99_999), (2_126_753_390, 1_702_766_719)):
        oracle_bin = install(pick)
        sol.guessNumber(n)
        # linear scan from 1 upward must call guess() exactly `pick` times
        # (guess(1)..guess(pick-1) return 1, guess(pick) returns 0)
        lin_calls = pick
        ratio = lin_calls / oracle_bin.calls if oracle_bin.calls else float("inf")
        print(f"  {n:>12} {pick:>12} {oracle_bin.calls:>13} {lin_calls:>13} {ratio:>9.1f}x")
    print("  Same story as problem 003: binary search's call count tracks")
    print("  log(n), a linear guess-from-1 scan tracks pick itself — for a")
    print("  pick deep in a huge range the difference is enormous.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
