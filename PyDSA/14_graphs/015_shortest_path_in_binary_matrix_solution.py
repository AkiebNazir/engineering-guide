"""
================================================================================
SOLUTION · LeetCode 1091 · Shortest Path in Binary Matrix             [Medium]
https://leetcode.com/problems/shortest-path-in-binary-matrix/
================================================================================

THE CORE IDEA
--------------
Unweighted shortest path on a grid is BFS (topic guide Part 2) — the first
time BFS reaches the target cell, that distance is guaranteed minimal. The
one thing that changes from every earlier grid problem in this folder is
the DIRECTIONS list: this problem explicitly allows diagonal movement, so
`DIRECTIONS` needs all 8 neighbor offsets, not the usual 4 (topic guide
§6.2's closing note). Using the familiar 4-directional list here is not
just suboptimal — it can silently turn a real path into a false "no path
exists," because some grids ONLY have a diagonal route between two regions.
This file's runtime demo builds exactly such a grid and proves it.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, don't ship): DFS every possible path from (0,0) to
(n-1,n-1), track the minimum length seen. Correct but exponential — DFS
has no notion of "closest first," so it explores every path to completion
before comparing, instead of stopping at the first (guaranteed shortest)
BFS arrival. Never worth coding for a shortest-path question.

Approach 1 (BFS, 8-directional) ✅ — the answer:
    Guard: if grid[0][0] or grid[n-1][n-1] is 1, return -1 immediately (no
    path can even start/end there). Otherwise BFS from (0,0) with 8-way
    DIRECTIONS, tracking path length (source starts at length 1, since the
    problem counts VISITED CELLS, not edges traversed). First arrival at
    (n-1, n-1) is the answer; empty queue with no arrival means -1.
    O(n^2) time — every cell visited once, each with up to 8 neighbor
    checks — O(n^2) space for the queue/visited set.

Approach 2 (A* / bidirectional BFS) — variants worth naming for a
follow-up: A* with an admissible heuristic (e.g. Chebyshev distance to the
target, which is exactly what 8-directional movement's true lower bound
is) can prune the search in practice, same worst-case O(n^2) but often
faster in the average case. Bidirectional BFS (search from both start and
end, meet in the middle) roughly halves the exponent of the search radius
for random terrain. Neither is coded here — plain BFS already meets this
problem's O(n^2) target and n <= 100 makes the constant-factor gains from
A*/bidirectional BFS unnecessary in an interview setting; naming them shows
awareness without over-engineering the answer.


================================================================================
STEP BY STEP TRACE
================================================================================
grid = [[0,0,0],
        [1,1,0],
        [1,1,0]]

    0  0  0
    1  1  0
    1  1  0

grid[0][0]=0, grid[2][2]=0 -> both endpoints clear, BFS starts.

queue = [(0,0,1)]   (row,col,pathLength)   visited={(0,0)}

Pop (0,0,1): check all 8 neighbors of (0,0) within bounds and value 0:
    (0,1)=0 unvisited -> enqueue (0,1,2)
    (1,0)=1 -> skip (blocked)
    (1,1)=1 -> skip (blocked, this is the diagonal neighbor)
    queue = [(0,1,2)]   visited={(0,0),(0,1)}

Pop (0,1,2): neighbors of (0,1):
    (0,0) visited, skip
    (0,2)=0 unvisited -> enqueue (0,2,3)
    (1,0)=1 skip   (1,1)=1 skip   (1,2)=0 unvisited -> enqueue (1,2,3)
    queue = [(0,2,3), (1,2,3)]   visited += {(0,2),(1,2)}

Pop (0,2,3): neighbors: (0,1) visited, (1,1)=1 skip, (1,2) visited -> nothing new
Pop (1,2,3): neighbors: (0,1) visited, (0,2) visited, (1,1)=1 skip,
             (2,1)=1 skip, (2,2)=0 unvisited -> enqueue (2,2,4)
    queue = [(2,2,4)]

Pop (2,2,4): (2,2) IS the target (n-1,n-1) -> return 4. ✅ matches expected.

    0  0  0        path: (0,0)->(0,1)->(0,2)->(1,2)[diagonal step down-left
    1  1  0                is NOT used here; (0,2)->(1,2) is a straight-down
    1  1  0                orthogonal move]->(2,2)[straight down]
    (this particular shortest path happens to use only orthogonal moves;
    Example 1 in the question docstring is the case where a DIAGONAL move
    is the only way through at all.)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time      Space    Mutates input?  Note
    ------------------------------  --------  -------  --------------  ----------------------------
    Brute-force DFS all paths        O(8^(n^2)) O(n^2)   no             never ship
    BFS, 8-directional ✅            O(n^2)     O(n^2)   no             the answer
    BFS, 4-directional (WRONG here)  O(n^2)     O(n^2)   no             misses valid diagonal-only paths

    "Mutates input?" — no. `visited` is a separate set; `grid` is only
    read. (An in-place variant could overwrite visited 0-cells with a
    sentinel, saving the `visited` set's space, but that mutates the input
    grid — not done here, matching this folder's default per the topic
    guide §6.1 rule of preferring a separate visited set unless the grid is
    provably single-use and mutation is explicitly acceptable.)


================================================================================
EDGE CASES
================================================================================
    grid[0][0] == 1               -> no path can even start; return -1
                                      immediately, don't run BFS at all.
    grid[n-1][n-1] == 1            -> no path can end there; same immediate
                                      -1 (checked alongside the start check).
    1x1 grid, value 0              -> start == target; path length is 1 (the
                                      single cell itself), not 0 — the
                                      problem counts visited cells.
    only a DIAGONAL path exists,   -> the case this file's runtime demo
    no orthogonal path does          constructs and measures directly: with
                                      4-directional DIRECTIONS this returns
                                      -1 incorrectly; 8-directional finds
                                      the true answer.
    grid fully blocked (no path    -> BFS exhausts the queue without ever
    at all between clear start       reaching the target -> return -1. This
    and target)                      is the "genuinely no path" case, not a
                                      directionality bug — distinguished
                                      from the diagonal-only case above by
                                      running BOTH direction sets and
                                      checking whether EITHER succeeds.


================================================================================
COMMON MISTAKES
================================================================================
1. Copy-pasting the 4-directional DIRECTIONS list from every earlier grid
   problem in this folder (001-008, 014) without re-reading THIS problem's
   movement rule. The topic guide flags this exact trap in §6.2. Silent
   wrong answer (-1 instead of a real length), not a crash — the worst kind
   of bug because nothing looks broken.

2. Forgetting the two upfront endpoint checks (`grid[0][0]` and
   `grid[n-1][n-1]` both must be 0) and letting BFS "discover" the failure
   the slow way. Functionally fine (BFS still returns -1 correctly if it
   never enqueues (0,0) in the first place because of an early value check
   inside the loop), but it's cleaner and cheaper to guard explicitly.

3. Off-by-one in path length: starting the source cell's length at 0
   instead of 1. The problem defines length as NUMBER OF CELLS VISITED, so
   a 1x1 grid's answer is 1, not 0, and every subsequent length increments
   from there.

4. Marking `visited` on dequeue instead of enqueue (topic guide mistake
   #2) — with 8 neighbors instead of 4 this bug is worse than usual, since
   diagonal double-enqueuing multiplies the wasted branching factor.

5. Using Chebyshev distance (`max(|dr|,|dc|)`) as a SHORTCUT formula
   instead of actually running BFS, reasoning "diagonal moves cost the same
   as orthogonal, so it's just chebyshev distance." This is only true on an
   OBSTACLE-FREE grid; the moment any cell is blocked (value 1), the
   straight-line Chebyshev distance underestimates the real path length.
   BFS is required precisely because obstacles exist.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why would you ever use 4-directional movement instead of 8?
A: Whenever the problem's movement rule says so — most grid problems in
   this folder (001-008, 014) are strictly orthogonal (island/room/gate
   problems model real 2D physical adjacency, e.g. Manhattan-style city
   blocks). This problem explicitly names diagonal adjacency in the
   statement; always re-derive DIRECTIONS from the problem text, never
   assume.

Q: Could you speed this up with A*?
A: Yes — using Chebyshev distance to the target as an admissible heuristic
   (never overestimates true remaining distance under 8-directional
   movement) keeps A* optimal while typically exploring far fewer cells in
   the average case. Same O(n^2) worst case, but with a priority queue
   instead of a plain BFS queue. Worth naming, not required at n <= 100.

Q: What if diagonal moves cost more than orthogonal ones (e.g. cost
   sqrt(2))?
A: This becomes a WEIGHTED shortest-path problem — plain BFS no longer
   guarantees correctness (BFS assumes all edges cost 1). Dijkstra's
   algorithm (topic 15, Advanced Graphs) would be the right tool.

Q: How would you reconstruct the actual PATH, not just its length?
A: Store a `parent` map during BFS (each newly-enqueued cell records which
   cell enqueued it), then walk backward from the target to the source once
   BFS finds it, and reverse the resulting list.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Pattern: unweighted shortest path via BFS on a grid, with a non-default
adjacency rule.

    LC 542  01 Matrix (014, this folder)         — multi-source BFS, 4-directional
    LC 733  Flood Fill (001, this folder)         — 4-directional, no shortest-path angle
    LC 675  Cut Off Trees for Golf Event          — BFS shortest path repeated per target
    LC 934  Shortest Bridge                        — components + multi-source BFS combined
    LC 127  Word Ladder (016, this folder)         — BFS shortest path, IMPLICIT graph (no grid at all)
================================================================================
"""

