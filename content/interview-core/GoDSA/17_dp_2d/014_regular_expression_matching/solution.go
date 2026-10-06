package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 10 · Regular Expression Matching                     [Hard]
https://leetcode.com/problems/regular-expression-matching/
================================================================================

PROBLEM
-------
Given an input string s and a pattern p, implement regular expression
matching with support for '.' and '*' where:
- '.' Matches any single character.
- '*' Matches zero or more of the preceding element.

The matching should cover the ENTIRE input string (not partial).


EXAMPLES
--------
Example 1:
    Input:  s = "aa", p = "a"
    Output: false
    Explanation: "a" does not match the entire string "aa".

Example 2:
    Input:  s = "aa", p = "a*"
    Output: true
    Explanation: '*' means zero or more of the preceding element, 'a'.
    Therefore, by repeating 'a' once, it becomes "aa".

Example 3:
    Input:  s = "ab", p = ".*"
    Output: true
    Explanation: ".*" means "zero or more (*) of any character (.)".


CONSTRAINTS
-----------
    1 <= s.length <= 20
    1 <= p.length <= 20
    s contains only lowercase English letters.
    p contains only lowercase English letters, '.', and '*'.
    It is guaranteed for each appearance of the character '*', there will
    be a previous valid character to match.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The third and final "two strings, two indices" boolean DP in this topic
(alongside 009 Interleaving String) -- but here the SECOND string is a
PATTERN with special metacharacters, so the transitions are pattern-driven
rather than symmetric.

dp[i][j] = does s[:i] match p[:j] (matching the ENTIRE prefix, not a
substring)? Case on p[j-1], the LAST character of the pattern prefix:

- If p[j-1] is a plain letter or '.': it must match s[i-1] exactly (or '.'
  matches anything), AND the rest must already match:
      dp[i][j] = dp[i-1][j-1] AND (p[j-1]=='.' OR p[j-1]==s[i-1])
- If p[j-1] == '*': it modifies p[j-2] (the character BEFORE the star), and
  has TWO independent ways to match:
      "zero occurrences" of p[j-2]: dp[i][j] = dp[i][j-2] (skip "x*" as a
          whole unit, star included, contributing nothing to s)
      "one more occurrence" of p[j-2] (only if p[j-2] matches s[i-1]):
          dp[i][j] |= dp[i-1][j]  (consume one char of s, STAY on the same
          "x*" pattern position, since '*' can match many)
  dp[i][j] = dp[i][j-2] OR (dp[i-1][j] if p[j-2] matches s[i-1] else False)

PROGRESSIVE HINTS
------------------
Hint 1: dp[i][j] = does s[:i] fully match p[:j]?
Hint 2: Base case dp[0][0] = True (two empty strings match). dp[0][j] can
        be True for patterns like "a*b*c*" that can match zero characters
        -- NOT automatically False just because s is empty.
Hint 3: When p[j-1] == '*', it always pairs with p[j-2] -- '*' NEVER
        appears as the first character of a valid pattern (constraints
        guarantee this).
Hint 4: The "zero occurrences" branch (dp[i][j-2]) does NOT require any
        character comparison -- it's purely "pretend p[j-2] and the '*'
        aren't there at all."
Hint 5: The "one more occurrence" branch (dp[i-1][j]) DOES require p[j-2]
        to match s[i-1] first -- and note it looks at dp[i-1][j], not
        dp[i-1][j-2] -- staying at column j lets '*' consume multiple s
        characters one at a time across multiple dp transitions.

COMPLEXITY TARGET
------------------
    Time:  O(len(s) * len(p))
    Space: O(len(p))  (rolling row -- but the j-2 dependency means TWO
                        previous rows' worth of data must be tracked
                        carefully; see the solution's approach notes)
================================================================================
*/

func main() {
	fmt.Println("Solution for Regular Expression Matching not implemented yet")
}
