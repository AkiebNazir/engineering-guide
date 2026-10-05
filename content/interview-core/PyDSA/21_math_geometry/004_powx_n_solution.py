"""
================================================================================
SOLUTION · LeetCode 50 · Pow(x, n)                                  [Medium]
https://leetcode.com/problems/powx-n/
================================================================================

THE CORE IDEA
--------------
Computing `x^n` by multiplying x by itself n-1 times is O(n). Binary
(fast) exponentiation gets it down to O(log n) by halving the exponent
each step instead of decrementing it by one:

    x^n = (x^(n/2))^2                  if n is even
    x^n = x * (x^((n-1)/2))^2          if n is odd

This is the SAME "throw away half the remaining work every round" idea as
**topic 05's binary search** -- binary search halves the search space by
COMPARISON, this halves the exponent by ARITHMETIC (repeated squaring),
but both turn a linear-in-n process into a logarithmic one by discarding
half of what's left at every step instead of processing it one unit at a
time.

Negative exponents reduce to the positive case: `x^-n = 1 / x^n`. This
must be handled BEFORE recursing (or at the top of the iterative loop),
not folded into the recursion itself, because flipping the sign changes
the final operation (a division) rather than the recursive structure.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive loop, price it): multiply x by itself n times in a
straight loop (`result = 1; for _ in range(n): result *= x`). Correct,
O(n) time. This is the approach fast exponentiation is explicitly designed
to beat, and the gap is measured below at a large n.

Approach 1 (chosen) -- binary exponentiation, implemented both ways:
  1a. RECURSIVE: `myPow(x, n) = myPow(x*x, n//2)` if even, else
      `x * myPow(x*x, n//2)` if odd (using integer floor division
      throughout, careful with negative n as described above). O(log n)
      time, O(log n) space for the recursion stack.
  1b. ITERATIVE: same halving logic unrolled into a `while n > 0` loop
      that accumulates a `result` factor whenever the current bit of n is
      1, and squares a running `base` each iteration -- this is literally
      "binary exponentiation via the binary representation of n": each bit
      of n, from least to most significant, decides whether the current
      power-of-two power of x gets folded into the answer. O(log n) time,
      O(1) space -- the version to reach for when the interviewer asks for
      the space-optimized follow-up.

The shipped `myPow` uses the iterative version (no recursion-depth
concerns, O(1) space); the recursive version is kept as
`_myPow_recursive` for the trace and the complexity-table entry.


================================================================================
STEP BY STEP TRACE
================================================================================
x = 2.0, n = 10 (iterative version)

    n is positive, no sign flip needed. base=2.0, result=1.0, n=10

    n=10 (even, bit=0): base = base*base = 4.0;  n //= 2 -> 5
    n=5  (odd,  bit=1): result *= base -> result = 1.0*4.0 = 4.0
                        base = base*base = 16.0; n //= 2 -> 2
    n=2  (even, bit=0): base = base*base = 256.0; n //= 2 -> 1
    n=1  (odd,  bit=1): result *= base -> result = 4.0*256.0 = 1024.0
                        base = base*base = 65536.0; n //= 2 -> 0
    n=0: loop ends.

    result = 1024.0  (matches 2^10 = 1024, and only 4 squarings + 2
    multiplications were needed instead of 9 sequential multiplications)


x = 2.0, n = -2

    n < 0 -> compute positive case for n=2, then invert:
    x^2 = 4.0  -> result = 1 / 4.0 = 0.25


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time         Space       Mutates input?
    ------------------------------------------------------------------
    Naive loop [priced]         O(n)         O(1)          no
    Recursive binary exp        O(log n)     O(log n)      no
    Iterative binary exp        O(log n)     O(1)          no
                                              (chosen)


================================================================================
EDGE CASES
================================================================================
    n == 0                -> x^0 = 1 for any x (including x == 0, by the
                             problem's convention); must be handled as an
                             immediate base case, not fall through into a
                             loop that never runs and returns garbage.
    n < 0                 -> x^n = 1 / x^(-n); must flip BEFORE processing,
                             and note `-n` on the most negative possible
                             32-bit int (`n == -2**31`) would overflow a
                             fixed-width negation in C/Java/Go -- solved
                             there by widening to a 64-bit accumulator
                             before negating. Python ints don't overflow,
                             so this specific bug can't manifest here, but
                             it's a genuine correctness edge in a fixed-
                             width language and worth naming.
    x == 0.0, n > 0        -> 0^n = 0 for positive n; handled correctly by
                             the general algorithm without a special case
                             (0 squared is still 0).
    x == 0.0, n < 0        -> mathematically undefined (division by zero);
                             LeetCode's constraints guarantee this case
                             doesn't appear in test input, but a defensive
                             implementation could raise or guard explicitly.
    x == 1.0 or x == -1.0  -> result is always +/-1 regardless of |n|;
                             correctly handled by the general algorithm,
                             good sanity check since no squaring changes
                             the magnitude.
    very large |n|          -> exactly the case the O(log n) approach is
                             for; a naive loop becomes noticeably slow well
                             before a machine's patience runs out, the
                             binary approach stays fast (measured below).


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting to handle negative n before recursing -- naive translations
   of the recurrence sometimes try to recurse on a negative n directly,
   which either infinite-loops or produces wrong results since the
   even/odd halving logic assumes n >= 0.
2. Using `n % 2` to test parity on a NEGATIVE n without first normalizing
   sign -- in some languages `%` on negative n returns a negative
   remainder, silently breaking the even/odd branch; sidestepped entirely
   here by flipping sign to positive first.
3. Off-by-one in the odd case -- writing `x^n = (x^(n//2))^2` for ODD n
   without also multiplying by the leftover `x` factor undercounts by
   exactly one factor of x (since `n // 2` truncates, `2 * (n//2) != n`
   when n is odd).
4. Recomputing `x^(n//2)` TWICE instead of computing it once and squaring
   it -- this silently degrades the algorithm back to O(n) (or worse,
   exponential, if done naively via naive recursion without memoization),
   defeating the entire point of the halving trick.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Can you do it without recursion?" -> Yes, the iterative bit-by-bit
  version above, O(1) space instead of O(log n) recursion stack.
- "What if x and n were both very large, and precision mattered?" -> Floats
  accumulate rounding error over repeated squaring; for exact large-integer
  powers you'd want integer-only arithmetic (Python's arbitrary-precision
  ints handle this natively; `pow(x, n)` with integers has no float error).
- "How does this relate to matrix exponentiation (e.g. computing Fibonacci
  in O(log n))?" -> Same halving trick, generalized: repeated squaring
  works for ANY associative operation with an identity element, not just
  scalar multiplication -- matrix multiplication qualifies, which is how
  `fib(n)` is computed in O(log n) via matrix power.


================================================================================
RELATED PROBLEMS
================================================================================
- Binary Search family (topic 05) -- same "halve and discard" mechanism,
  different operation (comparison vs. multiplication).
- Sqrt(x) (LC 69) -- another numeric problem solvable via a similar
  halving/binary-search-on-the-answer idea.
- Super Pow (LC 372) -- extends this exact technique to exponents given as
  huge digit arrays, computed modulo a fixed base.
================================================================================
"""

