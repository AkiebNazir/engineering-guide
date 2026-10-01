"""
================================================================================
SOLUTION · LeetCode 190 · Reverse Bits                               [Easy]
https://leetcode.com/problems/reverse-bits/
================================================================================

THE CORE IDEA
--------------
Extract each of the 32 input bits one at a time and place it at its
MIRRORED position in the output:

    result = 0
    for i in range(32):
        bit = (n >> i) & 1          # bit i of n, isolated
        result |= bit << (31 - i)   # place it at position 31-i
    return result

O(32) = O(1) time, O(1) space. The "reverse" is entirely in the index
mapping `i -> 31 - i`; nothing else about the loop changes.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force via string, name it and consider it): convert to a
32-char binary string with `format(n, '032b')`, reverse the string with
Python slicing (`s[::-1]`), parse back with `int(s, 2)`. Also O(32) and
arguably simpler -- BUT it's a masking trap in disguise: if the caller
ever hands you a value that ISN'T already guaranteed non-negative (e.g. a
raw negative int meant to represent a 32-bit two's-complement pattern,
which the problem statement explicitly says can happen conceptually --
see the Java note), `bin(n)` or `format(n, 'b')` on a negative n produces
a signed representation with a MINUS SIGN, not a 32-bit pattern, and the
whole string approach silently breaks. Demonstrated live below.

Approach 1 (bit-by-bit shift-and-place) [chosen] -- O(32) time, O(1)
space, and works correctly regardless of how n got produced, PROVIDED n
is masked to `& 0xFFFFFFFF` first to guarantee it's read as an unsigned
32-bit pattern (this problem's LeetCode signature already guarantees
that, but the discipline is what generalizes -- see 006/007 where you
must mask a Python int that legitimately IS negative).

Approach 2 (divide-and-conquer bit-swap, "SWAR" trick) -- swap 16-bit
halves, then 8-bit, 4-bit, 2-bit, 1-bit halves using precomputed masks
(e.g. `0x55555555`, `0x33333333`, ...). O(log 32) = O(5) mask-and-shift
operations instead of O(32) loop iterations -- the answer to the "called
many times" follow-up, since it does a fixed constant number of O(1)
machine-word ops instead of 32 loop iterations.

Approach 3 (memoize by byte) -- precompute the bit-reversal of every
8-bit byte (256 entries) once, then reverse a 32-bit int by reversing its
4 bytes and reassembling in swapped order. O(1) amortized per call after
O(256) one-time setup -- the practical answer to "called many times."


================================================================================
STEP BY STEP TRACE
================================================================================
n = 0b00000000000000000000000000001011   (11, using only the low 4 bits
                                            for a readable trace)

    i=0: bit=(n>>0)&1=1  -> result |= 1<<31  -> result=0b10000000000000000000000000000000
    i=1: bit=(n>>1)&1=1  -> result |= 1<<30  -> result=0b11000000000000000000000000000000
    i=2: bit=(n>>2)&1=0  -> nothing changes
    i=3: bit=(n>>3)&1=1  -> result |= 1<<28  -> result=0b11010000000000000000000000000000
    i=4..31: all remaining bits of n are 0 -> nothing more changes

    Final result = 0b11010000000000000000000000000000 = 3489660928

    Sanity check: n's low 4 bits 1011 became the result's HIGH 4 bits
    1101 -- reversed, exactly as required (1011 reversed IS 1101).


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time       Space   Mutates input?
    ------------------------------  ---------  ------  --------------
    String reverse (bin/format)     O(32)      O(32)   no
    Bit-by-bit shift-place [chosen] O(32)      O(1)    no
    SWAR mask-swap (log2(32)=5 ops) O(1)       O(1)    no
    Byte-lookup table (256 entries) O(1)*      O(256)  no

    * O(1) amortized per call after a one-time O(256) table build --
      the right answer to "called many times."


================================================================================
EDGE CASES
================================================================================
    n == 0                    -> every bit is 0, reversal is 0. No bit
                                  ever gets set in result.
    n == all 1s (2^32 - 1)    -> reversal is still all 1s -- a useful
                                  sanity check since the "shape" is
                                  symmetric even though every individual
                                  bit moved.
    n == 1 (only bit 0 set)   -> reverses to bit 31 set, i.e. 2^31 --
                                  the maximum possible single-bit output,
                                  confirming the mirrored-index math
                                  (31 - 0 = 31).
    result would look "negative" as a signed 32-bit value (top bit set)
                               -> irrelevant in Python -- ints are
                                  arbitrary precision, so a value with bit
                                  31 set is just a large positive int, not
                                  a negative one. LeetCode's Python judge
                                  expects exactly that (contrast with a
                                  language that has a true int32 type).


================================================================================
COMMON MISTAKES
================================================================================
1. Reversing via `bin(n)[2:].zfill(32)[::-1]` without ever validating that
   `n >= 0` first. If n could legitimately be a raw negative Python int
   representing a 32-bit two's-complement pattern (the scenario the
   problem's own Java note describes), `bin(-3)` is `'-0b11'` -- the
   leading `'-'` sign corrupts the whole string pipeline. Demonstrated
   live below: reversing -3 (meant as the 32-bit pattern for the input in
   example 2) via the naive string method throws or silently produces
   garbage, while masking with `& 0xFFFFFFFF` first fixes it.

2. Placing the extracted bit at position `i` instead of `31 - i` -- that's
   just a no-op copy, not a reversal. The mirrored index IS the entire
   algorithm; get it backwards and every test still "runs," it just
   returns nonsense.

3. Using `31 - i` but iterating i from 1 to 32 instead of 0 to 31 (an
   off-by-one on the loop bound) -- either drops bit 0 of the input or
   reads one bit past position 31, corrupting the result silently since
   Python ints don't raise on out-of-range shifts.

4. Assuming this problem's O(1) space bound is violated by using an int
   accumulator -- it isn't; a single Python int is O(1) space regardless
   of how many bits are logically "in play," since 32 bits is a fixed
   small constant here.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: "If this function is called many times, how would you optimize it?"
A: Precompute a reversed-byte lookup table for all 256 possible byte
   values once, then reverse a 32-bit int by looking up each of its 4
   bytes and reassembling them in reverse BYTE order (not just reverse
   bit order per byte -- both matter). O(1) amortized per call. See
   Approach 3.

Q: How does this relate to Reverse Integer (007)?
A: Both fix a 32-bit width and must respect it, but 007 reverses DECIMAL
   digits and must detect signed 32-bit overflow (raising if the result
   doesn't fit), while 004 reverses BITS and the result is defined to
   always fit in 32 bits by construction -- no overflow check needed here.

Q: What if the width were 64 instead of 32?
A: Change every `31` to `63` and the loop bound to `range(64)` -- the
   algorithm is otherwise identical; only the fixed width constant moves.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 7    Reverse Integer          (007 -- reverses DIGITS, needs overflow
                                        detection, same topic-defining masking
                                        discipline)
    LC 371  Sum of Two Integers      (006 -- same 32-bit masking discipline,
                                        applied to addition via bit ops)
    LC 191  Number of 1 Bits         (002 -- same 32-bit input, no masking
                                        needed because it's read-only)
================================================================================
"""

