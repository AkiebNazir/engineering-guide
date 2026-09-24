"""
================================================================================
SOLUTION · LeetCode 98 · Validate Binary Search Tree                 [Medium]
https://leetcode.com/problems/validate-binary-search-tree/
================================================================================

THE CORE IDEA
--------------
A local check ("is my left child smaller than me, is my right child bigger
than me") is NOT the BST invariant. The invariant is about the whole
subtree, not the immediate child, and the fix is one of two equally valid
mental models:

  A. BOUNDS DOWN THE RECURSION. Every node is validated against an open
     interval `(low, high)` handed down by its ANCESTORS, not just its
     parent. Going left tightens `high` to the parent's value; going right
     tightens `low`. A node is legal iff `low < node.val < high`.

  B. IN-ORDER IS SORTED. Part 1 of the topic guide: in-order traversal of a
     valid BST is strictly increasing. Walk in-order, remember the previous
     value, and the instant a value is <= the previous one, the tree is
     invalid. No bounds bookkeeping at all — just one running comparison.

Both are O(n) time, O(h) space, and both are worth knowing: bounds is the
one to reach for first (it generalizes to "range" problems like LC 938),
in-order is the one that makes the "why" undeniable because it's a direct
instance of Part 1's identity.


================================================================================
THE COUNTEREXAMPLE THAT MOTIVATES BOTH APPROACHES
================================================================================
          5
        ╱   ╲
      1       8
            ╱   ╲
          4       9

Every parent-child pair passes a local check: 1 < 5, 8 > 5, 4 < 8, 9 > 8.
The tree is still NOT a BST: 4 sits in 5's RIGHT subtree, and 4 < 5. A
search for 4 starting at the root would go LEFT at 5 (4 < 5) and never find
the 4 sitting on the right. The structure is unusable as a BST even though
every adjacent pair "looks" sorted.

    Bounds catches it:  node 4 inherits low=5 (its ancestor 5's value,
                         because 4 is in 5's right subtree) — 4 is not > 5
                         -> INVALID.
    In-order catches it: in-order visits 1, 5, 4, 9 — 4 follows 5 and
                         4 < 5, not increasing -> INVALID.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, price it and drop it): collect ALL values with a
full traversal into a list, then check `sorted(list) == list and no
duplicates`. Correct, O(n) time, O(n) EXTRA space for the list — strictly
worse than either approach below, which need only O(h). Mentioned because
"collect then check" is many people's first instinct; the fix is to check
DURING the traversal instead of after it, which is exactly approach B.

Approach 1 (bounds, recursive) — the answer:

    def valid(node, low, high):
        if node is None:
            return True
        if not (low < node.val < high):
            return False
        return valid(node.left, low, node.val) and \
               valid(node.right, node.val, high)

O(n) time (every node visited once), O(h) recursion stack. Short-circuits on
the FIRST violation found, so real-world inputs with an early bad node
finish faster than n, though the worst case is still O(n).

Approach 2 (in-order, recursive with a mutable box) — equivalent cost, a
different way to see the same fact:

    def inorder(node):
        nonlocal prev, ok
        if node is None or not ok:
            return
        inorder(node.left)
        if prev is not None and node.val <= prev:
            ok = False
            return
        prev = node.val
        inorder(node.right)

Approach 3 (in-order, ITERATIVE with an explicit stack) ✅ the version
shipped below — same idea as Approach 2, no recursion. This is the one to
default to when `n` can be large and the tree might be skewed (Part 7 of the
topic guide): a 10^4-node sorted-input BST is legal under this problem's
constraints and is exactly the shape that blows Python's ~1000-frame
recursion ceiling.

Approach 4 (bounds, ITERATIVE with an explicit stack of `(node, low, high)`
triples) — same idea as Approach 1, no recursion. Shipped below alongside 3
so both families have a stack-safe version.


================================================================================
STEP BY STEP TRACE — bounds approach, the counterexample tree
================================================================================
tree = [5,1,8,null,null,4,9]

          5
        ╱   ╲
      1       8
            ╱   ╲
          4       9

valid(5, -inf, +inf):  -inf < 5 < +inf                         ok
  valid(1, -inf, 5):    -inf < 1 < 5                            ok
    valid(None, ...) x2                                        ok, ok
  valid(8, 5, +inf):    5 < 8 < +inf                            ok
    valid(4, 5, 8):      5 < 4 < 8  ->  5 < 4 is FALSE          INVALID ✗
    (short-circuits; valid(9, 8, +inf) never runs)

result: False


================================================================================
STEP BY STEP TRACE — in-order approach, the same tree
================================================================================
stack-based in-order walk, `prev` starts at None:

  push 5, go left -> push 1, go left -> None, pop 1
    prev is None -> prev = 1                          [prev=1]
    go right of 1 -> None, pop 5
    5 > 1 -> ok, prev = 5                              [prev=5]
    go right of 5 -> 8, push 8, go left -> push 4, go left -> None, pop 4
    4 <= prev(5)  ->  INVALID ✗ (return False immediately)

result: False


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time   Space   Mutates input?  Note
    -------------------------------  -----  ------  --------------  -----------
    Collect-all-then-sort (brute)    O(n)   O(n)    no              check AFTER,
                                                                     wasteful
    Bounds, recursive                O(n)   O(h)    no              short-circuits
    In-order, recursive (box)        O(n)   O(h)    no              same cost
    In-order, iterative ✅           O(n)   O(h)    no              no recursion
                                                                     ceiling
    Bounds, iterative ✅             O(n)   O(h)    no              no recursion
                                                                     ceiling

    h = O(log n) balanced, h = O(n) skewed. There is no pruning possible in
    the worst case for EITHER approach — an invalid node could be the very
    last one visited, so O(n) is the true worst case, not just an upper
    bound the algorithm fails to reach.


================================================================================
EDGE CASES
================================================================================
    single node                  -> trivially valid; both approaches
                                     terminate at the base case immediately.
    duplicate values              -> INVALID under this problem's strict
                                     "<" / ">" definition (LC 98 explicitly
                                     rejects `[1,1]` and `[2,2,2]`). A `<=`
                                     bounds check would wrongly accept them.
    INT_MIN / INT_MAX as a value   -> `(-2**31)` or `(2**31 - 1)`. Using
                                     Python's own `-inf`/`float('inf')` as
                                     the initial bounds handles this for
                                     free — no need for sentinel integers
                                     like `float('-inf')` vs `-2**31 - 1`
                                     tricks that languages with fixed-width
                                     ints need.
    locally-sorted but globally    -> the counterexample above. The whole
    invalid tree                    reason this problem exists.
    left-skewed / right-skewed     -> h == n; the iterative versions handle
    (sorted input inserted           this fine, the recursive ones risk
    one-by-one)                      RecursionError at LC 98's 10^4 limit.
    already-invalid tree, error    -> both approaches must be able to
    at the ROOT's immediate child    report False on the very first
                                     comparison, not just deep in the tree.


================================================================================
COMMON MISTAKES
================================================================================
1. Checking only `node.left.val < node.val < node.right.val` (local check).
   Passes the counterexample tree above. This is THE mistake this problem
   exists to catch.

2. Using `<=`/`>=` instead of strict `<`/`>` in the bounds check or the
   in-order comparison. LC 98 treats duplicate values as invalid; `<=`
   silently accepts them.

3. Initializing bounds with sentinel integers (`-2**31 - 1`, `2**31`)
   instead of `float('-inf')`/`float('inf')`. Works until a test uses
   INT_MIN/INT_MAX as an actual node value, at which point the sentinel
   collides with a legal value and produces a false negative.

4. Forgetting that `prev` must be a value that survives across recursive
   calls (a `nonlocal`, an instance attribute, or a one-element list used as
   a box) — a plain local variable reassigned inside a recursive call does
   NOT persist back to the caller in Python, since integers are immutable
   and each call gets its own local binding.

5. Going recursive without measuring the recursion ceiling against the
   problem's stated `n <= 10^4` limit. A skewed tree at that size is legal
   input and will raise `RecursionError` on the default ~1000-frame limit.

6. Short-circuiting incorrectly in the iterative bounds version — e.g.
   pushing both children before checking the current node's own bounds,
   which can report a false negative for a subtree that was never actually
   invalid because the check order is misread as "check child, not check
   self against bounds."


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Which approach would you use in production, given `n` up to 10^4?
A: Iterative, either family — no recursion ceiling risk, same O(n)/O(h)
   cost. Bounds is usually slightly preferred because it can report WHERE
   and WHY a node is invalid (the violated interval), which is more useful
   for a validator that needs to explain itself, not just answer true/false.

Q: What if the tree allows duplicates, placed however the problem defines
   ("duplicates go in the right subtree")?
A: Relax the bound on exactly the side duplicates are allowed: e.g.
   `low <= node.val < high` for "duplicates go right". State which
   direction you're relaxing and why — get this backwards and duplicates on
   the wrong side pass silently.

Q: How would you validate WITHOUT extra space, not even O(h)?
A: Morris in-order traversal — temporarily rethread `null` right pointers
   to create backward links, walk with O(1) space, then undo the threading
   on the way past. Same strictly-increasing check as approach 3, but no
   stack and no recursion. Worth naming; rarely worth coding live unless
   explicitly asked, since it is fiddly to get the pointer restoration
   right under pressure.

Q: How would you validate a tree that's too large to fit in memory, read
   from a stream in some traversal order?
A: If the stream is pre-order, you can validate with the bounds approach
   online, one node at a time, using an explicit stack of `(low, high)`
   pairs that mirrors the recursion — never materializing the whole tree.

Q: Extend this to "how many nodes violate the BST property" instead of a
   yes/no?
A: Same bounds walk, but instead of returning False immediately, accumulate
   a violation count and continue (being careful about what bounds to pass
   the children of an already-invalid node — usually you keep propagating
   the ORIGINAL correct bounds, not ones derived from the bad value).


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Pattern 2 of the topic guide's taxonomy: in-order-is-sorted, used as a TEST.

    LC 230  Kth Smallest Element in a BST    — in-order used to INDEX (007)
    LC 173  Binary Search Tree Iterator       — in-order used to RESUME (008)
    LC 938  Range Sum of BST                  — bounds pruning, two-sided
    LC 270  Closest BST Value                 — descent tracking best-so-far
    LC 99   Recover Binary Search Tree         — in-order finds the two
                                                 out-of-order values (Hard)
    LC 530  Minimum Absolute Difference in BST — in-order adjacent-pair
                                                 minimum
    LC 700  Search in a Binary Search Tree     — the same descent, no
                                                 bounds needed (001)
================================================================================
"""

