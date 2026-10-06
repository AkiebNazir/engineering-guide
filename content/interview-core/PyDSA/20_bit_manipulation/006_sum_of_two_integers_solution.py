"""
================================================================================
SOLUTION · LeetCode 371 · Sum of Two Integers                        [Medium]
https://leetcode.com/problems/sum-of-two-integers/
================================================================================

THE CORE IDEA
--------------
Addition decomposes into two bitwise parts: XOR gives the sum of each bit
pair IGNORING carry, and `(a & b) << 1` gives exactly the carry that
addition would generate at each position. Feed the carry back in as the
new `b` and repeat until there's no carry left:

    while b != 0:
        carry = (a & b) << 1
        a = a ^ b
        b = carry
    return a

In a language with a real fixed-width int (C, Java, Go), this loop is
GUARANTEED to terminate: b's magnitude only ever shrinks or wraps, because
overflow past bit 31 is silently discarded by the hardware. In Python,
there is no such floor -- ints are arbitrary precision, so `(a & b) << 1`
on two negative Python ints (which are conceptually an INFINITE string of
leading 1-bits) can keep generating new 1-bits in an ever-growing negative
direction FOREVER. Masking every intermediate result to exactly 32 bits
with `& 0xFFFFFFFF` is not an optional nicety here -- it's the only thing
that makes the loop terminate at all when either input is negative.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (just use `+`, name it and reject it): the problem explicitly
forbids `+` and `-` -- not a real option, but worth stating why the
exercise exists: it's testing whether you understand how a CPU's adder
circuit actually works (half-adder = XOR + AND-carry, full-adder chains
those).

Approach 1 (unmasked bitwise loop) -- textbook-correct in C/Java where
ints are fixed-width and self-limiting. In Python: WRONG the moment
either input is negative, because there is no wraparound to force
termination. Demonstrated failing live below.

Approach 2 (masked bitwise loop, with sign fix-up at the end) [chosen] --
mask `a`, `b`, and `carry` to `& 0xFFFFFFFF` after every step, forcing the
loop to behave as if it were running on a real 32-bit register. At the
end, `a` holds an UNSIGNED 32-bit pattern; if bit 31 is set, reinterpret
it as the Python negative int it represents: `a - (1 << 32)`. O(1) time
(bounded by 32 bits), O(1) space, and terminates correctly for every
input in the problem's range.

Approach 3 (Python's own `+`, for comparison only) -- O(1), trivially
correct, but not a legal solution to the stated problem. Included only
as an oracle to check approach 2 against.


================================================================================
STEP BY STEP TRACE
================================================================================
a = -2, b = -3   (want -5)

Represented as 32-bit two's complement (masked):
    a = 0b11111111111111111111111111111110  (0xFFFFFFFE)
    b = 0b11111111111111111111111111111101  (0xFFFFFFFD)

Iteration 1:
    carry = (a & b) << 1 & MASK
          = 0b111...11100 << 1 & MASK = 0b111...111000  masked to 32 bits
    a = (a ^ b) & MASK = 0b00000000000000000000000000000011 (=3)
    b = carry

... (several more iterations, each shrinking b's "active" bit range) ...

Eventually b becomes 0, and a holds the 32-bit pattern for -5:
    a = 0b11111111111111111111111111111011  (0xFFFFFFFB)

Bit 31 of a is set (a >= 0x80000000), so reinterpret as negative:
    result = a - (1 << 32) = 4294967291 - 4294967296 = -5   <- matches


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time   Space   Mutates input?
    ---------------------------------  -----  ------  --------------
    Unmasked bitwise loop              N/A*   O(1)    no
    Masked bitwise loop [chosen]       O(1)   O(1)    no
    Python's `+` (oracle only)         O(1)   O(1)    no

    * "N/A" because on negative Python inputs the unmasked loop does not
      reliably terminate at all -- there is no valid time complexity for
      a loop that may run forever.


================================================================================
EDGE CASES
================================================================================
    both operands 0             -> loop never runs (b starts at 0), a=0
                                    already unsigned-safe, returns 0.
    result is exactly 0 from two
    nonzero opposite values     -> e.g. a=-1, b=1: the masked loop
                                    converges to a 32-bit all-zero pattern,
                                    bit 31 is NOT set, no sign fix-up
                                    needed, returns 0 directly.
    both operands negative       -> THE case that breaks the unmasked
                                    version outright (see live demo). The
                                    masked version handles it via the
                                    final bit-31 sign check.
    sum would need the full
    32-bit signed range          -> constraints cap |a|,|b| <= 1000, so
                                    the sum can never approach INT_MAX/MIN
                                    boundaries here, but the masking logic
                                    itself is written to be correct at
                                    those boundaries regardless (it's not
                                    tuned to this problem's narrow range).
    a and b already both positive -> masked loop still works: masking a
                                    non-negative Python int to 32 bits
                                    that already fits is a no-op, and bit
                                    31 stays clear, so no sign fix-up
                                    fires. The masking discipline doesn't
                                    change behavior on the "easy" inputs.


================================================================================
COMMON MISTAKES
================================================================================
1. THE headline mistake: writing the textbook C/Java bitwise-add loop
   verbatim in Python with no masking at all. It works on small positive
   inputs (accidentally, because small positives never trigger Python's
   unbounded-negative-carry behavior) and then hangs or misbehaves the
   moment either input is negative. Demonstrated live below with a
   bounded-iteration guard so the demo itself doesn't actually hang.

2. Masking `a` and `b` inside the loop but forgetting to mask `carry`
   itself before assigning it to `b` -- the carry computation `(a & b) <<
   1` can still produce a value wider than 32 bits even when `a` and `b`
   are individually masked, since the `<< 1` adds a bit. Every
   intermediate value needs the mask, not just the loop inputs.

3. Forgetting the FINAL sign fix-up. After the loop, `a` is guaranteed to
   be a 32-bit UNSIGNED pattern (0 to 0xFFFFFFFF) even when the true
   mathematical result is negative -- returning it as-is for e.g. -5
   would give 4294967291, a huge wrong-signed positive number. Must check
   bit 31 and subtract `1 << 32` if set.

4. Using `~(a ^ 0xFFFFFFFF)` for the sign fix-up but forgetting Python's
   `~x` is `-x - 1` on the ALREADY-reinterpreted value, not on the raw
   masked pattern -- easy to get an off-by-one here. `a - (1 << 32)` is
   the more directly reasoned version and is what this solution uses.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why does this problem even need special handling in Python but not in
   Java or C++?
A: Because Java/C++ `int` is a REAL fixed-width 32-bit type -- overflow
   silently wraps at the hardware level, so the naive bitwise loop is
   automatically correct and automatically terminates. Python ints have
   no width at all; the algorithm has to manually simulate the 32-bit
   register Java/C++ get for free.

Q: How would you extend this to 64-bit integers?
A: Change every `0xFFFFFFFF` to `0xFFFFFFFFFFFFFFFF` (64 one-bits) and
   the sign-check threshold from `1 << 31` to `1 << 63`, and the
   subtraction from `1 << 32` to `1 << 64`. Same algorithm, wider mask.

Q: Can you do subtraction the same way, without `-`?
A: Yes -- `a - b == a + (~b + 1)` (two's complement negation), so
   subtraction is just `getSum(a, getSum(~b, 1))`, reusing this exact
   function twice.

Q: What's the actual hardware analog?
A: This loop IS a ripple-carry adder, unrolled in software: XOR is each
   bit position's half-adder sum, `(a&b)<<1` is the carry rippling to the
   next position, and the loop terminates when the carry chain dies out
   -- identical to how a real adder circuit settles.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 7    Reverse Integer            (007 -- same masking discipline, for
                                          digit reversal + overflow detection)
    LC 190  Reverse Bits               (004 -- same 32-bit-width discipline,
                                          for a read-only reversal instead of
                                          an arithmetic loop that can hang)
    LC 67   Add Binary                 (same ripple-carry idea, over strings)
    LC 415  Add Strings                (decimal analog of manual carry logic)
================================================================================
"""

