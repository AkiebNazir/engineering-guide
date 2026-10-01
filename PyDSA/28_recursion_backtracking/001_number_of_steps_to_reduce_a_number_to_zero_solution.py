"""
================================================================================
SOLUTION · LeetCode 1342 · Number of Steps to Reduce a Number to Zero     [Easy]
https://leetcode.com/problems/number-of-steps-to-reduce-a-number-to-zero/
================================================================================

THE CORE IDEA
--------------
Simulate the rule directly, recursively: even numbers get halved, odd numbers
get decremented, and each recursive call answers "how many steps for what's
left," to which the current call adds 1 for the step it just took. The base
case is `num == 0`, needing 0 more steps. This is the smallest possible
recursion shape — one call, one base case, one accumulator (+1 per level) —
and it is here specifically to build that shape before anything harder is
layered on top.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. NAIVE "SUBTRACT-ONLY" RECURSION — always do `num - 1`, ignoring the /2
   rule entirely. Priced, not written: O(num) calls and O(num) stack depth.
   For num = 10**6 this blows Python's default recursion limit (~1000) long
   before finishing — demonstrated live in the tests below with a real
   RecursionError.
2. RECURSIVE, FOLLOWING THE ACTUAL RULE (even -> //2, odd -> -1) — O(log num)
   time, O(log num) space (call stack). The intended answer for this topic.
3. ITERATIVE TWIN — identical logic, a `while` loop and a counter instead of
   a call stack. O(log num) time, O(1) space. The version to actually write
   in an interview once you've shown you can reason about it recursively.
4. BIT-TRICK O(1)-ish — the number of steps equals
   `num.bit_length() - 1 + bin(num).count('1')` for num > 0 (one halving per
   bit position, plus one extra subtraction for every 1-bit, since a 1-bit
   forces an odd number at that point in the halving chain, needing an extra
   "-1" step before the next halve). Priced as a follow-up curiosity, not the
   point of this recursion-topic file.


================================================================================
STEP BY STEP TRACE — steps(14)
================================================================================
    call steps(14)               14 even -> 14 // 2 = 7,  need 1 + steps(7)
      call steps(7)               7 odd  -> 7 - 1 = 6,    need 1 + steps(6)
        call steps(6)             6 even -> 6 // 2 = 3,   need 1 + steps(3)
          call steps(3)           3 odd  -> 3 - 1 = 2,    need 1 + steps(2)
            call steps(2)         2 even -> 2 // 2 = 1,   need 1 + steps(1)
              call steps(1)       1 odd  -> 1 - 1 = 0,    need 1 + steps(0)
                call steps(0) -> base case, return 0
              steps(1) = 1 + 0 = 1
            steps(2) = 1 + 1 = 2
          steps(3) = 1 + 2 = 3
        steps(6) = 1 + 3 = 4
      steps(7) = 1 + 4 = 5
    steps(14) = 1 + 5 = 6

Six frames deep, six steps returned — depth and answer coincide exactly,
because every single recursive call corresponds to exactly one step of the
simulation (unlike a "search on the answer" recursion where depth and the
final count can diverge).


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time         Space          Mutates input?  Note
    ----------------------------  -----------  -------------  ---------------  --------------------------------
    Naive subtract-only recursion O(num)       O(num) stack   no               priced only; crashes for num~10^6
    Recursive (follow the rule)   O(log num)   O(log num)     no               depth == answer, the taught approach
    Iterative twin                O(log num)   O(1)           no               same logic, no call stack
    Bit-trick                     O(log num)*  O(1)           no               *bit_length()/count('1') are O(log num)
                                                                                internally; still no Python-level loop

    WHY THE RULE-FOLLOWING VERSION IS O(log num): a halving step appears at
    least every other step in the worst case (an odd number is always
    followed immediately by an even one, since n-1 is even when n is odd),
    so the number of halvings alone is O(log num), and each halving is
    interleaved with at most one subtraction — total steps stay O(log num).


================================================================================
EDGE CASES
================================================================================
    num = 0        -> 0   already at the base case; no steps taken at all.
    num = 1         -> 1   the smallest positive case: 1 is odd, 1 - 1 = 0,
                           one step. Confirms the base case triggers correctly
                           one level up, not that num == 0 was assumed at the
                           top.
    num = power of 2 (e.g. 8) -> pure halving chain, no subtractions needed
                           until the final 1 -> 0 step (every power of two is
                           even until it reaches 1, which is odd).
    num = 10**6      -> upper constraint bound; exercises real recursion
                           depth (~25) with the rule-following version, and is
                           exactly the case that overflows the naive
                           subtract-only version's stack — demonstrated below.


================================================================================
COMMON MISTAKES
================================================================================
1. Checking `num % 2 == 0` with `num` already mutated by a previous branch of
   an unrelated computation (not an issue here since `num` is a plain int
   parameter, but the general trap: always recurse on a NEW value, never
   assume a shared mutable variable reflects "the current num" — ints are
   immutable in Python so this specific bug can't happen here, but it is the
   #1 bug source in the linked-list problems later in this folder).
2. Forgetting the "+1" for the step just taken and returning `steps(n // 2)`
   directly — this silently undercounts every case that isn't already at the
   base case.
3. Using `num / 2` (float division) instead of `num // 2` (integer division)
   — this returns a float, and the very next call's `% 2` check on a float
   either misbehaves or the recursion never reaches the exact base case
   `num == 0` (it degrades toward `0.0`, which does equal `0` in Python, but
   relying on float/int equality by accident is fragile and not what the
   problem intends).
4. Writing the naive "always subtract 1" version out of habit (it's the
   simplest possible reading of "in one step... otherwise subtract 1") and
   not noticing it silently ignores the even/halve rule — this is still
   "correct" in the sense that many small test cases pass, but it's
   answering a different (much slower) problem; the recursion depth blowup
   at num ~ 10**6 is the tell, shown live below.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you do this without recursion at all?
A: Yes — the iterative twin below is a direct loop translation, O(log num)
   time, O(1) space, and is what most interviewers actually want to see
   written once the recursive idea has been explained.

Q: Can you do it in O(1) without any loop or recursion?
A: Close: `num.bit_length() - 1 + bin(num).count('1')` for num > 0 (0 for
   num == 0). `bit_length()` and `count('1')` are themselves O(log num)
   internally in CPython, so this isn't truly O(1), but it involves zero
   Python-level iteration.

Q: What's the recursion depth here, and is there any risk of RecursionError?
A: Depth is O(log num) with the rule-following recursion — at most ~40 for
   num up to 10**6. No risk. Contrast with the naive subtract-only version,
   whose depth is O(num) and DOES hit RecursionError well before num = 10**6,
   demonstrated live in the tests.

Q: Why does this problem belong before Reverse String (002) in the ladder if
   both are "easy"?
A: This one recurses on a shrinking NUMBER via arithmetic (halve/subtract) —
   the most direct possible mapping from problem statement to recursive
   step. 002 introduces recursing on an INDEX RANGE into a fixed-size
   structure instead, which is a different (and slightly less obvious) way
   to make progress toward a base case.


================================================================================
RELATED PROBLEMS
================================================================================
    Topic 28, 004 Power of Two   — same even/halve idea, but the goal is a
                                   yes/no answer, not a step count.
    Topic 28, 005 Power of Three — division that doesn't cleanly halve;
                                   compare termination reasoning directly.
    LC 191  Number of 1 Bits    — the bit-trick follow-up's other half
                                   (bin(num).count('1')) as its own problem.
    Topic 21 (Math & Geometry)  — general "recurse/loop on an arithmetic
                                   transform of n" family.
================================================================================
"""

