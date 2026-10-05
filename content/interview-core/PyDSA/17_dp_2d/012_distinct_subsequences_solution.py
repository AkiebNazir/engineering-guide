"""
================================================================================
SOLUTION · LeetCode 115 · Distinct Subsequences                          [Hard]
https://leetcode.com/problems/distinct-subsequences/
================================================================================

THE CORE IDEA
--------------
dp[i][j] = number of distinct subsequences of s[:i] that equal t[:j]. This
is a COUNTING member of the "two strings, two indices" family (005 LCS, 009,
010), combined with SUM (like 007's Coin Change II) instead of max/min/or.

Consider the LAST character of s[:i], s[i-1] -- it can be handled TWO
independent ways, and BOTH must be counted (they build different
subsequences, never the same one):

    Always: SKIP s[i-1] entirely  -> contributes dp[i-1][j] ways
            (every way to match t[:j] using only the first i-1 chars of s)
    If s[i-1] == t[j-1]: ALSO use s[i-1] as the match for t's last char
            -> contributes dp[i-1][j-1] ways ON TOP of the skip option

    dp[i][j] = dp[i-1][j] + (dp[i-1][j-1] if s[i-1] == t[j-1] else 0)

Base case: dp[i][0] = 1 for every i (exactly one way to match the empty
string -- use none of s's characters). dp[0][j>0] = 0 (an empty s can't
produce any non-empty t).


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, not coded): recursively try, at each
position in s, "skip this char" or (if it matches) "use this char," count
paths that fully consume t. O(2^len(s)) time -- the same (i, j) state is
reached via many different skip/use decision orderings, massively
overlapping.

Approach 1 (memoized top-down, 2D cache) -- recurse on (i, j), cache each
count. O(len(s)*len(t)) time, O(len(s)*len(t)) space (memo + recursion
depth len(s)+len(t)).

Approach 2 (bottom-up tabulation, full 2D table) [checked] -- fill dp row
by row using the skip/use-if-match recurrence. O(len(s)*len(t)) time,
O(len(s)*len(t)) space.

Approach 3 (space-optimized, rolling 1D row, j swept HIGH to LOW)
[checked, shipped] -- dp[i][j] only reads the row ABOVE (dp[i-1][j],
dp[i-1][j-1]) -- never the current row. To update one array in place while
still reading OLD (previous-row) values, sweep j from len(t) down to 1: by
the time row[j] is computed, row[j-1] has not yet been touched this pass,
so it still holds dp[i-1][j-1]. O(len(s)*len(t)) time, O(len(t)) space.


================================================================================
STEP BY STEP TRACE
================================================================================
s = "babgbag" (m=7), t = "bag" (n=3)

Full 2D table (rows = s prefixes 0..7, cols = t prefixes 0..3):

           ""  b  a  g
      "" :  1  0  0  0
      b  :  1  1  0  0     <- dp[1][1]=dp[0][1]+dp[0][0]('b'=='b')=0+1=1
      a  :  1  1  1  0     <- dp[2][2]=dp[1][2]+dp[1][1]('a'=='a')=0+1=1
      b  :  1  2  1  0     <- dp[3][1]=dp[2][1]+dp[2][0]('b'=='b')=1+1=2
      g  :  1  2  1  1     <- dp[4][3]=dp[3][3]+dp[3][2]('g'=='g')=0+1=1
      b  :  1  3  1  1     <- dp[5][1]=dp[4][1]+dp[4][0]('b'=='b')=2+1=3
      a  :  1  3  4  1     <- dp[6][2]=dp[5][2]+dp[5][1]('a'=='a')=1+3=4
      g  :  1  3  4  5     <- dp[7][3]=dp[6][3]+dp[6][2]('g'=='g')=1+4=5

Answer: dp[7][3] = 5.  MATCHES expected (5 distinct "bag" subsequences in
"babgbag": choosing which 'b' pairs with which 'a' and 'g' across the
repeated letters).


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time            Space          Mutates input?
    ---------------------------------  --------------  -------------  --------------
    Brute force recursion (no memo)    O(2^len(s))     O(len(s))      no
    Memoized top-down, 2D cache        O(len(s)*len(t))  O(len(s)*len(t))  no
    Bottom-up tabulation, full table   O(len(s)*len(t))  O(len(s)*len(t))  no
    Rolling row [chosen]               O(len(s)*len(t))  O(len(t))         no


================================================================================
EDGE CASES
================================================================================
    t is empty              -> exactly 1 way for every s (use no characters
                                at all) -- dp[i][0]=1 base case handles this
                                with no special-casing.
    s is empty, t non-empty -> 0 ways -- dp[0][j>0]=0 base case.
    len(t) > len(s)          -> answer is always 0 (can't select more
                                characters than exist) -- falls out of the
                                DP automatically, though it's a valid O(1)
                                early-exit optimization too.
    s == t                   -> exactly 1 way (use every character, no
                                skipping options exist for a perfect-length
                                match... unless characters repeat, see next).
    Repeated characters (e.g. s="aaaaa", t="aa") -> the DP correctly counts
                                EVERY distinct choice of WHICH positions are
                                used, e.g. C(5,2)=10 ways to choose 2 of 5
                                identical 'a's -- treats same-VALUE
                                characters at different POSITIONS as distinct
                                choices, matching the problem's "distinct
                                subsequences" definition (position-based, not
                                value-based).


================================================================================
COMMON MISTAKES
================================================================================
1. Taking MAX instead of SUM when s[i-1] == t[j-1] -- "skip this char" and
   "use this char to match" are NOT mutually exclusive alternatives to pick
   the better of (like LCS); they are two DIFFERENT valid subsequences that
   must BOTH be counted. Using max here silently undercounts.

2. Forgetting the "always skip" term dp[i-1][j] even on a character match --
   even when s[i-1]==t[j-1], you can still choose NOT to use this occurrence
   (saving it in case a later occurrence works better in combination with
   other choices) -- both branches must be added.

3. In the rolling-row version, sweeping j LOW to HIGH instead of HIGH to
   LOW -- since dp[i][j] never depends on dp[i][j-1] (only on the row
   ABOVE), sweeping low-to-high would overwrite row[j-1] with THIS row's
   value before row[j] reads it, silently reading the wrong (already
   advanced) row's data instead of the previous row's.

4. Confusing "distinct SUBSEQUENCES" (this problem, POSITION-based: two
   subsequences using different index sets count separately even if they
   spell the same substring) with "distinct SUBSTRINGS equal to t" (a
   different, contiguous-only counting problem).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How would you list the actual subsequences, not just count them?
A: Keep the full 2D table and walk backwards from dp[m][n], branching at
   every cell where BOTH the skip and use options contributed a nonzero
   count -- this can itself be exponential in the number of distinct
   subsequences, so it's only reasonable for small counts.

Q: What's the relationship to Longest Common Subsequence (005)?
A: Same two-index skeleton and the same "compare s[i-1] to t[j-1]" pivot,
   but LCS takes MAX over the mismatch branch (find the BEST single
   subsequence) while this problem takes SUM over both match branches
   (count ALL subsequences) -- LCS answers "does a match exist and how
   long," this answers "in how many distinct ways."

Q: Why must the answer fit in 32 bits per the constraints -- what's the
   growth rate?
A: In the worst case (s made of one repeated character, t a prefix of that
   repetition), the count is a binomial coefficient C(len(s), len(t)),
   which grows combinatorially -- the 32-bit guarantee is doing real
   constraint-tightening work here, not just boilerplate.

Q: Could this be solved with a sliding window or two pointers instead of DP?
A: No -- counting ALL distinct subsequences (not just checking existence)
   requires tracking cumulative counts across combinatorial choices, which
   two pointers (single pass, no state accumulation) cannot represent.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 1143  Longest Common Subsequence (005 -- same two-index skeleton,
             max instead of sum)
    LC 72    Edit Distance (010 -- same skeleton, min of three instead of
             sum of two)
    LC 518   Coin Change II (007 -- same "sum of independent choices"
             counting combinator, one-string-vs-target instead of two
             strings)
    LC 940   Distinct Subsequences II (single-string variant -- count
             distinct subsequences of s itself, not matches against a t)
================================================================================
"""


