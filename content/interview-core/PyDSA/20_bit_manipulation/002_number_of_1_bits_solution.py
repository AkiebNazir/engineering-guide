"""
================================================================================
SOLUTION · LeetCode 191 · Number of 1 Bits                           [Easy]
https://leetcode.com/problems/number-of-1-bits/
================================================================================

THE CORE IDEA
--------------
`n & (n - 1)` clears the LOWEST set bit and leaves every other bit alone
(see topic guide §1.0). Repeating it until n hits 0 takes exactly
popcount(n) iterations -- one per set bit, not one per bit position.

    count = 0
    while n:
        n &= n - 1
        count += 1
    return count

O(k) time where k is the number of set bits (at most 32), O(1) space.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, name it and reject it): convert to a binary
string with `bin(n)` and call `.count('1')`. Correct and actually fast in
CPython (C-implemented string ops), but it's cheating the point of a bit
manipulation exercise -- an interviewer wants to see you reason in bits,
not delegate to a string method. Worth naming, not "the answer."

Approach 1 (shift-and-mask, 32 fixed iterations) -- for each of the 32
bit positions, check `(n >> i) & 1` and accumulate. O(32) = O(1) time
always, even when n has very few set bits. Simple, predictable, no
masking pitfalls since we only ever look at bit i in isolation.

Approach 2 (Brian Kernighan's `n & (n-1)`) [chosen] -- O(popcount(n))
iterations, which is <= 32 and often much less. Same asymptotic class as
approach 1 but strictly less work whenever n is sparse, and it's the
identity the whole topic guide is built around, so worth knowing cold.

Approach 3 (Python's built-in `int.bit_count()`, 3.10+) -- O(1) from the
caller's perspective (CPython implements it in C with a popcount
intrinsic where available). The "real" answer in production Python 3.10+,
but an interview wants you to derive approach 2 by hand first.


================================================================================
STEP BY STEP TRACE
================================================================================
n = 0b1011  (11, three set bits)

    n = 0b1011,  n-1 = 0b1010  ->  n & (n-1) = 0b1010   count=1
    n = 0b1010,  n-1 = 0b1001  ->  n & (n-1) = 0b1000   count=2
    n = 0b1000,  n-1 = 0b0111  ->  n & (n-1) = 0b0000   count=3
    n = 0b0000  -> loop ends

    Answer: 3   (matches: 0b1011 has bits at positions 0, 1, 3 set)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time            Space   Mutates input?
    ---------------------------  --------------  ------  --------------
    bin(n).count('1')            O(32) (C-impl)  O(32)   no (n is an int)
    Shift-and-mask (32 fixed)    O(32)           O(1)    no
    n & (n-1) loop [chosen]      O(popcount(n))  O(1)    no
    int.bit_count() (3.10+)      O(1) amortized  O(1)    no


================================================================================
EDGE CASES
================================================================================
    n == 0                    -> loop body never runs, count stays 0. No
                                  special-case needed -- the while condition
                                  handles it naturally.
    n == 1                    -> single iteration, count 1.
    all 32 bits set (2^32-1)  -> 32 iterations, worst case for the
                                  Kernighan loop (still correct, just no
                                  better than the fixed shift-and-mask here).
    n given as an "unsigned" 32-bit pattern via a large positive int
    (e.g. 4294967293) -> Python has no unsigned type but `n` is ALREADY
                                  a non-negative int here (LeetCode's Python
                                  signature takes it as unsigned directly),
                                  so no masking is needed -- unlike 004/006/007
                                  where a genuinely negative Python int must
                                  be reinterpreted as a 32-bit pattern first.


================================================================================
COMMON MISTAKES
================================================================================
1. Assuming this problem needs `& 0xFFFFFFFF` masking like 004/006/007.
   It doesn't -- LeetCode's Python signature hands you n already as a
   non-negative int representing the unsigned bit pattern. Masking becomes
   relevant only if you're handed a genuinely negative Python int and told
   to treat it as 32-bit unsigned (that IS the lesson in 004/006/007).

2. Using `n & (n-1)` but forgetting the loop must terminate on n == 0, not
   on some fixed iteration count -- if you cap it at 32 fixed shifts
   AND use n&(n-1) together, you've written two different algorithms that
   happen to coexist without conflict, but it's a sign of confusion.

3. Off-by-one from shifting `n` itself instead of checking bit i with
   `(n >> i) & 1` in the fixed-32 approach -- mutating n while also trying
   to index by position is a common source of double-shift bugs.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How would you count set bits for a huge batch of numbers efficiently?
A: Precompute a DP table where `bits[i] = bits[i >> 1] + (i & 1)` (this is
   exactly LC 338 Counting Bits, 003 in this folder) -- O(1) amortized
   lookup per number after O(n) preprocessing.

Q: What's the actual hardware answer?
A: Most modern CPUs have a POPCNT instruction; `int.bit_count()` in
   CPython 3.10+ uses it when available, making the "loop" academic in
   production code -- but interviewers still want to see you derive it.

Q: Does `n & (n-1)` work the same in a language with true unsigned ints?
A: Yes, identically -- the identity is about the bit pattern, not about
   Python's arbitrary-precision representation.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 338  Counting Bits        (003 -- popcount for EVERY number 0..n via DP)
    LC 231  Power of Two         (n & (n-1) == 0 iff n is a power of two)
    LC 268  Missing Number       (005 -- different bit trick, same topic)
    LC 393  UTF-8 Validation     (leading-bit counting, same "count set bits"
                                   family in a different guise)
================================================================================
"""

