"""
================================================================================
LeetCode 1483 · Kth Ancestor of a Tree Node                               [Hard]
https://leetcode.com/problems/kth-ancestor-of-a-tree-node/
Topic: 10 · Binary Trees (and general rooted trees)
================================================================================

PROBLEM
-------
You are given a tree with n nodes numbered 0 to n - 1, as a parent array:
parent[i] is the parent of node i. The root is node 0, and parent[0] = -1.

Implement the TreeAncestor class:

    TreeAncestor(int n, int[] parent)   initialises the object.
    int getKthAncestor(int node, int k) returns the k-th ancestor of node,
                                        or -1 if there is no such ancestor.

The k-th ancestor is the k-th node on the path from node up to the root
(the 1st ancestor is the parent).


EXAMPLES
--------
    parent = [-1, 0, 0, 1, 1, 2, 2]

              0
            /   \
           1     2
          / \\   / \
         3   4 5   6

    getKthAncestor(3, 1) -> 1
    getKthAncestor(5, 2) -> 0
    getKthAncestor(6, 3) -> -1   (only two ancestors)


CONSTRAINTS
-----------
    1 <= k <= n <= 5 * 10^4
    parent.length == n, parent[0] == -1
    0 <= parent[i] < n for 0 < i < n
    At most 5 * 10^4 queries.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Walking up one parent at a time costs O(k) per query. On a path-shaped tree
with 50,000 nodes and 50,000 queries, that is up to 2.5 * 10^9 steps.

BINARY LIFTING precomputes jumps of every power-of-two length:

    up[j][v] = the 2^j-th ancestor of v   (-1 if it doesn't exist)
    up[0][v] = parent[v]
    up[j][v] = up[j-1][ up[j-1][v] ]      (two jumps of 2^(j-1))

Then any k is a sum of powers of two (its binary digits), so a query makes one
jump per set bit of k: at most about 16 jumps for k <= 5 * 10^4.


WHAT TO THINK ABOUT
--------------------
1. How many levels j do you need so that 2^j can cover every k <= n?

2. What must up[j][v] be when up[j-1][v] is already -1?

3. In what order must the table be filled so up[j-1][...] is ready?

4. In Python, what does list[-1] do if a -1 "no ancestor" sneaks in as an
   index?


PROGRESSIVE HINTS
------------------
Hint 1: LOG = n.bit_length() levels are enough (2^LOG > n).

Hint 2: Fill level by level (j outer, v inner). If the midpoint is -1, the
        result is -1.

Hint 3: Query: for each bit j set in k, node = up[j][node]; stop early if -1.


COMPLEXITY TARGET
------------------
    Build: O(n log n) time and space
    Query: O(log k)
================================================================================
"""
from typing import List


class TreeAncestor:
    def __init__(self, n: int, parent: List[int]):
        # YOUR CODE HERE
        pass

    def getKthAncestor(self, node: int, k: int) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 021_kth_ancestor_of_a_tree_node_question.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    t = TreeAncestor(7, [-1, 0, 0, 1, 1, 2, 2])
    for node, k, want in [(3, 1, 1), (5, 2, 0), (6, 3, -1), (0, 1, -1), (4, 2, 0)]:
        got = t.getKthAncestor(node, k)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  getKthAncestor({node}, {k})  got={got}  want={want}")

    # A path 0 <- 1 <- 2 <- ... <- 15 (n is a power of two: an off-by-one trap)
    path = TreeAncestor(16, [-1] + list(range(15)))
    for node, k, want in [(15, 15, 0), (15, 16, -1), (15, 8, 7), (9, 9, 0)]:
        got = path.getKthAncestor(node, k)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  path: getKthAncestor({node}, {k})  got={got}  want={want}")

    # Parents with LARGER indices than their children
    odd = TreeAncestor(5, [-1, 4, 1, 2, 0])          # chain 0 <- 4 <- 1 <- 2 <- 3
    for node, k, want in [(3, 4, 0), (3, 2, 1), (2, 3, 0), (3, 5, -1)]:
        got = odd.getKthAncestor(node, k)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  unordered: getKthAncestor({node}, {k})  got={got}  want={want}")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
