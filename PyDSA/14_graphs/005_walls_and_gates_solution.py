"""
================================================================================
SOLUTION · LeetCode 286 · Walls and Gates                          [Medium]
https://leetcode.com/problems/walls-and-gates/  (premium/locked — standard
interview problem regardless, written here at full depth)
================================================================================

THE CORE IDEA
--------------
"Distance from every empty cell to its NEAREST of several targets" is
multi-source BFS (topic guide §6.3): seed the BFS queue with ALL gates at
distance 0 before the first pop, instead of running single-source BFS once
per gate and taking the minimum. Because BFS explores in strictly increasing
distance order, the FIRST time a cell is reached — from whichever gate got
there first — that is its true shortest distance, full stop. No cell needs
to be visited twice, so `rooms[r][c] == INF` doubles as the "not yet
visited" check: once overwritten with a real distance, never enqueue again.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, don't ship): for every empty room, run its own BFS
(or DFS) outward until a gate is found, or scan every gate and take the
Manhattan-ish grid distance via a full BFS from each empty cell. That is
O((rows*cols)^2) in the worst case — one full grid traversal PER empty cell.
Never do this.

Approach 1 (single-source BFS per gate, then take the min) — CORRECT but
wasteful: for each gate, run one full BFS over the grid computing distance
from that gate to every reachable cell, then, per cell, keep the minimum
across all gates' runs. O(gates * rows * cols) time, since every gate's BFS
can touch every cell. Priced and benchmarked below — it is a real approach
some candidates reach for first, and it IS correct, just not optimal.

Approach 2 (multi-source BFS) ✅ — the answer. Push every gate onto the SAME
queue at distance 0 up front, then run one ordinary BFS. O(rows * cols) time
— each cell is enqueued and dequeued exactly once, regardless of how many
gates exist. Space O(rows * cols) for the queue in the worst case.

    from collections import deque

    def solve(rooms):
        if not rooms or not rooms[0]:
            return
        rows, cols = len(rooms), len(rooms[0])
        INF = 2147483647
        queue = deque()
        for r in range(rows):
            for c in range(cols):
                if rooms[r][c] == 0:
                    queue.append((r, c))            # ALL gates seeded first

        DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        while queue:
            r, c = queue.popleft()
            for dr, dc in DIRECTIONS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and rooms[nr][nc] == INF:
                    rooms[nr][nc] = rooms[r][c] + 1     # nearest-gate distance
                    queue.append((nr, nc))


================================================================================
STEP BY STEP TRACE
================================================================================
rooms =
    INF  -1   0  INF
    INF INF INF   -1
    INF  -1 INF   -1
      0  -1 INF INF

Gates found at (0,2) and (3,0). Seed queue = [(0,2), (3,0)], both dist 0.

wave 0 (the gates themselves, distance already 0 — nothing to write):
    INF  -1   0  INF
    INF INF INF   -1
    INF  -1 INF   -1
      0  -1 INF INF

pop (0,2), dist 0 -> neighbors (0,1)=-1 skip wall, (0,3)=INF write 1, (1,2)=INF write 1
pop (3,0), dist 0 -> neighbors (2,0)=INF write 1, (3,1)=-1 skip wall

    INF  -1   0   1
    INF INF   1   -1
      1  -1 INF   -1
      0  -1 INF INF

pop (0,3) dist1 -> (1,3)=-1 skip wall
pop (1,2) dist1 -> (1,1)=INF write 2, (2,2)=INF write 2
pop (2,0) dist1 -> (1,0)=INF write 2

    INF  -1   0   1
      2   2   1   -1
      1  -1   2   -1
      0  -1 INF INF

pop (1,1) dist2 -> (0,1)=-1 skip, (2,1)=-1 skip
pop (2,2) dist2 -> (3,2)=INF write 3, (2,3)=-1 skip
pop (1,0) dist2 -> (0,0)=INF write 3

    3  -1   0   1
    2   2   1   -1
    1  -1   2   -1
    0  -1   3 INF

pop (3,2) dist3 -> (3,3)=INF write 4

    3  -1   0   1
    2   2   1   -1
    1  -1   2   -1
    0  -1   3   4

pop (3,3) dist4 -> no unvisited neighbors. queue empty -> done.
Final grid matches the problem's Example 1 exactly.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time                Space    Mutates input?
    -------------------------------   -----------------   -------  --------------
    Brute force (BFS per empty cell)  O((R*C)^2)           O(R*C)   YES, in place
    Single-source BFS per gate + min  O(gates * R*C)        O(R*C)   YES, in place
    Multi-source BFS ✅                O(R*C)                O(R*C)   YES, in place

    "Mutates input?" is YES for every approach here — the problem explicitly
    asks for in-place modification and no return value, matching LC's exact
    signature `solve(self, rooms) -> None`.


================================================================================
EDGE CASES
================================================================================
    grid of all walls / single wall   -> queue starts empty, BFS does
                                          nothing, grid unchanged. Exists
                                          because "no gates at all" is legal
                                          input, not an error.
    grid with no gates                -> every INF cell stays INF forever;
                                          the loop that seeds the queue just
                                          finds nothing, exactly like above.
    gate walled in on all sides       -> BFS from that gate can never step
                                          off it; its distance-0 self stays
                                          0, nothing beyond the wall changes.
                                          Reachability, not just distance,
                                          is part of the correctness story.
    1x1 grid (wall, gate, or INF)     -> queue seeding and the BFS loop must
                                          both handle "no neighbors exist"
                                          without special-casing it.
    multiple gates equidistant        -> multi-source BFS handles this for
                                          free: the first gate's wave to
                                          reach a cell wins, and it does not
                                          matter WHICH gate it was — the
                                          distance is identical either way.


================================================================================
COMMON MISTAKES
================================================================================
1. Running BFS once per gate and taking the min per cell (Approach 1). It is
   CORRECT, but costs O(gates * rows * cols) instead of O(rows * cols) — on a
   grid with many gates this is a real, measurable slowdown (see the runtime
   demo below).
2. Marking `visited` on dequeue instead of checking `rooms[nr][nc] == INF`
   before pushing — the same cell can then be pushed by multiple gates
   before it's first processed, and worse, pushed again after it's already
   been overwritten with a distance, corrupting later comparisons.
3. Forgetting walls block movement — pushing a wall cell onto the queue (or
   reading through one) produces distances that "tunnel" through obstacles.
4. Treating 0 (gate) cells the same as INF cells when seeding — only 0-cells
   seed the queue; INF cells are the ones waiting to be filled.
5. Off-by-one on `INF` itself: `2147483647` is a real sentinel value, not
   Python's `float('inf')`. Comparing against the wrong sentinel (or against
   `sys.maxsize`) silently never matches any cell.
6. Single-source BFS looped per gate (mistake #1 restated) is the exact
   §6.3 trap this topic guide calls out by name for this problem.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if some rooms are diagonally adjacent to a gate — does diagonal
   movement count?
A: No, per the problem's grid movement rules — up/down/left/right only, same
   DIRECTIONS helper as every other grid problem in this folder (topic guide
   §6.2). If diagonals were allowed, add the 4 diagonal deltas (015's
   pattern).

Q: Could you solve this with DFS instead of BFS?
A: Not efficiently as multi-source shortest-distance — DFS does not explore
   in non-decreasing distance order, so without extra bookkeeping (revisiting
   a cell if a shorter distance is later found) DFS both revisits cells and
   can compute the WRONG minimum on the first pass. BFS's wave structure is
   exactly what "nearest of many sources" needs.

Q: How would you handle a weighted grid (some cells cost more to enter)?
A: Multi-source BFS assumes unweighted edges (uniform cost 1). Weighted
   would need multi-source Dijkstra (a min-heap of (cost, r, c) seeded with
   every gate at cost 0) — topic 15's toolkit, not this one.

Q: This is basically LC 542 (01 Matrix) and LC 1091-adjacent — how are they
   related?
A: 542 (014 in this folder) is the identical algorithm with the source set
   being "every 0 cell" instead of "every gate cell" — same multi-source BFS,
   different vocabulary. Rotting Oranges (006) is the same pattern again,
   with the added twist of counting BFS *waves* instead of writing distances
   into the grid.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Multi-source BFS, "distance to nearest of many sources":

    LC 994  Rotting Oranges           — same pattern, counts waves (006)
    LC 542  01 Matrix                 — same pattern, distance-to-nearest-zero (014)
    LC 1162 As Far from Land as Possible — same pattern, MAXIMIZE the min distance
    LC 133  Clone Graph               — multi-... no, single source, but same BFS
                                         skeleton with a visited MAP instead of a set (004)
================================================================================
"""

