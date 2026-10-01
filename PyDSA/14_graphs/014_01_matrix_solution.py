"""
================================================================================
SOLUTION · LeetCode 542 · 01 Matrix                                  [Medium]
https://leetcode.com/problems/01-matrix/
================================================================================

THE CORE IDEA
--------------
Flip the direction of the search. Instead of asking, for each 1-cell, "walk
outward until I hit a 0" (one BFS per 1-cell), start a SINGLE BFS from EVERY
0-cell simultaneously (topic guide §6.3, multi-source BFS — the same pattern
Walls and Gates, 005, and Rotting Oranges, 006, use). Seed the queue with
every 0-cell at distance 0, then expand outward one ring at a time. Because
BFS explores in strictly increasing distance order, the FIRST time the wave
reaches a given 1-cell, that distance IS its distance to the nearest 0 —
"nearest" falls out of BFS order for free, no need to compare against every
0 individually.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, don't ship): for every 1-cell, run a fresh BFS (or
even scan every 0-cell and take min Manhattan-ish grid distance — but grid
distance with obstacles-free movement is just BFS) to find its nearest 0.
O(ones * cells) — this file's runtime demo builds this literally and times
it against Approach 1 on the same grid.

Approach 1 (multi-source BFS) ✅ — the answer:
    Seed a queue with every (r, c) where mat[r][c] == 0, distance 0, mark
    all of them visited. Standard 4-directional grid BFS from there
    (topic guide §6.2): pop, look at neighbors, if unvisited set
    dist = current + 1, enqueue. O(rows * cols) time — every cell enqueued
    and processed exactly once — O(rows * cols) space for the queue/answer.

Approach 2 (DP, two passes) — variant worth knowing: since distance to the
nearest 0 can only come from a cell already closer (up/left on the first
pass, down/right on the second), do one pass top-left -> bottom-right
taking `min(cell, up+1, left+1)`, then bottom-right -> top-left taking
`min(cell, down+1, right+1)`. Same O(rows*cols) time, O(1) EXTRA space if
allowed to mutate `mat` in place (BFS needs an explicit visited structure
or a distance grid; DP can reuse `mat` itself as the answer grid). Doesn't
generalize as cleanly to 8-directional or weighted variants, which is why
BFS is the more broadly reusable tool to reach for first.


================================================================================
STEP BY STEP TRACE
================================================================================
mat = [[0,0,0],
       [0,1,0],
       [1,1,1]]

Seed: every 0-cell enters the queue at distance 0.
    0  0  0
    0  .  0        (.) = the only 1-cell not yet a source
    1  1  1

queue = [(0,0,0), (0,1,0), (0,2,0), (1,0,0), (1,2,0)]   (row,col,dist)
visited = {(0,0),(0,1),(0,2),(1,0),(1,2)}
dist grid so far:
    0  0  0
    0  ?  0
    ?  ?  ?

Wave 1 (all dist-0 cells popped, each looks at its 4 neighbors):
  (0,0) -> neighbor (1,0) already visited (it's a source itself), skip
  (0,1) -> neighbor (1,1) unvisited -> dist=1, enqueue
  (0,2) -> neighbor (1,2) already visited (source), skip
  (1,0) -> neighbor (2,0) unvisited -> dist=1, enqueue
  (1,2) -> neighbor (2,2) unvisited -> dist=1, enqueue

    0  0  0
    0  1  0
    1  ?  1

Wave 2 (the dist-1 cells: (1,1),(2,0),(2,2)):
  (1,1) -> neighbor (2,1) unvisited -> dist = 1+1 = 2, enqueue
  (2,0) -> neighbor (2,1) already claimed this same wave (or about to be) —
           whichever pops first sets it; both would compute dist=2 anyway
  (2,2) -> neighbor (2,1) same story

    0  0  0
    0  1  0
    1  2  1

Queue empties. Final:
    [[0,0,0],
     [0,1,0],
     [1,2,1]]   <- matches the expected output exactly.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time              Space    Mutates input?  Note
    ---------------------------------  ----------------  -------  --------------  --------------------------
    Naive: BFS from every 1-cell        O(ones * cells)   O(cells) no              catastrophic on sparse 0s
    Multi-source BFS ✅                 O(rows*cols)       O(rows*cols) no          answer, this file
    Two-pass DP                        O(rows*cols)       O(1) extra* no*          *if allowed to write into mat

    "Mutates input?" — the BFS solution here builds a SEPARATE answer
    matrix and a `visited` set; `mat` itself is only read. The two-pass DP
    variant (mentioned, not the primary answer) CAN write distances
    directly into `mat` for O(1) extra space, but that mutates the input,
    which is a tradeoff worth naming explicitly if the interviewer asks
    for the O(1)-extra-space version.


================================================================================
EDGE CASES
================================================================================
    grid is all 0s              -> every cell's answer is 0; multi-source BFS
                                    never even needs to expand — every cell is
                                    itself a source.
    grid has exactly one 0       -> equivalent to ordinary single-source BFS;
                                    multi-source degenerates gracefully to the
                                    single-source case with no special-casing.
    1x1 grid, value 0            -> trivial, answer [[0]]. Guaranteed to have
                                    at least one 0 per constraints, so a 1x1
                                    grid of [[1]] is not legal input.
    a 1-cell surrounded on all    -> BFS still reaches it, just at a higher
    sides by other 1s              distance — grid connectivity through 0s or
                                    1s doesn't matter, EVERY cell is reachable
                                    from SOME 0 because the grid is finite and
                                    fully connected via 4-directional adjacency
                                    (no walls block movement in this problem,
                                    unlike a maze).
    very large grid (up to 10^4   -> multi-source BFS's O(cells) bound matters
    cells)                          here specifically — this is why the naive
                                    "BFS from every 1" approach is a genuine
                                    trap at this problem's stated scale.


================================================================================
COMMON MISTAKES
================================================================================
1. Running BFS once per 1-cell ("obviously correct, just find the nearest
   0") instead of seeding one BFS with ALL 0-cells at once. Both are
   correct; only the multi-source version meets the problem's implicit
   scale expectations. See the runtime demo below for the actual measured
   cost of getting this wrong.

2. Marking `visited` on DEQUEUE instead of ENQUEUE (topic guide mistake
   #2) — lets the same cell get pushed onto the queue multiple times before
   its true nearest-0 distance is settled, corrupting the distance
   computation, not just wasting time.

3. Forgetting to seed ALL zero cells before the first pop — seeding only
   the first 0-cell found and treating the rest as ordinary 1-cells that
   happen to have value 0 breaks the "distance 0 for every 0-cell"
   invariant the problem requires.

4. Trying to use Manhattan distance (`|r1-r2| + |c1-c2|`) directly instead
   of BFS. This happens to be CORRECT for this specific problem (no
   obstacles block movement — every cell is freely reachable from every
   other), but it's a coincidence of this problem's lack of obstacles, not
   a generalizable technique; the moment obstacles could block a path
   (compare problem 015, or a maze variant), only BFS gives the right
   answer. Don't build the habit of reaching for the formula.

5. Off-by-one on distance: forgetting the source 0-cells start at distance
   0 (not 1), so the first neighbor ring is distance 1, not 0.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if some cells were also "walls" that block movement entirely
   (neither 0 nor reachable 1)?
A: Add a third grid value and skip it as a neighbor entirely during BFS
   expansion — same multi-source BFS shape, just a stricter neighbor
   filter, same O(cells) bound as long as the wall count doesn't change the
   total cell count being visited.

Q: Could you solve this with the two-pass DP variant for O(1) extra space?
A: Yes (Approach 2) — but it mutates `mat` in place, trading input
   preservation for space. State that tradeoff explicitly rather than
   silently picking one.

Q: How does this differ from Walls and Gates (005) in this folder?
A: Nearly identical mechanism — multi-source BFS from every "source" cell
   (there: gates: value 0; here: zero-cells). 005 writes distance in place
   (source is single-use, mutation is fine per the topic guide §6.1 rule);
   here the solution returns a NEW matrix instead, since returning the
   answer (not mutating and returning None) is what the signature asks for.

Q: What if the grid were 8-directionally connected instead of 4?
A: Extend DIRECTIONS to the 8-neighbor set (see problem 015's DIRECTIONS)
   — same BFS mechanism, still O(cells) time, marginally larger constant
   factor per cell (8 neighbor checks instead of 4).


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Pattern: multi-source BFS on a grid (topic guide §6.3).

    LC 286  Walls and Gates (005, this folder)     — the direct sibling, in-place
    LC 994  Rotting Oranges (006, this folder)     — same pattern, "minutes" = BFS depth
    LC 1162 As Far from Land as Possible            — same shape, maximize instead of read-off
    LC 934  Shortest Bridge                          — connected components + multi-source BFS combined
    LC 1091 Shortest Path in Binary Matrix (015)    — single-source BFS, 8-directional
================================================================================
"""

