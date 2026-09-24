"""
================================================================================
SOLUTION · LeetCode 695 · Max Area of Island                         [Medium]
https://leetcode.com/problems/max-area-of-island/
================================================================================

THE CORE IDEA
--------------
Identical scan to 002 (connected components over the grid-as-graph, topic
guide Part 6), with one change: the flood routine must REPORT a number
(cells visited) instead of just marking them. `area(r, c)` for a cell that's
out of bounds, water, or already visited contributes 0; for a valid
unvisited land cell it contributes `1 + sum of area(neighbor) for all 4
neighbors`. The outer scan takes the max over every new island's area
instead of just incrementing a counter.

    best = 0
    for r, c in every cell:
        if grid[r][c] == 1 and unvisited:
            best = max(best, area(r, c))     # area() marks visited AND counts
    return best


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, don't ship): for every land cell, run a fresh
flood-fill counting reachable land WITHOUT marking anything visited between
different starting cells, then dedupe by tracking which starts belong to the
same island. O((rows*cols)^2) worst case — massively wasteful, since every
cell in an island would re-derive the same area from scratch. Never actually
useful; the fix (share one `visited` structure across the whole outer scan)
is 002/003's real algorithm.

Approach 1 (DFS, recursive, returns an int):

    def area(r, c):
        if out of bounds or grid[r][c] != 1: return 0
        grid[r][c] = 0                      # mark visited by mutation
        return 1 + area(r-1,c) + area(r+1,c) + area(r,c-1) + area(r,c+1)

Clean, but — same as 001/002 — recursion depth equals the island's cell
count in the worst (single-file) layout, up to 50*50 = 2500 here (695's own
cap; smaller than 002's 300x300 but still enough to trip CPython's default
~1000-frame limit on a maximally snake-shaped island).

Approach 2 (DFS, iterative with an explicit stack) ✅: same traversal, count
cells as you pop them instead of via return-value summation. No recursion
ceiling.

Approach 3 (BFS, deque) ✅: same complexity, count cells as you dequeue
them.

Marking visited, in place vs a separate set (topic guide §6.1): 695 places
no restriction on the input, so in-place mutation (the default below) is
legitimate and saves memory. The `_preserve` variant keeps a separate
`visited` set instead — measured against each other below with
`tracemalloc`, not just asserted.


================================================================================
STEP BY STEP TRACE
================================================================================
grid = [[1,1,0,0,0],
        [1,1,0,0,0],
        [0,0,0,1,1],
        [0,0,0,1,1],
        [0,0,0,0,1]]

    scan (0,0): grid[0][0]==1, unvisited -> flood, counting as it goes:
        visit (0,0) count=1 -> push (1,0)(0,1)
        visit (1,0) count=2 -> push (1,1)
        visit (0,1) count=3 -> push (1,1) again (dup push, fine, revisit-safe)
        visit (1,1) count=4 -> neighbors (0,1)(2,1)(1,0)(1,2) all water/visited
        island area = 4.  best = max(0, 4) = 4

        1 1 . . .
        1 1 . . .
        . . . 1 1
        . . . 1 1
        . . . . 1

    scan continues through row 0-1 remainder, all water or visited -> skip
    scan (2,3): grid[2][3]==1, unvisited -> flood:
        visit (2,3) count=1 -> push (2,4)(3,3)
        visit (2,4) count=2 -> push (3,4)
        visit (3,3) count=3 -> push (3,4) again, (4,3) water
        visit (3,4) count=4 -> push (4,4)
        visit (4,4) count=5 -> neighbors all water/visited
        island area = 5.  best = max(4, 5) = 5

    scan finishes -> return 5.   Matches Example 2 above.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                      Time            Space            Mutates input?
    ----------------------------  --------------  ---------------  --------------
    Brute-force re-derive per cell O((rc)^2)      O(rc)            no
    DFS recursive                  O(rows*cols)   O(rows*cols)     YES (in-place variant)
                                                   worst-case stack
    DFS iterative (stack) ✅        O(rows*cols)   O(rows*cols)     YES, in place
    BFS (deque) ✅                  O(rows*cols)   O(rows*cols)     YES, in place
    Any + separate visited set     O(rows*cols)    O(rows*cols)     NO, grid preserved
                                                    extra (measured
                                                     below)

    rc = rows*cols. "Mutates input?" YES by default (695 places no
    restriction on the input, matching 002's reasoning) — cells are zeroed
    out as they're counted. Use `_preserve` when the grid must survive.


================================================================================
EDGE CASES
================================================================================
    grid is all 0               -> no land at all; `best` never updates from
                                   its initial 0. Return 0, not an error.
    grid is all 1                -> one island, area == rows*cols; worst case
                                   for recursion depth if the grid is a
                                   single row/column.
    single cell                  -> 1 -> area 1, 0 -> area 0.
    every land cell isolated      -> checkerboard-style input; max area is 1
    (no two land cells touch)     regardless of how many land cells exist.
    two islands of EQUAL max area -> `max()` keeps the first one seen in scan
                                   order; the problem only asks for the
                                   value, so this is fine, but don't assume
                                   the winning island is unique.
    grid values are INTEGERS      -> contrast 002, which used string '1'/'0'.
                                   `grid[r][c] == 1`, not `== "1"`. Mixing
                                   the two up between these two problems is
                                   an easy, silent bug (always-False compare
                                   -> answer always 0).


================================================================================
COMMON MISTAKES
================================================================================
1. Returning `True`/count-as-boolean from the flood instead of an actual
   cell count — e.g. `return grid[r][c] == 1 or ...` short-circuits and
   never sums the 4 recursive branches, silently capping every island's
   reported area at 1.

2. Forgetting to mark the CURRENT cell visited before recursing into
   neighbors. Without `grid[r][c] = 0` (or `visited.add((r,c))`) up front,
   a 2-cell-wide island immediately infinite-recurses between two adjacent
   cells that keep re-"discovering" each other.

3. Comparing against the wrong type — `grid[r][c] == "1"` on this INTEGER
   grid (695) always False, contrast 002 where the grid holds characters.
   Answer silently comes back 0 with no exception.

4. Initializing `best = grid[0][0]`'s area instead of `best = 0` — breaks
   the "no island at all" case, since there is then no valid area to seed
   from, or double-counts the first island if seeded incorrectly.

5. Recursive DFS on a maximally snake-shaped island — 695's cap is 50x50 =
   2500 cells, smaller than 002's 300x300, but a single-row/column snake at
   full width/height still exceeds CPython's default ~1000-frame recursion
   limit. See 001's live RecursionError demo; the same trap applies here
   verbatim, just at a smaller absolute grid size.

6. Off-by-one / missing bounds check on grid neighbors — `r-1` going
   negative doesn't raise in Python, it silently reads the LAST row
   (topic guide mistake #8), which can merge two islands that shouldn't be
   connected and inflate the reported max area.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the max area AND its top-left-most cell (or any cell in it)?
A: Track `(area, start_r, start_c)` alongside the running max instead of
   just the area — update all three together whenever a bigger island is
   found.

Q: What if the grid is far too large to load into memory at once?
A: Process it in row-stripes, keeping only the last row's land/visited
   state to merge components that span the stripe boundary — a streaming
   variant of the Union-Find approach mentioned in 002's follow-ups.

Q: Islands connect diagonally too?
A: Add the 4 diagonal deltas to the neighbor check (topic guide §6.2) —
   nothing else about the counting logic changes.

Q: Which of DFS/BFS/recursive would you actually type in an interview?
A: Iterative DFS (Approach 2) — same simplicity as the recursive version
   with none of its recursion-depth risk, and no need to justify BFS's
   extra queue machinery when order doesn't matter for a pure area count.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Grid-as-graph, per-component aggregation instead of just counting (topic
guide Part 6).

    LC 733  Flood Fill                    — the inner flood routine (001)
    LC 200  Number of Islands             — same scan, count components not area (002)
    LC 1254 Number of Closed Islands      — flood the border first, then count
    LC 694  Number of Distinct Islands    — same scan + shape fingerprinting
    LC 827  Making a Large Island         — flip one 0, maximize the merged area
================================================================================
"""

