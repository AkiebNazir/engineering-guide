"""
================================================================================
SOLUTION · LeetCode 72 · Edit Distance                                 [Medium]
https://leetcode.com/problems/edit-distance/
================================================================================

THE CORE IDEA
--------------
dp[i][j] = minimum operations to convert word1[:i] into word2[:j]. Same
"two strings, two indices" skeleton as LCS (005), but where LCS only ever
"agrees or skips" (max of two neighbors), Edit Distance additionally allows
REPLACE, giving a MIN of THREE neighbor operations:

    word1[i-1] == word2[j-1]:  dp[i][j] = dp[i-1][j-1]           (free -- no
                                                                    op needed)
    word1[i-1] != word2[j-1]:  dp[i][j] = 1 + min(
                                    dp[i-1][j-1],   # REPLACE word1[i-1]
                                    dp[i-1][j],     # DELETE word1[i-1]
                                    dp[i][j-1])     # INSERT word2[j-1]

Base case: dp[i][0] = i (delete all i chars to reach empty), dp[0][j] = j
(insert all j chars to build word2 from empty) -- these are the "forced"
straight-line edges of the table, exactly like LCS's zero row/column but
counting UP instead of staying at 0.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, not coded): recursively try all three
operations at every mismatched position, take the min over all resulting
edit sequences. O(3^(m+n)) time -- massive overlap of the same (i, j)
subproblem reached via different operation orderings.

Approach 1 (memoized top-down, 2D cache) -- recurse on (i, j) = "min edits
to convert word1[i:] to word2[j:]", cache each pair. O(m*n) time, O(m*n)
space (memo + recursion depth m+n).

Approach 2 (bottom-up tabulation, full 2D table) [checked] -- fill dp row
by row using the match/replace-delete-insert recurrence. O(m*n) time,
O(m*n) space.

Approach 3 (space-optimized, rolling 1D row) [checked, shipped] -- dp[i][j]
reads dp[i-1][j-1] (diagonal, snapshotted before overwrite), dp[i-1][j]
(row above, same column), dp[i][j-1] (same row, already updated). One row
of length min(m,n)+1, oriented over the SHORTER word. O(m*n) time,
O(min(m,n)) space.


================================================================================
STEP BY STEP TRACE
================================================================================
word1 = "horse" (m=5), word2 = "ros" (n=3)

Full 2D table (rows = word1 prefixes 0..5, cols = word2 prefixes 0..3):

           ""  r  o  s
      "" :  0  1  2  3
      h  :  1  1  2  3     <- dp[1][1]: 'h'!='r', 1+min(dp[0][0]=0,dp[0][1]=1,
                               dp[1][0]=1)=1+0=1
      o  :  2  2  1  2     <- dp[2][2]: 'o'=='o', dp[1][1]=1
      r  :  3  2  2  2     <- dp[3][1]: 'r'=='r', dp[2][0]=2
      s  :  4  3  3  2     <- dp[4][3]: 's'=='s', dp[3][2]=2
      e  :  5  4  4  3     <- dp[5][3]: 'e'!='s', 1+min(dp[4][2]=3,dp[4][3]=2,
                               dp[5][2]=4)=1+2=3

Answer: dp[5][3] = 3.  MATCHES expected (replace h->r, delete r, delete e:
horse -> rorse -> rose -> ros, 3 operations).


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time     Space        Mutates input?
    ---------------------------------  -------  -----------  --------------
    Brute force recursion (no memo)    O(3^(m+n))  O(m+n)    n/a
    Memoized top-down, 2D cache        O(m*n)   O(m*n)       n/a
    Bottom-up tabulation, full table   O(m*n)   O(m*n)       n/a
    Rolling row [chosen]               O(m*n)   O(min(m,n))  n/a


================================================================================
EDGE CASES
================================================================================
    Either word empty       -> answer is the other word's length (all
                                inserts or all deletes) -- the forced
                                base row/column handles this directly.
    Both words identical     -> answer 0, dp never leaves the diagonal-match
                                (free) branch.
    Completely disjoint chars -> every position is a replace, answer equals
                                max(len(word1), len(word2)) when lengths
                                differ (replace the shared prefix length,
                                insert/delete the remainder) -- NOT simply
                                the length sum.
    One word is a substring extension of the other -> answer equals the
                                length difference (pure inserts or deletes,
                                no replaces needed).


================================================================================
COMMON MISTAKES
================================================================================
1. Adding 1 to dp[i-1][j-1] even when the characters MATCH -- that spends an
   operation on a position that needs none; the match branch must copy
   dp[i-1][j-1] with NO +1.

2. In the rolling-row version, forgetting to snapshot the pre-overwrite
   diagonal value (dp[i-1][j-1]) before row[j-1] gets updated to dp[i][j-1]
   in the same pass -- same trap as 004 (Maximal Square) and 005 (LCS),
   because REPLACE reads the diagonal exactly like a square's corner does.

3. Confusing this with LCS's recurrence -- LCS takes MAX of two neighbors on
   a mismatch (never touching the diagonal on a mismatch); Edit Distance
   takes MIN of THREE neighbors including the diagonal on every mismatch.
   Mixing the two recurrences up is the single most common bug when
   switching between the two problems back to back.

4. Wrong base case direction -- dp[i][0] must equal i (not 0), because
   converting a non-empty word1 prefix to an EMPTY word2 prefix costs i
   deletions, not zero.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if operations had different costs (e.g. replace costs 2, insert/
   delete cost 1)?
A: Change the "+1" in each branch to "+cost_of_that_operation" -- the
   recurrence shape is unchanged, only the combinator's constants change.

Q: How would you reconstruct the actual sequence of edits?
A: Keep the full 2D table and walk backwards from dp[m][n]: if characters
   match, step diagonally with no recorded op; else step toward whichever
   of the three neighbors achieved the min, recording that operation.

Q: Relationship to LCS (005)?
A: LCS = m + n - 2*edit_distance_using_only_insert_and_delete (no replace
   allowed) -- when replace is disallowed, edit distance and LCS become two
   sides of the same coin; allowing replace here is what breaks that exact
   identity.

Q: Can you do it in O(min(m,n)) space AND still reconstruct the edit path?
A: Not directly -- reconstruction needs the full table (or Hirschberg's
   divide-and-conquer technique, which recovers O(m+n) space while still
   reconstructing the path, at the cost of a more involved algorithm).


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 1143  Longest Common Subsequence (005 -- same two-index family, max
             of two neighbors instead of min of three)
    LC 97    Interleaving String (009 -- same family, boolean OR instead of
             numeric min)
    LC 583   Delete Operation for Two Strings (edit distance restricted to
             delete-only, equals m + n - 2*LCS)
    LC 44    Wildcard Matching / LC 10 Regular Expression Matching (014 --
             pattern-driven two-index boolean DP, different transition rules)
================================================================================
"""