import time


class Solution:
    def reverseBits(self, n: int) -> int:
        """✅ Bit-by-bit shift-and-place. O(32)=O(1) time, O(1) space."""
        result = 0
        for i in range(32):
            bit = (n >> i) & 1
            result |= bit << (31 - i)
        return result

    def reverseBits_swar(self, n: int) -> int:
        """Alternative: SWAR mask-and-swap, O(1) fixed 5 operations
        instead of 32 loop iterations -- the answer to "called many
        times." All masks below assume n is already a 32-bit unsigned
        pattern (LeetCode guarantees this for the Python signature)."""
        n = ((n & 0xFFFF0000) >> 16) | ((n & 0x0000FFFF) << 16)
        n = ((n & 0xFF00FF00) >> 8) | ((n & 0x00FF00FF) << 8)
        n = ((n & 0xF0F0F0F0) >> 4) | ((n & 0x0F0F0F0F) << 4)
        n = ((n & 0xCCCCCCCC) >> 2) | ((n & 0x33333333) << 2)
        n = ((n & 0xAAAAAAAA) >> 1) | ((n & 0x55555555) << 1)
        return n & 0xFFFFFFFF

    def reverseBits_string_UNSAFE(self, n: int) -> int:
        """Naive string reversal -- BROKEN for negative n. Kept only to
        demonstrate the masking bug live in run_tests()."""
        s = bin(n)[2:].zfill(32)
        return int(s[::-1], 2)


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        (0b00000010100101000001111010011100, 964176192),
        (0b11111111111111111111111111111101, 3221225471),
        (0, 0),
        (1, 1 << 31),
        ((1 << 32) - 1, (1 << 32) - 1),
    ]
    print("--- correctness: shift-place vs SWAR agree ---")
    for n, want in cases:
        g1 = sol.reverseBits(n)
        g2 = sol.reverseBits_swar(n)
        ok = g1 == g2 == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n:>12}  shift={g1:>12} "
              f"swar={g2:>12}  (want {want})")

    # ------------------------------------------------------------------
    # LIVE BUG DEMO: the naive string-reversal approach breaks the moment
    # it sees a genuinely negative Python int meant to represent a 32-bit
    # two's-complement pattern (exactly the scenario the problem's own
    # "Java note" describes: input -3 represents unsigned 4294967293).
    # ------------------------------------------------------------------
    print("\n--- DEMO: masking discipline -- negative int as a 32-bit pattern ---")
    signed_value = -3   # intended 32-bit pattern: 0xFFFFFFFD (4294967293)
    masked = signed_value & 0xFFFFFFFF
    print(f"  Python int:            {signed_value}")
    print(f"  bin(signed_value):     {bin(signed_value)!r}  <- has a MINUS sign, not 32 bits")
    print(f"  After & 0xFFFFFFFF:    {masked}  (bin: {bin(masked)})  <- correct unsigned pattern")

    try:
        buggy = sol.reverseBits_string_UNSAFE(signed_value)
        print(f"  UNSAFE string reversal on raw -3:  returned {buggy} "
              f"(WRONG -- garbage, str had a sign char)")
        bug_triggered = True
    except ValueError as e:
        print(f"  UNSAFE string reversal on raw -3:  raised {type(e).__name__}: {e}")
        bug_triggered = True

    correct = sol.reverseBits(masked)
    expected = 3221225471  # reversal of 11111111111111111111111111111101
    print(f"  Correct (masked first, shift-place): {correct}  (want {expected})")
    all_ok &= bug_triggered and (correct == expected)

    # ------------------------------------------------------------------
    # RUNTIME DEMO: loop-based vs SWAR across a large batch of calls --
    # answers "how would you optimize for many calls."
    # ------------------------------------------------------------------
    print("\n--- DEMO: 32-iteration loop vs O(1) SWAR, 500,000 calls ---")
    import random
    random.seed(3)
    values = [random.getrandbits(32) for _ in range(500_000)]

    t0 = time.perf_counter()
    r1 = [sol.reverseBits(v) for v in values]
    t_loop = time.perf_counter() - t0

    t0 = time.perf_counter()
    r2 = [sol.reverseBits_swar(v) for v in values]
    t_swar = time.perf_counter() - t0

    print(f"  32-bit loop:  {t_loop * 1000:8.2f} ms")
    print(f"  SWAR (5 ops): {t_swar * 1000:8.2f} ms")
    speedup = t_loop / t_swar if t_swar > 0 else float("inf")
    print(f"  speedup: {speedup:.2f}x")
    all_ok &= (r1 == r2)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
