"""
================================================================================
QUESTION · LeetCode 115 · Distinct Subsequences                         [Hard]
https://leetcode.com/problems/distinct-subsequences/
================================================================================

PROBLEM
-------
Given two strings s and t, return the number of distinct subsequences of s
which equal t.

The test cases are generated so that the answer fits on a 32-bit signed
integer.


EXAMPLES
--------
Example 1:
    Input:  s = "rabbbit", t = "rabbit"
    Output: 3
    Explanation: there are 3 ways you can generate "rabbit" from s:
        raBBbit, raBbBit, rabBBit  (choosing different b's to drop)

Example 2:
    Input:  s = "babgbag", t = "bag"
    Output: 5


CONSTRAINTS
-----------
    1 <= s.length, t.length <= 1000
    s and t consist of English letters.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Another "two strings, two indices" DP (family with 005 LCS, 009, 010), but
COUNTING, like 007 (Coin Change II) -- the combinator is SUM, not max/min/or.

dp[i][j] = number of distinct subsequences of s[:i] that equal t[:j].
Consider the LAST character of s[:i], s[i-1]:
- You can always CHOOSE TO SKIP it: that contributes dp[i-1][j] ways (every
  way to match t[:j] using only s[:i-1]).
- If s[i-1] == t[j-1], you can ALSO choose to USE it as the match for
  t[j-1]: that contributes dp[i-1][j-1] ways.
So: dp[i][j] = dp[i-1][j] + (dp[i-1][j-1] if s[i-1]==t[j-1] else 0).

Note this ADDS the two options (both are valid, independent ways of
building a subsequence) rather than taking a max/min -- "skip s[i-1]" and
"use s[i-1] to match t[j-1]" are never the same subsequence, so they must
both be counted.

PROGRESSIVE HINTS
------------------
Hint 1: dp[i][j] = number of ways s[:i]'s subsequences equal t[:j] exactly.
Hint 2: s[i-1] can ALWAYS be skipped -- that alone contributes dp[i-1][j].
Hint 3: If s[i-1] == t[j-1], s[i-1] can ADDITIONALLY be used to match
        t[j-1] -- add dp[i-1][j-1] on top of the skip contribution.
Hint 4: Base case: dp[i][0] = 1 for all i (exactly one way to match the
        empty string: use no characters). dp[0][j] = 0 for j > 0 (an empty
        s can't produce any non-empty t).
Hint 5: Note len(t) > len(s) makes the answer trivially 0 -- a useful
        early-exit sanity check, though the DP handles it correctly anyway.

COMPLEXITY TARGET
------------------
    Time:  O(len(s) * len(t))
    Space: O(len(t))  (rolling row)
================================================================================
"""


class Solution:
    def numDistinct(self, s: str, t: str) -> int:
        # YOUR CODE HERE
        pass


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
    for s, t, want in cases:
        got = sol.numDistinct(s, t)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  s={s!r} t={t!r} -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
