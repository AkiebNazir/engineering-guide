"""
================================================================================
SOLUTION · LeetCode 172 · Factorial Trailing Zeroes                [Medium]
https://leetcode.com/problems/factorial-trailing-zeroes/
================================================================================

THE CORE IDEA
--------------
A trailing zero in `n!` comes from a factor of 10 = 2 x 5 in the product
`1 x 2 x 3 x ... x n`. Among the integers 1..n, factors of 2 are far more
abundant than factors of 5 (every 2nd number contributes at least one 2,
but only every 5th contributes a 5), so the number of available 5's is
ALWAYS the bottleneck -- there will never be a shortage of 2's to pair
with them. The answer is therefore just "how many times does 5 divide
into the product 1 x 2 x ... x n," counted correctly: multiples of 5
contribute one factor of 5 each, but multiples of 25 contribute a SECOND
factor of 5 (25 = 5x5), multiples of 125 a THIRD, and so on. So:

    trailing_zeroes(n) = floor(n/5) + floor(n/25) + floor(n/125) + ...

(the sum stops once `5^k > n`, since `floor(n / 5^k) = 0` past that
point). Crucially, none of this requires computing `n!` itself -- the
count is derived purely from n, never touching the astronomically large
factorial value.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (compute n! directly, then count trailing zeros on the
string/int, price it): `str(math.factorial(n)).rstrip('0')` length
difference, or repeatedly divide by 10 while divisible. Correct in
Python (arbitrary-precision ints), but `n!` grows FASTER than exponentially
-- `10000!` has over 35,000 digits -- so this approach does genuinely
enormous bignum multiplication work for no benefit whatsoever, purely to
extract a small integer answer. Kept as `_via_actual_factorial` below
strictly for a measured, honest demonstration of how impractical this
becomes even in a language with painless bignums.

Approach 1 (chosen) -- count factors of 5 directly via repeated division:
`count = 0; while n > 0: n //= 5; count += n`. This is the closed-form
sum `floor(n/5) + floor(n/25) + ...` computed iteratively (each loop
iteration computes the NEXT term by re-dividing the already-divided n,
which is equivalent to dividing the original n by the next power of 5).
O(log5 n) time, O(1) space -- and answers the follow-up's logarithmic-time
request directly.


================================================================================
STEP BY STEP TRACE
================================================================================
n = 30

    count = 0
    iter 1: n = 30 // 5 = 6;   count += 6  -> count = 6
            (this is floor(30/5) = 6: the multiples of 5 up to 30 are
             5,10,15,20,25,30 -- six of them, each contributing >=1 factor)
    iter 2: n = 6 // 5 = 1;    count += 1  -> count = 7
            (this is floor(30/25) = 1: only 25 is a multiple of 25 up to
             30, and it contributes a SECOND factor of 5 -- this iteration
             adds that extra one)
    iter 3: n = 1 // 5 = 0;    count += 0  -> count = 7
    loop ends (n == 0)

    trailingZeroes(30) = 7

    sanity check: 30! = 265252859812191058636308480000000, which indeed
    ends in exactly 7 zeros (count them: ...480000000 -- seven 0's).


n = 5

    count = 0
    iter 1: n = 5 // 5 = 1; count += 1 -> count = 1
    iter 2: n = 1 // 5 = 0; count += 0 -> count = 1
    loop ends. trailingZeroes(5) = 1

    sanity check: 5! = 120 -- exactly one trailing zero. Correct.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time         Space   Mutates input?
    -----------------------------------------------------------------------
    Compute n! then count zeros [priced]  O(n * M(n))* O(n)**    no
    Count factors of 5 [chosen]           O(log5 n)    O(1)      no

    *M(n) = cost of multiplying by the growing intermediate product,
    itself increasing as the factorial grows -- the true cost is
    super-linear in n and enormous in practice.
    **O(n) here refers to the number of DIGITS in n!, which itself grows
    faster than any polynomial in n (n! has roughly n*log10(n) digits).


================================================================================
EDGE CASES
================================================================================
    n == 0                -> 0! = 1, zero trailing zeros; the loop
                             (`while n > 0`) never executes, correctly
                             returning 0 without special-casing.
    n < 5                 -> e.g. n=1,2,3,4: no multiple of 5 exists in
                             1..n at all, so `n // 5 == 0` on the very
                             first iteration, loop body runs once (adding
                             0) then stops -- correctly returns 0.
    n exactly a power of 5,
    e.g. n=25, n=125       -> these are exactly the cases where the SECOND
                             (or third) term of the sum contributes a
                             nonzero amount beyond the naive "just count
                             multiples of 5" mistake -- the classic trap
                             this problem tests.
    largest n in range
    (n = 10^4)              -> still O(log5 10000) ~= 6 loop iterations;
                             confirms the approach is genuinely fast at
                             the upper bound, unlike computing 10000!
                             directly.
    no negative n           -> constraint guarantees n >= 0; factorial
                             and trailing-zero-count are undefined for
                             negative integers.


================================================================================
COMMON MISTAKES
================================================================================
1. Counting only `n // 5` and stopping there -- undercounts whenever n
   includes a multiple of 25 (or 125, ...), since those contribute MORE
   than one factor of 5 each. E.g. n=25 needs count=6 (5,10,15,20 give 1
   each = 4, plus 25 gives 2 = 6 total), but `25 // 5 = 5` alone is wrong.
2. Counting factors of 2 instead of (or in addition to) factors of 5 --
   factors of 2 are never the bottleneck since they're always more
   abundant; counting them is either redundant extra work or, if used
   AS the answer, an overcount.
3. Actually computing `n!` first (via `math.factorial(n)` or a manual
   loop) "to be safe" -- correct but wildly wasteful, exactly the trap
   the logarithmic-time follow-up is testing for; becomes impractically
   slow well before n reaches its stated upper bound of 10^4 in some
   languages, and even in Python it does unnecessary bignum work (see the
   runtime demo).
4. Off-by-one in the loop's termination -- forgetting that the loop must
   keep re-dividing the ALREADY-DIVIDED n (not the original n by 5, 25,
   125 separately recomputed) -- both are mathematically equivalent, but
   mixing the two implementations mid-loop is a common source of bugs.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Can you do this in O(log n) time?" -> Yes -- exactly what the chosen
  approach already is: at most log5(n) loop iterations.
- "What if the question asked for trailing zeros in base b instead of
  base 10?" -> Generalizes to: factor b into its prime factorization, find
  the prime factor whose count in n! is the bottleneck (the one with the
  largest prime, generally, since larger primes are rarer), and apply the
  same floor-division-sum technique for THAT prime's multiplicity in n!.
- "How would you count trailing zeros for n! where n itself could be
  astronomically large (e.g. 10^18)?" -> Same formula, same O(log5 n)
  loop -- it scales fine since each iteration only divides by 5, needing
  roughly log5(n) ~= 26 iterations even at n=10^18.


================================================================================
RELATED PROBLEMS
================================================================================
- Count Primes (LC 204, this topic, 008) -- another "count something
  about numbers up to n without brute-force per-number work" problem,
  solved by a sieve instead of a factor-counting formula.
- Preimage Size of Factorial Zeroes Function (LC 793) -- the INVERSE
  question: given a target trailing-zero count, how many n produce it
  (uses binary search over this same trailing-zero formula, since it's
  monotonically non-decreasing in n).
================================================================================
"""

