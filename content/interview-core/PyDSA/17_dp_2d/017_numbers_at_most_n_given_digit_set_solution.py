"""
================================================================================
SOLUTION · LeetCode 902 · Numbers At Most N Given Digit Set               [Hard]
https://leetcode.com/problems/numbers-at-most-n-given-digit-set/
================================================================================

THE CORE IDEA
--------------
DIGIT DP. Build candidates from the most significant digit, tracking whether
the prefix is still TIGHT (equal to n's prefix). Two parts:

    shorter numbers:  sum of D^L for L = 1 .. len(n) - 1       (all are < n)
    same length:      walk n's digits; at position i add
                      (#allowed digits < n[i]) * D^(digits remaining)
                      continue only if n[i] is allowed; if you finish, +1 for n


================================================================================
APPROACH 1 · Enumerate 1..n (priced, used as oracle)
================================================================================
    sum(1 for x in range(1, n + 1) if set(str(x)) <= allowed)

    Time: O(n log n) — 10^9 numbers is hopeless.    Space: O(1)


================================================================================
APPROACH 2 · Direct counting ✅ (the answer)
================================================================================
    s, D = str(n), len(digits)
    L = len(s)
    total = sum(D ** k for k in range(1, L))
    for i, c in enumerate(s):
        smaller = sum(d < c for d in digits)
        total += smaller * D ** (L - i - 1)
        if c not in digits:
            return total
    return total + 1

WHY STOP WHEN n[i] IS NOT ALLOWED. To stay tight you must place exactly n[i].
If that digit isn't allowed, the only same-length numbers left are ones already
counted by the "smaller digit" terms. There's nothing more to add.

WHY +1 AT THE END. Surviving the loop means every digit of n is allowed, so n
itself is a valid number and hasn't been counted yet.

    Time: O(L * D) with L <= 10, D <= 9    Space: O(1)


================================================================================
APPROACH 3 · The general digit-DP template: f(pos, tight)
================================================================================
    @cache
    def f(pos, tight, started):
        if pos == L:
            return 1 if started else 0          # count real numbers only
        limit = s[pos] if tight else '9'
        total = 0
        if not started:
            total += f(pos + 1, False, False)   # keep skipping (shorter number)
        for d in digits:
            if d > limit: break
            total += f(pos + 1, tight and d == limit, True)
        return total

This is the SAME count, written as the reusable template:
    pos      which digit we're placing
    tight    are we still bounded by n?
    started  have we placed a non-leading digit yet? (handles shorter numbers)
Add a `mask` for "digits used so far" and you get Count Special Integers
(018). Add a running remainder and you get "count multiples of k <= n".

    Time: O(L * 2 * 2 * D)    Space: O(L * 4)


================================================================================
STEP BY STEP TRACE · digits = ["1","3","5","7"], n = 100
================================================================================
    s = "100", L = 3, D = 4

    shorter: D^1 + D^2 = 4 + 16 = 20

    i=0, c='1': smaller digits than '1' -> 0   add 0 * 4^2 = 0
                '1' allowed -> stay tight
    i=1, c='0': smaller than '0' -> 0          add 0
                '0' NOT allowed -> return 20

    answer: 20   (no 3-digit number <= 100 uses only 1,3,5,7)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time           Space   Mutates input?
    ------------------------------  -------------  ------  --------------
    Enumerate 1..n                  O(n log n)     O(1)    No
    Direct counting ✅              O(L * D)       O(1)    No
    Memoized f(pos, tight, started) O(L * D)       O(L)    No


================================================================================
EDGE CASES
================================================================================
    n smaller than every digit     0 (e.g. digits ["7"], n = 6).
    n is exactly formable          +1 at the end (digits ["7"], n = 7 -> 1).
    n has a 0 digit                The walk stops there: no digit is < '0'.
    Single-digit n                 No "shorter" part.
    n = 10^9                       10 digits; D^9 fits easily.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting the +1 for n itself. digits ["7"], n = 7 returns 0. Demo.

2. Forgetting the shorter-length numbers. ["1","3","5","7"], n = 100 returns 0
   instead of 20. Demo.

3. Continuing the walk after hitting a digit that isn't allowed (treating it
   as if you could stay tight).

4. Using <= instead of < for "smaller" digits, which double-counts the tight
   branch.

5. Enumerating up to n. Fine for n = 10^4, times out at 10^9.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Count in a range [lo, hi]?
A: count(hi) - count(lo - 1). Every digit DP range question uses this.

Q: Digits may include '0'?
A: Leading zeros now matter: use the `started` flag, and zero can't be the first
   placed digit.

Q: Count numbers <= n with digit sum == S?
A: State (pos, tight, sum_so_far). O(L * 2 * S * 10).


================================================================================
RELATED PROBLEMS
================================================================================
    LC 2376  Count Special Integers (018)       — digit DP with a used-digits mask
    LC 233   Number of Digit One                — count occurrences of a digit
    LC 600   Non-negative Integers without Consecutive Ones — digit DP in binary
    LC 1012  Numbers With Repeated Digits        — complement of LC 2376
================================================================================
"""

