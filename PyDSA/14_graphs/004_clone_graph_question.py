"""
================================================================================
QUESTION · LeetCode 133 · Clone Graph                                 [Medium]
https://leetcode.com/problems/clone-graph/
================================================================================

PROBLEM
-------
Given a reference to a node in a CONNECTED undirected graph, return a DEEP
COPY (clone) of the graph. Each node in the graph contains a value (`int`)
and a list of its neighbors (`List[Node]`).

    class Node:
        def __init__(self, val=0, neighbors=None):
            self.val = val
            self.neighbors = neighbors if neighbors is not None else []

Test case format (for your understanding, not what your function receives):
the graph is given as an adjacency list, where `adjList[i]` is a list of
`[val_of_neighbor]` for the node with `val = i + 1`. The first node is
always `1`. You are handed the `Node` object for that first node; you must
return the `Node` object that is the clone's equivalent starting point.


EXAMPLES
--------
Example 1:
    Input:  adjList = [[2,4],[1,3],[2,4],[1,3]]
    Output: [[2,4],[1,3],[2,4],[1,3]]

        1 -- 2          Node 1's neighbors: [2, 4]
        |    |          Node 2's neighbors: [1, 3]
        4 -- 3          Node 3's neighbors: [2, 4]
                         Node 4's neighbors: [1, 3]

    The output must be a graph with the SAME shape, but every single Node
    object must be a NEW object — none of the returned nodes may be `is`
    any node from the input.

Example 2:
    Input:  adjList = [[]]
    Output: [[]]

        1 (no neighbors) — a single isolated node, its own connected graph.

Example 3:
    Input:  adjList = []
    Output: []

        The graph is empty; the input node itself is `None`.


CONSTRAINTS
-----------
    The number of nodes in the graph is in the range [0, 100].
    1 <= Node.val <= 100
    Node.val is unique for each node.
    There are no repeated edges and no self-loops in the graph.
    The Graph is connected and all nodes can be visited starting from the
    given node.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is graph traversal (topic guide Part 2) with a twist: instead of just
VISITING every node, you must CREATE a parallel structure — one clone per
original node, with the clones wired to each other in exactly the same
pattern as the originals. A plain `visited` set (which only answers "have I
seen this node?") is not enough, because when you first meet a node you
must also remember WHICH CLONE corresponds to it, so that when you meet it
again (as someone else's neighbor) you reuse the same clone instead of
creating a duplicate. That means the visited-tracking structure must be a
MAPPING from original node -> cloned node, not a set. This is exercised
directly by the solution file's live demo.


PROGRESSIVE HINTS
------------------
Hint 1: DFS or BFS from the given start node, same traversal shape as any
        other graph problem in this topic. The difference is what you do at
        each node: create its clone (if you haven't already) instead of
        just marking it seen.

Hint 2: Use a `dict` mapping `original_node -> cloned_node`. Before
        recursing/enqueuing into a neighbor, check the dict first — if the
        neighbor's clone already exists, reuse it (this is what breaks
        infinite loops on a graph with cycles, which this graph has by
        definition since it's undirected and connected with >= 2 nodes).

Hint 3: The graph is UNDIRECTED — every edge appears in both directions
        (node A's neighbor list contains B, and B's neighbor list contains
        A). Your clone must preserve both directions too; you don't need to
        do anything special for this beyond visiting every node's full
        neighbor list, since each node processes its own list independently.


COMPLEXITY TARGET
------------------
    Time:  O(V + E) — every node and every edge visited once
    Space: O(V) — the mapping, plus O(V) recursion/queue depth worst case
================================================================================
"""

from collections import deque
from typing import Dict, List, Optional


class Node:
    def __init__(self, val=0, neighbors=None):
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []


class Solution:
    def cloneGraph(self, node: Optional["Node"]) -> Optional["Node"]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TEST HELPERS — build a Node graph from / back to an adjacency list
# ==============================================================================
def build_graph(adj_list: List[List[int]]) -> Optional[Node]:
    """adjList[i] = neighbor VALUES of the node with val = i+1 -> Node graph,
    returns the node with val == 1 (or None for an empty graph)."""
    if not adj_list:
        return None
    nodes: Dict[int, Node] = {i + 1: Node(i + 1) for i in range(len(adj_list))}
    for i, neighbors in enumerate(adj_list):
        nodes[i + 1].neighbors = [nodes[v] for v in neighbors]
    return nodes[1]


def to_adj_list(node: Optional[Node]) -> List[List[int]]:
    """Node graph -> adjList sorted by val, via BFS. Inverse of build_graph."""
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
    return [sorted(n.val for n in by_val[v].neighbors)
            for v in sorted(by_val)]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        [[2, 4], [1, 3], [2, 4], [1, 3]],
        [[]],
        [],
        [[2], [1]],
    ]
    for adj in cases:
        original = build_graph(adj)
        clone = sol.cloneGraph(original)
        got = to_adj_list(clone)
        ok = got == adj
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  adjList={adj!r} -> {got} (want {adj!r})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