class Solution:
    def minDistance(self, word1: str, word2: str) -> int:
        """✅ Rolling-row DP, oriented so the row spans the SHORTER word.
        O(m*n) time, O(min(m,n)) space."""
        if len(word1) < len(word2):
            word1, word2 = word2, word1  # word2 is now the shorter word
        m, n = len(word1), len(word2)

        row = list(range(n + 1))  # dp[0][j] = j
        for i in range(1, m + 1):
            prev_diag = row[0]  # dp[i-1][0]
            row[0] = i  # dp[i][0] = i
            c1 = word1[i - 1]
            for j in range(1, n + 1):
                up = row[j]  # dp[i-1][j] before overwrite
                if c1 == word2[j - 1]:
                    row[j] = prev_diag
                else:
                    row[j] = 1 + min(prev_diag, up, row[j - 1])
                prev_diag = up
        return row[-1]

    def minDistance_full_table(self, word1: str, word2: str) -> int:
        """Alternative: full 2D tabulation, O(m*n) time and space -- useful
        when the actual edit sequence also needs to be reconstructed."""
        m, n = len(word1), len(word2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if word1[i - 1] == word2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = 1 + min(dp[i - 1][j - 1], dp[i - 1][j], dp[i][j - 1])
        return dp[m][n]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ("horse", "ros", 3),
        ("intention", "execution", 5),
        ("", "", 0),
        ("", "abc", 3),
        ("abc", "", 3),
        ("abc", "abc", 0),
    ]

    print("--- correctness: rolling row vs full table agree ---")
    for w1, w2, want in cases:
        got_roll = sol.minDistance(w1, w2)
        got_full = sol.minDistance_full_table(w1, w2)
        ok = got_roll == want and got_full == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  word1={w1!r} word2={w2!r} "
              f"roll={got_roll} full={got_full}  (want {want})")

    # --------------------------------------------------------------------
    # RUNTIME DEMO: prove mistake #3 (using LCS's max-of-two recurrence
    # instead of edit distance's min-of-three) diverges on real input.
    # --------------------------------------------------------------------
    print("\n--- DEMO: edit-distance recurrence vs LCS-style recurrence, same input ---")

    def wrong_using_lcs_shape(word1, word2):
        m, n = len(word1), len(word2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if word1[i - 1] == word2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    # BUG: LCS-style max of two, no diagonal, no +1
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
        return dp[m][n]

    w1, w2 = "horse", "ros"
    correct = sol.minDistance(w1, w2)
    wrong = wrong_using_lcs_shape(w1, w2)
    print(f"  word1={w1!r}, word2={w2!r}")
    print(f"  correct (edit-distance min-of-three): {correct}")
    print(f"  wrong   (LCS-shaped max-of-two):       {wrong}")
    print(f"  diverges: {wrong != correct}")
    all_ok &= (correct == 3)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
