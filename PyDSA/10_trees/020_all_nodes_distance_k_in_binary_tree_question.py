r"""
================================================================================
LeetCode 863 · All Nodes Distance K in Binary Tree                      [Medium]
https://leetcode.com/problems/all-nodes-distance-k-in-binary-tree/
Topic: 10 · Trees
================================================================================

PROBLEM
-------
Given the root of a binary tree, the value of a target node `target`, and an
integer k, return an array of the values of all nodes that have a distance k
from the target node.

You can return the answer in any order.


EXAMPLES
--------
Example 1:
    Input:  root = [3,5,1,6,2,0,8,null,null,7,4], target = 5, k = 2
    Output: [7, 4, 1]

                3            distance from 5:
              /   \              5 -> 0
             5     1             6, 2, 3 -> 1
            / \   / \            7, 4, 1 -> 2   <- answer
           6   2 0   8           0, 8 -> 3
              / \
             7   4

Example 2:
    Input:  root = [1], target = 1, k = 3
    Output: []


CONSTRAINTS
-----------
    The number of nodes in the tree is in the range [1, 500].
    0 <= Node.val <= 500
    All the values Node.val are unique.
    target is the value of one of the nodes in the tree.
    0 <= k <= 1000


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Distance here means the number of EDGES on the path between two nodes, and a
path can go UP through a parent. In Example 1, node 1 is at distance 2 from 5:
up to 3, then down to 1.

A tree node only points DOWN to its children. That's the whole difficulty:
you need to move upward too. Two standard fixes:

    1. Add the missing edges: record each node's parent, then the tree is just
       an undirected graph. Run BFS from the target for k levels.
    2. Stay recursive: a DFS that returns "how far below me is the target?"
       lets each ancestor collect nodes in its OTHER subtree at the remaining
       distance.


WHAT TO THINK ABOUT
--------------------
1. Once you have parent pointers, why does BFS need a visited set? (It
   didn't in plain tree traversal.)

2. BFS processes nodes level by level. How do you stop exactly at level k?

3. The function signature gives you the TARGET NODE, not just a value. Can
   you compare nodes by identity?


PROGRESSIVE HINTS
------------------
Hint 1: DFS once to build parent = {child: parent}.

Hint 2: BFS from target over neighbors (left, right, parent[node]), with a
        visited set.

Hint 3: Process the queue one level at a time. After k levels, the queue
        holds exactly the answer.


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(n)
================================================================================
"""

from collections import deque
from typing import List, Optional


class TreeNode:
    def __init__(self, x):
        self.val = x
        self.left = None
        self.right = None


class Solution:
    def distanceK(self, root: TreeNode, target: TreeNode, k: int) -> List[int]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TEST HELPERS — level-order list with None for absent children
# ==============================================================================
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
    if root is None or root.val == val:
        return root
    return find(root.left, val) or find(root.right, val)


# ==============================================================================
# TESTS — run:  python 020_all_nodes_distance_k_in_binary_tree_question.py
# ==============================================================================
def run_tests() -> None:
    ex = [3, 5, 1, 6, 2, 0, 8, None, None, 7, 4]
    cases = [
        (ex, 5, 2, [1, 4, 7]),
        ([1], 1, 3, []),
        (ex, 5, 0, [5]),
        (ex, 7, 3, [3, 6]),
        (ex, 3, 1, [1, 5]),
        (ex, 8, 4, [2, 6]),
        ([0, 1, None, 3, 2], 2, 1, [1]),
    ]
    all_ok = True
    for vals, t, k, want in cases:
        root = build(vals)
        got = Solution().distanceK(root, find(root, t), k)
        ok = got is not None and sorted(got) == sorted(want)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  target={t} k={k}  got={got}  want={want}")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
