"""
================================================================================
SOLUTION · LeetCode 994 · Rotting Oranges                          [Medium]
https://leetcode.com/problems/rotting-oranges/
================================================================================

THE CORE IDEA
--------------
Every rotten orange at minute 0 spreads to its fresh neighbors SIMULTANEOUSLY,
minute by minute — that is exactly multi-source BFS's wave structure (topic
guide §6.3). Seed the BFS queue with EVERY rotten orange up front (all at
"minute 0"), then process the queue one full LEVEL at a time: draining
everything currently in the queue before advancing the minute counter turns
"BFS depth" directly into "minutes elapsed." The answer is the number of
levels processed, or -1 if a fresh orange survives the whole BFS (it was
never reachable from any rotten cell).


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, don't ship): simulate minute by minute with a full
grid scan each minute — scan all `rows*cols` cells, rot any fresh cell
adjacent to a rotten one, repeat until a scan changes nothing. Each minute
costs O(rows*cols), and the number of minutes can itself be O(rows*cols) in
the worst case (a long snake-shaped path of oranges), giving O((rows*cols)^2)
total. Also awkward to tell "no more changes possible" from "converged."

Approach 1 (single-source BFS per rotten orange, then take the min minute
per fresh cell) — CORRECT but wasteful, same shape as 005's Approach 1: run
one full BFS from each rotten orange, track the arrival minute per cell,
then take the min across all runs. O(rotten_count * rows * cols). Priced and
benchmarked below.

Approach 2 (multi-source BFS, level by level) ✅ — the answer. Seed the queue
with every rotten orange, then process the queue in waves; each wave is one
minute. O(rows * cols) time, O(rows * cols) space.

    from collections import deque

    def orangesRotting(grid):
        rows, cols = len(grid), len(grid[0])
        queue = deque()
        fresh = 0
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == 2:
                    queue.append((r, c))
                elif grid[r][c] == 1:
                    fresh += 1

        if fresh == 0:
            return 0

        DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        minutes = 0
        while queue and fresh > 0:
            minutes += 1
            for _ in range(len(queue)):          # drain exactly this level
                r, c = queue.popleft()
                for dr, dc in DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
                        grid[nr][nc] = 2
                        fresh -= 1
                        queue.append((nr, nc))

        return minutes if fresh == 0 else -1


================================================================================
STEP BY STEP TRACE
================================================================================
grid =
    2 1 1
    1 1 0
    0 1 1

Seed: rotten = [(0,0)], fresh = 6 (count the 1s: (0,1),(0,2),(1,0),(1,1),(2,1),(2,2))

  2 1 1
  1 1 0
  0 1 1        queue=[(0,0)]  fresh=6  minutes=0

minute 1: drain level (just (0,0))
    (0,0)=2 -> neighbors (0,1)=1 rot->2, (1,0)=1 rot->2
    2 2 1
    2 1 0
    0 1 1        queue=[(0,1),(1,0)]  fresh=4

minute 2: drain level ((0,1),(1,0))
    (0,1)=2 -> (0,2)=1 rot->2, (1,1)=1 rot->2
    (1,0)=2 -> (1,1) already rotting this level (skip, already 2)
    2 2 2
    2 2 0
    0 1 1        queue=[(0,2),(1,1)]  fresh=2

minute 3: drain level ((0,2),(1,1))
    (0,2)=2 -> no fresh neighbors
    (1,1)=2 -> (2,1)=1 rot->2
    2 2 2
    2 2 0
    0 2 1        queue=[(2,1)]  fresh=1

minute 4: drain level ((2,1))
    (2,1)=2 -> (2,2)=1 rot->2
    2 2 2
    2 2 0
    0 2 2        queue=[(2,2)]  fresh=0

queue not empty but fresh==0 -> loop condition `while queue and fresh > 0`
stops here. minutes=4, fresh==0 -> return 4. Matches Example 1.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time                  Space    Mutates input?
    -------------------------------   -------------------   -------  --------------
    Brute force (rescan each minute)  O((R*C)^2)             O(1)     YES, in place
    Single-source BFS per rotten +min O(rotten * R*C)         O(R*C)   YES, in place
    Multi-source BFS, level by level ✅ O(R*C)                 O(R*C)   YES, in place

    "Mutates input?" is YES for the primary approach (it rots oranges in the
    grid as it goes, matching LC's expectations); the per-source variant
    below is written to leave the ORIGINAL grid untouched and compute minutes
    into a separate array, since it must compare several independent runs
    against the same starting grid.


================================================================================
EDGE CASES
================================================================================
    no fresh oranges at all      -> answer is 0 immediately; skip BFS
                                     entirely (an empty grid or all-0/2 grid).
    no rotten oranges, fresh>0   -> nothing can ever rot -> -1. The seed
                                     queue is empty and the while-loop body
                                     never runs, so fresh stays > 0.
    a fresh orange fully isolated (surrounded by empty cells / walls-by-
    absence) -> impossible to reach -> -1, exactly Example 2.
    1x1 grid                     -> [[0]] -> 0 (no oranges), [[1]] -> -1
                                     (isolated fresh, no source), [[2]] -> 0
                                     (already fully rotten).
    grid where the LAST minute rots nothing new but the queue still has
    leftover already-rotten neighbors -> the `while queue and fresh > 0`
    guard (or checking fresh==0 before incrementing minutes) stops one
    level early — otherwise you off-by-one the answer by counting a wasted
    final minute where nothing actually changed.


================================================================================
COMMON MISTAKES
================================================================================
1. Incrementing `minutes` unconditionally every BFS iteration instead of
   only per LEVEL — processing one cell at a time (not the whole current
   queue length) turns "minutes elapsed" into "cells processed," which is
   wrong the moment more than one orange rots in the same wave.
2. Incrementing `minutes` even on the final drained level when nothing new
   rotted (off-by-one) — guard with `fresh > 0` before starting a new level,
   or only count a level if it actually rotted something.
3. Forgetting to count `fresh` up front and instead checking "any 1 left in
   the grid" via a full re-scan after BFS — works, but costs an extra
   O(rows*cols) pass; tracking a running counter during the seed scan is
   free and immediate.
4. Not distinguishing "queue empty because everything's done" from "queue
   empty because fresh oranges are unreachable" — both drain the queue to
   empty; only the leftover `fresh > 0` check tells them apart.
5. Single-source BFS looped once per rotten orange (Approach 1) instead of
   seeding all rotten oranges into ONE queue (§6.3) — correct, but does
   redundant work proportional to the number of rotten sources.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if oranges could also rot diagonally?
A: Extend DIRECTIONS to all 8 neighbors, same as 015's diagonal movement —
   everything else in the algorithm is unchanged.

Q: What if you needed to know WHICH oranges rotted at each minute, not just
   the total?
A: Snapshot `list(queue)` (or the cells rotted during that iteration) at the
   top of each level before draining it — the level-by-level structure
   already segments the answer by minute, you're just keeping it instead of
   discarding it.

Q: How is this different from Walls and Gates (005)?
A: Identical multi-source BFS skeleton. 005 writes a DISTANCE into each
   cell; 006 counts BFS LEVELS (a scalar, not a per-cell value) and adds a
   reachability check (`fresh > 0` at the end) that 005 does implicitly by
   leaving unreachable cells at INF instead of failing outright.

Q: Could you solve this with DFS instead?
A: Not directly for the minute count — DFS doesn't process in wave order,
   so "minutes" would require tracking depth-on-first-visit per cell and
   re-visiting whenever a shorter path is found (Dijkstra-flavored, more
   bookkeeping for zero benefit on an unweighted grid). BFS's wave order
   gives you minutes for free.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Multi-source BFS, "spread from many sources simultaneously":

    LC 286  Walls and Gates            — same pattern, writes distances (005)
    LC 542  01 Matrix                  — same pattern, distance-to-nearest-zero (014)
    LC 1162 As Far from Land as Possible — same pattern, MAXIMIZE the min distance
    LC 1730 Shortest Path to Get Food    — single-source BFS variant, one target type
================================================================================
"""

