"""
================================================================================
SOLUTION · LeetCode 700 · Search in a Binary Search Tree               [Easy]
https://leetcode.com/problems/search-in-a-binary-search-tree/
================================================================================

THE CORE IDEA
--------------
One comparison per node throws away an entire subtree. That is the whole
value of a BST, and it rests entirely on the invariant (topic guide §1.1):

    EVERY value in node.left's SUBTREE  <  node.val  <  EVERY value in
    node.right's SUBTREE

Because the bound is subtree-wide and not merely parent-to-child, `val <
node.val` proves `val` is absent from the ENTIRE right subtree — not just
from `node.right` itself. So you may prune it unexamined:

    while node:
        if val == node.val: return node
        node = node.left if val < node.val else node.right
    return None

O(h) time where h is the tree HEIGHT, O(1) space. Say "O(h)", not
"O(log n)" — h == log n only when the tree is balanced, and nothing in the
BST contract guarantees that (§3 of the topic guide, and the height demo
below measures a real degenerate case).


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, state it and price it, don't ship it): ignore the
ordering and search like a plain binary tree (topic 10) — visit every node
via DFS/BFS until you find `val`. O(n) time, O(h) space. It is correct on a
BST, and it is exactly what you must NOT write: it discards the one property
that distinguishes this topic from topic 10. If your recursion has two
recursive calls in it, you wrote this by accident.

Approach 1 (recursive descent) — the natural expression of the invariant:

    def searchBST(root, val):
        if root is None or root.val == val:
            return root
        if val < root.val:
            return self.searchBST(root.left, val)
        return self.searchBST(root.right, val)

O(h) time, O(h) space for the call stack. Note both recursive calls are in
`return` position — this is tail recursion, and CPython does not eliminate
tail calls, so the frames really are allocated. On a degenerate BST of 5000
nodes (the problem's stated maximum) this raises `RecursionError`; the demo
below proves that at runtime.

Approach 2 (iterative descent) ✅ — the answer. Same three cases, one
`while` loop, O(1) space, no recursion ceiling. Prefer it: the recursion
buys nothing here because there is no backtracking to unwind.

Approach 3 (for completeness): if you were handed a sorted ARRAY instead of
a BST you would binary search it in guaranteed O(log n) (topic 05). Same
halving idea; different cost profile. See "vs topic 05" below.


================================================================================
O(h) IS NOT O(log n) — AND WHY THAT MATTERS HERE
================================================================================
Topic 05's binary search over a sorted array is O(log n) *guaranteed*: the
midpoint is computed arithmetically, so the halving is exact by
construction. A BST only halves as well as its shape allows. The tree's
shape is a historical artifact of the insertion order:

    inserted 1,2,3,4,5 in order        inserted 3,1,4,2,5 (shuffled)
      1                                    3
       ╲                                  ╱ ╲
        2                                1   4
         ╲                                ╲    ╲
          3                                2    5
           ╲
            4                            height 3, search touches <= 3 nodes
             ╲
              5

    height 5, search for 5 touches
    all 5 nodes: this is a linked list
    wearing a tree costume

Both are valid BSTs. Both satisfy the invariant. One searches in 3 steps and
one in 5, and the gap grows as O(n) vs O(log n) with size. The demo below
builds both at n = 4000 and prints the measured heights and search times.


================================================================================
STEP BY STEP TRACE
================================================================================
tree = [4,2,7,1,3], val = 3

            4
           ╱ ╲
          2   7
         ╱ ╲
        1   3

    node=4   3 < 4  -> prune the ENTIRE right subtree (7 and everything
                        under it). We never look at node 7 at all.
    node=2   3 > 2  -> prune left (node 1). Go right.
    node=3   3 == 3 -> return this node. Its subtree is [3].

    3 nodes visited out of 5. On a balanced tree of 5000 nodes it would be
    ~13 out of 5000.

tree = [4,2,7,1,3], val = 5

    node=4   5 > 4  -> right
    node=7   5 < 7  -> left
    node=None        -> loop ends, return None

    The "absent" case costs exactly the same O(h): you walk off the bottom.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time    Space   Mutates input?  Note
    ---------------------------  ------  ------  --------------  -------------------
    Plain-tree DFS (ignore BST)  O(n)    O(h)    no              throws the topic away
    Recursive descent            O(h)    O(h)    no              RecursionError on a
                                                                 degenerate 5000-node
                                                                 tree — demoed below
    Iterative descent ✅          O(h)    O(1)    no              the answer
    (reference: sorted array)    O(log n) O(1)   no              guaranteed halving,
                                                                 unlike a BST

    h = height. h == ceil(log2(n+1)) for a perfectly balanced tree,
    h == n for a chain. Both are legal BSTs.


================================================================================
EDGE CASES
================================================================================
    root is None            -> return None. (LeetCode's constraints say >= 1
                                node, but the recursion hits None on every
                                miss, so the None guard is not optional.)
    val == root.val          -> return the whole tree, immediately, 1 comparison.
    val is a leaf            -> full-height walk, the worst case for a hit.
    val absent, val < min    -> walks the entire left spine, then falls off.
    val absent, val > max    -> walks the entire right spine, then falls off.
    single-node tree          -> exercises "hit at root" and "immediate miss".
    degenerate (chain) tree   -> h == n; the recursive variant dies here.


================================================================================
COMMON MISTAKES
================================================================================
1. Recursing into BOTH children (`left = search(root.left); right =
   search(root.right)`). That is a plain-binary-tree search: correct answer,
   O(n), and it silently proves you did not use the BST property. This is
   the single most common way to "solve" 700 and still fail the interview.

2. Comparing against `root.left.val` / `root.right.val` instead of
   `root.val` to decide direction. It works on tiny trees by luck and breaks
   the moment the target lives two or more levels down.

3. Forgetting the `None` check before `node.val`, giving
   `AttributeError: 'NoneType' object has no attribute 'val'` on every miss.

4. Returning `True`/`False` or `root.val` instead of the NODE. The problem
   asks for the subtree — return the node object itself.

5. Claiming O(log n) in the complexity answer without saying "assuming the
   tree is balanced". Interviewers listen for exactly this; the honest
   answer is O(h) with h up to n.

6. Reaching for recursion by default. It is tail-recursive, CPython will not
   optimise it away, and the iterative form is strictly better here: fewer
   lines, O(1) space, no ceiling.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What is the worst case, and how do you fix it?
A: A chain (h == n), produced by inserting sorted data. Fix it with a
   self-balancing BST — AVL or a red-black tree — which rotates on insert to
   keep h == O(log n). Python ships no balanced BST in the stdlib; the
   practical substitutes are `sortedcontainers.SortedList` (a B-tree-ish
   list-of-lists, O(sqrt(n)) insert with tiny constants), `bisect` over a
   plain list (O(log n) search, O(n) insert), or a heap when you only need
   the extremes. Topic guide §3 prices all three.

Q: Return the node's PARENT as well.
A: Keep a `parent` variable that lags one step behind `node` in the loop —
   the same fixed-gap trick problem 003 (insert) needs, and 004 (delete)
   needs too.

Q: The tree is huge and lives on disk / across machines. Still a BST?
A: No — a binary node is one pointer hop per comparison, i.e. one disk seek
   per level. Databases use B-trees/B+trees: high fan-out (hundreds of keys
   per node) so the height is 3-4 instead of 30, matching the page size of
   the storage device. Same ordering idea, tuned for block I/O.

Q: Count how many nodes are less than `val`?
A: Not O(h) on a bare BST — you would in-order walk, O(n). Augment each node
   with its subtree size and it becomes O(h). Problem 007 (kth smallest)
   develops exactly that augmentation.

Q: What if values may repeat?
A: The invariant has to be tightened to a convention: duplicates all go
   left (`<=`), or all go right (`>=`), or each node carries a count. Say
   which one you picked out loud — problem 006 (validate) shows why "either
   side" makes the tree unsearchable.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Pattern 1 of the topic guide's taxonomy: O(h) descent by comparison.

    LC 701  Insert into a BST              — descent that ends at a leaf (003)
    LC 450  Delete Node in a BST            — descent, then structural surgery (004)
    LC 235  LCA of a BST                    — descent to the split point (005)
    LC 938  Range Sum of BST                — the same pruning, summing a window
    LC 1038 BST to Greater Sum Tree         — reverse in-order accumulation
    LC 270  Closest Binary Search Tree Value — descent tracking the best-so-far
    LC 285  Inorder Successor in BST         — descent tracking the last left-turn
    LC 653  Two Sum IV - Input is a BST      — this search inside a traversal,
                                                or two-pointer over the in-order
    LC 704  Binary Search (topic 05, 001)   — the array version, guaranteed
                                                O(log n) instead of O(h)
================================================================================
"""

