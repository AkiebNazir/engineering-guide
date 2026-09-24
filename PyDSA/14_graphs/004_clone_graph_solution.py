"""
================================================================================
SOLUTION · LeetCode 133 · Clone Graph                                 [Medium]
https://leetcode.com/problems/clone-graph/
================================================================================

THE CORE IDEA
--------------
Traverse the graph (DFS or BFS, topic guide Part 2) exactly as you would for
any other graph problem, but replace the usual `visited` SET with a `dict`
mapping ORIGINAL node -> CLONED node. The set only answers "have I seen
this node" (enough for cycle-safety); cloning additionally needs "WHICH
clone corresponds to this original," because every time a node is
encountered again as someone else's neighbor, you must attach the SAME
clone object, not create a second one. Get this wrong and you either lose
the graph's shape (duplicate clones per node, edges pointing at the wrong
copy) or recurse forever (the graph is undirected and connected, so with 2+
nodes it always contains a cycle: A->B->A).

    clones = {}                       # original Node -> cloned Node
    def dfs(node):
        if node in clones: return clones[node]
        copy = Node(node.val)
        clones[node] = copy           # register BEFORE recursing — breaks cycles
        for nb in node.neighbors:
            copy.neighbors.append(dfs(nb))
        return copy

The line `clones[node] = copy` BEFORE the neighbor loop is the whole trick:
it means that when the DFS walks back around a cycle to `node` a second
time, `node in clones` is already True and the recursion returns the
existing clone instead of infinite-looping or making a duplicate.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, don't ship): BFS to collect every original node
into a list first, create ALL the clone objects up front (unlinked), THEN
do a second pass wiring up `copy.neighbors` by looking up each original
neighbor's clone in the mapping. Correct and actually a fine two-pass
alternative — O(V + E) time and space, same as the one-pass versions below —
but doing it in ONE pass (create-and-wire as you go) is simpler to write
live and is what's shown here.

Approach 1 (DFS, recursive) ✅ — the version above. Natural recursive shape:
each call is responsible for exactly one node's clone and its outgoing
edges. O(V + E) time, O(V) map + O(V) worst-case recursion depth (a
graph that's one long path/cycle).

Approach 2 (BFS, iterative with a deque) ✅: same one-pass idea, no
recursion. Create the start's clone and register it FIRST, then process a
queue of ORIGINAL nodes; for each, walk its neighbor list, creating and
registering any not-yet-seen neighbor's clone before wiring the edge.
O(V + E) time, O(V) space, no recursion depth ceiling — matters because
133's own constraint of 100 nodes is small, but the SHAPE of this bug
(recursion depth == graph size on a long path) generalizes to every DFS
traversal in this topic once problems allow bigger graphs.

⚠️  Approach X (broken on purpose) — visited SET instead of a node->clone
MAP: track `seen = set()` of original nodes and build clones as you go, but
without a way to look up "the clone for THIS specific original node" you
either (a) never terminate on a cycle because "seen" doesn't tell you where
the corresponding clone lives, so you keep allocating new Node objects for
the same original val forever, or (b) if you cut corners by keying clones
on `node.val` instead of the node object itself, you get a graph shaped
correctly by VALUE but built from a different bookkeeping structure than
intended — fragile the moment `Node.val` is not guaranteed unique (the
constraints here happen to guarantee it, but the technique is still wrong
in general and the point of this exercise is to use identity, not value).
Demoed live below with the actual failure mode measured, not asserted.


================================================================================
STEP BY STEP TRACE
================================================================================
adjList = [[2,4],[1,3],[2,4],[1,3]]      (nodes 1-2-3-4 in a 4-cycle)

        1 -- 2
        |    |
        4 -- 3

    dfs(1): 1 not in clones -> copy1=Node(1), clones={1:copy1}
        neighbor 2: dfs(2): 2 not in clones -> copy2=Node(2), clones={1:copy1,2:copy2}
            neighbor 1: dfs(1): 1 IN clones -> return copy1 (no new object, no recursion)
            copy2.neighbors = [copy1]
            neighbor 3: dfs(3): 3 not in clones -> copy3=Node(3), clones+={3:copy3}
                neighbor 2: dfs(2): 2 IN clones -> return copy2
                neighbor 4: dfs(4): 4 not in clones -> copy4=Node(4), clones+={4:copy4}
                    neighbor 1: dfs(1): 1 IN clones -> return copy1
                    neighbor 3: dfs(3): 3 IN clones -> return copy3
                    copy4.neighbors = [copy1, copy3]
                copy3.neighbors = [copy2, copy4]
            copy2.neighbors = [copy1, copy3]        (completed above)
        neighbor 4: dfs(4): 4 IN clones -> return copy4
        copy1.neighbors = [copy2, copy4]

    clones dict has exactly 4 entries — one clone per original node, no
    duplicates, even though dfs() was CALLED 8 times (once per directed
    edge-traversal in this 4-cycle) because 4 of those 8 calls hit the
    "already in clones" shortcut and returned immediately.

    result: node 1's clone has neighbors [2,4], matching the input exactly,
    and `id(clone_of_1) != id(original_1)` for every node — verified below.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time        Space              Mutates input?
    ---------------------------  ----------  -----------------  --------------
    Two-pass (collect, then wire) O(V + E)   O(V) map           no (builds new graph)
    DFS recursive (map) ✅         O(V + E)   O(V) map + O(V)    no
                                              worst-case stack
    BFS iterative (map) ✅         O(V + E)   O(V) map + queue   no
    "Broken": visited SET only    unbounded / O(V) if lucky by  no, but WRONG —
                                  infinite loop on any cycle     see demo

    None of the correct approaches mutate the input graph — they build an
    entirely disjoint set of Node objects. Contrast the grid problems
    (001-003) in this same folder, which mutate their input by design; this
    problem's whole POINT is that the output must NOT alias the input.


================================================================================
EDGE CASES
================================================================================
    node is None (empty graph)  -> return None immediately. Constraints allow
                                   0 nodes; this is the given signal for it.
    single node, no neighbors    -> clone it, empty neighbor list, done. No
                                   traversal needed beyond the one node.
    graph has a cycle             -> guaranteed by the problem the moment
                                   there are >= 2 connected nodes (undirected
                                   edges always create a 2-cycle at minimum:
                                   A->B and B->A). This is WHY the
                                   register-before-recurse ordering matters;
                                   it's not a rare adversarial case, it's the
                                   default shape of every real test here.
    node with multiple neighbors
    pointing back to earlier
    nodes (diamond / dense graph) -> exercises the "reuse the existing
                                   clone" path repeatedly; the trace above
                                   hits this on node 1's second visit.


================================================================================
COMMON MISTAKES
================================================================================
1. Using a `set()` of visited ORIGINAL nodes instead of a `dict` mapping
   original -> clone. A set can tell you "don't re-clone this node," but it
   cannot tell you WHICH clone to reuse when the node is encountered again
   as someone else's neighbor — you either can't finish the wiring or you
   end up creating duplicate clone objects per original node, corrupting
   the graph's shape (this is the #1 bug in this problem; demoed live).

2. Registering the new clone in the map AFTER recursing into its neighbors
   instead of BEFORE. Since the graph is guaranteed connected with a cycle
   whenever it has 2+ nodes, this re-enters the same original node before
   its clone is registered, and — because a set/dict-not-yet-populated
   check fails — recurses again, and again: `RecursionError` or an infinite
   loop depending on exact structure.

3. Keying the map on `node.val` instead of the `node` object itself. Works
   here because the constraints guarantee unique vals, but it's solving a
   different, weaker problem (dedupe-by-value) than what's actually being
   asked (dedupe-by-identity) and breaks the moment that constraint is
   relaxed elsewhere.

4. Forgetting that the graph is UNDIRECTED — appending only ONE direction
   of an edge to a clone's neighbor list (topic guide mistake #7,
   originally about adjacency lists) produces a clone graph with fewer
   edges than the original, even though each node's own `.neighbors` list
   is processed independently and should naturally include both directions
   if you don't filter anything out.

5. Returning `original_node` instead of a NEW `Node(...)` somewhere in the
   traversal (e.g. as a fallback in an incomplete branch) — the clone then
   silently ALIASES part of the input graph. `id(clone) == id(original)`
   for that one node, and mutating the clone later corrupts the original.
   Demoed live below alongside the visited-set failure.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How would you clone a graph that ISN'T guaranteed connected?
A: Loop over ALL known starting nodes (however they're provided — e.g. a
   list of every node in the graph) and run the same
   map-register-before-recurse DFS/BFS from each one not already in the
   map, exactly like 002/003's outer scan restarts a flood from every
   unvisited component.

Q: What if nodes also carry extra mutable state beyond `val` and
   `neighbors` (e.g. a dict of properties)?
A: Deep-copy that state too when creating each clone (`copy.properties =
   dict(node.properties)`, or `copy.deepcopy` for nested structures) —
   otherwise the "clone" still aliases mutable fields even though the Node
   objects themselves are distinct.

Q: Iterative or recursive — which would you choose and why?
A: Iterative BFS/DFS for the same reason as 001-003: no recursion-depth
   ceiling. 133's own cap (100 nodes) is small enough that recursion is
   safe in practice, but the technique generalizes, and saying so signals
   you know the tradeoff rather than got lucky with small constraints.

Q: How do you verify your clone is actually a DEEP copy, not just a
   structurally-equal graph that happens to share objects?
A: Compare `id()`s — no cloned node's `id()` should match any original
   node's `id()`. Comparing `.val`/`.neighbors` equality alone can't catch
   aliasing; comparing identity can. Exactly what the live demo below does.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Graph traversal where you must BUILD a parallel structure, not just visit
nodes (topic guide Part 2, with the visited-SET-vs-MAP distinction as the
defining wrinkle).

    LC 138  Copy List with Random Pointer  — identical idea, one dimension
                                             simpler (a linked list instead
                                             of a general graph); same
                                             original->clone MAP trick
    LC 116  Populating Next Right Pointers  — BFS over a graph-shaped tree,
             in Each Node                    building links instead of clones
    LC 1462 Course Schedule IV              — a different "build alongside a
                                             traversal" problem (reachability
                                             matrix) on a directed graph
    LC 785  Is Graph Bipartite?             — same traversal shape, builds a
                                             color map instead of a clone map
================================================================================
"""

