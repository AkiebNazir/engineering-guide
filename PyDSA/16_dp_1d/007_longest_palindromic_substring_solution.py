"""
================================================================================
SOLUTION · LeetCode 5 · Longest Palindromic Substring                [Medium]
https://leetcode.com/problems/longest-palindromic-substring/
================================================================================

THE CORE IDEA
--------------
dp[i][j] MEANS "is s[i..j] a palindrome". It's true iff the ends match and
the strictly SMALLER interior is also a palindrome:

    dp[i][j] = s[i]==s[j] and (j-i < 2 or dp[i+1][j-1])

Equivalently: every palindrome has a CENTER (a character, for odd length,
or a gap between two characters, for even length) and can be found by
expanding outward from that center while the two sides keep matching.
There are exactly 2n-1 possible centers; trying all of them and expanding
each is the same O(n^2) work as the DP table, without materializing the
table -- that's the version shipped here.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, price it, don't ship it): check EVERY substring
s[i:j+1] for being a palindrome from scratch. O(n^2) substrings, O(n) to
check each (or O(n) to construct + reverse-compare) -> O(n^3) total. See
the runtime demo below for how badly this scales past a few hundred
characters.

Approach 1 (tabulated dp[i][j], fill by increasing length) [`longest_dp_table`]
-- dp[i][j] built from the smaller dp[i+1][j-1], filled in order of
increasing substring length so the interior is always ready.
O(n^2) time, O(n^2) space.

Approach 2 (expand around center) [chosen] -- for each of the 2n-1 centers
(n single-character centers + n-1 between-character gaps), expand outward
while s[left]==s[right]. O(n^2) time (n centers, each can expand O(n)),
O(1) extra space -- strictly better than the table approach on space with
identical time complexity, which is why it's the one to ship.

Approach 3 (Manacher's algorithm) -- O(n) time, O(n) space, using a
cleverly reused mirror-symmetry trick. Correct but a specialized algorithm
most interviewers don't expect verbatim; worth NAMING as the optimal bound
even if you implement approach 2.


================================================================================
STEP BY STEP TRACE
================================================================================
s = "babad"    (indices: b=0 a=1 b=2 a=3 d=4)

Expand-around-center, trying each center left-to-right (odd centers first
at each position, then the even gap to its right):

    center i=0 (odd 'b'):        expand -> "b"           len 1
    center gap(0,1) (even):      s[0]!=s[1] ('b'!='a')    len 0
    center i=1 (odd 'a'):        expand -> s[0]=='b'? no with s[2]=='b':
                                  s[1]='a' alone len1, try expand
                                  left=0,right=2: s[0]='b'==s[2]='b' -> match!
                                  expand further left=-1 stop.
                                  best here: "bab"          len 3   <- new best
    center gap(1,2):              s[1]!=s[2] ('a'!='b')    len 0
    center i=2 (odd 'b'):         expand left=1,right=3: s[1]='a'==s[3]='a'
                                  -> match! expand left=0,right=4:
                                  s[0]='b'!=s[4]='d' stop.
                                  best here: "aba"           len 3 (ties, first found kept)
    center gap(2,3):              s[2]!=s[3] ('b'!='a')    len 0
    center i=3 (odd 'a'):         "a"                        len 1
    center gap(3,4):              s[3]!=s[4] ('a'!='d')    len 0
    center i=4 (odd 'd'):         "d"                        len 1

Longest found: "bab" (length 3), returned as the answer (LC accepts "aba"
too -- either is valid).


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time    Space    Mutates input?
    ---------------------------------  ------  -------  --------------
    Brute force (check every substring) O(n^3) O(n)     no
    Tabulated dp[i][j]                  O(n^2)  O(n^2)   no
    Expand around center [chosen]       O(n^2)  O(1)     no
    Manacher's algorithm                O(n)    O(n)     no


================================================================================
EDGE CASES
================================================================================
    len(s) == 1           -> the single character is its own longest
                              palindrome; must not crash on an empty
                              "interior" when expanding.
    all identical characters ("aaaa") -> the ENTIRE string is the answer;
                              forces expansion to go all the way to the
                              string's boundaries without an off-by-one.
    no repeated characters ("abcd")   -> every single character is
                              (jointly) the longest palindrome, length 1;
                              confirms the algorithm doesn't spuriously
                              report a longer match.
    even-length answer ("cbbd")        -> only found via an EVEN center
                              (the gap between two equal characters);
                              skipping even centers is a common omission.


================================================================================
COMMON MISTAKES
================================================================================
1. Only trying ODD-length centers (single characters) and forgetting EVEN
   centers (gaps between adjacent characters) -- silently misses answers
   like "bb" or "cbbd" -> "bb".
2. Off-by-one when recording the best window: after the while loop exits,
   left/right have already stepped ONE PAST the actual matching bounds --
   the true palindrome is s[left+1:right] (Python slice), not s[left:right+1].
3. In the DP-table version, filling cells in the WRONG order (e.g. row by
   row with i increasing) reads dp[i+1][j-1] before it's been computed --
   must fill by increasing substring LENGTH, or iterate i from high to low
   and j from low to high, so the smaller interior is always ready.
4. Reversing the whole string and comparing to itself as a shortcut --
   this only proves s is a palindrome overall, doesn't help find the
   longest palindromic SUBSTRING.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Can you do it in O(n)?" -> yes, Manacher's algorithm; explain the
  mirror-reuse idea (a palindrome's radius info can be partially copied
  from its mirror position within a larger already-known palindrome)
  even if you don't code it from scratch under time pressure.
- "What if you need to COUNT all palindromic substrings, not just find the
  longest?" -> problem 008, same dp[i][j]/expand-center technique,
  different aggregation (count instead of track-max).
- "What's the tradeoff between the DP table and expand-around-center?" ->
  identical time, but expand-around-center is O(1) space and simpler to
  reason about; the table version generalizes more easily if you need
  dp[i][j] answers for MANY (i,j) pairs later, not just the overall max.


================================================================================
RELATED PROBLEMS
================================================================================
- 008 Palindromic Substrings (LC 647) -- count instead of find-longest,
  identical underlying technique.
- Palindrome Partitioning (LC 131) -- uses this dp[i][j] table as a
  building block for a further DP over partition points.
- Shortest Palindrome (LC 214) -- KMP-based, different technique family.
================================================================================
"""

