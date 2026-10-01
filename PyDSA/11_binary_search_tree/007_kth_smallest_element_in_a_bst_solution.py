"""
================================================================================
SOLUTION · LeetCode 230 · Kth Smallest Element in a BST               [Medium]
https://leetcode.com/problems/kth-smallest-element-in-a-bst/
================================================================================

THE CORE IDEA
--------------
In-order traversal of a BST is a strictly increasing sequence (topic guide,
Part 1). "The kth smallest value" is therefore just "the kth value produced
by an in-order walk" — and because you're generating the sequence rather
than being handed it, you can STOP the moment you've produced k values
instead of materializing the whole thing:

    stack, node, count = [], root, 0
    while stack or node:
        while node:                 # dive to the leftmost unvisited node
            stack.append(node)
            node = node.left
        node = stack.pop()          # visit — this IS the next value in order
        count += 1
        if count == k:
            return node.val
        node = node.right           # then explore the right subtree

O(h + k) time: O(h) to reach the first (smallest) value, then O(1)
amortized per subsequent value up to the kth. Compare to "collect everything
then index", which is always O(n) regardless of k.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, price it and drop it): full in-order into a Python
list, `return values[k-1]`. O(n) time, O(n) space, ALWAYS — even for k=1 on
a 10,000-node tree, you still visit and store all 10,000 values before
throwing 9,999 of them away.

Approach 1 (recursive in-order, early exit via exception or a box) — same
complexity as the answer, O(h + k) if you stop cleanly, but Python's
recursion depth caps it at ~1000 nodes reliably (Part 7 of the topic
guide), and "stop a recursive in-order early" needs either an exception, a
`nonlocal` flag checked at every call, or returning a sentinel up the
stack — all more moving parts than the iterative version needs.

Approach 2 (iterative in-order, early exit) ✅ — the answer, above. No
recursion ceiling, the natural place to `return` the moment `count == k`.

Approach 3 (augmented tree: each node caches its LEFT SUBTREE SIZE) — see
the follow-up section below. O(h) per query, O(h) per insert/delete to
maintain the counters — the right answer when this query runs MANY times
against a tree that also mutates. Implemented below as `kth_smallest_
augmented`, with a demo proving it's the answer to the LC 230 follow-up.

Approach 4 (recursive Morris in-order, O(1) space) — same in-order-with-
early-exit idea done via temporary thread pointers instead of a stack.
Mentioned in follow-ups; not shipped, since it is fiddly to restore
correctly under interview pressure and O(h) auxiliary space is already
tiny (h = O(log n) for anything balanced).


================================================================================
FOLLOW-UP: MANY QUERIES AGAINST A MUTATING TREE — THE AUGMENTED BST
================================================================================
The stated LC 230 follow-up: "if the BST is modified often and you need to
find the kth smallest frequently, how would you optimize?"

The iterative answer above is O(h + k) PER CALL. If you call it m times
with k averaging n/2, that's O(m * n) total — bad if m is large.

The fix: augment every node with `left_size` — the number of nodes in its
OWN left subtree (not including itself). This turns "kth smallest" into a
comparison-only descent, exactly like search (001) and LCA (005):

    def kth_smallest_augmented(node, k):
        while node:
            left_size = size(node.left)
            if k == left_size + 1:
                return node.val                  # node itself is the kth
            elif k <= left_size:
                node = node.left                 # kth is inside the left subtree
            else:
                k -= left_size + 1                # skip left subtree + this node
                node = node.right
        return -1

Each `insert`/`delete` must maintain `size` on every node along its path —
O(h) extra work per mutation, in exchange for O(h) per `kthSmallest` query
afterward instead of O(h + k). This is the standard "augment the tree with
metadata that answers your query as a comparison" trick — subtree size
here, subtree sum for "range sum" variants, subtree min/max for other
range queries. It is the single most common BST follow-up in interviews
and is worth stating even when not asked.


================================================================================
STEP BY STEP TRACE
================================================================================
tree = [5,3,6,2,4,null,null,1], k = 3

                5
              ╱   ╲
            3       6
          ╱   ╲
        2       4
      ╱
    1

Iterative in-order with early exit:
    dive left from 5: push 5, push 3, push 2, push 1 -> node=None
    pop 1              count=1  (1 != 3)  -> node = 1.right = None
    pop 2              count=2  (2 != 3)  -> node = 2.right = None
    pop 3              count=3  (3 == 3)  -> RETURN 3 ✅
    (never visits 4, 5, or 6 — the walk stops the instant count hits k)

Augmented descent, same tree, left_size cached at each node — subtree sizes
are 1->0, 2->1 (its left child), 3->3 (contains {2,1,4}... wait, 4 is 3's
RIGHT child, so 3's LEFT subtree is just {2,1}, size 2), 4->0, 6->0, 5->6:
    node=5, left_size(5)=3:  k=3 <= 3            -> go LEFT,  node=3
    node=3, left_size(3)=2:  k=3 == 2+1=3? YES   -> RETURN 3 ✅
    (matches the iterative result — node 3 itself is the 3rd-smallest,
    because exactly 2 nodes {1,2} are smaller than it)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                         Time      Space   Mutates input?  Note
    --------------------------------  --------  ------  --------------  ------
    Collect all, then index (brute)   O(n)      O(n)    no              always
                                                                         full scan
    Recursive in-order, early exit    O(h+k)    O(h)    no              recursion
                                                                         ceiling risk
    Iterative in-order, early exit ✅ O(h+k)    O(h)    no              the answer
    Augmented tree (size-cached)      O(h)      O(h)    no (query);     best for
                                       per query          O(h) extra     MANY queries
                                                          per mutation   on a
                                                                         mutating tree

    h = O(log n) balanced, h = O(n) skewed (Part 4 of the topic guide).


================================================================================
EDGE CASES
================================================================================
    k == 1                        -> the minimum; the walk dives all the way
                                     left and returns on the FIRST pop —
                                     this is where the O(h+k) vs O(n) gap is
                                     largest (see the runtime demo).
    k == n                         -> the maximum; every node gets pushed
                                     and popped, effectively a full scan.
    single-node tree, k=1          -> trivially the root's value.
    left-skewed tree (sorted        -> h == n; both the iterative walk and
    input inserted ascending)         the augmented descent degrade to O(n).
    right-skewed tree               -> only the FIRST pop matters (root is
                                     smallest); k=1 is O(1) after the initial
                                     dive, which is already O(1) since there
                                     is no left subtree to descend into.
    k out of range (k=0 or k>n)     -> excluded by the constraints
                                     (1 <= k <= n); not defended against
                                     here since LC guarantees it.


================================================================================
COMMON MISTAKES
================================================================================
1. Collecting the full in-order list and indexing `list[k-1]` (brute
   force). Correct, but always O(n) — loses the entire point of the
   problem when k is small and n is large.

2. Off-by-one on `count`/`k`: starting `count` at 0 and comparing
   `count == k` AFTER incrementing is correct; comparing BEFORE
   incrementing, or starting `count` at 1 without adjusting the comparison,
   silently returns the (k-1)th or (k+1)th value instead.

3. Forgetting to move to `node.right` after visiting a popped node — the
   walk gets stuck re-descending the same left spine or terminates early.

4. Using recursion without checking it against the problem's `n <= 10^4`
   bound. A left-skewed 5,000-node tree is legal input and raises
   `RecursionError` under Python's default recursion limit.

5. In the augmented version: forgetting that `left_size(node)` must count
   only `node.left`'s subtree, NOT `node` itself — an off-by-one here
   silently shifts every answer by one position.

6. In the augmented version: not maintaining `size` incrementally during
   insert/delete, which turns the O(h) query into an O(n) recount at query
   time and defeats the entire point of augmenting the tree.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: The tree is modified often (insert/delete) and kthSmallest is called
   often too. How do you optimize?
A: Augment every node with its left-subtree size (see above); O(h) per
   query, O(h) extra work per mutation to keep sizes correct. This file
   implements and demonstrates it.

Q: What if you needed the kth LARGEST instead?
A: Either mirror the descent (walk right-first with a right-subtree-size
   counter), or note that kth-largest = (n - k + 1)th-smallest and reuse
   this exact function with `n` known.

Q: What's the O(1)-space version?
A: Morris in-order traversal — thread `null` right-child pointers
   temporarily to simulate the stack, undoing the threads on the way past.
   Same early-exit logic, no stack, no recursion.

Q: How would you find the kth smallest across a STREAM of BST values you
   can't hold in memory?
A: That's a different problem entirely (unbounded/streaming selection) —
   a min-heap of size k (for kth SMALLEST from an unsorted stream) or
   reservoir-style approaches; the augmented-tree trick only helps when you
   actually own the tree structure.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Pattern 2 of the topic guide's taxonomy: in-order-is-sorted, used to INDEX.

    LC 173  Binary Search Tree Iterator       — in-order used to RESUME,
                                                 across arbitrary external
                                                 calls, not just one query (008)
    LC 98   Validate Binary Search Tree        — in-order used as a TEST (006)
    LC 96   Unique Binary Search Trees          — counting BST shapes, the
                                                 combinatorics cousin
    LC 700  Search in a Binary Search Tree      — the augmented descent's
                                                 unaugmented ancestor (001)
    LC 449  Serialize and Deserialize BST       — preorder + bounds, not
                                                 in-order, but same family
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
    def kthSmallest(self, root: Optional[TreeNode], k: int) -> int:
        """✅ THE ANSWER — iterative in-order with an early exit.
        O(h + k) time, O(h) space."""
        stack, node, count = [], root, 0
        while stack or node:
            while node:
                stack.append(node)
                node = node.left
            node = stack.pop()
            count += 1
            if count == k:
                return node.val
            node = node.right
        return -1  # unreachable given 1 <= k <= n

    def kthSmallest_brute(self, root: Optional[TreeNode], k: int) -> int:
        """Brute force: full in-order into a list, then index. Always
        O(n) time and O(n) space regardless of k."""
        values = []

        def walk(node):
            if node is None:
                return
            walk(node.left)
            values.append(node.val)
            walk(node.right)

        walk(root)
        return values[k - 1]

    def kthSmallest_recursive(self, root: Optional[TreeNode], k: int) -> int:
        """Recursive in-order with an early exit via a mutable box.
        Same O(h + k) cost as the answer, but O(h) call-stack depth —
        risks RecursionError on a skewed tree at LC 230's n <= 10^4 bound."""
        state = {"count": 0, "result": None}

        def walk(node):
            if node is None or state["result"] is not None:
                return
            walk(node.left)
            if state["result"] is not None:
                return
            state["count"] += 1
            if state["count"] == k:
                state["result"] = node.val
                return
            walk(node.right)

        walk(root)
        return state["result"]

    # ------------------------------------------------------------------
    # Follow-up: augmented tree with left-subtree-size counters.
    # O(h) per query instead of O(h + k), at the cost of maintaining
    # `size` during every insert/delete.
    # ------------------------------------------------------------------
    def kth_smallest_augmented(self, root, k: int):
        """`root` here is an AugNode (see below), not a plain TreeNode —
        each node already carries `size` = count of nodes in its OWN
        subtree, maintained incrementally by AugNode's insert."""
        node = root
        while node:
            left_size = node.left.size if node.left else 0
            if k == left_size + 1:
                return node.val
            elif k <= left_size:
                node = node.left
            else:
                k -= left_size + 1
                node = node.right
        return -1