import time


MASK32 = 0xFFFFFFFF
SIGN_BIT = 1 << 31
WIDTH = 1 << 32


class Solution:
    def getSum(self, a: int, b: int) -> int:
        """✅ Masked bitwise ripple-carry loop. O(1) time, O(1) space."""
        a &= MASK32
        b &= MASK32
        while b != 0:
            carry = ((a & b) << 1) & MASK32
            a = (a ^ b) & MASK32
            b = carry
        # a is now an UNSIGNED 32-bit pattern; reinterpret as signed.
        if a & SIGN_BIT:
            return a - WIDTH
        return a

    def getSum_unmasked_UNSAFE(self, a: int, b: int, max_iters: int = 200) -> tuple:
        """Textbook C/Java loop with NO masking. In Python this can fail
        to terminate on negative inputs. `max_iters` is a safety guard so
        the demo below doesn't actually hang -- returns
        (converged: bool, value_or_None, iterations_run)."""
        iters = 0
        while b != 0 and iters < max_iters:
            carry = (a & b) << 1
            a = a ^ b
            b = carry
            iters += 1
        return (b == 0, a if b == 0 else None, iters)


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        (1, 2, 3),
        (2, 3, 5),
        (-1, 1, 0),
        (-2, -3, -5),
        (0, 0, 0),
        (-1000, 1000, 0),
        (1000, 1000, 2000),
        (-5, -7, -12),
    ]
    print("--- correctness: masked bitwise sum vs Python's own + ---")
    for a, b, want in cases:
        got = sol.getSum(a, b)
        oracle = a + b
        ok = got == want == oracle
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  a={a:>6} b={b:>6}  -> {got:>6}  (want {want})")

    # ------------------------------------------------------------------
    # LIVE BUG DEMO: the unmasked textbook loop on two negative Python
    # ints. Guarded with max_iters so the demo itself terminates; the
    # point is to show it does NOT converge within a generous iteration
    # budget, unlike a real 32-bit machine where it always converges in
    # well under 32 iterations.
    # ------------------------------------------------------------------
    print("\n--- DEMO: unmasked loop fails to converge on opposite-sign Python ints ---")
    a, b = 1, -1
    converged, value, iters = sol.getSum_unmasked_UNSAFE(a, b, max_iters=200)
    print(f"  Unmasked loop on getSum({a}, {b}), capped at 200 iterations:")
    print(f"    converged={converged}  iterations_run={iters}  "
          f"value={'N/A (still carrying)' if value is None else value}")
    print(f"  Trace of the first few iterations (a, b) shows WHY: b DOUBLES "
          f"every step instead of shrinking (-2,2 -> -4,4 -> -8,8 -> ...), "
          f"because Python's infinite-precision negative ints never let the "
          f"carry 'fall off the top' the way a real 32-bit register would.")
    masked_result = sol.getSum(a, b)
    print(f"  Masked version: getSum({a}, {b}) = {masked_result} (correct, want 0)")
    bug_demonstrated = (not converged) and (masked_result == 0)
    all_ok &= bug_demonstrated

    # ------------------------------------------------------------------
    # RUNTIME DEMO: masked loop converges in a small, bounded number of
    # iterations across a spread of inputs -- confirms the O(1)-bounded
    # claim with a real measurement.
    # ------------------------------------------------------------------
    print("\n--- DEMO: masked loop iteration count stays bounded (<=32) ---")
    import random
    random.seed(5)
    max_seen = 0
    t0 = time.perf_counter()
    for _ in range(200_000):
        x = random.randint(-1000, 1000)
        y = random.randint(-1000, 1000)
        aa, bb = x & MASK32, y & MASK32
        n = 0
        while bb != 0:
            carry = ((aa & bb) << 1) & MASK32
            aa = (aa ^ bb) & MASK32
            bb = carry
            n += 1
        max_seen = max(max_seen, n)
    t_elapsed = time.perf_counter() - t0
    print(f"  200,000 random (a,b) pairs in [-1000,1000]: max iterations "
          f"seen = {max_seen} (<=32 confirms the O(1) bound)")
    print(f"  total time: {t_elapsed * 1000:8.2f} ms")
    all_ok &= (max_seen <= 32)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
