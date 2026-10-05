"""
================================================================================
SOLUTION · LeetCode 326 · Power of Three                                  [Easy]
https://leetcode.com/problems/power-of-three/
================================================================================

THE CORE IDEA
--------------
Structurally identical to 004: repeatedly divide by the base, check for
exact divisibility, three base cases (impossible, success, dead-end).
The point of pairing it with 004 is what's DIFFERENT: base 3 has no bit-
trick shortcut, so the O(1) follow-up has to come from a different idea
entirely (a fixed largest representable power, exploiting primality).


================================================================================
MULTIPLE APPROACHES
================================================================================
1. RECURSIVE DIVISION — the three-base-case version. O(log_3 n) time,
   O(log_3 n) space (call stack). The version taught here.
2. ITERATIVE TWIN — a `while n > 1` loop with the same three checks.
   O(log_3 n) time, O(1) space.
3. LARGEST-POWER TRICK (the stated follow-up) — `n > 0 and 3**19 % n == 0`.
   `3**19 = 1162261467` is the largest power of 3 that fits in a signed
   32-bit int (`3**20` overflows it). Since 3 is PRIME, the only divisors
   of `3**19` are smaller powers of 3 — so "n divides 3**19 evenly" is
   true if and only if n itself is a power of 3 (and n > 0). O(1) time,
   O(1) space — proven equivalent to the recursive version below by
   exhaustive cross-check, not by assertion.
4. LOG-BASE-3 via `log(n) / log(3)` — priced, not written: floating-point
   error near large powers can misclassify borderline non-powers as
   powers (the exact failure mode 004 also warned about for base 2, worse
   here since base 3 has no exact binary representation).


================================================================================
STEP BY STEP TRACE — isPowerOfThree(27)
================================================================================
    call isPowerOfThree(27)   27>0, 27!=1, 27%3==0 -> recurse on 27//3=9
      call isPowerOfThree(9)    9>0, 9!=1, 9%3==0 -> recurse on 9//3=3
        call isPowerOfThree(3)    3>0, 3!=1, 3%3==0 -> recurse on 3//3=1
          call isPowerOfThree(1)    n==1 -> base case, return True
        isPowerOfThree(3) = True
      isPowerOfThree(9) = True
    isPowerOfThree(27) = True

STEP BY STEP TRACE — isPowerOfThree(45)  (a FAILURE path)
    call isPowerOfThree(45)   45>0, 45!=1, 45%3==0 -> recurse on 45//3=15
      call isPowerOfThree(15)   15>0, 15!=1, 15%3==0 -> recurse on 15//3=5
        call isPowerOfThree(5)    5>0, 5!=1, 5%3!=0 -> base case, return False
      isPowerOfThree(15) = False
    isPowerOfThree(45) = False


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time         Space           Mutates input?  Note
    ---------------------------  -----------  --------------  ---------------  --------------------------------
    Recursive division          O(log_3 n)   O(log_3 n) stack  no               3 base cases, same shape as 004
    Iterative twin                O(log_3 n)   O(1)            no               same logic, no call stack
    Largest-power trick (3**19) O(1)         O(1)            no               relies on 3 being PRIME
    log-base-3 (not recommended) O(1)*        O(1)            no               *float precision risk


================================================================================
EDGE CASES
================================================================================
    n = 0    -> False  caught by `n <= 0` before the modulo check — without
                        this guard, `0 % 3 == 0` would recurse forever on
                        `0 // 3 == 0`.
    n = 1    -> True   `3^0`; the success base case, zero divisions needed.
    n < 0    -> False  never a power of three for integer exponents; the
                        constraint explicitly allows negative n, so this
                        must be tested, not assumed impossible by the
                        caller.
    n = 3**19 = 1162261467 -> True  the largest power of three that fits
                        in the stated int32 range; exercises the exact
                        boundary the O(1) trick is built around.
    n = 2**31 - 1 -> False  the largest int32 value; not divisible by 3
                        cleanly on the first check (2147483647 % 3 != 0),
                        fails immediately.


================================================================================
COMMON MISTAKES
================================================================================
1. Checking `n % 3 == 0` before checking `n <= 0` — `0 % 3 == 0` is True,
   causing infinite recursion on `isPowerOfThree(0)` (same bug class as
   004's `n & (n-1)` guard, different mechanism: here it's an ordering
   bug in the base cases, not a missing bitmask guard).
2. Assuming a bit trick exists for base 3 by analogy with 004 — there is
   none; 3 does not divide any power of 2 cleanly, so no fixed bitmask
   isolates "exactly one factor of 3." This is the intended lesson of
   placing 005 directly after 004.
3. Using `3**19 % n == 0` WITHOUT the `n > 0` guard — for n <= 0 this
   either raises `ZeroDivisionError` (n == 0) or gives a misleading
   result for negative n (Python's `%` with a negative n still returns a
   value in `[0, n)` by its own sign convention, which does not mean
   "n is a power of three").
4. Picking the wrong largest exponent for the trick (e.g. using `3**20`,
   which overflows the stated int32 range) — the constant must be the
   LARGEST power of 3 that still fits in the given range, or the trick's
   correctness argument (divisors of a prime power are only smaller
   powers of the same prime) breaks down at the boundary.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you solve this without loop or recursion?
A: Yes: `n > 0 and 1162261467 % n == 0`, using the largest power of 3
   representable in int32 and the fact that 3 is prime.

Q: Why does the "largest power" trick require the base to be prime?
A: If the base weren't prime (say base 4 = 2^2), then non-powers-of-4 that
   are still powers of 2 (like 8) could ALSO divide the largest power of
   4 evenly, giving false positives. Primality guarantees the only
   divisors of `3^19` are `3^0 .. 3^19` — nothing else.

Q: Why does 004 get a bit trick and this doesn't?
A: Binary representation is base 2 by construction, so "exactly one bit
   set" is a direct structural test for "power of 2." No analogous fixed-
   width structural property exists for powers of 3 in binary.


================================================================================
RELATED PROBLEMS
================================================================================
    Topic 28, 004 Power of Two       — identical recursive shape, contrast
                                       the O(1) follow-ups directly.
    Topic 28, 016 Super Pow          — a much harder "exponentiation with
                                       structure" problem in this same
                                       ladder.
    LC 342  Power of Four            — same recursive shape again, with
                                       its own O(1) bit-trick variant
                                       (unlike base 3, base 4 IS a power
                                       of 2, so a bit trick returns).
================================================================================
"""