# ==============================================================================
# TEST HELPERS — shared with topic 10; not part of the exercise
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


def bst_insert_iterative(root, val):
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


def balanced_bst(lo, hi):
    """Perfectly balanced BST over range(lo, hi)."""
    if lo >= hi:
        return None
    mid = (lo + hi) // 2
    node = TreeNode(mid)
    node.left = balanced_bst(lo, mid)
    node.right = balanced_bst(mid + 1, hi)
    return node


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


def visited_kth_smallest(root, k):
    """Instrumented copy of the answer: counts nodes PUSHED onto the
    stack (i.e. actually touched), for the runtime demo."""
    stack, node, count, visits = [], root, 0, 0
    while stack or node:
        while node:
            stack.append(node)
            visits += 1
            node = node.left
        node = stack.pop()
        count += 1
        if count == k:
            return visits
        node = node.right
    return visits


# ------------------------------------------------------------------
# Augmented BST node — carries `size` for the follow-up.
# ------------------------------------------------------------------
class AugNode:
    __slots__ = ("val", "left", "right", "size")

    def __init__(self, val):
        self.val = val
        self.left = None
        self.right = None
        self.size = 1          # count of nodes in THIS node's own subtree


def aug_insert(node, val):
    """Insert into an augmented BST, maintaining `size` on the path."""
    if node is None:
        return AugNode(val)
    if val < node.val:
        node.left = aug_insert(node.left, val)
    else:
        node.right = aug_insert(node.right, val)
    node.size = 1 + (node.left.size if node.left else 0) \
                  + (node.right.size if node.right else 0)
    return node