from collections import deque
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def isValidBST(self, root: Optional[TreeNode]) -> bool:
        """✅ THE ANSWER — in-order, iterative, explicit stack. O(n) time,
        O(h) space, no recursion ceiling."""
        stack, node, prev = [], root, None
        while stack or node:
            while node:
                stack.append(node)
                node = node.left
            node = stack.pop()
            if prev is not None and node.val <= prev:
                return False
            prev = node.val
            node = node.right
        return True

    def isValidBST_bounds_recursive(self, root: Optional[TreeNode]) -> bool:
        """Bounds threaded down the recursion. O(n) time, O(h) stack."""
        def valid(node, low, high):
            if node is None:
                return True
            if not (low < node.val < high):
                return False
            return valid(node.left, low, node.val) and \
                   valid(node.right, node.val, high)
        return valid(root, float('-inf'), float('inf'))

    def isValidBST_bounds_iterative(self, root: Optional[TreeNode]) -> bool:
        """Same bounds idea, no recursion — an explicit stack of
        (node, low, high) triples."""
        if root is None:
            return True
        stack = [(root, float('-inf'), float('inf'))]
        while stack:
            node, low, high = stack.pop()
            if node is None:
                continue
            if not (low < node.val < high):
                return False
            stack.append((node.left, low, node.val))
            stack.append((node.right, node.val, high))
        return True

    def isValidBST_inorder_recursive(self, root: Optional[TreeNode]) -> bool:
        """In-order with a mutable box, recursive. Same cost as the
        iterative version, kept here to demonstrate the `nonlocal`/box
        requirement called out in mistake #4."""
        state = {"prev": None, "ok": True}

        def walk(node):
            if node is None or not state["ok"]:
                return
            walk(node.left)
            if state["prev"] is not None and node.val <= state["prev"]:
                state["ok"] = False
                return
            state["prev"] = node.val
            walk(node.right)

        walk(root)
        return state["ok"]

    def isValidBST_local_check_broken(self, root: Optional[TreeNode]) -> bool:
        """✗ BROKEN ON PURPOSE — mistake #1: checks only the immediate
        child, not the whole subtree. Passes the counterexample tree."""
        if root is None:
            return True
        if root.left and root.left.val >= root.val:
            return False
        if root.right and root.right.val <= root.val:
            return False
        return (self.isValidBST_local_check_broken(root.left) and
                self.isValidBST_local_check_broken(root.right))


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


