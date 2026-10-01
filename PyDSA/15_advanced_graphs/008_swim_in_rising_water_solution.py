"""
================================================================================
SOLUTION · LeetCode 778 · Swim in Rising Water                          [Hard]
https://leetcode.com/problems/swim-in-rising-water/
================================================================================

THE CORE IDEA
--------------
The answer is the smallest T such that a path from (0,0) to (n-1,n-1)
exists using only cells with elevation <= T -- i.e., minimize the MAXIMUM
cell elevation along the path. Same minimax shape as problem 006, with the
cost attached to NODES (a cell's own elevation) rather than edges: when
you step onto a cell, your running "time so far" becomes
max(time so far, that cell's elevation).

    cost[0][0] = grid[0][0]
    heap = [(grid[0][0], 0, 0)]
    while heap:
        t, r, c = pop smallest
        if t > cost[r][c]: continue                # stale entry
        if (r,c) == target: return t
        for nr, nc in neighbors(r, c):
            nt = max(t, grid[nr][nc])
            if nt < cost[nr][nc]:
                cost[nr][nc] = nt; push (nt, nr, nc)

O(n^2 log(n^2)) time, O(n^2) space.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, name it and reject it): simulate t = 0, 1, 2, ...
one integer at a time; at each t, BFS/DFS to check if (n-1,n-1) is
reachable using only cells with elevation <= t; stop at the first t that
works. Correct, but O(n^2) possible values of t (elevations range up to
n^2-1), each with an O(n^2) traversal -- O(n^4) worst case. This is
"linear search on the answer" where the topic guide's binary-search
family (Approach 2 below) gets the same result in log time instead.

Approach 1 (minimax Dijkstra, node-weighted) [checked] -- the answer
above. O(n^2 log(n^2)) time, O(n^2) space.

Approach 2 (binary search on T + BFS/DFS feasibility) -- binary search
over T in [0, n^2 - 1]; `feasible(T)` = "is (0,0) connected to
(n-1,n-1) using only cells with elevation <= T AND grid[0][0] <= T"
checked with plain BFS/DFS. O(n^2 log(n^2)) -- same order as Dijkstra,
Family-B "search on the answer" from the binary search topic (§1.1),
applied here to a grid feasibility predicate.

Approach 3 (Union-Find on cells sorted by elevation, Kruskal-flavored)
[implemented below] -- sort every cell by its OWN elevation ascending.
Process cells in that order (this simulates "water level rising to exactly
this cell's elevation"); when a cell is processed, union it with any
already-processed 4-adjacent neighbor (both must have elevation <= current
level to be swimmable at this water level). The answer is the elevation of
the cell being processed at the moment (0,0) and (n-1,n-1) FIRST land in
the same Union-Find set. O(n^2 log(n^2)) for the sort, same order as
Dijkstra -- this is exactly the connection named in problem 006's
follow-ups: "smallest threshold that connects two specific nodes" is a
Kruskal's-shaped question whenever the graph edges (or here, node
activations) come with a natural weight ordering.


================================================================================
STEP BY STEP TRACE
================================================================================
grid = [[0,2],
        [1,3]]
target = (1,1)

cost = [[inf,inf],[inf,inf]]; cost[0][0] = grid[0][0] = 0
heap = [(0, 0,0)]

pop (0, 0,0): t=0 matches cost[0][0]=0. Not target. Relax neighbors:
    (0,1): grid=2, nt = max(0,2) = 2 < inf -> cost[0][1]=2, push (2,0,1)
    (1,0): grid=1, nt = max(0,1) = 1 < inf -> cost[1][0]=1, push (1,1,0)
heap = [(1,1,0), (2,0,1)]

pop (1, 1,0): t=1 matches. Not target. Relax neighbors:
    (0,0): already 0, no improvement.
    (1,1): grid=3, nt = max(1,3) = 3 < inf -> cost[1][1]=3, push (3,1,1)
heap = [(2,0,1), (3,1,1)]

pop (2, 0,1): t=2 matches. Not target. Relax neighbors:
    (0,0): no improvement.
    (1,1): grid=3, nt = max(2,3) = 3, NOT < cost[1][1]=3 (equal, not
           strictly less) -> no update, no duplicate push.
heap = [(3,1,1)]

pop (3, 1,1): t=3 matches cost[1][1]=3. This IS the target -> return 3.
              MATCHES expected output.

The path (0,0)=0 -> (1,0)=1 -> (1,1)=3 has running max 0,1,3 -> 3. The
alternative (0,0)=0 -> (0,1)=2 -> (1,1)=3 has running max 0,2,3 -> also 3
-- two different routes, same optimal answer, exactly the kind of tie
Dijkstra doesn't need to care about (any shortest/optimal route is fine).


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time                Space  Mutates input?
    -------------------------------------  ------------------  -----  --------------
    Linear search on T + BFS per t          O(n^4)              O(n^2) no
    Minimax Dijkstra, node-weighted [chos.] O(n^2 log(n^2))     O(n^2)  no
    Binary search on T + BFS feasibility     O(n^2 log(n^2))    O(n^2)  no
    Union-Find on cells sorted by elevation  O(n^2 log(n^2))    O(n^2)  no


================================================================================
EDGE CASES
================================================================================
    n == 1                     -> source IS target; answer is simply
                                   grid[0][0] (you must at least "arrive" at
                                   time equal to your own starting elevation).
    grid[0][0] is the LARGEST    -> still legal: the answer can never be
    elevation in the grid          smaller than grid[0][0] (Dijkstra's
                                   initialization already encodes this by
                                   seeding cost[0][0] = grid[0][0], not 0).
    all elevations already form   -> answer degenerates to
    a monotone increasing path       max(grid[0][0], grid[n-1][n-1]) along
    from source to target            that trivial path if it's also optimal.
    a grid requiring detour       -> Example 2: the "obvious" diagonal-ish
    around high elevations           path is blocked by higher elevations,
                                   forcing a longer detour with a SMALLER
                                   max elevation than the direct route would
                                   have -- exactly what the algorithm is
                                   built to discover.
    elevations are a permutation  -> guaranteed unique per constraints,
    of 0..n^2-1                     which is exactly what makes the
                                   Union-Find-by-elevation-order approach
                                   (Approach 3) unambiguous: there's a
                                   single well-defined order to process
                                   cells in.


================================================================================
COMMON MISTAKES
================================================================================
1. Seeding `cost[0][0] = 0` instead of `grid[0][0]`. The starting cell's
   OWN elevation is part of the answer -- you cannot "arrive" at (0,0)
   before the water has risen to at least its elevation. Demoed live below.

2. Relaxing with the EDGE weight (height DIFFERENCE between cells, like
   problem 006) instead of the NEIGHBOR's own elevation. This problem's
   cost is attached to NODES, not edges -- confusing the two problems'
   cost models produces a plausible-looking but wrong number.

3. In the Union-Find-by-elevation approach, unioning a newly-activated
   cell with a neighbor that has NOT yet been activated (i.e., whose
   elevation is still above the current water level) -- that neighbor
   isn't actually swimmable yet; only union with ALREADY-processed
   (lower-or-equal elevation) neighbors.

4. Off-by-one in when to check "have source and target connected yet" in
   the Union-Find approach -- checking BEFORE processing the current
   cell's unions (rather than after) can report the answer one elevation
   level too early or too late.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How does this relate to problem 006 (Path With Minimum Effort)?
A: Same minimax-path shape, different cost model: 006's cost lives on
   EDGES (|height difference| between adjacent cells), this problem's cost
   lives on NODES (a cell's own elevation, since "can I be here yet"
   depends only on whether the water has risen to this cell's height).
   Both admit the same three solution angles (minimax Dijkstra, binary
   search + BFS, Union-Find on sorted weights).

Q: Why does Union-Find work here at all -- isn't this a shortest-path
   problem?
A: It's really "smallest threshold connecting two specific nodes," which
   is Kruskal's MST question in disguise: process potential connections
   in ascending weight order, and stop the instant source and target land
   in the same component. You don't need the FULL MST, just the one
   moment the two specific nodes you care about first merge.

Q: What if diagonal moves were also allowed?
A: Extend the neighbor generator to 8 directions instead of 4 -- the
   algorithm itself is unchanged; only the "which cells are adjacent"
   definition changes.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 1631 Path With Minimum Effort (006 -- the edge-weighted sibling of
            this exact minimax shape)
    LC 1102 Path With Maximum Minimum Value (mirror image: maximize the
            minimum value along a path)
    LC 1631 / 778 together form the canonical "minimax Dijkstra" pair many
            interviewers draw from
    LC 1697 Checking Existence of Edge Length Limited Paths (Union-Find on
            sorted edge weights, offline queries -- same Kruskal's-flavored
            "smallest threshold" idea as Approach 3)
================================================================================
"""

