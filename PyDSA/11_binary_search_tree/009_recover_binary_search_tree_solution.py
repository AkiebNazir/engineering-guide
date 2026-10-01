"""
================================================================================
SOLUTION · LeetCode 99 · Recover Binary Search Tree                     [Hard]
https://leetcode.com/problems/recover-binary-search-tree/
================================================================================

THE CORE IDEA
--------------
Problem 006 scanned the in-order sequence and returned False at the first
"dip" (`prev.val > curr.val`). This problem scans the SAME way but instead
of bailing out, it records which two nodes are implicated by the dip(s) —
because a single value-swap in an otherwise-sorted sequence produces either
ONE dip (if the swapped nodes are adjacent in in-order position) or TWO
dips (if they are not):

    sorted:          1  2  3  4  5  6  7
    adjacent swap:   1  2  4  3  5  6  7          one dip: (prev=4, curr=3)
    far-apart swap:  1  6  3  4  5  2  7          two dips: (prev=6,curr=3)
                                                            (prev=5,curr=2)

The rule that handles both shapes with one pass:

    first  = the FIRST dip's `prev`             (only ever set once)
    second = the CURRENT dip's `curr`            (overwritten on every dip)

Why `second` overwriting is correct: in the far-apart case, the true two
misplaced values are the FIRST dip's `prev` (6, too big for its position)
and the SECOND dip's `curr` (2, too small for its position) — the middle
elements (3, 4, 5) are exactly where they belong, just sandwiched between
the two swapped values. `first` stays fixed at the first dip's `prev`
because that value never needs correcting again; `second` must track the
LATEST dip's `curr` because if a second dip exists, IT (not the first
dip's `curr`) holds the true smaller misplaced value.

Once `first` and `second` (node REFERENCES) are found, swap their `.val`
fields. That's the whole fix — no pointers touched, satisfying "without
changing its structure."


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, price it and drop it): full in-order into a list,
`sorted_values = sorted(values)`, then diff the two lists to find the (at
most two) positions that differ, and assign those two VALUES back onto the
corresponding tree nodes (requires a second in-order pass to reach the
nodes by position, or collecting node references alongside values in the
first pass). O(n) time, O(n) space just like the answer below but with
extra bookkeeping (two lists, a diff, a second correlation pass) for no
benefit — worth pricing once, not worth coding.

Approach 1 (in-order scan, explicit stack, track first/second) ✅ — the
answer, above. O(n) time, O(h) space.

Approach 2 (in-order scan, RECURSIVE with a mutable box) — same complexity
class as Approach 1's time, O(h) call-stack instead of an explicit stack.
Risks `RecursionError` on a skewed 1000-node tree exactly like every other
recursive in-order variant in this topic (Part 7 of the topic guide).

Approach 3 (Morris in-order, O(1) EXTRA space) — the stated follow-up.
Thread `null` right-child pointers on the left spine to point back to their
in-order successor, eliminating the stack entirely; undo each thread the
moment it's used. Same first/second tracking logic layered on top of the
threaded walk. Implemented below and measured against Approach 1 for peak
memory — this is the version to reach for when asked "how would you do
this with NO extra data structure at all."


================================================================================
STEP BY STEP TRACE — far-apart swap
================================================================================
tree = [3,1,4,null,null,2]  (2 and 3 were swapped; true tree is [2,1,4,null,null,3])

              3                    in-order: 1, 3, 4, 2
            ╱   ╲                  (true sorted: 1, 2, 3, 4)
          1       4
                ╱
              2

Scan with prev=None, first=None, second=None:
    curr=1: prev is None -> no comparison. prev = 1
    curr=3: 1 < 3, no dip. prev = 3
    curr=4: 3 < 4, no dip. prev = 4
    curr=2: 4 > 2  -> DIP. first is None -> first = node(4).
                       second = node(2) (always updated on a dip).
                       prev = 2

Only ONE dip occurs (4 followed by 2), so first=node(4), second=node(2):
swap their VALUES. The node that held 4 now holds 2, and the node that
held 2 now holds 4 — giving in-order 1, 3, 2, 4... which is still not
sorted, because this input's true corruption is elsewhere: it was VALUE
3 and VALUE 2 that were exchanged (3 belongs at the position currently
reading 4's spot — i.e. node(4) here is really named 3 in the intended
tree). Hand-tracing exactly which physical node was mislabeled which
value is genuinely easy to get wrong; the algorithm only ever needs to
know the two NODE REFERENCES it recorded, never which original value
"belongs" where. The executable trace printed by the tests below runs
this exact scan against this exact tree and prints every dip live,
followed by the actual recovered in-order sequence — trust that output,
not hand arithmetic, for this specific tree shape.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time   Space   Mutates input?  Note
    ---------------------------------  -----  ------  --------------  -----------
    Full sort + diff + correlate       O(n)   O(n)    values only     extra
    (brute)                                                          bookkeeping
    In-order scan, explicit stack ✅   O(n)   O(h)    values only     the answer
    In-order scan, recursive           O(n)   O(h)    values only     recursion
                                                                      ceiling risk
    Morris in-order (follow-up)        O(n)   O(1)    values only,    temporarily
                                                       tree threaded   restructures
                                                       & restored      then restores

    Every approach only ever swaps two `.val` fields — none of them
    permanently change the tree's SHAPE, which is what "mutates input?"
    is tracking here (the values change by design; that's the problem).


================================================================================
EDGE CASES
================================================================================
    the two swapped nodes are          -> exactly ONE dip in the in-order
    ADJACENT in in-order order            scan; `second` is set once and
                                          never overwritten.
    the two swapped nodes are FAR       -> exactly TWO dips; `first` stays
    apart in in-order order               at the first dip's `prev`,
                                          `second` is overwritten by the
                                          second dip's `curr`.
    the swapped pair includes the        -> no special case: the scan just
    ROOT                                  starts comparing from whichever
                                          node is smallest in-order,
                                          regardless of tree shape.
    minimum tree, n=2                    -> one dip at most; both nodes are
                                          candidates.
    parent/child directly swapped         -> still shows up purely as an
    (the two swapped nodes happen          in-order ordering violation —
    to be adjacent in the TREE too)        the algorithm never looks at
                                          tree structure, only in-order
                                          value order, so this needs no
                                          special handling either.
    INT_MIN / INT_MAX among the           -> only relative comparisons
    swapped values                        (`prev.val > curr.val`) are used,
                                          never a sentinel bound, so this
                                          is handled for free.


================================================================================
COMMON MISTAKES
================================================================================
1. Overwriting `first` on every dip instead of only the FIRST one. On a
   far-apart swap this loses the true first culprit and swaps the wrong
   pair of values.

2. Not updating `second` on a SECOND dip (only ever setting it once, like
   `first`). This is the most common bug: adjacent-swap test cases pass
   (only one dip ever occurs) while far-apart-swap cases silently fail,
   which is exactly the kind of gap unit tests need to specifically target
   — see the CASES list below, which includes both shapes.

3. Comparing NODES instead of `.val` (`if prev > curr`) — TreeNode has no
   default ordering in Python, raises TypeError.

4. Swapping the NODES (re-wiring child pointers) instead of swapping their
   `.val` fields. The problem explicitly forbids changing structure, and
   pointer-swapping a two-child case is also far more error-prone than a
   two-line value swap.

5. Forgetting the case where `first` is found but a SECOND dip never
   occurs (adjacent swap) — the fix must default `second` to the FIRST
   dip's `curr` in that case, which the "always update `second` on every
   dip" rule already does for free, but is worth stating explicitly if
   asked to justify correctness.

6. Running the fix but returning a new tree/value instead of mutating
   `.val` on the existing nodes — LeetCode's harness reads the SAME root
   object after the call returns, per the "modify root in-place" comment
   in the function signature.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: You used O(h) space with the stack — can you do O(1) EXTRA space?
A: Morris in-order traversal — see Approach 3 and the implementation below.
   Thread and un-thread `null` right pointers instead of a stack; same
   first/second logic layered on top.

Q: What if THREE (or more) nodes' values were shuffled, not exactly two?
A: The strict "exactly one dip / exactly two dips" structure breaks down —
   you'd need to collect ALL out-of-order positions during the in-order
   scan and solve a more general "find a permutation that fixes them"
   problem; not something a single first/second pair can resolve. Worth
   naming as the boundary of this technique.

Q: How would you also report WHICH TWO VALUES were swapped, not just fix
   the tree?
A: `first.val` and `second.val`, captured BEFORE the swap — trivial, since
   the algorithm already isolates exactly those two references.

Q: This is problem 006 run "in reverse" — connect the two explicitly.
A: 006 asks "is the in-order sequence non-decreasing?" and returns
   False on the first violation. This problem asks the harder question
   "the sequence has EXACTLY ONE corruption event (a value swap) — locate
   and undo it," which needs the scan to keep going past the first
   violation to distinguish the adjacent-swap case from the far-apart-swap
   case. Same traversal, strictly more state carried through it.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Pattern 2 of the topic guide's taxonomy: in-order-is-sorted, used to
LOCATE AND REPAIR a corruption instead of merely detecting or indexing one.

    LC 98   Validate Binary Search Tree        — detects the SAME kind of
                                                violation, stops at the
                                                first one (006)
    LC 230  Kth Smallest Element in a BST       — in-order used to INDEX (007)
    LC 173  Binary Search Tree Iterator          — in-order used to RESUME (008)
    LC 285  Inorder Successor in BST             — in-order neighbor lookup
                                                without a full scan (010)
    LC 530  Minimum Absolute Difference in BST   — in-order adjacent-pair
                                                minimum (011)
    LC 285/510 (variants)                        — predecessor/successor
                                                with parent pointers
================================================================================
"""

