package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 647 · Palindromic Substrings                     [Medium]
https://leetcode.com/problems/palindromic-substrings/
================================================================================

PROBLEM
-------
Given a string s, return the number of palindromic substrings in it.

A string is a palindrome when it reads the same backward as forward.

A substring is a contiguous sequence of characters within the string.


EXAMPLES
--------
Example 1:
    Input:  s = "abc"
    Output: 3
    Explanation: "a", "b", "c" -- three palindromic substrings.

Example 2:
    Input:  s = "aaa"
    Output: 6
    Explanation: "a", "a", "a", "aa", "aa", "aaa" -- 6 palindromic
                 substrings (counting each OCCURRENCE, not distinct strings).


CONSTRAINTS
-----------
    1 <= s.length <= 1000
    s consists of lowercase English letters.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Same underlying structure as problem 007 (Longest Palindromic Substring):
dp[i][j] MEANS "is s[i..j] a palindrome", built from the smaller interior
dp[i+1][j-1]. The only difference is the AGGREGATION -- instead of
tracking the max-length true cell, COUNT every cell that's true. Every
center (2n-1 of them, same as 007) contributes exactly one count per step
of successful expansion, since each successful expansion IS a distinct
palindromic substring occurrence.

PROGRESSIVE HINTS
------------------
Hint 1: Every single character is a palindrome -- that's n free counts
        before considering anything else.
Hint 2: Reuse the "expand around center" idea from problem 007: for each
        of the 2n-1 centers, every successful expansion step is ONE MORE
        palindromic substring to count (not just the final longest one).
Hint 3: Alternatively, fill the dp[i][j] table exactly as in 007 and
        count the True cells instead of tracking the longest span.

COMPLEXITY TARGET
------------------
    Time:  O(n^2)
    Space: O(1) (expand-around-center) or O(n^2) (dp table)
================================================================================
*/

func main() {
	fmt.Println("Solution for Palindromic Substrings not implemented yet")
}
