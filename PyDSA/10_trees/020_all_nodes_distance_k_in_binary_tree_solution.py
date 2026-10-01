r"""
================================================================================
SOLUTION · LeetCode 863 · All Nodes Distance K in Binary Tree           [Medium]
https://leetcode.com/problems/all-nodes-distance-k-in-binary-tree/
================================================================================

THE CORE IDEA
--------------
A binary tree is an undirected graph that only stores its DOWNWARD edges.
Add the upward edges with a parent map, and the question becomes "which nodes
are exactly k BFS levels away from target?" BFS needs a visited set now,
because with parent edges you can walk back to where you came from.


================================================================================
APPROACH 1 · Parent map + BFS ✅ (the answer)
================================================================================
    parent = {}                                   # built by one DFS
    queue, seen = deque([target]), {target}
    for _ in range(k):
        for _ in range(len(queue)):               # one full level
            node = queue.popleft()
            for nxt in (node.left, node.right, parent.get(node)):
                if nxt and nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
    return [node.val for node in queue]

After exactly k levels the queue holds the distance-k nodes and nothing else.

    Time: O(n)    Space: O(n) — parent map, visited set, queue


================================================================================
APPROACH 2 · Single DFS returning distance to target (no parent map)
================================================================================
dfs(node) returns the distance from node DOWN to target, or -1 if target is
not in node's subtree. Along the way it collects answers:

    - At target: collect nodes k levels down in target's subtree; return 0.
    - If dfs(node.left) returns d_left >= 0, target is in the LEFT subtree and
      node is d = d_left + 1 edges from it. If d == k, node itself is an
      answer; otherwise collect nodes (k - d - 1) levels down the RIGHT
      subtree (one edge to the right child, then k - d - 1 more). Return d.
    - Mirror for the right side.

    Time: O(n)    Space: O(h) recursion

Less memory, more index arithmetic. It's the version to reach for if the
interviewer says "no extra hash map".


================================================================================
APPROACH 3 · Convert to adjacency list, then BFS
================================================================================
Build a full graph {val: [neighbors]} from the tree and BFS by value. Same
complexity as Approach 1; slightly more memory; handy because values are
unique here.


================================================================================
STEP BY STEP TRACE · Example 1, target = 5, k = 2
================================================================================
                3
              /   \
             5     1
            / \   / \
           6   2 0   8
              / \
             7   4

    parent: 5->3, 1->3, 6->5, 2->5, 0->1, 8->1, 7->2, 4->2

    level 0  queue [5]            seen {5}
    level 1  pop 5: left 6, right 2, parent 3
             queue [6, 2, 3]      seen {5, 6, 2, 3}
    level 2  pop 6: no children, parent 5 (seen)
             pop 2: left 7, right 4, parent 5 (seen)
             pop 3: left 5 (seen), right 1, no parent
             queue [7, 4, 1]

    answer: [7, 4, 1]


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time   Space   Mutates input?
    ---------------------------  -----  ------  ---------------------------
    Parent map + BFS ✅          O(n)   O(n)    No
    DFS returning distance       O(n)   O(h)    No
    Adjacency list + BFS         O(n)   O(n)    No
    (Setting node.parent attrs)  O(n)   O(n)    YES — avoid; mutates the tree


================================================================================
EDGE CASES
================================================================================
    k == 0                     Just [target.val].
    k larger than tree height  Queue empties early; return [].
    target is the root         No parent; only downward nodes.
    target is a leaf           All answers come through parent edges.
    Single-node tree           [] unless k == 0.


================================================================================
COMMON MISTAKES
================================================================================
1. BFS without a visited set. Walking target -> child -> parent returns to
   target and counts it at distance 2. Demo below: Example 1 returns extra
   nodes.

2. Popping ALL nodes in one while loop instead of level by level, then losing
   track of the distance.

3. Keying the parent map by VALUE when values might repeat. Here values are
   unique, but node identity is always safe.

4. Only searching the target's subtree. Misses every node reached through an
   ancestor (node 1 in the example).

5. Adding `node.parent = ...` attributes to the input tree. Works, but mutates
   the caller's structure.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Many queries (different targets and k) on the same tree?
A: Build the parent map once. Each query is a BFS bounded by the nodes within
   distance k. For distance between arbitrary PAIRS, precompute depths and use
   LCA: dist(u, v) = depth[u] + depth[v] - 2 * depth[lca(u, v)], with binary
   lifting for O(log n) per query.

Q: Return nodes at distance <= k?
A: Collect every node dequeued during the first k + 1 levels.

Q: The tree is huge and stored on disk, one node per record?
A: The parent map is the expensive part. Store parent ids in the records
   (an index), then BFS reads only the O(nodes within k) records it needs.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 236   Lowest Common Ancestor (017)      — distance via LCA
    LC 2385  Amount of Time for Binary Tree to Be Infected — same parent-map BFS
    LC 1740  Find Distance in a Binary Tree
    LC 994   Rotting Oranges (14_graphs/006)   — level-by-level BFS
================================================================================
"""

