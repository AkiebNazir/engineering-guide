"""
================================================================================
QUESTION · LeetCode 97 · Interleaving String                         [Medium]
https://leetcode.com/problems/interleaving-string/
================================================================================

PROBLEM
-------
Given strings s1, s2, and s3, find whether s3 is formed by an interleaving
of s1 and s2.

An interleaving of two strings s and t is a configuration where s and t are
divided into n and m substrings respectively, such that:
- s = s1 + s2 + ... + sn
- t = t1 + t2 + ... + tm
- |n - m| <= 1
- The interleaving is s1 + t1 + s2 + t2 + ... or t1 + s1 + t2 + s2 + ...

Note: a + b is the concatenation of strings a and b.


EXAMPLES
--------
Example 1:
    Input:  s1 = "aabcc", s2 = "dbbca", s3 = "aadbbcbcac"
    Output: true

Example 2:
    Input:  s1 = "aabcc", s2 = "dbbca", s3 = "aadbbbaccc"
    Output: false

Example 3:
    Input:  s1 = "", s2 = "", s3 = ""
    Output: true


CONSTRAINTS
-----------
    0 <= s1.length, s2.length <= 100
    0 <= s3.length <= 200
    s1, s2, and s3 consist of lowercase English letters.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Note that a mathematical necessary condition is len(s1)+len(s2)==len(s3) --
check that first, it's a free O(1) rejection.

dp[i][j] = can the first (i+j) characters of s3 be formed by interleaving
the first i characters of s1 with the first j characters of s2? The LAST
character of that s3 prefix (s3[i+j-1]) must have come from EITHER the end
of the s1 prefix OR the end of the s2 prefix:

    dp[i][j] = (dp[i-1][j] AND s1[i-1] == s3[i+j-1])   # last char from s1
            OR (dp[i][j-1] AND s2[j-1] == s3[i+j-1])   # last char from s2

This is another member of the "two strings, two indices" family (005/010) --
genuinely 2D because i and j vary independently, but the combinator is OR
of two boolean-AND terms instead of a length/count.

PROGRESSIVE HINTS
------------------
Hint 1: First check len(s1) + len(s2) == len(s3) -- if not, immediately
        false, no DP needed.
Hint 2: dp[i][j] = "can s1[:i] interleaved with s2[:j] produce s3[:i+j]".
Hint 3: The character being matched in s3 is ALWAYS s3[i+j-1] -- position
        i+j-1, derived from i and j, not a third independent index.
Hint 4: Base case dp[0][0] = True (two empty strings interleave to an empty
        string). dp[i][0] and dp[0][j] are "forced" chains -- only true if
        every character so far matched straight through from one string.

COMPLEXITY TARGET
------------------
    Time:  O(len(s1) * len(s2))
    Space: O(min(len(s1), len(s2)))  (rolling row over the shorter string)
================================================================================
"""


class Solution:
    def isInterleave(self, s1: str, s2: str, s3: str) -> bool:
        # YOUR CODE HERE
        pass


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ("aabcc", "dbbca", "aadbbcbcac", True),
        ("aabcc", "dbbca", "aadbbbaccc", False),
        ("", "", "", True),
        ("", "abc", "abc", True),
        ("abc", "", "abd", False),
        ("aab", "axy", "aaxaby", True),
    ]
    for s1, s2, s3, want in cases:
        got = sol.isInterleave(s1, s2, s3)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  s1={s1!r} s2={s2!r} s3={s3!r} -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
