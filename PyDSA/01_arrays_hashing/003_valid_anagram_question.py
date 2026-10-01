"""
================================================================================
LeetCode 242 · Valid Anagram                                             [Easy]
https://leetcode.com/problems/valid-anagram/
Topic: 01 · Arrays & Hashing
================================================================================

PROBLEM
-------
Given two strings `s` and `t`, return true if `t` is an anagram of `s`, and
false otherwise.

An Anagram is a word or phrase formed by rearranging the letters of a different
word or phrase, typically using all the original letters exactly once.


EXAMPLES
--------
Example 1:
    Input:  s = "anagram", t = "nagaram"
    Output: true

Example 2:
    Input:  s = "rat", t = "car"
    Output: false


CONSTRAINTS
-----------
    1 <= s.length, t.length <= 5 * 10^4
    s and t consist of lowercase English letters.

FOLLOW UP
---------
    What if the inputs contain Unicode characters? How would you adapt your
    solution to such a case?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

"Anagram" means: same multiset of characters. Order is irrelevant, but COUNTS
matter — "aab" and "abb" are not anagrams even though they use the same letter
set. So a plain `set` is the wrong tool here; you need frequencies.

    s = "anagram"  ->  {a:3, n:1, g:1, r:1, m:1}
    t = "nagaram"  ->  {a:3, n:1, g:1, r:1, m:1}   equal -> True

    s = "rat"      ->  {r:1, a:1, t:1}
    t = "car"      ->  {c:1, a:1, r:1}             differ -> False

The very first check should be length: two strings of different lengths can
never be anagrams, and bailing early saves the whole scan.


WHAT TO THINK ABOUT
-------------------
1. What is the cheapest possible disqualifier? (Check it first.)

2. Two families of solution:
     - SORT both and compare.        O(n log n) time, no auxiliary counts.
     - COUNT characters and compare. O(n) time, O(k) space where k = alphabet.

3. The constraint says "lowercase English letters" — only 26 possible keys.
   Does that let you replace the hash map with something cheaper?

4. The follow-up removes that guarantee. Which of your solutions survives
   Unicode unchanged, and which one breaks?


PROGRESSIVE HINTS
-----------------
Hint 1: If len(s) != len(t), return False immediately.

Hint 2: Count how many times each character appears in s. Then walk t and
        decrement. If any count goes negative, or a character is missing,
        return False.

Hint 3: With a fixed 26-letter alphabet you can use a list of 26 ints indexed
        by `ord(c) - ord('a')` instead of a dict — same complexity, much
        smaller constant, and no hashing at all.


COMPLEXITY TARGET
-----------------
    Time:  O(n)
    Space: O(1) — the count table is 26 entries regardless of input size,
           which is a constant. (Say "O(k) where k is the alphabet size" if
           you want to be precise; for the follow-up, k is unbounded.)
================================================================================
"""


class Solution:
    def isAnagram(self, s: str, t: str) -> bool:
        """Fixed 26-slot table, one pass. Time O(n), space O(1)."""
        if len(s) != len(t):
            return False
        counts = [0] * 26
        for a, b in zip(s, t):          # lengths equal, so one loop covers both
            counts[ord(a) - 97] += 1
            counts[ord(b) - 97] -= 1
        return all(c == 0 for c in counts)


# ==============================================================================
# TESTS — run:  python 003_valid_anagram_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ("anagram", "nagaram", True),
        ("rat", "car", False),
        ("a", "a", True),
        ("a", "ab", False),
        ("aacc", "ccac", False),   # same letter SET, different counts
        ("ab", "ba", True),
    ]
    passed = 0
    for s, t, expected in cases:
        got = sol.isAnagram(s, t)
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  s={s!r} t={t!r} -> {got} (want {expected})")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