import time


class Solution:
    def myPow(self, x: float, n: int) -> float:
        if n < 0:
            x = 1 / x
            n = -n

        result = 1.0
        base = x
        while n > 0:
            if n & 1:  # current bit is 1 -- fold this power-of-two power of x in
                result *= base
            base *= base
            n >>= 1
        return result


def _myPow_recursive(x: float, n: int) -> float:
    """Recursive variant, O(log n) time, O(log n) recursion-stack space."""
    if n < 0:
        return 1 / _myPow_recursive(x, -n)
    if n == 0:
        return 1.0
    half = _myPow_recursive(x, n // 2)
    if n % 2 == 0:
        return half * half
    return x * half * half


def _naive_pow(x: float, n: int) -> float:
    """O(n) alternative, priced but not shipped, used only for comparison."""
    if n < 0:
        x = 1 / x
        n = -n
    result = 1.0
    for _ in range(n):
        result *= x
    return result


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        (2.0, 10, 1024.0),
        (2.1, 3, 9.261),
        (2.0, -2, 0.25),
        (2.0, 0, 1.0),
        (0.0, 5, 0.0),
        (1.0, 12345, 1.0),
        (-1.0, 7, -1.0),
        (-1.0, 8, 1.0),
        (-2.0, 3, -8.0),
        (0.00001, 2147483647, 0.0),
    ]
    for x, n, expected in cases:
        got = sol.myPow(x, n)
        ok = abs(got - expected) < 1e-6 if expected != 0.0 else abs(got) < 1e-100
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  myPow({x}, {n}) -> {got} (expected ~{expected})")

    print()
    print("CROSS-CHECK -- iterative vs recursive vs naive, 1000 random (x, n) pairs")
    print("-" * 72)
    import random
    random.seed(5)
    mismatch = 0
    for _ in range(1000):
        x = random.uniform(0.5, 2.0)
        n = random.randint(-30, 30)
        a = sol.myPow(x, n)
        b = _myPow_recursive(x, n)
        c = _naive_pow(x, n)
        if not (abs(a - b) < 1e-6 and abs(a - c) < 1e-6):
            mismatch += 1
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {1000 - mismatch}/1000 agree ({mismatch} mismatches)")

    print()
    print("RUNTIME DEMO -- binary exponentiation vs naive O(n) loop, measured live")
    print("-" * 72)
    n_exp = 5_000_000
    x = 1.0000001

    t0 = time.perf_counter()
    fast_result = sol.myPow(x, n_exp)
    fast_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    naive_result = _naive_pow(x, n_exp)
    naive_ms = (time.perf_counter() - t0) * 1000

    print(f"x={x}, n={n_exp}:")
    print(f"  binary exponentiation (O(log n)): {fast_ms:8.4f} ms  -> {fast_result:.6f}")
    print(f"  naive loop (O(n)):                {naive_ms:8.2f} ms  -> {naive_result:.6f}")
    speedup = naive_ms / fast_ms if fast_ms > 0 else float("inf")
    print(f"  measured: binary exponentiation is {speedup:.0f}x faster at n={n_exp}, "
          f"confirming O(log n) vs O(n) at scale.")
    demo_ok = abs(fast_result - naive_result) < 1e-3
    all_ok &= demo_ok
    print(f"{'PASS' if demo_ok else 'FAIL'}  both approaches agree on the result")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