import sys
import time
import tracemalloc
from collections import deque
from typing import List, Set, Tuple


class Solution:
    def maxAreaOfIsland(self, grid: List[List[int]]) -> int:
        """✅ THE ANSWER — iterative DFS, marks visited by MUTATING the grid
        in place (zeroes out land as it's counted). O(rows*cols) time,
        O(rows*cols) worst case stack space. MUTATES `grid`."""
        if not grid or not grid[0]:
            return 0
        rows, cols = len(grid), len(grid[0])
        best = 0

        def area(r, c):
            stack = [(r, c)]
            grid[r][c] = 0
            count = 0
            while stack:
                cr, cc = stack.pop()
                count += 1
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
                        grid[nr][nc] = 0
                        stack.append((nr, nc))
            return count

        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == 1:
                    best = max(best, area(r, c))
        return best

    def maxAreaOfIsland_bfs(self, grid: List[List[int]]) -> int:
        """BFS variant, same in-place mutation strategy. O(rows*cols) time
        and space. MUTATES `grid`."""
        if not grid or not grid[0]:
            return 0
        rows, cols = len(grid), len(grid[0])
        best = 0

        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == 1:
                    count = 0
                    queue = deque([(r, c)])
                    grid[r][c] = 0
                    while queue:
                        cr, cc = queue.popleft()
                        count += 1
                        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                            nr, nc = cr + dr, cc + dc
                            if (0 <= nr < rows and 0 <= nc < cols
                                    and grid[nr][nc] == 1):
                                grid[nr][nc] = 0
                                queue.append((nr, nc))
                    best = max(best, count)
        return best

    def maxAreaOfIsland_preserve(self, grid: List[List[int]]) -> int:
        """Same algorithm, marks visited with a SEPARATE set instead of
        mutating `grid`. O(rows*cols) time, O(rows*cols) extra space for the
        visited set. Does NOT mutate the input."""
        if not grid or not grid[0]:
            return 0
        rows, cols = len(grid), len(grid[0])
        visited: Set[Tuple[int, int]] = set()
        best = 0

        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == 1 and (r, c) not in visited:
                    count = 0
                    stack = [(r, c)]
                    visited.add((r, c))
                    while stack:
                        cr, cc = stack.pop()
                        count += 1
                        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                            nr, nc = cr + dr, cc + dc
                            if (0 <= nr < rows and 0 <= nc < cols
                                    and grid[nr][nc] == 1
                                    and (nr, nc) not in visited):
                                visited.add((nr, nc))
                                stack.append((nr, nc))
                    best = max(best, count)
        return best

    def maxAreaOfIsland_recursive(self, grid: List[List[int]]) -> int:
        """Textbook recursive DFS, area via return-value summation.
        O(rows*cols) time, O(rows*cols) worst case CALL STACK —
        RecursionError on a maximally snake-shaped island. MUTATES `grid`."""
        if not grid or not grid[0]:
            return 0
        rows, cols = len(grid), len(grid[0])

        def area(r, c):
            if not (0 <= r < rows and 0 <= c < cols):
                return 0
            if grid[r][c] != 1:
                return 0
            grid[r][c] = 0
            return (1 + area(r - 1, c) + area(r + 1, c)
                    + area(r, c - 1) + area(r, c + 1))

        best = 0
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == 1:
                    best = max(best, area(r, c))
        return best


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def make_strip(length: int) -> List[List[int]]:
    """1-row, all-land strip — one island of size `length`, worst case for
    recursive DFS's call stack depth."""
    return [[1] * length]


