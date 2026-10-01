"""
================================================================================
SOLUTION · LeetCode 338 · Counting Bits                              [Easy]
https://leetcode.com/problems/counting-bits/
================================================================================

THE CORE IDEA
--------------
popcount(i) can be derived from a SMALLER already-computed index in O(1):
right-shifting i by 1 drops its lowest bit, and `i & 1` tells you exactly
what that dropped bit was.

    ans[i] = ans[i >> 1] + (i & 1)

Building the array left to right, `i >> 1 < i` for all i >= 1, so every
lookup hits an already-filled slot. One pass, O(1) work per index, O(n)
total.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, name it and reject it): for each i in 0..n, call
`bin(i).count('1')` or a Kernighan loop (002). O(n log n) overall (each
call costs up to O(log i) bit operations) -- correct, and the problem
explicitly calls this out as "the easy answer," then asks for O(n).

Approach 1 (DP via lowest bit, shift recurrence) [chosen] --
`ans[i] = ans[i >> 1] + (i & 1)`. O(n) time, O(n) space (output only).

Approach 2 (DP via lowest SET bit, Kernighan recurrence) -- `ans[i] =
ans[i & (i - 1)] + 1`, since `i & (i-1)` is i with its lowest set bit
cleared (topic guide §1.0), so its popcount is exactly one less than i's.
Also O(n), a different but equally valid decomposition -- worth knowing
both since interviewers sometimes ask for "a second way."

Approach 3 (power-of-two boundary DP) -- reset a running "offset" pointer
each time i is a power of two (`i & (i-1) == 0`), then `ans[i] = ans[i -
offset] + 1`. Also O(n); more moving parts than approaches 1/2 for the
same result, included for completeness since some textbooks present it
this way.


================================================================================
STEP BY STEP TRACE
================================================================================
n = 5, using ans[i] = ans[i >> 1] + (i & 1)

    ans[0] = 0                                (base case)
    ans[1] = ans[0b1 >> 1] + (1 & 1) = ans[0] + 1 = 0 + 1 = 1
    ans[2] = ans[0b10 >> 1] + (2 & 1) = ans[1] + 0 = 1 + 0 = 1
    ans[3] = ans[0b11 >> 1] + (3 & 1) = ans[1] + 1 = 1 + 1 = 2
    ans[4] = ans[0b100 >> 1] + (4 & 1) = ans[2] + 0 = 1 + 0 = 1
    ans[5] = ans[0b101 >> 1] + (5 & 1) = ans[2] + 1 = 1 + 1 = 2

    ans = [0, 1, 1, 2, 1, 2]   <- matches expected output


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time          Space    Mutates input?
    -------------------------------  ------------  -------  --------------
    Per-index popcount (002)         O(n log n)    O(n)     n/a (no input)
    DP via i>>1, i&1 [chosen]        O(n)          O(n)*    n/a
    DP via i&(i-1)                   O(n)          O(n)*    n/a
    Power-of-two offset DP           O(n)          O(n)*    n/a

    * O(n) is the OUTPUT array itself, required by the problem; auxiliary
      space beyond the output is O(1) for all three DP variants.


================================================================================
EDGE CASES
================================================================================
    n == 0        -> output is just [0] (length n+1 = 1). Loop body for
                      i=1..n never runs.
    n == 1         -> [0, 1]. ans[1] = ans[0] + 1 works fine at the boundary.
    large n (1e5)  -> confirms O(n) actually matters -- the brute-force
                      O(n log n) approach is measurably slower at this size
                      (see runtime demo).
    powers of two (i=1,2,4,8,...) -> always popcount 1; a good sanity check
                      since ans[i>>1] for i a power of two is always ans[1]
                      or the earlier power's slot, itself always 1 or a
                      cascading base case.


================================================================================
COMMON MISTAKES
================================================================================
1. Writing `ans[i] = ans[i // 2] + i % 2` -- correct in VALUE (Python's
   `//` and `%` on non-negative ints match `>>` and `&1` exactly), but it's
   worth being explicit that `>>`/`&` is the "bit manipulation" framing an
   interviewer wants to see, not just "it happens to compute the same
   thing."

2. Off-by-one on the array size: the problem wants indices 0..n inclusive,
   i.e. length n+1, not length n. Allocating `[0] * n` instead of
   `[0] * (n + 1)` silently drops the last entry.

3. Trying to use `ans[i & (i-1)] + 1` but computing `i & (i-1)` BEFORE
   confirming i >= 1 -- at i=0, `i - 1 == -1`, and `0 & -1 == 0` in Python
   (two's-complement AND with an infinite string of 1-bits), which
   actually happens to self-reference ans[0] correctly only because ans[0]
   is defined as the base case 0 and is filled first -- fragile reasoning
   to rely on; guard i==0 explicitly instead.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you do it without any built-in bit-count function?
A: Yes -- both DP recurrences use only `>>`, `&`, `+`, no popcount builtin
   at all. That's exactly what's shown here.

Q: Which of the two DP recurrences is "better"?
A: Asymptotically identical (O(n) time, O(1) auxiliary space each). The
   `i >> 1` version is arguably more intuitive (halving); the `i & (i-1)`
   version ties directly back to 002's Kernighan trick. Pick either in an
   interview and explain why it's O(1) extra work per index.

Q: How would you extend this to 64-bit integers?
A: The recurrences are width-agnostic -- they only depend on relationships
   between i and smaller indices, not on a fixed bit width. Works for any
   size int without modification (a rare case in this topic where NO
   masking is needed at all -- contrast with 004/006/007).


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 191  Number of 1 Bits       (002 -- single-number popcount, the base op)
    LC 231  Power of Two           (i & (i-1) == 0 check)
    LC 137  Single Number II       (008 -- bit-position counting, different use)
    LC 70   Climbing Stairs        (same "DP reuses a smaller subproblem"
                                     shape, different recurrence)
================================================================================
"""

