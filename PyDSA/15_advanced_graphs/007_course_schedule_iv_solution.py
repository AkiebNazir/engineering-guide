"""
================================================================================
SOLUTION · LeetCode 1462 · Course Schedule IV                        [Medium]
https://leetcode.com/problems/course-schedule-iv/
================================================================================

THE CORE IDEA
--------------
"Prerequisite" is TRANSITIVE reachability in a DAG -- exactly what
Floyd-Warshall computes for ALL pairs at once. With up to 10^4 queries
against only <= 100 courses, precompute the full reachability table ONCE
(O(V^3)), then answer every query in O(1).

    reach = [[False]*V for _ in range(V)]
    for a, b in prerequisites: reach[a][b] = True
    for k in range(V):                   # intermediate -- MUST be outermost
        for i in range(V):
            for j in range(V):
                if reach[i][k] and reach[k][j]:
                    reach[i][j] = True
    return [reach[u][v] for u, v in queries]

O(V^3 + Q) time, O(V^2) space.


================================================================================
WHY k MUST BE THE OUTERMOST LOOP
================================================================================
Floyd-Warshall's correctness relies on an inductive invariant: after the
k-th iteration of the outer loop, `reach[i][j]` is True iff j is reachable
from i using only intermediate nodes from {0, 1, ..., k}. Each pass over k
EXTENDS every pair's answer by allowing one more node as a stepping stone.
This only works if, by the time `reach[i][j]` is read for a given k, EVERY
pair `reach[i][k]` and `reach[k][j]` has ALREADY been fully finalized for
all smaller k -- which requires k to have completed ITS ENTIRE i,j sweep
before moving to k+1. Putting i or k in the wrong loop position breaks
this: a pair might get updated using a k-value that hasn't itself been
fully resolved yet, silently producing an incomplete closure. This is a
famous, easy-to-get-backwards mistake -- demoed live below with a broken
loop order that gives an incorrect answer with no exception raised.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, name it and reject it): for EACH query, run a
fresh BFS/DFS from u to check whether v is reachable. Correct, but with Q
up to 10^4 and each traversal up to O(V+E), that's O(Q*(V+E)) -- at
V=100, E up to ~5000, Q=10^4, roughly 5*10^7 operations -- wasteful when
the SAME reachability facts get recomputed for every query that happens to
share a source or land inside an already-explored subgraph.

Approach 1 (Floyd-Warshall, precompute once) [checked] -- the answer
above. O(V^3 + Q). At V=100, V^3 = 10^6 -- trivial, and every query after
that is O(1).

Approach 2 (V independent BFS/DFS runs, precompute once) -- for each
course i, BFS/DFS forward and mark every course reachable from i in
reach[i][...]. O(V * (V + E)) to build, O(1) per query after. Slightly
better asymptotically than Floyd-Warshall when E is sparse (O(V^2 + V*E)
vs O(V^3)), though at V<=100 the difference is negligible in practice --
worth naming as the graph-native alternative to the matrix-DP view.


================================================================================
STEP BY STEP TRACE
================================================================================
numCourses=3, prerequisites=[[1,2],[1,0],[2,0]]
Initial reach (True cells only): reach[1][2]=T, reach[1][0]=T, reach[2][0]=T

k=0 (can we route THROUGH course 0?):
    need reach[i][0] and reach[0][j] both True for some i,j.
    reach[*][0]: only reach[1][0] and reach[2][0] are True.
    reach[0][*]: NONE are True (course 0 has no outgoing edges yet).
    -> no updates this pass.

k=1 (can we route THROUGH course 1?):
    reach[*][1]: none are True yet (nothing points INTO 1).
    -> no updates this pass (nothing to combine).

k=2 (can we route THROUGH course 2?):
    reach[*][2]: reach[1][2] is True.
    reach[2][*]: reach[2][0] is True.
    combine: reach[1][2] and reach[2][0] -> reach[1][0] already True
             (no-op, but this IS the transitive link 1->2->0 confirming
             the direct edge 1->0 that also already existed).

Final reach: {1:0, 1:2, 2:0} all True; nothing else.
queries = [[1,0],[1,2]] -> reach[1][0]=True, reach[1][2]=True -> [True, True]
MATCHES expected output.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time            Space   Mutates input?
    -------------------------------  --------------  -------  --------------
    Per-query BFS/DFS                O(Q*(V+E))       O(V)     no
    Floyd-Warshall precompute [chos.] O(V^3 + Q)      O(V^2)   no
    V independent BFS/DFS precompute  O(V*(V+E) + Q)  O(V^2)   no


================================================================================
EDGE CASES
================================================================================
    prerequisites is empty      -> reach stays all False; every query
                                   answers False (Example 2).
    a course with no             -> its row in `reach` stays all False (it's
    prerequisites and no          not a prerequisite of anything); its
    dependents                    column stays all False too.
    query asks about a course    -> not possible per constraints (ui != vi),
    and itself                    but if it were, a DAG's node is never its
                                   own prerequisite (no self-loops, no
                                   cycles), so it would correctly be False.
    a long prerequisite CHAIN    -> exactly where transitivity matters most
    (0->1->2->...->n-1)           -- reach[0][n-1] must end up True even
                                   though there's no DIRECT edge 0->(n-1);
                                   Floyd-Warshall's k-sweep builds this up
                                   one intermediate hop at a time.
    numCourses at its max (100)  -> V^3 = 10^6, trivially fast; no scaling
                                   concern at these bounds.
    the graph is guaranteed       -> stated in the constraints; if it
    acyclic (no cycles)           weren't, "prerequisite" would be
                                   ill-defined (mutual prerequisites), and
                                   the closure would just mark both
                                   directions True for everything in the cycle.


================================================================================
COMMON MISTAKES
================================================================================
1. Putting the intermediate node k in the INNERMOST loop position instead
   of outermost. Compiles, runs, produces a plausible-looking (but
   incomplete) reachability table with no exception raised. Demoed live
   below on the chain 0->1->2->3->4.

2. Answering each query with a fresh BFS/DFS instead of precomputing --
   correct, but wastes an enormous amount of repeated work when Q is large
   relative to V (this problem's bounds, Q up to 10^4 vs V up to 100, are
   specifically shaped to reward precomputation).

3. Forgetting that "prerequisite" here means STRICTLY prerequisite-of, a
   directed relation -- initializing `reach` symmetrically (setting both
   reach[a][b] AND reach[b][a]) from each prerequisite edge would treat
   "b requires a" as also meaning "a requires b," which is backwards and
   would incorrectly answer queries in the wrong direction.

4. Confusing DIRECT prerequisites (the raw edge list) with the full
   TRANSITIVE closure the problem actually asks about -- only checking
   `[u,v] in prerequisites` directly (or building an adjacency set from
   the raw edges without running the closure) misses every INDIRECT
   prerequisite relationship, e.g. Example 3's [1,0] pair, which holds
   transitively via 1->2->0, not as a direct edge.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if numCourses were much larger, say 10^5?
A: O(V^3) Floyd-Warshall becomes infeasible immediately. Switch to V
   independent BFS/DFS runs (Approach 2), O(V*(V+E)) -- still expensive at
   V=10^5 unless E is sparse, but strictly better than V^3. Beyond that,
   this shape (many reachability queries on a large DAG) typically calls
   for offline batching or a specialized reachability index (e.g., a
   2-hop cover), well past interview scope.

Q: Why is Floyd-Warshall (usually taught as ALL-PAIRS SHORTEST PATH)
   correct here for plain reachability?
A: Reachability is the Boolean special case of shortest-path DP: instead
   of `dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])`, use
   `reach[i][j] = reach[i][j] or (reach[i][k] and reach[k][j])` -- OR/AND
   in place of min/+. Same recurrence structure, same loop-order
   requirement, different semiring.

Q: How would you detect that the input DAG actually HAS a cycle, if that
   guarantee were removed?
A: Kahn's topological sort (topic guide Part 7) -- if it can't order all V
   nodes (the BFS queue empties early), a cycle exists. The problem here
   guarantees acyclicity, but that's exactly the check to add defensively
   if the guarantee were untrustworthy.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 207  Course Schedule (cycle detection only, no transitive queries)
    LC 210  Course Schedule II (topological ORDER, not reachability)
    LC 1334 Find the City With the Smallest Number of Neighbors at a
            Threshold Distance (Floyd-Warshall, weighted, all-pairs
            shortest distance instead of Boolean reachability)
    LC 399  Evaluate Division (Floyd-Warshall-flavored transitive closure
            with a numeric ratio carried along each path)
================================================================================
"""

