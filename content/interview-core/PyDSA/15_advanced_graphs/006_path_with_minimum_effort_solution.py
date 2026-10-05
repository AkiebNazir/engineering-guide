"""
================================================================================
SOLUTION · LeetCode 1631 · Path With Minimum Effort                   [Medium]
https://leetcode.com/problems/path-with-minimum-effort/
================================================================================

THE CORE IDEA
--------------
The grid IS a graph -- cells are nodes, orthogonal neighbors are edges,
edge weight = |height difference|. The cost to MINIMIZE is a path's
MAXIMUM edge weight, not the sum -- a "minimax path" (topic guide Part 3).
Dijkstra's exact skeleton still applies: pop the frontier cell with the
smallest running effort-so-far, it is finalized (nothing farther-off can
ever produce something smaller), relax neighbors with `max` instead of `+`.

    effort = [[inf]*cols for _ in range(rows)]; effort[0][0] = 0
    heap = [(0, 0, 0)]
    while heap:
        e, r, c = pop smallest
        if e > effort[r][c]: continue          # stale entry, same as always
        if (r,c) == target: return e
        for nr, nc in neighbors(r, c):
            cost = max(e, abs(heights[r][c] - heights[nr][nc]))
            if cost < effort[nr][nc]:
                effort[nr][nc] = cost; push (cost, nr, nc)

O(R*C log(R*C)) time, O(R*C) space.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, name it and reject it): DFS/backtrack every path
from (0,0) to (R-1,C-1), track the max edge weight per path, keep the
smallest. Exponential -- a grid has exponentially many simple paths.

Approach 1 (minimax Dijkstra) [checked] -- the answer above.

Approach 2 (binary search on the answer + BFS/DFS feasibility check) --
binary search over candidate effort values E (0 to max height difference
in the grid); `feasible(E)` = "can I reach the target using only edges
with weight <= E?", checked with a plain BFS/DFS using edges filtered by
that threshold. O(R*C * log(max_height)) -- same ballpark as Dijkstra,
philosophically the topic guide's Family-B "search on the answer" move
(binary search topic, §1.1) applied to a graph feasibility predicate
instead of an array.

Approach 3 (Union-Find on edges sorted by weight, Kruskal-flavored) --
sort all grid edges by weight ascending, union them into a growing forest
one at a time; the answer is the weight of the edge whose addition FIRST
connects source and target (every edge added before that point has weight
<= the answer, by construction of the sort order). O(R*C log(R*C)) for the
sort, same order as Dijkstra. This is the same "smallest threshold that
connects two specific nodes" idea problem 008 (Swim in Rising Water) uses
explicitly -- worth naming the connection between the two problems.


================================================================================
STEP BY STEP TRACE
================================================================================
heights = [[1,2,2],
           [3,8,2],
           [5,3,5]]
target = (2,2)

effort = [[0,inf,inf],[inf,inf,inf],[inf,inf,inf]]
heap = [(0, 0,0)]

pop (0, 0,0): e=0 matches effort[0][0]=0. Relax neighbors (0,1) and (1,0):
    (0,1): cost = max(0, |1-2|)=1 < inf -> effort[0][1]=1, push (1,0,1)
    (1,0): cost = max(0, |1-3|)=2 < inf -> effort[1][0]=2, push (2,1,0)
heap = [(1,0,1), (2,1,0)]

pop (1, 0,1): e=1 matches. Relax (0,0)[already 0, no improvement], (0,2), (1,1):
    (0,2): cost = max(1, |2-2|)=1 < inf -> effort[0][2]=1, push (1,0,2)
    (1,1): cost = max(1, |2-8|)=6 < inf -> effort[1][1]=6, push (6,1,1)
heap = [(1,0,2), (2,1,0), (6,1,1)]

pop (1, 0,2): e=1 matches. Relax (1,2):
    (1,2): cost = max(1, |2-2|)=1 < inf -> effort[1][2]=1, push (1,1,2)
heap = [(1,1,2), (2,1,0), (6,1,1)]

pop (1, 1,2): e=1 matches. Relax (0,2)[no improve], (2,2), (1,1)[6, no improve since max(1,|2-8|)=6 not < 6]:
    (2,2): cost = max(1, |2-5|)=3 < inf -> effort[2][2]=3, push (3,2,2)
heap = [(2,1,0), (3,2,2), (6,1,1)]

pop (2, 1,0): e=2 matches. Relax (2,0), (1,1)[max(2,|3-8|)=5, not<6... wait 5<6 IS true]:
    (2,0): cost = max(2, |3-5|)=2 < inf -> effort[2][0]=2, push (2,2,0)
    (1,1): cost = max(2, |3-8|)=5 < 6 -> effort[1][1]=5, push (5,1,1)
heap = [(2,2,0), (3,2,2), (5,1,1), (6,1,1)]

pop (2, 2,0): e=2 matches. Relax (2,1):
    (2,1): cost = max(2, |5-3|)=2 < inf -> effort[2][1]=2, push (2,2,1)
heap = [(2,2,1), (3,2,2), (5,1,1), (6,1,1)]

pop (2, 2,1): e=2 matches. Relax (1,1)[max(2,|3-8|)=5, not<5], (2,2)[max(2,|3-5|)=2, < 3! improves]:
    (2,2): cost = max(2, |3-5|)=2 < 3 -> effort[2][2]=2, push (2,2,2)
heap = [(2,2,2), (3,2,2)(stale), (5,1,1), (6,1,1)(stale)]

pop (2, 2,2): e=2 matches effort[2][2]=2. This IS the target -> return 2.
              MATCHES expected output. (The stale (3,2,2) entry, if popped
              later, would be skipped by `e > effort[2][2]` -> 3 > 2.)

This traces the route 1(0,0) -> 3(1,0) -> 5(2,0) -> 3(2,1) -> 5(2,2): diffs
2,2,2,2 -> max effort 2, matching the problem's own explanation route
[1,3,5,3,5].


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time                  Space   Mutates input?
    -------------------------------------  --------------------  ------  --------------
    Brute-force DFS over all paths          exponential           O(R*C)  no
    Minimax Dijkstra [chosen]               O(R*C log(R*C))       O(R*C)  no
    Binary search + BFS feasibility          O(R*C log(maxH))      O(R*C)  no
    Union-Find on sorted edges               O(R*C log(R*C))       O(R*C)  no


================================================================================
EDGE CASES
================================================================================
    1x1 grid                   -> source == target already; effort 0
                                   trivially (no edges to traverse). Example
                                   handled naturally since the heap pops
                                   (0,0,0) and the "is this target" check
                                   fires immediately.
    a single row or column      -> only one possible simple path exists (no
                                   branching), so the answer is FORCED to be
                                   the max consecutive-cell difference along
                                   that one path -- the algorithm still
                                   works, it just has no real choice to make.
    all heights equal           -> every edge weight is 0 -> answer 0
                                   regardless of path (Example 3's flavor).
    very large height range     -> up to 10^6 per cell -> diffs up to
                                   ~10^6, well within a Python int / heap
                                   comparison, no overflow concern.
    grid has only one row AND   -> 1x1 case above; both conditions coincide.
    one column


================================================================================
COMMON MISTAKES
================================================================================
1. Relaxing with `d + w` (sum) instead of `max(d, w)` -- copy-pasting
   plain Dijkstra without adapting the cost function to what THIS problem
   actually asks for (max edge weight on the path, not total weight).
   Silently computes the wrong quantity, no exception, plausible-looking
   number. Demoed live below.

2. Forgetting the stale-entry guard (`if e > effort[r][c]: continue`).
   Still terminates correctly (the trace above shows a stale (3,2,2) entry
   safely ignored), but skipping the guard means the heap can carry
   redundant entries for nodes whose effort has already improved,
   inflating heap operations.

3. Returning as soon as the TARGET COORDINATES are first pushed onto the
   heap, rather than when they are POPPED (and validated against the
   stale-entry guard). A push is only a candidate; only a pop with a
   non-stale distance is a confirmed final answer for that cell -- exactly
   the same principle plain Dijkstra relies on.

4. Off-by-one in neighbor generation -- forgetting bounds checks
   (`0 <= nr < rows and 0 <= nc < cols`) causes an IndexError, or checking
   only 2 of the 4 directions (e.g., only right/down) which silently
   restricts the search to monotone paths and can miss the true minimum
   when backtracking through a "cheaper but longer" route is required.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Could you solve this with binary search instead of Dijkstra?
A: Yes -- binary search over candidate effort values (0 to the grid's max
   height difference), and for each candidate E run a plain BFS/DFS using
   only edges with weight <= E to test reachability from source to target.
   O(R*C * log(max_height)) -- same order as Dijkstra, different mechanism
   (topic guide Part 3 names this explicitly).

Q: How does this relate to problem 008 (Swim in Rising Water)?
A: Structurally identical -- both ask for the smallest threshold T such
   that a path exists using only edges/cells with weight <= T. 008's
   Union-Find/Kruskal-flavored solution (Approach 3 above) is a third
   valid angle on both problems.

Q: What if the grid were much larger, say 10^5 x 10^5?
A: R*C would be ~10^10 -- infeasible for any of these approaches; a truly
   massive grid needs a fundamentally different technique (e.g., an
   A*-style heuristic search, or streaming/tiling), well beyond interview
   scope -- worth flagging the scaling limit rather than pretending
   Dijkstra scales indefinitely.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 778  Swim in Rising Water (008 -- the same minimax-path shape, three
            interchangeable solution angles)
    LC 743  Network Delay Time (003 -- Dijkstra's SUM-cost sibling)
    LC 1102 Path With Maximum Minimum Value (the mirror image: MAXIMIZE the
            MINIMUM edge weight along a path -- same skeleton, flipped)
    LC 1368 Minimum Cost to Make at Least One Valid Path in a Grid
            (0-1 BFS variant of grid-as-graph shortest path)
================================================================================
"""

