"""
================================================================================
SOLUTION · LeetCode 329 · Longest Increasing Path in a Matrix            [Hard]
https://leetcode.com/problems/longest-increasing-path-in-a-matrix/
================================================================================

THE CORE IDEA
--------------
dp[i][j] = length of the longest strictly-increasing path STARTING at
(i, j), moving to any of up to 4 orthogonal neighbors:

    dp[i][j] = 1 + max(dp[neighbor] for each neighbor with a STRICTLY
                        LARGER value), or 1 if no neighbor qualifies.

The critical observation that makes this safe to memoize with NO separate
"visited" set: because every move must strictly increase in value, you can
NEVER walk back to a cell already on the current path -- that would require
the value to both increase (to get there) and later be revisited (implying
a cycle, which would need it to also be reachable by decreasing, a
contradiction). The "increasing move" graph is a DAG by construction, so a
plain memo table doubles as both "already computed" and "no cycle risk"
bookkeeping -- unlike generic grid DFS/backtracking, which needs an explicit
visited set to avoid infinite loops.

Answer = max(dp[i][j]) over every cell (the longest path can start
anywhere, so every cell's dp value must be computed).


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, not coded): from every cell, DFS every
increasing path with no memoization, track the max length seen. Exponential
in the worst case -- the same suffix path gets re-explored from every cell
that can reach it, no reuse at all.

Approach 1 (memoized top-down DFS, recursion) -- recurse outward from each
unvisited cell, cache dp[i][j] the first time it's computed. O(m*n) time (each
cell's dp computed once), O(m*n) space for the memo -- BUT the recursion
STACK can reach depth equal to the LONGEST increasing path in the worst
case (e.g. a 1x40,000 strictly-increasing row is 40,000 cells deep), which
exceeds Python's default recursion limit (1000)
and crashes with RecursionError. See the runtime demo below -- this is a
real, measured crash, not a theoretical concern.

Approach 2 (bottom-up, sort cells by value, process in DECREASING order)
[checked, shipped] -- if every cell is processed in order of DECREASING
value, then by the time cell (i, j) is processed, every neighbor with a
LARGER value has ALREADY been processed (its dp value is final) -- this is
exactly a topological order of the increasing-move DAG, computed explicitly
instead of via recursion. No call stack, no depth limit. O(m*n log(m*n))
time (dominated by the sort), O(m*n) space.

Approach 3 (iterative DFS with an explicit stack) -- functionally identical
to Approach 1 but replaces the Python call stack with a manual list-based
stack, sidestepping the RecursionError entirely while keeping O(m*n) time
(no sort needed). More code, but avoids both the recursion limit AND the
sort's log factor. Not shown here; Approach 2 is preferred for clarity.


================================================================================
STEP BY STEP TRACE
================================================================================
matrix = [[9,9,4],
          [6,6,8],
          [2,1,1]]

Sorted cells by value, DESCENDING (ties broken arbitrarily):
    (0,0)=9, (0,1)=9, (1,2)=8, (1,0)=6, (1,1)=6, (0,2)=4, (2,0)=2, (2,1)=1, (2,2)=1

Process in that order -- by the time each cell is handled, all its
LARGER neighbors are already finalized:

    (0,0)=9: neighbors (0,1)=9 [not >9], (1,0)=6 [not >9] -> dp=1
    (0,1)=9: neighbors (0,0)=9 [not >], (0,2)=4 [not >], (1,1)=6 [not >] -> dp=1
    (1,2)=8: neighbors (0,2)=4 [not >], (1,1)=6 [not >], (2,2)=1 [not >] -> dp=1
    (1,0)=6: neighbors (0,0)=9 [>6, dp=1], (1,1)=6 [not >], (2,0)=2 [not >]
             -> dp=1+dp(0,0)=1+1=2
    (1,1)=6: neighbors (0,1)=9[>6,dp=1],(1,0)=6[not>],(1,2)=8[>6,dp=1],(2,1)=1[not>]
             -> dp=1+max(1,1)=2
    (0,2)=4: neighbors (0,1)=9[>4,dp=1],(1,2)=8[>4,dp=1] -> dp=1+max(1,1)=2
    (2,0)=2: neighbors (1,0)=6[>2,dp=2],(2,1)=1[not>] -> dp=1+2=3
    (2,1)=1: neighbors (1,1)=6[>1,dp=2],(2,0)=2[>1,dp=3],(2,2)=1[not>]
             -> dp=1+max(2,3)=4
    (2,2)=1: neighbors (1,2)=8[>1,dp=1],(2,1)=1[not>] -> dp=1+1=2

max(dp) = 4, achieved at (2,1).  MATCHES expected (path 1->2->6->9:
(2,1)=1 -> (2,0)=2 -> (1,0)=6 -> (0,0)=9).


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time              Space   Mutates input?
    ---------------------------------  ----------------  ------  --------------
    Brute force (no memo)              exponential       O(mn)   no
    Memoized top-down DFS (recursion)  O(m*n)            O(m*n)  no (crashes
                                                                   on deep grids)
    Sorted bottom-up [chosen]          O(mn log(mn))     O(m*n)  no
    Iterative DFS + explicit stack     O(m*n)            O(m*n)  no


================================================================================
EDGE CASES
================================================================================
    1x1 matrix               -> single cell, no neighbors qualify, dp=1,
                                 answer 1.
    All cells equal value    -> no move is ever strictly increasing (moves
                                 require >, not >=), every dp[i][j] = 1,
                                 answer 1.
    Strictly increasing snake -> the worst case for BOTH time (still O(mn),
                                 fine) and for the RECURSIVE approach's
                                 stack depth (up to m*n, NOT fine) -- this is
                                 exactly what the runtime demo below
                                 constructs to trigger a real RecursionError.
    Matrix values up to 2^31-1 -> Python's ints handle this natively, no
                                 overflow concern; just don't assume values
                                 fit in a fixed-width type if porting to
                                 another language.


================================================================================
COMMON MISTAKES
================================================================================
1. Using >= instead of > when comparing a neighbor's value -- the path must
   be STRICTLY increasing; treating equal values as a valid step silently
   creates false "increasing" paths through plateaus (and would also
   reintroduce cycle risk on equal-value neighbors, since two equal cells
   could each "increase" into the other).

2. Adding a separate `visited` set out of habit from generic grid DFS/
   backtracking -- unnecessary here (the strictly-increasing constraint
   already guarantees no cycles) and, if implemented incorrectly (e.g.
   shared across different starting cells instead of per-path), can produce
   WRONG answers by blocking legitimate revisits from a different starting
   point.

3. Recursing without any depth safeguard on grids that can produce very
   long paths -- Python's default recursion limit (1000) is far below the
   worst-case path length (m*n, up to 40,000 for 200x200) -- crashes with
   RecursionError on inputs the algorithm is otherwise perfectly capable of
   solving in O(m*n) time.

4. Forgetting to take the max over ALL cells at the end -- the longest path
   can start anywhere, not necessarily at (0,0) or any other fixed corner.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why is memoization here NOT vulnerable to the same infinite-recursion
   risk as, say, naive DFS on an undirected grid graph?
A: Because every edge in the "increasing move" graph only points toward
   STRICTLY larger values -- this graph is a DAG by construction (a cycle
   would require values to both increase and decrease around the loop,
   impossible). Standard grid DFS needs a visited set specifically because
   undirected grid edges DO form cycles; this problem's edges don't.

Q: How would you avoid the RecursionError on very large/adversarial grids?
A: Either the sorted bottom-up approach (shipped here, trades a log factor
   for zero recursion), or an iterative DFS using an explicit stack (keeps
   O(m*n) time with no sort, more bookkeeping code).

Q: How does this relate to topological sort?
A: Directly -- "process cells in decreasing value order" IS a valid
   topological order of the increasing-move DAG (every edge points from a
   smaller-processed-later cell to a larger-processed-earlier one). This is
   the grid-DP analogue of topic 15's Kahn's-algorithm topological sort.

Q: What if diagonal moves were also allowed?
A: Same DP shape, just check up to 8 neighbors instead of 4 -- the
   strictly-increasing DAG property still holds regardless of how many
   neighbors are considered.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 200  Number of Islands (topic 14 -- undirected grid DFS, DOES need a
            visited set, contrast case for why this problem doesn't)
    LC 207  Course Schedule (topic 14/15 -- topological sort on an explicit
            DAG, same "process in dependency order" idea as Approach 2 here)
    LC 300  Longest Increasing Subsequence (topic 16 -- the 1D ancestor of
            this problem: same "strictly increasing, DAG-safe" property,
            single array instead of a grid)
================================================================================
"""