import time
from collections import deque
from typing import List


DIRECTIONS_8 = [(-1, -1), (-1, 0), (-1, 1),
                (0, -1),           (0, 1),
                (1, -1),  (1, 0),  (1, 1)]

DIRECTIONS_4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]


class Solution:
    def shortestPathBinaryMatrix(self, grid: List[List[int]]) -> int:
        """✅ THE ANSWER — BFS with 8-directional movement (diagonals count).
        O(n^2) time, O(n^2) space. Does not mutate `grid`."""
        n = len(grid)
        if grid[0][0] != 0 or grid[n - 1][n - 1] != 0:
            return -1
        if n == 1:
            return 1

        visited = {(0, 0)}
        queue = deque([(0, 0, 1)])  # row, col, path length so far

        while queue:
            r, c, length = queue.popleft()
            for dr, dc in DIRECTIONS_8:
                nr, nc = r + dr, c + dc
                if (0 <= nr < n and 0 <= nc < n
                        and grid[nr][nc] == 0 and (nr, nc) not in visited):
                    if nr == n - 1 and nc == n - 1:
                        return length + 1
                    visited.add((nr, nc))
                    queue.append((nr, nc, length + 1))

        return -1

    def shortestPathBinaryMatrix_4directional(self, grid: List[List[int]]) -> int:
        """✗ WRONG FOR THIS PROBLEM, kept for the runtime demo — same BFS
        shape but using only 4-directional DIRECTIONS. Misses paths that
        require a diagonal step. O(n^2) time, O(n^2) space."""
        n = len(grid)
        if grid[0][0] != 0 or grid[n - 1][n - 1] != 0:
            return -1
        if n == 1:
            return 1

        visited = {(0, 0)}
        queue = deque([(0, 0, 1)])

        while queue:
            r, c, length = queue.popleft()
            for dr, dc in DIRECTIONS_4:
                nr, nc = r + dr, c + dc
                if (0 <= nr < n and 0 <= nc < n
                        and grid[nr][nc] == 0 and (nr, nc) not in visited):
                    if nr == n - 1 and nc == n - 1:
                        return length + 1
                    visited.add((nr, nc))
                    queue.append((nr, nc, length + 1))

        return -1


