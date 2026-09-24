package main

/*
================================================================================
QUESTION · LeetCode 1143 · Longest Common Subsequence                [Medium]
https://leetcode.com/problems/longest-common-subsequence/
================================================================================

PROBLEM
-------
Given two strings text1 and text2, return the length of their longest common
subsequence. If there is no common subsequence, return 0.

A subsequence is a new string generated from the original string with some
characters (can be none) deleted without changing the relative order of the
remaining characters. A common subsequence of two strings is a subsequence
that is common to both strings.


EXAMPLES
--------
Example 1:
    Input:  text1 = "abcde", text2 = "ace"
    Output: 3
    Explanation: "ace" is the longest common subsequence, length 3.

Example 2:
    Input:  text1 = "abc", text2 = "abc"
    Output: 3

Example 3:
    Input:  text1 = "abc", text2 = "def"
    Output: 0


CONSTRAINTS
-----------
    1 <= text1.length, text2.length <= 1000
    text1 and text2 consist of only lowercase English characters.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is the seed problem of the "two strings, two indices" DP family (the
first genuinely 2D DP where BOTH indices vary independently and neither can
be collapsed away -- unlike topic 16's dp[i][j] palindrome check, which was
built from a SMALLER interior of the SAME string).

Let dp[i][j] = LCS length between text1[:i] (first i chars) and text2[:j]
(first j chars). Compare the LAST character of each prefix:
- if text1[i-1] == text2[j-1]: that character can be part of the LCS -- add
  1 to the LCS of the two strings WITHOUT that character: dp[i-1][j-1] + 1.
- else: the LCS of the full prefixes is the better of dropping the last char
  of EITHER string: max(dp[i-1][j], dp[i][j-1]).

PROGRESSIVE HINTS
------------------
Hint 1: dp[i][j] = LCS length of text1[:i] and text2[:j] (1-indexed prefix
        lengths, so dp[0][*] = dp[*][0] = 0 -- empty prefix has LCS 0).
Hint 2: Compare text1[i-1] to text2[j-1] (the actual LAST characters of the
        two prefixes), not text1[i] to text2[j].
Hint 3: Match -> dp[i-1][j-1] + 1. No match -> max(dp[i-1][j], dp[i][j-1]).
Hint 4: The answer is dp[len(text1)][len(text2)] -- the bottom-right corner.

COMPLEXITY TARGET
------------------
    Time:  O(len(text1) * len(text2))
    Space: O(min(len(text1), len(text2)))  (rolling row over the shorter string)
================================================================================
*/

// TODO: Implement the stub
