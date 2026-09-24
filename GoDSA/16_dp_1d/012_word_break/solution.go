package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 139 · Word Break                                  [Medium]
https://leetcode.com/problems/word-break/
================================================================================

PROBLEM
-------
Given a string s and a dictionary of strings wordDict, return true if s
can be segmented into a space-separated sequence of one or more
dictionary words.

Note that the same word in the dictionary may be reused multiple times in
the segmentation.


EXAMPLES
--------
Example 1:
    Input:  s = "leetcode", wordDict = ["leet","code"]
    Output: true
    Explanation: return true because "leetcode" can be segmented as
                 "leet code".

Example 2:
    Input:  s = "applepenapple", wordDict = ["apple","pen"]
    Output: true
    Explanation: "apple pen apple". Note "apple" is reused.

Example 3:
    Input:  s = "catsandog", wordDict = ["cats","dog","sand","and","cat"]
    Output: false


CONSTRAINTS
-----------
    1 <= s.length <= 300
    1 <= wordDict.length <= 1000
    1 <= wordDict[i].length <= 20
    s and wordDict[i] consist of only lowercase English letters.
    All the strings of wordDict are UNIQUE.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
dp[i] MEANS "can the prefix s[:i] be segmented into dictionary words".
The last decision at position i is "which dictionary word ends exactly
here" -- scan every j < i, and if dp[j] is already true AND s[j:i] is a
dictionary word, then dp[i] is true:

    dp[0] = True                          (empty prefix, trivially segmentable)
    dp[i] = any(dp[j] and s[j:i] in wordSet for j in range(i))

Variable-range look-back (unlike the fixed-window problems 002/003/005) --
scan every earlier split point, not just the last 1 or 2 positions.

PROGRESSIVE HINTS
------------------
Hint 1: Convert wordDict to a SET first -- O(1) membership checks instead
        of O(len(wordDict)) linear scans per candidate word.
Hint 2: dp[0] = True (the empty string needs zero words).
Hint 3: For each end position i, try every earlier split point j: if
        dp[j] is true and s[j:i] is a dictionary word, dp[i] is true --
        stop scanning as soon as one j works (no need to check the rest).
Hint 4: Bound the inner scan by the LONGEST word length in the dictionary
        -- j never needs to go back further than that, which turns an
        O(n^2) inner scan into O(n * maxWordLen) in practice.

COMPLEXITY TARGET
------------------
    Time:  O(n^2) worst case (O(n * maxWordLen) with the length bound)
    Space: O(n + total dictionary characters)
================================================================================
*/

func main() {
	fmt.Println("Solution for Word Break not implemented yet")
}