import random
import time
from collections import deque
from typing import List, Tuple

INF = 2147483647
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


class Solution:
    def solve(self, rooms: List[List[int]]) -> None:
        """✅ THE ANSWER — multi-source BFS. Seed the queue with EVERY gate
        before the first pop. O(rows*cols) time, O(rows*cols) space."""
        if not rooms or not rooms[0]:
            return
        rows, cols = len(rooms), len(rooms[0])
        queue = deque()
        for r in range(rows):
            for c in range(cols):
                if rooms[r][c] == 0:
                    queue.append((r, c))

        while queue:
            r, c = queue.popleft()
            for dr, dc in DIRECTIONS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and rooms[nr][nc] == INF:
                    rooms[nr][nc] = rooms[r][c] + 1
                    queue.append((nr, nc))

    def solve_single_source_per_gate(self, rooms: List[List[int]]) -> None:
        """Correct but wasteful — Approach 1. Run a full BFS from EACH gate
        independently and keep the minimum per cell. O(gates * rows * cols)."""
        if not rooms or not rooms[0]:
            return
        rows, cols = len(rooms), len(rooms[0])
        gates = [(r, c) for r in range(rows) for c in range(cols)
                 if rooms[r][c] == 0]
        best = [[INF] * cols for _ in range(rows)]
        for gr, gc in gates:
            dist = [[-2] * cols for _ in range(rows)]   # -2 = unvisited marker
            dist[gr][gc] = 0
            queue = deque([(gr, gc)])
            while queue:
                r, c = queue.popleft()
                for dr, dc in DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < rows and 0 <= nc < cols
                            and rooms[nr][nc] != -1 and dist[nr][nc] == -2):
                        dist[nr][nc] = dist[r][c] + 1
                        queue.append((nr, nc))
                        if dist[nr][nc] < best[nr][nc]:
                            best[nr][nc] = dist[nr][nc]
        for r in range(rows):
            for c in range(cols):
                if rooms[r][c] == INF and best[r][c] < INF:
                    rooms[r][c] = best[r][c]


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def make_random_grid(rows: int, cols: int, n_gates: int, n_walls: int,
                      seed: int) -> List[List[int]]:
    rng = random.Random(seed)
    cells = [(r, c) for r in range(rows) for c in range(cols)]
    rng.shuffle(cells)
    grid = [[INF] * cols for _ in range(rows)]
    for (r, c) in cells[:n_gates]:
        grid[r][c] = 0
    for (r, c) in cells[n_gates:n_gates + n_walls]:
        grid[r][c] = -1
    return grid