# ==============================================================================
# TESTS — run:  python 007_kth_smallest_element_in_a_bst_solution.py
# ==============================================================================
CASES = [
    ([3, 1, 4, None, 2], 1, 1),
    ([5, 3, 6, 2, 4, None, None, 1], 3, 3),
    ([5, 3, 6, 2, 4, None, None, 1], 1, 1),
    ([5, 3, 6, 2, 4, None, None, 1], 6, 6),
    ([1], 1, 1),
    ([2, 1, 3], 2, 2),
    ([2, 1, 3], 3, 3),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: iterative in-order with early exit (the answer) ---")
    for values, k, want in CASES:
        got = sol.kthSmallest(build(values), k)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  tree={values!r:<30} k={k} "
              f"-> {got}  (want {want})")

    print("\n--- three implementations agree ---")
    for values, k, want in CASES:
        a = sol.kthSmallest(build(values), k)
        b = sol.kthSmallest_brute(build(values), k)
        c = sol.kthSmallest_recursive(build(values), k)
        ok = a == b == c == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  k={k}  iterative={a} brute={b} "
              f"recursive={c}")

    # ----------------------------------------------------------------------
    # Augmented-tree follow-up: correctness against every k, cross-checked.
    # ----------------------------------------------------------------------
    print("\n--- follow-up: augmented tree (size-cached descent) ---")
    random.seed(230)
    aug_mismatches = 0
    for _ in range(500):
        vals = random.sample(range(-1000, 1000), random.randint(1, 60))
        plain_root = None
        aug_root = None
        for v in vals:
            plain_root = bst_insert_iterative(plain_root, v)
            aug_root = aug_insert(aug_root, v)
        for k in range(1, len(vals) + 1):
            expected = sol.kthSmallest(plain_root, k)
            got = sol.kth_smallest_augmented(aug_root, k)
            if expected != got:
                aug_mismatches += 1
    print(f"  500 random trees x all valid k: {aug_mismatches} mismatches")
    all_ok &= (aug_mismatches == 0)

    # ----------------------------------------------------------------------
    # STEP BY STEP trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: k=3 on [5,3,6,2,4,null,null,1] ---")
    root = build([5, 3, 6, 2, 4, None, None, 1])
    stack, node, count = [], root, 0
    while stack or node:
        while node:
            print(f"  push {node.val}, descend left")
            stack.append(node)
            node = node.left
        node = stack.pop()
        count += 1
        print(f"  pop {node.val}  (count={count})", end="")
        if count == 3:
            print(f"  <- count == k=3, RETURN {node.val}")
            break
        print()
        node = node.right

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 1: nodes touched, small k vs k=n, on a large balanced tree.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 1: nodes touched — early exit vs full scan ---")
    n = 50_000
    bal = balanced_bst(0, n)
    h = height_iterative(bal)
    print(f"  balanced tree, n={n}, height={h}")
    for k, label in ((1, "k=1 (smallest)"), (n // 2, "k=n/2"), (n, "k=n (largest)")):
        touched = visited_kth_smallest(bal, k)
        print(f"  {label:<16} nodes touched = {touched:>7}  "
              f"(brute always touches {n})")
    print("  For k=1 the walk touches only `height` nodes — the early exit is")
    print("  the entire point of the algorithm; the brute-force list-then-index")
    print("  approach would touch all 50,000 nodes regardless of k.")

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 2: wall-clock, iterative-early-exit vs brute, small k.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 2: wall clock, k=1 on a 50,000-node balanced tree ---")
    reps = 2000
    t0 = time.perf_counter()
    for _ in range(reps):
        sol.kthSmallest(bal, 1)
    t1 = time.perf_counter()
    for _ in range(reps):
        sol.kthSmallest_brute(bal, 1)
    t2 = time.perf_counter()
    us_early = (t1 - t0) / reps * 1e6
    us_brute = (t2 - t1) / reps * 1e6
    print(f"  early-exit iterative: {us_early:8.2f} us/call")
    print(f"  brute (list + index): {us_brute:8.2f} us/call")
    print(f"  speedup: {us_brute / us_early:.0f}x")
    print("  Measured on THIS machine, THIS run — brute force must build and")
    print("  discard a 50,000-element list every single call, even for k=1.")
    demo2_ok = us_brute > us_early
    all_ok &= demo2_ok

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 3: augmented O(h) descent vs O(h+k) iterative walk,
    # for MANY repeated queries — the stated LC 230 follow-up.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 3: follow-up payoff — many queries, k near n/2 ---")
    # Sequential insert order would build a fully skewed (linked-list)
    # tree and blow the recursion limit in aug_insert; shuffle first so
    # both trees come out reasonably balanced — the realistic "many
    # queries against a live tree" case.
    random.seed(1)
    shuffled = list(range(n))
    random.shuffle(shuffled)
    plain_root = None
    aug_root = None
    for v in shuffled:
        plain_root = bst_insert_iterative(plain_root, v)
        aug_root = aug_insert(aug_root, v)
    k_mid = n // 2
    reps2 = 500
    t0 = time.perf_counter()
    for _ in range(reps2):
        sol.kthSmallest(plain_root, k_mid)
    t1 = time.perf_counter()
    for _ in range(reps2):
        sol.kth_smallest_augmented(aug_root, k_mid)
    t2 = time.perf_counter()
    us_plain = (t1 - t0) / reps2 * 1e6
    us_aug = (t2 - t1) / reps2 * 1e6
    print(f"  n={n}, k=n/2={k_mid}, {reps2} repeated queries")
    print(f"  iterative in-order (O(h+k)): {us_plain:9.2f} us/call")
    print(f"  augmented descent  (O(h)):   {us_aug:9.2f} us/call")
    print(f"  speedup: {us_plain / us_aug:.1f}x")
    print("  With k near n/2, O(h+k) is dominated by k, while the augmented")
    print("  descent stays O(h) regardless of k — this gap is exactly why the")
    print("  augmented tree is the standard answer to the 'many queries on a")
    print("  live tree' follow-up.")
    demo3_ok = us_plain > us_aug
    all_ok &= demo3_ok

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 4: recursion ceiling on a legal skewed tree.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 4: a legal skewed tree breaks the recursive version ---")
    chain = None
    for v in range(3000):
        chain = bst_insert_iterative(chain, v)
    print(f"  chain of 3000 nodes, recursion limit {sys.getrecursionlimit()}")
    it_result = sol.kthSmallest(chain, 2999)
    print(f"  iterative: kthSmallest(k=2999) = {it_result}")
    raised = False
    try:
        sol.kthSmallest_recursive(chain, 2999)
        print("  recursive: did NOT raise this run")
    except RecursionError as e:
        raised = True
        print(f"  recursive: RecursionError -> {e!r}")
    print(f"  iterative succeeded where recursive failed: "
          f"{it_result == 2998 and raised}")
    all_ok &= (it_result == 2998 and raised)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
