"""
================================================================================
SOLUTION · LeetCode 137 · Single Number II                           [Medium]
https://leetcode.com/problems/single-number-ii/
================================================================================

THE CORE IDEA
--------------
Count set bits PER POSITION instead of per value. For each of the 32 bit
positions, sum how many numbers have that bit set; every number that
appears 3 times contributes a multiple of 3 to that sum, so `sum % 3`
strips those away entirely and leaves exactly the singleton's bit.

    for i in range(32):
        bit_sum = sum((x >> i) & 1 for x in nums)
        if bit_sum % 3:
            result |= 1 << i

Then fix up the sign: `result` is built as an UNSIGNED 32-bit pattern; if
bit 31 is set, reinterpret as the Python negative int it represents
(`result -= 1 << 32`) -- the same masking discipline as 006/007, needed
here because nums[i] can legitimately be negative.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, name it and reject it): Counter/hash map, return
the key with count 1. O(n) time, O(n) space -- correct, violates the
stated O(1) space constraint.

Approach 1 (bit-count-mod-3, per position) [chosen for the trace] --
O(32n) = O(n) time, O(1) space (32 is a constant, not proportional to
n). Directly generalizes 001's XOR trick from "cancel pairs" to "cancel
triples," and is the version most people can derive and explain in an
interview without memorizing anything.

Approach 2 (ones/twos two-variable automaton) -- track two accumulators,
`ones` (bits seen exactly once so far, mod 3) and `twos` (bits seen
exactly twice so far, mod 3), updated with a specific XOR/AND formula per
number: `ones = (ones ^ x) & ~twos; twos = (twos ^ x) & ~ones`. Same
O(n) time, same O(1) space, but a SINGLE pass over nums (no inner loop
over 32 bit positions) and no per-bit summation -- faster in practice,
harder to derive/remember without having seen it before. Worth knowing
exists; the mod-3 version is what you should be able to produce live.

Approach 3 (generalize to "appears k times except one") -- track k
counter variables (or a base-k digit per bit position via `count[i] =
(count[i] + bit) % k`), same idea as approach 1 generalized. This is
what an interviewer follow-up usually asks for.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [2, 2, 3, 2]   (2 appears 3x, 3 is the singleton; want 3)

    2 = 0b010,  3 = 0b011

    Bit position 0: values with bit0 set -> only 3 (0b011). count=1.
        1 % 3 = 1 -> result bit0 = 1
    Bit position 1: values with bit1 set -> 2,2,2,3 all have bit1 set
        (0b010 and 0b011 both have bit1). count=4.
        4 % 3 = 1 -> result bit1 = 1
    Bit position 2 and above: no value has these bits set. count=0.
        0 % 3 = 0 -> result bits stay 0

    result = 0b011 = 3   <- matches expected output

    (Sanity: 2's three copies contribute 3 to bit1's count -- a multiple
    of 3 -- so bit1's count of 4 is "3 (from the triples) + 1 (from the
    singleton 3)," and 4 % 3 recovers exactly that 1.)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time      Space   Mutates input?
    ---------------------------------  --------  ------  --------------
    Counter / hash map                 O(n)      O(n)    no
    Bit-count mod 3 [chosen]           O(32n)=O(n) O(1)  no
    Ones/twos automaton (single pass)  O(n)      O(1)    no


================================================================================
EDGE CASES
================================================================================
    single-element array         -> that element IS the singleton by
                                     definition; loop over 32 positions
                                     correctly recovers it bit by bit.
    negative singleton            -> e.g. [-2,-2,-2,-5]: bit-counting
                                     works on the MASKED 32-bit pattern of
                                     each number (Python negatives are
                                     conceptually infinite two's
                                     complement, so `(x >> i) & 1` for a
                                     fixed i in 0..31 is well-defined and
                                     correct without masking x itself --
                                     but the FINAL result must still be
                                     sign-corrected, since it's assembled
                                     as an unsigned pattern).
    negative repeated value        -> same masking story: `(x >> i) & 1`
                                     on a negative x for i in [0,31] is
                                     safe because right-shift on a
                                     negative Python int sign-extends
                                     correctly (arithmetic shift), so bit
                                     i is read correctly without an
                                     explicit `& 0xFFFFFFFF` on x.
    all repeated values share bits
    with the singleton              -> handled automatically -- the
                                     mod-3 reduction operates per bit
                                     position independently, so overlap
                                     in which bits are set across
                                     different numbers doesn't matter.


================================================================================
COMMON MISTAKES
================================================================================
1. Reaching for plain XOR-fold (001's trick) out of habit. It's the wrong
   tool here: `x ^ x ^ x == x`, not 0, so three-times-repeated values do
   NOT cancel under XOR, and the whole fold produces a meaningless value.

2. Forgetting the SIGN FIX-UP on the final result. `result` is built bit
   by bit as an unsigned 32-bit pattern (`result |= 1 << i` only ever
   sets bits, never produces a "negative" accumulation) -- if the true
   singleton is negative, the raw `result` is a large positive int
   (e.g. bit 31 set) and must be converted with `result -= (1 << 32)`
   before returning. Demonstrated live below.

3. Iterating `for i in range(31)` instead of `range(32)` -- drops bit 31
   entirely, which is exactly the sign bit needed to detect a negative
   result at all. Off-by-one here silently breaks every negative-answer
   test case while every positive-answer test case still passes.

4. In the ones/twos automaton (Approach 2), getting the update ORDER
   wrong -- `twos` must be updated using the NEW `ones` (post-update),
   not the old one, or vice versa depending on which formula variant is
   used; swapping the order silently produces a working-looking but
   wrong automaton for some inputs.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How would you generalize to "every element appears k times except
   one"?
A: Replace `% 3` with `% k` in the per-bit-position counting approach --
   everything else is identical. This is Approach 3.

Q: Can you do it in a single pass without counting bits per position?
A: Yes -- the ones/twos automaton (Approach 2) processes each number once
   with O(1) work, using two accumulator variables that together encode
   "seen 0/1/2 times mod 3" per bit position implicitly.

Q: Why does `(x >> i) & 1` not need `x` to be masked first, when 006 and
   008's own final result DO need masking?
A: Reading a single bit at a FIXED, already-in-range position (i in
   0..31) from a Python int -- positive or negative -- is always
   well-defined and correct, because Python's right-shift on negative
   ints is arithmetic (sign-extending), matching two's complement
   semantics exactly for that one bit. Masking becomes necessary only
   when you need the WHOLE value to behave as a bounded 32-bit quantity
   (e.g. after summing/reconstructing bits into a fresh result, or
   before an operation like `<<` that could otherwise grow unboundedly).


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 136  Single Number         (001 -- appears 2x except one, XOR)
    LC 260  Single Number III     (009 -- two singletons, XOR + partition)
    LC 371  Sum of Two Integers   (006 -- same masking/sign-fixup discipline)
    LC 645  Set Mismatch          (different technique, same "one value is
                                    special" family)
================================================================================
"""