def chain_bst(n):
    """A legal, strictly increasing chain: 0 -> 1 -> ... -> n-1, every node
    a right child. Valid, but height == n."""
    root = None
    for v in range(n):
        root = bst_insert_iterative(root, v)
    return root


# ==============================================================================
# TESTS — run:  python 006_validate_binary_search_tree_solution.py
# ==============================================================================
CASES = [
    ([2, 1, 3], True),
    ([5, 1, 4, None, None, 3, 6], False),
    ([5, 1, 8, None, None, 4, 9], False),     # every parent-child pair is fine
    ([1], True),
    ([1, 1], False),                           # duplicates are invalid
    ([2, 2, 2], False),
    ([10, 5, 15, None, None, 6, 20], False),   # 6 is in 10's right subtree
    ([3, 1, 5, 0, 2, 4, 6], True),
    ([-2147483648], True),                     # INT_MIN as a real value
    ([2147483647], True),                      # INT_MAX as a real value
    ([0, None, -1], False),                    # right child smaller than root
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: iterative in-order (the answer) ---")
    for values, want in CASES:
        got = sol.isValidBST(build(values))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {values!r:<40} -> {got}  (want {want})")

    print("\n--- all four correct implementations agree ---")
    for values, want in CASES:
        a = sol.isValidBST(build(values))
        b = sol.isValidBST_bounds_recursive(build(values))
        c = sol.isValidBST_bounds_iterative(build(values))
        d = sol.isValidBST_inorder_recursive(build(values))
        ok = a == b == c == d == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {values!r:<40} -> "
              f"in-order-iter={a} bounds-rec={b} bounds-iter={c} in-order-rec={d}")

    # ----------------------------------------------------------------------
    # ⚠️ LIVE DEMO: mistake #1, local-check-only, fooled by the counterexample.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: the local-check trap ---")
    tree = [5, 1, 8, None, None, 4, 9]
    correct = sol.isValidBST(build(tree))
    broken = sol.isValidBST_local_check_broken(build(tree))
    print(f"  tree {tree}")
    print(f"  correct (whole-subtree bounds): {correct}")
    print(f"  broken  (parent-child only):    {broken}")
    print("  Every parent-child pair (1<5, 8>5, 4<8, 9>8) is individually")
    print("  fine, so the local check says True. The tree is not a BST: 4")
    print("  sits in 5's right subtree and 4 < 5. This is exactly why the")
    print("  problem's own definition says 'the whole left/right SUBTREE'.")
    trap_demonstrated = (correct is False and broken is True)
    all_ok &= trap_demonstrated
    print(f"  trap demonstrated (correct=False, broken=True): "
          f"{trap_demonstrated}")

    # ----------------------------------------------------------------------
    # STEP BY STEP trace, printed live.
    # ----------------------------------------------------------------------
    print("\n--- trace: bounds approach on the counterexample tree ---")
    def traced_valid(node, low, high, depth=0):
        pad = "  " * depth
        if node is None:
            return True
        inside = low < node.val < high
        print(f"{pad}valid({node.val}, {low}, {high}) -> "
              f"{low} < {node.val} < {high} -> {inside}")
        if not inside:
            return False
        return (traced_valid(node.left, low, node.val, depth + 1) and
                traced_valid(node.right, node.val, high, depth + 1))
    traced_valid(build(tree), float('-inf'), float('inf'))

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: recursion ceiling on a legal skewed BST.
    # ----------------------------------------------------------------------
    print("\n--- DEMO: a legal skewed BST breaks recursive validation ---")
    import sys
    n = 3000
    chain = chain_bst(n)
    print(f"  chain of {n} nodes (strictly increasing, legal input), "
          f"recursion limit {sys.getrecursionlimit()}")
    it_result = sol.isValidBST(chain)
    print(f"  iterative in-order: {it_result}")
    raised = False
    try:
        sol.isValidBST_bounds_recursive(chain)
        print("  recursive bounds: did NOT raise this run")
    except RecursionError as e:
        raised = True
        print(f"  recursive bounds: RecursionError -> {e!r}")
    print(f"  iterative succeeded where recursive failed: "
          f"{it_result is True and raised}")
    print("  LC 98 allows n up to 10^4, and sorted/near-sorted input is a")
    print("  natural (not adversarial-only) way to produce this shape —")
    print("  exactly the case Part 7 of the topic guide calls out.")
    all_ok &= (it_result is True and raised)

    # ----------------------------------------------------------------------
    # Randomised cross-check across all four correct implementations.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check: valid BSTs built by insertion ---")
    import random
    random.seed(98)
    mismatches, trials = 0, 3000
    for _ in range(trials):
        vals = random.sample(range(-500, 500), random.randint(1, 40))
        root = None
        for v in vals:
            root = bst_insert_iterative(root, v)
        a = sol.isValidBST(root)
        b = sol.isValidBST_bounds_recursive(root)
        c = sol.isValidBST_bounds_iterative(root)
        d = sol.isValidBST_inorder_recursive(root)
        # a tree built purely by bst_insert_iterative is always valid
        if not (a is b is c is d is True):
            mismatches += 1
    print(f"  {trials} random valid BSTs x 4 implementations: "
          f"{mismatches} mismatches")
    all_ok &= (mismatches == 0)

    print("\n--- randomised cross-check: corrupted trees (swap two node vals) ---")
    random.seed(99)
    mismatches2, trials2 = 0, 3000
    for _ in range(trials2):
        vals = random.sample(range(-500, 500), random.randint(3, 40))
        root = None
        nodes = []
        for v in vals:
            root = bst_insert_iterative(root, v)
        # collect nodes, swap two values to corrupt the tree (usually)
        stack, collected = [root], []
        while stack:
            n_ = stack.pop()
            if n_ is None:
                continue
            collected.append(n_)
            stack.append(n_.left)
            stack.append(n_.right)
        if len(collected) >= 2:
            i, j = random.sample(range(len(collected)), 2)
            collected[i].val, collected[j].val = collected[j].val, collected[i].val
        a = sol.isValidBST(root)
        b = sol.isValidBST_bounds_recursive(root)
        c = sol.isValidBST_bounds_iterative(root)
        d = sol.isValidBST_inorder_recursive(root)
        if not (a is b is c is d):
            mismatches2 += 1
    print(f"  {trials2} corrupted trees x 4 implementations: "
          f"{mismatches2} mismatches")
    all_ok &= (mismatches2 == 0)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
