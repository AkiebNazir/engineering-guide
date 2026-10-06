"""
================================================================================
SOLUTION · LeetCode 200 · Number of Islands                          [Medium]
https://leetcode.com/problems/number-of-islands/
================================================================================

THE CORE IDEA
--------------
"Number of islands" is "number of connected components" (topic guide Part 3)
on the grid-as-graph from Part 6, where land cells are nodes and edges
connect orthogonally-adjacent land. Scan every cell in row-major order.
Every time the scan finds a land cell that hasn't been claimed by an earlier
flood, that is by definition the FIRST cell of a brand-new island (nothing
earlier in scan order could have reached it, or it would already be
visited) — count it, then flood-fill (001) the whole component so the scan
never fires on it again.

    islands = 0
    for r, c in every cell:
        if grid[r][c] == land and (r, c) not visited:
            islands += 1
            flood_mark_whole_component(r, c)     # 001's routine, no repaint value needed
    return islands

Everything from problem 001 is reused verbatim as the inner routine; the
only new idea is the outer "count the first sighting of each component."


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, don't ship): Union-Find over all land cells, union
every pair of adjacent land cells, then count distinct roots. Correct,
O(rows*cols * alpha(rows*cols)) ~ O(rows*cols) with path compression — same
asymptotic complexity as DFS/BFS, but more machinery (a DSU structure) for
no benefit on a STATIC grid. Union-Find earns its keep the moment the grid
is built incrementally (see follow-ups) — LC 305 Number of Islands II is
exactly that problem.

Approach 1 (DFS, recursive): flood each new component with 001's recursive
helper. Shortest to write; carries 001's recursion-depth risk, worse here
because 200's own constraints go up to 300x300 = 90,000 cells — a single
snake-shaped island of that size would need 90,000 stack frames, far past
CPython's default ~1000-frame limit.

Approach 2 (DFS, iterative stack) ✅: same traversal, an explicit list
instead of the call stack. No depth ceiling.

Approach 3 (BFS, deque) ✅: same complexity, breadth-first order. Timed
against Approach 2 below — they land within noise of each other on this
workload; BFS is worth preferring only when you also want shortest-distance
information, which counting doesn't need.

Marking "visited," two ways (topic guide §6.1) — a real tradeoff, not just
style:
  (a) mutate the grid in place: flip a visited `'1'` to `'0'` (or any
      non-land sentinel) the moment you enqueue/push it. Zero extra memory
      beyond the traversal stack/queue, but the caller's grid is gone
      afterward.
  (b) a separate `visited` set of `(r, c)` tuples. O(rows*cols) extra
      memory, but the input is untouched. Demoed live below: identical
      counts, very different grid state after the call.

200 never says "don't modify the input," so mutating in place is legitimate
and is what the primary `numIslands` below does; `numIslands_preserve` shows
the alternative for problems that forbid it.


================================================================================
STEP BY STEP TRACE
================================================================================
grid = [["1","1","0","0","0"],
        ["1","1","0","0","0"],
        ["0","0","1","0","0"],
        ["0","0","0","1","1"]]

    scan (0,0): '1', unvisited -> islands=1, flood:
        mark (0,0)(0,1)(1,0)(1,1)   [all '1', connected]
        0 0 . . .          . . . . .
        0 0 . . .   -->    . . . . .    ('.' = visited/consumed)
        . . 1 . .          . . 1 . .
        . . . 1 1          . . . 1 1

    scan continues (0,2)..(1,4): all '0' or already visited -> skip
    scan (2,2): '1', unvisited -> islands=2, flood:
        only (2,2) itself is land-adjacent to land -> component of size 1
        . . . . .
        . . . . .
        . . . . .
        . . . 1 1

    scan (3,3): '1', unvisited -> islands=3, flood:
        mark (3,3)(3,4)
        . . . . .
        . . . . .
        . . . . .
        . . . . .

    scan finishes, no more '1's found -> return 3.   Matches Example 2.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                      Time            Space            Mutates input?
    ----------------------------  --------------  ---------------  --------------
    Union-Find                    O(rc * a(rc))   O(rc)            depends on marker
    DFS recursive                 O(rows*cols)    O(rows*cols)     YES (in-place variant)
                                                   worst-case stack
    DFS iterative (stack) ✅       O(rows*cols)    O(rows*cols)     YES, in place
    BFS (deque) ✅                 O(rows*cols)    O(rows*cols)     YES, in place
    Any of the above + visited set O(rows*cols)    O(rows*cols)     NO, grid preserved
                                                    (traversal + set,
                                                     ~2x the memory)

    rc = rows*cols. "Mutates input?" YES for the in-place variants (the
    default here, since 200 places no restriction on the input) — the
    caller's grid comes back with every land cell overwritten. Use the
    `visited`-set variant the moment the grid must survive the call.


================================================================================
EDGE CASES
================================================================================
    grid is all '0'            -> 0 islands; outer scan never fires a flood.
    grid is all '1'            -> 1 island; worst case for BOTH space (visited
                                  set/queue size) and recursion depth if DFS
                                  is recursive and the grid is a single row
                                  or column (a "snake").
    single cell                -> '1' -> 1, '0' -> 0. Smallest real input.
    grid values are STRINGS     -> `grid[r][c] == "1"`, not `== 1`. Mixing up
                                  str vs int is a real, silent bug here (an
                                  int 1 never equals str "1" in Python, so
                                  every land cell would look like water and
                                  the answer would silently come back 0).
    checkerboard pattern        -> every '1' isolated from every other by
                                  '0's on all 4 sides -> islands == count of
                                  '1's, each flood touches exactly one cell.
    single row or column, all
    land ("snake")              -> forces DFS recursion depth == length;
                                  see 001's live RecursionError demo, which
                                  applies here unchanged.


================================================================================
COMMON MISTAKES
================================================================================
1. Comparing grid values to the integer `1` instead of the string `"1"`.
   LeetCode 200 explicitly hands you a grid of CHARACTERS. `grid[r][c] == 1`
   is always `False`, so every cell reads as water and the function
   silently returns 0 on every real test — no exception, just a wrong
   answer that looks like an empty grid was passed in.

2. Marking a cell as visited on DEQUEUE/pop instead of on
   enqueue/push (topic guide mistake #2). The same cell can be pushed
   multiple times by different neighbors before it's first processed,
   inflating the queue/stack and, in pathological layouts, producing an
   inflated island count if the "have I counted this land yet" check is
   naively tied to the wrong moment.

3. Re-flooding an already-visited island because the outer double loop's
   visited check and the inner flood's visited check use two DIFFERENT
   conditions (e.g. outer checks a `visited` set but inner mutates the grid,
   or vice versa) — pick ONE source of truth and use it everywhere.

4. Recursive DFS on the full 300x300 constraint with a single-file land
   shape — see 001's live demo; the failure mode is a hard RecursionError,
   not a slowdown, so "it passed my small test" gives false confidence.

5. Off-by-one / missing bounds check on grid neighbors — `r-1` going
   negative doesn't raise in Python, it silently reads the LAST row
   (topic guide mistake #8), which on an all-land grid can merge unrelated
   islands or miscount depending on layout.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if islands are added one at a time (LC 305, streaming)?
A: DFS/BFS from scratch after each addition is O(rows*cols) PER addition —
   too slow for many additions. Union-Find with path compression + union by
   rank answers "how many islands now?" in near-O(1) amortized per
   addition, because you only need to know whether the new land cell
   connects to existing components, not re-scan the whole grid.

Q: Diagonal connections count too?
A: Add the 4 diagonal deltas to the neighbor check (topic guide §6.2, same
   extension 015 makes for a different reason). Nothing else about the
   algorithm changes.

Q: Return the SIZE of each island, not just the count?
A: That's 003 (Max Area of Island), next in this folder — have the flood
   routine return a count of cells visited instead of nothing.

Q: Grid too large to fit in memory / streamed row by row?
A: Union-Find again, processing rows as they arrive and unioning each new
   cell with its already-seen left/up neighbors — never needs the whole
   grid in memory as a graph, only a rolling window.

Q: Can you avoid the O(rows*cols) visited-set/mutation memory entirely?
A: Not for a general adjacency-based approach — you must not re-count
   already-claimed land. In-place mutation IS the zero-extra-memory answer
   when the caller allows it (§6.1); if not, O(rows*cols) is unavoidable
   for a separate visited structure.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Grid-as-graph, whole-grid scan for multiple components (topic guide Part 6).

    LC 733  Flood Fill                    — the inner routine, single source (001)
    LC 695  Max Area of Island            — same scan, track size not just count (003)
    LC 305  Number of Islands II          — streaming version, Union-Find
    LC 1254 Number of Closed Islands      — flood the border first, then count
    LC 694  Number of Distinct Islands    — same scan + shape fingerprinting
    LC 130  Surrounded Regions            — flood from the border inward
================================================================================
"""

