"""
================================================================================
SOLUTION · LeetCode 701 · Insert into a Binary Search Tree           [Medium]
https://leetcode.com/problems/insert-into-a-binary-search-tree/
================================================================================

THE CORE IDEA
--------------
Insertion is a FAILED search. Descend exactly as problem 001 does; because
`val` is guaranteed absent, the descent must run off the bottom of the tree,
and the `None` pointer it runs off is the one and only place the node can go
without disturbing anything.

    node = root
    while True:
        if val < node.val:
            if node.left is None:
                node.left = TreeNode(val); return root
            node = node.left
        else:
            if node.right is None:
                node.right = TreeNode(val); return root
            node = node.right

**The new node is always a leaf.** No existing node moves, no subtree is
rebuilt, and the only pointer written in the whole operation is the single
`None` child slot you landed on. O(h) time, O(1) space.

Why that slot is provably correct: the descent maintains, implicitly, the
open interval that any node in the current subtree must live in. Every
left-turn tightens the upper bound to the parent's value, every right-turn
tightens the lower bound. When you reach `None`, the interval is still
non-empty and `val` is inside it, so putting `val` there satisfies the
subtree-wide invariant (topic guide §1.1) at every ancestor at once. That
interval-narrowing argument is the same machinery problem 006 (validate)
uses to CHECK a tree; here it is used to build one.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, don't ship): collect all values with an in-order
traversal, append `val`, sort, and rebuild a balanced tree with problem
002's algorithm. O(n) time and O(n) space per insert, and it changes the
whole tree instead of touching one pointer. Occasionally the RIGHT answer if
what you actually need is rebalancing (see LC 1382), but it is not an
insert.

Approach 1 (recursive, re-attachment idiom):

    def insertIntoBST(root, val):
        if root is None:
            return TreeNode(val)
        if val < root.val:
            root.left = self.insertIntoBST(root.left, val)
        else:
            root.right = self.insertIntoBST(root.right, val)
        return root

Read that middle line carefully — `root.left = self.insertIntoBST(root.left,
val)`. The recursive call returns the (possibly brand-new) root of the left
subtree, and the parent RE-ATTACHES it. For insert that assignment is
redundant on every level except the one that hit `None`; it is written this
way because it is the same idiom problem 004 (delete) absolutely requires,
where the subtree root really can change. Learning it here, where it is
harmless, is what makes 450 tractable. O(h) time, O(h) stack.

Approach 2 (iterative with a trailing parent pointer) ✅ — the answer above,
or the equivalent shape that keeps `parent` explicitly:

    parent, node = None, root
    while node:
        parent = node
        node = node.left if val < node.val else node.right
    if parent is None: return TreeNode(val)
    if val < parent.val: parent.left = TreeNode(val)
    else: parent.right = TreeNode(val)
    return root

The trailing-parent form is worth knowing because delete (004) and
"insert into a doubly-linked BST" style follow-ups need the parent anyway.
O(h) time, O(1) space, no recursion ceiling — which matters, because a
degenerate BST at the problem's stated 10^4 nodes has h = 10^4 and the
recursive version raises RecursionError. Demoed below.


================================================================================
⚠️  THE PROPERTY THAT MAKES THIS PROBLEM DANGEROUS: SORTED INSERTS DEGENERATE
================================================================================
Every insert lands at a leaf, and where that leaf is depends entirely on the
order the values arrived. Insert 1,2,3,4,5 in ascending order:

    insert 1:  1        insert 2:  1        insert 3:  1        insert 4:  1
                                    ╲                   ╲                   ╲
                                     2                   2                   2
                                                          ╲                   ╲
                                                           3                   3
                                                                                ╲
                                                                                 4

Each insert walks the entire existing right spine, so insert #k costs k
comparisons: 1 + 2 + ... + n = n(n+1)/2 = O(n^2) to build, and the result is
a chain of height n with O(n) search. The BST has silently become a singly
linked list with extra pointers.

Sorted input is not a contrived adversary — it is the single most common
shape real data arrives in (timestamps, auto-increment ids, anything read
out of an already-sorted file). The measured demo below builds n = 4000 both
ways and prints the two heights and the two build times.

The fix is a SELF-BALANCING tree: AVL or red-black, which perform O(1)
rotations after each insert to keep h = O(log n). Python's stdlib has no
balanced BST at all (topic guide §3): the interview-relevant substitutes are
`sortedcontainers.SortedList` (third-party, O(sqrt n) insert with very small
constants, beats a hand-rolled AVL in practice), `bisect` over a plain list
(O(log n) search but O(n) insert because of the memmove), and `heapq` if you
only ever need the extremes.


================================================================================
STEP BY STEP TRACE
================================================================================
tree = [4,2,7,1,3], val = 5

            4
           ╱ ╲
          2   7
         ╱ ╲
        1   3

    node=4   5 > 4  -> node.right is 7, not None -> descend right
    node=7   5 < 7  -> node.left is None ✅ -> attach here
             7.left = TreeNode(5)

            4
           ╱ ╲
          2   7
         ╱ ╲  ╱
        1  3 5

    level-order: [4,2,7,1,3,5]     in-order: [1,2,3,4,5,7] — still sorted ✅
    nodes touched: 2. Nothing else in the tree was read or written.

tree = [], val = 1        ->  root is None -> return TreeNode(1)
tree = [1], val = 0       ->  0 < 1, 1.left is None -> attach -> [1,0]


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time      Space   Mutates input?  Note
    ---------------------------  --------  ------  --------------  --------------
    Flatten, sort, rebuild (002)  O(n)      O(n)    no (new tree)   not an insert
    Recursive re-attachment       O(h)      O(h)    YES, in place   the idiom 004 needs
    Iterative + parent ptr ✅      O(h)      O(1)    YES, in place   the answer

    n sequential inserts, SORTED   O(n^2)    O(1)    YES             height ends at n
    n sequential inserts, RANDOM   O(n log n) O(1)   YES             height ~2*log2(n)
    n inserts into an AVL/RB tree  O(n log n) O(1)   YES             height guaranteed
                                                                     O(log n)

    "Mutates input?" is YES and it matters: the caller's tree is modified in
    place, and the returned root is the SAME object as the input root unless
    the input was None. Code that does `new = insertIntoBST(old, v)` and then
    expects `old` to be unchanged is broken. (Contrast 002, which only reads.)


================================================================================
EDGE CASES
================================================================================
    root is None            -> return a fresh single node. Not an error case;
                                it is also the recursion's base case.
    val < every value        -> walks the entire LEFT spine, attaches at the
                                bottom-left. Worst case for a left-leaning tree.
    val > every value        -> walks the entire RIGHT spine. This is the case
                                repeated sorted inserts hit every single time.
    val fits between two      -> the interesting case: lands as the left child
    existing values            of the in-order successor, or the right child of
                               the in-order predecessor — whichever is deeper.
                               (Exactly one of those two slots is free; see
                               the "why not both" note in COMMON MISTAKES.)
    single-node tree          -> smallest case with a real attach decision.
    val already present       -> excluded by the constraints. If it happened,
                                this code would insert a duplicate on the
                                `else` (>=) branch; a real implementation must
                                pick a documented policy (ignore / count /
                                always-left) — see 006 on duplicates.
    degenerate tree, h = 10^4 -> inside the constraints, and the recursive
                                version raises RecursionError there.


================================================================================
COMMON MISTAKES
================================================================================
1. Writing `if root is None: root = TreeNode(val)` inside a loop and
   expecting it to attach. Assigning to a local name never writes into the
   parent's `.left`/`.right` slot — Python has no pointers-to-pointers. You
   must either hold the PARENT (iterative) or return the subtree and let the
   parent re-attach (recursive). This is the #1 bug in this problem and it
   fails silently: the value is simply not in the tree afterwards.

2. Forgetting to `return root` from the recursive branches, or returning the
   result of the recursive call instead of `root`. Both re-root the tree at
   the wrong node and lose everything above the insertion point.

3. Descending to a leaf and then trying to decide which side to attach on by
   comparing against the LEAF's value after the loop has already moved past
   it — you need the value of the last non-None node, i.e. the parent.

4. Assuming both child slots of the landing node are free. They are not: the
   descent stops at the FIRST `None` it meets, so exactly one specific slot
   is the target, and it is determined by the last comparison, not by
   whichever child happens to be empty.

5. Rebalancing "to be safe". 701 does not ask for balance, and a rotation
   you cannot justify is a bug you cannot debug. Mention AVL/red-black as a
   follow-up instead.

6. Reporting the cost of n inserts as O(n log n) unconditionally. On sorted
   input it is O(n^2) — the demo below measures it. Say "O(h) per insert" and
   then say what h is for your data.

7. Choosing recursion at n = 10^4. The constraints permit a chain that deep,
   and CPython's ~1000-frame limit turns that into a RecursionError, not a
   slowdown.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Now delete a node.
A: Problem 004 (LC 450) — strictly harder, because deletion can remove an
   INTERNAL node and something must take its place. Insert never has that
   problem, which is why insert is the easier half of the pair.

Q: How do you keep the tree balanced across many inserts?
A: AVL (strict: heights differ by <= 1, more rotations, faster lookups) or
   red-black (looser: <= 2x height, fewer rotations, faster writes — what
   `std::map` and Java's `TreeMap` use). Both do O(1) rotations per insert
   and keep h = O(log n). Or, if the whole dataset is known up front, skip
   balancing entirely and build with problem 002's midpoint recursion.

Q: What would you actually use in Python?
A: Almost never a hand-rolled BST. `sortedcontainers.SortedList` for an
   ordered multiset with fast insert/search/index; `bisect` on a list when
   inserts are rare and searches are common; `heapq` when only the min (or
   max) matters. Topic guide §3 prices all three against each other.

Q: Insert into a BST that also maintains subtree SIZES?
A: Increment `node.size` on the way down the descent (every node you pass
   through gains one descendant). That augmentation makes "kth smallest" and
   "rank of x" O(h) — see problem 007's follow-up.

Q: Duplicates allowed?
A: Pick a policy and state it: send duplicates consistently left or
   consistently right (and use `<=`/`>=` in the descent to match), or store
   a count on the node. Sending them to "either" side breaks search, since
   you would then have to check both subtrees.

Q: Can you insert at the ROOT instead of at a leaf?
A: Yes — root insertion via rotations (used by treaps and splay trees).
   Also O(h), and it is how randomised balancing schemes get their
   guarantees. Worth naming; not worth coding on a whiteboard.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Pattern 1 (O(h) descent) plus the first taste of pattern 3 (surgery).

    LC 700  Search in a BST                 — the descent, without the attach (001)
    LC 450  Delete Node in a BST             — the hard counterpart (004)
    LC 108  Sorted Array to BST              — build balanced up front (002)
    LC 1382 Balance a Binary Search Tree     — fix a degenerate tree after the fact
    LC 510  Inorder Successor in BST II      — parent pointers, the same trailing
                                                -parent bookkeeping
    LC 285  Inorder Successor in BST          — where a value WOULD go, without
                                                inserting it
    LC 173  BST Iterator                      — walks the tree insert built (008)
    LC 449  Serialize and Deserialize BST     — re-inserting a whole tree from one
                                                traversal
================================================================================
"""

