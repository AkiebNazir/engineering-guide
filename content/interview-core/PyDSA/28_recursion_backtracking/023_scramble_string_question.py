"""
================================================================================
LeetCode 87 · Scramble String                                            [Hard]
https://leetcode.com/problems/scramble-string/
Topic: 28 · Recursion Mastery
================================================================================
PROBLEM
-------
We can scramble a string `s` to get a string `t` using the following
algorithm:
    1. If the length of the string is 1, stop.
    2. If the length of the string is > 1, split it into two non-empty
       substrings at a random index, i.e. `s = s1 + s2`.
    3. Randomly decide to either swap the two substrings or keep them in the
       same order, i.e. after this step, `s` may become `s1 + s2` or
       `s2 + s1`.
    4. Apply step 1 recursively on each of the two substrings `s1` and `s2`.

Given two strings `s1` and `s2` of the same length, return `True` if `s2` is
a scrambled string of `s1`, otherwise `False`.

EXAMPLES
--------
Example 1:
    Input:  s1 = "great", s2 = "rgeat"
    Output: True
    Explanation: "great" splits into "gr"/"eat", swaps to "eat"/"gr" ... one
    valid decomposition eventually reaches "rgeat".

Example 2:
    Input:  s1 = "abcde", s2 = "caebd"
    Output: False

Example 3:
    Input:  s1 = "a", s2 = "a"
    Output: True

CONSTRAINTS
-----------
    s1.length == s2.length
    1 <= s1.length <= 30
    s1 and s2 consist of lowercase English letters.

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is a "does there EXIST a way" problem, which means recursion with a
choice at every level: for a split point `i` (1 <= i < n), the algorithm
either keeps order (s1's first `i` chars scramble-match s2's first `i` chars,
AND s1's remaining chars scramble-match s2's remaining chars) OR swaps
(s1's first `i` chars scramble-match s2's LAST `i` chars, AND s1's remaining
chars scramble-match s2's FIRST `n-i` chars). `s2 is a scramble of s1` iff
ANY split point `i` makes ONE of those two options work, checked recursively
all the way down to length-1 base cases (equal iff the single characters
match).

Without memoization this is exponential (each call branches into ~2n further
calls). The fix is memoizing on the actual pair of substrings being compared
— `lru_cache` on `(s1, s2)` turns the same exponential recursion into
O(n^4) by ensuring every distinct `(s1, s2)` pair is solved only once (there
are O(n^2) distinct substrings of each string, so O(n^4) pairs, each doing
O(n) work to try every split).

A crucial PRUNE: if `s1` and `s2` don't have the same multiset of characters
(same sorted string, or same `Counter`), NO scramble can ever make them equal
— return False immediately without trying any split. This prune alone
collapses huge swaths of the search space for real inputs.

WHAT TO THINK ABOUT
--------------------
1. What is the base case, exactly — and does `s1 == s2` at length > 1 let you
   skip early too (yes — if the strings are already identical, they trivially
   scramble-match with zero swaps, without checking any split point)?
2. At a given split point `i`, what are the TWO ways the recursive check can
   succeed (no-swap vs swap) — and why must you check both, since the
   original algorithm makes an ARBITRARY choice at every level, not a fixed
   one?
3. Why does memoizing on `(s1, s2)` (the actual substring pair) work, when
   memoizing on `(i, j)` positions into the ORIGINAL strings would not
   directly apply here (there's no single original string — every recursive
   call is already comparing two independently-produced substrings)?
4. Why is the character-multiset prune safe to apply as an early exit, and
   why does it help so much in practice even though it doesn't change the
   worst-case asymptotic bound?

PROGRESSIVE HINTS
------------------
Hint 1: Base case: `len(s1) != len(s2)` -> False (shouldn't happen given the
        problem's constraint, but a recursive call always compares equal-
        length substrings anyway). `s1 == s2` -> True immediately.
Hint 2: Prune: `sorted(s1) != sorted(s2)` -> False (different letters, no
        scramble is possible).
Hint 3: For each split `i` in `1..len(s1)-1`: no-swap check is
        `scramble(s1[:i], s2[:i]) and scramble(s1[i:], s2[i:])`; swap check
        is `scramble(s1[:i], s2[-i:]) and scramble(s1[i:], s2[:-i])`. If
        EITHER succeeds for ANY `i`, return True.
Hint 4: Wrap the recursive helper with `functools.lru_cache` (or a manual
        dict keyed on `(s1, s2)`) so repeated `(s1, s2)` pairs across
        different branches of the search are computed only once.

COMPLEXITY TARGET
------------------
    Memoized recursion: O(n^4) time (O(n^2) distinct substring-pairs per
    string pair dimension... more precisely O(n^4) total states across both
    strings' substring choices, O(n) work per state), O(n^4) space for the
    memo in the worst case.
    Naive (no memo): exponential — infeasible beyond small n.
================================================================================
"""


class Solution:
    def isScramble(self, s1: str, s2: str) -> bool:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 023_scramble_string_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ("great", "rgeat", True),
        ("abcde", "caebd", False),
        ("a", "a", True),
        ("a", "b", False),
        ("abc", "bca", True),
        ("abcdefghijklmnopq", "efghijklmnopqcadb", False),
    ]
    passed = 0
    for s1, s2, expected in cases:
        got = sol.isScramble(s1, s2)
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  isScramble({s1!r}, {s2!r}) -> {got}  (want {expected})")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