import math
import sys
import time

# n=10000 makes n! a ~35,660-digit integer; str()/factorial() on numbers
# this large trip CPython's int<->str conversion guardrail (added in
# 3.11 to prevent DoS via huge integer formatting). Raising the limit here
# is deliberate and safe -- this file computes n! on purpose, specifically
# to measure how impractical that is, which is the whole point of the
# comparison below.
sys.set_int_max_str_digits(200_000)


class Solution:
    def trailingZeroes(self, n: int) -> int:
        count = 0
        while n > 0:
            n //= 5
            count += n
        return count


def _via_actual_factorial(n: int) -> int:
    """Priced-not-shipped alternative: actually compute n! (Python bignum),
    then count trailing zeros by repeated division. Used only for the
    measured comparison demo below."""
    fact = math.factorial(n)
    if fact == 0:
        return 0
    count = 0
    while fact % 10 == 0:
        fact //= 10
        count += 1
    return count


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        (3, 0),
        (5, 1),
        (0, 0),
        (1, 0),
        (4, 0),
        (10, 2),
        (25, 6),
        (30, 7),
        (100, 24),
        (125, 31),
        (10000, 2499),
    ]
    for n, expected in cases:
        got = sol.trailingZeroes(n)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  trailingZeroes({n}) -> {got} (expected {expected})")

    print()
    print("CROSS-CHECK -- factor-of-5 counting vs actual n! computation, n = 0..2000")
    print("-" * 72)
    mismatch = 0
    for n in range(0, 2001):
        a = sol.trailingZeroes(n)
        b = _via_actual_factorial(n)
        if a != b:
            mismatch += 1
            if mismatch <= 3:
                print(f"  FAIL example: n={n} -> formula={a}, actual={b}")
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {2001 - mismatch}/2001 agree ({mismatch} mismatches)")

    print()
    print("RUNTIME DEMO -- factor-of-5 formula vs computing n! directly, measured live")
    print("-" * 72)
    n = 10_000

    t0 = time.perf_counter()
    formula_result = sol.trailingZeroes(n)
    formula_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    actual_result = _via_actual_factorial(n)
    actual_ms = (time.perf_counter() - t0) * 1000

    digit_count = len(str(math.factorial(n)))
    print(f"n={n} (n! has {digit_count} digits):")
    print(f"  factor-of-5 formula (O(log5 n)): {formula_ms:8.4f} ms")
    print(f"  compute n! then count [priced]:  {actual_ms:8.2f} ms")
    speedup = actual_ms / formula_ms if formula_ms > 0 else float("inf")
    print(f"  measured: the formula is {speedup:.0f}x faster at n={n}, and the gap only widens as "
          f"n grows further, since n! itself grows faster than any polynomial while the formula "
          f"stays at ~log5(n) iterations.")
    demo_ok = formula_result == actual_result
    all_ok &= demo_ok
    print(f"{'PASS' if demo_ok else 'FAIL'}  both approaches agree on the result ({formula_result})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