# ==============================================================================
# TESTS
# ==============================================================================
CASES = [
    ([[0, 1], [1, 0]], 2),
    ([[0, 0, 0], [1, 1, 0], [1, 1, 0]], 4),
    ([[1, 0, 0], [1, 1, 0], [1, 1, 0]], -1),
    ([[0]], 1),
    ([[0, 0], [1, 0]], 2),
    ([[1, 0], [0, 0]], -1),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: BFS, 8-directional ---")
    for grid, expected in CASES:
        result = sol.shortestPathBinaryMatrix([row[:] for row in grid])
        ok = result == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  grid={grid!r:<35} "
              f"-> {result} (want {expected})")

    # ----------------------------------------------------------------------
    # Trace, printed live.
    # ----------------------------------------------------------------------
    print("\n--- trace: grid=[[0,0,0],[1,1,0],[1,1,0]] ---")
    grid = [[0, 0, 0], [1, 1, 0], [1, 1, 0]]
    n = 3
    visited = {(0, 0)}
    queue = deque([(0, 0, 1)])
    print(f"  start: queue={list(queue)}")
    while queue:
        r, c, length = queue.popleft()
        found = None
        added = []
        for dr, dc in DIRECTIONS_8:
            nr, nc = r + dr, c + dc
            if (0 <= nr < n and 0 <= nc < n
                    and grid[nr][nc] == 0 and (nr, nc) not in visited):
                if nr == n - 1 and nc == n - 1:
                    found = length + 1
                    break
                visited.add((nr, nc))
                queue.append((nr, nc, length + 1))
                added.append((nr, nc, length + 1))
        print(f"  pop ({r},{c},len={length}) -> enqueue {added}")
        if found is not None:
            print(f"  reached target -> return {found}")
            break

    # ----------------------------------------------------------------------
    # ⚠️ RUNTIME DEMO: a grid where ONLY a diagonal path exists.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  DEMO: 4-directional DIRECTIONS misses a real diagonal-only path ---")
    # Build a grid where the only route from corner to corner is a chain of
    # pure diagonal steps, with the orthogonal cells around each diagonal
    # step deliberately blocked.
    diag_grid = [
        [0, 1, 1, 1, 1],
        [1, 0, 1, 1, 1],
        [1, 1, 0, 1, 1],
        [1, 1, 1, 0, 1],
        [1, 1, 1, 1, 0],
    ]
    print("  grid (0=open, 1=blocked) — only the main diagonal is open:")
    for row in diag_grid:
        print("   ", row)

    result_8dir = sol.shortestPathBinaryMatrix([row[:] for row in diag_grid])
    result_4dir = sol.shortestPathBinaryMatrix_4directional([row[:] for row in diag_grid])
    print(f"  8-directional BFS result: {result_8dir}")
    print(f"  4-directional BFS result: {result_4dir}")
    diag_proof = result_8dir == 5 and result_4dir == -1
    print(f"  8-dir finds the real path (length 5, straight down the diagonal) "
          f"while 4-dir wrongly reports NO path (-1): {diag_proof}")
    all_ok &= diag_proof

    # ----------------------------------------------------------------------
    # Timing note: both directional variants are the same asymptotic cost;
    # the point of this problem is CORRECTNESS of the direction set, not
    # speed, so we measure wall-clock only to show 8-dir isn't materially
    # slower despite checking twice as many neighbors per cell.
    # ----------------------------------------------------------------------
    print("\n--- timing: 8-directional vs 4-directional on a larger open grid ---")
    n = 80
    open_grid = [[0] * n for _ in range(n)]
    t0 = time.perf_counter()
    sol.shortestPathBinaryMatrix([row[:] for row in open_grid])
    t1 = time.perf_counter()
    t2 = time.perf_counter()
    sol.shortestPathBinaryMatrix_4directional([row[:] for row in open_grid])
    t3 = time.perf_counter()
    ms8, ms4 = (t1 - t0) * 1000, (t3 - t2) * 1000
    print(f"  n={n} fully open grid: 8-dir {ms8:.2f} ms, 4-dir {ms4:.2f} ms "
          f"(8-dir checks 2x the neighbors per cell but both stay O(n^2))")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
