"""
================================================================================
SOLUTION · LeetCode 10 · Regular Expression Matching                      [Hard]
https://leetcode.com/problems/regular-expression-matching/
================================================================================

THE CORE IDEA
--------------
dp[i][j] = does s[:i] fully match p[:j]? A boolean two-index DP (family with
009's Interleaving String), but pattern-driven: case on p[j-1], the LAST
character of the pattern prefix.

Case A -- p[j-1] is a plain letter or '.': must match s[i-1] exactly ('.'
matches anything), and the REST must already match:

    dp[i][j] = dp[i-1][j-1] AND (p[j-1]=='.' OR p[j-1]==s[i-1])

Case B -- p[j-1] == '*': it modifies p[j-2] (the character it follows;
constraints guarantee '*' is never first), and has TWO independent, OR'd
ways to be satisfied:

    "zero occurrences" of p[j-2]: treat "p[j-2]+'*'" as contributing
        NOTHING to s -- dp[i][j] |= dp[i][j-2]  (skip the whole x* unit,
        no character comparison needed at all)
    "one more occurrence" of p[j-2] (only valid if it matches s[i-1]):
        consume ONE character of s but STAY at the same pattern position j
        (since '*' can match many characters) -- dp[i][j] |= dp[i-1][j]

    dp[i][j] = dp[i][j-2] OR (dp[i-1][j] if matches(p[j-2], s[i-1]) else False)

Base case: dp[0][0] = True. dp[0][j] can be True for patterns that match
zero characters (e.g. "a*b*c*") -- NOT automatically False just because s
is empty; it depends entirely on whether every unit in p[:j] is a
zero-occurrence-capable "x*" pair.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, not coded): recursively try, at each
position, every way to consume the pattern (match one char, or expand a
'*' by 0/1/2/... repetitions), backtracking on failure. Exponential in the
worst case (e.g. "aaaa...a" vs "a*a*a*...a*b") -- massively overlapping
(i, j) subproblems reached via different repetition counts.

Approach 1 (memoized top-down, 2D cache) -- recurse on (i, j) with the same
case analysis, cache each boolean. O(len(s)*len(p)) time, O(len(s)*len(p))
space (memo + recursion depth up to len(s)+len(p)).

Approach 2 (bottom-up tabulation, full 2D table) [checked] -- fill dp row
by row using the case-A/case-B recurrence above. O(len(s)*len(p)) time,
O(len(s)*len(p)) space.

Approach 3 (space-optimized, TWO rolling 1D rows) [checked, shipped] --
dp[i][j] reads dp[i-1][j-1] and dp[i-1][j] (the row ABOVE) plus dp[i][j-2]
(the SAME row, two columns back -- unlike every other problem in this
topic, the "zero occurrences" branch looks sideways within its own row,
not just at the row above). A SINGLE in-place rolling array can't safely
serve both needs at once, so this keeps two explicit rows (previous,
current) instead of one -- still O(len(p)) space, just with a small
constant-factor doubling versus a true single-row roll. O(len(s)*len(p))
time, O(len(p)) space.


================================================================================
STEP BY STEP TRACE
================================================================================
s = "aa" (m=2), p = "a*" (n=2)

Full 2D table (rows = s prefixes 0..2, cols = p prefixes 0..2), T/F:

           ""  a  a*
      "" :  T  F  T      <- dp[0][2]: p[1]='*' pairs with p[0]='a';
                             zero-occ: dp[0][0]=T -> dp[0][2]=T
      a  :  F  T  T      <- dp[1][1]: 'a'=='a' AND dp[0][0]=T -> T
                             dp[1][2]: zero-occ dp[1][0]=F; one-more: 'a'
                             matches s[0]='a', dp[0][2]=T -> dp[1][2]=T
      aa:  F  F  T      <- dp[2][1]: dp[1][0]=F -> F
                             dp[2][2]: zero-occ dp[2][0]=F; one-more: 'a'
                             matches s[1]='a', dp[1][2]=T -> dp[2][2]=T

Answer: dp[2][2] = True.  MATCHES expected ("a*" matches "aa" by repeating
'a' twice via the "one more occurrence" branch, applied twice: dp[1][2]
used dp[0][2], and dp[2][2] used dp[1][2] -- the '*' consumes one s
character per dp transition while staying at the same pattern column).


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time              Space          Mutates input?
    ---------------------------------  ----------------  -------------  --------------
    Brute force recursion (no memo)    exponential       O(len(s)+len(p))  no
    Memoized top-down, 2D cache        O(len(s)*len(p))  O(len(s)*len(p))  no
    Bottom-up tabulation, full table   O(len(s)*len(p))  O(len(s)*len(p))  no
    Two rolling rows [chosen]          O(len(s)*len(p))  O(len(p))         no


================================================================================
EDGE CASES
================================================================================
    Empty s, pattern all "x*" pairs (e.g. p="a*b*c*") -> True -- every unit
                                can independently choose zero occurrences;
                                dp[0][j] must be computed correctly across
                                the FULL top row, not assumed False.
    Empty p, non-empty s     -> always False -- dp[i][0]=False for i>0.
    '.' matching everything   -> ".*" matches any string including empty
                                (Example 3) -- '.' never fails a character
                                comparison, only the star-repetition logic
                                controls length.
    '*' with zero prior matches in s (e.g. p="a*" vs s="b...") -> the
                                "zero occurrence" branch must still work
                                even when the "one more occurrence" branch
                                never fires because the character never
                                matches -- these are independent OR terms,
                                not a fallback chain.
    Pattern longer than string or vice versa -> handled naturally since the
                                dp table's shape covers len(s)+1 by
                                len(p)+1 regardless of which is longer.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting the "zero occurrences" branch entirely and only implementing
   "match one more" -- this makes '*' behave like a mandatory "one or
   more," which is wrong (breaks patterns like "a*" matching empty s, or
   "c*a*b" matching "aab" where 'c' must occur ZERO times).

2. In the "one more occurrence" branch, mistakenly reading dp[i-1][j-2]
   instead of dp[i-1][j] -- that would only allow '*' to match EXACTLY one
   extra character total, not "zero or more" (arbitrarily many); staying at
   column j (not j-2) across the recursive/iterative step is what allows
   repeated matching, one character at a time, over multiple dp[i][j] steps.

3. Assuming dp[0][j] is always False because s is empty -- WRONG whenever
   p[:j] is built entirely from "x*" units that can each independently
   contribute zero characters; this must be computed explicitly, not
   defaulted.

4. Treating '.' and '*' identically, or checking `p[j-1] == '*'` BEFORE
   checking whether j >= 2 (to safely index p[j-2]) -- since constraints
   guarantee '*' always has a preceding valid character, j>=2 is
   guaranteed whenever p[j-1]=='*', but a hand-rolled implementation that
   doesn't rely on that guarantee (e.g. testing malformed patterns) needs
   an explicit bounds check to avoid IndexError.

5. Attempting the naive single-rolling-array space optimization used in
   004/005/010 -- here dp[i][j-2] (same row, not previous row) means a
   single row updated strictly left-to-right can still read an
   ALREADY-UPDATED value at j-2 by the time j is processed, which is
   actually the CORRECT behavior for this recurrence (dp[i][j-2] SHOULD be
   this row's value) -- but it's easy to instead accidentally read a stale
   previous-row value if the implementation isn't careful about which row
   each read is supposed to come from. Keeping two explicit named rows
   (prev, curr) avoids this ambiguity entirely.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How does this differ from Wildcard Matching (LC 44)?
A: LC 44's '*' matches any sequence of characters directly (no "preceding
   element" concept -- '*' is a standalone wildcard for zero-or-more of
   ANY characters, and '?' matches exactly one), so its recurrence is
   simpler: dp[i][j] = dp[i-1][j-1] (char match) or dp[i-1][j] or dp[i][j-1]
   (star matches empty or absorbs one more char) -- no "preceding element"
   pairing step needed at all.

Q: What if the pattern needed to match a SUBSTRING of s, not the entire
   string?
A: Different problem shape -- would need to try matching starting at every
   position in s (or equivalently, prepend ".*" to the pattern
   conceptually), not a simple tweak of this DP's base case.

Q: How would you handle '+' (one or more) if it were added to the pattern
   language?
A: "x+" is equivalent to "xx*" -- could be preprocessed away by expanding
   it before running this same DP, or handled with a near-identical
   recurrence that drops the "zero occurrences" OR-branch (since '+'
   requires at least one).

Q: Time/space complexity in terms of both string lengths -- why is space
   O(len(p)) with two rows and not O(len(s))?
A: Arbitrary choice of which axis to roll -- the implementation rolls over
   s (row = current s-prefix, columns = full p-prefix range) because p's
   "look two columns back" dependency is easiest to reason about within a
   single row; rolling the other way (row = p-prefix) is equally valid and
   would give O(len(s)) instead.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 44   Wildcard Matching (similar surface problem, simpler recurrence
            -- no "preceding element" pairing)
    LC 97   Interleaving String (009 -- same boolean two-index DP family,
            symmetric two-source transitions instead of pattern-driven)
    LC 72   Edit Distance (010 -- same family, numeric min instead of
            boolean, no metacharacters)
================================================================================
"""


