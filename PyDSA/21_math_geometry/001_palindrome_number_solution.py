"""
================================================================================
SOLUTION · LeetCode 9 · Palindrome Number                            [Easy]
https://leetcode.com/problems/palindrome-number/
================================================================================

THE CORE IDEA
--------------
Two O(1) rejections before doing any digit work: a negative number is never
a palindrome (the sign only shows up on one side, "-121" reversed is
"121-"), and a positive number ending in 0 is never a palindrome unless it
IS 0 (a reversed number can't have a leading zero, so anything like `120`
or `100` fails immediately). Past those, peel digits off the BACK of `x`
into a `reversed_half` accumulator, one at a time, only until
`reversed_half >= x` (the remaining front half has shrunk to be no bigger
than the reversed back half). At that point compare the two halves
directly: for even digit-counts they must be equal; for odd digit-counts
the reversed half has one extra (middle) digit, so drop it with
`reversed_half // 10` before comparing.

This reverses only ABOUT HALF of the digits, not the whole number. In a
fixed-width language (32-bit int) that matters directly: reversing the full
number can overflow (e.g. reversing `1534236469` overflows a 32-bit int),
so full-reverse-and-compare needs an explicit overflow guard, while
half-reversal never produces a value larger than `sqrt(x)`-ish in
magnitude and never overflows. Python ints are arbitrary precision, so
overflow can't crash this specific run — but the technique is still the
right algorithmic answer: it does strictly less work (half the digit
peels) and is the version worth knowing cold for languages where it does
matter.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (convert to string, price it): `s = str(x); return s == s[::-1]`
after rejecting negatives. O(n) time and O(n) EXTRA space for the string
and its reverse, where n = number of digits. Trivially correct, and the
follow-up explicitly asks you not to do this.

Approach 1 (chosen) -- reverse only the second half, using pure integer
arithmetic (`% 10` to peel a digit, `// 10` to shift), and compare the two
halves. O(log10 x) time (proportional to digit count), O(1) extra space --
no string materialized at all.


================================================================================
STEP BY STEP TRACE
================================================================================
x = 1221 (even digit count)

    reject negative? no.  x % 10 == 0 and x != 0? 1221 % 10 = 1, no.

    x = 1221, reversed_half = 0
    loop while x > reversed_half:
        iter 1: digit = 1221 % 10 = 1; reversed_half = 0*10+1 = 1; x = 1221//10 = 122
                x(122) > reversed_half(1)? yes, continue
        iter 2: digit = 122 % 10 = 2; reversed_half = 1*10+2 = 12; x = 122//10 = 12
                x(12) > reversed_half(12)? no (equal) -- STOP

    even digit count check: x == reversed_half -> 12 == 12 -> True -> PALINDROME


x = 12321 (odd digit count)

    x = 12321, reversed_half = 0
        iter 1: digit=1, reversed_half=1,  x=1232;  1232 > 1? yes
        iter 2: digit=2, reversed_half=12, x=123;   123 > 12? yes
        iter 3: digit=3, reversed_half=123, x=12;   12 > 123? no -- STOP

    x(12) < reversed_half(123): odd digit count, middle digit is the extra
    one in reversed_half. Drop it: reversed_half // 10 = 12.
    x == reversed_half // 10 -> 12 == 12 -> True -> PALINDROME


x = 10 (trailing-zero rejection)

    x % 10 == 0 (10 % 10 == 0) and x != 0 -> reject immediately -> NOT a
    palindrome, no digit-peeling needed at all.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time            Space    Mutates input?
    -------------------------------------------------------------------
    String reverse [priced]     O(n)            O(n)      no
    Half-reversal [chosen]      O(log10 x)      O(1)      no

    n = number of decimal digits in x.


================================================================================
EDGE CASES
================================================================================
    x < 0                -> never a palindrome; sign only appears on one
                             side once "reversed". Reject in O(1).
    x == 0                -> IS a palindrome (single digit, trivially equal
                             to its own reverse); must not be caught by the
                             "ends in 0" rejection, which is why that check
                             is `x % 10 == 0 and x != 0`.
    x ends in 0, x != 0   -> e.g. 10, 120, 100 -- a reversed number can
                             never have a leading zero, so these can never
                             be palindromes; reject in O(1) without peeling
                             a single digit.
    single-digit x (1-9)  -> trivially a palindrome; loop body runs zero
                             times because x == reversed_half (both 0)
                             before the first peel is even needed... actually
                             the loop peels exactly one digit and then
                             x <= reversed_half immediately, handled by the
                             same even-length equality check.
    even vs. odd digit
    count                 -> the two different post-loop comparisons
                             (`x == reversed_half` vs `x == reversed_half //
                             10`) are the crux of the whole approach; getting
                             this branch wrong is the #1 bug source.


================================================================================
COMMON MISTAKES
================================================================================
1. Converting to a string anyway despite the explicit follow-up asking for
   an integer-only approach -- works, but loses the interview signal the
   question is testing for.
2. Reversing the WHOLE number instead of half of it -- correct in Python,
   but in a fixed-width language this can silently overflow (e.g. reversing
   `1534236469`, a real LeetCode test case, overflows a 32-bit signed int).
3. Forgetting the odd-length correction (`reversed_half // 10`) and
   comparing `x == reversed_half` unconditionally -- fails every odd-digit
   palindrome (e.g. `12321` would compare `12 == 123`, False, wrongly
   rejecting a real palindrome).
4. Forgetting `x != 0` in the "ends in zero" rejection -- would incorrectly
   reject 0 itself, which IS a valid single-digit palindrome.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Why not just reverse the whole number and compare?" -> Works in Python,
  but (a) it's twice the digit-peeling work for no benefit, and (b) in a
  fixed-width-integer language it can overflow; half-reversal never
  produces a value larger in magnitude than roughly sqrt(x) and is safe by
  construction.
- "What if x could be a very large number represented as a string (bigger
  than any fixed integer type)?" -> Then a two-pointer string comparison
  (front pointer / back pointer, walk inward) is the right O(n) tool --
  the "avoid string conversion" constraint here is specifically about
  a machine-integer-sized input.
- "Is 0 a palindrome? What about negative numbers?" -> 0 yes (trivially),
  negative no (asymmetric sign) -- both must be handled as explicit edge
  cases, not accidents of the general algorithm.


================================================================================
RELATED PROBLEMS
================================================================================
- Valid Palindrome (LC 125, topic 02) -- the string/two-pointer version of
  "is this a palindrome," contrast with this integer-arithmetic version.
- Reverse Integer (LC 7) -- the same digit-peeling loop, without the
  early-stop-at-half trick, plus an explicit 32-bit overflow check.
- Happy Number (LC 202, this topic, 003) -- another "operate on individual
  digits via % and //" problem, different goal (cycle detection).
================================================================================
"""

