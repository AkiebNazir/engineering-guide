"""
================================================================================
SOLUTION · LeetCode 399 · Evaluate Division                             [Medium]
https://leetcode.com/problems/evaluate-division/
================================================================================

THE CORE IDEA
--------------
Equations are edges of a weighted graph: a / b = v gives a -> b with weight v
and b -> a with weight 1/v. The value of c / d is the PRODUCT of edge weights
along any path from c to d. No contradictions means every path gives the same
product. No path means c and d are in different components: unknown, -1.0.


================================================================================
APPROACH 1 · Graph + DFS per query ✅ (the answer at this input size)
================================================================================
    graph = defaultdict(list)
    for (a, b), v in zip(equations, values):
        graph[a].append((b, v))
        graph[b].append((a, 1.0 / v))

    def query(c, d):
        if c not in graph or d not in graph:
            return -1.0                     # undefined variable (even c == d)
        stack, seen = [(c, 1.0)], {c}
        while stack:
            node, acc = stack.pop()
            if node == d:
                return acc
            for nxt, w in graph[node]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append((nxt, acc * w))
        return -1.0

    Time: O(Q * (V + E))    Space: O(V + E)

With E, Q <= 20 this is effectively instant, and it's the easiest to get
right under pressure.


================================================================================
APPROACH 2 · Weighted Union-Find
================================================================================
Store for each variable x: parent[x] and weight[x] = x / parent[x].
find(x) compresses the path and multiplies weights so weight[x] becomes
x / root.

    union(a, b, v):   ra, rb = find(a), find(b)
                      # a / b = v  and a = weight[a] * ra,  b = weight[b] * rb
                      # => ra / rb = v * weight[b] / weight[a]
                      parent[ra] = rb; weight[ra] = v * weight[b] / weight[a]
    query(c, d):      same root ? weight[c] / weight[d] : -1.0

    Time: O((E + Q) α(V))    Space: O(V)

This is the one to use for many queries or equations arriving online.


================================================================================
APPROACH 3 · Floyd-Warshall on ratios
================================================================================
ratio[i][k] = ratio[i][j] * ratio[j][k] whenever both are known. Precompute
all pairs once, then every query is O(1).

    Time: O(V^3) precompute    Space: O(V^2)

Good when V is small and queries are plentiful.


================================================================================
STEP BY STEP TRACE · a/b = 2, b/c = 3, query a/c (DFS)
================================================================================
    graph:  a -> (b, 2)
            b -> (a, 0.5), (c, 3)
            c -> (b, 1/3)

    stack [(a, 1)]           seen {a}
    pop (a, 1): push (b, 2)  seen {a, b}
    pop (b, 2): a seen; push (c, 6)
    pop (c, 6): c == target -> 6.0


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                   Precompute        Per query   Space    Mutates input?
    -------------------------  ----------------  ----------  -------  --------------
    Graph + DFS ✅             O(E)              O(V + E)    O(V+E)   No
    Weighted Union-Find        O(E α(V))         O(α(V))     O(V)     No
    Floyd-Warshall             O(V^3)            O(1)        O(V^2)   No


================================================================================
EDGE CASES
================================================================================
    x / x, x known             1.0
    x / x, x unknown           -1.0 (NOT 1.0) — the classic trap.
    Different components       -1.0
    Reverse query b / a        Uses the 1/v reverse edge.
    Chains                     Products of several edges.
    Floating point             Products drift slightly; compare with tolerance.


================================================================================
COMMON MISTAKES
================================================================================
1. Returning 1.0 for x / x before checking that x exists. Demo below.

2. Forgetting reverse edges. b / a becomes unreachable. Demo below.

3. No visited set: cycles (a/b, b/c, c/a) loop forever.

4. In weighted union-find, getting the weight formula direction backwards
   (v * weight[a] / weight[b]). The randomized test catches it immediately.

5. Comparing floats with == in tests.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Equations can be contradictory; detect it?
A: Weighted union-find: when uniting two variables already in the same set,
   check weight[a] / weight[b] against the new v (with tolerance). A mismatch
   is a contradiction. (LC 2307 Check for Contradictions in Equations.)

Q: Currency exchange rates: is there an arbitrage cycle?
A: Take -log(rate) as the edge weight; an arbitrage opportunity is a negative
   cycle, which Bellman-Ford detects.

Q: Millions of queries?
A: Weighted union-find, or precompute each node's ratio to its component root
   once, so any query is root check + one division.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 2307  Check for Contradictions in Equations  — weighted union-find
    LC 990   Satisfiability of Equality Equations (002)
    LC 787   Cheapest Flights Within K Stops (004) — Bellman-Ford
    LC 1631  Path With Minimum Effort (006)
================================================================================
"""

import math
import random
from collections import defaultdict
from typing import Dict, List, Tuple


class Solution:
    def calcEquation(self, equations: List[List[str]], values: List[float],
                     queries: List[List[str]]) -> List[float]:
        graph: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        for (a, b), v in zip(equations, values):
            graph[a].append((b, v))
            graph[b].append((a, 1.0 / v))

        def query(c: str, d: str) -> float:
            if c not in graph or d not in graph:
                return -1.0
            stack = [(c, 1.0)]
            seen = {c}
            while stack:
                node, acc = stack.pop()
                if node == d:
                    return acc
                for nxt, w in graph[node]:
                    if nxt not in seen:
                        seen.add(nxt)
                        stack.append((nxt, acc * w))
            return -1.0

        return [query(c, d) for c, d in queries]


