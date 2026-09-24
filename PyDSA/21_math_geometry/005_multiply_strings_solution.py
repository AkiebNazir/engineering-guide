"""
================================================================================
SOLUTION · LeetCode 43 · Multiply Strings                          [Medium]
https://leetcode.com/problems/multiply-strings/
================================================================================

THE CORE IDEA
--------------
Simulate grade-school long multiplication directly on the digit strings,
never converting either input to a native integer (the problem explicitly
bans it -- this is 002 Plus One's manual-carry discipline, extended from
addition to multiplication). Multiplying an m-digit number by an n-digit
number produces a result with AT MOST `m + n` digits -- never more, because
the largest possible m-digit number times the largest possible n-digit
number is less than `10^m * 10^n = 10^(m+n)`, which has exactly m+n
digits. So allocate a result array of size `m + n`, initialized to zero,
and for every pair of digit positions `(i, j)` (i in num1, j in num2, both
0-indexed from the LEFT), the product `num1[i] * num2[j]` contributes to
result positions `i + j` (the more-significant slot, taking the tens
place of the partial product) and `i + j + 1` (the less-significant
slot, taking the ones place) -- ACCUMULATE into both, then do a single
final carry-propagation pass left-to-right (well, right-to-left through
the digit array, same direction as 002) to resolve any position that
built up more than a single digit's worth from multiple contributions.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (native int conversion, price it -- and the problem explicitly
forbids it): `str(int(num1) * int(num2))`. Trivial in Python because ints
are arbitrary-precision; ZERO of the digit-array bookkeeping below is
needed. This is exactly why the problem bans it -- it sidesteps the
graded skill (manual big-number arithmetic) entirely. Kept here ONLY as
`_via_int_conversion` for an honest measured comparison, never as the
shipped answer.

Approach 1 (chosen) -- digit-array simulation of grade-school
multiplication: O(m*n) time (every digit pair is visited once), O(m+n)
space for the result array. This is the intended, and required, approach.


================================================================================
STEP BY STEP TRACE
================================================================================
num1 = "123", num2 = "45"     (123 * 45 = 5535)

    m = 3, n = 2. result = [0, 0, 0, 0, 0]  (size m+n = 5)

    i=2 (num1[2]='3'), j=1 (num2[1]='5'): 3*5=15
        pos i+j+1 = 4 (ones slot): result[4] += 15 -> result[4]=15
    i=2, j=0 (num2[0]='4'): 3*4=12
        pos i+j+1 = 3: result[3] += 12 -> result[3]=12
    i=1 (num1[1]='2'), j=1: 2*5=10
        pos i+j+1 = 3: result[3] += 10 -> result[3]=22
    i=1, j=0: 2*4=8
        pos i+j+1 = 2: result[2] += 8 -> result[2]=8
    i=0 (num1[0]='1'), j=1: 1*5=5
        pos i+j+1 = 2: result[2] += 5 -> result[2]=13
    i=0, j=0: 1*4=4
        pos i+j+1 = 1: result[1] += 4 -> result[1]=4

    raw accumulated result (before carry pass): [0, 4, 13, 22, 15]
    (positions can hold values >= 10 at this stage -- that's expected and
    resolved next, NOT an error)

    carry pass, right to left:
    pos 4: val=15 -> digit=15%10=5, carry=15//10=1; result[4]=5
    pos 3: val=22+1(carry)=23 -> digit=3, carry=2; result[3]=3
    pos 2: val=13+2=15 -> digit=5, carry=1; result[2]=5
    pos 1: val=4+1=5 -> digit=5, carry=0; result[1]=5
    pos 0: val=0+0=0 -> digit=0, carry=0; result[0]=0

    final array: [0, 5, 5, 3, 5] -> strip leading zero(s) -> "5535" -- correct.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time      Space     Mutates input?
    ---------------------------------------------------------------------
    Native int conversion [priced,
    forbidden by the problem]        O(m+n)*   O(m+n)     no
    Digit-array simulation [chosen]  O(m*n)    O(m+n)     no

    m, n = digit lengths of num1, num2. *Python's int() parsing and
    bignum multiplication are themselves sub-quadratic under the hood
    (Karatsuba-family algorithms for large enough operands) but this is
    irrelevant here since the problem forbids using them at all.


================================================================================
EDGE CASES
================================================================================
    num1 == "0" or num2 == "0"  -> product is "0"; the digit-array
                             approach naturally produces an all-zero
                             array, so the leading-zero-strip step must
                             stop at a SINGLE "0", not strip it down to an
                             empty string.
    both single-digit        -> e.g. "2" * "3" -> result array size 2,
                             smallest possible case, exercises the basic
                             loop with no carry chains needed.
    product needs the FULL
    m+n digits, e.g.
    "99" * "99" = "9801"     -> exactly 4 digits for two 2-digit inputs
                             (m+n=4), confirming the array is exactly
                             large enough, never one short.
    product needs FEWER than
    m+n digits, e.g.
    "10" * "10" = "100"      -> 3 digits, not 4 -- the leading-zero-strip
                             step is what handles this; the array is
                             ALWAYS allocated at size m+n but the leading
                             position is simply 0 whenever the true
                             product has fewer digits.
    very long inputs (up to
    200 digits each)          -> exactly why the O(m*n) digit-array
                             approach (40,000 digit-pairs worst case) is
                             the intended tool -- still fast, no need for
                             a fancier multiplication algorithm at this
                             problem's constraints.


================================================================================
COMMON MISTAKES
================================================================================
1. Reaching for `int(num1) * int(num2)` -- works in Python but violates
   the explicit constraint and defeats the point of the exercise (which is
   specifically to practice big-number arithmetic without a language's
   built-in bignum support).
2. Off-by-one in the position mapping -- using `i + j` for BOTH digits of
   the partial product (instead of `i+j` for the carry-out position and
   `i+j+1` for the units position) collapses two distinct result slots
   into one and produces a wrong, too-small result.
3. Forgetting the final carry-propagation pass -- treating each
   accumulated `result[k]` as already a single valid digit (it can be
   anywhere from 0 to 81*min(m,n)-ish before the carry pass resolves it)
   produces a string with values outside 0-9 baked in.
4. Stripping ALL leading zeros including the very last remaining digit --
   turning a genuine `"0"` product into an empty string; must stop
   stripping once only one digit (possibly "0") remains.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Can you avoid the O(m*n) blowup for very large numbers?" -> Yes,
  Karatsuba's algorithm reduces multiplication to roughly O(n^1.585) by
  recursively splitting each number in half and combining three
  sub-products instead of four -- overkill for this problem's 200-digit
  cap, but the right answer if asked "what if these were 100,000 digits."
- "Why is m+n always enough digits, never m+n+1?" -> The maximum possible
  m-digit number is `10^m - 1`, and the maximum n-digit number is `10^n -
  1`; their product is strictly less than `10^m * 10^n = 10^(m+n)`, which
  has exactly m+n digits -- so m+n digits always suffice, and the array
  size never needs adjusting after the fact.
- "How would this change for addition instead of multiplication?" -> That's
  2 Plus One / Add Binary's simpler single-pass carry, since each digit
  position only ever receives contributions from ONE pair of aligned
  digits (plus a carry), not from up to `min(m,n)` different pairs.


================================================================================
RELATED PROBLEMS
================================================================================
- Plus One (LC 66, this topic, 002) -- the addition analog of this exact
  manual-digit-arithmetic discipline.
- Add Strings (LC 415) -- string addition without built-in bignums, a
  strict subset of this problem's technique.
- Karatsuba's algorithm (classic divide & conquer, not on LeetCode as a
  standalone problem) -- the asymptotically better multiplication method
  referenced in the follow-up above.
================================================================================
"""