import heapq
from typing import List


class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: int, y: int) -> bool:
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
        return True


class Solution:
    def swimInWater(self, grid: List[List[int]]) -> int:
        """✅ Minimax Dijkstra, node-weighted. O(n^2 log(n^2)) time,
        O(n^2) space."""
        n = len(grid)
        if n == 1:
            return grid[0][0]

        cost = [[float('inf')] * n for _ in range(n)]
        cost[0][0] = grid[0][0]
        heap = [(grid[0][0], 0, 0)]

        while heap:
            t, r, c = heapq.heappop(heap)
            if t > cost[r][c]:                  # stale entry
                continue
            if (r, c) == (n - 1, n - 1):
                return t
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n:
                    nt = max(t, grid[nr][nc])
                    if nt < cost[nr][nc]:
                        cost[nr][nc] = nt
                        heapq.heappush(heap, (nt, nr, nc))
        return -1   # unreachable given a fully connected grid

    def swimInWater_union_find(self, grid: List[List[int]]) -> int:
        """Alternative: Union-Find on cells sorted by elevation ascending
        (Kruskal's-flavored). O(n^2 log(n^2)) time, O(n^2) space."""
        n = len(grid)
        if n == 1:
            return grid[0][0]

        cells = sorted(((grid[r][c], r, c) for r in range(n) for c in range(n)))
        uf = UnionFind(n * n)
        activated = [[False] * n for _ in range(n)]

        def idx(r: int, c: int) -> int:
            return r * n + c

        for elevation, r, c in cells:
            activated[r][c] = True
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n and activated[nr][nc]:
                    uf.union(idx(r, c), idx(nr, nc))
            if uf.find(idx(0, 0)) == uf.find(idx(n - 1, n - 1)):
                return elevation
        return -1

    def swimInWater_zero_seed_BROKEN(self, grid: List[List[int]]) -> int:
        """✗ BROKEN ON PURPOSE -- mistake #1. Seeds cost[0][0] = 0 instead
        of grid[0][0], ignoring that the starting cell's own elevation is
        part of the answer. Demoed live below."""
        n = len(grid)
        cost = [[float('inf')] * n for _ in range(n)]
        cost[0][0] = 0                          # BUG: should be grid[0][0]
        heap = [(0, 0, 0)]

        while heap:
            t, r, c = heapq.heappop(heap)
            if t > cost[r][c]:
                continue
            if (r, c) == (n - 1, n - 1):
                return t
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n:
                    nt = max(t, grid[nr][nc])
                    if nt < cost[nr][nc]:
                        cost[nr][nc] = nt
                        heapq.heappush(heap, (nt, nr, nc))
        return -1


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([[0, 2], [1, 3]], 3),
        ([[0, 1, 2, 3, 4], [24, 23, 22, 21, 5], [12, 13, 14, 15, 16],
          [11, 17, 18, 19, 20], [10, 9, 8, 7, 6]], 16),
        ([[0]], 0),
        ([[3, 2], [0, 1]], 3),
    ]

    print("--- correctness: Dijkstra vs Union-Find agree ---")
    for grid, want in cases:
        got_dij = sol.swimInWater([row[:] for row in grid])
        got_uf = sol.swimInWater_union_find([row[:] for row in grid])
        ok = got_dij == want and got_uf == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={len(grid)}  dij={got_dij} "
              f"uf={got_uf}  (want {want})")

    # --------------------------------------------------------------------
    # ⚠️ LIVE DEMO: seeding cost[0][0]=0 instead of grid[0][0].
    # --------------------------------------------------------------------
    print("\n--- ⚠️  live demo: mistake #1, seeding cost[0][0]=0 ---")
    grid = [[5, 2], [1, 3]]     # source elevation (5) EXCEEDS everything else
    correct = sol.swimInWater([row[:] for row in grid])
    broken = sol.swimInWater_zero_seed_BROKEN([row[:] for row in grid])
    print(f"  grid = {grid}  (source elevation 5 is the grid's MAXIMUM)")
    print(f"  correct (seeded with grid[0][0]):  {correct}")
    print(f"  broken  (seeded with 0):            {broken}")
    exposed = broken != correct
    print(f"  the broken version returns a time BEFORE the water has even "
          f"risen enough to let you leave the start: {exposed}")
    all_ok &= exposed and correct == 5

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
