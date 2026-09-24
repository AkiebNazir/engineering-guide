"""
================================================================================
SOLUTION · LeetCode 372 · Super Pow                                     [Medium]
https://leetcode.com/problems/super-pow/
================================================================================

THE CORE IDEA
--------------
Treat `b` as a number built digit by digit and use
`a^(10x + d) = (a^x)^10 * a^d`: peel off the LAST digit `d`, recurse on
the remaining digits to get `a^x mod 1337`, then raise that to the 10th
power and multiply by `a^d`, applying `% 1337` at EVERY step so numbers
never grow beyond a few thousand regardless of how many digits `b` has.
Python's 3-argument `pow(base, exp, mod)` does the modular exponentiation
for each step in O(log exp) time, but exp here is always tiny (10 or a
single digit) — the real cost driver is the NUMBER OF RECURSIVE CALLS,
one per digit of `b`.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. RECURSIVE, PEEL LAST DIGIT — the version above. O(len(b)) recursive
   calls, each O(1) via built-in modular `pow()`. Total O(len(b)) time,
   O(len(b)) space (call stack). The version taught here.
2. ITERATIVE, FOLD LEFT-TO-RIGHT — same identity, no recursion: start
   `result = 1`, and for each digit `d` in `b` (left to right this time):
   `result = pow(result, 10, 1337) * pow(a, d, 1337) % 1337`. O(len(b))
   time, O(1) space. What to write in an interview once the identity is
   explained.
3. CONVERT b TO ONE HUGE INTEGER AND USE `pow(a, bigInt, 1337)` DIRECTLY
   — Python's arbitrary-precision integers and built-in modular
   exponentiation make this technically correct and fast in Python
   specifically, but it defeats the point of the exercise (in most
   other languages, a 2000-digit exponent literally cannot be stored in
   a native integer type, which is WHY this problem exists) — named as
   a language-specific shortcut, not the general technique.


================================================================================
STEP BY STEP TRACE — superPow(2, [1, 0])   i.e. 2^10 mod 1337
================================================================================
    call superPow(2, [1, 0])
      lastDigit = 0, rest = [1]
      call superPow(2, [1])
        lastDigit = 1, rest = []
        call superPow(2, [])   base case -> return 1
        combine: pow(1, 10, 1337) * pow(2, 1, 1337) % 1337 = 1 * 2 % 1337 = 2
      superPow(2, [1]) = 2                    (this is 2^1 mod 1337, correctly)
      combine: pow(2, 10, 1337) * pow(2, 0, 1337) % 1337 = (1024 % 1337) * 1 % 1337 = 1024

Result: 1024 = 2^10, matching the expected output exactly (well under
1337, so the modulus didn't even need to reduce it here).


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time         Space          Mutates input?  Note
    ------------------------------  -----------  -------------  ---------------  --------------------------------
    Recursive, peel last digit      O(len(b))    O(len(b)) stack no              one call per digit
    Iterative, fold left-to-right   O(len(b))    O(1)           no               same identity, no recursion
    Convert to one big int + pow    O(len(b))*   O(len(b))*     no               *big-int arithmetic cost in general


================================================================================
EDGE CASES
================================================================================
    b = [0]           -> 1     any positive `a` to the 0th power is 1;
                                the recursion peels the single digit 0,
                                recurses on an EMPTY rest (base case = 1),
                                then combines `pow(1,10,1337) *
                                pow(a,0,1337) = 1 * 1 = 1`.
    a = 1              -> 1     1 to ANY power is 1, regardless of how
                                large `b` is (2000+ digits in the given
                                example) — a useful sanity check that
                                the recursion terminates correctly even
                                for the longest allowed `b`.
    len(b) = 2000 (upper bound) -> exercises real recursion depth of
                                2000, comfortably within what Python's
                                default recursion limit would need
                                raising for (2000 < 1000 is false — this
                                actually DOES exceed the default ~1000
                                limit and needs attention, demonstrated
                                live below).
    a at its maximum, 2^31 - 1 -> confirms `pow(a, digit, 1337)` handles
                                a large base correctly without ever
                                computing the full unreduced power.


================================================================================
COMMON MISTAKES
================================================================================
1. Applying `% 1337` only at the very END of the whole computation
   instead of at every intermediate step — the unreduced number
   `a^b` for `a` near 2^31 and `b` with 2000 digits would have on the
   order of tens of billions of digits, computationally infeasible to
   even construct, let alone reduce afterward.
2. Using plain `**` for `a ** lastDigit` or `result ** 10` instead of
   Python's 3-argument `pow(base, exp, mod)` — computes the full
   unreduced power first (fine for `exp` this small, since digits are
   0-9 and the other exponent is fixed at 10, but a red flag habit that
   fails catastrophically the moment exponents aren't guaranteed tiny).
3. Peeling off the FIRST digit of `b` instead of the LAST, and trying to
   adapt the identity to fit — `a^(10x + d)` specifically corresponds to
   `d` being the LAST digit of the number `10x + d` represents; peeling
   from the front requires a different (more awkward) identity built
   around the digit's actual place value.
4. For `len(b)` up to 2000, not noticing this exceeds Python's default
   recursion limit (~1000) — the plain recursive version WILL raise
   `RecursionError` for the longest allowed inputs unless the limit is
   raised or the iterative version is used, demonstrated live below.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you avoid recursion given `b` can have up to 2000 digits?
A: Yes — the iterative left-to-right fold computes the identical result
   with a simple loop and O(1) extra space, with no recursion-depth risk
   at all.

Q: Why does `(x * y) mod m = ((x mod m) * (y mod m)) mod m` matter here?
A: It's the modular arithmetic identity that justifies reducing mod 1337
   at every intermediate multiplication instead of only at the end —
   without it, there'd be no guarantee that reducing early gives the
   same final answer as reducing late (it does, and this is why).

Q: How would this change if the modulus weren't a small fixed constant
   like 1337, but itself a huge number?
A: The approach is unaffected in principle — `pow(base, exp, mod)` works
   for any modulus — but the intermediate values would then be as large
   as the modulus itself, so the "everything stays small" benefit would
   shrink proportionally.


================================================================================
RELATED PROBLEMS
================================================================================
    Topic 28, 004/005 Power of Two / Power of Three — much simpler
                                       "recurse on a shrinking exponent-
                                       like structure" problems, without
                                       a modulus or digit-array input.
    LC 50   Pow(x, n)                 — classic fast exponentiation
                                       without a modulus or an
                                       oversized exponent.
    Topic 21 Math & Geometry (Multiply Strings) — another problem where
                                       an "arbitrarily large number" is
                                       represented as an array/string of
                                       digits, forcing digit-by-digit
                                       processing.
================================================================================
"""