import random
import sys
import time
from collections import deque
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def searchBST(self, root: Optional[TreeNode], val: int) -> Optional[TreeNode]:
        """✅ THE ANSWER — iterative descent. O(h) time, O(1) space."""
        node = root
        while node:
            if val == node.val:
                return node
            node = node.left if val < node.val else node.right
        return None

    # ------------------------------------------------------------------
    # Variants, for comparison.
    # ------------------------------------------------------------------
    def searchBST_recursive(self, root: Optional[TreeNode],
                            val: int) -> Optional[TreeNode]:
        """Recursive descent. O(h) time, O(h) call-stack space. Tail calls are
        NOT eliminated by CPython, so a degenerate tree raises RecursionError."""
        if root is None or root.val == val:
            return root
        if val < root.val:
            return self.searchBST_recursive(root.left, val)
        return self.searchBST_recursive(root.right, val)

    def searchBST_plain_tree(self, root: Optional[TreeNode],
                             val: int) -> Optional[TreeNode]:
        """✗ THE ANTI-PATTERN (correct, but O(n)) — a topic-10 plain-tree
        search that ignores the ordering and cannot prune anything. Kept only
        as a baseline for the visited-node count demo."""
        if root is None:
            return None
        if root.val == val:
            return root
        return (self.searchBST_plain_tree(root.left, val)
                or self.searchBST_plain_tree(root.right, val))


