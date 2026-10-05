"""
================================================================================
LeetCode 1456 · Maximum Number of Vowels in a Substring of Given Length   [Easy]
https://leetcode.com/problems/maximum-number-of-vowels-in-a-substring-of-given-length/
Topic: 03 · Sliding Window
================================================================================

PROBLEM
-------
Given a string `s` and an integer `k`, return the maximum number of vowel
letters in any substring of `s` with length `k`.

Vowel letters in English are 'a', 'e', 'i', 'o', and 'u'.


EXAMPLES
--------
Example 1:
    Input:  s = "abciiidef", k = 3
    Output: 3
    Explanation: The substring "iii" contains 3 vowel letters.

Example 2:
    Input:  s = "aeiou", k = 2
    Output: 2
    Explanation: Any substring of length 2 contains 2 vowels.

Example 3:
    Input:  s = "leetcode", k = 3
    Output: 2
    Explanation: "lee", "eet" and "ode" contain 2 vowels.


CONSTRAINTS
-----------
    1 <= s.length <= 10^5
    s consists of lowercase English letters.
    1 <= k <= s.length


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Structurally this is LC 643 again — a FIXED-SIZE window, one enter and one
leave per step — with one substitution:

    LC 643 aggregate:   running SUM of the values
    LC 1456 aggregate:  running COUNT of elements satisfying a PREDICATE

That is the entire difference, and it is worth internalising because the
substitution generalises. Any "how many X in each window of size k" question is
the same five lines:

    s = 0
    for r, ch in enumerate(text):
        s += P(ch)                       # enter: 1 if the predicate holds
        if r >= k:      s -= P(text[r - k])   # leave
        if r >= k - 1:  best = max(best, s)

Because P returns 0 or 1, the count is still an integer you can add and
subtract in O(1) — which is the only requirement a sliding window has.

    s = "abciiidef",  k = 3          v = vowel

        a  b  c  i  i  i  d  e  f
        v        v  v  v     v
       [a  b  c] i  i  i  d  e  f     count = 1
        a [b  c  i] i  i  d  e  f     count = 1  (a left, i entered)
        a  b [c  i  i] i  d  e  f     count = 2
        a  b  c [i  i  i] d  e  f     count = 3   <- answer, and it is also
        a  b  c  i [i  i  d] e  f     count = 2      the maximum POSSIBLE
        ...


A FREE OPTIMISATION WORTH NOTICING
----------------------------------
The count can never exceed `k` — a window of length k has at most k vowels. So
the moment `count == k` you have found the best possible answer and can return
immediately, skipping the rest of the string.

This does not change the worst-case O(n) (a vowel-free string never triggers
it), but on realistic input it often ends the scan in the first few percent.
Interviewers like candidates who notice that the answer has a known CEILING.


WHAT TO THINK ABOUT
-------------------
1. How do you test "is this character a vowel"? There are at least three ways —
   `ch in "aeiou"`, `ch in {'a','e','i','o','u'}`, and a 26-slot lookup table.
   They differ in constant factor. Which is asymptotically irrelevant but
   measurably faster, and why?

2. In Python, `True + True == 2`. Does that let you drop an `if` entirely?
   Is that clearer or less clear? (Have an opinion; both are defensible.)

3. What is the maximum value the answer can take? Can you exit early?

4. Same two off-by-ones as LC 643: which index leaves, and on which iterations
   is the window complete? Write them down before coding.

5. Could you solve this with `s.count('a') + ...` on each substring? What is
   that complexity, and why is it the same mistake as `sum(nums[i:i+k])`?


PROGRESSIVE HINTS
-----------------
Hint 1: Convert the character stream into a 0/1 stream conceptually:
        "leetcode" -> [0,1,1,0,0,0,0,1]. Now it is literally LC 643 with a
        fixed window sum.

Hint 2: `VOWELS = set('aeiou')` outside the loop — building the set INSIDE the
        loop makes it O(n) set constructions.

Hint 3: The body:
            if s[r] in VOWELS:            count += 1
            if r >= k and s[r-k] in VOWELS: count -= 1
            if r >= k - 1:                best = max(best, count)

Hint 4: Add `if best == k: return k` right after the update, and be able to
        explain why the worst case is still O(n).


COMPLEXITY TARGET
-----------------
    Time:  O(n)   — one pass; each character tested at most twice
    Space: O(1)   — a counter and a 5-element constant set
================================================================================
"""


class Solution:
    def maxVowels(self, s: str, k: int) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 003_maximum_number_of_vowels_in_a_substring_question.py
# ==============================================================================
def _brute(s, k):
    """O(n*k) reference: count vowels in every length-k substring."""
    return max(sum(c in "aeiou" for c in s[i:i + k])
               for i in range(len(s) - k + 1))


def run_tests() -> None:
    sol = Solution()
    cases = [
        ("abciiidef", 3),
        ("aeiou", 2),
        ("leetcode", 3),
        ("rhythms", 4),          # NO vowels at all -> 0
        ("tryhard", 4),
        ("a", 1),                # n == k == 1
        ("b", 1),                # single consonant
        ("aeiou", 5),            # k == n, all vowels
        ("weallloveyou", 7),
        ("aaaaaaaaaa", 1),       # k == 1
        ("novowelshere", 12),    # k == n
        ("uuuuxxxx", 4),         # best window is at the very front
        ("xxxxuuuu", 4),         # best window is at the very end
        ("xuxuxuxu", 3),         # alternating
    ]

    passed = 0
    for text, k in cases:
        expected = _brute(text, k)
        got = sol.maxVowels(text, k)
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  k={k:<2} {text!r:<16} -> {got}  "
              f"(want {expected})")

    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
