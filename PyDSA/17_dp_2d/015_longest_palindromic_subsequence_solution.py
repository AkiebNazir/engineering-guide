"""
================================================================================
SOLUTION · LeetCode 516 · Longest Palindromic Subsequence               [Medium]
https://leetcode.com/problems/longest-palindromic-subsequence/
================================================================================

THE CORE IDEA
--------------
Interval DP over ranges [i, j]:

    dp[i][j] = dp[i+1][j-1] + 2                 if s[i] == s[j]
             = max(dp[i+1][j], dp[i][j-1])      otherwise
    dp[i][i] = 1

Matching ends wrap whatever palindrome fits inside. Mismatched ends can't both
be in the answer, so the best of dropping either end wins. Fill i from the
BOTTOM row up so dp[i+1][...] is always ready.


================================================================================
APPROACH 1 · Try every subsequence (priced, used as oracle)
================================================================================
Check all 2^n subsequences for being palindromes.

    Time: O(2^n * n)    Space: O(n)


================================================================================
APPROACH 2 · Top-down memoized recursion
================================================================================
    @cache
    def lps(i, j):
        if i > j:  return 0
        if i == j: return 1
        if s[i] == s[j]: return lps(i + 1, j - 1) + 2
        return max(lps(i + 1, j), lps(i, j - 1))

    Time: O(n^2)    Space: O(n^2) cache + O(n) recursion depth

Easiest to derive, but the recursion can go about n frames deep. Measured on
this machine (Python 3.13, default recursion limit 1000): n = 1000 completed,
n = 3000 raised RecursionError. The bottom-up table never has to think about
it.


================================================================================
APPROACH 3 · Bottom-up table ✅ (the answer)
================================================================================
    dp = [[0] * n for _ in range(n)]
    for i in range(n - 1, -1, -1):
        dp[i][i] = 1
        for j in range(i + 1, n):
            if s[i] == s[j]:
                dp[i][j] = dp[i + 1][j - 1] + 2
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])
    return dp[0][n - 1]

When j == i + 1 and s[i] == s[j], dp[i+1][j-1] is dp[i+1][i], a "reversed"
empty range that's still 0 in the table. So "aa" gives 2 with no special case.

    Time: O(n^2)    Space: O(n^2)


================================================================================
APPROACH 4 · Rolling row, O(n) space
================================================================================
Row i only needs row i + 1. Keep one array `dp` (row i+1) and overwrite it left
to right into row i, saving the diagonal dp[i+1][j-1] before it's overwritten:

    dp = [0] * n
    for i in range(n - 1, -1, -1):
        dp[i] = 1
        prev_diag = 0                 # dp[i+1][i] (empty range)
        for j in range(i + 1, n):
            saved = dp[j]             # dp[i+1][j], becomes next diagonal
            dp[j] = prev_diag + 2 if s[i] == s[j] else max(dp[j], dp[j - 1])
            prev_diag = saved

    Time: O(n^2)    Space: O(n)


================================================================================
APPROACH 5 · LCS(s, reversed(s))
================================================================================
A palindromic subsequence reads the same forwards and backwards, so it's a
common subsequence of s and reversed(s). Conversely, the LCS of the two has the
same length as the LPS. Reuse LCS (17_dp_2d/005). Same O(n^2).


================================================================================
STEP BY STEP TRACE · s = "cbbd"
================================================================================
          j:  0(c)  1(b)  2(b)  3(d)
    i=3 (d)                      1
    i=2 (b)               1      max(dp[3][3], dp[2][2]) = 1
    i=1 (b)         1     2      max(dp[2][3], dp[1][2]) = 2
                          ^ s[1]==s[2]: dp[2][1] + 2 = 0 + 2
    i=0 (c)   1     1     2      2
                    ^ c != b: max(dp[1][1], dp[0][0]) = 1

    answer dp[0][3] = 2


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                 Time        Space    Mutates input?
    -----------------------  ----------  -------  --------------
    All subsequences         O(2^n * n)  O(n)     No
    Memoized recursion       O(n^2)      O(n^2)   No (depth ~n)
    Bottom-up table ✅       O(n^2)      O(n^2)   No
    Rolling row              O(n^2)      O(n)     No
    LCS with reverse         O(n^2)      O(n)     No


================================================================================
EDGE CASES
================================================================================
    Single character    1
    Two equal chars     2 — relies on the empty-range dp[i+1][i] == 0.
    All distinct        1
    Already palindrome  n
    n = 1000            10^6 cells — fine bottom-up, deep for recursion.


================================================================================
COMMON MISTAKES
================================================================================
1. Solving SUBSTRING instead of SUBSEQUENCE. "bbbab" -> 3 instead of 4. Demo.

2. Filling i ASCENDING. dp[i+1][j-1] is read before it's computed (still 0),
   so matches only ever add 2 to nothing. Demo.

3. For s[i] == s[j], also taking max with dp[i+1][j] / dp[i][j-1]. Not wrong,
   just unnecessary: using both matching ends is always at least as good.

4. Relying on memoized recursion close to the recursion limit. It passed at
   n = 1000 here and failed at n = 3000. Demo.

5. In the rolling version, forgetting to save the diagonal before overwriting.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the palindrome itself?
A: Walk the full table from (0, n-1): on a match take both ends and move to
   (i+1, j-1); otherwise move toward the larger neighbor.

Q: Minimum insertions to make s a palindrome (LC 1312)?
A: n - LPS(s).

Q: Minimum deletions to make s a palindrome?
A: Also n - LPS(s).

Q: Count palindromic subsequences (LC 730)?
A: Same interval structure, counting instead of maximizing, with care for
   duplicates.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 5     Longest Palindromic Substring (16_dp_1d/007)  — contiguous version
    LC 1143  Longest Common Subsequence (005)
    LC 1312  Minimum Insertion Steps to Make a String Palindrome
    LC 312   Burst Balloons (013)                           — interval DP
================================================================================
"""

