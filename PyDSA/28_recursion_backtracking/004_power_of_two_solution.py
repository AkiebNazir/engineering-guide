"""
================================================================================
SOLUTION · LeetCode 231 · Power of Two                                    [Easy]
https://leetcode.com/problems/power-of-two/
================================================================================

THE CORE IDEA
--------------
Repeatedly halve `n`; a power of two always reaches exactly 1 this way
without ever hitting an odd number first. This reuses 001's halving
progress measure but turns it into a yes/no predicate with THREE distinct
base cases (one success, two failure) instead of a single accumulator —
the first "multiple ways to stop" recursion in this folder.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. RECURSIVE HALVING — the three-base-case version above. O(log n) time,
   O(log n) space (call stack). The version taught here.
2. ITERATIVE TWIN — a `while n > 1` loop with the same three checks.
   O(log n) time, O(1) space.
3. BIT TRICK `n > 0 and (n & (n - 1)) == 0` — a power of two has exactly
   one set bit; subtracting 1 flips that bit and every bit below it, so
   the AND is 0 only in that case (and only for n > 0, since the trick
   also spuriously holds for n == 0 without the explicit guard). O(1)
   time, O(1) space — the stated follow-up, proven equivalent to the
   recursive version below by exhaustive cross-check, not by assertion.
4. MATH via `log2` — check whether `log2(n)` is (close to) an integer.
   Priced, not written: floating-point `log2` has precision issues near
   powers of two at the extremes of the int32 range, making this the
   LEAST reliable approach despite looking the most "mathematical."


================================================================================
STEP BY STEP TRACE — isPowerOfTwo(16)
================================================================================
    call isPowerOfTwo(16)   16>0, 16!=1, 16 even -> recurse on 16//2=8
      call isPowerOfTwo(8)    8>0, 8!=1, 8 even -> recurse on 8//2=4
        call isPowerOfTwo(4)    4>0, 4!=1, 4 even -> recurse on 4//2=2
          call isPowerOfTwo(2)    2>0, 2!=1, 2 even -> recurse on 2//2=1
            call isPowerOfTwo(1)    n==1 -> base case, return True
          isPowerOfTwo(2) = True
        isPowerOfTwo(4) = True
      isPowerOfTwo(8) = True
    isPowerOfTwo(16) = True

STEP BY STEP TRACE — isPowerOfTwo(12)  (a FAILURE path)
    call isPowerOfTwo(12)   12>0, 12!=1, 12 even -> recurse on 12//2=6
      call isPowerOfTwo(6)    6>0, 6!=1, 6 even -> recurse on 6//2=3
        call isPowerOfTwo(3)    3>0, 3!=1, 3 is ODD -> base case, return False
      isPowerOfTwo(6) = False
    isPowerOfTwo(12) = False


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                Time      Space         Mutates input?  Note
    -----------------------  --------  ------------  ---------------  --------------------------------
    Recursive halving       O(log n)  O(log n) stack  no               3 base cases (1 success, 2 fail)
    Iterative twin           O(log n)  O(1)           no               same logic, no call stack
    Bit trick n & (n-1)     O(1)      O(1)           no               proven equivalent below
    log2 (not recommended)  O(1)*     O(1)           no               *float precision issues at extremes


================================================================================
EDGE CASES
================================================================================
    n = 0    -> False  never a power of two; MUST be caught by `n <= 0`
                        before checking `n % 2`, or `0 % 2 == 0` would
                        recurse forever on `0 // 2 == 0` (infinite loop /
                        RecursionError, not a wrong answer).
    n = 1    -> True   `2^0`; the success base case, reached with zero
                        halvings.
    n < 0    -> False  negative numbers are never powers of two for
                        integer exponents; caught by the same `n <= 0`
                        guard as n == 0.
    n = 2^30 -> True   near the top of the positive int32 range; exercises
                        real recursion depth (30) without overflowing.
    n = 2^31 - 1 -> False  the largest int32 value, one less than 2^31 —
                        odd, so it fails on the very first odd-check,
                        despite being suspiciously close to a power of two.


================================================================================
COMMON MISTAKES
================================================================================
1. Checking `n % 2 == 0` BEFORE checking `n <= 0` — `0 % 2 == 0` is True,
   so this recurses on `isPowerOfTwo(0 // 2) = isPowerOfTwo(0)` forever,
   causing infinite recursion (RecursionError) instead of correctly
   returning False for n = 0.
2. Missing the `n == 1` base case and instead treating `n == 0` as the only
   "stop" condition — halving 1 gives `1 // 2 == 0` in integer division,
   so without an explicit `n == 1` check, 1 would incorrectly recurse into
   the n == 0 branch and return False instead of True.
3. Using the bit trick without the `n > 0` guard — `0 & (0 - 1) == 0 & -1
   == 0` in Python (arbitrary-precision two's-complement semantics), so
   the bare `(n & (n-1)) == 0` check WRONGLY reports 0 as a power of two
   without the explicit positivity guard.
4. Forgetting negative inputs are in-bounds per the constraints (`-2^31 <=
   n`) and only testing n >= 0 by habit — a solution that doesn't
   explicitly reject negatives can pass casual testing while being wrong
   for half the input domain.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you do this without any loop or recursion?
A: Yes — `n > 0 and (n & (n - 1)) == 0`. A power of two has exactly one bit
   set; `n - 1` flips that bit and all lower bits to 1, so ANDing the two
   clears everything, giving 0 only in that case.

Q: Why does `n & (n - 1)` work, mechanically?
A: For `n = 8 = 0b1000`, `n - 1 = 7 = 0b0111` — no overlapping set bits, AND
   is 0. For `n = 12 = 0b1100` (not a power of two), `n - 1 = 11 = 0b1011`
   — bit 3 (value 8) is set in both, AND is nonzero.

Q: Is `log2(n) % 1 == 0` a safe check?
A: Not fully — floating-point `log2` can round a non-power-of-two up to
   what looks like an exact power near the edges of the representable
   range, giving false positives. The bit trick has no such risk.


================================================================================
RELATED PROBLEMS
================================================================================
    Topic 28, 001 Number of Steps to Reduce a Number to Zero — the same
                                       halving progress measure, used to
                                       count steps instead of test a
                                       predicate.
    Topic 28, 005 Power of Three     — the same shape (repeatedly divide,
                                       check for exact division), but base 3
                                       has NO equivalent bit trick.
    LC 191 Number of 1 Bits          — counting set bits directly relates
                                       to why n & (n-1) works.
================================================================================
"""