import random
import sys
import time
from collections import deque
from typing import List, Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def insertIntoBST(self, root: Optional[TreeNode], val: int) -> Optional[TreeNode]:
        """✅ THE ANSWER — iterative descent, attach at the first None.
        O(h) time, O(1) space. MUTATES the tree in place."""
        if root is None:
            return TreeNode(val)
        node = root
        while True:
            if val < node.val:
                if node.left is None:
                    node.left = TreeNode(val)
                    return root
                node = node.left
            else:
                if node.right is None:
                    node.right = TreeNode(val)
                    return root
                node = node.right

    def insertIntoBST_parent(self, root: Optional[TreeNode],
                             val: int) -> Optional[TreeNode]:
        """Same thing with an explicit trailing PARENT pointer — the shape
        problem 004 (delete) and LC 510 both need. O(h) time, O(1) space."""
        parent, node = None, root
        while node:
            parent = node
            node = node.left if val < node.val else node.right
        if parent is None:                      # empty tree
            return TreeNode(val)
        if val < parent.val:
            parent.left = TreeNode(val)
        else:
            parent.right = TreeNode(val)
        return root

    def insertIntoBST_recursive(self, root: Optional[TreeNode],
                                val: int) -> Optional[TreeNode]:
        """The RE-ATTACHMENT idiom: `root.left = insert(root.left, val)`.
        Redundant here (the subtree root never changes except at the None),
        but it is exactly what problem 004 requires — learn it here.
        O(h) time, O(h) stack: RecursionError on a degenerate 10^4-node tree."""
        if root is None:
            return TreeNode(val)
        if val < root.val:
            root.left = self.insertIntoBST_recursive(root.left, val)
        else:
            root.right = self.insertIntoBST_recursive(root.right, val)
        return root

    def insertIntoBST_broken_local(self, root: Optional[TreeNode],
                                   val: int) -> Optional[TreeNode]:
        """✗ BROKEN ON PURPOSE — mistake #1. Assigns the new node to a LOCAL
        name instead of into the parent's child slot. Rebinding a local never
        touches the parent, so the value silently never enters the tree."""
        if root is None:
            return TreeNode(val)
        node = root
        while node is not None:
            if val < node.val:
                node = node.left
            else:
                node = node.right
        node = TreeNode(val)                    # <-- writes a LOCAL only
        return root


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


