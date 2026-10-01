"""
================================================================================
SOLUTION · LeetCode 1143 · Longest Common Subsequence                 [Medium]
https://leetcode.com/problems/longest-common-subsequence/
================================================================================

THE CORE IDEA
--------------
dp[i][j] = LCS length of text1[:i] and text2[:j] (prefix lengths, 1-indexed
so index 0 means the empty prefix). This is the CANONICAL two-string DP:
both string positions vary independently, so the state is genuinely 2D --
unlike topic 16's single-string dp[i][j] palindrome check (built from a
SMALLER interior of the SAME string), this one compares two DIFFERENT
strings advancing at independent rates.

    text1[i-1] == text2[j-1]:  dp[i][j] = dp[i-1][j-1] + 1
                                (this matching char extends the LCS found
                                 without it -- consume BOTH strings by one)
    text1[i-1] != text2[j-1]:  dp[i][j] = max(dp[i-1][j], dp[i][j-1])
                                (best of: drop text1's last char, or drop
                                 text2's last char -- keep the better LCS)

Base case: dp[0][*] = dp[*][0] = 0 (an empty prefix shares no characters
with anything).


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, not coded): for every one of the 2^len(text1)
subsequences of text1, check whether it's a subsequence of text2 (O(len(text2))
per check). O(2^m * n) time -- catastrophic, and doesn't even reuse the work
of overlapping subsequence prefixes.

Approach 1 (memoized top-down, 2D cache) -- recurse on (i, j) = "LCS of
text1[i:], text2[j:]", cache each (i,j) pair. O(m*n) time, O(m*n) space
(memo + recursion depth up to m+n).

Approach 2 (bottom-up tabulation, full 2D table) [checked] -- fill dp row by
row using the match/no-match recurrence above. O(m*n) time, O(m*n) space.

Approach 3 (space-optimized, rolling 1D row) [checked, shipped] -- dp[i][j]
only reads the row above (dp[i-1][j], dp[i-1][j-1]) and the current row's
left neighbor (dp[i][j-1]). Keep one row of length n+1 plus a single scalar
snapshotting the pre-overwrite diagonal (same trick as 004's maximal
square). O(m*n) time, O(n) space.


================================================================================
STEP BY STEP TRACE
================================================================================
text1 = "abcde" (m=5), text2 = "ace" (n=3)

Full 2D table (rows = text1 prefixes 0..5, cols = text2 prefixes 0..3):

          ""  a  c  e
      "" : 0  0  0  0
      a  : 0  1  1  1     <- text1[0]='a' matches text2[0]='a': dp=dp[0][0]+1=1
      b  : 0  1  1  1     <- 'b' matches nothing: dp[i][j]=max(above,left)
      c  : 0  1  2  2     <- 'c' matches text2[1]='c': dp=dp[1][1]+1=2
      d  : 0  1  2  2
      e  : 0  1  2  3     <- 'e' matches text2[2]='e': dp=dp[3][2]+1=3

Answer: dp[5][3] = 3.  MATCHES expected ("ace").


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time        Space      Mutates input?
    ---------------------------------  ----------  ---------  --------------
    Brute force (enumerate subseqs)    O(2^m * n)  O(m)       n/a (no input)
    Memoized top-down, 2D cache        O(m*n)      O(m*n)     n/a
    Bottom-up tabulation, full table   O(m*n)      O(m*n)     n/a
    Rolling row [chosen]               O(m*n)      O(n)       n/a


================================================================================
EDGE CASES
================================================================================
    Either string empty    -> LCS is 0 -- the base row/column of zeros
                               handles this with no special-casing.
    No characters in common -> dp never increments off the match branch,
                               stays 0 throughout, answer 0.
    Identical strings       -> LCS equals the full string length (every char
                               matches its own diagonal).
    Repeated characters (e.g. "aaaa" vs "aa") -> the DP naturally handles
                               this since it always consumes exactly one
                               character from EACH string on a match, never
                               double-counting a repeated letter.


================================================================================
COMMON MISTAKES
================================================================================
1. Comparing text1[i] to text2[j] instead of text1[i-1] to text2[j-1] -- the
   dp indices are 1-indexed PREFIX LENGTHS, so dp[i][j] corresponds to the
   characters at position i-1 and j-1 in the 0-indexed strings.

2. Confusing "longest common SUBSEQUENCE" (this problem, characters need not
   be contiguous) with "longest common SUBSTRING" (a different, contiguous-
   only problem whose recurrence resets to 0 on any mismatch instead of
   taking a max).

3. On a mismatch, taking max(dp[i-1][j-1], ...) instead of
   max(dp[i-1][j], dp[i][j-1]) -- the diagonal is only ever used on an
   actual character MATCH; skipping a character from one string alone is
   what the up/left neighbors represent.

4. Allocating dp with the wrong dimensions -- must be (m+1) x (n+1), not
   m x n, to leave room for the "empty prefix" row/column at index 0.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you reconstruct the actual LCS string, not just its length?
A: Keep the full 2D table and walk backwards from dp[m][n]: on a character
   match, step diagonally and record it; otherwise step toward whichever of
   dp[i-1][j] / dp[i][j-1] is larger.

Q: How does this relate to Edit Distance (010)?
A: Same "two strings, two indices" DP skeleton and the same dp[m][n]
   table shape, but Edit Distance's recurrence allows insert/delete/replace
   operations (min of three neighbors +1) instead of only "match or skip"
   (max of two neighbors, or +1 on match) -- LCS never "replaces," it only
   ever agrees or disagrees.

Q: What about Shortest Common Supersequence?
A: LC 1092 -- the shortest string containing both text1 and text2 as
   subsequences. Its length is len(text1) + len(text2) - LCS(text1, text2)
   (share the LCS once, append the rest of both strings around it).

Q: Can you do it in O(min(m,n)) space?
A: Yes -- always make the rolling row the length of the SHORTER string, and
   iterate the longer string as the outer loop (Approach 3, orientation
   chosen to minimize the row's length).


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 72    Edit Distance (010 -- same two-index skeleton, insert/delete/
             replace recurrence instead of match/skip)
    LC 97    Interleaving String (009 -- same skeleton, boolean instead of
             length)
    LC 1092  Shortest Common Supersequence (LCS length feeds directly in)
    LC 583   Delete Operation for Two Strings (answer = m + n - 2*LCS)
    LC 674   Longest Increasing Subsequence (1D cousin -- topic 16, single
             string, no second independent axis)
================================================================================
"""


