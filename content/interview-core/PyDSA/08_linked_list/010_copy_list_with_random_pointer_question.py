"""
================================================================================
LeetCode 138 · Copy List with Random Pointer                          [Medium]
https://leetcode.com/problems/copy-list-with-random-pointer/
================================================================================

PROBLEM
-------
A linked list of length n is given such that each node contains an additional
random pointer, which could point to any node in the list, or null.

Construct a DEEP COPY of the list. The deep copy should consist of exactly n
brand new nodes, where each new node has its value set to the value of its
corresponding original node. Both the next and random pointer of the new
nodes should point to new nodes in the copied list, such that the pointers in
the original list and copied list represent the same list state. None of the
pointers in the new list should point to nodes in the original list.

For example, if there are two nodes X and Y in the original list, where
X.random --> Y, then for the corresponding two nodes x and y in the copied
list, x.random --> y.

Return the head of the copied linked list.

The list is represented in the input/output as a list of n nodes. Each node
is represented as a pair of [val, random_index] where random_index is the
index of the node (range from 0 to n-1) that the random pointer points to, or
null if it does not point to any node.

Your code will only be given the head of the original linked list.

EXAMPLES
--------
Example 1:
    Input:  head = [[7,null],[13,0],[11,4],[10,2],[1,0]]
    Output: [[7,null],[13,0],[11,4],[10,2],[1,0]]

Example 2:
    Input:  head = [[1,1],[2,1]]
    Output: [[1,1],[2,1]]

Example 3:
    Input:  head = [[3,null],[3,0],[3,null]]
    Output: [[3,null],[3,0],[3,null]]

CONSTRAINTS
-----------
    0 <= n <= 1000
    -10^4 <= Node.val <= 10^4
    Node.random is null or is pointing to some node in the linked list.

FOLLOW UP
---------
    Can you do it with O(1) extra space (not counting the output list)?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Note the class is called `Node`, not `ListNode` — it has an EXTRA pointer,
`random`, that can point anywhere in the list (including forward, backward,
to itself, or nowhere).

The obvious approach — build new nodes as you walk `.next` and set
`.random` immediately — breaks, because a node's `random` may point to a
node you haven't created yet (a forward reference). You need every node
mapped BEFORE you can safely wire up any `random` pointer.

Two ways to solve the ordering problem:
    1. Hashmap: old node -> new node. Two passes (or one pass + a second
       pass over the map). O(n) time, O(n) EXTRA space.
    2. Interleave-and-split (topic guide §5, Part 5 pattern 5): splice a
       copy of each node directly after its original, so "the copy of
       X.random" is always reachable as "X.random.next" — no map needed.
       O(n) time, O(1) extra space.


PROGRESSIVE HINTS
------------------
Hint 1: The hard part isn't `.next` — it's that `.random` can point FORWARD,
        to a node you haven't built a copy of yet.

Hint 2: A hashmap from old node -> new node solves the ordering problem
        directly: map every node first, then a second pass can look up
        `mapping[old.random]` safely no matter which direction it points.

Hint 3: Can you avoid the O(n) map? What if you glued each copy directly next
        to its original in the SAME list, so "the copy of any node" is
        always one `.next` hop away from that node?


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1) extra (the interleave trick) — O(n) is also acceptable and
           simpler to write first (hashmap approach).
================================================================================
"""

from typing import Optional


class Node:
    def __init__(self, x: int, next: "Optional[Node]" = None, random: "Optional[Node]" = None):
        self.val = int(x)
        self.next = next
        self.random = random


class Solution:
    def copyRandomList(self, head: "Optional[Node]") -> "Optional[Node]":
        # YOUR CODE HERE
        pass


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def build(pairs):
    """pairs: list of (val, random_index_or_None). Returns head."""
    if not pairs:
        return None
    nodes = [Node(v) for v, _ in pairs]
    for i in range(len(nodes) - 1):
        nodes[i].next = nodes[i + 1]
    for node, (_, ridx) in zip(nodes, pairs):
        node.random = nodes[ridx] if ridx is not None else None
    return nodes[0]


def to_pairs(head):
    """Serialize a Node list back to [(val, random_index_or_None), ...]
    using object identity to recover indices, LeetCode-style."""
    nodes = []
    node = head
    while node:
        nodes.append(node)
        node = node.next
    index_of = {id(n): i for i, n in enumerate(nodes)}
    return [(n.val, index_of[id(n.random)] if n.random else None) for n in nodes]


CASES = [
    [(7, None), (13, 0), (11, 4), (10, 2), (1, 0)],
    [(1, 1), (2, 1)],
    [(3, None), (3, 0), (3, None)],
    [],
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for pairs in CASES:
        head = build(pairs)
        copy_head = sol.copyRandomList(head)
        got = to_pairs(copy_head)
        ok = got == pairs
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  input={pairs!r} -> {got}")
    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
