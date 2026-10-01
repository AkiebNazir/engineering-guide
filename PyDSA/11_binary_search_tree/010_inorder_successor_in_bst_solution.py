"""
================================================================================
SOLUTION · LeetCode 285 · Inorder Successor in BST                    [Medium]
https://leetcode.com/problems/inorder-successor-in-bst/
================================================================================

THE CORE IDEA
--------------
The two-case description in the question file (has a right child / doesn't)
is the right way to UNDERSTAND the problem, but there is a single unified
comparison descent from `root` that handles both cases with no branching on
`p.right` at all — the same "compare and remember the best candidate seen
so far" shape as floor/ceiling (topic guide Part 5.3):

    def successor(root, p):
        candidate = None
        node = root
        while node:
            if p.val < node.val:
                candidate = node          # node is BIGGER than p -> a
                node = node.left          #   candidate; maybe a smaller
                                           #   one exists further left
            else:
                node = node.right         # node <= p -> answer is further right
        return candidate

Why this needs no special case for "p has a right child": when the descent
reaches `p` itself, `p.val < node.val` is False (they're equal), so the
walk goes RIGHT into `p`'s own right subtree — and then the SAME rule
("value bigger than p -> candidate, go left for a smaller one") naturally
finds the leftmost node of that subtree, which is exactly Case A's answer.
When `p` has no right child, the walk from `root` never enters `p`'s
subtree at all after reaching it — every candidate came from ABOVE `p`,
which is exactly Case B's "closest ancestor via a left turn."

One descent, one rule, both cases — you never need to locate `p` in the
tree as a separate step, and you never need to know whether `p.right`
exists before starting.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, price it and drop it): full in-order traversal
into a list, `bisect` or linear-scan for `p.val`, return the next element
(or None if `p.val` is last). O(n) time, O(n) space, and it materializes
the entire tree just to answer one adjacency question — always pays for
the whole traversal even when `p` is near the root.

Approach 1 (two explicit cases, matching the question file's explanation)
— clear to explain out loud, same O(h) cost as the answer:

    if p.right:
        node = p.right
        while node.left:
            node = node.left
        return node
    candidate = None
    node = root
    while node:
        if p.val < node.val:
            candidate = node
            node = node.left
        elif p.val > node.val:
            node = node.right
        else:
            break
    return candidate

Approach 2 (unified single descent) ✅ — the answer, above. Same O(h) cost,
fewer lines, no need to special-case `p.right`.

Approach 3 (in-order scan with early exit, "next value after p") — walk
in-order with a stack (problem 007's pattern), stop the instant you've
JUST visited `p`, return the next popped value. O(h + rank(p)) — matches
Approach 0's correctness without materializing the WHOLE list, but is
still worse than O(h) when `p` sits deep in in-order rank; useful mainly as
a cross-check oracle, which is how it's used below.


================================================================================
STEP BY STEP TRACE
================================================================================
tree = [5,3,6,2,4,null,null,1]

                5
              ╱   ╲
            3       6
          ╱   ╲
        2       4
      ╱
    1

p = 3 (HAS a right child, value 4):
    node = p.right = 4
    4.left is None -> stop
    successor = 4 ✅

p = 6 (no right child, and it's the tree's maximum):
    unified descent from root, candidate = None:
    node=5: 6 < 5? No -> node = 5.right = 6
    node=6: 6 < 6? No (equal) -> node = 6.right = None
    loop ends, candidate never set -> successor = None ✅
    (6 never triggered "go left, remember candidate" because nothing in
    the tree exceeds 6 — it's the max)

p = 1 (no right child; the closest ancestor via a left turn is 2):
    unified descent from root, candidate = None:
    node=5: 1 < 5 -> candidate = 5, node = 5.left = 3
    node=3: 1 < 3 -> candidate = 3, node = 3.left = 2
    node=2: 1 < 2 -> candidate = 2, node = 2.left = 1
    node=1: 1 < 1? No (equal) -> node = 1.right = None
    loop ends -> successor = candidate = 2 ✅
    (candidate was overwritten each time a SMALLER "bigger than p" node
    was found while descending — 5, then 3, then 2, keeping only the
    tightest one)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time        Space   Mutates input?  Note
    ---------------------------------  ----------  ------  --------------  -----------
    Full in-order + linear scan        O(n)        O(n)    no              always full
    (brute)                                                                scan
    Two explicit cases                 O(h)        O(1)    no              matches
                                                                            question file
    Unified single descent ✅          O(h)        O(1)    no              the answer
    In-order scan, early exit          O(h+rank)   O(h)    no              oracle only,
    (oracle)                                                              in tests below

    h = O(log n) balanced, h = O(n) skewed (topic guide Part 4).


================================================================================
EDGE CASES
================================================================================
    p is the maximum value in the tree  -> no successor exists; candidate
                                         stays None through the whole
                                         descent, correctly returning null.
    p is the minimum value in the tree  -> successor is whatever the
                                         second-smallest value is; the walk
                                         finds it either via p.right (if it
                                         has one) or the first ancestor.
    single-node tree                    -> p IS root, no right child, no
                                         ancestor -> None.
    p's right child has NO left child    -> successor is p.right itself,
                                         the while-loop body in Approach 1
                                         (or the unified descent's first
                                         step past p) exits immediately.
    p's right subtree is a long LEFT     -> the descent must walk the
    spine                                  ENTIRE spine — this is where
                                         h matters, still O(h) worst case.
    duplicate values                    -> excluded by the constraints
                                         ("All Nodes will have unique
                                         values"); the comparison logic
                                         above assumes strict ordering.
    p not present in the tree             -> not a case the constraints
                                         allow (p is guaranteed to be a
                                         node in the tree); the unified
                                         descent would behave as if
                                         searching for a value that
                                         happens not to exist, which is
                                         undefined behavior here by design.


================================================================================
COMMON MISTAKES
================================================================================
1. Assuming the successor is always found by "if no right child, look at
   p's PARENT" directly — this problem's TreeNode has no parent pointer
   (unlike LC 510's variant), so you must re-derive the ancestor chain by
   descending from `root`, not by walking up.

2. Forgetting Case A entirely and only implementing the ancestor-descent —
   fails immediately whenever `p` has a right child, which is roughly half
   of all nodes in a random BST.

3. In Case A, returning `p.right` itself instead of continuing left to find
   its MINIMUM — correct only when `p.right` happens to have no left
   child, silently wrong otherwise.

4. In the unified descent, using `<=` instead of `<` for
   `p.val < node.val` — this would treat `p` itself as "bigger than p,"
   incorrectly recording `p` as its own candidate successor (and then
   incorrectly continuing to search its own left subtree instead of its
   right subtree).

5. Searching for `p` by identity (`node is p`) instead of by VALUE
   comparison (`p.val < node.val`) in the unified descent — works, but
   requires an extra field/branch to switch modes after finding `p`; the
   value-only comparison collapses this into one rule, which is the whole
   point of the unified approach.

6. Materializing the whole in-order sequence (Approach 0) when asked to
   optimize — correct, but ignores that a BST answers this in O(h) with no
   traversal at all.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Now find the in-order PREDECESSOR instead (the largest value less than
   `p.val`).
A: The exact mirror: if `p.left` exists, the predecessor is the MAXIMUM of
   that subtree (walk `left`, then `right` all the way down). Otherwise,
   descend from `root` remembering the last node where you turned RIGHT
   (i.e. the closest ancestor smaller than `p.val`). The unified descent
   mirrors too: flip every `<`/`left`/`right` in the code above.

Q: What if each node HAD a parent pointer (LC 510's exact variant)?
A: Then you don't need `root` at all: if `p.right` exists, same Case A
   (leftmost of `p.right`). Otherwise, walk UP via `parent` pointers until
   you reach a node that IS its own parent's left child — that parent is
   the successor. O(h) time, O(1) space, and root is never consulted.

Q: How would you answer successor/predecessor queries MANY times on the
   same static tree?
A: Precompute the full in-order sequence once into a sorted array (O(n)
   space, O(n) one-time cost), then binary search for `p.val`'s position
   and index +1/-1 — O(log n) per query after the one-time cost, useful
   when queries vastly outnumber tree mutations. If the tree also mutates
   frequently, the augmented-size-counter trick from problem 007's
   follow-up generalizes to rank-based lookup too.

Q: Connect this to problem 005's LCA and problem 001's search.
A: All three are "pure comparison descent from the root, O(h), no
   traversal" — LCA compares TWO values against each node to find a split
   point; search compares ONE value for equality; this problem compares
   ONE value for a one-sided bound and remembers the tightest candidate.
   Same shape, different question asked at each node.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Pattern 3 of the topic guide's taxonomy (Part 5.3): descent remembering the
best candidate seen so far, instead of failing on a miss.

    LC 510  Inorder Successor in BST II (parent pointers, no root)
    LC 700  Search in a Binary Search Tree     — same descent, exact match
                                                only, no candidate tracking (001)
    LC 270  Closest BST Value                   — descent tracking the
                                                closest value overall, not
                                                just one-sided
    LC 235  Lowest Common Ancestor of a BST      — descent comparing TWO
                                                values, not one (005)
    LC 938  Range Sum of BST                     — descent pruning on a
                                                two-sided range
    LC 501  Find Mode in Binary Search Tree       — in-order adjacent-run
                                                counting (allows duplicates)
================================================================================
"""