import sys
from collections import deque
from typing import Dict, List, Optional


class Node:
    def __init__(self, val=0, neighbors=None):
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []


class Solution:
    def cloneGraph(self, node: Optional["Node"]) -> Optional["Node"]:
        """✅ THE ANSWER — recursive DFS with a node -> clone MAP.
        O(V + E) time, O(V) map + O(V) worst-case recursion depth. Does NOT
        mutate the input graph; builds an entirely disjoint set of nodes."""
        if node is None:
            return None

        clones: Dict[Node, Node] = {}

        def dfs(original: Node) -> Node:
            if original in clones:
                return clones[original]
            copy = Node(original.val)
            clones[original] = copy          # register BEFORE recursing — breaks cycles
            for neighbor in original.neighbors:
                copy.neighbors.append(dfs(neighbor))
            return copy

        return dfs(node)

    def cloneGraph_bfs(self, node: Optional["Node"]) -> Optional["Node"]:
        """BFS variant, same node -> clone MAP idea, iterative. O(V + E)
        time, O(V) map + queue, no recursion depth ceiling. Does NOT mutate
        the input."""
        if node is None:
            return None

        clones: Dict[Node, Node] = {node: Node(node.val)}
        queue = deque([node])
        while queue:
            original = queue.popleft()
            for neighbor in original.neighbors:
                if neighbor not in clones:
                    clones[neighbor] = Node(neighbor.val)
                    queue.append(neighbor)
                clones[original].neighbors.append(clones[neighbor])
        return clones[node]

    def cloneGraph_broken_visited_set(self, node: Optional["Node"]) -> Optional["Node"]:
        """✗ BROKEN ON PURPOSE — uses a visited SET (original nodes only)
        instead of a MAP to clones. A set can prevent re-cloning the SAME
        node once already visited, but has no way to hand back "the clone
        for this original," so every RE-ENCOUNTER of an already-visited
        node (guaranteed by any cycle) falls through to allocating a brand
        new Node — the clone graph ends up with far more nodes than the
        original, and a node's `.neighbors` can contain several distinct
        clone objects that all logically represent the same original node."""
        if node is None:
            return None

        visited: set = set()
        clone_start = Node(node.val)

        def dfs(original: Node, copy: Node):
            visited.add(original)
            for neighbor in original.neighbors:
                if neighbor in visited:
                    # No map to look up the EXISTING clone for `neighbor` —
                    # the best this broken version can do is fabricate a
                    # new, disconnected stand-in. This under-links the graph
                    # instead of reusing the real clone.
                    copy.neighbors.append(Node(neighbor.val))
                    continue
                neighbor_copy = Node(neighbor.val)
                copy.neighbors.append(neighbor_copy)
                dfs(neighbor, neighbor_copy)

        dfs(node, clone_start)
        return clone_start