import random
import time
from collections import deque
from typing import List

DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


class Solution:
    def orangesRotting(self, grid: List[List[int]]) -> int:
        """✅ THE ANSWER — multi-source BFS, level by level = minute by
        minute. O(rows*cols) time, O(rows*cols) space. Mutates grid in place."""
        rows, cols = len(grid), len(grid[0])
        queue = deque()
        fresh = 0
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == 2:
                    queue.append((r, c))
                elif grid[r][c] == 1:
                    fresh += 1

        if fresh == 0:
            return 0

        minutes = 0
        while queue and fresh > 0:
            minutes += 1
            for _ in range(len(queue)):
                r, c = queue.popleft()
                for dr, dc in DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
                        grid[nr][nc] = 2
                        fresh -= 1
                        queue.append((nr, nc))

        return minutes if fresh == 0 else -1

    def orangesRotting_single_source_per_rotten(self, grid: List[List[int]]) -> int:
        """Correct but wasteful — Approach 1. BFS from EACH rotten orange
        independently, keep the min arrival minute per cell, then answer is
        the max of those minimums (the last cell to rot). Does NOT mutate
        the input grid — it reads it only.
        O(rotten_count * rows * cols) time."""
        rows, cols = len(grid), len(grid[0])
        rotten = [(r, c) for r in range(rows) for c in range(cols) if grid[r][c] == 2]
        fresh_cells = {(r, c) for r in range(rows) for c in range(cols) if grid[r][c] == 1}

        if not fresh_cells:
            return 0
        if not rotten:
            return -1

        best = {cell: float("inf") for cell in fresh_cells}
        for sr, sc in rotten:
            dist = {(sr, sc): 0}
            queue = deque([(sr, sc)])
            while queue:
                r, c = queue.popleft()
                for dr, dc in DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < rows and 0 <= nc < cols
                            and grid[nr][nc] != 0 and (nr, nc) not in dist):
                        dist[(nr, nc)] = dist[(r, c)] + 1
                        queue.append((nr, nc))
                        if (nr, nc) in best and dist[(nr, nc)] < best[(nr, nc)]:
                            best[(nr, nc)] = dist[(nr, nc)]

        if any(v == float("inf") for v in best.values()):
            return -1
        return max(best.values())


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def make_random_grid(rows: int, cols: int, n_rotten: int, n_empty: int,
                      seed: int) -> List[List[int]]:
    rng = random.Random(seed)
    cells = [(r, c) for r in range(rows) for c in range(cols)]
    rng.shuffle(cells)
    grid = [[1] * cols for _ in range(rows)]
    for (r, c) in cells[:n_rotten]:
        grid[r][c] = 2
    for (r, c) in cells[n_rotten:n_rotten + n_empty]:
        grid[r][c] = 0
    return grid