import random
import time
from collections import deque
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def inorderSuccessor(self, root: 'TreeNode', p: 'TreeNode') -> Optional['TreeNode']:
        """✅ THE ANSWER — unified comparison descent, no branch on
        p.right. O(h) time, O(1) space."""
        candidate = None
        node = root
        while node:
            if p.val < node.val:
                candidate = node
                node = node.left
            else:
                node = node.right
        return candidate

    def inorderSuccessor_two_cases(self, root: 'TreeNode',
                                   p: 'TreeNode') -> Optional['TreeNode']:
        """Two explicit cases, matching the question file's explanation.
        Same O(h) cost, more lines."""
        if p.right:
            node = p.right
            while node.left:
                node = node.left
            return node
        candidate = None
        node = root
        while node:
            if p.val < node.val:
                candidate = node
                node = node.left
            elif p.val > node.val:
                node = node.right
            else:
                break
        return candidate

    def inorderPredecessor(self, root: 'TreeNode', p: 'TreeNode') -> Optional['TreeNode']:
        """Follow-up: the mirror problem. Largest value strictly less than
        p.val. O(h) time, O(1) space."""
        candidate = None
        node = root
        while node:
            if p.val > node.val:
                candidate = node
                node = node.right
            else:
                node = node.left
        return candidate

    def inorderSuccessor_full_scan_oracle(self, root: 'TreeNode',
                                          p: 'TreeNode') -> Optional['TreeNode']:
        """Oracle only (used by the tests, not the answer): iterative
        in-order scan, return the node immediately after p. O(h + rank(p))
        time, O(h) space."""
        stack, node, found = [], root, False
        while stack or node:
            while node:
                stack.append(node)
                node = node.left
            node = stack.pop()
            if found:
                return node
            if node is p:
                found = True
            node = node.right
        return None


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


