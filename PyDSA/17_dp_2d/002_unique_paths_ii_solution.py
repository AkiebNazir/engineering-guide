"""
================================================================================
SOLUTION · LeetCode 63 · Unique Paths II                              [Medium]
https://leetcode.com/problems/unique-paths-ii/
================================================================================

THE CORE IDEA
--------------
Identical recurrence to 001 (dp[i][j] = dp[i-1][j] + dp[i][j-1]), plus one
override: an obstacle cell can never be landed on, so its dp value is forced
to 0 -- which then correctly propagates zero contribution to every cell that
would otherwise route a path through it. This one override is exactly what
kills 001's closed-form binomial shortcut: with holes in the grid there is no
longer a clean "choose which m-1 of m+n-2 moves are down" formula, so the DP
table becomes the ONLY correct tool, not merely the more-obvious one.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, name it and reject it): DFS/backtracking from (0,0),
branching right/down, skipping obstacle cells, counting paths that reach the
end. Exponential re-exploration of the same cells, same blowup as 001's
brute force. O(2^(m+n)) time. Priced, not coded.

Approach 1 (memoized top-down, 2D cache) -- recursion + memo table, obstacle
cells short-circuit to 0 immediately. O(m*n) time, O(m*n) space.

Approach 2 (bottom-up tabulation, full 2D table) [checked] -- fill row by
row; dp[i][j] = 0 if grid[i][j] is an obstacle, else the usual sum (treating
an out-of-bounds predecessor as contributing 0). O(m*n) time, O(m*n) space.

Approach 3 (space-optimized, rolling 1D row) [checked] -- same rolling-row
trick as 001, with the obstacle override applied per cell:
    dp[j] = 0                     if grid[i][j] == 1
    dp[j] = dp[j] + dp[j-1]       otherwise (dp[j] = value from row above,
                                   dp[j-1] = this row's already-updated left
                                   neighbor)
One extra subtlety versus 001: dp[0] (the left column) is NOT automatically 1
for every row anymore -- it must also be zeroed the instant an obstacle
appears in column 0, since after that no path can ever reach anything below
it (only "down" moves reach column 0 at all). O(m*n) time, O(n) space.


================================================================================
STEP BY STEP TRACE
================================================================================
obstacleGrid =
    [0, 0, 0]
    [0, 1, 0]
    [0, 0, 0]

Full 2D table (Approach 2), filled row by row (X marks the obstacle):

        j=0  j=1  j=2
    i=0:  1    1    1      top row, no obstacles -> straight line of 1s
    i=1:  1    X=0  1      dp[1][0]=dp[0][0]=1 (left col, no obstacle yet)
                            dp[1][1]=0 (obstacle, forced)
                            dp[1][2]=dp[0][2]+dp[1][1]=1+0=1
    i=2:  1    1    2      dp[2][0]=dp[1][0]=1
                            dp[2][1]=dp[1][1]+dp[2][0]=0+1=1
                            dp[2][2]=dp[1][2]+dp[2][1]=1+1=2

Answer: dp[2][2] = 2.  MATCHES the expected output (the two paths that swing
around the obstacle on either side).

Rolling-row trace, same grid:
    row i=0: [1, 1, 1]                (base row, no obstacle)
    row i=1: j=0: grid[1][0]=0, not obstacle, dp[0] stays 1 (top-of-column,
                  no left neighbor to add)
             j=1: grid[1][1]=1, OBSTACLE -> row[1] = 0
             j=2: grid[1][2]=0, row[2] = row[2](=1, old) + row[1](=0, new) = 1
             row = [1, 0, 1]
    row i=2: j=0: grid[2][0]=0, row[0] stays 1
             j=1: grid[2][1]=0, row[1] = row[1](=0, old) + row[0](=1, new) = 1
             j=2: grid[2][2]=0, row[2] = row[2](=1, old) + row[1](=1, new) = 2
             row = [1, 1, 2]
    return row[-1] = 2.  MATCHES.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time        Space      Mutates input?
    ---------------------------------  ----------  ---------  --------------
    Brute force DFS (no memo)          O(2^(m+n))  O(m+n)     no
    Memoized top-down, 2D cache        O(m*n)      O(m*n)     no
    Bottom-up tabulation, full table   O(m*n)      O(m*n)     no
    Rolling row [chosen]               O(m*n)      O(n)       no


================================================================================
EDGE CASES
================================================================================
    grid[0][0] == 1 (start blocked)     -> 0 paths exist at all; must be
                                            checked before/at initialization,
                                            not discovered mid-loop.
    grid[m-1][n-1] == 1 (end blocked)   -> falls out naturally: that cell's
                                            dp value is forced to 0 by the
                                            same obstacle rule, no special
                                            case needed.
    An obstacle anywhere in row 0 or   -> every cell after it in that row/
    column 0                              column is permanently unreachable
                                            (only right/down moves exist) --
                                            the rolling-row init must zero
                                            past it, not assume 1s all the way.
    Every cell in the grid is an       -> answer 0; the base case dp[0][0]=1
    obstacle except start==end            only applies when grid[0][0]==0,
    (1x1 grid, single cell, no obst.)     so an all-obstacle single-cell grid
                                            correctly yields 0, an obstacle-
                                            free single-cell grid yields 1.
    1xN or Mx1 grid                     -> straight line; a single obstacle
                                            anywhere on it drops the answer
                                            to 0 immediately.


================================================================================
COMMON MISTAKES
================================================================================
1. Checking `grid[0][0] == 1` for the whole-answer-is-zero case but
   forgetting to also apply the SAME check when initializing dp[0][0]/row[0]
   before the main loop -- leads to `dp[0][0] = 1` sneaking through even
   though the start is blocked, silently double-counting nonexistent paths.

2. Reusing 001's "top row and left column are all 1s" base case verbatim.
   That assumption is false here the instant an obstacle appears anywhere in
   row 0 or column 0 -- everything past the obstacle in that line must be 0,
   not 1, because there is no way to detour around it while confined to a
   single row/column.

3. In the rolling-row version, updating `row[j]` for an obstacle cell using
   the sum formula and THEN separately trying to zero it -- order matters
   only if done sloppily; the cleanest correct form checks the obstacle
   FIRST, and only computes the sum in the else branch, avoiding any moment
   where a stale nonzero value could leak forward into `row[j+1]`'s
   `row[j-1]` read.

4. Mutating the input grid in place to mark visited/obstacle cells (turning
   `1`s into sentinel values) -- unnecessary here and violates the "does not
   mutate input" property that most interviewers expect by default unless
   told otherwise; a separate dp array is one line and avoids the concern.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What changed structurally between this and Unique Paths (001)?
A: The recurrence is unchanged; only the base case and per-cell override
   changed. That's the general 2D-grid-DP lesson: the SHAPE of the
   recurrence rarely changes across variants, but the boundary conditions
   and per-cell overrides do all the real work of adapting to new rules.

Q: Could you solve this with the closed-form combinatorics trick from 001?
A: No -- obstacles break the clean "choose which moves are down" bijection;
   inclusion-exclusion over obstacle positions is possible in principle but
   is strictly more complex than just running the O(m*n) DP, so it's not
   worth it in an interview.

Q: How would you handle a grid too large to fit an O(m*n) table in memory at
   all, e.g. m, n in the millions?
A: The rolling-row trick already caps working memory at O(n) (or O(min(m,n))
   by iterating over whichever dimension is smaller and rolling the other) --
   for genuinely huge grids beyond that, this problem's counting nature (not
   shortest-path) offers no further reduction; you'd need to stream the grid
   row by row from disk rather than materialize it.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 62   Unique Paths (001 -- the un-obstructed base case this extends)
    LC 64   Minimum Path Sum (003 -- same grid-DP shape, min+cost instead of
            sum+count, and obstacles would slot in the same way)
    LC 120  Triangle (same "predecessors sum/min" shape, triangular bounds)
    LC 174  Dungeon Game (grid DP that must be computed BACKWARDS from the
            destination because the recurrence depends on future health)
================================================================================
"""