# ------------------------------------------------------------------------
# Alternatives / oracle / broken versions for the demos.
# ------------------------------------------------------------------------
def calc_union_find(equations: List[List[str]], values: List[float], queries: List[List[str]]) -> List[float]:
    parent: Dict[str, str] = {}
    weight: Dict[str, float] = {}          # weight[x] = x / parent[x]

    def find(x: str) -> str:
        if parent[x] != x:
            root = find(parent[x])
            weight[x] *= weight[parent[x]]
            parent[x] = root
        return parent[x]

    for (a, b), v in zip(equations, values):
        for x in (a, b):
            if x not in parent:
                parent[x], weight[x] = x, 1.0
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
            weight[ra] = v * weight[b] / weight[a]

    out = []
    for c, d in queries:
        if c not in parent or d not in parent or find(c) != find(d):
            out.append(-1.0)
        else:
            out.append(weight[c] / weight[d])
    return out


def calc_self_query_bug(equations: List[List[str]], values: List[float], queries: List[List[str]]) -> List[float]:
    """Mistake 1: answers x / x = 1.0 without checking x is defined."""
    base = Solution().calcEquation(equations, values, queries)
    return [1.0 if c == d else r for (c, d), r in zip(queries, base)]


def calc_no_reverse_bug(equations: List[List[str]], values: List[float], queries: List[List[str]]) -> List[float]:
    """Mistake 2: forward edges only."""
    graph: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
    names = set()
    for (a, b), v in zip(equations, values):
        graph[a].append((b, v))
        names.update((a, b))
    out = []
    for c, d in queries:
        if c not in names or d not in names:
            out.append(-1.0)
            continue
        stack, seen, ans = [(c, 1.0)], {c}, -1.0
        while stack:
            node, acc = stack.pop()
            if node == d:
                ans = acc
                break
            for nxt, w in graph[node]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append((nxt, acc * w))
        out.append(ans)
    return out


def close(a: List[float], b: List[float]) -> bool:
    return len(a) == len(b) and all(math.isclose(x, y, rel_tol=1e-9, abs_tol=1e-9) for x, y in zip(a, b))


# ==============================================================================
# TESTS — run:  python 014_evaluate_division_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: DFS vs weighted union-find ---")
    cases = [
        ([["a", "b"], ["b", "c"]], [2.0, 3.0],
         [["a", "c"], ["b", "a"], ["a", "e"], ["a", "a"], ["x", "x"]],
         [6.0, 0.5, -1.0, 1.0, -1.0]),
        ([["a", "b"], ["b", "c"], ["bc", "cd"]], [1.5, 2.5, 5.0],
         [["a", "c"], ["c", "b"], ["bc", "cd"], ["cd", "bc"]],
         [3.75, 0.4, 5.0, 0.2]),
        ([["a", "b"]], [0.5], [["a", "b"], ["b", "a"], ["a", "c"], ["x", "y"]], [0.5, 2.0, -1.0, -1.0]),
        ([["a", "b"], ["c", "d"]], [2.0, 3.0], [["a", "d"], ["d", "c"]], [-1.0, 1 / 3]),
    ]
    for eq, vals, qs, want in cases:
        a, b = sol.calcEquation(eq, vals, qs), calc_union_find(eq, vals, qs)
        ok = close(a, want) and close(b, want)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  dfs={[round(x, 4) for x in a]}  uf={[round(x, 4) for x in b]}")

    print("\n--- randomized: hidden true values, consistent equations (400 cases) ---")
    rng = random.Random(399)
    bad = 0
    for _ in range(400):
        names = [f"v{i}" for i in range(rng.randint(2, 10))]
        truth = {n: rng.uniform(0.5, 4.0) for n in names}
        equations, values = [], []
        for _ in range(rng.randint(1, 12)):
            a, b = rng.sample(names, 2)
            equations.append([a, b])
            values.append(truth[a] / truth[b])
        queries = [[rng.choice(names + ["zz"]), rng.choice(names + ["zz"])] for _ in range(10)]
        a, b = sol.calcEquation(equations, values, queries), calc_union_find(equations, values, queries)
        if not close(a, b):
            bad += 1
            continue
        for (c, d), r in zip(queries, a):
            if r != -1.0 and not math.isclose(r, truth[c] / truth[d], rel_tol=1e-9):
                bad += 1
                break
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  every answered ratio equals truth[c] / truth[d]; DFS and union-find agree")

    print("\n--- mistake 1 LIVE: x / x for an undefined x ---")
    q = [["x", "x"]]
    wrong = calc_self_query_bug([["a", "b"]], [2.0], q)
    right = sol.calcEquation([["a", "b"]], [2.0], q)
    ok = wrong == [1.0] and right == [-1.0]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  x never appears: shortcut returns {wrong}, correct {right}")

    print("\n--- mistake 2 LIVE: no reverse edges ---")
    q = [["b", "a"], ["c", "a"]]
    wrong = calc_no_reverse_bug([["a", "b"], ["b", "c"]], [2.0, 3.0], q)
    right = sol.calcEquation([["a", "b"], ["b", "c"]], [2.0, 3.0], q)
    ok = wrong == [-1.0, -1.0] and close(right, [0.5, 1 / 6])
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  b/a and c/a: forward-only returns {wrong}, correct {[round(x, 4) for x in right]}")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