# ==============================================================================
# TEST HELPERS — build a Node graph from / back to an adjacency list
# ==============================================================================
def build_graph(adj_list: List[List[int]]) -> Optional[Node]:
    if not adj_list:
        return None
    nodes: Dict[int, Node] = {i + 1: Node(i + 1) for i in range(len(adj_list))}
    for i, neighbors in enumerate(adj_list):
        nodes[i + 1].neighbors = [nodes[v] for v in neighbors]
    return nodes[1]


def to_adj_list(node: Optional[Node]) -> List[List[int]]:
    if node is None:
        return []
    by_val: Dict[int, Node] = {}
    queue = deque([node])
    by_val[node.val] = node
    while queue:
        cur = queue.popleft()
        for nb in cur.neighbors:
            if nb.val not in by_val:
                by_val[nb.val] = nb
                queue.append(nb)
    return [sorted(n.val for n in by_val[v].neighbors) for v in sorted(by_val)]


def all_nodes(node: Optional[Node]) -> List[Node]:
    """BFS collect every reachable node object (used for identity checks)."""
    if node is None:
        return []
    seen = {id(node): node}
    queue = deque([node])
    while queue:
        cur = queue.popleft()
        for nb in cur.neighbors:
            if id(nb) not in seen:
                seen[id(nb)] = nb
                queue.append(nb)
    return list(seen.values())


