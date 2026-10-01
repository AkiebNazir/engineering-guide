"""
================================================================================
SOLUTION · LeetCode 2376 · Count Special Integers                         [Hard]
https://leetcode.com/problems/count-special-integers/
================================================================================

THE CORE IDEA
--------------
Digit DP with state (pos, used-digit mask, tight, started). Place digits from
the most significant position; `tight` bounds the digit by n; `mask` forbids
reuse; `started` makes leading zeros free (they're padding, not digits).

The same count also falls out of plain combinatorics: count all shorter
special numbers with permutations, then walk n's digits and count, at each
position, the unused smaller digits times the permutations of what's left.


================================================================================
APPROACH 1 · Enumerate 1..n (priced, used as oracle)
================================================================================
    sum(len(set(str(x))) == len(str(x)) for x in range(1, n + 1))

    Time: O(n log n) — 2 * 10^9 numbers is hopeless.    Space: O(1)


================================================================================
APPROACH 2 · Combinatorics ✅ (the answer)
================================================================================
P(a, b) = a * (a-1) * ... * (a-b+1)   (ordered picks of b from a)

    s = str(n); L = len(s)
    total = sum(9 * P(9, k - 1) for k in range(1, L))       # shorter numbers
    used = 0
    for i, c in enumerate(s):
        d_n = int(c)
        for d in range(1 if i == 0 else 0, d_n):             # smaller choices
            if not used >> d & 1:
                total += P(10 - i - 1, L - i - 1)
        if used >> d_n & 1:
            return total                                     # n's prefix repeats
        used |= 1 << d_n
    return total + 1                                         # n itself is special

WHY P(10 - i - 1, L - i - 1). After fixing i + 1 distinct digits (the prefix
plus the chosen smaller digit), 10 - (i + 1) digits remain unused, and
L - i - 1 positions remain to fill, in order, without reuse.

WHY SHORTER NUMBERS ARE 9 * P(9, k - 1). The first digit has 9 choices (1-9,
no leading zero); the remaining k - 1 positions pick in order from the 9
digits not yet used (0 is now allowed).

    Time: O(L * 10)    Space: O(1)


================================================================================
APPROACH 3 · Memoized digit DP (the reusable template)
================================================================================
    @cache
    def f(pos, mask, tight, started):
        if pos == L:
            return int(started)
        limit = int(s[pos]) if tight else 9
        total = 0
        for d in range(limit + 1):
            if not started and d == 0:
                total += f(pos + 1, mask, tight and d == limit, False)   # leading 0
            elif not mask >> d & 1:
                total += f(pos + 1, mask | 1 << d, tight and d == limit, True)
        return total
    return f(0, 0, True, False)

    States: L * 1024 * 2 * 2 ~ 40,000, each trying 10 digits.
    Time: O(L * 2^10 * 10)    Space: O(L * 2^10)

This template extends to "digit sum divisible by k", "no two adjacent equal
digits", ranges [lo, hi] via count(hi) - count(lo - 1), and so on. The
combinatorics version doesn't generalize as easily.


================================================================================
STEP BY STEP TRACE · n = 135 (combinatorics)
================================================================================
    L = 3
    shorter: k=1: 9 * P(9,0) = 9       k=2: 9 * P(9,1) = 81      -> 90

    i=0, c='1': smaller first digits in [1, 1): none                +0
                mark 1 used
    i=1, c='3': d in 0..2, unused: 0, 2 (1 is used) -> 2 choices
                each * P(10-1-1, 3-1-1) = P(8, 1) = 8               +16
                mark 3 used
    i=2, c='5': d in 0..4, unused: 0, 2, 4 -> 3 choices
                each * P(10-2-1, 0) = 1                             +3   (130, 132, 134)
                mark 5 used
    walk finished: 135 is special                                   +1

    total = 90 + 16 + 3 + 1 = 110

    Check the +16: 10x has x in {0..9} minus {0, 1} used -> 8 (102..109);
                   12x has x not in {1, 2} -> 8 (120, 123..129). 8 + 8 = 16. ✓


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time               Space        Mutates input?
    ------------------------------  -----------------  -----------  --------------
    Enumerate 1..n                  O(n log n)         O(1)         No
    Combinatorics ✅                O(L * 10)          O(1)         No
    Memoized digit DP               O(L * 2^10 * 10)   O(L * 2^10)  No


================================================================================
EDGE CASES
================================================================================
    n <= 9           Every number 1..n: answer n.
    n = 10, 11       10 is special, 11 is not: both give 10.
    n with a repeat  e.g. 1123: the walk stops at the second '1' (no +1).
    n = 2 * 10^9     10 digits; 9,876,543,210 > 2 * 10^9 so many 10-digit
                      specials exceed n — only those <= n count.


================================================================================
COMMON MISTAKES
================================================================================
1. No `started` flag: leading zeros mark 0 as used. n = 100 returns 72 instead
   of 90 (1-9 and 10, 20, ..., 90 are wrongly rejected). Demo below.

2. Allowing 0 as the first digit in the same-length walk (i == 0).

3. Forgetting to stop when n's own prefix repeats a digit. Then tight
   branches keep counting numbers that start with an invalid prefix.

4. Forgetting +1 for n itself when it's special.

5. Memoizing on `tight` states unnecessarily is harmless; forgetting `mask` in
   the cache key is not.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Numbers WITH at least one repeated digit (LC 1012)?
A: n - countSpecialNumbers(n).

Q: Count special numbers in [lo, hi]?
A: f(hi) - f(lo - 1).

Q: Special in base b?
A: Same combinatorics with 10 replaced by b; mask has b bits.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 902   Numbers At Most N Given Digit Set (017)
    LC 1012  Numbers With Repeated Digits
    LC 357   Count Numbers with Unique Digits    — n = 10^k special case
    LC 233   Number of Digit One
================================================================================
"""