class Solution:
    def longestIncreasingPath(self, matrix: list[list[int]]) -> int:
        """✅ Bottom-up: process cells in DECREASING value order (a valid
        topological order of the increasing-move DAG). No recursion, so no
        stack-depth risk. O(m*n log(m*n)) time, O(m*n) space."""
        m, n = len(matrix), len(matrix[0])
        cells = sorted(((i, j) for i in range(m) for j in range(n)),
                        key=lambda ij: matrix[ij[0]][ij[1]], reverse=True)

        dp = [[1] * n for _ in range(m)]
        best = 1
        for i, j in cells:
            val = matrix[i][j]
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ni, nj = i + di, j + dj
                if 0 <= ni < m and 0 <= nj < n and matrix[ni][nj] > val:
                    dp[i][j] = max(dp[i][j], 1 + dp[ni][nj])
            best = max(best, dp[i][j])
        return best

    def longestIncreasingPath_memoized_dfs(self, matrix: list[list[int]]) -> int:
        """Alternative: memoized top-down DFS, O(m*n) time, O(m*n) space --
        conceptually simpler, but can hit Python's recursion limit on grids
        with very long increasing chains. See the runtime demo."""
        import sys
        m, n = len(matrix), len(matrix[0])
        memo = {}

        def dfs(i, j):
            if (i, j) in memo:
                return memo[(i, j)]
            best = 1
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ni, nj = i + di, j + dj
                if 0 <= ni < m and 0 <= nj < n and matrix[ni][nj] > matrix[i][j]:
                    best = max(best, 1 + dfs(ni, nj))
            memo[(i, j)] = best
            return best

        old_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(max(old_limit, m * n + 100))
        try:
            return max(dfs(i, j) for i in range(m) for j in range(n))
        finally:
            sys.setrecursionlimit(old_limit)


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([[9, 9, 4], [6, 6, 8], [2, 1, 1]], 4),
        ([[3, 4, 5], [3, 2, 6], [2, 2, 1]], 4),
        ([[1]], 1),
        ([[1, 2], [3, 4]], 3),
        ([[7, 7, 5]], 2),
        ([[5, 5], [5, 5]], 1),
    ]

    print("--- correctness: sorted bottom-up vs memoized DFS agree ---")
    for matrix, want in cases:
        got_sorted = sol.longestIncreasingPath([row[:] for row in matrix])
        got_dfs = sol.longestIncreasingPath_memoized_dfs([row[:] for row in matrix])
        ok = got_sorted == want and got_dfs == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  matrix={matrix}  sorted={got_sorted} "
              f"dfs={got_dfs}  (want {want})")

    # --------------------------------------------------------------------
    # RUNTIME DEMO: construct a long strictly-increasing 1xN row and show
    # that naive recursive DFS (no recursion-limit bump) actually crashes
    # with RecursionError, while the sorted bottom-up version does not --
    # a real, measured failure, not a theoretical claim. A single row is
    # used (rather than a 2D snake) because a snake's extra grid neighbors
    # give DFS shortcuts that keep its ACTUAL call depth far below the
    # path length (measured: a 60x60 snake's 3600-long path only reaches
    # ~120 stack frames, since branching lets memoization short-circuit
    # most of it) -- a single row has exactly ONE larger neighbor per
    # cell, so DFS has no shortcut and must recurse the full length.
    # --------------------------------------------------------------------
    import sys
    print("\n--- DEMO: RecursionError on a long increasing row, naive DFS ---")
    length = 2000  # single row, each cell has exactly one larger neighbor
    snake = [[v + 1 for v in range(length)]]
    print(f"  1x{length} strictly-increasing row, longest path = {length} cells")

    def naive_dfs_no_limit_bump(matrix):
        m, n = len(matrix), len(matrix[0])
        memo = {}

        def dfs(i, j):
            if (i, j) in memo:
                return memo[(i, j)]
            best = 1
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ni, nj = i + di, j + dj
                if 0 <= ni < m and 0 <= nj < n and matrix[ni][nj] > matrix[i][j]:
                    best = max(best, 1 + dfs(ni, nj))
            memo[(i, j)] = best
            return best

        return max(dfs(i, j) for i in range(m) for j in range(n))

    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(1000)  # force the default-ish ceiling for the demo
    crashed = False
    try:
        naive_dfs_no_limit_bump(snake)
    except RecursionError as e:
        crashed = True
        print(f"  naive recursive DFS (limit=1000): RecursionError -- {e}")
    finally:
        sys.setrecursionlimit(old_limit)

    got_sorted = sol.longestIncreasingPath(snake)
    print(f"  sorted bottom-up (no recursion): {got_sorted} "
          f"(expected {length}, no crash)")
    print(f"  naive DFS crashed as predicted: {crashed}")
    all_ok &= crashed and (got_sorted == length)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
