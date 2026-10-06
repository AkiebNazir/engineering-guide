"""
================================================================================
SOLUTION · LeetCode 112 · Path Sum                                       [Easy]
https://leetcode.com/problems/path-sum/
================================================================================

THE CORE IDEA
--------------
"Does some root-to-leaf path sum to targetSum" needs each node to know how
much of targetSum its ANCESTORS already consumed. Information cannot flow
from ancestor to descendant through a return value — return values go UP.
It has to flow through a PARAMETER, carried DOWN:

    def go(node, remaining):
        if node is None:
            return False
        remaining -= node.val
        if node.left is None and node.right is None:   # a leaf
            return remaining == 0
        return go(node.left, remaining) or go(node.right, remaining)

That is the whole solution. One integer of state, threaded downward, tested
only at leaves. Nothing needs to come back UP except the boolean answer
itself — no aggregation across siblings beyond `or`.

O(n) time, O(h) space (the call stack).

THIS IS THE MIRROR IMAGE OF THE BOTTOM-UP PATTERN (topic guide Part 4):
    009 (Balanced), 010 (Diameter), 018 (Max Path Sum) all compute a property
    of a node's DESCENDANTS and RETURN it up the call stack (postorder).
    This problem computes a property of a node's ANCESTORS and PASSES it
    down the call stack (preorder-shaped, parameter-carrying) — exactly the
    other half of the guide's Part 4.1/4.2 split, and the direct sibling of
    015 (Count Good Nodes), which carries the running MAX instead of a
    running REMAINING-TARGET. Same shape, different payload.

THE SUBTLETY THAT MAKES THIS "EASY" PROBLEM HAVE A REAL BUG IN IT: the
`remaining == 0` test must fire ONLY at a leaf. A non-leaf node can have a
cumulative sum that happens to equal targetSum while still having children —
that is not a complete root-to-leaf path. Checking "any node" instead of
"any LEAF" is demonstrated as a live, concrete bug below (not asserted).


================================================================================
MULTIPLE APPROACHES
================================================================================
0. ITERATIVE, EXPLICIT STACK OF (node, remaining) — the recursive algorithm
   with the call stack made into a Python list you control. O(n) time, O(h)
   space, immune to Python's ~1000-frame recursion limit. Per the topic
   guide §2.2, this is not academic: n can be 5000 here and a chain of 5000
   nodes is a legal input. Measured live below against the recursive version
   on a chain, at the actual N where this machine's recursion limit bites.

1. RECURSIVE TOP-DOWN, `remaining` AS A PARAMETER ✅ — the version above.
   O(n) time, O(h) space. The answer; what an interview expects first.

2. WRONG: CHECK `remaining == 0` AT ANY NODE, NOT JUST LEAVES — the
   deliberate-breakage demo. Built and run below on a concrete small tree
   where it disagrees with the correct answer.

3. BFS, EXPLICIT QUEUE OF (node, remaining) — same idea as approach 0 with a
   `collections.deque`, level order instead of stack order. Correct, O(n)
   time, O(w) space instead of O(h). Included for completeness; the stack
   version is the natural iterative counterpart of the recursion.


================================================================================
STEP BY STEP TRACE — root = [5,4,8,11,null,13,4,7,2,null,null,null,1],
                      targetSum = 22
================================================================================
            5
          ┌─┴──┐
          4     8
        ┌─┘   ┌─┴──┐
       11     13    4
     ┌─┴─┐         ┌─┴┐
     7   2       null 1

    call                       remaining IN   node.val   remaining OUT   leaf?  result
    -------------------------  -------------  ---------  --------------  -----  ------
    go(5,  remaining=22)       22             5          17              no     recurse
      go(4, remaining=17)      17             4          13              no     recurse
        go(11, remaining=13)   13             11         2               no     recurse
          go(7, remaining=2)   2              7          -5              YES    -5==0? False
          go(2, remaining=2)   2              2          0               YES    0==0?  True  <-
        -> True (7-branch False, 2-branch True, `or` -> True)
      -> True
    -> True

    The path 5 -> 4 -> 11 -> 2 is exactly the one LeetCode names, and the
    leaf 2 is where `remaining` finally hits 0. Every other leaf in this tree
    (7, 13, 1) has a nonzero remaining and correctly reports False; the `or`
    chain short-circuits at the first True, so the right-hand subtree (8, 13,
    4, 1) is never even visited once the left side succeeds.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time    Space (aux)  Mutates input?  Note
    -------------------------------------  ------  -----------  --------------  ------------------
    Recursive, `remaining` parameter ✅   O(n)    O(h)         no              the answer
    Iterative DFS, stack of (node, rem)   O(n)    O(h)         no              recursion-limit proof
    Iterative BFS, queue of (node, rem)   O(n)    O(w)         no              order is irrelevant
    Broken: check ANY node, not just leaf O(n)    O(h)         no              WRONG ANSWER

    n = nodes, h = height, w = widest level. No approach mutates the tree;
    `remaining` is an int, passed by value — each recursive call gets its own
    copy, so there is no backtracking "undo" step needed (contrast LC 113,
    which carries a mutable path list and does need one — see FOLLOW-UPS).


================================================================================
EDGE CASES
================================================================================
    empty tree (root is None)     -> False, ALWAYS, even when targetSum == 0.
                                      There are no leaves in an empty tree, so
                                      there is no root-to-leaf path to check —
                                      not even a trivial zero-length one. This
                                      is Example 3 and it is easy to get
                                      backwards by reasoning "0 - 0 == 0".
    single node, val == target    -> True (the node is its own leaf).
    single node, val != target    -> False.
    negative values in the path   -> handled for free: `remaining -= node.val`
                                      works whether node.val is positive,
                                      negative, or zero; no special-casing
                                      needed. Constraints allow [-1000, 1000].
    targetSum == 0, single zero
      valued node                 -> True: remaining starts at 0, subtracts 0,
                                      hits the leaf at exactly 0.
    an INTERNAL node's prefix sum
      equals targetSum, but no
      leaf completes it           -> False is correct; this is exactly the
                                      case the leaf-only check exists for.
                                      Demonstrated live below with a concrete
                                      tree and a concrete wrong answer.
    a leaf reached with
      remaining != 0              -> False for that path; other branches may
                                      still succeed (`or` keeps exploring).


================================================================================
COMMON MISTAKES
================================================================================
1. Checking `remaining == 0` at ANY node instead of only at LEAVES. A node
   whose prefix sum matches targetSum but that still has children is not the
   end of a path — reporting True there is a bug. Demonstrated live below on
   root=[1,2,3], targetSum=1: the root's own value already equals the target,
   but the root has two children, so no root-to-LEAF path of sum 1 exists
   (the leaves sum to 1+2=3 and 1+3=4). The correct answer is False; checking
   "any node" gives True.

2. Off-by-one in WHAT "remaining" means — subtracting `node.val` AFTER the
   leaf check instead of BEFORE it. If you test `remaining == 0` and only
   then do `remaining -= node.val`, the leaf's own value never gets
   subtracted, and every leaf is tested against last leaf's PARENT'S
   remaining instead of its own. Always subtract first, check second.

3. Forgetting the `root is None` base case, or having it return `True`
   instead of `False`. `True` would make every empty subtree trivially
   satisfy any target, which then makes plenty of trees falsely pass — the
   classic way this shows up is writing `not node.left and not node.right`
   for "leaf" and forgetting that `go(None, ...)` is reached from a node
   with only ONE child, where the other branch must NOT silently succeed.

4. Treating a one-child node as if it were a leaf. `node.left is None` alone
   does not mean node is a leaf — it means the LEFT branch is closed. The
   leaf test must be `node.left is None AND node.right is None`; a node with
   only a right child is not a leaf and must recurse into that right child.

5. Assuming recursion is always safe. n can be 5000 and a chain of 5000
   nodes is legal input; Python's default recursion limit is ~1000 frames.
   Measured live below: the recursive version RAISES on a large enough chain
   on this machine, the iterative version does not.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the actual path(s), not just True/False.
A: LC 113 (Path Sum II) — same recursion, but now you carry a mutable path
   LIST down as well: append the node's value on entry, and if you're at a
   qualifying leaf, append a COPY of the path to the results; then pop the
   value on the way back up (the backtracking "undo" this problem's plain
   int doesn't need — topic guide Part 4 / topic 09).

Q: Count (or sum) paths from ANY node to ANY descendant, not just root to
   leaf, summing to targetSum.
A: LC 437 (Path Sum III). This stops being "carry one number down" and
   becomes topic 04's prefix-sum-as-hashmap-key trick walked along tree
   paths instead of array indices: a running prefix sum plus a
   `seen = {0: 1}` hashmap of prefix-sum counts along the current root-to-
   node path, incrementing on entry and decrementing on exit (see topic
   guide Part 6).

Q: What if node values could make the running sum overflow, or the tree
   could be a long chain?
A: Python ints don't overflow, so that half is free; the chain case is
   exactly the recursion-limit issue measured below — switch to the
   iterative stack version, or raise the limit and mention the C stack is
   still a hard ceiling.

Q: Sum root-to-leaf numbers formed by concatenating digits, not adding
   values.
A: LC 129 (Sum Root to Leaf Numbers) — same top-down shape, but the
   parameter carried down is `running_number = running_number * 10 +
   node.val` instead of a subtracted remaining, and the aggregation at each
   qualifying leaf is a SUM across all leaves instead of an `or`.


================================================================================
RELATED PROBLEMS — the pattern family
================================================================================
  TOP-DOWN, carry state down as a parameter (this pattern; topic guide Part 4.1):
    LC 112   Path Sum                             — this problem
    LC 1448  Count Good Nodes in Binary Tree       — carry the running MAX (015 here)
    LC 113   Path Sum II                           — 112 + carry the path list (mutable, needs undo)
    LC 129   Sum Root to Leaf Numbers               — carry the number built so far
    LC 437   Path Sum III                          — prefix-sum + hashmap along paths (topic guide Part 6)

  BOTTOM-UP, return a value up — the mirror pattern (topic guide Part 4.2):
    LC 104   Maximum Depth                        — return the height up
    LC 110   Balanced Binary Tree                  — return height, flag imbalance (009 here)
    LC 543   Diameter of Binary Tree               — return depth, keep a global best (010 here)
    LC 124   Binary Tree Maximum Path Sum          — return gain, keep a global best (018 here)
================================================================================
"""

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
    def hasPathSum(self, root: Optional[TreeNode], targetSum: int) -> bool:
        """Top-down DFS carrying the remaining target down as a parameter.
        O(n) time, O(h) space. See THE CORE IDEA above."""
        if root is None:
            return False

        def go(node: Optional[TreeNode], remaining: int) -> bool:
            remaining -= node.val
            if node.left is None and node.right is None:   # a leaf
                return remaining == 0
            if node.left is not None and go(node.left, remaining):
                return True
            if node.right is not None and go(node.right, remaining):
                return True
            return False

        return go(root, targetSum)

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def hasPathSum_iterative_stack(self, root: Optional[TreeNode],
                                    targetSum: int) -> bool:
        """Approach 0: explicit stack of (node, remaining). O(n) time,
        O(h) space, immune to the recursion limit."""
        if root is None:
            return False
        stack = [(root, targetSum)]
        while stack:
            node, remaining = stack.pop()
            remaining -= node.val
            if node.left is None and node.right is None:
                if remaining == 0:
                    return True
                continue
            if node.left is not None:
                stack.append((node.left, remaining))
            if node.right is not None:
                stack.append((node.right, remaining))
        return False

    def hasPathSum_iterative_bfs(self, root: Optional[TreeNode],
                                  targetSum: int) -> bool:
        """Approach 3: BFS queue of (node, remaining). O(n) time, O(w)
        space. Level order is irrelevant here — kept for completeness."""
        if root is None:
            return False
        q = deque([(root, targetSum)])
        while q:
            node, remaining = q.popleft()
            remaining -= node.val
            if node.left is None and node.right is None:
                if remaining == 0:
                    return True
                continue
            if node.left is not None:
                q.append((node.left, remaining))
            if node.right is not None:
                q.append((node.right, remaining))
        return False

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def hasPathSum_broken_any_node(self, root: Optional[TreeNode],
                                    targetSum: int) -> bool:
        """✗ BROKEN ON PURPOSE — tests `remaining == 0` at ANY node, not
        just leaves. A non-leaf node whose prefix sum matches targetSum is
        reported as a hit even though it is not the end of any path."""
        if root is None:
            return False

        def go(node: Optional[TreeNode], remaining: int) -> bool:
            if node is None:
                return False
            remaining -= node.val
            if remaining == 0:                 # BUG: no leaf check
                return True
            return go(node.left, remaining) or go(node.right, remaining)

        return go(root, targetSum)