import random
import time
from collections import deque
from typing import List


DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # up, down, left, right


class Solution:
    def updateMatrix(self, mat: List[List[int]]) -> List[List[int]]:
        """✅ THE ANSWER — multi-source BFS, seeded with every 0-cell at once.
        O(rows * cols) time, O(rows * cols) space. Does not mutate `mat`."""
        rows, cols = len(mat), len(mat[0])
        dist = [[-1] * cols for _ in range(rows)]
        queue = deque()

        for r in range(rows):
            for c in range(cols):
                if mat[r][c] == 0:
                    dist[r][c] = 0
                    queue.append((r, c))

        while queue:
            r, c = queue.popleft()
            for dr, dc in DIRECTIONS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and dist[nr][nc] == -1:
                    dist[nr][nc] = dist[r][c] + 1
                    queue.append((nr, nc))

        return dist

    def updateMatrix_naive_per_cell_bfs(self, mat: List[List[int]]) -> List[List[int]]:
        """✗ SLOW ON PURPOSE, for the runtime demo — single-source BFS from
        EVERY 1-cell to find its own nearest 0. Correct, but O(ones * cells)
        instead of O(cells). Does not mutate `mat`."""
        rows, cols = len(mat), len(mat[0])
        result = [[0] * cols for _ in range(rows)]

        for sr in range(rows):
            for sc in range(cols):
                if mat[sr][sc] == 0:
                    result[sr][sc] = 0
                    continue
                visited = {(sr, sc)}
                queue = deque([(sr, sc, 0)])
                found = 0
                while queue:
                    r, c, d = queue.popleft()
                    if mat[r][c] == 0:
                        found = d
                        break
                    for dr, dc in DIRECTIONS:
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < rows and 0 <= nc < cols
                                and (nr, nc) not in visited):
                            visited.add((nr, nc))
                            queue.append((nr, nc, d + 1))
                result[sr][sc] = found

        return result