# ==============================================================================
# TEST HELPERS — shared with topic 10 (plain binary trees), verbatim
# ==============================================================================
def build(values):
    """LeetCode level-order list (with `None` holes) -> root TreeNode."""
    if not values or values[0] is None:
        return None
    root = TreeNode(values[0])
    queue = deque([root])
    i = 1
    while queue and i < len(values):
        node = queue.popleft()
        if i < len(values):
            v = values[i]
            i += 1
            if v is not None:
                node.left = TreeNode(v)
                queue.append(node.left)
        if i < len(values):
            v = values[i]
            i += 1
            if v is not None:
                node.right = TreeNode(v)
                queue.append(node.right)
    return root


def to_level_order(root):
    """Inverse of build(): level-order list with `None` for absent children,
    trailing `None`s trimmed."""
    if root is None:
        return []
    out, queue = [], deque([root])
    while queue:
        node = queue.popleft()
        if node is None:
            out.append(None)
            continue
        out.append(node.val)
        queue.append(node.left)
        queue.append(node.right)
    while out and out[-1] is None:
        out.pop()
    return out


def bst_insert_iterative(root, val):
    """Iterative BST insert — used to BUILD demo trees. Safe on a chain of any
    depth (no recursion). Problem 003 develops this properly."""
    node = TreeNode(val)
    if root is None:
        return node
    curr = root
    while True:
        if val < curr.val:
            if curr.left is None:
                curr.left = node
                return root
            curr = curr.left
        else:
            if curr.right is None:
                curr.right = node
                return root
            curr = curr.right


