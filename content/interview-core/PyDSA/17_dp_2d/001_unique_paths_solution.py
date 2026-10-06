"""
================================================================================
SOLUTION · LeetCode 62 · Unique Paths                                 [Medium]
https://leetcode.com/problems/unique-paths/
================================================================================

THE CORE IDEA
--------------
Every cell (i, j) can only be entered from above (i-1, j) or from the left
(i, j-1) — those are the only two legal predecessors, since the robot never
moves up or left. So the number of ways to reach (i, j) is simply the SUM of
the ways to reach its two predecessors:

    dp[i][j] = dp[i-1][j] + dp[i][j-1]

with dp[0][*] = dp[*][0] = 1 (only one way to walk in a straight line along
the top row or left column). This is the canonical shape every other 2D grid
DP problem in this topic (002, 003, 004) reuses.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, name it and reject it): recurse from (0,0), branching
right/down at every cell, count paths that reach (m-1, n-1). No memoization
-> re-explores the same cell an exponential number of times (the number of
distinct root-to-cell paths through an m x n grid without memo is C(i+j, i),
which blows up combinatorially). O(2^(m+n)) time. Never coded, priced only.

Approach 1 (memoized top-down, 2D cache) -- recursion with an (m x n) memo
table. Same recurrence, each cell computed once. O(m*n) time, O(m*n) space
(memo + recursion stack up to depth m+n).

Approach 2 (bottom-up tabulation, full 2D table) [checked] -- fill the table
row by row, left to right. No recursion, no stack risk. O(m*n) time, O(m*n)
space.

Approach 3 (space-optimized, rolling 1D row) [checked] -- dp[i][j] only ever
reads the row directly above and the current row's own previous entry. Keep
ONE array of length n and update it in place, left to right:
    dp[j] = dp[j] (value from row above, not yet overwritten) + dp[j-1] (this
    row's already-updated left neighbor)
O(m*n) time, O(n) space -- this is the version actually shipped below.

Approach 4 (closed-form combinatorics) -- the robot makes exactly (m-1) down
moves and (n-1) right moves in some order among (m+n-2) total moves; the
answer is the binomial coefficient C(m+n-2, m-1). O(m+n) time (computing the
combination iteratively to avoid huge intermediate factorials), O(1) space.
Elegant, but interviewers usually want the DP first since it generalizes to
002/003 (obstacles, weighted cells) where no closed form exists.


================================================================================
STEP BY STEP TRACE
================================================================================
m=3, n=3  (rows x cols)

Full 2D table (Approach 2), filled row by row:

        j=0  j=1  j=2
    i=0:  1    1    1      <- top row: only "all rights" reaches any cell
    i=1:  1    2    3      dp[1][1]=dp[0][1]+dp[1][0]=1+1=2
                            dp[1][2]=dp[0][2]+dp[1][1]=1+2=3
    i=2:  1    3    6      dp[2][1]=dp[1][1]+dp[2][0]=2+1=3
                            dp[2][2]=dp[1][2]+dp[2][1]=3+3=6

Answer: dp[2][2] = 6.

Rolling-row version (Approach 3), same grid, tracking the single array:
    start:        row = [1, 1, 1]              (this IS row i=0, the base case)
    after i=1:    row = [1, 2, 3]               row[j] = row[j](=1, old, row0) + row[j-1](=2, new, row1)
    after i=2:    row = [1, 3, 6]
    return row[-1] = 6.  MATCHES.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time        Space      Mutates input?
    ---------------------------------  ----------  ---------  --------------
    Brute force recursion (no memo)    O(2^(m+n))  O(m+n)     n/a (no input)
    Memoized top-down, 2D cache        O(m*n)      O(m*n)     n/a
    Bottom-up tabulation, full table   O(m*n)      O(m*n)     n/a
    Rolling row [chosen]               O(m*n)      O(n)       n/a
    Closed-form C(m+n-2, m-1)          O(m+n)      O(1)       n/a


================================================================================
EDGE CASES
================================================================================
    m == 1 or n == 1     -> single row/column, exactly 1 path (a straight
                             line) -- the base-case row already returns this
                             correctly with no special-casing needed.
    m == n == 1           -> start == destination, 1 trivial "path" (stand
                             still) -- also falls out of the base case.
    m, n at the max (100) -> answer up to C(198, 99) ~ 2.27 x 10^57 in
                             principle, but constraints GUARANTEE the actual
                             answer fits in 32 bits, so no overflow concern
                             in Python (unbounded ints) or in a correctly
                             constrained test set.


================================================================================
COMMON MISTAKES
================================================================================
1. Swapping the roles of m and n (rows vs. columns) when allocating the
   table -- e.g. building an m x m or n x n table instead of m x n. Silently
   produces a wrong-shaped grid that either crashes on IndexError or, worse,
   quietly returns the wrong number when m == n masks the bug.

2. Initializing the rolling row to all zeros instead of all ones. The top
   row genuinely has exactly one way to reach every cell (walk right the
   whole way) -- starting it at 0 makes every downstream sum 0 forever.

3. Updating the rolling array right-to-left instead of left-to-right. The
   in-place recurrence `dp[j] = dp[j] + dp[j-1]` relies on `dp[j-1]` already
   being THIS row's updated value (not last row's) -- iterating backwards
   would read the previous row's dp[j-1], silently reproducing an unrelated
   (wrong) recurrence.

4. Reaching for the closed-form binomial coefficient by default. It's
   elegant here, but the SAME recurrence must generalize to 002 (Unique
   Paths II, obstacles block cells -- no closed form survives that) and 003
   (Minimum Path Sum, weighted cells) -- practicing the DP table here is what
   pays off two problems later, not the one clever formula.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if some cells were blocked (obstacles)?
A: That's LC 63 (problem 002) -- same recurrence, but dp[i][j] = 0 whenever
   (i, j) is an obstacle, breaking the closed-form approach entirely; the DP
   table is the only surviving tool.

Q: What if diagonal moves were also allowed?
A: dp[i][j] = dp[i-1][j] + dp[i][j-1] + dp[i-1][j-1] -- same shape, one more
   predecessor term. Still O(m*n).

Q: Can you get this down to O(1) extra space?
A: Yes, via the closed-form C(m+n-2, m-1) (Approach 4) -- but only because
   this specific problem has no obstacles/weights breaking the symmetry.

Q: How would you reconstruct one actual path, not just the count?
A: Walk the filled DP table backwards from (m-1, n-1): at each step, move to
   whichever of the "up" or "left" neighbor has the larger dp value (or
   either, if you just want *a* path, not a specific one), recording the
   move, until (0, 0) is reached.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 63   Unique Paths II (002 -- same recurrence + obstacle zeroing)
    LC 64   Minimum Path Sum (003 -- same recurrence shape, min+cost instead
            of sum+count)
    LC 120  Triangle (same "sum from two predecessors" shape on a triangular
            grid)
    LC 931  Minimum Falling Path Sum (three predecessors instead of two)
================================================================================
"""