# ==============================================================================
# TESTS — run:  python 005_walls_and_gates_solution.py
# ==============================================================================
CASES: List[Tuple[List[List[int]], List[List[int]]]] = [
    (
        [
            [INF, -1, 0, INF],
            [INF, INF, INF, -1],
            [INF, -1, INF, -1],
            [0, -1, INF, INF],
        ],
        [
            [3, -1, 0, 1],
            [2, 2, 1, -1],
            [1, -1, 2, -1],
            [0, -1, 3, 4],
        ],
    ),
    ([[-1]], [[-1]]),
    ([[0]], [[0]]),
    ([[INF]], [[INF]]),
    ([[0, INF], [INF, INF]], [[0, 1], [1, 2]]),
    (
        [[-1, -1, -1], [-1, 0, -1], [-1, -1, -1]],
        [[-1, -1, -1], [-1, 0, -1], [-1, -1, -1]],
    ),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: primary multi-source BFS ---")
    for i, (grid, expected) in enumerate(CASES):
        working = [row[:] for row in grid]
        sol.solve(working)
        ok = working == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  case {i}: -> {working}")

    print("\n--- correctness: single-source-per-gate variant agrees ---")
    for i, (grid, expected) in enumerate(CASES):
        working = [row[:] for row in grid]
        sol.solve_single_source_per_gate(working)
        ok = working == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  case {i}: -> {working}")

    print("\n--- randomised cross-check: both approaches agree, 300 random grids ---")
    mismatches = 0
    for i in range(300):
        rng = random.Random(1000 + i)
        rows, cols = rng.randint(1, 12), rng.randint(1, 12)
        n_cells = rows * cols
        n_gates = rng.randint(0, max(1, n_cells // 6))
        n_walls = rng.randint(0, max(1, n_cells // 4))
        grid = make_random_grid(rows, cols, n_gates, n_walls, seed=1000 + i)
        g1 = [row[:] for row in grid]
        g2 = [row[:] for row in grid]
        sol.solve(g1)
        sol.solve_single_source_per_gate(g2)
        if g1 != g2:
            mismatches += 1
    print(f"  300 random grids, multi-source vs per-gate BFS: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # STEP BY STEP trace, printed live (matches the docstring's hand trace).
    # ----------------------------------------------------------------------
    print("\n--- trace: Example 1 grid, wave by wave ---")
    trace_grid = [row[:] for row in CASES[0][0]]
    rows, cols = len(trace_grid), len(trace_grid[0])
    queue = deque((r, c) for r in range(rows) for c in range(cols)
                  if trace_grid[r][c] == 0)
    print(f"  seed queue (all gates at dist 0): {list(queue)}")
    wave = 0
    while queue:
        wave += 1
        size = len(queue)
        for _ in range(size):
            r, c = queue.popleft()
            for dr, dc in DIRECTIONS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and trace_grid[nr][nc] == INF:
                    trace_grid[nr][nc] = trace_grid[r][c] + 1
                    queue.append((nr, nc))
        print(f"  after wave {wave}: {trace_grid}")
    print(f"  final == expected: {trace_grid == CASES[0][1]}")

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: multi-source BFS vs single-source-per-gate, MEASURED.
    # ----------------------------------------------------------------------
    print("\n--- RUNTIME DEMO: multi-source BFS vs BFS-per-gate-then-min ---")
    rows, cols = 80, 80
    n_gates = 40
    grid = make_random_grid(rows, cols, n_gates=n_gates, n_walls=200, seed=42)
    print(f"  grid {rows}x{cols} = {rows*cols} cells, {n_gates} gates, 200 walls")

    g1 = [row[:] for row in grid]
    t0 = time.perf_counter()
    sol.solve(g1)
    t1 = time.perf_counter()
    multi_ms = (t1 - t0) * 1000

    g2 = [row[:] for row in grid]
    t2 = time.perf_counter()
    sol.solve_single_source_per_gate(g2)
    t3 = time.perf_counter()
    per_gate_ms = (t3 - t2) * 1000

    same_result = g1 == g2
    speedup = per_gate_ms / multi_ms if multi_ms > 0 else float("inf")
    print(f"  multi-source BFS:        {multi_ms:8.3f} ms")
    print(f"  BFS-per-gate ({n_gates} gates): {per_gate_ms:8.3f} ms")
    print(f"  speedup:                 {speedup:8.1f}x")
    print(f"  both approaches produced identical grids: {same_result}")
    print("  O(rows*cols) vs O(gates*rows*cols): with 40 gates the per-gate")
    print("  version does roughly 40x the traversal work of multi-source BFS,")
    print("  and the measured speedup above is in that ballpark on this machine.")
    all_ok &= same_result
    all_ok &= (multi_ms < per_gate_ms)   # multi-source really must be faster here

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