import time


class Solution:
    def isPalindrome(self, x: int) -> bool:
        if x < 0:
            return False
        if x != 0 and x % 10 == 0:
            return False

        reversed_half = 0
        while x > reversed_half:
            digit = x % 10
            reversed_half = reversed_half * 10 + digit
            x //= 10

        return x == reversed_half or x == reversed_half // 10


def _full_reverse_isPalindrome(x: int) -> bool:
    """Priced-not-shipped alternative: reverse the WHOLE number via string,
    used only for the measured comparison demo below."""
    if x < 0:
        return False
    s = str(x)
    return s == s[::-1]


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        (121, True),
        (-121, False),
        (10, False),
        (0, True),
        (1, True),
        (12321, True),
        (1221, True),
        (123, False),
        (100, False),
        (11, True),
        (1000021, False),
        (1234321, True),
    ]
    for x, expected in cases:
        got = sol.isPalindrome(x)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  isPalindrome({x}) -> {got} (expected {expected})")

    print()
    print("CROSS-CHECK -- half-reversal vs full string-reverse, 5000 random ints")
    print("-" * 72)
    import random
    random.seed(3)
    mismatch = 0
    for _ in range(5000):
        v = random.randint(-10_000_000, 10_000_000)
        a = sol.isPalindrome(v)
        b = _full_reverse_isPalindrome(v)
        if a != b:
            mismatch += 1
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {5000 - mismatch}/5000 agree ({mismatch} mismatches)")

    print()
    print("RUNTIME DEMO -- half-reversal vs full-string-reverse, measured live")
    print("-" * 72)
    n = 2_000_000
    values = [10**9 + i for i in range(n)]  # 10-digit-ish ints, mixed palindromic-ness

    t0 = time.perf_counter()
    for v in values:
        sol.isPalindrome(v)
    half_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    for v in values:
        _full_reverse_isPalindrome(v)
    full_ms = (time.perf_counter() - t0) * 1000

    print(f"n={n} calls:")
    print(f"  half-reversal (int arithmetic): {half_ms:8.2f} ms")
    print(f"  full string reverse:            {full_ms:8.2f} ms")
    if full_ms < half_ms:
        print(f"  measured: string-reverse is {half_ms / full_ms:.2f}x FASTER here -- CPython's "
              f"C-level string reversal (`s[::-1]`) beats interpreted per-digit `%`/`//` "
              f"arithmetic at this scale. The int-only approach is still the correct answer "
              f"to the asked follow-up (no string conversion, O(1) extra space, no overflow "
              f"risk in fixed-width languages) -- this is a CPython constant-factor artifact, "
              f"not a complexity finding.")
    else:
        print(f"  measured: half-reversal is {full_ms / half_ms:.2f}x faster here.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
