"""
================================================================================
SOLUTION · LeetCode 87 · Scramble String                                 [Hard]
https://leetcode.com/problems/scramble-string/
================================================================================

THE CORE IDEA
--------------
`s2` scrambles from `s1` iff SOME split point `i` makes either the no-swap
pairing (`s1[:i]`~`s2[:i]` and `s1[i:]`~`s2[i:]`) or the swap pairing
(`s1[:i]`~`s2[-i:]` and `s1[i:]`~`s2[:-i]`) both recursively true — checked
all the way down to length-1 base cases. Memoize on the literal `(s1, s2)`
substring pair so the same comparison, reached via different split
histories, is only ever solved once; that turns an exponential search into
O(n^4).


================================================================================
MULTIPLE APPROACHES
================================================================================
1. NAIVE UNMEMOIZED RECURSION — identical branching, no cache. Correct but
   exponential: re-derives the same `(s1, s2)` comparison from many different
   split paths. Priced, not written: infeasible past roughly n=12-15 within a
   reasonable time budget; the memoization payoff is demonstrated live below
   via actual cache hit/miss counts on a hard case.
2. TOP-DOWN MEMOIZED RECURSION (the intended answer) — O(n^4) time, O(n^4)
   worst-case memo space. Written below as the primary solution.
3. BOTTOM-UP 4D DP — `dp[length][i][j] = True` if `s1[i:i+length]` scrambles
   to `s2[j:j+length]`, built up from `length=1`. Same O(n^4) asymptotics as
   the memoized recursion, iterative instead of recursive; written as an
   alternative to show the two are the same algorithm in different clothing.


================================================================================
STEP BY STEP TRACE — isScramble("great", "rgeat")
================================================================================
    isScramble("great", "rgeat")
      multiset check: sorted("great") == sorted("rgeat") -> True, continue
      try split i=1: "g"/"reat" vs "r"/"geat"
        no-swap: "g"~"r"?  chars differ -> False
        swap:    "g"~"t" (s2[-1:]="t")? differ -> False
                 "reat"~"rgea" (s2[:-1]="rgea")? multiset differs -> False
        i=1 fails entirely
      try split i=2: "gr"/"eat" vs "rg"/"eat"
        no-swap: "gr"~"rg"?  multiset matches, recurse...
                    isScramble("gr","rg"): split i=1: "g"/"r" vs "r"/"g":
                      no-swap "g"~"r" False; swap "g"~"g" True and "r"~"r" True
                      -> isScramble("gr","rg") = True
                 "eat"~"eat"? identical strings -> True immediately
        no-swap succeeds for i=2: isScramble("great","rgeat") = True

Only two split points needed to find a witness; the memo cache means
"eat"~"eat" and any repeated sub-comparisons across other split attempts
(e.g. from i=3, i=4) are answered instantly rather than re-derived.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                  Time      Space     Mutates input?  Note
    -------------------------  --------  --------  ---------------  --------------------------------
    Naive unmemoized           exp.      O(n)      no               re-derives shared subproblems
                                                                     repeatedly; priced only
    Top-down memoized          O(n^4)    O(n^4)    no               memo keyed on the (s1,s2) pair
    Bottom-up 4D DP             O(n^4)    O(n^3)    no               same algorithm, no recursion,
                                                                     drops the length dimension after use


================================================================================
EDGE CASES
================================================================================
    s1 == s2 (any length)   -> True immediately without checking any split;
                              this is what keeps the recursion from exploring
                              splits on strings that are already a match, and
                              is what makes length-1 identical chars a valid
                              base case return True.
    len == 1, different char -> False immediately; no split is possible on a
                              length-1 string, so this must be a base case,
                              not something the split loop would ever catch.
    Anagram-but-not-scramble  -> "abcdefghijklmnopq" vs "efghijklmnopqcadb":
                              same multiset of letters (so the cheap prune
                              does NOT reject it), yet not reachable by any
                              sequence of split/swap operations — demonstrates
                              the prune is necessary-but-not-sufficient, and
                              the real recursive check is still required.
    Repeated characters       -> "aabb" vs "abab": multiset matches; scramble
                              structure must still be checked recursively
                              since repeats can create multiset-matching
                              splits that aren't structurally reachable.


================================================================================
COMMON MISTAKES
================================================================================
1. Only checking the no-swap pairing and forgetting the swap pairing (or vice
   versa) — the original scrambling algorithm makes an ARBITRARY choice at
   every level of every recursive call that built `s2`, so an `isScramble`
   check must allow for a swap having happened at any point; omitting either
   check silently produces false negatives.
2. Memoizing on `(i, j, length)` positions into the ORIGINAL `s1`/`s2` as if
   this were a classic substring-DP over one fixed pair of strings — this
   problem's recursive calls compare substrings of s1 against SUBSTRINGS OF
   s2 taken from potentially different offsets under the swap case, so the
   memo key must be the actual substring content (or the honest
   (i1, len, i2) triple into the two original strings), not just a single
   shared index pair as in, say, longest-common-subsequence.
3. Skipping the character-multiset prune under the assumption it's "just an
   optimization" — without it, real inputs at n=30 with no shared answer can
   take dramatically longer, since the recursion explores every split before
   discovering no combination works; the prune turns most True/False
   decisions for clearly-mismatched strings into O(n log n) (the sort) work.
4. Using `s1[:i]` / `s2[-i:]` correctly for the swap case but getting the
   COMPLEMENT halves backwards — the swap case pairs `s1[:i]` with `s2[-i:]`
   (the LAST i characters of s2) AND `s1[i:]` with `s2[:-i]` (the FIRST
   n-i characters of s2); swapping which half pairs with which silently
   checks a different (wrong) hypothesis.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you improve on O(n^4)?
A: Not asymptotically with this approach — the state space genuinely has
   O(n^2) starting-position pairs times O(n) lengths times O(n) split
   choices per state, and no known polynomial improvement beats O(n^4) for
   this exact problem; n <= 30 in the constraints exists precisely because
   O(n^4) (and its ~n^5 practical constant from the split loop) is the
   expected ceiling.

Q: Why is the character-multiset prune correct — could two strings with the
   same multiset ever still NOT be scrambles of each other?
A: Yes, absolutely — same multiset is NECESSARY but not SUFFICIENT (see the
   "abcdefghijklmnopq" example in Edge Cases); the prune only ever produces
   early FALSE-only shortcuts, it never claims True without the full
   recursive check, so it cannot introduce incorrect positives.

Q: How would memory scale if this needed to run on much longer strings?
A: The O(n^4) memo becomes the bottleneck well before time does; a common
   mitigation is memoizing on a hashed/interned key instead of the raw
   substring pair to reduce memory overhead per entry, though the number of
   DISTINCT entries stays the same — true scaling would need a fundamentally
   different algorithm, which isn't known for this problem.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 5    Longest Palindromic Substring — same "recurse on (i, length)
            windows into a string" DP shape, one string instead of a pair.
    LC 10   Regular Expression Matching — another two-string recursive
            match with memoization on the (i, j) position pair.
    Topic 17 (DP 2D) — the general two-sequence memoized-recursion family
            this problem belongs to structurally.
================================================================================
"""

