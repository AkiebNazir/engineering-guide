"""
================================================================================
SOLUTION · LeetCode 1483 · Kth Ancestor of a Tree Node                    [Hard]
https://leetcode.com/problems/kth-ancestor-of-a-tree-node/
================================================================================

THE CORE IDEA
--------------
Binary lifting: precompute every power-of-two jump, then answer a query with
one jump per set bit of k.

    up[0][v] = parent[v]
    up[j][v] = up[j-1][ up[j-1][v] ]      (-1 stays -1)

    query(v, k): for each bit j of k:  v = up[j][v]   (stop at -1)

k = 13 = 0b1101 is a jump of 8, then 4, then 1 — three table lookups instead
of thirteen parent steps.


================================================================================
APPROACH 1 · Walk up one parent at a time
================================================================================
    while k and node != -1:
        node = parent[node]; k -= 1

    Build: O(1)    Query: O(k) — up to O(n) on a path-shaped tree


================================================================================
APPROACH 2 · Store every node's full ancestor list
================================================================================
ancestors[v] = [parent, grandparent, ...]; query is one index.

    Build: O(n * depth) — O(n^2) time and memory on a path. 50,000 nodes means
    ~1.25 * 10^9 stored entries. Not an option at this size.


================================================================================
APPROACH 3 · Binary lifting ✅ (the answer)
================================================================================
    LOG = max(1, n.bit_length())
    up = [parent[:]]
    for j in range(1, LOG):
        prev = up[-1]
        up.append([prev[m] if (m := prev[v]) != -1 else -1 for v in range(n)])

    def get(node, k):
        j = 0
        while k and node != -1:
            if k & 1:
                node = up[j][node]
            k >>= 1; j += 1
        return node

Filling level by level (j outer) means up[j-1] is COMPLETE before level j
reads it, whatever order the node numbers are in. If k needs a bit beyond the
table (k >= 2^LOG > n), there is no such ancestor anyway: the loop runs out of
levels with node still set, so guard j < LOG.

    Build: O(n log n)    Query: O(log k)    Space: O(n log n)


================================================================================
STEP BY STEP TRACE · parent = [-1, 0, 0, 1, 1, 2, 2], query (6, 3)
================================================================================
    node:        0    1    2    3    4    5    6
    up[0] (1):  -1    0    0    1    1    2    2
    up[1] (2):  -1   -1   -1    0    0    0    0
    up[2] (4):  -1   -1   -1   -1   -1   -1   -1

    k = 3 = 0b11
      bit 0 set: node = up[0][6] = 2
      bit 1 set: node = up[1][2] = -1
    answer -1 (node 6 has only two ancestors)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Build          Query      Space     Mutates input?
    --------------------------  -------------  ---------  --------  --------------
    Walk parents                O(1)           O(k)       O(1)      No
    Full ancestor lists         O(n * depth)   O(1)       O(n^2)    No
    Binary lifting ✅           O(n log n)     O(log k)   O(n log n) No (copies parent)


================================================================================
EDGE CASES
================================================================================
    The root, any k           -1.
    k equal to the depth      The root (0).
    k larger than n           -1 — must not index past the table.
    n a power of two          The off-by-one in LOG shows up here.
    Parent index > child      Only a level-by-level fill is correct.


================================================================================
COMMON MISTAKES
================================================================================
1. Too few levels. On a 16-node path, k = 15 = 0b1111 needs jumps of 1, 2, 4
   and 8 — four levels. A table built with floor(log2(n - 1)) = 3 levels has
   no 8-jump, so the query can't reach the answer. The safe rule is
   LOG = n.bit_length(), which guarantees 2^LOG > n. Demo.

2. Python's -1 index. Computing up[j][v] = up[j-1][up[j-1][v]] with no check
   reads up[j-1][-1] — the LAST node's entry — whenever the midpoint doesn't
   exist. No exception; just a wrong ancestor. Demo.

3. Filling node by node (v outer, j inner) instead of level by level. up[j-1]
   of a node with a larger index isn't built yet, so it silently reads
   placeholders when parents have larger indices than children. Demo.

4. Walking parents one at a time: correct, and fine for a few queries, but
   O(n) per query on deep trees. Demo times it on a 50,000-node path.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Lowest common ancestor of u and v?
A: Also compute depth. Lift the deeper node up by the depth difference, then
   for j from high to low: if up[j][u] != up[j][v], move both. The answer is
   the parent of where they stop. O(log n) per query.

Q: The tree changes (nodes added as leaves)?
A: A new leaf's up[j] row depends only on its ancestors, so it can be built
   in O(log n) when the leaf is added.

Q: Distance between two nodes?
A: depth[u] + depth[v] - 2 * depth[lca(u, v)].


================================================================================
RELATED PROBLEMS
================================================================================
    LC 236  Lowest Common Ancestor of a Binary Tree (017)  — single query, DFS
    LC 1650 LCA of a Binary Tree III                       — parent pointers
    LC 2836 Maximize Value of Function in a Ball Passing Game — lifting on a functional graph
    26_segment_tree_fenwick                                 — the other O(log n) "powers of two" structure
================================================================================
"""

import math
import random
import time
from typing import List


class TreeAncestor:
    def __init__(self, n: int, parent: List[int]):
        self.log = max(1, n.bit_length())
        up = [list(parent)]
        for _ in range(1, self.log):
            prev = up[-1]
            up.append([prev[mid] if (mid := prev[v]) != -1 else -1 for v in range(n)])
        self.up = up

    def getKthAncestor(self, node: int, k: int) -> int:
        j = 0
        while k and node != -1:
            if j >= self.log:
                return -1                                 # k >= 2^LOG > n
            if k & 1:
                node = self.up[j][node]
            k >>= 1
            j += 1
        return node