import time
from typing import List


MASK32 = 0xFFFFFFFF
SIGN_BIT = 1 << 31
WIDTH = 1 << 32


class Solution:
    def singleNumber(self, nums: List[int]) -> int:
        """✅ Bit-count mod 3, per position. O(32n)=O(n) time, O(1) space."""
        result = 0
        for i in range(32):
            bit_sum = 0
            for x in nums:
                bit_sum += (x >> i) & 1
            if bit_sum % 3:
                result |= 1 << i
        if result & SIGN_BIT:
            result -= WIDTH
        return result

    def singleNumber_automaton(self, nums: List[int]) -> int:
        """Alternative: ones/twos single-pass automaton. O(n) time,
        O(1) space, one pass over nums (no inner 32-loop)."""
        ones = twos = 0
        for x in nums:
            ones = (ones ^ x) & ~twos
            twos = (twos ^ x) & ~ones
        ones &= MASK32
        if ones & SIGN_BIT:
            ones -= WIDTH
        return ones

    def singleNumber_counter(self, nums: List[int]) -> int:
        """Brute force: Counter. O(n) time, O(n) space."""
        from collections import Counter
        counts = Counter(nums)
        for value, c in counts.items():
            if c == 1:
                return value
        raise ValueError("no singleton found")


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([2, 2, 3, 2], 3),
        ([0, 1, 0, 1, 0, 1, 99], 99),
        ([1], 1),
        ([-2, -2, -2, -5], -5),
        ([30000, 500, 100, 30000, 100, 30000, 100], 500),
    ]
    print("--- correctness: all three approaches agree ---")
    for nums, want in cases:
        g1 = sol.singleNumber(nums[:])
        g2 = sol.singleNumber_automaton(nums[:])
        g3 = sol.singleNumber_counter(nums[:])
        ok = g1 == g2 == g3 == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums}  bitcount={g1} "
              f"automaton={g2} counter={g3}  (want {want})")

    # ------------------------------------------------------------------
    # LIVE BUG DEMO: forgetting the sign fix-up on a negative singleton.
    # ------------------------------------------------------------------
    print("\n--- DEMO: forgetting the sign fix-up on a negative singleton ---")
    nums = [-2, -2, -2, -5]
    result_unsigned = 0
    for i in range(32):
        bit_sum = sum((x >> i) & 1 for x in nums)
        if bit_sum % 3:
            result_unsigned |= 1 << i
    print(f"  Raw bit-reconstructed result (NO sign fix-up): {result_unsigned}")
    print(f"  That's the UNSIGNED 32-bit pattern for -5, reported as a huge "
          f"positive int -- clearly wrong for an input that should give -5.")
    fixed = result_unsigned - WIDTH if result_unsigned & SIGN_BIT else result_unsigned
    print(f"  After sign fix-up (result -= 1<<32 since bit 31 is set): {fixed}")
    all_ok &= (result_unsigned != -5) and (fixed == -5)

    # ------------------------------------------------------------------
    # RUNTIME DEMO: bit-count-mod-3 vs single-pass automaton.
    # ------------------------------------------------------------------
    print("\n--- DEMO: bit-count-mod-3 vs single-pass automaton, n=150,000 triples ---")
    import random
    random.seed(13)
    n_groups = 50_000
    values = random.sample(range(-1_000_000, 1_000_000), n_groups)
    big_nums = values * 3
    singleton = 424242
    big_nums.append(singleton)
    random.shuffle(big_nums)

    t0 = time.perf_counter()
    r1 = sol.singleNumber(big_nums)
    t_bitcount = time.perf_counter() - t0

    t0 = time.perf_counter()
    r2 = sol.singleNumber_automaton(big_nums)
    t_automaton = time.perf_counter() - t0

    print(f"  Bit-count mod 3 (32 passes/number): {t_bitcount * 1000:8.2f} ms")
    print(f"  Ones/twos automaton (1 pass):        {t_automaton * 1000:8.2f} ms")
    speedup = t_bitcount / t_automaton if t_automaton > 0 else float("inf")
    print(f"  speedup: {speedup:.1f}x -- avoiding the inner 32-position loop wins big")
    all_ok &= (r1 == r2 == singleton)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