import random
import time
from functools import cache


def perm(a: int, b: int) -> int:
    out = 1
    for x in range(a, a - b, -1):
        out *= x
    return out


class Solution:
    def countSpecialNumbers(self, n: int) -> int:
        s = str(n)
        L = len(s)
        total = sum(9 * perm(9, k - 1) for k in range(1, L))
        used = 0
        for i, c in enumerate(s):
            d_n = ord(c) - 48
            for d in range(1 if i == 0 else 0, d_n):
                if not used >> d & 1:
                    total += perm(10 - i - 1, L - i - 1)
            if used >> d_n & 1:
                return total
            used |= 1 << d_n
        return total + 1


# ------------------------------------------------------------------------
# Alternatives / oracle / broken version for the demos.
# ------------------------------------------------------------------------
def special_digit_dp(n: int) -> int:
    s = str(n)
    L = len(s)

    @cache
    def f(pos: int, mask: int, tight: bool, started: bool) -> int:
        if pos == L:
            return int(started)
        limit = ord(s[pos]) - 48 if tight else 9
        total = 0
        for d in range(limit + 1):
            nt = tight and d == limit
            if not started and d == 0:
                total += f(pos + 1, mask, nt, False)
            elif not mask >> d & 1:
                total += f(pos + 1, mask | 1 << d, nt, True)
        return total

    return f(0, 0, True, False)


def special_brute(n: int) -> int:
    count = 0
    for x in range(1, n + 1):
        t = str(x)
        if len(set(t)) == len(t):
            count += 1
    return count


def special_no_started_bug(n: int) -> int:
    """Mistake 1: every position's digit, including leading zeros, marks the mask."""
    s = str(n)
    L = len(s)

    @cache
    def f(pos: int, mask: int, tight: bool) -> int:
        if pos == L:
            return 1 if mask else 0            # exclude the all-zero "number"
        limit = ord(s[pos]) - 48 if tight else 9
        total = 0
        for d in range(limit + 1):
            if not mask >> d & 1:
                total += f(pos + 1, mask | 1 << d, tight and d == limit)
        return total

    return f(0, 0, True)


# ==============================================================================
# TESTS — run:  python 018_count_special_integers_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: combinatorics vs digit DP ---")
    cases = [(20, 19), (5, 5), (135, 110), (1, 1), (10, 10), (11, 10), (100, 90)]
    for n, want in cases:
        a, b = sol.countSpecialNumbers(n), special_digit_dp(n)
        ok = a == b == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n:<5} combinatorics={a}  digit-dp={b}  want={want}")

    big = 2 * 10**9
    a, b = sol.countSpecialNumbers(big), special_digit_dp(big)
    ok = a == b
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  n=2*10^9  combinatorics={a}  digit-dp={b}  (independent methods agree)")

    print("\n--- exhaustive check for every n in 1..3000, plus 300 random n <= 200,000 ---")
    bad = 0
    running = 0
    for n in range(1, 3001):
        t = str(n)
        running += len(set(t)) == len(t)
        if sol.countSpecialNumbers(n) != running:
            bad += 1
    rng = random.Random(2376)
    for _ in range(300):
        n = rng.randint(1, 200_000)
        if sol.countSpecialNumbers(n) != special_digit_dp(n):
            bad += 1
    for n in (99_999, 123_456):
        if sol.countSpecialNumbers(n) != special_brute(n):
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  all 3000 prefixes match a running brute-force count; random checks agree")

    print("\n--- mistake 1 LIVE: no `started` flag, leading zeros mark 0 as used ---")
    wrong = special_no_started_bug(100)
    ok = wrong == 72 and sol.countSpecialNumbers(100) == 90
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  n=100: no-started version {wrong}, correct 90")
    print("      1..9 padded to '00d' repeat 0; 10, 20, ..., 90 padded to '0d0' repeat 0")

    print("\n--- benchmark ---")
    for n in (10**5, 10**6):
        t0 = time.perf_counter(); x = special_brute(n); tb = time.perf_counter() - t0
        t0 = time.perf_counter(); y = sol.countSpecialNumbers(n); tc = time.perf_counter() - t0
        all_ok &= x == y
        print(f"      n={n:>9,}  enumerate {tb * 1000:8.1f} ms   combinatorics {tc * 1e6:6.1f} µs")
    t0 = time.perf_counter(); special_digit_dp(big); td = time.perf_counter() - t0
    t0 = time.perf_counter(); sol.countSpecialNumbers(big); tc = time.perf_counter() - t0
    print(f"      n=2*10^9    digit DP {td * 1000:6.1f} ms   combinatorics {tc * 1e6:6.1f} µs")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