class Solution:
    def longestCommonSubsequence(self, text1: str, text2: str) -> int:
        """✅ Rolling-row DP, oriented so the row spans the SHORTER string.
        O(m*n) time, O(min(m,n)) space."""
        if len(text1) < len(text2):
            text1, text2 = text2, text1  # text2 is now the shorter one
        m, n = len(text1), len(text2)

        row = [0] * (n + 1)
        for i in range(1, m + 1):
            prev_diag = 0  # dp[i-1][0] is always 0
            c1 = text1[i - 1]
            for j in range(1, n + 1):
                up = row[j]  # dp[i-1][j] before this cell overwrites it
                if c1 == text2[j - 1]:
                    row[j] = prev_diag + 1
                else:
                    row[j] = max(up, row[j - 1])
                prev_diag = up
        return row[-1]

    def longestCommonSubsequence_full_table(self, text1: str, text2: str) -> int:
        """Alternative: full 2D tabulation, O(m*n) time and space -- useful
        when the actual LCS string also needs to be reconstructed."""
        m, n = len(text1), len(text2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if text1[i - 1] == text2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
        return dp[m][n]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ("abcde", "ace", 3),
        ("abc", "abc", 3),
        ("abc", "def", 0),
        ("", "abc", 0),
        ("bl", "yby", 1),
        ("abcba", "abcbcba", 5),
    ]

    print("--- correctness: rolling-row vs full-table agree ---")
    for t1, t2, want in cases:
        got_roll = sol.longestCommonSubsequence(t1, t2)
        got_full = sol.longestCommonSubsequence_full_table(t1, t2)
        ok = got_roll == want and got_full == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  text1={t1!r} text2={t2!r} "
              f"roll={got_roll} full={got_full}  (want {want})")

    # --------------------------------------------------------------------
    # RUNTIME DEMO: measure real speedup from orienting the rolling row
    # over the SHORTER string (row length = min(m,n)) vs the longer one.
    # --------------------------------------------------------------------
    import time
    import random
    print("\n--- DEMO: rolling row over shorter string vs longer string ---")
    random.seed(0)
    long_s = "".join(random.choice("abcd") for _ in range(2000))
    short_s = "".join(random.choice("abcd") for _ in range(50))

    def lcs_oriented(a, b):
        """Row spans len(b); caller controls which string is 'b'."""
        m, n = len(a), len(b)
        row = [0] * (n + 1)
        for i in range(1, m + 1):
            prev_diag = 0
            ca = a[i - 1]
            for j in range(1, n + 1):
                up = row[j]
                row[j] = prev_diag + 1 if ca == b[j - 1] else max(up, row[j - 1])
                prev_diag = up
        return row[-1]

    t0 = time.perf_counter()
    r1 = lcs_oriented(long_s, short_s)  # row length = 50 (short)
    t_short_row = time.perf_counter() - t0

    t0 = time.perf_counter()
    r2 = lcs_oriented(short_s, long_s)  # row length = 2000 (long)
    t_long_row = time.perf_counter() - t0

    print(f"  |long_s|={len(long_s)}, |short_s|={len(short_s)}")
    print(f"  row over shorter string: {t_short_row * 1000:.3f} ms, result={r1}")
    print(f"  row over longer string:  {t_long_row * 1000:.3f} ms, result={r2}")
    print(f"  same result both orientations: {r1 == r2}")
    print(f"  (total work O(m*n) is identical either way -- what differs is "
          f"only the row's memory footprint, min(m,n) vs max(m,n))")
    all_ok &= (r1 == r2)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