# ==============================================================================
# TESTS
# ==============================================================================
CASES = [
    ([[0, 0, 0], [0, 1, 0], [0, 0, 0]], [[0, 0, 0], [0, 1, 0], [0, 0, 0]]),
    ([[0, 0, 0], [0, 1, 0], [1, 1, 1]], [[0, 0, 0], [0, 1, 0], [1, 2, 1]]),
    ([[0]], [[0]]),
    ([[1, 1, 1], [1, 1, 1], [1, 1, 0]], [[4, 3, 2], [3, 2, 1], [2, 1, 0]]),
    ([[0, 1], [1, 1]], [[0, 1], [1, 2]]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: multi-source BFS ---")
    for mat, expected in CASES:
        result = sol.updateMatrix([row[:] for row in mat])
        ok = result == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  mat={mat!r:<40} "
              f"-> {result} (want {expected})")

    print("\n--- multi-source BFS agrees with naive per-cell BFS ---")
    for mat, expected in CASES:
        a = sol.updateMatrix([row[:] for row in mat])
        b = sol.updateMatrix_naive_per_cell_bfs([row[:] for row in mat])
        ok = a == b == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  fast={a} naive={b}")

    # ----------------------------------------------------------------------
    # Trace, printed live.
    # ----------------------------------------------------------------------
    print("\n--- trace: mat=[[0,0,0],[0,1,0],[1,1,1]] ---")
    mat = [[0, 0, 0], [0, 1, 0], [1, 1, 1]]
    rows, cols = 3, 3
    dist = [[-1] * cols for _ in range(rows)]
    queue = deque()
    for r in range(rows):
        for c in range(cols):
            if mat[r][c] == 0:
                dist[r][c] = 0
                queue.append((r, c))
    print(f"  sources seeded: {list(queue)}")
    wave = 0
    while queue:
        wave += 1
        wave_size = len(queue)
        for _ in range(wave_size):
            r, c = queue.popleft()
            for dr, dc in DIRECTIONS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and dist[nr][nc] == -1:
                    dist[nr][nc] = dist[r][c] + 1
                    queue.append((nr, nc))
        print(f"  after wave {wave}: dist grid = {dist}")
    print(f"  final: {dist}")

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: multi-source BFS vs naive-per-cell BFS on a real grid.
    # ----------------------------------------------------------------------
    print("\n--- DEMO: multi-source BFS vs BFS-from-every-1-cell, measured ---")
    random.seed(542)
    size = 60  # 60x60 = 3600 cells, sparse zeros (mirrors this problem's trap)
    grid = [[1] * size for _ in range(size)]
    # sprinkle a small number of 0s so most cells are 1s needing a real search
    zero_count = 0
    for r in range(size):
        for c in range(size):
            if random.random() < 0.01:
                grid[r][c] = 0
                zero_count += 1
    if zero_count == 0:  # guarantee at least one 0 exists
        grid[0][0] = 0
        zero_count = 1
    ones_count = size * size - zero_count
    print(f"  grid {size}x{size} = {size*size} cells, {zero_count} zero-cells, "
          f"{ones_count} one-cells")

    t0 = time.perf_counter()
    fast_result = sol.updateMatrix([row[:] for row in grid])
    t1 = time.perf_counter()
    fast_ms = (t1 - t0) * 1000

    t2 = time.perf_counter()
    naive_result = sol.updateMatrix_naive_per_cell_bfs([row[:] for row in grid])
    t3 = time.perf_counter()
    naive_ms = (t3 - t2) * 1000

    same = fast_result == naive_result
    speedup = naive_ms / fast_ms if fast_ms > 0 else float("inf")
    print(f"  multi-source BFS:      {fast_ms:>9.2f} ms")
    print(f"  naive BFS-per-1-cell:  {naive_ms:>9.2f} ms")
    print(f"  measured speedup:      {speedup:>9.1f}x")
    print(f"  both approaches agree on every cell: {same}")
    print("  Naive re-walks a large chunk of the grid from EVERY 1-cell "
          "independently (O(ones*cells)); multi-source BFS walks the whole "
          "grid exactly once (O(cells)) because all 0-cells share one wavefront.")
    all_ok &= same and speedup > 1.0

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
