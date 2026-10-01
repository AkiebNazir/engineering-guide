"""
================================================================================
SOLUTION · LeetCode 7 · Reverse Integer                              [Medium]
https://leetcode.com/problems/reverse-integer/
================================================================================

THE CORE IDEA
--------------
Peel decimal digits off the end of `abs(x)` with `% 10` / `// 10` and
rebuild them in reverse order with `rev = rev * 10 + digit`. Restore the
sign at the end. The entire difficulty is NOT the digit reversal itself
(three lines) -- it's that Python has no signed-32-bit int type to lean
on, so the "if this overflows INT32, return 0" requirement has to be
implemented by hand, by comparing against explicit INT32_MIN/INT32_MAX
constants, since nothing in Python will do it for you or even complain.

    INT_MAX, INT_MIN = 2**31 - 1, -2**31
    sign = -1 if x < 0 else 1
    x = abs(x)
    rev = 0
    while x:
        rev = rev * 10 + x % 10
        x //= 10
    rev *= sign
    return rev if INT_MIN <= rev <= INT_MAX else 0


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force via string, name it and consider it): convert
abs(x) to a string, reverse it with `s[::-1]`, convert back to int,
restore sign, then bounds-check. O(log x) time and space (string length
scales with digit count) -- perfectly valid, arguably clearer, and is
included below as an alternative. The forbidden move here isn't the
string conversion itself, it's SKIPPING the bounds check afterward --
covered in Common Mistakes.

Approach 1 (digit-by-digit arithmetic, check AFTER building) [chosen for
the trace] -- build the full reversed value with `% 10` / `// 10`, then
compare the finished value against INT32_MIN/MAX. Simple, but means you
momentarily hold a value that could be arbitrarily large before the
check happens (harmless in Python since ints are unbounded, but worth
naming as a design choice).

Approach 2 (digit-by-digit arithmetic, check BEFORE each multiply)
[hardened variant] -- before doing `rev = rev * 10 + digit`, check
whether `rev` is already past `INT_MAX // 10` (or the equivalent for
INT_MIN) -- the standard technique from languages where a fixed-width
int WOULD silently wrap or corrupt during the multiply itself, so the
check must happen pre-emptively rather than after the fact. Not strictly
necessary in Python (which never wraps), but this is the version that
ports directly to C/Java with zero behavior change, and is what most
interviewers actually want to see, since it demonstrates you understand
WHY the check matters, not just that a check exists.


================================================================================
STEP BY STEP TRACE
================================================================================
x = -123   (sign = -1, work with abs(x) = 123)

    x=123: digit = 123 % 10 = 3, rev = 0*10+3 = 3,   x //= 10 -> x=12
    x=12:  digit = 12 % 10 = 2,  rev = 3*10+2 = 32,  x //= 10 -> x=1
    x=1:   digit = 1 % 10 = 1,   rev = 32*10+1 = 321, x //= 10 -> x=0
    loop ends (x == 0)

    rev *= sign -> rev = -321
    Bounds check: -2147483648 <= -321 <= 2147483647  -> True, no overflow

    Return -321   <- matches expected output


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time        Space   Mutates input?
    -------------------------------------  ----------  ------  --------------
    String reverse + bounds check          O(log x)    O(log x) no
    Digit arithmetic, check after [chosen] O(log x)    O(1)    no
    Digit arithmetic, check before (hardened) O(log x) O(1)    no


================================================================================
EDGE CASES
================================================================================
    x == 0                     -> loop never runs, rev stays 0. Trivially
                                   in bounds.
    trailing zeros (x=120)     -> reversing naturally drops the leading
                                   zero that would otherwise appear
                                   (120 -> "021" conceptually, but integer
                                   arithmetic just produces 21 directly --
                                   no special-casing needed).
    x == INT32_MIN (-2^31)     -> abs(-2^31) in Python is fine (arbitrary
                                   precision, no "can't represent
                                   +2^31" trap that a fixed-width abs()
                                   would hit) -- but the REVERSED digits
                                   of 2147483648 is 8463847412, which
                                   overflows INT32_MAX by a wide margin.
                                   Must return 0.
    x == INT32_MAX (2^31 - 1)  -> reversed digits of 2147483647 is
                                   7463847412, also overflows. Must
                                   return 0.
    reversed value lands EXACTLY on a boundary -> e.g. reversing
                                   1463847412 gives 2147483641, which is
                                   <= INT32_MAX -- a legitimate success,
                                   not an overflow, even though it's very
                                   close to the limit. The check must be
                                   an exact comparison, not a heuristic
                                   "looks too big" guess.


================================================================================
COMMON MISTAKES
================================================================================
1. THE headline mistake: forgetting the bounds check entirely, because
   Python happily computes `rev` correctly no matter how large it gets --
   there's no crash, no wrap, no signal of any kind that anything is
   wrong. The function "works" on every test EXCEPT the overflow cases,
   which silently return a huge (wrong) int instead of 0. Demonstrated
   live below.

2. Checking bounds with `abs(rev) > 2**31` instead of the correct
   asymmetric range `[-2**31, 2**31 - 1]` -- signed 32-bit range is NOT
   symmetric (there's one more negative value than positive, e.g.
   -2147483648 is valid but 2147483648 is not). A symmetric check either
   wrongly rejects -2147483648 or wrongly accepts 2147483648.

3. Applying the sign BEFORE reversing digits (`x = -123`, reverse of
   -123 as a whole including the minus sign via naive string slicing) --
   `str(-123)[::-1]` gives `'321-'`, and `int('321-')` raises ValueError.
   Must strip the sign first, reverse the magnitude, then reapply the
   sign.

4. Using `x % 10` directly on a NEGATIVE x in Python without first taking
   abs() -- Python's `%` always returns a result with the SAME SIGN AS
   THE DIVISOR (here positive), so `-123 % 10` is `7`, not `-3` as
   C/Java's truncating `%` would give. Silently produces wrong digits if
   you forget Python's modulo semantics differ from C's.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why can't you just check `if rev > INT_MAX: return 0` inside the loop,
   the way languages with fixed-width ints often teach it?
A: You can, and should for the "hardened" version (Approach 2) -- check
   BEFORE the multiply-and-add using `rev > INT_MAX // 10 or (rev ==
   INT_MAX // 10 and digit > INT_MAX % 10)`, which is what actually
   prevents an overflow from ever being computed in a fixed-width
   language. In Python it's cosmetic (ints never overflow), but it's the
   version that's correct in EVERY language, so it's the safer default
   to reach for.

Q: How is this different from 006 Sum of Two Integers' masking?
A: 006 emulates a 32-bit machine WORD via bitwise `&` masking because the
   algorithm literally manipulates bits. 007 reverses DECIMAL digits (a
   base-10 operation) and only needs a numeric RANGE check at the end --
   no bitwise masking is involved at all, just a comparison against
   INT32_MIN/MAX. Different mechanism, same underlying lesson: Python
   won't enforce the 32-bit contract for you.

Q: What if the environment truly didn't allow 64-bit integers (as the
   problem statement says), i.e. you're in a language where even holding
   an intermediate `rev` value past 2^31-1 is itself illegal?
A: That's exactly why Approach 2 (check-before-multiply) exists --
   Python's unbounded ints make it MOOT here, but the discipline
   generalizes to that constraint directly.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 371  Sum of Two Integers    (006 -- masking discipline, bitwise not
                                      decimal, same "Python won't stop you"
                                      lesson)
    LC 190  Reverse Bits           (004 -- reverses BITS not digits, fixed
                                      32-bit width by construction, no
                                      overflow possible by design)
    LC 8    String to Integer (atoi) (same INT32 clamp-and-check discipline)
    LC 9    Palindrome Number       (digit-reversal building block reused)
================================================================================
"""