def inorder_iterative(root):
    """In-order traversal, iterative — safe on chains thousands deep."""
    out, stack, node = [], [], root
    while stack or node:
        while node:
            stack.append(node)
            node = node.left
        node = stack.pop()
        out.append(node.val)
        node = node.right
    return out


def height_iterative(root):
    if root is None:
        return 0
    best, stack = 0, [(root, 1)]
    while stack:
        node, d = stack.pop()
        best = max(best, d)
        if node.left:
            stack.append((node.left, d + 1))
        if node.right:
            stack.append((node.right, d + 1))
    return best


def is_valid_bst(root):
    """In-order strictly increasing <=> valid BST (problem 006). Iterative."""
    io = inorder_iterative(root)
    return all(io[i] < io[i + 1] for i in range(len(io) - 1))


def find_node(root, val):
    node = root
    while node:
        if node.val == val:
            return node
        node = node.left if val < node.val else node.right
    return None


def is_leaf(node):
    return node is not None and node.left is None and node.right is None


def count_visited_insert(root, val):
    """Nodes examined by the insert descent."""
    if root is None:
        return 0
    n, node = 0, root
    while True:
        n += 1
        if val < node.val:
            if node.left is None:
                return n
            node = node.left
        else:
            if node.right is None:
                return n
            node = node.right