class Solution:
    def uniquePaths(self, m: int, n: int) -> int:
        """✅ Rolling-row DP. O(m*n) time, O(n) space."""
        row = [1] * n
        for _ in range(1, m):
            for j in range(1, n):
                row[j] += row[j - 1]
        return row[-1]

    def uniquePaths_full_table(self, m: int, n: int) -> int:
        """Alternative: full 2D tabulation, O(m*n) time and space -- useful
        when you also need to reconstruct a path, not just count them."""
        dp = [[1] * n for _ in range(m)]
        for i in range(1, m):
            for j in range(1, n):
                dp[i][j] = dp[i - 1][j] + dp[i][j - 1]
        return dp[m - 1][n - 1]

    def uniquePaths_combinatorics(self, m: int, n: int) -> int:
        """Alternative: closed-form C(m+n-2, m-1). O(m+n) time, O(1) space.
        Only works because there are no obstacles/weights here."""
        from math import comb
        return comb(m + n - 2, m - 1)


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        (3, 7, 28),
        (3, 2, 3),
        (1, 1, 1),
        (1, 10, 1),
        (10, 1, 1),
        (7, 3, 28),
        (23, 12, 193536720),
    ]

    print("--- correctness: rolling-row vs full-table vs combinatorics agree ---")
    for m, n, want in cases:
        got_roll = sol.uniquePaths(m, n)
        got_full = sol.uniquePaths_full_table(m, n)
        got_comb = sol.uniquePaths_combinatorics(m, n)
        ok = got_roll == want and got_full == want and got_comb == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  m={m} n={n}  roll={got_roll} "
              f"full={got_full} comb={got_comb}  (want {want})")

    # --------------------------------------------------------------------
    # RUNTIME DEMO: measure actual memory footprint, O(m*n) full table vs
    # O(n) rolling row, at a large grid (m=n=1000, beyond LC's own m,n<=100
    # bound, chosen specifically to make the list-of-lists allocation cost
    # visible).
    # --------------------------------------------------------------------
    import sys
    print("\n--- DEMO: O(m*n) table vs O(n) rolling row, measured memory ---")
    m = n = 1000

    full = [[1] * n for _ in range(m)]
    full_bytes = sys.getsizeof(full) + sum(sys.getsizeof(r) for r in full)

    roll = [1] * n
    roll_bytes = sys.getsizeof(roll)

    print(f"  m=n={m}:")
    print(f"    full 2D table:  {full_bytes:>10,} bytes ({m} row objects + "
          f"outer list)")
    print(f"    rolling 1D row: {roll_bytes:>10,} bytes (one list object)")
    print(f"    ratio: full table uses {full_bytes / roll_bytes:.1f}x more "
          f"memory than the rolling row, for the identical O(m*n) time and "
          f"the identical final answer.")
    r1 = sol.uniquePaths(m, n)
    r2 = sol.uniquePaths_full_table(m, n)
    print(f"    both agree: {r1 == r2}")
    all_ok &= (r1 == r2)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