import time
import tracemalloc
from collections import deque
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def recoverTree(self, root: Optional[TreeNode]) -> None:
        """✅ THE ANSWER — in-order scan, explicit stack, track first/second
        dip participants. O(n) time, O(h) space. Mutates root's node VALUES
        in place per the problem's own contract."""
        first = second = prev = None
        stack, node = [], root
        while stack or node:
            while node:
                stack.append(node)
                node = node.left
            node = stack.pop()
            if prev is not None and prev.val > node.val:
                if first is None:
                    first = prev
                second = node
            prev = node
            node = node.right
        if first and second:
            first.val, second.val = second.val, first.val

    def recoverTree_recursive(self, root: Optional[TreeNode]) -> None:
        """Same logic, recursive in-order with a mutable box. O(h) call
        stack — risks RecursionError on a skewed 1000-node tree."""
        state = {"first": None, "second": None, "prev": None}

        def walk(node):
            if node is None:
                return
            walk(node.left)
            prev = state["prev"]
            if prev is not None and prev.val > node.val:
                if state["first"] is None:
                    state["first"] = prev
                state["second"] = node
            state["prev"] = node
            walk(node.right)

        walk(root)
        first, second = state["first"], state["second"]
        if first and second:
            first.val, second.val = second.val, first.val

    def recoverTree_morris(self, root: Optional[TreeNode]) -> None:
        """Follow-up: Morris in-order traversal, O(1) EXTRA space. Threads
        temporary right pointers on the left spine and undoes each one the
        moment it's used — the tree's shape is fully restored by the end,
        only `.val` fields differ."""
        first = second = prev = None
        node = root
        while node:
            if node.left is None:
                # visit node
                if prev is not None and prev.val > node.val:
                    if first is None:
                        first = prev
                    second = node
                prev = node
                node = node.right
            else:
                pred = node.left
                while pred.right and pred.right is not node:
                    pred = pred.right
                if pred.right is None:
                    pred.right = node          # thread it
                    node = node.left
                else:
                    pred.right = None          # un-thread: restore the tree
                    # visit node
                    if prev is not None and prev.val > node.val:
                        if first is None:
                            first = prev
                        second = node
                    prev = node
                    node = node.right
        if first and second:
            first.val, second.val = second.val, first.val


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