# ==============================================================================
# TEST HELPERS — standard tree kit (documented in 001/008/015)
# ==============================================================================
def build(vals: List[Optional[int]]) -> Optional[TreeNode]:
    """Level-order list with `None` for absent children -> root node."""
    if not vals or vals[0] is None:
        return None
    root = TreeNode(vals[0])
    queue = deque([root])
    i = 1
    while queue and i < len(vals):
        node = queue.popleft()
        if i < len(vals):
            v = vals[i]
            i += 1
            if v is not None:
                node.left = TreeNode(v)
                queue.append(node.left)
        if i < len(vals):
            v = vals[i]
            i += 1
            if v is not None:
                node.right = TreeNode(v)
                queue.append(node.right)
    return root


def to_level_order(root: Optional[TreeNode]) -> List[Optional[int]]:
    if root is None:
        return []
    out: List[Optional[int]] = []
    queue = deque([root])
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


def left_chain(vals: List[int]) -> Optional[TreeNode]:
    """A left-only chain from a list of values (h == n)."""
    if not vals:
        return None
    root = TreeNode(vals[0])
    cur = root
    for v in vals[1:]:
        cur.left = TreeNode(v)
        cur = cur.left
    return root


def random_tree(n, rng, vals=6):
    if n == 0:
        return None
    root = TreeNode(rng.randrange(-vals, vals))
    nodes = [root]
    for _ in range(n - 1):
        parent = rng.choice(nodes)
        while parent.left is not None and parent.right is not None:
            parent = rng.choice(nodes)
        node = TreeNode(rng.randrange(-vals, vals))
        if parent.left is None and (parent.right is not None or rng.random() < 0.5):
            parent.left = node
        else:
            parent.right = node
        nodes.append(node)
    return root