import heapq
from typing import List


class Solution:
    def minimumEffortPath(self, heights: List[List[int]]) -> int:
        """✅ Minimax Dijkstra. O(R*C log(R*C)) time, O(R*C) space."""
        rows, cols = len(heights), len(heights[0])
        if rows == 1 and cols == 1:
            return 0

        effort = [[float('inf')] * cols for _ in range(rows)]
        effort[0][0] = 0
        heap = [(0, 0, 0)]

        while heap:
            e, r, c = heapq.heappop(heap)
            if e > effort[r][c]:                # stale entry
                continue
            if (r, c) == (rows - 1, cols - 1):
                return e
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    cost = max(e, abs(heights[r][c] - heights[nr][nc]))
                    if cost < effort[nr][nc]:
                        effort[nr][nc] = cost
                        heapq.heappush(heap, (cost, nr, nc))
        return 0   # unreachable given a fully connected grid

    def minimumEffortPath_binary_search_bfs(self, heights: List[List[int]]) -> int:
        """Alternative: binary search on the answer + BFS feasibility
        check. O(R*C log(max_height)) time, O(R*C) space."""
        from collections import deque

        rows, cols = len(heights), len(heights[0])
        if rows == 1 and cols == 1:
            return 0

        def feasible(limit: int) -> bool:
            visited = [[False] * cols for _ in range(rows)]
            visited[0][0] = True
            queue = deque([(0, 0)])
            while queue:
                r, c = queue.popleft()
                if (r, c) == (rows - 1, cols - 1):
                    return True
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < rows and 0 <= nc < cols and not visited[nr][nc]
                            and abs(heights[r][c] - heights[nr][nc]) <= limit):
                        visited[nr][nc] = True
                        queue.append((nr, nc))
            return False

        lo, hi = 0, max(max(row) for row in heights)
        while lo < hi:
            mid = (lo + hi) // 2
            if feasible(mid):
                hi = mid
            else:
                lo = mid + 1
        return lo

    def minimumEffortPath_sum_relax_BROKEN(self, heights: List[List[int]]) -> int:
        """✗ BROKEN ON PURPOSE -- mistake #1. Uses SUM-of-edges relaxation
        (plain Dijkstra) instead of MAX-of-edges, computing total path
        weight instead of the path's maximum single edge. Demoed live
        below."""
        rows, cols = len(heights), len(heights[0])
        dist = [[float('inf')] * cols for _ in range(rows)]
        dist[0][0] = 0
        heap = [(0, 0, 0)]
        while heap:
            d, r, c = heapq.heappop(heap)
            if d > dist[r][c]:
                continue
            if (r, c) == (rows - 1, cols - 1):
                return d
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    nd = d + abs(heights[r][c] - heights[nr][nc])  # SUM -- BUG
                    if nd < dist[nr][nc]:
                        dist[nr][nc] = nd
                        heapq.heappush(heap, (nd, nr, nc))
        return 0


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([[1, 2, 2], [3, 8, 2], [5, 3, 5]], 2),
        ([[1, 2, 3], [3, 8, 4], [5, 3, 5]], 1),
        ([[1, 2, 1, 1, 1], [1, 2, 1, 2, 1], [1, 2, 1, 2, 1],
          [1, 2, 1, 2, 1], [1, 1, 1, 2, 1]], 0),
        ([[1]], 0),
        ([[1, 10, 6, 7, 9, 10, 4, 9]], 9),
    ]

    print("--- correctness: minimax Dijkstra vs binary-search+BFS agree ---")
    for heights, want in cases:
        got_dij = sol.minimumEffortPath([row[:] for row in heights])
        got_bs = sol.minimumEffortPath_binary_search_bfs([row[:] for row in heights])
        ok = got_dij == want and got_bs == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {len(heights)}x{len(heights[0])} "
              f"dij={got_dij} bs={got_bs}  (want {want})")

    # --------------------------------------------------------------------
    # ⚠️ LIVE DEMO: sum-relax vs max-relax on the worked example.
    # --------------------------------------------------------------------
    print("\n--- ⚠️  live demo: mistake #1, sum-relax instead of max-relax ---")
    heights = [[1, 2, 2], [3, 8, 2], [5, 3, 5]]
    correct = sol.minimumEffortPath([row[:] for row in heights])
    broken = sol.minimumEffortPath_sum_relax_BROKEN([row[:] for row in heights])
    print(f"  heights = {heights}")
    print(f"  correct (max-relax, true 'effort'):  {correct}")
    print(f"  broken (sum-relax, total path cost):  {broken}")
    exposed = broken != correct
    print(f"  the broken version silently returns TOTAL path weight instead "
          f"of the MAXIMUM edge on the path: {exposed}  (no exception raised, "
          f"both look like plausible integers)")
    all_ok &= exposed and correct == 2

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