def find_node(root, val):
    node = root
    while node:
        if node.val == val:
            return node
        node = node.left if val < node.val else node.right
    return None


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


# ==============================================================================
# TESTS — run:  python 010_inorder_successor_in_bst_solution.py
# ==============================================================================
CASES = [
    ([2, 1, 3], 1, 2),
    ([2, 1, 3], 2, 3),
    ([2, 1, 3], 3, None),
    ([5, 3, 6, 2, 4, None, None, 1], 6, None),
    ([5, 3, 6, 2, 4, None, None, 1], 3, 4),
    ([5, 3, 6, 2, 4, None, None, 1], 4, 5),
    ([5, 3, 6, 2, 4, None, None, 1], 1, 2),
    ([5, 3, 6, 2, 4, None, None, 1], 2, 3),
    ([1], 1, None),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: unified single descent (the answer) ---")
    for values, pv, want in CASES:
        root = build(values)
        p = find_node(root, pv)
        got = sol.inorderSuccessor(root, p)
        got_val = got.val if got else None
        ok = got_val == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  tree={values!r:<30} p={pv} "
              f"-> {got_val}  (want {want})")

    print("\n--- both correct implementations agree ---")
    for values, pv, want in CASES:
        root = build(values)
        p = find_node(root, pv)
        a = sol.inorderSuccessor(root, p)
        b = sol.inorderSuccessor_two_cases(root, p)
        av = a.val if a else None
        bv = b.val if b else None
        ok = av == bv == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  p={pv}  unified={av} two-case={bv}")

    # ----------------------------------------------------------------------
    # Predecessor follow-up: cross-checked against sorted-list neighbors.
    # ----------------------------------------------------------------------
    print("\n--- follow-up: predecessor, cross-checked ---")
    values = [5, 3, 6, 2, 4, None, None, 1]
    root = build(values)
    sorted_vals = sorted(v for v in values if v is not None)
    pred_mismatches = 0
    for v in sorted_vals:
        p = find_node(root, v)
        idx = sorted_vals.index(v)
        expected = sorted_vals[idx - 1] if idx > 0 else None
        got = sol.inorderPredecessor(root, p)
        got_val = got.val if got else None
        if got_val != expected:
            pred_mismatches += 1
        print(f"  predecessor({v}) = {got_val}  (want {expected})")
    all_ok &= (pred_mismatches == 0)

    # ----------------------------------------------------------------------
    # STEP BY STEP trace, printed live.
    # ----------------------------------------------------------------------
    print("\n--- trace: unified descent for p=1 on the example tree ---")
    root = build([5, 3, 6, 2, 4, None, None, 1])
    p = find_node(root, 1)
    node, candidate = root, None
    while node:
        if p.val < node.val:
            candidate = node
            print(f"  at {node.val}: {p.val} < {node.val} -> candidate = "
                  f"{node.val}, go LEFT")
            node = node.left
        else:
            print(f"  at {node.val}: {p.val} >= {node.val} -> go RIGHT")
            node = node.right
    print(f"  successor(1) = {candidate.val if candidate else None}")

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 1: nodes touched — O(h) descent vs O(n) full scan.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 1: nodes touched — O(h) descent vs full in-order scan ---")
    n = 60_000
    bal = balanced_bst(0, n)
    h = height_iterative(bal)
    print(f"  balanced tree, n={n}, height={h}")

    def visited_unified(root, p):
        visits, node = 0, root
        candidate = None
        while node:
            visits += 1
            if p.val < node.val:
                candidate = node
                node = node.left
            else:
                node = node.right
        return visits, candidate

    for target, label in ((1, "near the minimum"), (n // 2, "middle value"),
                          (n - 2, "near the maximum")):
        p = find_node(bal, target)
        visits, cand = visited_unified(bal, p)
        print(f"  p={target:<8} ({label:<17}) nodes touched = {visits:>3} "
              f"(<= height {h})  successor = {cand.val if cand else None}")
    print("  Every query touches at most `height` nodes, regardless of WHERE")
    print("  p sits in sorted order — unlike a full in-order scan, which must")
    print("  walk up to the entirety of the tree to reach a value near the end.")

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 2: wall clock, unified descent vs full-scan oracle.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 2: wall clock — O(h) descent vs O(h+rank) full scan ---")
    p_near_end = find_node(bal, n - 2)
    reps = 3000
    t0 = time.perf_counter()
    for _ in range(reps):
        sol.inorderSuccessor(bal, p_near_end)
    t1 = time.perf_counter()
    for _ in range(reps):
        sol.inorderSuccessor_full_scan_oracle(bal, p_near_end)
    t2 = time.perf_counter()
    us_descent = (t1 - t0) / reps * 1e6
    us_scan = (t2 - t1) / reps * 1e6
    print(f"  p near the maximum (rank ~{n-1} of {n})")
    print(f"  unified O(h) descent:      {us_descent:8.2f} us/call")
    print(f"  full in-order scan oracle: {us_scan:8.2f} us/call")
    print(f"  speedup: {us_scan / us_descent:.0f}x")
    print("  Measured on THIS machine: the full scan must walk almost the")
    print("  entire in-order sequence to reach a node near the end, while the")
    print("  descent only ever takes `height` steps regardless of rank.")
    demo2_ok = us_scan > us_descent
    all_ok &= demo2_ok

    # ----------------------------------------------------------------------
    # Randomised cross-check: unified descent vs the full-scan oracle,
    # across every node in many random BSTs, successor AND predecessor.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs full-scan oracle ---")
    random.seed(285)
    mismatches, trials = 0, 800
    for _ in range(trials):
        vals = random.sample(range(-2000, 2000), random.randint(1, 40))
        root = None
        for v in vals:
            root = bst_insert_iterative(root, v)
        sorted_vals = sorted(vals)
        for v in vals:
            p = find_node(root, v)
            a = sol.inorderSuccessor(root, p)
            b = sol.inorderSuccessor_two_cases(root, p)
            c = sol.inorderSuccessor_full_scan_oracle(root, p)
            av = a.val if a else None
            bv = b.val if b else None
            cv = c.val if c else None
            idx = sorted_vals.index(v)
            expected = sorted_vals[idx + 1] if idx + 1 < len(sorted_vals) else None
            if not (av == bv == cv == expected):
                mismatches += 1
    print(f"  {trials} random BSTs x every node: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