# ==============================================================================
# TESTS — run:  python 003_insert_into_a_binary_search_tree_solution.py
# ==============================================================================
CASES = [
    ([4, 2, 7, 1, 3], 5),
    ([40, 20, 60, 10, 30, 50, 70], 25),
    ([], 1),
    ([1], 0),
    ([1], 2),
    ([4, 2, 7, 1, 3], 100),
    ([4, 2, 7, 1, 3], -100),
    ([8, 3, 10, 1, 6, None, 14, None, None, 4, 7, 13], 5),
    ([8, 3, 10, 1, 6, None, 14, None, None, 4, 7, 13], 9),
    ([2, 1, 3], 4),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: still a BST, value present exactly once ---")
    for values, val in CASES:
        root = sol.insertIntoBST(build(values), val)
        io = inorder_iterative(root)
        want = sorted([v for v in values if v is not None] + [val])
        ok = io == want and is_valid_bst(root)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  tree={values!r:<48} val={val:<5} "
              f"-> {to_level_order(root)}")

    print("\n--- all three implementations agree, node for node ---")
    for values, val in CASES:
        a = to_level_order(sol.insertIntoBST(build(values), val))
        b = to_level_order(sol.insertIntoBST_parent(build(values), val))
        c = to_level_order(sol.insertIntoBST_recursive(build(values), val))
        ok = a == b == c
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  val={val:<5} iterative={a}")

    # ----------------------------------------------------------------------
    # PROPERTY: the inserted node is ALWAYS a leaf, and nothing else moved.
    # ----------------------------------------------------------------------
    print("\n--- property: the new node is always a LEAF; no existing node moves ---")
    random.seed(701)
    leaf_violations, move_violations, checks = 0, 0, 0
    for _ in range(2000):
        vals = random.sample(range(-200, 200), random.randint(1, 30))
        root = None
        for v in vals:
            root = sol.insertIntoBST(root, v)
        # snapshot every existing node's identity and its children
        before = {}
        stack = [root]
        while stack:
            node = stack.pop()
            before[id(node)] = (id(node.left), id(node.right), node.val)
            if node.left:
                stack.append(node.left)
            if node.right:
                stack.append(node.right)
        newval = random.choice([v for v in range(-300, 300) if v not in vals])
        root = sol.insertIntoBST(root, newval)
        inserted = find_node(root, newval)
        checks += 1
        if not is_leaf(inserted):
            leaf_violations += 1
        # exactly one pre-existing node changed, and only by gaining one child
        changed = 0
        stack = [root]
        while stack:
            node = stack.pop()
            if id(node) in before:
                l, r, v = before[id(node)]
                if (id(node.left), id(node.right), node.val) != (l, r, v):
                    changed += 1
            if node.left:
                stack.append(node.left)
            if node.right:
                stack.append(node.right)
        if changed != 1:
            move_violations += 1
    print(f"  {checks} random inserts: new node was a leaf every time "
          f"(violations={leaf_violations})")
    print(f"  exactly ONE pre-existing node's pointers changed each time "
          f"(violations={move_violations})")
    all_ok &= (leaf_violations == 0 and move_violations == 0)

    # ----------------------------------------------------------------------
    # Trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: insert 5 into [4,2,7,1,3] ---")
    root = build([4, 2, 7, 1, 3])
    node, val = root, 5
    while True:
        if val < node.val:
            if node.left is None:
                print(f"  at {node.val}: {val} < {node.val}, left is None "
                      f"-> ATTACH as left child")
                node.left = TreeNode(val)
                break
            print(f"  at {node.val}: {val} < {node.val} -> descend left")
            node = node.left
        else:
            if node.right is None:
                print(f"  at {node.val}: {val} > {node.val}, right is None "
                      f"-> ATTACH as right child")
                node.right = TreeNode(val)
                break
            print(f"  at {node.val}: {val} > {node.val} -> descend right")
            node = node.right
    print(f"  result level-order: {to_level_order(root)}")
    print(f"  result in-order:    {inorder_iterative(root)}  (sorted ✅)")

    # ----------------------------------------------------------------------
    # ⚠️  LIVE DEMO: mistake #1 — assigning to a local instead of a child slot.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: mistake #1, writing to a LOCAL name ---")
    root_ok = sol.insertIntoBST(build([4, 2, 7, 1, 3]), 5)
    root_bad = sol.insertIntoBST_broken_local(build([4, 2, 7, 1, 3]), 5)
    good_io, bad_io = inorder_iterative(root_ok), inorder_iterative(root_bad)
    print(f"  correct  -> {to_level_order(root_ok):}   in-order {good_io}")
    print(f"  broken   -> {to_level_order(root_bad)}   in-order {bad_io}")
    silently_lost = 5 not in bad_io and 5 in good_io
    print(f"  the broken version silently DROPPED the value (no exception): "
          f"{silently_lost}")
    print("  `node = TreeNode(val)` rebinds a local. Python has no pointer to")
    print("  the parent's child slot, so nothing in the tree was written.")
    all_ok &= silently_lost

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 1: n SORTED inserts vs n SHUFFLED inserts — height + time.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 1: sorted inserts degenerate to a linked list, measured ---")
    print(f"  {'n':>6} {'sorted h':>9} {'sorted ms':>10} {'shuffled h':>11} "
          f"{'shuffled ms':>12} {'time ratio':>11}")
    import math
    degenerate_confirmed = True
    for n in (500, 1_000, 2_000, 4_000):
        t0 = time.perf_counter()
        root_s = None
        for v in range(n):                       # ASCENDING — the trap
            root_s = sol.insertIntoBST(root_s, v)
        t1 = time.perf_counter()

        vals = list(range(n))
        random.seed(n)
        random.shuffle(vals)
        t2 = time.perf_counter()
        root_r = None
        for v in vals:
            root_r = sol.insertIntoBST(root_r, v)
        t3 = time.perf_counter()

        hs, hr = height_iterative(root_s), height_iterative(root_r)
        ms_s, ms_r = (t1 - t0) * 1000, (t3 - t2) * 1000
        degenerate_confirmed &= (hs == n and hr < 4 * math.log2(n))
        print(f"  {n:>6} {hs:>9} {ms_s:>9.2f}  {hr:>11} {ms_r:>11.2f}  "
              f"{ms_s / ms_r:>10.1f}x")
    print(f"  Sorted: height == n EXACTLY, every time (a chain). Time quadruples")
    print(f"  when n doubles -> O(n^2). Shuffled: height ~2*log2(n) "
          f"(log2(4000) = {math.log2(4000):.1f}), time roughly doubles -> O(n log n).")
    print("  Same code, same values, ONLY the arrival order differs.")
    all_ok &= degenerate_confirmed

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 2: comparisons per insert, sorted vs shuffled.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 2: comparisons the NEXT insert costs, on each tree ---")
    n = 4_000
    root_s = None
    for v in range(n):
        root_s = sol.insertIntoBST(root_s, v)
    vals = list(range(n))
    random.seed(3)
    random.shuffle(vals)
    root_r = None
    for v in vals:
        root_r = sol.insertIntoBST(root_r, v)
    print(f"  n = {n}; inserting the value {n} (a new maximum)")
    print(f"  nodes visited, chain tree:    {count_visited_insert(root_s, n):>6}")
    print(f"  nodes visited, shuffled tree: {count_visited_insert(root_r, n):>6}")
    print(f"  heights:                      {height_iterative(root_s)} vs "
          f"{height_iterative(root_r)}")

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 3: the recursive variant dies inside the constraints.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 3: recursion vs the problem's own 10^4-node limit ---")
    limit = sys.getrecursionlimit()
    print(f"  sys.getrecursionlimit() = {limit}; chain height = "
          f"{height_iterative(root_s)}")
    iter_ok = to_level_order(sol.insertIntoBST(root_s, n))[0] == 0
    print(f"  iterative insert into the chain: succeeded -> {iter_ok}")
    raised = False
    try:
        sol.insertIntoBST_recursive(root_s, n + 1)
        print("  recursive insert into the chain: did NOT raise this run")
    except RecursionError as e:
        raised = True
        print(f"  recursive insert into the chain: RecursionError -> {e!r}")
    print(f"  iterative succeeded where recursive failed: {iter_ok and raised}")
    all_ok &= iter_ok and raised
    print("  The constraints allow 10^4 nodes, so a chain that deep is legal")
    print("  input — this is a failure inside the problem, not a contrived one.")

    # ----------------------------------------------------------------------
    # Randomised: 3000 sequences, invariant must hold after EVERY insert.
    # ----------------------------------------------------------------------
    print("\n--- randomised: BST invariant re-checked after every single insert ---")
    random.seed(99)
    violations = 0
    for _ in range(3000):
        vals = random.sample(range(-100, 100), random.randint(1, 20))
        root = None
        seen: List[int] = []
        for v in vals:
            root = sol.insertIntoBST(root, v)
            seen.append(v)
            if inorder_iterative(root) != sorted(seen) or not is_valid_bst(root):
                violations += 1
    print(f"  3000 insert sequences, invariant checked at every step: "
          f"{violations} violations")
    all_ok &= (violations == 0)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