import random
import sys
import time
from functools import cache
from itertools import combinations


class Solution:
    def longestPalindromeSubseq(self, s: str) -> int:
        n = len(s)
        dp = [[0] * n for _ in range(n)]
        for i in range(n - 1, -1, -1):
            row, below = dp[i], dp[i + 1] if i + 1 < n else None
            row[i] = 1
            si = s[i]
            for j in range(i + 1, n):
                if si == s[j]:
                    row[j] = below[j - 1] + 2
                else:
                    row[j] = below[j] if below[j] > row[j - 1] else row[j - 1]
        return dp[0][n - 1]


# ------------------------------------------------------------------------
# Alternatives / oracle / broken versions for the demos.
# ------------------------------------------------------------------------
def lps_rolling(s: str) -> int:
    n = len(s)
    dp = [0] * n
    for i in range(n - 1, -1, -1):
        dp[i] = 1
        prev_diag = 0
        for j in range(i + 1, n):
            saved = dp[j]
            dp[j] = prev_diag + 2 if s[i] == s[j] else max(dp[j], dp[j - 1])
            prev_diag = saved
    return dp[n - 1]


def lps_lcs_reverse(s: str) -> int:
    t = s[::-1]
    n = len(s)
    prev = [0] * (n + 1)
    for i in range(1, n + 1):
        cur = [0] * (n + 1)
        for j in range(1, n + 1):
            cur[j] = prev[j - 1] + 1 if s[i - 1] == t[j - 1] else max(prev[j], cur[j - 1])
        prev = cur
    return prev[n]


def lps_memo(s: str) -> int:
    @cache
    def go(i: int, j: int) -> int:
        if i > j:
            return 0
        if i == j:
            return 1
        if s[i] == s[j]:
            return go(i + 1, j - 1) + 2
        return max(go(i + 1, j), go(i, j - 1))
    return go(0, len(s) - 1)