class Solution:
    def isPowerOfThree(self, n: int) -> bool:
        """Recursive division, three base cases. O(log_3 n) time/space."""
        if n <= 0:
            return False
        if n == 1:
            return True
        if n % 3 != 0:
            return False
        return self.isPowerOfThree(n // 3)

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def isPowerOfThree_iterative(self, n: int) -> bool:
        """Iterative twin. O(log_3 n) time, O(1) space."""
        if n <= 0:
            return False
        while n > 1:
            if n % 3 != 0:
                return False
            n //= 3
        return True

    def isPowerOfThree_largest_power(self, n: int) -> bool:
        """O(1) trick: 3 is prime, so only powers of 3 divide 3**19 evenly."""
        return n > 0 and 1162261467 % n == 0  # 3**19, the largest fitting int32


# ==============================================================================
# TESTS — run:  python 005_power_of_three_solution.py
# ==============================================================================
CASES = [
    (27, True), (0, False), (9, True), (1, True), (3, True),
    (45, False), (-3, False), (3**19, True), (2**31 - 1, False),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    impls = [
        ("recursive division ", sol.isPowerOfThree),
        ("iterative twin     ", sol.isPowerOfThree_iterative),
        ("largest-power trick", sol.isPowerOfThree_largest_power),
    ]

    for name, fn in impls:
        ok = all(fn(n) == expected for n, expected in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- proving the largest-power trick against recursion, -1000..1000000 ---")
    mismatches = [n for n in range(-1000, 1000000)
                  if sol.isPowerOfThree(n) != sol.isPowerOfThree_largest_power(n)]
    if mismatches:
        print(f"  FAIL — {len(mismatches)} mismatches, e.g. {mismatches[:5]}")
        all_ok = False
    else:
        print("  CONFIRMED: largest-power trick matches recursion on all 1,001,000 cases.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