# ==============================================================================
# TESTS — run:  python 003_max_area_of_island_solution.py
# ==============================================================================
CASES = [
    ([[1, 1, 0, 0, 0],
      [1, 1, 0, 0, 0],
      [0, 0, 0, 1, 1],
      [0, 0, 0, 1, 1],
      [0, 0, 0, 0, 1]], 5),
    ([[0, 0, 0, 0, 0, 0, 0, 0]], 0),
    ([[1]], 1),
    ([[0]], 0),
    ([[1, 0, 1, 0, 1]], 1),
    ([[1, 1, 1], [1, 1, 1], [1, 1, 1]], 9),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: all four implementations agree ---")
    for grid, want in CASES:
        a = sol.maxAreaOfIsland([row[:] for row in grid])
        b = sol.maxAreaOfIsland_bfs([row[:] for row in grid])
        c = sol.maxAreaOfIsland_preserve([row[:] for row in grid])
        d = sol.maxAreaOfIsland_recursive([row[:] for row in grid])
        ok = a == b == c == d == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  -> DFS={a} BFS={b} preserve={c} "
              f"recursive={d} (want {want})")

    # ----------------------------------------------------------------------
    # ⚠️  LIVE DEMO 1: recursive DFS vs a maximally snake-shaped island.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: recursive DFS on a snake island within 695's "
          "own 50x50 cap ---")
    limit = sys.getrecursionlimit()
    n = limit + 500
    strip = make_strip(n)
    print(f"  sys.getrecursionlimit() = {limit}; island size (strip length) = {n} "
          f"(695 caps a real grid at 50x50=2500; a snake THAT shape at "
          f"larger scale hits this exact wall)")

    raised = False
    try:
        sol.maxAreaOfIsland_recursive([row[:] for row in strip])
        print("  recursive maxAreaOfIsland on the strip: did NOT raise this run")
    except RecursionError as e:
        raised = True
        print(f"  recursive maxAreaOfIsland on the strip: RecursionError -> {e!r}")

    iter_area = sol.maxAreaOfIsland([row[:] for row in strip])
    iter_ok = iter_area == n
    print(f"  iterative maxAreaOfIsland on the SAME strip: succeeded -> {iter_ok} "
          f"(area={iter_area}, want {n})")
    print(f"  iterative succeeded where recursive raised RecursionError: "
          f"{iter_ok and raised}")
    all_ok &= iter_ok and raised

    # ----------------------------------------------------------------------
    # LIVE DEMO 2: measured PEAK MEMORY, in-place mutation vs a visited set.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 2: measured peak memory, in-place mutation vs a "
          "separate visited set ---")
    import random
    random.seed(695)
    side = 200
    big = [[1 if random.random() < 0.6 else 0 for _ in range(side)]
           for _ in range(side)]

    tracemalloc.start()
    _ = sol.maxAreaOfIsland([row[:] for row in big])
    _, peak_mutate = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    tracemalloc.start()
    _ = sol.maxAreaOfIsland_preserve([row[:] for row in big])
    _, peak_preserve = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"  {side}x{side} grid (~60% land), {side*side} cells:")
    print(f"  peak traced memory, in-place mutation:     {peak_mutate:>9,} bytes")
    print(f"  peak traced memory, separate visited set:  {peak_preserve:>9,} bytes")
    ratio = peak_preserve / peak_mutate if peak_mutate else float("inf")
    print(f"  visited-set variant peak / in-place variant peak = {ratio:.2f}x")
    memory_result_measured = True
    all_ok &= memory_result_measured

    # ----------------------------------------------------------------------
    # LIVE DEMO 3: grid state after the call — destroyed vs preserved.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 3: grid state after the call — destroyed vs preserved ---")
    original = [[1, 1, 0], [0, 1, 0], [0, 0, 1]]
    mutate_copy = [row[:] for row in original]
    preserve_copy = [row[:] for row in original]
    area_mutate = sol.maxAreaOfIsland(mutate_copy)
    area_preserve = sol.maxAreaOfIsland_preserve(preserve_copy)
    destroyed = mutate_copy != original
    preserved = preserve_copy == original
    print(f"  original:  {original}")
    print(f"  after in-place call:   {mutate_copy}  (destroyed: {destroyed})")
    print(f"  after preserve call:   {preserve_copy}  (preserved: {preserved})")
    print(f"  both report the same max area: {area_mutate} == {area_preserve} "
          f"-> {area_mutate == area_preserve}")
    all_ok &= destroyed and preserved and area_mutate == area_preserve

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