import sys
import time
from collections import deque
from typing import List, Set, Tuple


class Solution:
    def numIslands(self, grid: List[List[str]]) -> int:
        """✅ THE ANSWER — iterative DFS, marks visited by MUTATING the grid
        in place (flips '1' to '0'). O(rows*cols) time, O(rows*cols) worst
        case stack space. MUTATES `grid`; 200 places no restriction on the
        input, so this is legitimate and needs zero extra visited structure."""
        if not grid or not grid[0]:
            return 0
        rows, cols = len(grid), len(grid[0])
        islands = 0

        def flood(r, c):
            stack = [(r, c)]
            grid[r][c] = "0"
            while stack:
                cr, cc = stack.pop()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == "1":
                        grid[nr][nc] = "0"
                        stack.append((nr, nc))

        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == "1":
                    islands += 1
                    flood(r, c)
        return islands

    def numIslands_bfs(self, grid: List[List[str]]) -> int:
        """BFS variant, same in-place mutation strategy. O(rows*cols) time
        and space. MUTATES `grid`."""
        if not grid or not grid[0]:
            return 0
        rows, cols = len(grid), len(grid[0])
        islands = 0

        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == "1":
                    islands += 1
                    queue = deque([(r, c)])
                    grid[r][c] = "0"
                    while queue:
                        cr, cc = queue.popleft()
                        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                            nr, nc = cr + dr, cc + dc
                            if (0 <= nr < rows and 0 <= nc < cols
                                    and grid[nr][nc] == "1"):
                                grid[nr][nc] = "0"
                                queue.append((nr, nc))
        return islands

    def numIslands_preserve(self, grid: List[List[str]]) -> int:
        """Same algorithm, but marks visited with a SEPARATE set instead of
        mutating the grid. O(rows*cols) time, O(rows*cols) extra space for
        the visited set (on top of the traversal stack). Does NOT mutate
        `grid` — the caller's input comes back unchanged. Use this whenever
        the grid must be read again, or the problem forbids mutation."""
        if not grid or not grid[0]:
            return 0
        rows, cols = len(grid), len(grid[0])
        visited: Set[Tuple[int, int]] = set()
        islands = 0

        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == "1" and (r, c) not in visited:
                    islands += 1
                    stack = [(r, c)]
                    visited.add((r, c))
                    while stack:
                        cr, cc = stack.pop()
                        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                            nr, nc = cr + dr, cc + dc
                            if (0 <= nr < rows and 0 <= nc < cols
                                    and grid[nr][nc] == "1"
                                    and (nr, nc) not in visited):
                                visited.add((nr, nc))
                                stack.append((nr, nc))
        return islands

    def numIslands_recursive(self, grid: List[List[str]]) -> int:
        """Textbook recursive DFS. O(rows*cols) time, O(rows*cols) worst
        case CALL STACK — RecursionError on a large single-file island (see
        001's live demo, same failure mode). MUTATES `grid`."""
        if not grid or not grid[0]:
            return 0
        rows, cols = len(grid), len(grid[0])
        islands = 0

        def dfs(r, c):
            if not (0 <= r < rows and 0 <= c < cols):
                return
            if grid[r][c] != "1":
                return
            grid[r][c] = "0"
            dfs(r - 1, c)
            dfs(r + 1, c)
            dfs(r, c - 1)
            dfs(r, c + 1)

        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == "1":
                    islands += 1
                    dfs(r, c)
        return islands


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def make_strip(length: int) -> List[List[str]]:
    """1-row, all-land strip — one island of size `length`, worst case for
    recursive DFS's call stack depth."""
    return [["1"] * length]


