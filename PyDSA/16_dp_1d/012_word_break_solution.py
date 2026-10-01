"""
================================================================================
SOLUTION · LeetCode 139 · Word Break                                  [Medium]
https://leetcode.com/problems/word-break/
================================================================================

THE CORE IDEA
--------------
dp[i] MEANS "can the prefix s[:i] be segmented into dictionary words". The
last decision was "which dictionary word ends exactly at position i" --
scan every earlier split point j, and dp[i] is true if dp[j] is already
true AND s[j:i] is in the dictionary:

    dp[0] = True
    dp[i] = any(dp[j] and s[j:i] in wordSet for j in range(i))

A variable-range look-back (not a fixed window) -- this is the same
"scan all valid last-decisions" shape as Coin Change (010), applied over
string positions instead of amounts.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive backtracking recursion, price it, don't ship it): try
every dictionary word as a prefix match at the current position, recurse
on the remainder, backtrack on failure. Without memoization this
recomputes the SAME remaining suffix's segmentability many times over --
classically exponential on adversarial inputs like "aaaa...aaab" against
a dictionary of "a", "aa", "aaa", ... (every position can be reached many
different ways, and each failing path re-explores the same dead end).
See the runtime demo below for the measured blowup.

Approach 1 (memoized top-down) [`word_break_memo`] -- cache each start
index's True/False result the first time it's computed. Collapses to
O(n^2) (or O(n*maxWordLen) with the word-length bound) distinct subproblems.

Approach 2 (tabulated bottom-up) [chosen] -- fill dp[0..n] left to right,
no recursion, no stack-depth ceiling (relevant since Trap B in
`_TOPIC_GUIDE.md` notes Python's recursion limit is a real risk at
this topic's typical input sizes, up to 300 here). O(n^2) time (bounded to
O(n*maxWordLen) by only trying split points within maxWordLen of i),
O(n + dictionary size) space.


================================================================================
STEP BY STEP TRACE
================================================================================
s = "leetcode", wordDict = {"leet", "code"}     (n = 8)

dp[0] = True   (empty prefix)
dp[1..3]: no j with dp[j] True and s[j:i] in the dict -> all False
          ("l","le","lee" are not in the dictionary)
dp[4]: try j=0: dp[0]=True and s[0:4]="leet" in dict -> dp[4] = True
dp[5..7]: no valid (j, word) pair makes these true
          ("leetc","leetco","leetcod" not reachable) -> False
dp[8]: try j=4: dp[4]=True and s[4:8]="code" in dict -> dp[8] = True

 i    : 0     1  2  3  4     5  6  7  8
dp[i] : True  F  F  F  True  F  F  F  True    <- answer dp[8] = True

Segmentation reconstructed by walking back: dp[8] came from j=4 ("code"),
dp[4] came from j=0 ("leet") -> "leet" + "code".


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time                Space              Mutates input?
    -------------------------------  ------------------  -----------------  --------------
    Naive backtracking recursion     exponential worst    O(n) call depth    no
    Memoized top-down                O(n * maxWordLen)    O(n)               no
    Tabulated bottom-up [chosen]     O(n * maxWordLen)    O(n)               no


================================================================================
EDGE CASES
================================================================================
    s exactly equals one dictionary
    word                              -> dp[n] reached via a single split
                                        at j=0; smallest possible "true" case.
    no valid segmentation exists
    ("catsandog")                     -> "cats"+"and"+"og"? "og" not in
                                        dict; "cat"+"sand"+"og"? still "og"
                                        missing -- every path dead-ends,
                                        dp[n] stays False.
    a word can be REUSED multiple
    times ("applepenapple")           -> the dp recurrence naturally
                                        allows this: dp[j] doesn't care
                                        HOW many times a word has already
                                        been used, only that the prefix up
                                        to j is segmentable.
    adversarial repeated-character
    string with an unreachable tail
    ("aaa...aaab" vs {"a","aa",...})  -> the exact case that makes naive
                                        backtracking exponential -- many
                                        ways to reach each 'a'-only
                                        position, all eventually fail at
                                        the trailing 'b'. Demonstrated live
                                        below.


================================================================================
COMMON MISTAKES
================================================================================
1. Checking word membership with `s[j:i] in wordDict` where wordDict is
   still a LIST -- O(len(wordDict)) per check instead of O(1); convert to
   a set first (a classic reuse/efficiency miss, not a correctness one).
2. Not memoizing/tabulating at all and shipping the naive backtracking
   recursion -- passes small examples, times out or effectively hangs on
   adversarial inputs at the problem's own stated bound (s.length up to 300).
3. Off-by-one in the slice: `s[j:i]` is the substring from split point j
   up to (not including) i -- easy to shift by one and check `s[j:i+1]` or
   `s[j-1:i]` instead.
4. Forgetting that dp[i] can be satisfied by MULTIPLE different j values --
   stopping the inner scan too early (e.g. only trying the LONGEST or
   SHORTEST matching word) instead of trying all valid j and taking any
   success.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Can you return ALL possible segmentations, not just true/false?" -> LC
  140 Word Break II -- same dp[i] feasibility check first (prunes
  hopeless branches), then a separate backtracking pass collects every
  valid split, memoizing the list of segmentations per start index.
- "How would you speed up the substring/dictionary matching for a huge
  dictionary?" -> build a Trie of the dictionary words and walk it
  character-by-character from each position instead of slicing +
  hashing every candidate substring.
- "What's the tightest complexity bound?" -> O(n * maxWordLen) once the
  inner loop only tries split points within maxWordLen characters of i,
  since no dictionary word can be longer than that.


================================================================================
RELATED PROBLEMS
================================================================================
- Word Break II (LC 140) -- same feasibility DP, extended to enumerate
  segmentations.
- 010 Coin Change (LC 322) -- same "scan all valid last decisions" 1D DP
  shape, over amounts instead of string positions.
- 013 Longest Increasing Subsequence -- also variable-range look-back
  ("which earlier element does this one extend"), same technique family.
================================================================================
"""

