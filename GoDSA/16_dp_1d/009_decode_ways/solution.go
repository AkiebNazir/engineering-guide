package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 91 · Decode Ways                                  [Medium]
https://leetcode.com/problems/decode-ways/
================================================================================

PROBLEM
-------
A message containing letters from A-Z can be encoded into numbers using
the mapping:
    'A' -> "1", 'B' -> "2", ..., 'Z' -> "26"

To decode an encoded message, all the digits must be grouped then mapped
back into letters using the reverse of the mapping above (there may be
multiple ways). For example, "11106" can be mapped into:
    "AAJF" with the grouping (1 1 10 6)
    "KJF"  with the grouping (11 10 6)
Note: the grouping (1 11 06) is invalid because "06" is not a valid
mapping (a leading zero is not allowed).

Given a string s containing only digits, return the NUMBER of ways to
decode it. The test cases are generated so that the answer fits in a
32-bit integer.


EXAMPLES
--------
Example 1:
    Input:  s = "12"
    Output: 2
    Explanation: "12" could be decoded as "AB" (1 2) or "L" (12).

Example 2:
    Input:  s = "226"
    Output: 3
    Explanation: "226" could be decoded as "BZ" (2 26), "VF" (22 6), or
                 "BBF" (2 2 6).

Example 3:
    Input:  s = "06"
    Output: 0
    Explanation: "06" cannot be mapped to "F" because of the leading zero
                 ("6" is different from "06").


CONSTRAINTS
-----------
    1 <= s.length <= 100
    s consists of digits and may contain leading zero(s).


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
dp[i] MEANS "the number of ways to decode the PREFIX s[:i]" (the first i
characters). To extend a decoding up to position i, the LAST decoded
"token" was either the single digit s[i-1] (valid iff it's not '0'), or
the two-digit pair s[i-2:i] (valid iff it's between "10" and "26"). Both
options, when valid, ADD their contribution (they never overlap -- they're
distinguished by how many characters the last token consumed):

    dp[i] = dp[i-1]  (if s[i-1] != '0')
          + dp[i-2]  (if 10 <= int(s[i-2:i]) <= 26)

Same "last decision" framing as climbing stairs (last move was 1-step or
2-step) but the VALIDITY of each option now depends on the actual
characters, not just a fixed rule.

PROGRESSIVE HINTS
------------------
Hint 1: dp[0] = 1 (empty prefix has exactly one, trivial, decoding: nothing).
Hint 2: A single digit contributes dp[i-1] to dp[i] ONLY if that digit
        isn't '0' (a lone "0" can never be decoded).
Hint 3: A two-digit pair contributes dp[i-2] to dp[i] ONLY if the pair,
        read as a number, is between 10 and 26 inclusive.
Hint 4: Same fixed window of 2 as climbing stairs -- but each contribution
        is conditionally zero, so watch for a whole prefix collapsing to 0
        ways (e.g. any string containing "00" or a stray leading "0").

COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1)
================================================================================
*/

func main() {
	fmt.Println("Solution for Decode Ways not implemented yet")
}