# ------------------------------------------------------------------------
# Alternatives / oracle / broken versions for the demos.
# ------------------------------------------------------------------------
def walk(parent: List[int], node: int, k: int) -> int:
    """Approach 1, also the oracle."""
    while k and node != -1:
        node = parent[node]
        k -= 1
    return node


def build(n: int, parent: List[int], levels: int, check_minus_one: bool = True):
    up = [list(parent)]
    for _ in range(1, levels):
        prev = up[-1]
        if check_minus_one:
            up.append([prev[prev[v]] if prev[v] != -1 else -1 for v in range(n)])
        else:
            up.append([prev[prev[v]] for v in range(n)])          # BUG: prev[-1] is the last node
    return up


def query(up, node: int, k: int) -> int:
    j = 0
    while k and node != -1:
        if j >= len(up):
            return -1
        if k & 1:
            node = up[j][node]
        k >>= 1
        j += 1
    return node


def node_outer_bug(n: int, parent: List[int]):
    """Mistake 3: v outer, j inner — reads levels of later nodes before they exist."""
    log = max(1, n.bit_length())
    up = [[-1] * n for _ in range(log)]
    for v in range(n):
        up[0][v] = parent[v]
        for j in range(1, log):
            mid = up[j - 1][v]
            up[j][v] = up[j - 1][mid] if mid != -1 else -1
    return up


def random_tree(n: int, rng: random.Random, shuffle: bool) -> List[int]:
    """A random tree rooted at 0; with shuffle, parent labels exceed child labels too."""
    order = list(range(1, n))
    if shuffle:
        rng.shuffle(order)
    order = [0] + order                                   # order[i]'s parent comes earlier in order
    parent = [-1] * n
    for i in range(1, n):
        parent[order[i]] = order[rng.randrange(i)]
    return parent


# ==============================================================================
# TESTS — run:  python 021_kth_ancestor_of_a_tree_node_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    print("--- correctness on the examples ---")
    t = TreeAncestor(7, [-1, 0, 0, 1, 1, 2, 2])
    for node, k, want in [(3, 1, 1), (5, 2, 0), (6, 3, -1), (0, 1, -1), (4, 2, 0)]:
        got = t.getKthAncestor(node, k)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  getKthAncestor({node}, {k})  got={got}  want={want}")
    path = TreeAncestor(16, [-1] + list(range(15)))
    odd = TreeAncestor(5, [-1, 4, 1, 2, 0])
    checks = [(path, 15, 15, 0), (path, 15, 16, -1), (path, 15, 8, 7), (path, 9, 9, 0),
              (odd, 3, 4, 0), (odd, 3, 2, 1), (odd, 2, 3, 0), (odd, 3, 5, -1)]
    for obj, node, k, want in checks:
        ok = obj.getKthAncestor(node, k) == want
        all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  path of 16 (power of two) and parent-index > child cases")

    print("\n--- randomized cross-check vs walking parents (300 trees x 200 queries) ---")
    rng = random.Random(1483)
    bad = 0
    for _ in range(300):
        n = rng.randint(1, 80)
        parent = random_tree(n, rng, shuffle=rng.random() < 0.5)
        ta = TreeAncestor(n, parent)
        for _ in range(200):
            v, k = rng.randrange(n), rng.randint(1, n + 3)
            if ta.getKthAncestor(v, k) != walk(parent, v, k):
                bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  60,000 random queries agree with the naive walk")

    print("\n--- mistakes LIVE ---")
    n, parent = 16, [-1] + list(range(15))
    short = build(n, parent, levels=int(math.log2(n - 1)))            # 3 levels: jumps 1, 2, 4
    w1 = query(short, 15, 15)
    ok = w1 != 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  only floor(log2(n-1)) = 3 levels: 15th ancestor of 15 -> {w1}, want 0")
    tree = [-1, 0, 0, 1, 1, 2, 2]
    unchecked = build(7, tree, levels=3, check_minus_one=False)
    w2 = query(unchecked, 1, 3)
    ok = w2 != -1
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  no -1 check (Python reads up[j-1][-1]): 3rd ancestor of 1 -> {w2}, want -1")
    wrong = 0
    for _ in range(200):
        n = rng.randint(5, 60)
        parent = random_tree(n, rng, shuffle=True)
        up = node_outer_bug(n, parent)
        wrong += any(query(up, v, k) != walk(parent, v, k) for v in range(n) for k in (2, 3, 5, 9))
    ok = wrong > 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  node-by-node fill on shuffled labels: wrong on {wrong} of 200 trees")

    print("\n--- scale: a 50,000-node path, 50,000 random queries ---")
    n = 50_000
    parent = [-1] + list(range(n - 1))
    queries = [(rng.randrange(n), rng.randint(1, n)) for _ in range(50_000)]
    t0 = time.perf_counter(); ta = TreeAncestor(n, parent); t1 = time.perf_counter()
    fast = [ta.getKthAncestor(v, k) for v, k in queries]; t2 = time.perf_counter()
    slow = [walk(parent, v, k) for v, k in queries[:2000]]; t3 = time.perf_counter()
    ok = fast[:2000] == slow
    all_ok &= ok
    print(f"      binary lifting: build {1000 * (t1 - t0):.0f} ms, 50,000 queries {1000 * (t2 - t1):.0f} ms")
    print(f"{'PASS' if ok else 'FAIL'}  walking parents: 2,000 queries alone took {1000 * (t3 - t2):.0f} ms "
          f"(about {25 * (t3 - t2):.0f} s for all 50,000); answers match")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
