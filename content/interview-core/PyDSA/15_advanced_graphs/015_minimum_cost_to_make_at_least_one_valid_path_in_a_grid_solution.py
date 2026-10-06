"""
================================================================================
SOLUTION · LeetCode 1368 · Minimum Cost to Make at Least One Valid Path   [Hard]
https://leetcode.com/problems/minimum-cost-to-make-at-least-one-valid-path-in-a-grid/
================================================================================

THE CORE IDEA
--------------
Shortest path on a grid graph with edge weights 0 (follow the sign) or 1
(change the sign). That's the textbook case for 0-1 BFS: a deque where
0-weight relaxations go to the FRONT and 1-weight relaxations go to the BACK.
The deque then always holds nodes in non-decreasing distance order, exactly
like Dijkstra's heap, but each operation is O(1).


================================================================================
APPROACH 1 · Dijkstra with a heap
================================================================================
Standard Dijkstra over m*n nodes with 4 edges each.

    Time: O(mn log(mn))    Space: O(mn)

Always correct for non-negative weights. A perfectly good interview answer;
mention 0-1 BFS as the optimization.


================================================================================
APPROACH 2 · 0-1 BFS with a deque ✅ (the answer)
================================================================================
    DIRS = [(0, 1), (0, -1), (1, 0), (-1, 0)]      # sign 1, 2, 3, 4
    dist = [[inf] * n for _ in range(m)]
    dist[0][0] = 0
    dq = deque([(0, 0)])
    while dq:
        i, j = dq.popleft()
        for s, (di, dj) in enumerate(DIRS, start=1):
            ni, nj = i + di, j + dj
            if 0 <= ni < m and 0 <= nj < n:
                cost = 0 if grid[i][j] == s else 1
                if dist[i][j] + cost < dist[ni][nj]:
                    dist[ni][nj] = dist[i][j] + cost
                    if cost == 0: dq.appendleft((ni, nj))
                    else:         dq.append((ni, nj))
    return dist[m - 1][n - 1]

WHY THE DEQUE STAYS SORTED. Invariant: the deque holds distances from at most
two consecutive values, D at the front part and D + 1 at the back part. Popping
a node at distance D pushes 0-edges (distance D) to the front and 1-edges
(distance D + 1) to the back. The invariant holds, so nodes leave the deque in
non-decreasing distance order, which is Dijkstra's key property.

A node may be pushed more than once (when relaxed again with a smaller
distance). Stale copies just fail the relaxation check when popped.

WHY "CHANGE ONCE PER CELL" DOESN'T MATTER. A shortest path never revisits a
cell (cutting out the loop can't increase cost), so each cell's sign is changed
at most once anyway.

    Time: O(mn) — each node is pushed at most a few times, 4 edges each
    Space: O(mn)


================================================================================
APPROACH 3 · DFS-flood + BFS by layers
================================================================================
Cost 0: flood-fill every cell reachable by following signs from the current
frontier. Cost 1: from all flooded cells, take one "changed" step to each
neighbor, then flood again. Repeat until the target is flooded. Same O(mn),
different shape; it's 0-1 BFS written as layers.


================================================================================
STEP BY STEP TRACE · grid = [[1,2],[4,3]]
================================================================================
        (0,0)=→  (0,1)=←
        (1,0)=↑  (1,1)=↓

    dist (0,0)=0, deque [(0,0)]
    pop (0,0) d=0:
        right (0,1): sign 1 matches -> cost 0 -> dist 0, push FRONT
        down  (1,0): cost 1 -> dist 1, push BACK
    deque [(0,1), (1,0)]
    pop (0,1) d=0:
        left (0,0): 0+0 not < 0
        down (1,1): cost 1 -> dist 1, push BACK
    pop (1,0) d=1: right (1,1): 1+1 not < 1 ...
    pop (1,1) d=1: target distance 1

    answer: 1   (change (0,1) from ← to ↓)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                 Time            Space   Mutates input?
    -----------------------  --------------  ------  --------------
    Plain BFS (WRONG)        O(mn)           O(mn)   —
    Dijkstra (heap)          O(mn log mn)    O(mn)   No
    0-1 BFS ✅               O(mn)           O(mn)   No
    Flood + layer BFS        O(mn)           O(mn)   No


================================================================================
EDGE CASES
================================================================================
    1x1 grid               0 — already at the target.
    Signs point outside    Those moves are skipped; you pay 1 to redirect.
    Already valid path     0.
    All signs away         Worst case cost m + n - 2 (a monotone path).


================================================================================
COMMON MISTAKES
================================================================================
1. Plain BFS with a visited-on-enqueue set. It treats the grid as unweighted
   and finalizes cells too early. Demo below: wrong on random grids.

2. Pushing BOTH 0- and 1-cost neighbors to the back (a regular queue with
   relaxation). Still correct eventually (it becomes Bellman-Ford-like SPFA),
   but loses the linear bound.

3. Mapping sign numbers to directions in the wrong order. 1 right, 2 left,
   3 down, 4 up.

4. Marking a node "done" when pushed instead of when popped with its final
   distance.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Changing a sign costs different amounts per cell?
A: General non-negative weights: Dijkstra.

Q: Weights are small integers 0..K?
A: Dial's algorithm: an array of K + 1 buckets used circularly. O(E + V * K).

Q: Where else does 0-1 BFS show up?
A: Minimum Obstacle Removal (LC 2290), shortest paths where some moves are
   free (teleports, following a conveyor), and minimum edge reversals to make
   a path in a directed graph.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 2290  Minimum Obstacle Removal to Reach Corner — 0-1 BFS
    LC 1631  Path With Minimum Effort (006)           — Dijkstra / binary search
    LC 743   Network Delay Time (003)                 — Dijkstra
    LC 752   Open the Lock (14_graphs/018)            — plain BFS, all weights 1
================================================================================
"""