# ==============================================================================
# TESTS — run:  python 006_rotting_oranges_solution.py
# ==============================================================================
CASES = [
    ([[2, 1, 1], [1, 1, 0], [0, 1, 1]], 4),
    ([[2, 1, 1], [0, 1, 1], [1, 0, 1]], -1),
    ([[0, 2]], 0),
    ([[0]], 0),
    ([[1]], -1),
    ([[2]], 0),
    ([[0, 0, 0], [0, 0, 0]], 0),
    ([[2, 1, 1], [1, 1, 1], [1, 1, 1]], 4),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: primary multi-source BFS ---")
    for i, (grid, expected) in enumerate(CASES):
        working = [row[:] for row in grid]
        got = sol.orangesRotting(working)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  case {i}: grid={grid} -> {got} (want {expected})")

    print("\n--- correctness: single-source-per-rotten variant agrees ---")
    for i, (grid, expected) in enumerate(CASES):
        working = [row[:] for row in grid]
        got = sol.orangesRotting_single_source_per_rotten(working)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  case {i}: -> {got} (want {expected})")

    print("\n--- randomised cross-check: both approaches agree, 300 random grids ---")
    mismatches = 0
    for i in range(300):
        rng = random.Random(2000 + i)
        rows, cols = rng.randint(1, 8), rng.randint(1, 8)
        n_cells = rows * cols
        n_rotten = rng.randint(0, max(1, n_cells // 4))
        n_empty = rng.randint(0, max(1, n_cells // 4))
        grid = make_random_grid(rows, cols, n_rotten, n_empty, seed=2000 + i)
        g1 = [row[:] for row in grid]
        r1 = sol.orangesRotting(g1)
        r2 = sol.orangesRotting_single_source_per_rotten([row[:] for row in grid])
        if r1 != r2:
            mismatches += 1
    print(f"  300 random grids, multi-source vs per-rotten BFS: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # STEP BY STEP trace, printed live.
    # ----------------------------------------------------------------------
    print("\n--- trace: Example 1 grid, minute by minute ---")
    trace_grid = [row[:] for row in CASES[0][0]]
    rows, cols = len(trace_grid), len(trace_grid[0])
    queue = deque((r, c) for r in range(rows) for c in range(cols) if trace_grid[r][c] == 2)
    fresh = sum(row.count(1) for row in trace_grid)
    print(f"  minute 0: {trace_grid}  fresh={fresh}")
    minutes = 0
    while queue and fresh > 0:
        minutes += 1
        for _ in range(len(queue)):
            r, c = queue.popleft()
            for dr, dc in DIRECTIONS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and trace_grid[nr][nc] == 1:
                    trace_grid[nr][nc] = 2
                    fresh -= 1
                    queue.append((nr, nc))
        print(f"  minute {minutes}: {trace_grid}  fresh={fresh}")
    print(f"  final minutes={minutes}, matches expected 4: {minutes == 4}")

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: multi-source BFS vs BFS-per-rotten-orange, MEASURED.
    # ----------------------------------------------------------------------
    print("\n--- RUNTIME DEMO: multi-source BFS vs BFS-per-rotten-then-min ---")
    rows, cols = 80, 80
    n_rotten = 40
    grid = make_random_grid(rows, cols, n_rotten=n_rotten, n_empty=300, seed=7)
    print(f"  grid {rows}x{cols} = {rows*cols} cells, {n_rotten} rotten sources, 300 empty")

    g1 = [row[:] for row in grid]
    t0 = time.perf_counter()
    r1 = sol.orangesRotting(g1)
    t1 = time.perf_counter()
    multi_ms = (t1 - t0) * 1000

    g2 = [row[:] for row in grid]
    t2 = time.perf_counter()
    r2 = sol.orangesRotting_single_source_per_rotten(g2)
    t3 = time.perf_counter()
    per_source_ms = (t3 - t2) * 1000

    same_result = r1 == r2
    speedup = per_source_ms / multi_ms if multi_ms > 0 else float("inf")
    print(f"  multi-source BFS:            {multi_ms:8.3f} ms  -> {r1}")
    print(f"  BFS-per-rotten ({n_rotten} sources): {per_source_ms:8.3f} ms  -> {r2}")
    print(f"  speedup:                     {speedup:8.1f}x")
    print(f"  both approaches produced the same answer: {same_result}")
    print("  O(rows*cols) vs O(rotten*rows*cols): with 40 rotten sources the")
    print("  per-source version does roughly 40x the traversal work of")
    print("  multi-source BFS, and the measured speedup above reflects that.")
    all_ok &= same_result
    all_ok &= (multi_ms < per_source_ms)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
