"""
================================================================================
SOLUTION · LeetCode 547 · Number of Provinces                        [Medium]
https://leetcode.com/problems/number-of-provinces/
================================================================================

THE CORE IDEA
--------------
A province is a connected component of the "is directly connected" graph.
Union every pair of directly-connected cities; the number of provinces is
the number of DISTINCT roots left standing once every union has happened.

    for i in range(n):
        for j in range(i + 1, n):
            if isConnected[i][j] == 1:
                uf.union(i, j)
    return number of i with uf.find(i) == i     # roots

O(n^2 * alpha(n)) time (scanning the upper triangle dominates; alpha(n) is
Union-Find's near-constant per-operation cost, see the topic guide §5),
O(n) space.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, name it and reject it): repeatedly compute the
transitive closure by squaring the adjacency matrix (Floyd-Warshall-style
reachability) until it stabilizes, then count identical rows. Correct,
O(n^3) or worse, and does far more work than the question needs.

Approach 1 (DFS/BFS flood fill) -- for every unvisited city, flood-fill its
whole component and mark it visited; count how many times a flood fill has
to start fresh. O(n^2) time (matrix has n^2 cells), O(n) space for the
visited set + recursion/queue. Fully correct and arguably simpler here --
worth naming as the alternative.

Approach 2 (Union-Find) [checked] -- the answer above. Chosen for this
folder because 002 needs the same structure for a genuinely different
purpose (checking equations are jointly satisfiable, not just counting
groups), and because Union-Find generalizes to a STREAM of edges (you don't
need the whole graph up front, unlike DFS/BFS) -- a property this exact
problem does not need but that shows up constantly in this topic (Kruskal's
MST, 011's edge inclusion/exclusion).


================================================================================
STEP BY STEP TRACE
================================================================================
isConnected = [[1,0,0,0],
               [0,1,0,0],
               [0,0,1,1],
               [0,0,1,1]]

Initial: parent = [0,1,2,3]   rank = [0,0,0,0]   (4 separate sets)

Scan upper triangle (i<j):
    (0,1)=0  (0,2)=0  (0,3)=0  (1,2)=0  (1,3)=0
    (2,3)=1  -> union(2,3): find(2)=2, find(3)=3, ranks equal (0==0) ->
               parent[3]=2, rank[2] becomes 1
               parent = [0,1,2,2]   rank = [0,0,1,0]

Roots left: find(0)=0, find(1)=1, find(2)=2, find(3)=2 (path-compressed
to 2 directly on next find). Distinct roots = {0, 1, 2} -> 3 provinces.

    province {0}   province {1}   province {2,3}


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                  Time              Space   Mutates input?
    -------------------------  ----------------  ------  --------------
    Matrix-squaring closure    O(n^3) or worse   O(n^2)  no
    DFS/BFS flood fill         O(n^2)            O(n)    no (uses visited set)
    Union-Find [chosen]        O(n^2 * alpha(n))  O(n)    no


================================================================================
EDGE CASES
================================================================================
    n == 1                  -> single city, always its own province. Answer 1.
    fully connected matrix  -> every union succeeds until one root remains.
                                Answer 1.
    fully disconnected      -> isConnected[i][j]==0 for all i != j (only the
                                diagonal is 1, per the problem's own
                                constraint isConnected[i][i]==1). No unions
                                happen. Answer n.
    isConnected[i][i] == 1  -> guaranteed by the constraints; iterating only
                                i<j means the diagonal is never even visited,
                                so it cannot cause a spurious self-union bug.
    disjoint clusters of different sizes -> the union-by-rank tree shape
                                differs per cluster; the ROOT COUNT, not the
                                tree shape, is what is graded.


================================================================================
COMMON MISTAKES
================================================================================
1. Scanning the full matrix (i in range(n), j in range(n)) instead of just
   i < j. Not wrong (union(i,j) and union(j,i) collapse to the same thing,
   and union(i,i) is a same-root no-op), but doubles the work for nothing.

2. Counting provinces as "n minus number of successful unions" -- true in
   this case, but fragile: it silently assumes every union call is being
   given a genuinely new edge. Counting DISTINCT ROOTS after the fact
   (`len({find(i) for i in range(n)})`) is the robust version and is what
   generalizes to 002, where "how many groups" is never the actual question.

3. Forgetting path compression in `find`. Still correct, just slower --
   worst case O(n) per find on a degenerate chain instead of near-O(1).

4. Using the RAW matrix as a visited-tracking structure for a DFS solution
   and forgetting cities can appear in their own row (`isConnected[i][i]`)
   -- an infinite self-loop trap if the recursion does not check
   `already visited` before recursing into `i` from `i`.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if the input were an edge list instead of an adjacency matrix?
A: Identical Union-Find code, just iterate the edge list directly instead
   of the upper triangle -- O(E * alpha(n)) instead of O(n^2), better when
   the graph is sparse (this is exactly LC 323, Number of Connected
   Components in an Undirected Graph).

Q: What if edges arrive one at a time, and you need the province count
   after each one (a live stream)?
A: This is precisely what Union-Find is built for and DFS/BFS is not --
   maintain a running "number of distinct roots" counter, decrement it by
   one every time `union` returns True (a merge actually happened).

Q: How would you list the cities in each province, not just count them?
A: Group `range(n)` by `find(i)` into a dict of lists -- one more O(n)
   pass after all unions are done.

Q: How much does path compression actually buy you?
A: Measured on this machine (4000-node worst-case chain, 5 passes finding
   every node): 1.66 ms WITH path compression vs 650.30 ms WITHOUT --
   about 393x. See the runtime demo below.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 323  Number of Connected Components (edge-list version of this exact
            problem)
    LC 990  Satisfiability of Equality Equations (002 -- Union-Find used to
            check consistency, not just count groups)
    LC 1319 Number of Operations to Make Network Connected (Union-Find +
            counting redundant edges)
    LC 1061 Lexicographically Smallest Equivalent String (Union-Find with a
            custom "smallest representative" merge rule)
================================================================================
"""