import random
from collections import deque
from typing import Dict, List, Optional


class TreeNode:
    def __init__(self, x):
        self.val = x
        self.left = None
        self.right = None


class Solution:
    def distanceK(self, root: TreeNode, target: TreeNode, k: int) -> List[int]:
        parent: Dict[TreeNode, Optional[TreeNode]] = {root: None}
        stack = [root]
        while stack:                                  # iterative DFS: no recursion limit worries
            node = stack.pop()
            for child in (node.left, node.right):
                if child:
                    parent[child] = node
                    stack.append(child)

        queue = deque([target])
        seen = {target}
        for _ in range(k):
            if not queue:
                return []
            for _ in range(len(queue)):
                node = queue.popleft()
                for nxt in (node.left, node.right, parent[node]):
                    if nxt is not None and nxt not in seen:
                        seen.add(nxt)
                        queue.append(nxt)
        return [node.val for node in queue]


# ------------------------------------------------------------------------
# Alternatives / oracle / broken version for the demos.
# ------------------------------------------------------------------------
def distance_k_dfs(root: TreeNode, target: TreeNode, k: int) -> List[int]:
    """Approach 2: DFS returning distance to target, no parent map."""
    out: List[int] = []

    def collect_down(node: Optional[TreeNode], depth: int) -> None:
        if node is None or depth < 0:
            return
        if depth == 0:
            out.append(node.val)
            return
        collect_down(node.left, depth - 1)
        collect_down(node.right, depth - 1)

    def dfs(node: Optional[TreeNode]) -> int:
        if node is None:
            return -1
        if node is target:
            collect_down(node, k)
            return 0
        for here, other in ((node.left, node.right), (node.right, node.left)):
            d = dfs(here)
            if d >= 0:
                dist = d + 1                     # distance from node to target
                if dist == k:
                    out.append(node.val)
                else:
                    collect_down(other, k - dist - 1)
                return dist
        return -1

    dfs(root)
    return out


def distance_k_no_visited_bug(root: TreeNode, target: TreeNode, k: int) -> List[int]:
    """Mistake 1: BFS over parent edges without a visited set."""
    parent: Dict[TreeNode, Optional[TreeNode]] = {root: None}
    stack = [root]
    while stack:
        node = stack.pop()
        for child in (node.left, node.right):
            if child:
                parent[child] = node
                stack.append(child)
    queue = deque([target])
    for _ in range(k):
        for _ in range(len(queue)):
            node = queue.popleft()
            for nxt in (node.left, node.right, parent[node]):
                if nxt is not None:
                    queue.append(nxt)           # BUG: may walk straight back
    return [node.val for node in queue]


def distance_k_oracle(root: TreeNode, target: TreeNode, k: int) -> List[int]:
    """Undirected adjacency by value + all-distances BFS."""
    adj: Dict[int, List[int]] = {}
    stack = [root]
    while stack:
        node = stack.pop()
        adj.setdefault(node.val, [])
        for child in (node.left, node.right):
            if child:
                adj[node.val].append(child.val)
                adj.setdefault(child.val, []).append(node.val)
                stack.append(child)
    dist = {target.val: 0}
    q = deque([target.val])
    while q:
        v = q.popleft()
        for w in adj[v]:
            if w not in dist:
                dist[w] = dist[v] + 1
                q.append(w)
    return [v for v, d in dist.items() if d == k]