import time
from typing import List


class Solution:
    def countBits(self, n: int) -> List[int]:
        """✅ DP via lowest-bit shift. O(n) time, O(n) output space."""
        ans = [0] * (n + 1)
        for i in range(1, n + 1):
            ans[i] = ans[i >> 1] + (i & 1)
        return ans

    def countBits_kernighan_dp(self, n: int) -> List[int]:
        """Alternative: DP via lowest SET bit (i & (i-1)). O(n) time."""
        ans = [0] * (n + 1)
        for i in range(1, n + 1):
            ans[i] = ans[i & (i - 1)] + 1
        return ans

    def countBits_brute(self, n: int) -> List[int]:
        """Brute force: popcount each index independently. O(n log n)."""
        return [bin(i).count("1") for i in range(n + 1)]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        (0, [0]),
        (2, [0, 1, 1]),
        (5, [0, 1, 1, 2, 1, 2]),
        (1, [0, 1]),
        (8, [0, 1, 1, 2, 1, 2, 2, 3, 1]),
    ]
    print("--- correctness: all three approaches agree ---")
    for n, want in cases:
        g1 = sol.countBits(n)
        g2 = sol.countBits_kernighan_dp(n)
        g3 = sol.countBits_brute(n)
        ok = g1 == g2 == g3 == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n}  -> {g1}  (want {want})")

    # ------------------------------------------------------------------
    # RUNTIME DEMO: O(n) DP vs O(n log n) brute force at n = 100,000.
    # ------------------------------------------------------------------
    print("\n--- DEMO: O(n) DP vs O(n log n) brute force, n=100,000 ---")
    n = 100_000

    t0 = time.perf_counter()
    r1 = sol.countBits(n)
    t_dp = time.perf_counter() - t0

    t0 = time.perf_counter()
    r2 = sol.countBits_brute(n)
    t_brute = time.perf_counter() - t0

    print(f"  DP (i>>1, i&1):     {t_dp * 1000:8.2f} ms")
    print(f"  Brute (per-index):  {t_brute * 1000:8.2f} ms")
    speedup = t_brute / t_dp if t_dp > 0 else float("inf")
    print(f"  speedup: {speedup:.2f}x")
    all_ok &= (r1 == r2)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