import heapq
import random
import time
from collections import deque
from typing import List

DIRS = [(0, 1), (0, -1), (1, 0), (-1, 0)]   # sign 1, 2, 3, 4


class Solution:
    def minCost(self, grid: List[List[int]]) -> int:
        m, n = len(grid), len(grid[0])
        INF = float("inf")
        dist = [[INF] * n for _ in range(m)]
        dist[0][0] = 0
        dq = deque([(0, 0)])
        while dq:
            i, j = dq.popleft()
            d = dist[i][j]
            sign = grid[i][j]
            for s, (di, dj) in enumerate(DIRS, start=1):
                ni, nj = i + di, j + dj
                if 0 <= ni < m and 0 <= nj < n:
                    cost = 0 if sign == s else 1
                    if d + cost < dist[ni][nj]:
                        dist[ni][nj] = d + cost
                        if cost == 0:
                            dq.appendleft((ni, nj))
                        else:
                            dq.append((ni, nj))
        return dist[m - 1][n - 1]


# ------------------------------------------------------------------------
# Alternatives / broken version for the demos.
# ------------------------------------------------------------------------
def min_cost_dijkstra(grid: List[List[int]]) -> int:
    m, n = len(grid), len(grid[0])
    dist = [[float("inf")] * n for _ in range(m)]
    dist[0][0] = 0
    heap = [(0, 0, 0)]
    while heap:
        d, i, j = heapq.heappop(heap)
        if d > dist[i][j]:
            continue
        for s, (di, dj) in enumerate(DIRS, start=1):
            ni, nj = i + di, j + dj
            if 0 <= ni < m and 0 <= nj < n:
                nd = d + (0 if grid[i][j] == s else 1)
                if nd < dist[ni][nj]:
                    dist[ni][nj] = nd
                    heapq.heappush(heap, (nd, ni, nj))
    return dist[m - 1][n - 1]