class Solution:
    def isMatch(self, s: str, p: str) -> bool:
        """✅ Two rolling 1D rows (previous s-prefix row, current row).
        O(len(s)*len(p)) time, O(len(p)) space."""
        m, n = len(s), len(p)

        def matches(si: int, pj: int) -> bool:
            """Does p[pj] match s[si] (or is p[pj] '.')? si, pj 0-indexed."""
            return p[pj] == "." or p[pj] == s[si]

        prev = [False] * (n + 1)  # dp[0][*]
        prev[0] = True
        for j in range(1, n + 1):
            if p[j - 1] == "*" and j >= 2:
                prev[j] = prev[j - 2]  # zero occurrences, s still empty

        for i in range(1, m + 1):
            curr = [False] * (n + 1)  # dp[i][*], curr[0] stays False
            for j in range(1, n + 1):
                if p[j - 1] == "*":
                    curr[j] = curr[j - 2]  # zero occurrences (same row!)
                    if matches(i - 1, j - 2):
                        curr[j] = curr[j] or prev[j]  # one more occurrence
                else:
                    curr[j] = prev[j - 1] and matches(i - 1, j - 1)
            prev = curr
        return prev[n]

    def isMatch_full_table(self, s: str, p: str) -> bool:
        """Alternative: full 2D tabulation, O(len(s)*len(p)) time and
        space -- clearer to trace by hand, no row-management bookkeeping."""
        m, n = len(s), len(p)

        def matches(si: int, pj: int) -> bool:
            return p[pj] == "." or p[pj] == s[si]

        dp = [[False] * (n + 1) for _ in range(m + 1)]
        dp[0][0] = True
        for j in range(1, n + 1):
            if p[j - 1] == "*" and j >= 2:
                dp[0][j] = dp[0][j - 2]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if p[j - 1] == "*":
                    dp[i][j] = dp[i][j - 2]
                    if matches(i - 1, j - 2):
                        dp[i][j] = dp[i][j] or dp[i - 1][j]
                else:
                    dp[i][j] = dp[i - 1][j - 1] and matches(i - 1, j - 1)
        return dp[m][n]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ("aa", "a", False),
        ("aa", "a*", True),
        ("ab", ".*", True),
        ("aab", "c*a*b", True),
        ("mississippi", "mis*is*p*.", False),
        ("", "a*", True),
        ("", ".*", True),
        ("ab", ".*c", False),
    ]

    print("--- correctness: two-row rolling vs full table agree ---")
    for s, p, want in cases:
        got_roll = sol.isMatch(s, p)
        got_full = sol.isMatch_full_table(s, p)
        ok = got_roll == want and got_full == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  s={s!r} p={p!r} roll={got_roll} "
              f"full={got_full}  (want {want})")

    # --------------------------------------------------------------------
    # RUNTIME DEMO: prove mistake #2 ('one more occurrence' reading
    # dp[i-1][j-2] instead of dp[i-1][j]) actually breaks multi-repeat
    # matching, live.
    # --------------------------------------------------------------------
    print("\n--- DEMO: correct 'stay at column j' vs buggy 'jump to j-2' for '*' ---")

    def is_match_buggy_jump(s, p):
        m, n = len(s), len(p)

        def matches(si, pj):
            return p[pj] == "." or p[pj] == s[si]

        dp = [[False] * (n + 1) for _ in range(m + 1)]
        dp[0][0] = True
        for j in range(1, n + 1):
            if p[j - 1] == "*" and j >= 2:
                dp[0][j] = dp[0][j - 2]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if p[j - 1] == "*":
                    dp[i][j] = dp[i][j - 2]
                    if matches(i - 1, j - 2):
                        # BUG: should be dp[i-1][j] (stay), not dp[i-1][j-2]
                        # (only allows exactly one extra repeat, not "many")
                        dp[i][j] = dp[i][j] or dp[i - 1][j - 2]
                else:
                    dp[i][j] = dp[i - 1][j - 1] and matches(i - 1, j - 1)
        return dp[m][n]

    s, p = "aaa", "a*"  # needs THREE repeats of 'a' -- only works if '*'
    # can chain across multiple dp transitions, not just one extra repeat
    correct = sol.isMatch(s, p)
    buggy = is_match_buggy_jump(s, p)
    print(f"  s={s!r}, p={p!r}  (requires matching 3 repeats of 'a')")
    print(f"  correct ('*' stays at column j, can chain):  {correct}")
    print(f"  buggy   ('*' jumps to j-2, one repeat only):  {buggy}")
    print(f"  buggy diverges from correct: {buggy != correct}")
    all_ok &= correct is True

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