from functools import lru_cache


class Solution:
    def isScramble(self, s1: str, s2: str) -> bool:
        """Top-down memoized recursion. O(n^4) time, O(n^4) space."""

        @lru_cache(maxsize=None)
        def scramble(a: str, b: str) -> bool:
            if a == b:
                return True
            if sorted(a) != sorted(b):
                return False
            n = len(a)
            for i in range(1, n):
                if scramble(a[:i], b[:i]) and scramble(a[i:], b[i:]):
                    return True
                if scramble(a[:i], b[-i:]) and scramble(a[i:], b[:-i]):
                    return True
            return False

        result = scramble(s1, s2)
        scramble.cache_clear()
        return result

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def isScramble_naive_unmemoized(self, s1: str, s2: str) -> bool:
        """WRONG SCALING, kept only to demonstrate the exponential blowup.
        Identical logic, no memoization."""

        def scramble(a: str, b: str) -> bool:
            if a == b:
                return True
            if sorted(a) != sorted(b):
                return False
            n = len(a)
            for i in range(1, n):
                if scramble(a[:i], b[:i]) and scramble(a[i:], b[i:]):
                    return True
                if scramble(a[:i], b[-i:]) and scramble(a[i:], b[:-i]):
                    return True
            return False

        return scramble(s1, s2)

    def isScramble_bottom_up(self, s1: str, s2: str) -> bool:
        """Bottom-up 4D DP (collapsed to 3D by dropping length after use).
        O(n^4) time, O(n^3) space."""
        n = len(s1)
        if n != len(s2):
            return False
        # dp[length][i][j]: True if s1[i:i+length] scrambles to s2[j:j+length]
        dp = [[[False] * n for _ in range(n)] for _ in range(n + 1)]
        for i in range(n):
            for j in range(n):
                dp[1][i][j] = s1[i] == s2[j]

        for length in range(2, n + 1):
            for i in range(n - length + 1):
                for j in range(n - length + 1):
                    for k in range(1, length):
                        no_swap = dp[k][i][j] and dp[length - k][i + k][j + k]
                        swap = dp[k][i][j + length - k] and dp[length - k][i + k][j]
                        if no_swap or swap:
                            dp[length][i][j] = True
                            break
        return dp[n][0][0]


# ==============================================================================
# TESTS — run:  python 023_scramble_string_solution.py
# ==============================================================================
CASES = [
    ("great", "rgeat", True),
    ("abcde", "caebd", False),
    ("a", "a", True),
    ("a", "b", False),
    ("abc", "bca", True),
    ("abcdefghijklmnopq", "efghijklmnopqcadb", False),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    impls = [
        ("top-down memoized ", sol.isScramble),
        ("bottom-up 4D DP    ", sol.isScramble_bottom_up),
    ]

    for name, fn in impls:
        ok = all(fn(s1, s2) == expected for s1, s2, expected in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # ----------------------------------------------------------------------
    # Memoization payoff: actual cache hit/miss counts, measured live via
    # lru_cache.cache_info() (not asserted from theory).
    # ----------------------------------------------------------------------
    from functools import lru_cache

    print("\n--- memoization payoff, measured via lru_cache.cache_info() ---")
    s1, s2 = "abcdefghijklmnopq", "efghijklmnopqcadb"  # the hardest case above

    @lru_cache(maxsize=None)
    def scramble_counted(a: str, b: str) -> bool:
        if a == b:
            return True
        if sorted(a) != sorted(b):
            return False
        n = len(a)
        for i in range(1, n):
            if scramble_counted(a[:i], b[:i]) and scramble_counted(a[i:], b[i:]):
                return True
            if scramble_counted(a[:i], b[-i:]) and scramble_counted(a[i:], b[:-i]):
                return True
        return False

    result = scramble_counted(s1, s2)
    info = scramble_counted.cache_info()
    ok = result == sol.isScramble(s1, s2)
    all_ok &= ok
    print(f"  isScramble({s1!r}, {s2!r}) -> {result}")
    print(f"  {info.misses} distinct (s1, s2) pairs actually computed; "
          f"{info.hits} repeat lookups answered instantly from cache "
          f"instead of re-recursing.")
    print(f"  {'PASS' if ok else 'FAIL'} — memoized and reference implementation agree.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