from typing import List


class Solution:
    def uniquePathsWithObstacles(self, obstacleGrid: List[List[int]]) -> int:
        """✅ Rolling-row DP. O(m*n) time, O(n) space. Does not mutate input."""
        if not obstacleGrid or obstacleGrid[0][0] == 1:
            return 0

        n = len(obstacleGrid[0])
        row = [0] * n
        row[0] = 1

        for i in range(len(obstacleGrid)):
            for j in range(n):
                if obstacleGrid[i][j] == 1:
                    row[j] = 0
                elif j > 0:
                    row[j] += row[j - 1]
                # j == 0 and not an obstacle: row[0] carries over unchanged
                # from the row above (only a "down" move can reach column 0).
        return row[-1]

    def uniquePathsWithObstacles_full_table(self, obstacleGrid: List[List[int]]) -> int:
        """Alternative: full 2D tabulation, O(m*n) time and space."""
        if not obstacleGrid or obstacleGrid[0][0] == 1:
            return 0

        m, n = len(obstacleGrid), len(obstacleGrid[0])
        dp = [[0] * n for _ in range(m)]
        dp[0][0] = 1

        for i in range(m):
            for j in range(n):
                if obstacleGrid[i][j] == 1:
                    dp[i][j] = 0
                    continue
                if i == 0 and j == 0:
                    continue
                above = dp[i - 1][j] if i > 0 else 0
                left = dp[i][j - 1] if j > 0 else 0
                dp[i][j] = above + left
        return dp[m - 1][n - 1]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([[0, 0, 0], [0, 1, 0], [0, 0, 0]], 2),
        ([[0, 1], [0, 0]], 1),
        ([[1]], 0),
        ([[0]], 1),
        ([[1, 0]], 0),
        ([[0], [1], [0]], 0),
        ([[0, 0], [1, 1], [0, 0]], 0),
        ([[0, 0, 0, 0]], 1),
        ([[0], [0], [0], [0]], 1),
    ]

    print("--- correctness: rolling-row vs full-table agree ---")
    for grid, want in cases:
        got_roll = sol.uniquePathsWithObstacles([row[:] for row in grid])
        got_full = sol.uniquePathsWithObstacles_full_table([row[:] for row in grid])
        ok = got_roll == want and got_full == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  grid={grid}  roll={got_roll} "
              f"full={got_full}  (want {want})")

    # --------------------------------------------------------------------
    # RUNTIME DEMO: prove the input grid is never mutated -- a common
    # shortcut for this exact problem is to overwrite obstacleGrid in place
    # as a scratch DP table. Snapshot before/after and diff.
    # --------------------------------------------------------------------
    print("\n--- DEMO: input grid is never mutated ---")
    grid = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
    before = [row[:] for row in grid]
    sol.uniquePathsWithObstacles(grid)
    unmutated = grid == before
    print(f"  grid before: {before}")
    print(f"  grid after:  {grid}")
    print(f"  unchanged: {unmutated}")
    all_ok &= unmutated

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