class Solution:
    def numDistinct(self, s: str, t: str) -> int:
        """✅ Rolling-row DP, j swept HIGH to LOW to preserve previous-row
        values while updating in place. O(len(s)*len(t)) time, O(len(t))
        space."""
        n = len(t)
        row = [0] * (n + 1)
        row[0] = 1  # dp[i][0] = 1 for every i, including i=0
        for ch in s:
            for j in range(n, 0, -1):
                if ch == t[j - 1]:
                    row[j] += row[j - 1]
        return row[n]

    def numDistinct_full_table(self, s: str, t: str) -> int:
        """Alternative: full 2D tabulation, O(len(s)*len(t)) time and
        space -- useful for tracing the skip/use decomposition explicitly."""
        m, n = len(s), len(t)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m + 1):
            dp[i][0] = 1
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                dp[i][j] = dp[i - 1][j]
                if s[i - 1] == t[j - 1]:
                    dp[i][j] += dp[i - 1][j - 1]
        return dp[m][n]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ("rabbbit", "rabbit", 3),
        ("babgbag", "bag", 5),
        ("", "", 1),
        ("abc", "", 1),
        ("", "abc", 0),
        ("aaaaa", "aa", 10),
    ]

    print("--- correctness: rolling row vs full table agree ---")
    for s, t, want in cases:
        got_roll = sol.numDistinct(s, t)
        got_full = sol.numDistinct_full_table(s, t)
        ok = got_roll == want and got_full == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  s={s!r} t={t!r} roll={got_roll} "
              f"full={got_full}  (want {want})")

    # --------------------------------------------------------------------
    # RUNTIME DEMO: prove mistake #1 (max instead of sum on a character
    # match) actually undercounts, live, on the canonical example.
    # --------------------------------------------------------------------
    print("\n--- DEMO: sum-of-both-branches (correct) vs max-of-both (buggy) ---")

    def num_distinct_buggy_max(s, t):
        m, n = len(s), len(t)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m + 1):
            dp[i][0] = 1
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s[i - 1] == t[j - 1]:
                    dp[i][j] = max(dp[i - 1][j], dp[i - 1][j - 1])  # BUG
                else:
                    dp[i][j] = dp[i - 1][j]
        return dp[m][n]

    s, t = "rabbbit", "rabbit"
    correct = sol.numDistinct(s, t)
    buggy = num_distinct_buggy_max(s, t)
    print(f"  s={s!r}, t={t!r}")
    print(f"  correct (sum of skip + use):  {correct}")
    print(f"  buggy   (max of skip vs use): {buggy}")
    print(f"  buggy undercounts: {buggy < correct}")
    all_ok &= (correct == 3)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