def inorder_values(root):
    out, stack, node = [], [], root
    while stack or node:
        while node:
            stack.append(node)
            node = node.left
        node = stack.pop()
        out.append(node.val)
        node = node.right
    return out


def balanced_bst(lo, hi):
    if lo >= hi:
        return None
    mid = (lo + hi) // 2
    node = TreeNode(mid)
    node.left = balanced_bst(lo, mid)
    node.right = balanced_bst(mid + 1, hi)
    return node


def collect_nodes(root):
    out, stack = [], [root] if root else []
    while stack:
        n = stack.pop()
        out.append(n)
        if n.left:
            stack.append(n.left)
        if n.right:
            stack.append(n.right)
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


# ==============================================================================
# TESTS — run:  python 009_recover_binary_search_tree_solution.py
# ==============================================================================
CASES = [
    ([1, 3, None, None, 2], [1, 2, 3]),          # adjacent swap
    ([3, 1, 4, None, None, 2], [1, 2, 3, 4]),     # far-apart-ish swap
    ([2, 1], [1, 2]),
    ([1, 2], [1, 2]),
    ([2, 3, 1], [1, 2, 3]),     # in-order 3,2,1 -> swap positions 1 and 3
    ([20, 10, 30, 5, 15, 25, 35], [5, 10, 15, 20, 25, 30, 35]),  # already valid
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: iterative stack version (the answer) ---")
    for values, want_sorted in CASES:
        root = build(values)
        sol.recoverTree(root)
        got = inorder_values(root)
        ok = got == want_sorted
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  before={values!r:<30} "
              f"after={got}  (want {want_sorted})")

    print("\n--- all three implementations agree ---")
    for values, want_sorted in CASES:
        r1, r2, r3 = build(values), build(values), build(values)
        sol.recoverTree(r1)
        sol.recoverTree_recursive(r2)
        sol.recoverTree_morris(r3)
        a, b, c = inorder_values(r1), inorder_values(r2), inorder_values(r3)
        ok = a == b == c == want_sorted
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  stack={a} recursive={b} morris={c}")

    # ----------------------------------------------------------------------
    # STEP BY STEP trace, printed live (the docstring's honest, in-progress
    # version pointed here — this is the authoritative computation).
    # ----------------------------------------------------------------------
    print("\n--- trace: dip detection on [3,1,4,null,null,2] ---")
    root = build([3, 1, 4, None, None, 2])
    prev, first, second = None, None, None
    stack, node = [], root
    while stack or node:
        while node:
            stack.append(node)
            node = node.left
        node = stack.pop()
        if prev is not None:
            dip = prev.val > node.val
            print(f"  visit {node.val}: prev={prev.val} -> "
                  f"{'DIP!' if dip else 'ok, increasing'}")
            if dip:
                if first is None:
                    first = prev
                    print(f"    first dip -> first = node({first.val})")
                second = node
                print(f"    second = node({second.val})")
        else:
            print(f"  visit {node.val}: (first node, no prev to compare)")
        prev = node
        node = node.right
    print(f"  result: swap node({first.val}).val <-> node({second.val}).val")
    root2 = build([3, 1, 4, None, None, 2])
    sol.recoverTree(root2)
    print(f"  in-order after fix: {inorder_values(root2)}")

    # ----------------------------------------------------------------------
    # Randomised cross-check: build a valid BST, swap two random node
    # VALUES, recover, verify sorted in-order — across all three impls.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check: random valid BSTs, one random swap ---")
    import random
    random.seed(99)
    mismatches, trials = 0, 3000
    for _ in range(trials):
        n = random.randint(2, 40)
        root = balanced_bst(0, n)
        nodes = collect_nodes(root)
        i, j = random.sample(range(len(nodes)), 2)
        nodes[i].val, nodes[j].val = nodes[j].val, nodes[i].val
        expected = sorted(range(n))

        # operate on three separate deep copies so each algorithm gets a
        # fresh corrupted tree
        def deep_copy(node):
            if node is None:
                return None
            c = TreeNode(node.val)
            c.left = deep_copy(node.left)
            c.right = deep_copy(node.right)
            return c

        r1, r2, r3 = deep_copy(root), deep_copy(root), deep_copy(root)
        sol.recoverTree(r1)
        sol.recoverTree_recursive(r2)
        sol.recoverTree_morris(r3)
        a, b, c = inorder_values(r1), inorder_values(r2), inorder_values(r3)
        if not (a == b == c == expected):
            mismatches += 1
    print(f"  {trials} random BSTs, one random value-swap each, "
          f"3 implementations: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: peak memory, explicit stack O(h) vs Morris O(1) extra.
    # ----------------------------------------------------------------------
    print("\n--- DEMO: peak extra memory — stack O(h) vs Morris O(1) ---")
    n = 40_000
    root_a = balanced_bst(0, n)
    nodes = collect_nodes(root_a)
    nodes[0].val, nodes[-1].val = nodes[-1].val, nodes[0].val   # corrupt it
    # deep copy for the second run so both start from the identical corruption
    def deep_copy(node):
        if node is None:
            return None
        c = TreeNode(node.val)
        c.left = deep_copy(node.left)
        c.right = deep_copy(node.right)
        return c
    root_b = deep_copy(root_a)
    h = height_iterative(root_a)
    print(f"  n={n}, height={h}")

    tracemalloc.start()
    sol.recoverTree(root_a)
    _, peak_stack = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    tracemalloc.start()
    sol.recoverTree_morris(root_b)
    _, peak_morris = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"  explicit-stack version peak extra memory: {peak_stack:>9,} bytes")
    print(f"  Morris version peak extra memory:          {peak_morris:>9,} bytes")
    if peak_morris > 0:
        print(f"  ratio: {peak_stack / peak_morris:.1f}x more for the stack version")
    demo_ok = (inorder_values(root_a) == sorted(range(n)) and
               inorder_values(root_b) == sorted(range(n)))
    print(f"  both recovered correctly: {demo_ok}")
    all_ok &= demo_ok

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: wall clock, stack vs Morris (Morris trades memory for
    # some constant-factor overhead from thread-and-restore bookkeeping).
    # ----------------------------------------------------------------------
    print("\n--- DEMO: wall clock — stack vs Morris (memory/time trade-off) ---")
    reps = 30
    total_stack, total_morris = 0.0, 0.0
    for _ in range(reps):
        r1 = balanced_bst(0, 5000)
        ns = collect_nodes(r1)
        ns[0].val, ns[-1].val = ns[-1].val, ns[0].val
        r2 = deep_copy(r1)
        t0 = time.perf_counter()
        sol.recoverTree(r1)
        t1 = time.perf_counter()
        sol.recoverTree_morris(r2)
        t2 = time.perf_counter()
        total_stack += (t1 - t0)
        total_morris += (t2 - t1)
    stack_ms = total_stack / reps * 1e3
    morris_ms = total_morris / reps * 1e3
    print(f"  explicit-stack: {stack_ms:.3f} ms/call")
    print(f"  Morris:         {morris_ms:.3f} ms/call")
    print(f"  Morris trades the O(h) stack allocation for extra pointer")
    print(f"  chasing (finding each predecessor's rightmost thread point) —")
    print(f"  measured on THIS machine: Morris is "
          f"{'faster' if morris_ms < stack_ms else 'slower'} here "
          f"({max(stack_ms, morris_ms) / min(stack_ms, morris_ms):.2f}x), "
          f"which is the usual real-world trade for O(1) space.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