def lps_brute(s: str) -> int:
    n = len(s)
    for length in range(n, 0, -1):
        for idx in combinations(range(n), length):
            sub = [s[k] for k in idx]
            if sub == sub[::-1]:
                return length
    return 0


def longest_palindromic_substring_len(s: str) -> int:
    """Mistake 1: the CONTIGUOUS problem (expand around center)."""
    best = 0
    for c in range(2 * len(s) - 1):
        lo, hi = c // 2, (c + 1) // 2
        while lo >= 0 and hi < len(s) and s[lo] == s[hi]:
            lo -= 1
            hi += 1
        best = max(best, hi - lo - 1)
    return best


def lps_wrong_order_bug(s: str) -> int:
    """Mistake 2: fills rows top to bottom, reading dp[i+1] before it exists."""
    n = len(s)
    dp = [[0] * n for _ in range(n)]
    for i in range(n):                                  # BUG: must go n-1 .. 0
        dp[i][i] = 1
        for j in range(i + 1, n):
            if s[i] == s[j]:
                dp[i][j] = (dp[i + 1][j - 1] if i + 1 <= j - 1 else 0) + 2
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])
    return dp[0][n - 1]


# ==============================================================================
# TESTS — run:  python 015_longest_palindromic_subsequence_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: table vs rolling row vs LCS(s, reverse) vs memo ---")
    cases = [("bbbab", 4), ("cbbd", 2), ("a", 1), ("ab", 1), ("aa", 2),
             ("character", 5), ("abcdef", 1), ("agbdba", 5)]
    for s, want in cases:
        results = (sol.longestPalindromeSubseq(s), lps_rolling(s), lps_lcs_reverse(s), lps_memo(s))
        ok = all(r == want for r in results)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  s={s!r:<12} got={results}  want={want}")

    print("\n--- randomized cross-check vs brute force over all subsequences (400 strings) ---")
    rng = random.Random(516)
    bad = 0
    for _ in range(400):
        s = "".join(rng.choice("abc") for _ in range(rng.randint(1, 12)))
        want = lps_brute(s)
        if sol.longestPalindromeSubseq(s) != want or lps_rolling(s) != want or lps_lcs_reverse(s) != want:
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  400 random strings agree with brute force")

    print("\n--- mistakes LIVE ---")
    w1 = longest_palindromic_substring_len("bbbab")
    ok = w1 == 3 and sol.longestPalindromeSubseq("bbbab") == 4
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  substring instead of subsequence: 'bbbab' -> {w1} ('bbb'), want 4 ('bbbb')")
    w2 = lps_wrong_order_bug("agbdba")
    ok = w2 != 5 and sol.longestPalindromeSubseq("agbdba") == 5
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  rows filled top-down:             'agbdba' -> {w2}, want 5 ('abdba')")

    print("\n--- memoized recursion depth vs CPython's recursion limit ---")
    for n in (1000, 3000):
        probe = "".join(rng.choice("ab") for _ in range(n))
        try:
            lps_memo(probe)
            outcome = "completed"
        except RecursionError:
            outcome = "RecursionError"
        print(f"      n={n}, recursion limit {sys.getrecursionlimit()}: memoized version -> {outcome}")
    s = "".join(rng.choice("ab") for _ in range(1000))
    ok = sol.longestPalindromeSubseq(s) == lps_rolling(s)
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  bottom-up table and rolling row agree at n = 1000")

    print("\n--- benchmark at n = 1000: table vs rolling row vs LCS form ---")
    for name, fn in (("2D table   ", sol.longestPalindromeSubseq), ("rolling row", lps_rolling),
                     ("LCS reverse", lps_lcs_reverse)):
        t0 = time.perf_counter(); fn(s); dt = time.perf_counter() - t0
        print(f"      {name}  {dt * 1000:7.1f} ms")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