import random
import time


class Solution:
    def multiply(self, num1: str, num2: str) -> str:
        if num1 == "0" or num2 == "0":
            return "0"

        m, n = len(num1), len(num2)
        result = [0] * (m + n)

        for i in range(m - 1, -1, -1):
            d1 = ord(num1[i]) - ord("0")
            for j in range(n - 1, -1, -1):
                d2 = ord(num2[j]) - ord("0")
                # partial product lands split across (i+j) and (i+j+1)
                # in the LEFT-indexed result array (index 0 is most
                # significant). Using left-to-right digit indices i, j
                # directly, the units digit of this pair's contribution
                # goes to position i+j+1 and any tens-carry to i+j.
                total = result[i + j + 1] + d1 * d2
                result[i + j + 1] = total % 10
                result[i + j] += total // 10

        # strip leading zeros, but keep at least one digit
        start = 0
        while start < len(result) - 1 and result[start] == 0:
            start += 1
        return "".join(map(str, result[start:]))


def _via_int_conversion(num1: str, num2: str) -> str:
    """Forbidden-by-the-problem alternative, kept only for the measured
    comparison / cross-check demo below."""
    return str(int(num1) * int(num2))


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        ("2", "3", "6"),
        ("123", "456", "56088"),
        ("0", "12345", "0"),
        ("12345", "0", "0"),
        ("0", "0", "0"),
        ("99", "99", "9801"),
        ("10", "10", "100"),
        ("1", "1", "1"),
        ("123", "45", "5535"),
        ("999", "999", "998001"),
    ]
    for a, b, expected in cases:
        got = sol.multiply(a, b)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  multiply({a!r}, {b!r}) -> {got!r} (expected {expected!r})")

    print()
    print("CROSS-CHECK -- digit-array simulation vs int conversion, 2000 random pairs")
    print("-" * 72)
    random.seed(17)
    mismatch = 0
    for _ in range(2000):
        len1, len2 = random.randint(1, 25), random.randint(1, 25)
        a = "".join(str(random.randint(0, 9)) for _ in range(len1)).lstrip("0") or "0"
        b = "".join(str(random.randint(0, 9)) for _ in range(len2)).lstrip("0") or "0"
        got = sol.multiply(a, b)
        expected = _via_int_conversion(a, b)
        if got != expected:
            mismatch += 1
            if mismatch <= 3:
                print(f"  FAIL example: {a} * {b} -> got {got}, expected {expected}")
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {2000 - mismatch}/2000 agree ({mismatch} mismatches)")

    print()
    print("RUNTIME DEMO -- digit-array simulation vs native int conversion, measured live")
    print("-" * 72)
    random.seed(23)
    trials = 20_000
    pairs = []
    for _ in range(trials):
        a = "".join(str(random.randint(0, 9)) for _ in range(random.randint(50, 200))).lstrip("0") or "0"
        b = "".join(str(random.randint(0, 9)) for _ in range(random.randint(50, 200))).lstrip("0") or "0"
        pairs.append((a, b))

    t0 = time.perf_counter()
    for a, b in pairs:
        sol.multiply(a, b)
    array_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    for a, b in pairs:
        _via_int_conversion(a, b)
    int_ms = (time.perf_counter() - t0) * 1000

    print(f"{trials} pairs of 50-200 digit numbers:")
    print(f"  digit-array simulation (required by the problem): {array_ms:8.2f} ms")
    print(f"  native int() conversion (forbidden by the problem): {int_ms:8.2f} ms")
    if int_ms < array_ms:
        print(f"  measured honestly: native int conversion is {array_ms / int_ms:.2f}x FASTER "
              f"here -- CPython's C-level bignum multiplication (which itself uses a "
              f"Karatsuba-family algorithm for large operands) beats the pure-Python O(m*n) "
              f"digit-array simulation. This is expected and does not change the answer: the "
              f"problem explicitly requires the manual approach, and this measurement exists "
              f"only to be honest about which is actually faster on this machine, not to argue "
              f"for using the forbidden approach.")
    else:
        print(f"  measured: digit-array simulation is {int_ms / array_ms:.2f}x faster here.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
