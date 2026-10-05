"""
================================================================================
LeetCode 76 · Minimum Window Substring                                    [Hard]
https://leetcode.com/problems/minimum-window-substring/
Topic: 03 · Sliding Window
================================================================================

PROBLEM
-------
Given two strings `s` and `t` of lengths m and n, return the MINIMUM WINDOW
SUBSTRING of `s` such that every character in `t` (INCLUDING DUPLICATES) is
included in the window. If there is no such substring, return "".

The answer is guaranteed to be unique.


EXAMPLES
--------
Example 1:
    Input:  s = "ADOBECODEBANC", t = "ABC"
    Output: "BANC"

Example 2:
    Input:  s = "a", t = "a"
    Output: "a"

Example 3:
    Input:  s = "a", t = "aa"
    Output: ""
    Explanation: both 'a's from t must be in the window; s has only one.


CONSTRAINTS
-----------
    m == s.length, n == t.length
    1 <= m, n <= 10^5
    s and t consist of uppercase and lowercase English letters.

    Follow up: could you find an algorithm that runs in O(m + n) time?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is the "shortest valid window" form of the variable sliding window:

    expand right until the window is VALID
    then shrink left while it STAYS valid, recording the shortest one
    repeat

The sliding window works because validity is MONOTONE: if a window contains
all of t, any bigger window containing it does too. So once the window is
valid, shrinking is the only way to find something shorter, and once
shrinking breaks validity, only expanding can fix it.

The hard part is checking "is the window valid?" in O(1) instead of comparing
two whole count maps at every step.


WHAT TO THINK ABOUT
--------------------
1. "Including duplicates" means you need COUNTS, not a set.

2. Keep `need[c]` = how many more of c the window still needs. How do you
   know, in O(1), that every entry is <= 0?

3. Track one integer `missing` = total characters still needed. When does it
   change? Only when a count crosses the boundary between "needed" and
   "satisfied".


PROGRESSIVE HINTS
------------------
Hint 1: need = Counter(t); missing = len(t).

Hint 2: Adding s[r]: if need[s[r]] > 0, missing -= 1. Then need[s[r]] -= 1
        (it can go negative: surplus copies).

Hint 3: While missing == 0: record the window, then remove s[l]:
        need[s[l]] += 1; if need[s[l]] > 0, missing += 1. Then l += 1.


COMPLEXITY TARGET
------------------
    Time:  O(m + n)
    Space: O(alphabet) = O(52)
================================================================================
"""


class Solution:
    def minWindow(self, s: str, t: str) -> str:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 014_minimum_window_substring_question.py
# ==============================================================================
def run_tests() -> None:
    cases = [
        ("ADOBECODEBANC", "ABC", "BANC"),
        ("a", "a", "a"),
        ("a", "aa", ""),
        ("aa", "aa", "aa"),
        ("ab", "b", "b"),
        ("bba", "ab", "ba"),
        ("abc", "d", ""),
        ("aaflslflsldkalskaaa", "aaa", "aaa"),
    ]
    all_ok = True
    for s, t, want in cases:
        got = Solution().minWindow(s, t)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  s={s!r} t={t!r}  got={got!r}  want={want!r}")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
