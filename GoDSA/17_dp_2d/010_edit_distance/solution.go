package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 72 · Edit Distance                                [Medium]
https://leetcode.com/problems/edit-distance/
================================================================================

PROBLEM
-------
Given two strings word1 and word2, return the minimum number of operations
required to convert word1 to word2.

You have the following three operations permitted on a word:
- Insert a character
- Delete a character
- Replace a character


EXAMPLES
--------
Example 1:
    Input:  word1 = "horse", word2 = "ros"
    Output: 3
    Explanation: horse -> rorse (replace 'h' with 'r')
                 rorse -> rose (remove 'r')
                 rose -> ros (remove 'e')

Example 2:
    Input:  word1 = "intention", word2 = "execution"
    Output: 5


CONSTRAINTS
-----------
    0 <= word1.length, word2.length <= 500
    word1 and word2 consist of lowercase English letters.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Another "two strings, two indices" DP (family with 005 LCS, 009 Interleaving)
-- but where LCS only ever "agrees or skips," Edit Distance additionally
allows "replace," so the recurrence takes a MIN over THREE neighbor
operations instead of a MAX over two.

dp[i][j] = minimum operations to convert word1[:i] into word2[:j].

    word1[i-1] == word2[j-1]:  dp[i][j] = dp[i-1][j-1]         (chars already
                                                                 match, no op
                                                                 needed)
    word1[i-1] != word2[j-1]:  dp[i][j] = 1 + min(
                                    dp[i-1][j-1],   # replace word1[i-1]
                                    dp[i-1][j],     # delete word1[i-1]
                                    dp[i][j-1])     # insert word2[j-1]

PROGRESSIVE HINTS
------------------
Hint 1: dp[i][j] = min edits to turn word1[:i] into word2[:j] (1-indexed
        prefix lengths, dp[0][*]/dp[*][0] handle one string being empty).
Hint 2: Base case dp[i][0] = i (delete all i characters of word1 to reach
        empty), dp[0][j] = j (insert all j characters to build word2 from
        empty).
Hint 3: On a character match, NO operation is spent -- dp[i][j] =
        dp[i-1][j-1] directly, don't add 1.
Hint 4: On a mismatch, the three neighbors correspond to REPLACE (diagonal),
        DELETE (up), INSERT (left) -- take the min, add 1 for the operation
        itself.

COMPLEXITY TARGET
------------------
    Time:  O(len(word1) * len(word2))
    Space: O(min(len(word1), len(word2)))  (rolling row)
================================================================================
*/

func main() {
	fmt.Println("Solution for Edit Distance not implemented yet")
}