def path_sums_to_leaves(root: Optional[TreeNode]) -> List[int]:
    """Brute force oracle: every root-to-leaf sum, via explicit stack."""
    if root is None:
        return []
    out = []
    stack = [(root, root.val)]
    while stack:
        node, s = stack.pop()
        if node.left is None and node.right is None:
            out.append(s)
            continue
        if node.left is not None:
            stack.append((node.left, s + node.left.val))
        if node.right is not None:
            stack.append((node.right, s + node.right.val))
    return out


def brute_has_path_sum(root, target) -> bool:
    return target in path_sums_to_leaves(root)


# ==============================================================================
# TESTS — run:  python 011_path_sum_solution.py
# ==============================================================================
CASES = [
    ([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, 1], 22, True),
    ([1, 2, 3], 5, False),
    ([], 0, False),
    ([1], 1, True),
    ([1], 2, False),
    ([1, 2], 1, False),
    ([-2, None, -3], -5, True),
    ([0], 0, True),
    ([1, 2, 3], 1, False),          # root's own value equals target, not a leaf
    ([1, -2, -3, 1, 3, -2, None, -1], -1, True),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: three working implementations agree ---")
    impls = [
        ("recursive, `remaining` param ", sol.hasPathSum),
        ("iterative DFS stack          ", sol.hasPathSum_iterative_stack),
        ("iterative BFS queue          ", sol.hasPathSum_iterative_bfs),
    ]
    for name, fn in impls:
        ok = all(fn(build(vals), t) == expected for vals, t, expected in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- per-case output ---")
    for vals, target, expected in CASES:
        got = sol.hasPathSum(build(vals), target)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  root={str(vals):<50} target={target:>5} "
              f"-> {got}  (want {expected})")

    # ----------------------------------------------------------------------
    # Live trace: `remaining` carried DOWN.
    # ----------------------------------------------------------------------
    print("\n--- trace: `remaining` carried DOWN, root = [5,4,8,11,..,2,..1], target=22 ---")
    root = build([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, 1])
    print(f"  {'node':>5} {'depth':>6} {'rem in':>7} {'rem out':>8} {'leaf?':>6} "
          f"{'result':>8}  path")
    order = []

    def trace(node, remaining_in, depth, path):
        if node is None:
            return None
        remaining_out = remaining_in - node.val
        is_leaf = node.left is None and node.right is None
        here_path = path + [node.val]
        if is_leaf:
            result = remaining_out == 0
            order.append((node.val, depth, remaining_in, remaining_out, is_leaf,
                          result, here_path))
            return result
        order.append((node.val, depth, remaining_in, remaining_out, is_leaf,
                      None, here_path))
        left_r = trace(node.left, remaining_out, depth + 1, here_path)
        if left_r:
            return True
        return trace(node.right, remaining_out, depth + 1, here_path)

    found = trace(root, 22, 0, [])
    for val, depth, rin, rout, is_leaf, result, path in order:
        res_txt = "" if result is None else ("True" if result else "False")
        print(f"  {val:>5} {depth:>6} {rin:>7} {rout:>8} "
              f"{'YES' if is_leaf else 'no':>6} {res_txt:>8}  {path}")
    print(f"  hasPathSum(root, 22) = {found}")
    all_ok &= (found is True)
    print("  The successful leaf is 2, reached via 5->4->11->2; `remaining` hits")
    print("  exactly 0 there. The right subtree (8,13,4,1) is never visited once")
    print("  the left side returns True, because `or` short-circuits.")

    # ----------------------------------------------------------------------
    # ⚠️  bug: checking `remaining == 0` at ANY node, not just leaves.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  bug: check remaining==0 at ANY node vs LEAF-ONLY ---")
    root = build([1, 2, 3])
    print("  root = [1,2,3]   targetSum = 1")
    print(f"  leaf sums: {path_sums_to_leaves(root)}  (target 1 is not among them)")
    correct = sol.hasPathSum(root, 1)
    broken = sol.hasPathSum_broken_any_node(root, 1)
    print(f"  correct (leaf-only check)   -> {correct}")
    print(f"  broken  (any-node check)    -> {broken}   <- WRONG: root.val==1 fires")
    print("  immediately, even though the root has two children and neither leaf")
    print("  (1+2=3, 1+3=4) actually sums to 1. The root's prefix sum matching")
    print("  the target is a coincidence of an INTERNAL node, not a completed path.")
    all_ok &= (correct is False and broken is True)

    print("\n  ...and the same bug on the canonical example, checked both ways:")
    root = build([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, 1])
    c2 = sol.hasPathSum(root, 22)
    b2 = sol.hasPathSum_broken_any_node(root, 22)
    print(f"  root=[5,4,8,11,..,2,..,1] target=22  correct={c2}  broken={b2}  "
          f"(agree here: {c2 == b2})")
    print("  The bug does not always fire, which is exactly why it survives")
    print("  casual testing — it needs a prefix that hits the target at a node")
    print("  WITH children, which the canonical example does not happen to have.")

    print("\n--- randomised hunt: how often does the any-node bug lie? ---")
    import random
    rng = random.Random(112)
    wrong = 0
    trials = 4000
    for _ in range(trials):
        n = rng.randint(1, 8)
        root = random_tree(n, rng, vals=3)
        target = rng.randint(-6, 6)
        want = brute_has_path_sum(root, target)
        if sol.hasPathSum_broken_any_node(root, target) != want:
            wrong += 1
    print(f"  {trials} random (tree, target) pairs: any-node bug wrong on "
          f"{wrong} ({100 * wrong / trials:.1f}%)")
    all_ok &= (wrong > 0)
    print("  Small trees over a handful of distinct values are already enough")
    print("  to expose it — this is not an exotic adversarial input.")

    # ----------------------------------------------------------------------
    # Recursion limit: measure the actual N where recursion fails here.
    # ----------------------------------------------------------------------
    print("\n--- recursion limit: measured on THIS machine ---")
    print(f"  sys.getrecursionlimit() = {sys.getrecursionlimit()}")
    default_limit = sys.getrecursionlimit()
    found_n = None
    for n in (900, 995, 998, 999, 1000, 1200, 2000):
        chain = left_chain([0] * n)          # every value 0, never matches, worst case
        try:
            sol.hasPathSum(chain, 1)
            status = "ok"
        except RecursionError:
            status = "RecursionError"
            if found_n is None:
                found_n = n
        print(f"  n={n:>5} (chain, default limit {default_limit}) -> {status}")
    print(f"  first N that raised on this machine: {found_n}")
    all_ok &= (found_n is not None)

    print("\n  constraints allow n up to 5000; a 5000-node chain is legal input:")
    saved = sys.getrecursionlimit()
    chain5000 = left_chain([0] * 5000)
    try:
        sol.hasPathSum(chain5000, 1)
        rec_msg, died = "ok (unexpected)", False
    except RecursionError as exc:
        rec_msg, died = f"{type(exc).__name__}: {exc}", True
    all_ok &= died
    print(f"  recursive, default limit ({saved}) on n=5000 chain -> {rec_msg}")

    it_result_stack = sol.hasPathSum_iterative_stack(chain5000, 1)
    it_result_bfs = sol.hasPathSum_iterative_bfs(chain5000, 1)
    print(f"  iterative DFS stack       on n=5000 chain -> ok, {it_result_stack}")
    print(f"  iterative BFS queue       on n=5000 chain -> ok, {it_result_bfs}")
    all_ok &= (it_result_stack == it_result_bfs == False)
    print("  Both iterative forms carry `remaining` in the stack/queue ENTRY,")
    print("  which is exactly what the call frame was doing implicitly — and")
    print("  neither one cares how deep the chain is.")

    # ----------------------------------------------------------------------
    # Timing: recursive vs iterative, up to the point recursion still works.
    # ----------------------------------------------------------------------
    print("\n--- timing: recursive vs iterative DFS, within the safe range ---")
    sys.setrecursionlimit(20000)
    try:
        print(f"  {'n (chain)':>10} {'recursive (ms)':>15} {'iterative (ms)':>15}")
        for n in (200, 500, 800):
            chain = left_chain([0] * n)
            t0 = time.perf_counter()
            r1 = sol.hasPathSum(chain, 1)
            t1 = time.perf_counter()
            r2 = sol.hasPathSum_iterative_stack(chain, 1)
            t2 = time.perf_counter()
            all_ok &= (r1 == r2 == False)
            print(f"  {n:>10} {(t1 - t0) * 1000:>15.3f} {(t2 - t1) * 1000:>15.3f}")
    finally:
        sys.setrecursionlimit(saved)
    print("  Both are O(n) — this problem is not about complexity, it's about")
    print("  whether the recursive version SURVIVES a large skewed input at all.")

    # ----------------------------------------------------------------------
    # Randomised cross-check.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the brute-force oracle ---")
    rng = random.Random(1120)
    mismatches = 0
    trials = 3000
    for _ in range(trials):
        n = rng.randint(0, 12)
        root = random_tree(n, rng, vals=5) if n > 0 else None
        target = rng.randint(-15, 15)
        want = brute_has_path_sum(root, target)
        for _name, fn in impls:
            if fn(root, target) != want:
                mismatches += 1
    all_ok &= (mismatches == 0)
    print(f"  {trials} random trees x {len(impls)} implementations: {mismatches} mismatches")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