def build(vals: List[Optional[int]]) -> Optional[TreeNode]:
    if not vals or vals[0] is None:
        return None
    root = TreeNode(vals[0])
    queue = deque([root])
    i = 1
    while queue and i < len(vals):
        node = queue.popleft()
        if i < len(vals) and vals[i] is not None:
            node.left = TreeNode(vals[i])
            queue.append(node.left)
        i += 1
        if i < len(vals) and vals[i] is not None:
            node.right = TreeNode(vals[i])
            queue.append(node.right)
        i += 1
    return root


def find(root: Optional[TreeNode], val: int) -> Optional[TreeNode]:
    stack = [root]
    while stack:
        node = stack.pop()
        if node is None:
            continue
        if node.val == val:
            return node
        stack.extend((node.left, node.right))
    return None


def random_tree(rng: random.Random, n: int) -> TreeNode:
    nodes = [TreeNode(i) for i in range(n)]
    for i in range(1, n):
        while True:
            p = nodes[rng.randrange(i)]
            side = rng.choice(("left", "right"))
            if getattr(p, side) is None:
                setattr(p, side, nodes[i])
                break
    return nodes[0]


# ==============================================================================
# TESTS — run:  python 020_all_nodes_distance_k_in_binary_tree_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()
    ex = [3, 5, 1, 6, 2, 0, 8, None, None, 7, 4]

    print("--- correctness: BFS vs DFS on examples and edge cases ---")
    cases = [
        (ex, 5, 2, [1, 4, 7]),
        ([1], 1, 3, []),
        (ex, 5, 0, [5]),
        (ex, 7, 3, [3, 6]),
        (ex, 3, 1, [1, 5]),
        (ex, 8, 4, [2, 6]),
        ([0, 1, None, 3, 2], 2, 1, [1]),
        (ex, 3, 10, []),
    ]
    for vals, t, k, want in cases:
        root = build(vals)
        target = find(root, t)
        a = sorted(sol.distanceK(root, target, k))
        b = sorted(distance_k_dfs(root, target, k))
        ok = a == b == sorted(want)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  target={t} k={k:<2}  bfs={a}  dfs={b}  want={sorted(want)}")

    print("\n--- randomized cross-check vs adjacency-list oracle (300 trees) ---")
    rng = random.Random(863)
    bad = 0
    for _ in range(300):
        n = rng.randint(1, 60)
        root = random_tree(rng, n)
        target = find(root, rng.randrange(n))
        k = rng.randint(0, 8)
        want = sorted(distance_k_oracle(root, target, k))
        if sorted(sol.distanceK(root, target, k)) != want or sorted(distance_k_dfs(root, target, k)) != want:
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  300 random trees: BFS and DFS match the oracle")

    print("\n--- mistake 1 LIVE: no visited set ---")
    root = build(ex)
    target = find(root, 5)
    wrong = sorted(distance_k_no_visited_bug(root, target, 2))
    right = sorted(sol.distanceK(root, target, 2))
    ok = wrong != right and right == [1, 4, 7]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  target=5, k=2: no-visited returns {wrong}, correct {right}")
    print("      5 -> 6 -> back to parent 5, and 5 -> 3 -> back to child 5: the target")
    print("      itself shows up at 'distance 2', along with duplicates")

    print("\n--- deep tree: iterative parent map survives where recursion would not ---")
    import sys
    n = sys.getrecursionlimit() * 3
    nodes = [TreeNode(i) for i in range(n)]
    for i in range(n - 1):
        nodes[i].left = nodes[i + 1]
    got = sol.distanceK(nodes[0], nodes[n // 2], 5)
    ok = sorted(got) == [n // 2 - 5, n // 2 + 5]
    all_ok &= ok
    try:
        distance_k_dfs(nodes[0], nodes[n // 2], 5)
        rec = "completed"
    except RecursionError:
        rec = "RecursionError"
    print(f"{'PASS' if ok else 'FAIL'}  path of {n} nodes: BFS answer {sorted(got)}; recursive DFS -> {rec}")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