import sys
import time
from typing import List


class Solution:
    def wordBreak(self, s: str, wordDict: List[str]) -> bool:
        word_set = set(wordDict)
        max_len = max((len(w) for w in word_set), default=0)
        n = len(s)
        dp = [False] * (n + 1)
        dp[0] = True
        for i in range(1, n + 1):
            for j in range(max(0, i - max_len), i):
                if dp[j] and s[j:i] in word_set:
                    dp[i] = True
                    break
        return dp[n]


def word_break_naive(s: str, wordDict: List[str]) -> bool:
    word_set = set(wordDict)

    def solve(start: int) -> bool:
        if start == len(s):
            return True
        for end in range(start + 1, len(s) + 1):
            if s[start:end] in word_set and solve(end):
                return True
        return False

    return solve(0)


def word_break_memo(s: str, wordDict: List[str]) -> bool:
    word_set = set(wordDict)
    memo = {}

    def solve(start: int) -> bool:
        if start == len(s):
            return True
        if start in memo:
            return memo[start]
        ok = False
        for end in range(start + 1, len(s) + 1):
            if s[start:end] in word_set and solve(end):
                ok = True
                break
        memo[start] = ok
        return ok

    return solve(0)


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ("leetcode", ["leet", "code"], True),
        ("applepenapple", ["apple", "pen"], True),
        ("catsandog", ["cats", "dog", "sand", "and", "cat"], False),
        ("a", ["a"], True),
        ("a", ["b"], False),
        ("aaaaaaa", ["aaaa", "aaa"], True),
        ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaab", ["a", "aa", "aaa", "aaaa", "aaaaa"], False),
    ]
    for s, wordDict, want in cases:
        got = sol.wordBreak(s, wordDict[:])
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  s={s!r} dict={wordDict}  -> {got}  (want {want})")
        assert word_break_memo(s, wordDict[:]) == want

    print()
    print("RUNTIME DEMO -- naive backtracking (exponential) vs memoized DP (polynomial)")
    print("-" * 72)
    print("(adversarial input: 'aaa...a' + 'b', dict = {'a','aa','aaa','aaaa','aaaaa'})")
    sys.setrecursionlimit(10000)
    dictionary = ["a", "aa", "aaa", "aaaa", "aaaaa"]
    for n in (14, 18, 22):
        s = "a" * n + "b"
        t0 = time.perf_counter()
        naive_result = word_break_naive(s, dictionary)
        naive_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        memo_result = word_break_memo(s, dictionary)
        memo_ms = (time.perf_counter() - t0) * 1000

        assert naive_result == memo_result == False
        print(f"n={n:3d}  naive={naive_ms:9.3f} ms   memo={memo_ms:7.4f} ms   "
              f"ratio={naive_ms / max(memo_ms, 1e-6):9.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
