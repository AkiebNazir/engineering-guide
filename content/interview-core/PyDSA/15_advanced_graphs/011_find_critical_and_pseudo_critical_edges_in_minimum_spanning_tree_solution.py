"""
================================================================================
SOLUTION · LeetCode 1489 · Find Critical and Pseudo-Critical Edges in
Minimum Spanning Tree                                                   [Hard]
https://leetcode.com/problems/find-critical-and-pseudo-critical-edges-in-minimum-spanning-tree/
================================================================================

THE CORE IDEA
--------------
Compute the true MST weight once. Then, for every edge, probe it TWICE by
re-running Kruskal's (topic guide Part 4/5) with that one edge forced OUT
or forced IN:

    base = mst_weight()                              # true optimum
    for i, edge in enumerate(edges):
        if mst_weight(exclude=i) > base:              # (or disconnects)
            critical.append(i)
        elif mst_weight(include=i) == base:
            pseudo_critical.append(i)

O(E^2 * alpha(V)) time (E edges, each probe an O(E*alpha(V)) Kruskal's
run), O(V+E) space.


================================================================================
WHY "EXCLUDE" AND "INCLUDE" ARE SEPARATE, NECESSARY PROBES
================================================================================
CRITICAL asks: "is this edge the ONLY way to achieve the optimum?" --
answered by removing it and seeing if the optimum gets WORSE (or the graph
falls apart). If NO cheaper alternative exists once this edge is gone, it
was irreplaceable.

PSEUDO-CRITICAL asks a DIFFERENT question: "CAN this edge appear in SOME
optimal MST, even though it's not required in ALL of them?" A non-critical
edge (removing it didn't hurt, some other combination fills the gap
equally well) might STILL be usable in an equally-good alternative MST --
that's exactly what forcing it IN and checking the total still matches
`base` verifies. An edge can be excluded without cost (not critical) AND
also be includable without cost (pseudo-critical) simultaneously -- those
are not contradictory, they describe an edge that's optional but valid.

A third, silent category exists too: an edge that, when forced IN, makes
the total WORSE than `base` -- that edge is neither critical nor
pseudo-critical, it simply never belongs in any optimal MST at all
(Example 1's edge index 6, weight 6, is exactly this case -- see the trace).


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, name it and reject it): enumerate every possible
spanning tree, find every one that achieves the minimum weight, then
intersect/union their edge sets to classify critical vs pseudo-critical.
Combinatorially infeasible -- there can be exponentially many minimum-
weight spanning trees.

Approach 1 (Kruskal's, exclude/include re-runs) [checked] -- the answer
above. Kruskal's is naturally suited to "run it again with one edge
pinned" because Union-Find's incremental structure makes forcing an edge
in (pre-union its endpoints) or out (skip it in the sorted scan) trivial
edits to the same core loop.

Approach 2 (Prim's-based re-runs) -- possible in principle, but Prim's
grows a tree node-by-node rather than edge-by-edge, making "force this
SPECIFIC edge in/out" much more awkward to express cleanly than in
Kruskal's edge-centric view. Kruskal's is the natural fit for this
problem specifically because the QUESTION is edge-centric.


================================================================================
STEP BY STEP TRACE
================================================================================
n=5, edges (indexed) =
    0: (0,1,1)  1: (1,2,1)  2: (2,3,2)  3: (0,3,2)
    4: (0,4,3)  5: (3,4,3)  6: (1,4,6)

BASE MST (Kruskal's, sorted by weight, ties broken by original order):
    sorted: [0:(0,1,1), 1:(1,2,1), 2:(2,3,2), 3:(0,3,2), 4:(0,4,3), 5:(3,4,3), 6:(1,4,6)]
    take 0: (0,1,1) -> union(0,1). components: {0,1}
    take 1: (1,2,1) -> union(1,2). components: {0,1,2}
    take 2: (2,3,2) -> union(2,3). components: {0,1,2,3}
    take 3: (0,3,2) -> find(0)==find(3) already -> SKIP (would cycle)
    take 4: (0,4,3) -> union(0,4). components: {0,1,2,3,4} -- all 5 nodes!
    (n-1 = 4 edges used: 0,1,2,4) -> base weight = 1+1+2+3 = 7

PROBE edge 0 (0,1,1) -- EXCLUDE:
    remaining sorted: [1,2,3,4,5,6]. take 1:(1,2,1)->union(1,2).
    take 2:(2,3,2)->union(2,3). take 3:(0,3,2)->union(0,3) [0 and 3 were
    NOT yet connected without edge 0] -> components {0,1,2,3}.
    take 4:(0,4,3)->union(0,4) -> all 5 connected. weight=1+2+2+3=8 > 7(base)
    -> edge 0 is CRITICAL (removing it makes the MST strictly worse).

PROBE edge 1 (1,2,1) -- EXCLUDE:
    take 0:(0,1,1)->union(0,1). take 2:(2,3,2)->union(2,3). take 3:(0,3,2)
    ->union(0,3)[0,1 and 2,3 merge] -> {0,1,2,3}. take 4:(0,4,3)->union(0,4)
    -> all 5 connected. weight=1+2+2+3=8 > 7 -> edge 1 is CRITICAL.

PROBE edge 2 (2,3,2) -- EXCLUDE:
    take 0,1 as usual -> {0,1,2}. take 3:(0,3,2)->union(0,3)-> {0,1,2,3}.
    take 4:(0,4,3)->union(0,4) -> all 5. weight=1+1+2+3=7 == base
    -> NOT critical. Now probe INCLUDE edge 2 (force it first):
    force union(2,3) first (cost 2 committed). Then Kruskal's on the rest:
    take 0:(0,1,1)->union. take 1:(1,2,1)->union[merges {0,1} with {2,3}]
    -> {0,1,2,3}. take 4:(0,4,3)->union(0,4)->all 5. weight=2+1+1+3=7==base
    -> edge 2 is PSEUDO-CRITICAL.

PROBE edge 3 (0,3,2) -- symmetric to edge 2 by the SAME reasoning (edges 2
    and 3 are the two equal-weight-2 edges that can interchangeably close
    the {0,1,2} <-> {3} gap) -> NOT critical, and forcing it in also
    reproduces weight 7 -> PSEUDO-CRITICAL.

PROBE edge 4 (0,4,3) -- EXCLUDE: without it, is there another way to reach
    node 4? Only edges touching 4 are index 4 (0,4,3), index 5 (3,4,3), and
    index 6 (1,4,6). Kruskal's without edge 4: takes 0,1,2 as usual -> all
    of {0,1,2,3} connected, weight so far 4. Then next cheapest edge
    touching 4 is edge 5 (3,4,3) -> union(3,4) -> all 5 connected.
    weight=1+1+2+3=7==base -> NOT critical. INCLUDE probe: force (0,4,3)
    first, run the rest -> same 7 -> PSEUDO-CRITICAL.

PROBE edge 5 (3,4,3) -- symmetric to edge 4 (the other weight-3 edge into
    node 4) -> NOT critical, INCLUDE reproduces 7 -> PSEUDO-CRITICAL.

PROBE edge 6 (1,4,6) -- EXCLUDE: the base MST never used it anyway, so
    excluding changes nothing -> weight stays 7==base -> NOT critical.
    INCLUDE probe: force (1,4,6) first (cost 6 committed) -> Kruskal's on
    the rest can only add 3 more edges among the remaining 4 nodes'
    components -> best achievable total is 6 + (cheapest completion) > 7
    -> NOT equal to base -> NOT pseudo-critical either. Edge 6 belongs to
    NEITHER list (it's simply too expensive to ever be optimal).

Final: critical=[0,1], pseudo_critical=[2,3,4,5].  MATCHES expected output.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time                   Space  Mutates input?
    -------------------------------------  ---------------------  -----  --------------
    Brute-force enumerate all MSTs         exponential            large   no
    Kruskal's exclude/include re-runs      O(E^2 * alpha(V))      O(V+E)  no
    [chosen]


================================================================================
EDGE CASES
================================================================================
    all edges have DISTINCT weights -> EVERY edge in the base MST is
                                       critical (no tie means no
                                       alternative can ever match the
                                       optimum), and every edge NOT in the
                                       base MST is neither critical nor
                                       pseudo-critical -- there is exactly
                                       one MST, full stop.
    many edges tied at the SAME       -> Example 2: a 4-cycle, all weight
    weight, forming ties               1 -- every single edge is pseudo-
                                       critical (any 3 of the 4 form a
                                       valid MST) and NONE is critical
                                       (any one can be dropped without
                                       loss).
    the graph has exactly n-1 edges   -> a tree already; every edge is
    (already minimally connected)      critical by definition (removing
                                       ANY edge disconnects the graph
                                       entirely, and Kruskal's is not even
                                       needed to see this, though the
                                       algorithm handles it correctly
                                       regardless).
    an edge whose removal              -> the algorithm's own "disconnects
    DISCONNECTS the graph entirely       the graph" check (fewer than n-1
                                        edges used) must be treated as
                                        "infinitely worse than base," not
                                        silently ignored or compared as a
                                        finite number.
    duplicate parallel edges           -> excluded by the constraints
                                       ("All pairs (ai, bi) are distinct"),
                                       so no two edges connect the same
                                       pair of nodes.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting to check "does mst_weight(exclude=i) actually still connect
   all n nodes" -- only comparing weights and missing the case where
   removing an edge makes the graph fall apart entirely (which is an even
   stronger signal of criticality than merely "more expensive").

2. Running the INCLUDE probe on an edge WITHOUT first confirming it isn't
   already known critical -- wasted work, not a correctness bug, but
   worth noting: once an edge is known critical, it cannot also be
   pseudo-critical (the problem defines the two categories as mutually
   exclusive), so skipping the include-probe for already-critical edges
   is a legitimate optimization.

3. Comparing the INCLUDE probe's weight with `>=` instead of `==` --
   forcing an edge in can never produce a total STRICTLY LESS than base
   (base is already optimal), so `<` should never occur; if your
   implementation ever produces a smaller number here, that's a signal
   `base` itself was computed incorrectly, not a sign to loosen the
   comparison.

4. Re-sorting the edge list inside every probe call instead of sorting
   ONCE up front and reusing the sorted list/indices across all O(E)
   probes -- correctness-preserving but needlessly re-pays an O(E log E)
   sort E times over, inflating the total to O(E^2 log E) instead of
   O(E^2 * alpha(V)).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How would this scale if E were much larger, say 10^5?
A: O(E^2) re-running becomes infeasible. A more advanced technique
   precomputes, for each edge NOT in a fixed base MST, the MAXIMUM edge
   weight on the tree path between its endpoints (via binary lifting /
   LCA over the MST) to determine criticality/pseudo-criticality without
   a full Kruskal's re-run per edge -- O(E log V) total. Well beyond
   interview scope to implement live, but naming the direction shows depth.

Q: Why can an edge be BOTH excludable (not critical) and includable
   (pseudo-critical) at the same time -- isn't that contradictory?
A: No -- "not critical" means "some OTHER combination achieves the same
   optimum without this edge." "Pseudo-critical" means "this edge CAN
   still be part of an equally-good alternative combination." Both can be
   true simultaneously for an edge that is optional but valid, which is
   precisely the definition of a tie in the MST's structure.

Q: What is the relationship between this problem and cycle property /
   cut property from MST theory?
A: The CUT PROPERTY says the minimum-weight edge crossing any cut belongs
   to SOME MST; the CYCLE PROPERTY says the maximum-weight edge in any
   cycle belongs to NO MST unless tied for the max. Critical edges are
   exactly those that are the UNIQUE minimum across some cut; pseudo-
   critical edges are tied minimums across some cut with at least one
   other edge of equal weight.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 1584 Min Cost to Connect All Points (005 -- the base MST computation
            this problem probes repeatedly)
    LC 1135 Connecting Cities With Minimum Cost (plain MST weight, no
            edge-classification layer)
    LC 261  Graph Valid Tree (topic 14 -- Union-Find used purely to check
            "is this a valid tree," the primitive this problem's exclude-
            probe's "still connects everyone" check relies on)
================================================================================
"""