def min_cost_plain_bfs_bug(grid: List[List[int]]) -> int:
    """Mistake 1: FIFO BFS, cell finalized the first time it's reached."""
    m, n = len(grid), len(grid[0])
    dist = [[-1] * n for _ in range(m)]
    dist[0][0] = 0
    q = deque([(0, 0)])
    while q:
        i, j = q.popleft()
        for s, (di, dj) in enumerate(DIRS, start=1):
            ni, nj = i + di, j + dj
            if 0 <= ni < m and 0 <= nj < n and dist[ni][nj] == -1:
                dist[ni][nj] = dist[i][j] + (0 if grid[i][j] == s else 1)
                q.append((ni, nj))
    return dist[m - 1][n - 1]


# ==============================================================================
# TESTS — run:  python 015_minimum_cost_to_make_at_least_one_valid_path_in_a_grid_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: 0-1 BFS vs Dijkstra ---")
    big = [[3, 4, 3], [2, 2, 2], [2, 1, 1], [4, 3, 2], [2, 1, 4], [2, 4, 1], [3, 3, 3], [1, 4, 2], [2, 2, 1],
           [2, 1, 1], [3, 3, 1], [4, 1, 4], [2, 1, 4], [3, 2, 2], [3, 3, 1], [4, 4, 1], [1, 2, 2], [1, 1, 1],
           [1, 3, 4], [1, 2, 1], [2, 2, 4], [2, 1, 3], [1, 2, 1], [4, 3, 2], [3, 3, 4], [2, 2, 1], [3, 4, 3],
           [4, 2, 3], [4, 4, 4]]
    cases = [
        ([[1, 1, 1, 1], [2, 2, 2, 2], [1, 1, 1, 1], [2, 2, 2, 2]], 3),
        ([[1, 1, 3], [3, 2, 2], [1, 1, 4]], 0),
        ([[1, 2], [4, 3]], 1),
        ([[4]], 0),
        ([[2, 2, 2], [2, 2, 2]], 3),
        (big, 18),
    ]
    for grid, want in cases:
        a, b = sol.minCost(grid), min_cost_dijkstra(grid)
        ok = a == b == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {len(grid)}x{len(grid[0])}  0-1 BFS={a}  Dijkstra={b}  want={want}")

    print("\n--- randomized cross-check vs Dijkstra (500 grids) ---")
    rng = random.Random(1368)
    bad = 0
    bfs_wrong = 0
    example = None
    for _ in range(500):
        m, n = rng.randint(1, 8), rng.randint(1, 8)
        grid = [[rng.randint(1, 4) for _ in range(n)] for _ in range(m)]
        want = min_cost_dijkstra(grid)
        if sol.minCost(grid) != want:
            bad += 1
        if min_cost_plain_bfs_bug(grid) != want:
            bfs_wrong += 1
            if example is None or len(grid) * len(grid[0]) < len(example[0]) * len(example[0][0]):
                example = (grid, min_cost_plain_bfs_bug(grid), want)
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  500 random grids: 0-1 BFS matches Dijkstra")

    print("\n--- mistake 1 LIVE: plain FIFO BFS ---")
    ok = bfs_wrong > 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  plain BFS was wrong on {bfs_wrong} of the same 500 grids")
    if example:
        print(f"      smallest failing grid: {example[0]}")
        print(f"      plain BFS says {example[1]}, true minimum is {example[2]}")
        print("      BFS locks in the first cost that reaches a cell, even if a 0-cost route arrives later")

    print("\n--- benchmark: 100x100 (constraint max), random signs ---")
    grid = [[rng.randint(1, 4) for _ in range(100)] for _ in range(100)]
    for name, fn in (("Dijkstra (heap)", min_cost_dijkstra), ("0-1 BFS (deque)", sol.minCost)):
        t0 = time.perf_counter()
        for _ in range(5):
            r = fn(grid)
        dt = (time.perf_counter() - t0) / 5
        print(f"      {name}  {dt * 1000:6.1f} ms   cost={r}")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