import time


class Solution:
    def longestPalindrome(self, s: str) -> str:
        if not s:
            return ""

        def expand(left: int, right: int) -> str:
            while left >= 0 and right < len(s) and s[left] == s[right]:
                left -= 1
                right += 1
            return s[left + 1:right]  # step back to the last valid match

        best = ""
        for center in range(len(s)):
            odd = expand(center, center)
            if len(odd) > len(best):
                best = odd
            even = expand(center, center + 1)
            if len(even) > len(best):
                best = even
        return best


def longest_brute_force(s: str) -> str:
    if not s:
        return ""
    n = len(s)
    best = s[0]
    for i in range(n):
        for j in range(i, n):
            sub = s[i:j + 1]
            if sub == sub[::-1] and len(sub) > len(best):
                best = sub
    return best


def longest_dp_table(s: str) -> str:
    if not s:
        return ""
    n = len(s)
    dp = [[False] * n for _ in range(n)]
    start, max_len = 0, 1
    for i in range(n):
        dp[i][i] = True
    for length in range(2, n + 1):
        for i in range(0, n - length + 1):
            j = i + length - 1
            if s[i] == s[j] and (length == 2 or dp[i + 1][j - 1]):
                dp[i][j] = True
                if length > max_len:
                    start, max_len = i, length
    return s[start:start + max_len]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    def is_valid_answer(s: str, got: str, want_len: int) -> bool:
        return got in s and got == got[::-1] and len(got) == want_len

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
        if s:
            assert is_valid_answer(s, longest_dp_table(s), want_len)
            assert is_valid_answer(s, longest_brute_force(s), want_len)

    print()
    print("RUNTIME DEMO -- brute force O(n^3) vs expand-around-center O(n^2)")
    print("-" * 72)
    import random
    random.seed(0)
    for n in (50, 150, 400):
        s = "".join(random.choice("ab") for _ in range(n))  # few distinct
        # chars -> long matches, stresses the palindrome check heavily
        t0 = time.perf_counter()
        longest_brute_force(s)
        brute_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        sol.longestPalindrome(s)
        fast_ms = (time.perf_counter() - t0) * 1000

        print(f"n={n:4d}  brute={brute_ms:9.3f} ms   expand_center={fast_ms:7.3f} ms   "
              f"ratio={brute_ms / max(fast_ms, 1e-6):7.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