import time


class Solution:
    def hammingWeight(self, n: int) -> int:
        """✅ Brian Kernighan's n & (n-1). O(popcount(n)) time, O(1) space."""
        count = 0
        while n:
            n &= n - 1
            count += 1
        return count

    def hammingWeight_shift(self, n: int) -> int:
        """Alternative: fixed 32 shift-and-mask. O(32) = O(1) time."""
        count = 0
        for i in range(32):
            if (n >> i) & 1:
                count += 1
        return count

    def hammingWeight_string(self, n: int) -> int:
        """Alternative: delegate to CPython's C-implemented string count."""
        return bin(n).count("1")


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        (0b1011, 3),
        (0b10000000, 1),
        (4294967293, 31),
        (0, 0),
        (1, 1),
        ((1 << 32) - 1, 32),
    ]
    print("--- correctness: all three approaches agree ---")
    for n, want in cases:
        g1 = sol.hammingWeight(n)
        g2 = sol.hammingWeight_shift(n)
        g3 = sol.hammingWeight_string(n)
        ok = g1 == g2 == g3 == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n:>12}  kernighan={g1} "
              f"shift={g2} string={g3}  (want {want})")

    # ------------------------------------------------------------------
    # RUNTIME DEMO: Kernighan's loop vs fixed shift-and-mask, across
    # numbers of varying sparsity -- showing WHY "O(popcount)" beats a
    # blind "O(32)" when most numbers have few set bits.
    # ------------------------------------------------------------------
    print("\n--- DEMO: Kernighan vs fixed-shift over 500,000 sparse numbers ---")
    import random
    random.seed(7)
    # sparse: numbers with only 1-3 bits set (e.g. powers-of-two-ish)
    sparse_nums = [
        (1 << random.randint(0, 20)) | (1 << random.randint(0, 20))
        for _ in range(500_000)
    ]

    t0 = time.perf_counter()
    total1 = sum(sol.hammingWeight(x) for x in sparse_nums)
    t_kern = time.perf_counter() - t0

    t0 = time.perf_counter()
    total2 = sum(sol.hammingWeight_shift(x) for x in sparse_nums)
    t_shift = time.perf_counter() - t0

    print(f"  Kernighan (n&(n-1)):   {t_kern * 1000:8.2f} ms  (sum={total1})")
    print(f"  Fixed 32-shift:        {t_shift * 1000:8.2f} ms  (sum={total2})")
    print(f"  Kernighan does far fewer Python-level loop iterations per "
          f"number on sparse inputs (1-2 vs a fixed 32).")
    all_ok &= (total1 == total2)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