import time


INT_MAX = 2**31 - 1
INT_MIN = -2**31


class Solution:
    def reverse(self, x: int) -> int:
        """✅ Digit-by-digit reversal, bounds check after. O(log x) time,
        O(1) space."""
        sign = -1 if x < 0 else 1
        x = abs(x)
        rev = 0
        while x:
            rev = rev * 10 + x % 10
            x //= 10
        rev *= sign
        return rev if INT_MIN <= rev <= INT_MAX else 0

    def reverse_hardened(self, x: int) -> int:
        """Alternative: check BEFORE each multiply -- the version that
        ports unchanged to a language with true fixed-width ints."""
        sign = -1 if x < 0 else 1
        x = abs(x)
        rev = 0
        limit = INT_MAX if sign == 1 else -INT_MIN  # 2**31-1 or 2**31
        while x:
            digit = x % 10
            if rev > (limit - digit) // 10:
                return 0
            rev = rev * 10 + digit
            x //= 10
        return rev * sign

    def reverse_string(self, x: int) -> int:
        """Alternative: string reversal + bounds check. O(log x) time,
        O(log x) space."""
        sign = -1 if x < 0 else 1
        rev = int(str(abs(x))[::-1]) * sign
        return rev if INT_MIN <= rev <= INT_MAX else 0

    def reverse_NO_BOUNDS_CHECK_UNSAFE(self, x: int) -> int:
        """Same digit-by-digit reversal but with the overflow check
        REMOVED. Kept only to demonstrate the bug live in run_tests()."""
        sign = -1 if x < 0 else 1
        x = abs(x)
        rev = 0
        while x:
            rev = rev * 10 + x % 10
            x //= 10
        return rev * sign


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        (123, 321),
        (-123, -321),
        (120, 21),
        (0, 0),
        (1534236469, 0),
        (-2147483648, 0),
        (1463847412, 2147483641),
    ]
    print("--- correctness: all three safe approaches agree ---")
    for x, want in cases:
        g1 = sol.reverse(x)
        g2 = sol.reverse_hardened(x)
        g3 = sol.reverse_string(x)
        ok = g1 == g2 == g3 == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  x={x:>12}  -> {g1:>12}  (want {want})")

    # ------------------------------------------------------------------
    # LIVE BUG DEMO: forgetting the INT32 bounds check. Python happily
    # computes a "correct" reversed digit sequence that is nonetheless
    # not a valid signed 32-bit int -- and returns it with no error.
    # ------------------------------------------------------------------
    print("\n--- DEMO: skipping the overflow check silently returns a garbage value ---")
    overflow_cases = [(1534236469, 0), (-2147483648, 0)]
    bug_demonstrated = True
    for x, want in overflow_cases:
        unsafe = sol.reverse_NO_BOUNDS_CHECK_UNSAFE(x)
        safe = sol.reverse(x)
        in_range = INT_MIN <= unsafe <= INT_MAX
        print(f"  reverse({x}):")
        print(f"    WITHOUT bounds check: {unsafe}  "
              f"({'within' if in_range else 'OUTSIDE'} signed 32-bit range "
              f"[{INT_MIN}, {INT_MAX}]) -- Python computed it with zero complaint")
        print(f"    WITH bounds check:    {safe}  (want {want})")
        bug_demonstrated &= (not in_range) and (safe == want)
    all_ok &= bug_demonstrated

    # ------------------------------------------------------------------
    # RUNTIME DEMO: after-the-fact check vs check-before-multiply,
    # across a large batch. Both correct in Python; measured to show
    # the "hardened" version's extra per-digit branch cost.
    # ------------------------------------------------------------------
    print("\n--- DEMO: check-after vs check-before-multiply, 500,000 random ints ---")
    import random
    random.seed(9)
    values = [random.randint(INT_MIN, INT_MAX) for _ in range(500_000)]

    t0 = time.perf_counter()
    r1 = [sol.reverse(v) for v in values]
    t_after = time.perf_counter() - t0

    t0 = time.perf_counter()
    r2 = [sol.reverse_hardened(v) for v in values]
    t_before = time.perf_counter() - t0

    print(f"  check-after (chosen):        {t_after * 1000:8.2f} ms")
    print(f"  check-before (hardened):     {t_before * 1000:8.2f} ms")
    all_ok &= (r1 == r2)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