import random
import time
from functools import cache
from typing import List


class Solution:
    def atMostNGivenDigitSet(self, digits: List[str], n: int) -> int:
        s = str(n)
        L, D = len(s), len(digits)
        total = sum(D ** k for k in range(1, L))
        for i, c in enumerate(s):
            smaller = sum(d < c for d in digits)
            total += smaller * D ** (L - i - 1)
            if c not in digits:
                return total
        return total + 1


# ------------------------------------------------------------------------
# Alternatives / oracle / broken versions for the demos.
# ------------------------------------------------------------------------
def at_most_template(digits: List[str], n: int) -> int:
    s = str(n)
    L = len(s)

    @cache
    def f(pos: int, tight: bool, started: bool) -> int:
        if pos == L:
            return 1 if started else 0
        limit = s[pos] if tight else "9"
        total = 0
        if not started:
            total += f(pos + 1, False, False)
        for d in digits:
            if d > limit:
                break
            total += f(pos + 1, tight and d == limit, True)
        return total

    return f(0, True, False)


def at_most_brute(digits: List[str], n: int) -> int:
    allowed = set(digits)
    return sum(1 for x in range(1, n + 1) if set(str(x)) <= allowed)


def at_most_no_plus_one_bug(digits: List[str], n: int) -> int:
    s = str(n)
    L, D = len(s), len(digits)
    total = sum(D ** k for k in range(1, L))
    for i, c in enumerate(s):
        total += sum(d < c for d in digits) * D ** (L - i - 1)
        if c not in digits:
            return total
    return total                                          # BUG: n itself not counted


def at_most_no_shorter_bug(digits: List[str], n: int) -> int:
    s = str(n)
    L, D = len(s), len(digits)
    total = 0                                             # BUG: shorter numbers ignored
    for i, c in enumerate(s):
        total += sum(d < c for d in digits) * D ** (L - i - 1)
        if c not in digits:
            return total
    return total + 1


# ==============================================================================
# TESTS — run:  python 017_numbers_at_most_n_given_digit_set_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: direct counting vs digit-DP template ---")
    cases = [
        (["1", "3", "5", "7"], 100, 20),
        (["1", "4", "9"], 1000000000, 29523),
        (["7"], 8, 1),
        (["7"], 7, 1),
        (["7"], 6, 0),
        (["3", "4", "8"], 4, 2),
        (["1", "2", "3"], 321, 34),
        (["5", "6"], 19, 2),
    ]
    for digits, n, want in cases:
        a, b = sol.atMostNGivenDigitSet(digits, n), at_most_template(digits, n)
        ok = a == b == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  digits={digits} n={n}  direct={a}  template={b}  want={want}")

    print("\n--- randomized cross-check vs enumerating 1..n (500 cases, n <= 50,000) ---")
    rng = random.Random(902)
    bad = 0
    for _ in range(500):
        digits = sorted(rng.sample("123456789", rng.randint(1, 9)))
        n = rng.randint(1, 50_000)
        want = at_most_brute(digits, n)
        if sol.atMostNGivenDigitSet(digits, n) != want or at_most_template(digits, n) != want:
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  500 random cases agree with brute force")

    print("\n--- mistakes LIVE ---")
    w1 = at_most_no_plus_one_bug(["7"], 7)
    ok = w1 == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  no +1 for n itself:      digits ['7'], n=7 -> {w1} (want 1)")
    w2 = at_most_no_shorter_bug(["1", "3", "5", "7"], 100)
    ok = w2 == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  no shorter-length count: digits [1,3,5,7], n=100 -> {w2} (want 20)")

    print("\n--- benchmark: enumeration vs digit DP ---")
    digits = ["1", "3", "5", "7", "9"]
    for n in (10**4, 10**5, 10**6):
        t0 = time.perf_counter(); a = at_most_brute(digits, n); tb = time.perf_counter() - t0
        t0 = time.perf_counter(); b = sol.atMostNGivenDigitSet(digits, n); td = time.perf_counter() - t0
        all_ok &= a == b
        print(f"      n={n:>9,}  enumerate {tb * 1000:8.1f} ms   digit DP {td * 1e6:6.1f} µs   count={b}")
    t0 = time.perf_counter(); r = sol.atMostNGivenDigitSet(digits, 10**9); td = time.perf_counter() - t0
    print(f"      n=1,000,000,000 digit DP {td * 1e6:.1f} µs   count={r}  (enumeration would take ~1000x the n=10^6 time)")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
