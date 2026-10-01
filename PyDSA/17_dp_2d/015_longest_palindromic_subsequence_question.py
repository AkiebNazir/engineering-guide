"""
================================================================================
LeetCode 516 · Longest Palindromic Subsequence                          [Medium]
https://leetcode.com/problems/longest-palindromic-subsequence/
Topic: 17 · Dynamic Programming (2D)
================================================================================

PROBLEM
-------
Given a string s, find the length of the longest palindromic SUBSEQUENCE in s.

A subsequence can be derived from another sequence by deleting some or no
elements without changing the order of the remaining elements.


EXAMPLES
--------
Example 1:   s = "bbbab"   ->  4    ("bbbb")
Example 2:   s = "cbbd"    ->  2    ("bb")


CONSTRAINTS
-----------
    1 <= s.length <= 1000
    s consists only of lowercase English letters.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
SUBSEQUENCE, not substring. In "bbbab", the longest palindromic SUBSTRING
(contiguous) is "bbb" (length 3). The longest palindromic SUBSEQUENCE skips the
'a' and gets "bbbb" (length 4). Problem 16_dp_1d/007 is the substring version;
don't mix them up.

This is INTERVAL DP. The state is a range [i, j] of the string:

    dp[i][j] = length of the longest palindromic subsequence of s[i..j]

Look at the two ends:
    s[i] == s[j]  -> both ends can wrap a palindrome from the inside:
                     dp[i][j] = dp[i+1][j-1] + 2
    s[i] != s[j]  -> they can't both be used; drop one:
                     dp[i][j] = max(dp[i+1][j], dp[i][j-1])

Base: dp[i][i] = 1 (a single character), and dp[i][i-1] = 0 (empty range).


WHAT TO THINK ABOUT
--------------------
1. dp[i][j] depends on dp[i+1][...] (a LATER row) and dp[...][j-1] (an EARLIER
   column). In what order must you fill the table?

2. Can you express this as Longest Common Subsequence with some other string?

3. The table is n x n = 10^6 cells. Can you keep just one row?


PROGRESSIVE HINTS
------------------
Hint 1: Loop i from n-1 DOWN to 0, and j from i+1 UP to n-1.

Hint 2: LPS(s) == LCS(s, reversed(s)).

Hint 3: Rolling array: dp[j] holds row i+1 before you overwrite it; save the
        old dp[j-1] (the diagonal) in a variable before updating.


COMPLEXITY TARGET
------------------
    Time:  O(n^2)
    Space: O(n^2), or O(n) with a rolling row
================================================================================
"""


class Solution:
    def longestPalindromeSubseq(self, s: str) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 015_longest_palindromic_subsequence_question.py
# ==============================================================================
def run_tests() -> None:
    cases = [
        ("bbbab", 4),
        ("cbbd", 2),
        ("a", 1),
        ("ab", 1),
        ("aa", 2),
        ("character", 5),
        ("abcdef", 1),
        ("agbdba", 5),
    ]
    all_ok = True
    for s, want in cases:
        got = Solution().longestPalindromeSubseq(s)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  s={s!r}  got={got}  want={want}")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