import sys
from typing import List

MOD = 1337


class Solution:
    def superPow(self, a: int, b: List[int]) -> int:
        """Recursive, peel the last digit each call. O(len(b)) time/space."""
        if not b:
            return 1
        last_digit = b[-1]
        rest_power = self.superPow(a, b[:-1])
        return (pow(rest_power, 10, MOD) * pow(a, last_digit, MOD)) % MOD

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def superPow_iterative(self, a: int, b: List[int]) -> int:
        """Iterative, fold left to right. O(len(b)) time, O(1) space."""
        result = 1
        for digit in b:
            result = (pow(result, 10, MOD) * pow(a, digit, MOD)) % MOD
        return result


# ==============================================================================
# TESTS — run:  python 016_super_pow_solution.py
# ==============================================================================
CASES = [
    (2, [3], 8),
    (2, [1, 0], 1024),
    (1, [4, 3, 3, 8, 5, 2, 4, 3, 7, 9, 8, 2, 3, 8, 9, 7, 9, 2, 3, 8, 4, 7, 9, 2, 2, 3], 1),
    (2, [0], 1),
    (7, [7], 1288),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    impls = [
        ("recursive, peel last digit", sol.superPow),
        ("iterative, fold left       ", sol.superPow_iterative),
    ]

    for name, fn in impls:
        ok = all(fn(a, b) == expected for a, b, expected in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- pushing the recursive version to len(b)=2000 (upper bound), measured live ---")
    limit = sys.getrecursionlimit()
    print(f"  sys.getrecursionlimit() = {limit}")
    big_b = [1] + [0] * 1999  # a valid 2000-digit exponent, no leading zero
    try:
        sol.superPow(2, big_b)
        recursive_ok = True
    except RecursionError:
        recursive_ok = False
    print(f"  recursive superPow with len(b)=2000: {'succeeded' if recursive_ok else 'RAISED RecursionError'}")
    iterative_result = sol.superPow_iterative(2, big_b)
    print(f"  iterative superPow with len(b)=2000 succeeds regardless: result={iterative_result}")
    if not recursive_ok:
        # cross-check the iterative result against a bumped recursion limit, to confirm correctness
        old_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(3000)
        cross_check = sol.superPow(2, big_b)
        sys.setrecursionlimit(old_limit)
        all_ok &= (cross_check == iterative_result)
        print(f"  cross-check (limit raised to 3000): recursive result={cross_check} "
              f"{'matches' if cross_check == iterative_result else 'MISMATCHES'} iterative result")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
