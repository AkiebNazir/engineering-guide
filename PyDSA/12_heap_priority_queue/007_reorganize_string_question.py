"""
================================================================================
QUESTION · LeetCode 767 · Reorganize String                           [Medium]
https://leetcode.com/problems/reorganize-string/
================================================================================

Given a string `s`, rearrange the characters of `s` so that any two adjacent
characters are not the same.

Return any possible rearrangement of `s`, or return "" if it is not possible.

Example 1:
    Input:  s = "aab"
    Output: "aba"

Example 2:
    Input:  s = "aaab"
    Output: ""

Constraints:
    1 <= s.length <= 500
    s consists of lowercase English letters.
"""

from collections import Counter


class Solution:
    def reorganizeString(self, s: str) -> str:
        # YOUR CODE HERE
        pass


def run_tests():
    sol = Solution()

    def is_valid(result: str, original: str) -> bool:
        if result == "":
            return False
        if Counter(result) != Counter(original):
            return False
        return all(result[i] != result[i + 1] for i in range(len(result) - 1))

    assert is_valid(sol.reorganizeString("aab"), "aab")
    assert sol.reorganizeString("aaab") == ""
    assert is_valid(sol.reorganizeString("aabb"), "aabb")
    assert sol.reorganizeString("a") == "a"
    assert is_valid(sol.reorganizeString("vvvlo"), "vvvlo")
    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