from typing import List


class Solution:
    def checkIfPrerequisite(self, numCourses: int, prerequisites: List[List[int]],
                            queries: List[List[int]]) -> List[bool]:
        """✅ Floyd-Warshall transitive closure, precomputed once.
        O(V^3 + Q) time, O(V^2) space."""
        V = numCourses
        reach = [[False] * V for _ in range(V)]
        for a, b in prerequisites:
            reach[a][b] = True

        for k in range(V):                 # intermediate node -- OUTERMOST
            for i in range(V):
                if not reach[i][k]:
                    continue                # small prune: nothing to extend
                for j in range(V):
                    if reach[k][j]:
                        reach[i][j] = True

        return [reach[u][v] for u, v in queries]

    def checkIfPrerequisite_bfs_per_course(self, numCourses: int,
                                           prerequisites: List[List[int]],
                                           queries: List[List[int]]) -> List[bool]:
        """Alternative: V independent BFS runs, one forward traversal per
        course. O(V*(V+E) + Q) time, O(V^2) space."""
        from collections import deque, defaultdict

        adj = defaultdict(list)
        for a, b in prerequisites:
            adj[a].append(b)

        reach = [[False] * numCourses for _ in range(numCourses)]
        for start in range(numCourses):
            visited = [False] * numCourses
            queue = deque(adj[start])
            while queue:
                node = queue.popleft()
                if visited[node]:
                    continue
                visited[node] = True
                reach[start][node] = True
                queue.extend(adj[node])

        return [reach[u][v] for u, v in queries]

    def checkIfPrerequisite_wrong_loop_order_BROKEN(self, numCourses: int,
                                                     prerequisites: List[List[int]],
                                                     queries: List[List[int]]) -> List[bool]:
        """✗ BROKEN ON PURPOSE -- mistake #1. Puts k as the INNERMOST loop
        instead of outermost, producing an incomplete transitive closure.
        Demoed live below."""
        V = numCourses
        reach = [[False] * V for _ in range(V)]
        for a, b in prerequisites:
            reach[a][b] = True

        for i in range(V):
            for j in range(V):
                for k in range(V):          # WRONG position -- BUG
                    if reach[i][k] and reach[k][j]:
                        reach[i][j] = True

        return [reach[u][v] for u, v in queries]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        (2, [[1, 0]], [[0, 1], [1, 0]], [False, True]),
        (2, [], [[1, 0], [0, 1]], [False, False]),
        (3, [[1, 2], [1, 0], [2, 0]], [[1, 0], [1, 2]], [True, True]),
        (5, [[0, 1], [1, 2], [2, 3], [3, 4]], [[0, 4], [4, 0], [1, 3]], [True, False, True]),
    ]

    print("--- correctness: Floyd-Warshall vs per-course BFS agree ---")
    for numCourses, prereqs, queries, want in cases:
        got_fw = sol.checkIfPrerequisite(numCourses, [p[:] for p in prereqs],
                                         [q[:] for q in queries])
        got_bfs = sol.checkIfPrerequisite_bfs_per_course(
            numCourses, [p[:] for p in prereqs], [q[:] for q in queries])
        ok = got_fw == want and got_bfs == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={numCourses}  fw={got_fw} "
              f"bfs={got_bfs}  (want {want})")

    # --------------------------------------------------------------------
    # ⚠️ LIVE DEMO: wrong loop order on a branching (non-chain) DAG.
    # NOTE: on a simple linear chain 0->1->2->3->4 the wrong loop order
    # happens to still produce the right answer in one pass, because the
    # chain's node order coincides with the loops' iteration order -- it
    # takes a graph where transitivity must route through a node whose
    # OWN reachability hasn't been finalized yet (found here by brute-
    # force random search over small DAGs) to actually expose the bug.
    # --------------------------------------------------------------------
    print("\n--- ⚠️  live demo: mistake #1, k as the INNERMOST loop ---")
    numCourses = 7
    prereqs = [[1, 0], [1, 4], [3, 6], [4, 0], [5, 2], [5, 3], [6, 4]]
    queries = [[3, 0], [5, 0], [1, 0], [5, 4]]
    correct = sol.checkIfPrerequisite(numCourses, [p[:] for p in prereqs],
                                      [q[:] for q in queries])
    broken = sol.checkIfPrerequisite_wrong_loop_order_BROKEN(
        numCourses, [p[:] for p in prereqs], [q[:] for q in queries])
    print(f"  edges={prereqs}, queries={queries}")
    print(f"  correct (k outermost):  {correct}")
    print(f"  broken  (k innermost):  {broken}")
    exposed = broken != correct
    print(f"  the broken loop order produced a DIFFERENT (incomplete) "
          f"closure: {exposed}  (no exception raised, just wrong booleans)")
    print("  specifically: 3->6->4->0 makes course 0 transitively required")
    print("  by course 3, but the wrong loop order misses it because row 3")
    print("  is finalized (i=3's full j,k sweep) BEFORE row 6's own")
    print("  reachability through 4 has been established.")
    all_ok &= exposed and correct == [True, True, True, True]

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