class Solution:
    def isPowerOfTwo(self, n: int) -> bool:
        """Recursive halving, three base cases. O(log n) time/space."""
        if n <= 0:
            return False
        if n == 1:
            return True
        if n % 2 != 0:
            return False
        return self.isPowerOfTwo(n // 2)

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def isPowerOfTwo_iterative(self, n: int) -> bool:
        """Iterative twin. O(log n) time, O(1) space."""
        if n <= 0:
            return False
        while n > 1:
            if n % 2 != 0:
                return False
            n //= 2
        return True

    def isPowerOfTwo_bit_trick(self, n: int) -> bool:
        """O(1) bit trick: a power of two has exactly one set bit."""
        return n > 0 and (n & (n - 1)) == 0


# ==============================================================================
# TESTS — run:  python 004_power_of_two_solution.py
# ==============================================================================
CASES = [
    (1, True), (2, True), (3, False), (4, True), (16, True),
    (0, False), (-16, False), (2**30, True), (2**31 - 1, False), (5, False),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    impls = [
        ("recursive halving  ", sol.isPowerOfTwo),
        ("iterative twin     ", sol.isPowerOfTwo_iterative),
        ("bit trick          ", sol.isPowerOfTwo_bit_trick),
    ]

    for name, fn in impls:
        ok = all(fn(n) == expected for n, expected in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- proving the bit trick against the recursive version, -1000..100000 ---")
    mismatches = [n for n in range(-1000, 100000)
                  if sol.isPowerOfTwo(n) != sol.isPowerOfTwo_bit_trick(n)]
    if mismatches:
        print(f"  FAIL — {len(mismatches)} mismatches, e.g. {mismatches[:5]}")
        all_ok = False
    else:
        print("  CONFIRMED: bit trick matches recursion on all 101,000 cases.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