import sys


class Solution:
    def numberOfSteps(self, num: int) -> int:
        """Recursive, following the actual rule. O(log num) time/space."""
        if num == 0:
            return 0
        if num % 2 == 0:
            return 1 + self.numberOfSteps(num // 2)
        return 1 + self.numberOfSteps(num - 1)

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def numberOfSteps_iterative(self, num: int) -> int:
        """Iterative twin. O(log num) time, O(1) space."""
        steps = 0
        while num > 0:
            if num % 2 == 0:
                num //= 2
            else:
                num -= 1
            steps += 1
        return steps

    def numberOfSteps_naive_subtract_only(self, num: int) -> int:
        """WRONG RULE, kept only to demonstrate the recursion-depth blowup.
        Always subtracts 1, ignoring the halving rule. O(num) time/space."""
        if num == 0:
            return 0
        return 1 + self.numberOfSteps_naive_subtract_only(num - 1)

    def numberOfSteps_bit_trick(self, num: int) -> int:
        """O(log num)-internal, no Python-level loop or recursion."""
        if num == 0:
            return 0
        return num.bit_length() - 1 + bin(num).count("1")


# ==============================================================================
# TESTS — run:  python 001_number_of_steps_to_reduce_a_number_to_zero_solution.py
# ==============================================================================
CASES = [
    (0, 0), (1, 1), (2, 2), (3, 3), (4, 3), (8, 4), (14, 6),
    (123, 12), (1000000, 26),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    impls = [
        ("recursive (rule)   ", sol.numberOfSteps),
        ("iterative twin     ", sol.numberOfSteps_iterative),
        ("bit trick          ", sol.numberOfSteps_bit_trick),
    ]

    for name, fn in impls:
        ok = all(fn(n) == expected for n, expected in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # ----------------------------------------------------------------------
    # Recursion depth: measured, not asserted.
    # ----------------------------------------------------------------------
    print("\n--- recursion depth, measured live (rule-following vs naive subtract-only) ---")
    print(f"  {'num':>10} {'rule-following depth':>22} {'naive subtract-only depth':>27}")
    for n in (14, 123, 987):
        # rule-following depth == its own return value (each call == one step)
        rule_depth = sol.numberOfSteps(n)
        naive_depth = sol.numberOfSteps_naive_subtract_only(n)
        print(f"  {n:>10} {rule_depth:>22} {naive_depth:>27}")

    print("\n  Pushing the naive subtract-only version past Python's recursion limit:")
    limit = sys.getrecursionlimit()
    print(f"  sys.getrecursionlimit() = {limit}")
    big = limit + 500          # guaranteed deeper than the limit allows
    try:
        sol.numberOfSteps_naive_subtract_only(big)
        print(f"  FAIL — expected RecursionError for naive subtract-only on num={big}")
        all_ok = False
    except RecursionError:
        print(f"  CONFIRMED: naive subtract-only(num={big}) raised RecursionError.")
    # the rule-following version handles the same num trivially
    safe_depth = sol.numberOfSteps(big)
    print(f"  Meanwhile numberOfSteps(num={big}) (rule-following) succeeds, "
          f"depth={safe_depth} (O(log num)).")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