import time
from typing import List


class UnionFind:
    """Path compression + union by rank -- see topic guide Part 5."""

    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.components = n

    def find(self, x: int) -> int:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])   # path compression
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
        self.components -= 1
        return True


class UnionFindNoCompression:
    """Same interface, WITHOUT path compression -- used only to demonstrate
    the performance gap live in the demo below."""

    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            x = self.parent[x]
        return x

    def union(self, x: int, y: int) -> bool:
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        self.parent[ry] = rx          # always attach y under x -- no rank,
        return True                   # builds a long chain on purpose


class Solution:
    def findCircleNum(self, isConnected: List[List[int]]) -> int:
        """✅ Union-Find. O(n^2 * alpha(n)) time, O(n) space."""
        n = len(isConnected)
        uf = UnionFind(n)
        for i in range(n):
            for j in range(i + 1, n):
                if isConnected[i][j] == 1:
                    uf.union(i, j)
        return len({uf.find(i) for i in range(n)})

    def findCircleNum_dfs(self, isConnected: List[List[int]]) -> int:
        """Alternative: DFS flood fill. O(n^2) time, O(n) space."""
        n = len(isConnected)
        visited = [False] * n

        def dfs(city: int) -> None:
            visited[city] = True
            for neighbor in range(n):
                if isConnected[city][neighbor] == 1 and not visited[neighbor]:
                    dfs(neighbor)

        provinces = 0
        for city in range(n):
            if not visited[city]:
                provinces += 1
                dfs(city)
        return provinces


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([[1, 1, 0], [1, 1, 0], [0, 0, 1]], 2),
        ([[1, 0, 0], [0, 1, 0], [0, 0, 1]], 3),
        ([[1]], 1),
        ([[1, 1, 1], [1, 1, 1], [1, 1, 1]], 1),
        ([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 1], [0, 0, 1, 1]], 3),
    ]

    print("--- correctness: Union-Find vs DFS agree ---")
    for matrix, want in cases:
        got_uf = sol.findCircleNum([row[:] for row in matrix])
        got_dfs = sol.findCircleNum_dfs([row[:] for row in matrix])
        ok = got_uf == want and got_dfs == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={len(matrix)}  uf={got_uf} "
              f"dfs={got_dfs}  (want {want})")

    # --------------------------------------------------------------------
    # RUNTIME DEMO: path compression's effect on find() on a WORST-CASE
    # chain (union always attaches the new node under the previous one,
    # which is exactly what union-BY-RANK is designed to prevent -- so
    # this isolates path compression's contribution specifically).
    # --------------------------------------------------------------------
    print("\n--- DEMO: path compression vs none, find() on a long chain ---")
    n = 4000
    calls = 20000

    uf_plain = UnionFind(n)
    uf_none = UnionFindNoCompression(n)
    # Build a genuine WORST-CASE chain (i+1's parent is i) by writing the
    # parent arrays directly -- going through union()'s own find() would
    # attach every node straight to the root and defeat the demo.
    for i in range(n - 1):
        uf_plain.parent[i + 1] = i
        uf_none.parent[i + 1] = i

    # find() EVERY node once (so path compression's benefit -- shortening
    # the chain for THIS AND EVERY FUTURE lookup -- actually gets paid off
    # repeatedly), across several passes.
    passes = calls // n

    t0 = time.perf_counter()
    for _ in range(passes):
        for node in range(n):
            uf_plain.find(node)
    t_plain = time.perf_counter() - t0

    t0 = time.perf_counter()
    for _ in range(passes):
        for node in range(n):
            uf_none.find(node)
    t_none = time.perf_counter() - t0

    print(f"  {passes} passes x find() over every one of {n} nodes on a "
          f"worst-case chain ({passes * n} calls each):")
    print(f"    WITH path compression:    {t_plain * 1000:8.2f} ms "
          f"(pass 1 compresses the chain; later passes are ~O(1)/call)")
    print(f"    WITHOUT path compression: {t_none * 1000:8.2f} ms "
          f"(every call re-walks up to O(n) of the chain)")
    speedup = t_none / t_plain if t_plain > 0 else float("inf")
    print(f"    speedup: {speedup:.1f}x")
    all_ok &= t_plain < t_none   # compression must win on this machine

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
