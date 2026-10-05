"""
================================================================================
QUESTION · LeetCode 5 · Longest Palindromic Substring                [Medium]
https://leetcode.com/problems/longest-palindromic-substring/
================================================================================

PROBLEM
-------
Given a string s, return the longest palindromic substring in s.


EXAMPLES
--------
Example 1:
    Input:  s = "babad"
    Output: "bab"
    Explanation: "aba" is also a valid answer.

Example 2:
    Input:  s = "cbbd"
    Output: "bb"


CONSTRAINTS
-----------
    1 <= s.length <= 1000
    s consists of only digits and English letters.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
dp[i][j] MEANS "is s[i..j] (inclusive) a palindrome". A substring is a
palindrome exactly when its two ends match AND the INTERIOR (a strictly
SMALLER substring, s[i+1..j-1]) is also a palindrome:

    dp[i][j] = (s[i] == s[j]) and (j - i < 2 or dp[i+1][j-1])

Although indexed by a PAIR (i, j), the recurrence only ever reads a
strictly smaller interval -- this is "1D-style smaller-subproblem
reasoning applied to intervals" (see `_TOPIC_GUIDE.md` Part 2, row 007).
Fill dp by increasing substring LENGTH so the interior is always already
computed. The much simpler "expand around every center" technique achieves
the same O(n^2) time without the O(n^2) table at all -- that's the
approach actually shipped below.

PROGRESSIVE HINTS
------------------
Hint 1: Every single character is trivially a palindrome of length 1.
Hint 2: A 2-character substring is a palindrome iff both characters match.
Hint 3: For length >= 3, s[i..j] is a palindrome iff s[i]==s[j] AND
        s[i+1..j-1] is a palindrome -- a strictly smaller subproblem.
Hint 4: Alternative framing: every palindrome has a CENTER (a single
        character for odd length, a gap between two characters for even
        length). Expand outward from each of the 2n-1 possible centers as
        far as the two sides keep matching -- no table needed.

COMPLEXITY TARGET
------------------
    Time:  O(n^2)
    Space: O(1) (expand-around-center) or O(n^2) (tabulated dp[i][j])
================================================================================
"""


class Solution:
    def longestPalindrome(self, s: str) -> str:
        # YOUR CODE HERE
        pass


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    def is_valid_answer(s: str, got: str, want_len: int) -> bool:
        # Multiple longest palindromes can be valid; check got is a genuine
        # palindromic substring of s with the expected optimal length.
        return isinstance(got, str) and got in s and got == got[::-1] and len(got) == want_len

    cases = [
        ("babad", 3),
        ("cbbd", 2),
        ("a", 1),
        ("ac", 1),
        ("racecar", 7),
        ("forgeeksskeegfor", 10),  # "geeksskeeg"
        ("", 0),
    ]
    for s, want_len in cases:
        got = sol.longestPalindrome(s)
        ok = is_valid_answer(s, got, want_len) if s else got == ""
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  s={s!r}  -> {got!r}  (want length {want_len})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
