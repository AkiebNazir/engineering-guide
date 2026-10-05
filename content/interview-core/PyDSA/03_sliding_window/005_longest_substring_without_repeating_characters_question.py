"""
================================================================================
LeetCode 3 · Longest Substring Without Repeating Characters             [Medium]
https://leetcode.com/problems/longest-substring-without-repeating-characters/
Topic: 03 · Sliding Window
================================================================================

PROBLEM
-------
Given a string `s`, find the length of the longest SUBSTRING without repeating
characters.

(A substring is a CONTIGUOUS sequence of characters. "pwke" is a SUBSEQUENCE of
"pwwkew", not a substring — this distinction is the whole reason the problem is
a window and not a DP.)


EXAMPLES
--------
Example 1:
    Input:  s = "abcabcbb"
    Output: 3
    Explanation: The answer is "abc", with the length of 3.

Example 2:
    Input:  s = "bbbbb"
    Output: 1
    Explanation: The answer is "b", with the length of 1.

Example 3:
    Input:  s = "pwwkew"
    Output: 3
    Explanation: The answer is "wke", with the length of 3.
                 Notice that the answer must be a SUBSTRING; "pwke" is a
                 subsequence and not a substring.


CONSTRAINTS
-----------
    0 <= s.length <= 5 * 10^4          <- NOTE: the string may be EMPTY
    s consists of English letters, digits, symbols and spaces.
                                       <- NOTE: NOT just lowercase a-z


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is THE archetypal variable-size sliding window, and everything after it in
this folder is a variation. Learn this one properly and 006, 007, 009 fall out.

The brute force checks every substring for distinctness:

    for l in range(n):
        for r in range(l, n):
            if all distinct: best = max(best, r - l + 1)

    O(n^2) substrings, O(n) to check each -> O(n^3), or O(n^2) if you extend a
    set incrementally. Either way, too slow.

THE WINDOW. Maintain `[l, r]` such that the characters inside are all DISTINCT.
Walk `r` forward one step at a time. When the incoming character breaks
distinctness, advance `l` until it is repaired:

    s = "abcabcbb"

      a b c a b c b b
      [a]                 window "a"     len 1
      [a b]               window "ab"    len 2
      [a b c]             window "abc"   len 3   <- best
       a[b c a]           'a' entered, duplicate -> drop from the left until fixed
         [b c a]          window "bca"   len 3
           [c a b]        window "cab"   len 3
             [a b c]      window "abc"   len 3
               [b c]      ...


WHY MOVING `l` FORWARD IS PROVABLY SAFE
---------------------------------------
This is the part to actually understand — it is the hereditary property from
Part 1.2 of the topic guide, instantiated:

    "all characters distinct" is HEREDITARY: any substring of a distinct
    string is still distinct.

Contrapositive: if `s[l..r]` contains a duplicate, then every LARGER window
`s[l'..r]` with `l' < l` contains that same duplicate too. So once the window
is broken, no earlier left endpoint can rescue it — shrinking is the only
possible repair, and everything you shrink past is dead forever.

That is why `l` never needs to move backwards, which is why the whole scan is
O(n) rather than O(n^2). Say it out loud; it is the difference between knowing
the template and understanding it.


WHAT TO THINK ABOUT
-------------------
1. What data structure tracks "the characters currently in the window"? You
   need O(1) "is it present", O(1) insert, and O(1) delete. Name it.

2. When `s[r]` is already in the window, how far must `l` advance? Two answers:
       (a) one step at a time, until the duplicate is gone;
       (b) in ONE JUMP, straight past the previous occurrence.
   Both are O(n) overall. (b) needs a different structure — what does it store?

3. For version (b): the previous occurrence might be BEHIND the current `l`
   (already evicted). What must you do to stop `l` from moving BACKWARDS?
   This is the single most common bug in this problem. Construct a 4-character
   string that exposes it before you write any code.

4. In what order do you (i) record the answer, (ii) shrink, (iii) add the new
   character? Getting this wrong measures an invalid window.

5. What is the maximum possible answer, given the alphabet? Can you stop early?

6. The empty string is legal input. What does your code return?


PROGRESSIVE HINTS
-----------------
Hint 1: Keep a `set` of the characters in `[l, r]`. For each r:
            while s[r] in window:  window.remove(s[l]); l += 1
            window.add(s[r])
            best = max(best, r - l + 1)

Hint 2: The `while` is not nested work. `l` only ever increases and is bounded
        by n, so across the WHOLE run it advances at most n times: O(n) total.

Hint 3: The jump version stores `last[ch] = the index where ch last appeared`:
            if ch in last and last[ch] >= l:
                l = last[ch] + 1
            last[ch] = r
        or, equivalently and more safely,
            l = max(l, last.get(ch, -1) + 1)

Hint 4: In the jump version, `max(l, ...)` is MANDATORY. Without it a stale
        index from before the window drags `l` backwards. Try "abba".

Hint 5: `r - l + 1`, not `r - l`. A one-character window has length 1.


COMPLEXITY TARGET
-----------------
    Time:  O(n)          — each character enters once and leaves once
    Space: O(min(n, Σ))  — Σ = alphabet size; the window cannot hold more than
                           Σ distinct characters, so it is O(1) for a fixed
                           alphabet
================================================================================
"""


class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 005_longest_substring_without_repeating_characters_question.py
# ==============================================================================
def _brute(s):
    """O(n^2) reference: extend from every start until a repeat appears."""
    best = 0
    for i in range(len(s)):
        seen = set()
        for j in range(i, len(s)):
            if s[j] in seen:
                break
            seen.add(s[j])
            best = max(best, j - i + 1)
    return best


def run_tests() -> None:
    sol = Solution()
    cases = [
        ("abcabcbb", 3),
        ("bbbbb", 1),
        ("pwwkew", 3),
        ("", 0),                  # EMPTY string is legal input
        ("a", 1),
        ("au", 2),
        ("abba", 2),              # THE `max(l, ...)` DETECTOR — see Hint 4
        ("tmmzuxt", 5),           # another stale-index trap ("mzuxt")
        ("dvdf", 3),              # classic: answer is "vdf", not "dv"
        ("abcdefg", 7),           # all distinct -> the whole string
        ("aab", 2),
        ("cdd", 2),
        ("abcb", 3),
        (" ", 1),                 # a space IS a character
        ("a b c a", 3),           # the SPACE repeats too: "a b" is the best
        ("!@#!@#", 3),            # symbols are in the alphabet too
        ("0123401234", 5),        # digits
        ("aA", 2),                # case-SENSITIVE: 'a' != 'A'
    ]

    passed = 0
    for text, expected in cases:
        # cross-check the hand-written expectation against the oracle
        assert _brute(text) == expected, (
            f"bad test expectation for {text!r}: "
            f"oracle says {_brute(text)}, test says {expected}")
        got = sol.lengthOfLongestSubstring(text)
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {text!r:<14} -> {got}  "
              f"(want {expected})")

    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