def height_iterative(root):
    """Height in EDGES + 1 (node count on the longest root-to-leaf path).
    Iterative on purpose: a recursive height() blows the stack on the very
    degenerate trees this file is built to demonstrate."""
    if root is None:
        return 0
    best = 0
    stack = [(root, 1)]
    while stack:
        node, depth = stack.pop()
        if depth > best:
            best = depth
        if node.left:
            stack.append((node.left, depth + 1))
        if node.right:
            stack.append((node.right, depth + 1))
    return best


def count_visited_descent(root, val):
    """Nodes examined by the O(h) descent."""
    n, node = 0, root
    while node:
        n += 1
        if val == node.val:
            return n
        node = node.left if val < node.val else node.right
    return n


def count_visited_plain(root, val):
    """Nodes examined by the O(n) plain-tree DFS (pre-order, short-circuiting)."""
    if root is None:
        return 0
    n = 0
    stack = [root]
    while stack:
        node = stack.pop()
        n += 1
        if node.val == val:
            return n
        if node.right:
            stack.append(node.right)
        if node.left:
            stack.append(node.left)
    return n


# ==============================================================================
# TESTS — run:  python 001_search_in_a_binary_search_tree_solution.py
# ==============================================================================
CASES = [
    ([4, 2, 7, 1, 3], 2, [2, 1, 3]),
    ([4, 2, 7, 1, 3], 5, []),
    ([4, 2, 7, 1, 3], 4, [4, 2, 7, 1, 3]),
    ([4, 2, 7, 1, 3], 7, [7]),
    ([4, 2, 7, 1, 3], 1, [1]),
    ([4, 2, 7, 1, 3], 3, [3]),
    ([1], 1, [1]),
    ([1], 2, []),
    ([8, 3, 10, 1, 6, None, 14, None, None, 4, 7, 13], 6, [6, 4, 7]),
    ([8, 3, 10, 1, 6, None, 14, None, None, 4, 7, 13], 13, [13]),
    ([8, 3, 10, 1, 6, None, 14, None, None, 4, 7, 13], 5, []),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: iterative descent ---")
    for values, val, want in CASES:
        got = to_level_order(sol.searchBST(build(values), val))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  tree={values!r:<48} val={val:<4} "
              f"-> {got}  (want {want})")

    print("\n--- correctness: recursive variant cross-check ---")
    for values, val, want in CASES:
        got = to_level_order(sol.searchBST_recursive(build(values), val))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  recursive val={val:<4} -> {got}")

    # ----------------------------------------------------------------------
    # Trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: tree=[4,2,7,1,3], val=3 ---")
    node = build([4, 2, 7, 1, 3])
    target = 3
    while node:
        if target == node.val:
            print(f"  at {node.val}: equal -> return this node")
            break
        direction = "left" if target < node.val else "right"
        pruned = "right" if direction == "left" else "left"
        print(f"  at {node.val}: {target} {'<' if target < node.val else '>'} "
              f"{node.val} -> go {direction}, prune the whole {pruned} subtree")
        node = node.left if target < node.val else node.right

    # ----------------------------------------------------------------------
    # Randomised cross-check against the O(n) plain-tree oracle.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n) plain-tree search ---")
    random.seed(700)
    mismatches, trials = 0, 2000
    for _ in range(trials):
        vals = random.sample(range(1, 200), random.randint(1, 25))
        root = None
        for v in vals:
            root = bst_insert_iterative(root, v)
        probe = random.choice(vals) if random.random() < 0.5 else random.randint(1, 250)
        a = sol.searchBST(root, probe)
        b = sol.searchBST_plain_tree(root, probe)
        if (a is None) != (b is None) or (a is not None and a is not b):
            mismatches += 1
    print(f"  {trials} random BSTs: {mismatches} mismatches "
          f"(identity-compared, not value-compared)")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 1: pruning is real — count nodes actually examined.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 1: nodes EXAMINED, O(h) descent vs O(n) plain-tree DFS ---")
    random.seed(1)
    print(f"  {'n':>7} {'height':>7} {'descent':>9} {'plain DFS':>11} {'ratio':>8}")
    for n in (100, 1_000, 10_000):
        vals = list(range(1, n + 1))
        random.shuffle(vals)
        root = None
        for v in vals:
            root = bst_insert_iterative(root, v)
        target = n            # the largest value: worst case for both
        d = count_visited_descent(root, target)
        p = count_visited_plain(root, target)
        print(f"  {n:>7} {height_iterative(root):>7} {d:>9} {p:>11} "
              f"{p / d:>7.1f}x")
    print("  The descent examines at most `height` nodes; the plain DFS has no")
    print("  ordering to exploit, so it can be forced to walk almost everything.")

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 2: insertion order decides the height, and thus the cost.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 2: sorted inserts build a CHAIN; shuffled inserts build a tree ---")
    n = 4_000
    root_sorted = None
    for v in range(1, n + 1):                     # 1,2,3,...  strictly ascending
        root_sorted = bst_insert_iterative(root_sorted, v)

    shuffled = list(range(1, n + 1))
    random.seed(42)
    random.shuffle(shuffled)
    root_shuffled = None
    for v in shuffled:
        root_shuffled = bst_insert_iterative(root_shuffled, v)

    h_sorted = height_iterative(root_sorted)
    h_shuffled = height_iterative(root_shuffled)
    import math
    print(f"  n = {n}")
    print(f"  height after SORTED   inserts (1..n): {h_sorted:>6}   "
          f"(== n, a linked list)")
    print(f"  height after SHUFFLED inserts:        {h_shuffled:>6}   "
          f"(log2(n) = {math.log2(n):.1f}, ~2x that is typical for random)")

    # Measure a search on each, worst case (deepest value).
    reps = 300
    t0 = time.perf_counter()
    for _ in range(reps):
        sol.searchBST(root_sorted, n)
    t1 = time.perf_counter()
    for _ in range(reps):
        sol.searchBST(root_shuffled, n)
    t2 = time.perf_counter()
    us_sorted = (t1 - t0) / reps * 1e6
    us_shuffled = (t2 - t1) / reps * 1e6
    print(f"  search for {n} on the chain:  {us_sorted:>9.2f} us "
          f"({h_sorted} comparisons)")
    print(f"  search for {n} on the tree:   {us_shuffled:>9.2f} us "
          f"({height_iterative(root_shuffled)} max comparisons)")
    print(f"  chain is {us_sorted / us_shuffled:.0f}x slower — SAME algorithm, "
          f"SAME n, different SHAPE.")
    chain_is_worse = h_sorted == n and h_shuffled < n // 10
    print(f"  sorted inserts produced height == n exactly: {chain_is_worse}")
    all_ok &= chain_is_worse

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 3: the recursive variant is not a free alternative.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 3: recursion on a degenerate BST hits CPython's ceiling ---")
    limit = sys.getrecursionlimit()
    print(f"  sys.getrecursionlimit() = {limit}; degenerate tree height = {h_sorted}")
    iterative_ok = sol.searchBST(root_sorted, n) is not None
    print(f"  iterative on the chain: found the node -> {iterative_ok}")
    raised = False
    try:
        sol.searchBST_recursive(root_sorted, n)
        print("  recursive on the chain: did NOT raise (limit not reached this run)")
    except RecursionError as e:
        raised = True
        print(f"  recursive on the chain: RecursionError -> {e!r}")
    print(f"  iterative succeeded where recursive failed: {iterative_ok and raised}")
    all_ok &= iterative_ok
    all_ok &= raised
    print("  Note: 5000 nodes is the problem's stated maximum, so this is a")
    print("  failure inside the constraints, not a contrived one.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