# ==============================================================================
# TESTS — run:  python 002_number_of_islands_solution.py
# ==============================================================================
CASES = [
    ([["1", "1", "1", "1", "0"],
      ["1", "1", "0", "1", "0"],
      ["1", "1", "0", "0", "0"],
      ["0", "0", "0", "0", "0"]], 1),
    ([["1", "1", "0", "0", "0"],
      ["1", "1", "0", "0", "0"],
      ["0", "0", "1", "0", "0"],
      ["0", "0", "0", "1", "1"]], 3),
    ([["0"]], 0),
    ([["1"]], 1),
    ([["1", "0", "1", "0", "1"]], 3),
    ([["1", "1", "1"], ["1", "1", "1"], ["1", "1", "1"]], 1),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: all four implementations agree ---")
    for grid, want in CASES:
        a = sol.numIslands([row[:] for row in grid])
        b = sol.numIslands_bfs([row[:] for row in grid])
        c = sol.numIslands_preserve([row[:] for row in grid])
        d = sol.numIslands_recursive([row[:] for row in grid])
        ok = a == b == c == d == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  -> DFS={a} BFS={b} preserve={c} "
              f"recursive={d} (want {want})")

    # ----------------------------------------------------------------------
    # LIVE DEMO 1: mutate-in-place DESTROYS the grid; visited-set PRESERVES it.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 1: in-place mutation destroys the grid; a visited set doesn't ---")
    original = [["1", "1", "0"], ["0", "1", "0"], ["0", "0", "1"]]
    mutate_copy = [row[:] for row in original]
    preserve_copy = [row[:] for row in original]

    count_mutate = sol.numIslands(mutate_copy)
    count_preserve = sol.numIslands_preserve(preserve_copy)

    grid_destroyed = mutate_copy != original
    grid_preserved = preserve_copy == original
    print(f"  original grid:        {original}")
    print(f"  after numIslands():   {mutate_copy}   (destroyed: {grid_destroyed})")
    print(f"  after numIslands_preserve(): {preserve_copy}   "
          f"(preserved: {grid_preserved})")
    print(f"  both report the same count: {count_mutate} == {count_preserve} "
          f"-> {count_mutate == count_preserve}")
    all_ok &= grid_destroyed and grid_preserved and count_mutate == count_preserve

    # ----------------------------------------------------------------------
    # ⚠️  LIVE DEMO 2: recursive DFS's stack depth on a large single-file island.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: recursive DFS on a long thin island (200's own "
          "300x300 cap makes this realistic) ---")
    limit = sys.getrecursionlimit()
    n = limit + 500
    strip = make_strip(n)
    print(f"  sys.getrecursionlimit() = {limit}; island size (strip length) = {n}")

    raised = False
    try:
        sol.numIslands_recursive([row[:] for row in strip])
        print("  recursive numIslands on the strip: did NOT raise this run")
    except RecursionError as e:
        raised = True
        print(f"  recursive numIslands on the strip: RecursionError -> {e!r}")

    iter_count = sol.numIslands([row[:] for row in strip])
    iter_ok = iter_count == 1
    print(f"  iterative numIslands on the SAME strip: succeeded -> {iter_ok} "
          f"(counted {iter_count} island)")
    print(f"  iterative succeeded where recursive raised RecursionError: "
          f"{iter_ok and raised}")
    all_ok &= iter_ok and raised

    # ----------------------------------------------------------------------
    # DFS vs BFS timing on a large, richly-connected grid.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 3: DFS vs BFS timing on a large checkerboard-ish grid ---")
    import random
    random.seed(200)
    side = 250
    big = [["1" if random.random() < 0.55 else "0" for _ in range(side)]
           for _ in range(side)]

    t0 = time.perf_counter()
    dfs_count = sol.numIslands([row[:] for row in big])
    t1 = time.perf_counter()
    bfs_count = sol.numIslands_bfs([row[:] for row in big])
    t2 = time.perf_counter()

    dfs_ms, bfs_ms = (t1 - t0) * 1000, (t2 - t1) * 1000
    same_count = dfs_count == bfs_count
    all_ok &= same_count
    print(f"  {side}x{side} random grid (~55% land), {side*side} cells:")
    print(f"  DFS (iterative stack): {dfs_ms:.2f} ms, {dfs_count} islands")
    print(f"  BFS (deque):           {bfs_ms:.2f} ms, {bfs_count} islands")
    print(f"  same island count both ways: {same_count}  "
          f"(ratio DFS/BFS = {dfs_ms / bfs_ms:.2f}x)")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
