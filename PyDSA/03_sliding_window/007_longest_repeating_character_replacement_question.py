"""
================================================================================
LeetCode 424 · Longest Repeating Character Replacement                  [Medium]
https://leetcode.com/problems/longest-repeating-character-replacement/
Topic: 03 · Sliding Window
================================================================================

PROBLEM
-------
You are given a string `s` and an integer `k`. You can choose any character of
the string and change it to any other uppercase English character. You can
perform this operation AT MOST `k` times.

Return the length of the longest substring containing the SAME LETTER you can
get after performing the above operations.


EXAMPLES
--------
Example 1:
    Input:  s = "ABAB", k = 2
    Output: 4
    Explanation: Replace the two 'A's with two 'B's, or vice versa.

Example 2:
    Input:  s = "AABABBA", k = 1
    Output: 4
    Explanation: Replace the one 'A' in the middle with 'B' and form
                 "AABBBBA". The substring "BBBB" has the longest repeating
                 letters, which is 4.
                 There may exist other ways to achieve this answer too.


CONSTRAINTS
-----------
    1 <= s.length <= 10^5
    s consists of only UPPERCASE English letters.
    0 <= k <= s.length


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Same reframe as problem 006 — the "operation" is a constraint in disguise. You
are not choosing which characters to replace; you are choosing a WINDOW, and
the replacements follow automatically.

    For a fixed window, what does it COST to make it all one letter?

        Keep the letter that already appears most often, and replace
        everything else.

            cost = (window length) - (frequency of the most common letter)

        Keeping any OTHER letter costs strictly more, so the most frequent one
        is always the right choice. No search, no DP — just arithmetic.

So the validity condition is:

    (r - l + 1) - max_freq  <=  k

and the problem is the Shape-B template again: longest window satisfying that.

    s = "AABABBA",  k = 1

    [A A]                len 2, maxf 2 (A), cost 0  ok      best 2
    [A A B]              len 3, maxf 2 (A), cost 1  ok      best 3
    [A A B A]            len 4, maxf 3 (A), cost 1  ok      best 4  <- answer
    [A A B A B]          len 5, maxf 3 (A), cost 2  BROKEN -> shrink
     [A B A B]           len 4, maxf 2,     cost 2  BROKEN -> shrink
      [B A B]            len 3, maxf 2 (B), cost 1  ok
    ...


THE PART THAT MAKES THIS A MEDIUM
---------------------------------
Everything above is mechanical. The interesting question is:

    WHEN THE WINDOW SHRINKS, DO YOU HAVE TO RECOMPUTE `max_freq`?

Recomputing it means `max(count.values())` — a scan of up to 26 entries on
every step. That is O(26n), which IS still O(n) for a fixed alphabet, so it is
a perfectly good answer.

But the famous solution NEVER DECREASES `max_freq`. It lets the value go stale:

    max_freq = max(max_freq, count[s[r]])      # only ever grows

and it is still correct. Working out WHY is the real content of this problem.
Do not look it up yet — think about what a too-large `max_freq` does to the
validity test, and in which direction the error can push the window.

Two hints, in increasing order of directness, are in PROGRESSIVE HINTS below.


WHAT TO THINK ABOUT
-------------------
1. Why is "keep the most frequent letter" always optimal for a fixed window?
   State the one-line argument.

2. Write the version that recomputes `max_freq` honestly on every shrink. Get
   it correct first. What is its complexity, precisely?

3. Now the stale version. If `max_freq` is larger than the window's true
   maximum frequency, the cost `len - max_freq` is UNDERESTIMATED — so the
   window can look valid when it is not. Why does that never inflate the
   answer?

4. If the window is never allowed to shrink below its best-so-far width, what
   does that tell you about whether you need `max()` at the end at all?

5. With a stale `max_freq`, how many times can the shrink step fire on a single
   iteration? Work this out exactly — the answer is surprising and it explains
   why `while` and `if` behave identically here.

6. k can be 0, and k can be >= len(s). What are the answers then?


PROGRESSIVE HINTS
-----------------
Hint 1: The validity test is `(r - l + 1) - max_freq <= k`. Maintain a
        frequency Counter over the window.

Hint 2: The honest version:
            count[s[r]] += 1
            while (r - l + 1) - max(count.values()) > k:
                count[s[l]] -= 1; l += 1
            best = max(best, r - l + 1)

Hint 3 (the stale version): `max_freq` only ever increases. A stale value makes
        the cost look SMALLER than it is, so a window can survive that should
        have shrunk. But that window's width is one you already achieved
        legitimately with the old, genuine `max_freq` — so it never reports a
        width that was not truly attainable.

Hint 4: Since the window then never shrinks (it only slides), its width is
        non-decreasing, and `len(s) - l` at the end is the answer. `max()` is
        allowed but redundant.


COMPLEXITY TARGET
-----------------
    Time:  O(n)      with the stale max_freq
           O(26n)    if you recompute — also O(n) for a fixed alphabet, and a
                     perfectly acceptable answer if you can say the constant
    Space: O(26) = O(1)
================================================================================
"""


class Solution:
    def characterReplacement(self, s: str, k: int) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 007_longest_repeating_character_replacement_question.py
# ==============================================================================
def _brute(s, k):
    """O(n^2 * 26) reference: check every substring's replacement cost."""
    from collections import Counter
    best = 0
    for i in range(len(s)):
        c = Counter()
        for j in range(i, len(s)):
            c[s[j]] += 1
            if (j - i + 1) - max(c.values()) <= k:
                best = max(best, j - i + 1)
    return best


def run_tests() -> None:
    sol = Solution()
    cases = [
        ("ABAB", 2, 4),
        ("AABABBA", 1, 4),
        ("A", 0, 1),                  # single character, no budget
        ("AB", 0, 1),                 # k=0 -> longest existing run
        ("AAAA", 0, 4),
        ("ABCDE", 0, 1),
        ("ABCDE", 4, 5),              # enough budget for the whole string
        ("ABCDE", 100, 5),            # k > n
        ("AABA", 0, 2),
        ("BAAAB", 2, 5),
        ("ABBB", 2, 4),
        ("ABAA", 0, 2),
        ("AAAB", 0, 3),               # best run at the FRONT
        ("BAAA", 0, 3),               # best run at the END
        ("ABABBA", 1, 4),
        ("XYZXYZXYZ", 2, 4),          # all runs length 1; budget buys "XYZX"
        ("AAAABBBB", 2, 6),
    ]

    passed = 0
    for text, k, expected in cases:
        assert _brute(text, k) == expected, (
            f"bad test expectation for {text!r}, k={k}: "
            f"oracle says {_brute(text, k)}, test says {expected}")
        got = sol.characterReplacement(text, k)
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  k={k:<3} {text!r:<13} -> {got}  "
              f"(want {expected})")

    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