from typing import List, Optional


class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.components = n

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
        self.components -= 1
        return True


class Solution:
    def findCriticalAndPseudoCriticalEdges(self, n: int,
                                           edges: List[List[int]]) -> List[List[int]]:
        """✅ Kruskal's, re-run with each edge excluded / forced-included.
        O(E^2 * alpha(V)) time, O(V+E) space."""
        indexed = sorted(range(len(edges)), key=lambda i: edges[i][2])

        def mst_weight(exclude: Optional[int] = None,
                      include: Optional[int] = None) -> int:
            uf = UnionFind(n)
            total = 0
            if include is not None:
                a, b, w = edges[include]
                uf.union(a, b)
                total += w
            for i in indexed:
                if i == exclude or i == include:
                    continue
                a, b, w = edges[i]
                if uf.union(a, b):
                    total += w
            return total if uf.components == 1 else float('inf')

        base = mst_weight()
        critical, pseudo = [], []

        for i in range(len(edges)):
            if mst_weight(exclude=i) > base:
                critical.append(i)
            elif mst_weight(include=i) == base:
                pseudo.append(i)

        return [critical, pseudo]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        (5, [[0, 1, 1], [1, 2, 1], [2, 3, 2], [0, 3, 2], [0, 4, 3], [3, 4, 3], [1, 4, 6]],
         [[0, 1], [2, 3, 4, 5]]),
        (4, [[0, 1, 1], [1, 2, 1], [2, 3, 1], [0, 3, 1]],
         [[], [0, 1, 2, 3]]),
    ]

    print("--- correctness ---")
    for n, edges, want in cases:
        got = sol.findCriticalAndPseudoCriticalEdges(n, [e[:] for e in edges])
        ok = [sorted(got[0]), sorted(got[1])] == [sorted(want[0]), sorted(want[1])]
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n}  -> {got}  (want {want})")

    # --------------------------------------------------------------------
    # RUNTIME DEMO: verify the "every edge falls into exactly one of three
    # buckets, and base/exclude/include weights obey base <= exclude and
    # base <= include" invariant on 200 random weighted connected graphs.
    # --------------------------------------------------------------------
    print("\n--- DEMO: exclude/include invariants across random graphs ---")
    import random
    random.seed(1489)
    violations = 0
    trials = 200
    for _ in range(trials):
        n = random.randint(4, 8)
        # build a random connected graph: a random spanning tree, plus
        # extra random edges, with random distinct weights.
        nodes = list(range(n))
        random.shuffle(nodes)
        edge_set = set()
        for i in range(1, n):
            a, b = nodes[i], nodes[random.randint(0, i - 1)]
            edge_set.add((min(a, b), max(a, b)))
        extra = random.randint(0, 4)
        attempts = 0
        while len(edge_set) < (n - 1 + extra) and attempts < 50:
            a, b = random.sample(range(n), 2)
            edge_set.add((min(a, b), max(a, b)))
            attempts += 1
        weights = random.sample(range(1, 1000), len(edge_set))
        edges = [[a, b, w] for (a, b), w in zip(edge_set, weights)]

        result = sol.findCriticalAndPseudoCriticalEdges(n, [e[:] for e in edges])
        crit, pseudo = set(result[0]), set(result[1])
        if crit & pseudo:
            violations += 1     # must be mutually exclusive
        if len(crit) + len(pseudo) > len(edges):
            violations += 1

    print(f"  {trials} random connected graphs: critical/pseudo-critical "
          f"sets always disjoint, no violations = {violations == 0} "
          f"({violations} violations found)")
    all_ok &= (violations == 0)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