def make_cycle(n: int) -> Node:
    """A single n-node cycle: 1-2-3-...-n-1. Guarantees every node has
    exactly 2 neighbors and the whole thing is one connected component with
    a cycle, the worst case for "visited without a map" bugs."""
    nodes = [Node(i + 1) for i in range(n)]
    for i in range(n):
        nodes[i].neighbors = [nodes[(i - 1) % n], nodes[(i + 1) % n]]
    return nodes[0]


# ==============================================================================
# TESTS — run:  python 004_clone_graph_solution.py
# ==============================================================================
CASES = [
    [[2, 4], [1, 3], [2, 4], [1, 3]],
    [[]],
    [],
    [[2], [1]],
    [[2, 3], [1, 3], [1, 2]],
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: DFS and BFS clones match the original shape ---")
    for adj in CASES:
        original = build_graph(adj)
        dfs_clone = sol.cloneGraph(build_graph(adj))
        bfs_clone = sol.cloneGraph_bfs(build_graph(adj))
        got_dfs, got_bfs = to_adj_list(dfs_clone), to_adj_list(bfs_clone)
        ok = got_dfs == adj and got_bfs == adj
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  adjList={adj!r} -> DFS={got_dfs} "
              f"BFS={got_bfs}")

    # ----------------------------------------------------------------------
    # Identity check: every cloned node must be a DIFFERENT object than
    # every original node, val for val, structure intact.
    # ----------------------------------------------------------------------
    print("\n--- identity check: clones are FRESH objects, not aliases ---")
    original = build_graph([[2, 4], [1, 3], [2, 4], [1, 3]])
    clone = sol.cloneGraph(original)
    orig_nodes = all_nodes(original)
    clone_nodes = all_nodes(clone)
    orig_ids = {id(n) for n in orig_nodes}
    clone_ids = {id(n) for n in clone_nodes}
    no_shared_ids = orig_ids.isdisjoint(clone_ids)
    same_count = len(orig_nodes) == len(clone_nodes) == 4
    same_vals = sorted(n.val for n in orig_nodes) == sorted(n.val for n in clone_nodes)
    print(f"  original node ids: {sorted(orig_ids)}")
    print(f"  clone node ids:    {sorted(clone_ids)}")
    print(f"  no id overlap between original and clone: {no_shared_ids}")
    print(f"  exactly 4 distinct nodes on each side: {same_count}")
    print(f"  same multiset of vals: {same_vals}")
    all_ok &= no_shared_ids and same_count and same_vals

    # ----------------------------------------------------------------------
    # ⚠️  LIVE DEMO: visited SET (no map) vs visited MAP — measured, on a cycle.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: a visited SET is not enough — need a "
          "node->clone MAP ---")
    cycle_size = 6
    original_cycle = make_cycle(cycle_size)
    n_original = len(all_nodes(original_cycle))
    print(f"  original graph: a {cycle_size}-node cycle, "
          f"{n_original} distinct node objects")

    correct_clone = sol.cloneGraph(make_cycle(cycle_size))
    n_correct = len(all_nodes(correct_clone))
    print(f"  correct clone (node->clone MAP):  {n_correct} distinct node "
          f"objects (want {cycle_size})")

    broken_clone = sol.cloneGraph_broken_visited_set(make_cycle(cycle_size))
    n_broken = len(all_nodes(broken_clone))
    print(f"  broken clone (visited SET only):  {n_broken} distinct node "
          f"objects (want {cycle_size}, got MORE because re-encountered "
          f"nodes get re-fabricated instead of reused)")

    map_correct = n_correct == cycle_size
    set_broken = n_broken > cycle_size
    print(f"  map version produced exactly {cycle_size} nodes: {map_correct}")
    print(f"  set-only version over-produced nodes ({n_broken} > "
          f"{cycle_size}): {set_broken}")
    print("  Every time the broken traversal re-meets an already-visited")
    print("  original node, it has no way to look up 'the clone I already")
    print("  made for this' — a set only knows THAT it saw the node, not")
    print("  WHICH object to reuse — so it fabricates a disconnected")
    print("  stand-in clone instead. The graph's edge structure is also")
    print("  corrupted as a result (broken clone's shape no longer matches).")
    broken_shape = to_adj_list(broken_clone) != to_adj_list(make_cycle(cycle_size))
    print(f"  broken clone's adjacency shape differs from the true one: "
          f"{broken_shape}")
    all_ok &= map_correct and set_broken and broken_shape

    # ----------------------------------------------------------------------
    # Recursion depth: a long path graph (not a cycle) still isn't a real
    # RecursionError risk at 133's own 100-node cap, but demonstrate the
    # iterative BFS variant handles a much larger synthetic graph too.
    # ----------------------------------------------------------------------
    print("\n--- DFS vs BFS agree on a larger synthetic cycle ---")
    big_n = 500
    dfs_big = sol.cloneGraph(make_cycle(big_n))
    bfs_big = sol.cloneGraph_bfs(make_cycle(big_n))
    dfs_shape = to_adj_list(dfs_big)
    bfs_shape = to_adj_list(bfs_big)
    shapes_match = dfs_shape == bfs_shape
    print(f"  {big_n}-node cycle: DFS and BFS clones produce identical "
          f"adjacency shape: {shapes_match}")
    print(f"  sys.getrecursionlimit() = {sys.getrecursionlimit()}; DFS depth "
          f"for a {big_n}-node cycle stays well under it because each node "
          f"has only 2 neighbors and the SECOND one is always already "
          f"cloned, so the recursion doesn't chain node-to-node the way a "
          f"single-file grid snake does in 001-003.")
    all_ok &= shapes_match

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
