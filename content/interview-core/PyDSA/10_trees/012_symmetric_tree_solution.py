"""
================================================================================
SOLUTION · LeetCode 101 · Symmetric Tree                                [Easy]
https://leetcode.com/problems/symmetric-tree/
================================================================================

THE CORE IDEA
--------------
A tree is symmetric iff its left and right subtrees are MIRROR images of each
other. That is two-pointer recursion over ONE tree's two halves — not two
separate trees, the way 007 (Same Tree) walks `p` and `q`:

    def isSymmetric(root):
        if not root:
            return True
        return isMirror(root.left, root.right)

    def isMirror(left, right):
        if not left and not right:   return True      # both empty: fine
        if not left or not right:    return False     # exactly one empty
        if left.val != right.val:    return False
        return (isMirror(left.left,  right.right)     # CROSSED: outer edges
                and isMirror(left.right, right.left))  # CROSSED: inner edges

Compare this line-for-line against 007's `isSameTree`:

    007 isSameTree(p, q):    same(p.left, q.left)  and same(p.right, q.right)
                              -> SAME-SIDE pairing: left-with-left, right-with-right
    012 isMirror(l, r):      mirror(l.left, r.right) and mirror(l.right, r.left)
                              -> CROSSED pairing: left's-left with right's-right,
                                 left's-right with right's-left

That one swap is the entire problem. Everything else — the base cases, the
value check, the `and` — is copied verbatim from 007.

WHY THE PAIRING MUST BE CROSSED, CONCRETELY
--------------------------------------------
Picture folding the tree down its vertical center line. A point on the left
at "go left, then go left" ends up, after folding, directly on top of the
point on the right reached by "go right, then go right" — both are the
OUTERMOST branches. A point on the left at "go left, then go right" (nearer
the centerline) folds onto the right's "go right, then go left" — both are
the INNERMOST branches. That is exactly `isMirror(l.left, r.right)` and
`isMirror(l.right, r.left)`. Pairing same sides instead (`l.left` vs
`r.left`) would ask "are the left and right subtrees IDENTICAL", which is a
different, strictly stronger question — a tree can be symmetric without its
two halves being identical (Example 1: the left half is `[2,3,4]`, the right
half is `[2,4,3]` — NOT identical, but a mirror of each other), so same-side
pairing produces false NEGATIVES on genuinely symmetric trees. Demonstrated
live below on the canonical LC example.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (WRONG, deliberate breakage): use 007's SAME-SIDE pairing instead
   of crossed — `isSameTree(root.left, root.right)`. This asks "is the left
   subtree an exact copy of the right subtree", not "is the right subtree a
   mirror of the left subtree". It gives a FALSE NEGATIVE on
   `[1,2,2,3,4,4,3]` (LC's own "true" example): the left subtree `[2,3,4]`
   and right subtree `[2,4,3]` are mirrors but not copies, so same-side
   pairing wrongly reports False. Verified live below — this is the #1
   conceptual bug on this problem.

Approach 1 (recursive isMirror, crossed pairing) ✅ — the shape above.
   O(n) time (every node visited once in the symmetric case; early exit on
   the first mismatch otherwise), O(h) space for the call stack.

Approach 2 (iterative, explicit stack of PAIRS) ✅ — push `(l, r)` pairs,
   pop, check, push the two CROSSED child pairs. Same idea as 007 Approach 3,
   crossed instead of same-side. O(n) time, O(h) (stack) or O(w) (queue, BFS-
   flavored — see below) space, immune to Python's recursion limit (topic
   guide §2.2). Since it naturally processes pairs of nodes from opposite
   sides, using a `collections.deque` and popping from the LEFT makes it a
   genuine level-order / BFS walk of mirrored pairs (topic guide Part 3) —
   useful when you also want "process level by level" as a side effect, and
   the version to reach for on adversarially deep trees per the topic guide's
   recursion-limit discussion (§2.2).

Approach 3 (serialisation-based comparison) — encode the left subtree
   normally (preorder, null markers) and the right subtree with LEFT and
   RIGHT SWAPPED at every step (mirrored preorder), then compare the two
   strings for equality. If the mirrored encoding of the right subtree
   equals the plain encoding of the left subtree, the tree is symmetric.
   O(n) time and space. This inherits 008's exact null-marker and delimiter
   pitfalls: omit either and you get false positives, demonstrated live
   below with a concrete failing case (not assumed — built and run).


================================================================================
STEP BY STEP TRACE — root = [1,2,2,3,4,4,3]
================================================================================
            1
          ╱   ╲
         2      2
       ╱  ╲    ╱  ╲
      3    4  4    3

isSymmetric(1) -> isMirror(left=2(3,4), right=2(4,3))

isMirror(2, 2)                          # root.left vs root.right
  vals equal (2 == 2)
  CROSSED pair 1: isMirror(left.left=3, right.right=3)
      vals equal (3 == 3)
      isMirror(3.left=None, 3.right=None) -> both None -> True
      isMirror(3.right=None, 3.left=None) -> both None -> True
      -> True
  CROSSED pair 2: isMirror(left.right=4, right.left=4)
      vals equal (4 == 4)
      isMirror(4.left=None, 4.right=None) -> True
      isMirror(4.right=None, 4.left=None) -> True
      -> True
  -> True and True = True

isSymmetric returns True.

Notice which nodes get compared: the LEFT tree's `3` (left.left.left, i.e.
node 2's LEFT child) is compared against the RIGHT tree's `3` (right.right,
i.e. the other node 2's RIGHT child) — outer edges of the fold. The LEFT
tree's `4` (node 2's right child) is compared against the RIGHT tree's `4`
(the other node 2's LEFT child) — inner edges of the fold. Same-side pairing
would instead compare left's `3` against right's `4` and fail immediately —
exactly the bug Approach 0 demonstrates.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time    Space   Mutates?  Note
    ---------------------------------  ------  ------  --------  -------------
    Same-side pairing (broken)         O(n)    O(h)    no        WRONG ANSWER
    Recursive isMirror, crossed ✅     O(n)    O(h)    no        the answer
    Iterative stack of crossed pairs ✅ O(n)   O(h)    no        no rec. limit
    BFS deque of crossed pairs         O(n)    O(w)    no        level-by-level
    Serialise (plain vs mirrored) ✅   O(n)    O(n)    no        needs markers +
                                                                    delimiters
    Serialise, no markers (broken)     O(n)    O(n)    no        FALSE POSITIVE

    h = height (O(log n) balanced, O(n) skewed); w = max width (can be O(n)
    for a wide, shallow tree — topic guide §3.1).


================================================================================
EDGE CASES
================================================================================
    empty tree                  -> True. Vacuously symmetric; also the base
                                    case `isSymmetric` must handle before ever
                                    calling `isMirror`.
    single node                 -> True. `isMirror(None, None)` -> True.
    root, two children, equal values, both leaves
                                 -> True. The simplest non-trivial case.
    root, two children, different values
                                 -> False. Caught by the `left.val != right.val`
                                    check at the very first `isMirror` call.
    equal values, shape differs ([1,2,2,null,3,null,3])
                                 -> False. LC's own counterexample: same VALUES
                                    on each side but the `3`s hang off the SAME
                                    side (both right children) instead of
                                    mirrored sides, so folding does not align
                                    them. Caught by the "exactly one None"
                                    base case deep in the recursion, not by
                                    the value check.
    symmetric at the top level, broken deeper down
                                 ([1,2,2,3,4,4,3] with one leaf value changed,
                                    e.g. the rightmost 3 -> 9)
                                 -> False. Top-level values (2,2) and the
                                    first crossed pair (3,3) still match; the
                                    mismatch is only caught at depth 2 —
                                    proof that shallow checks are not enough
                                    and the recursion must go all the way down.


================================================================================
COMMON MISTAKES
================================================================================
1. SAME-SIDE pairing instead of CROSSED pairing — reusing 007's
   `isSameTree(root.left, root.right)` verbatim. This is THE central bug:
   it answers "is the left subtree identical to the right subtree", which
   is stricter than "is the right subtree a mirror of the left subtree", and
   it fails LC's own example ([1,2,2,3,4,4,3]) by reporting False when the
   true answer is True. Demonstrated live below.

2. Forgetting the paired null-vs-null / null-vs-non-null base cases
   (mirroring 007's ordering: check both-None first, then either-None, THEN
   read `.val`). Reading `.val` before ruling out None raises AttributeError,
   exactly as in 007.

3. Assuming a single traversal string, reversed and compared, is enough
   without null markers. E.g. comparing `preorder(left)` against
   `reversed(preorder(right))` as plain value lists ignores shape entirely —
   the same ambiguity trap 008 hit with `[1,2]` vs `[1,null,2]`: two
   structurally different subtrees can produce identical value sequences.
   Demonstrated live below with a concrete false positive.

4. Using recursion unguarded on an adversarially deep but still symmetric
   tree (e.g. two long chains hanging off the root, each `n/2` deep). Python's
   ~1000-frame recursion limit (topic guide §2.2) turns a valid, symmetric
   input into a crashing `RecursionError`; the iterative pair-stack version
   has no such limit. Measured below.

5. Comparing `root.left == root.right` (or checking they are the SAME object)
   instead of walking values — object identity/equality says nothing about
   mirror structure, and `TreeNode` has no `__eq__` (007, mistake 5).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Do it iteratively.
A: Approach 2 — a stack (or deque) of CROSSED pairs `(l.left, r.right)` and
   `(l.right, r.left)`, same three checks as the recursive base cases.

Q: What's the difference between this and isSameTree (007)?
A: Same base cases and same overall recursive shape, but the pairing is
   crossed instead of same-side: mirror-checking one tree's two halves,
   versus equality-checking two independent trees. Symmetric Tree can also be
   framed as `isSameTree(root.left, invertTree(root.right))` — invert one
   side (004, LC 226) and then do a same-side comparison — which is a useful
   alternate framing to mention, at the cost of an extra O(n) inversion pass
   (and, if done in place, mutating input the crossed version never does).

Q: Generalize to an n-ary tree.
A: A node's children no longer have a fixed "left"/"right" — the definition
   becomes "the list of the leftmost subtree's children, in order, equals
   the reverse of the rightmost subtree's children's list, recursively,
   pairwise mirrored inward". Concretely: zip the children list against its
   own reverse and recurse on each matched pair, exactly generalizing the
   two-child crossed pairing to a k-child one.

Q: Must you use recursion, or is an explicit-stack requirement realistic?
A: Realistic on deep/adversarial trees — see mistake 4 and the measured
   recursion-limit demo below; the pair-stack (or pair-deque) version is the
   answer either way.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
    LC 100   Same Tree                       — the non-mirrored sibling,
                                                 same-side pairing (007 here)
    LC 951   Flip Equivalent Binary Trees    — try BOTH pairings (same-side OR
                                                 crossed) at every node
    LC 226   Invert Binary Tree              — invert one side, then same-side
                                                 compare: an alternate framing
                                                 (004 here)
    LC 572   Subtree of Another Tree         — the serialization pitfalls this
                                                 file's Approach 3 inherits
                                                 (008 here)
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
    # ------------------------------------------------------------------
    # Approach 1 — the answer: recursive isMirror, CROSSED pairing.
    # ------------------------------------------------------------------
    def isSymmetric(self, root: Optional[TreeNode]) -> bool:
        """Two-pointer recursion over one tree's two halves. O(n) time,
        O(h) space."""
        if not root:
            return True
        return self._isMirror(root.left, root.right)

    def _isMirror(self, left: Optional[TreeNode], right: Optional[TreeNode]) -> bool:
        if not left and not right:
            return True
        if not left or not right:
            return False
        if left.val != right.val:
            return False
        return (self._isMirror(left.left, right.right)      # outer edges
                and self._isMirror(left.right, right.left))  # inner edges

    # ------------------------------------------------------------------
    # Approach 2 — iterative, explicit stack of CROSSED pairs.
    # ------------------------------------------------------------------
    def isSymmetric_iterative(self, root: Optional[TreeNode]) -> bool:
        """One stack of crossed pairs. O(n) time, O(h) space, no recursion
        limit."""
        if not root:
            return True
        stack = [(root.left, root.right)]
        while stack:
            l, r = stack.pop()
            if not l and not r:
                continue
            if not l or not r:
                return False
            if l.val != r.val:
                return False
            stack.append((l.left, r.right))
            stack.append((l.right, r.left))
        return True

    # ------------------------------------------------------------------
    # Approach 2b — BFS with a deque of crossed pairs: level-by-level.
    # ------------------------------------------------------------------
    def isSymmetric_bfs(self, root: Optional[TreeNode]) -> bool:
        """Same crossed pairing, FIFO instead of LIFO — a genuine BFS over
        mirrored pairs (topic guide Part 3). O(n) time, O(w) space."""
        if not root:
            return True
        queue = deque([(root.left, root.right)])
        while queue:
            l, r = queue.popleft()
            if not l and not r:
                continue
            if not l or not r:
                return False
            if l.val != r.val:
                return False
            queue.append((l.left, r.right))
            queue.append((l.right, r.left))
        return True

    # ------------------------------------------------------------------
    # Approach 3 — serialise left plainly, right MIRRORED, compare.
    # ------------------------------------------------------------------
    def isSymmetric_serialised(self, root: Optional[TreeNode]) -> bool:
        """Encode the left subtree preorder (root, left, right); encode the
        right subtree with children SWAPPED at every step (root, right,
        left) -- i.e. its mirror-preorder. The tree is symmetric iff the two
        strings match. O(n) time and space; uses 008's null-marker +
        delimiter machinery to stay injective."""
        if not root:
            return True
        return self._encode_plain(root.left) == self._encode_mirrored(root.right)

    @staticmethod
    def _encode_plain(node: Optional[TreeNode]) -> str:
        out: List[str] = []

        def walk(nd):
            if nd is None:
                out.append(",#")
                return
            out.append(f",{nd.val}")
            walk(nd.left)
            walk(nd.right)

        walk(node)
        return "".join(out)

    @staticmethod
    def _encode_mirrored(node: Optional[TreeNode]) -> str:
        """Same walk, but RIGHT before LEFT at every step -- the mirror
        image of the plain preorder encoding."""
        out: List[str] = []

        def walk(nd):
            if nd is None:
                out.append(",#")
                return
            out.append(f",{nd.val}")
            walk(nd.right)     # swapped
            walk(nd.left)      # swapped

        walk(node)
        return "".join(out)

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def isSymmetric_broken_sameside(self, root: Optional[TreeNode]) -> bool:
        """✗ BROKEN ON PURPOSE — reuses 007's SAME-SIDE isSameTree pairing
        instead of crossing it. Answers 'is the left subtree identical to
        the right subtree', not 'is it a mirror' -- a stricter, wrong
        condition. THE central bug for this problem."""
        if not root:
            return True
        return self._same_side(root.left, root.right)

    def _same_side(self, p, q) -> bool:
        if not p and not q:
            return True
        if not p or not q:
            return False
        if p.val != q.val:
            return False
        return self._same_side(p.left, q.left) and self._same_side(p.right, q.right)

    @staticmethod
    def _encode_no_markers_plain(node) -> str:
        """✗ BROKEN ON PURPOSE — no null markers: value list only."""
        out: List[str] = []

        def walk(nd):
            if nd is None:
                return
            out.append(f",{nd.val}")
            walk(nd.left)
            walk(nd.right)

        walk(node)
        return "".join(out)

    @staticmethod
    def _encode_no_markers_mirrored(node) -> str:
        """✗ BROKEN ON PURPOSE — mirrored walk, still no null markers."""
        out: List[str] = []

        def walk(nd):
            if nd is None:
                return
            out.append(f",{nd.val}")
            walk(nd.right)
            walk(nd.left)

        walk(node)
        return "".join(out)

    def isSymmetric_broken_no_markers(self, root: Optional[TreeNode]) -> bool:
        if not root:
            return True
        return (self._encode_no_markers_plain(root.left)
                == self._encode_no_markers_mirrored(root.right))


# ==============================================================================
# TEST HELPERS — standard tree kit (documented in 001)
# ==============================================================================
def build(values):
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


def build_symmetric(depth, rng, vals=6):
    """Build a random tree, then MIRROR-COPY it onto the other side of a
    fresh root, guaranteeing a genuinely symmetric tree (whose two halves
    need not be identical)."""
    def random_half(d):
        if d == 0 or rng.random() < 0.25:
            return None
        node = TreeNode(rng.randrange(vals))
        node.left = random_half(d - 1)
        node.right = random_half(d - 1)
        return node

    def mirror_copy(node):
        if node is None:
            return None
        return TreeNode(node.val, mirror_copy(node.right), mirror_copy(node.left))

    root = TreeNode(rng.randrange(vals))
    left = random_half(depth)
    root.left = left
    root.right = mirror_copy(left)
    return root


def random_tree(n, rng, vals=6):
    if n == 0:
        return None
    root = TreeNode(rng.randrange(vals))
    nodes = [root]
    for _ in range(n - 1):
        parent = rng.choice(nodes)
        while parent.left is not None and parent.right is not None:
            parent = rng.choice(nodes)
        node = TreeNode(rng.randrange(vals))
        if parent.left is None and (parent.right is not None or rng.random() < 0.5):
            parent.left = node
        else:
            parent.right = node
        nodes.append(node)
    return root


def build_symmetric_chain(depth, val=1):
    """Two chains of length `depth` hanging off a shared root, each a mirror
    of the other -- deep AND symmetric, for the recursion-limit demo."""
    root = TreeNode(val)

    left = None
    for _ in range(depth):
        node = TreeNode(val)
        node.left = left
        left = node
    root.left = left

    right = None
    for _ in range(depth):
        node = TreeNode(val)
        node.right = right
        right = node
    root.right = right

    return root


# ==============================================================================
# TESTS — run:  python 012_symmetric_tree_solution.py
# ==============================================================================
CASES = [
    ([1, 2, 2, 3, 4, 4, 3], True),
    ([1, 2, 2, None, 3, None, 3], False),
    ([], True),
    ([1], True),
    ([1, 2, 2], True),
    ([1, 2, 2, None, 3, 3, None], True),
    ([1, 2, 2, 3, None, None, 3], True),
    ([1, 2, 2, 3, None, 3, None], False),
    ([1, 2, 3], False),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: recursive isMirror, crossed pairing ---")
    for vals, want in CASES:
        got = sol.isSymmetric(build(vals))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  root={vals!r:<32} -> {got}  (want {want})")

    print("\n--- correctness: iterative, BFS, serialised ---")
    impls = [
        ("iterative pair stack", sol.isSymmetric_iterative),
        ("BFS pair queue      ", sol.isSymmetric_bfs),
        ("serialised (mirror)  ", sol.isSymmetric_serialised),
    ]
    for name, fn in impls:
        ok = all(fn(build(vals)) == want for vals, want in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- randomised cross-check: guaranteed-symmetric + arbitrary trees ---")
    rng = random.Random(101)
    mismatches = 0
    trials = 1000
    for i in range(trials):
        if i % 2 == 0:
            t = build_symmetric(rng.randint(0, 6), rng)
        else:
            t = random_tree(rng.randint(0, 15), rng, vals=4)
        want = sol.isSymmetric(t)
        if any(fn(t) != want for _, fn in impls):
            mismatches += 1
    print(f"  {trials} random trees, 4 implementations: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # ⚠️  THE central bug: same-side pairing vs crossed pairing.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: SAME-SIDE pairing (007's isSameTree, reused wrong) ---")
    vals = [1, 2, 2, 3, 4, 4, 3]
    t = build(vals)
    print(f"  root = {vals}   (LC's own 'true' example)")
    print("  left subtree  = [2,3,4]   right subtree = [2,4,3]")
    print("  these are MIRRORS of each other but NOT identical trees")
    same_side_result = sol.isSymmetric_broken_sameside(t)
    crossed_result = sol.isSymmetric(t)
    print(f"  same-side pairing (broken) -> {same_side_result}   <- WRONG "
          f"(false negative)")
    print(f"  crossed pairing (correct)  -> {crossed_result}")
    all_ok &= (same_side_result is False and crossed_result is True)

    # a case where same-side pairing accidentally gets it right, for contrast
    vals2 = [1, 2, 2, 3, 3, 3, 3]
    t2 = build(vals2)
    print(f"\n  contrast: root = {vals2} (left and right subtrees ARE identical here)")
    print(f"  same-side pairing -> {sol.isSymmetric_broken_sameside(t2)}   "
          f"(right by accident: identical trees are also mirrors of themselves)")
    print(f"  crossed pairing    -> {sol.isSymmetric(t2)}")
    print("  Same-side pairing only ever agrees with crossed pairing when the")
    print("  two halves happen to be identical, not merely mirrored -- the")
    print("  general case (the LC example above) exposes the difference.")

    # ----------------------------------------------------------------------
    # ⚠️  Serialisation without null markers: a concrete false positive.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: serialisation WITHOUT null markers ---")
    vals3 = [1, 2, 2, None, 3, None, 3]
    t3 = build(vals3)
    print(f"  root = {vals3}   (LC's own 'false' example)")
    l_enc = Solution._encode_no_markers_plain(t3.left)
    r_enc = Solution._encode_no_markers_mirrored(t3.right)
    print(f"  encode_no_markers_plain(left)      = {l_enc!r}")
    print(f"  encode_no_markers_mirrored(right)  = {r_enc!r}")
    fp = sol.isSymmetric_broken_no_markers(t3)
    truth = sol.isSymmetric(t3)
    print(f"  no-markers comparison -> {fp}   <- FALSE POSITIVE" if fp != truth
          else f"  no-markers comparison -> {fp}")
    print(f"  the truth              -> {truth}")
    l_full = Solution._encode_plain(t3.left)
    r_full = Solution._encode_mirrored(t3.right)
    print(f"  with markers: encode_plain(left)     = {l_full!r}")
    print(f"  with markers: encode_mirrored(right) = {r_full!r}")
    print(f"  markers+delimiters comparison -> {sol.isSymmetric_serialised(t3)}")
    print("  Same lesson as 008: a preorder value list alone is not injective,")
    print("  so 'reversed traversal equals the other traversal' is not a valid")
    print("  symmetry test without null markers preserving the shape.")
    all_ok &= (fp is True and truth is False
               and sol.isSymmetric_serialised(t3) is False)

    # ----------------------------------------------------------------------
    # trace: the crossed-pair recursion, printed.
    # ----------------------------------------------------------------------
    print("\n--- trace: isMirror on root.left/root.right of [1,2,2,3,4,4,3] ---")
    calls = []

    def traced(l, r, depth=0):
        lv = l.val if l else None
        rv = r.val if r else None
        calls.append((lv, rv))
        pad = "  " * (depth + 1)
        if not l and not r:
            print(f"{pad}isMirror(None, None) -> True")
            return True
        if not l or not r:
            print(f"{pad}isMirror({lv}, {rv}) -> False (one side empty)")
            return False
        if l.val != r.val:
            print(f"{pad}isMirror({lv}, {rv}) -> False (values differ)")
            return False
        print(f"{pad}isMirror({lv}, {rv}): values match, cross-descend")
        return (traced(l.left, r.right, depth + 1)
                and traced(l.right, r.left, depth + 1))

    root = build([1, 2, 2, 3, 4, 4, 3])
    result = traced(root.left, root.right)
    print(f"  result {result} after {len(calls)} calls")

    # ----------------------------------------------------------------------
    # RUNTIME: recursion limit on a deep-but-symmetric tree.
    # ----------------------------------------------------------------------
    print("\n--- measured: recursion limit on a deep, genuinely symmetric tree ---")
    saved = sys.getrecursionlimit()
    depth = 100_000
    deep_sym = build_symmetric_chain(depth)
    print(f"  two mirrored chains of depth {depth} hanging off a shared root")
    sys.setrecursionlimit(saved)  # keep Python's default ~1000 limit
    raised = False
    try:
        sol.isSymmetric(deep_sym)
    except RecursionError:
        raised = True
    print(f"  recursion at limit {sys.getrecursionlimit()}: "
          f"RecursionError = {raised}")
    it_ok = sol.isSymmetric_iterative(deep_sym)
    bfs_ok = sol.isSymmetric_bfs(deep_sym)
    print(f"  iterative pair stack: returned {it_ok} with no limit to hit")
    print(f"  BFS pair queue:       returned {bfs_ok} with no limit to hit")
    all_ok &= (raised and it_ok and bfs_ok)

    print("\n  ... and timed, recursive (raised limit) vs iterative, on a")
    print("  smaller-but-still-deep symmetric tree the recursive version CAN")
    print("  finish, to compare their actual cost:")
    sys.setrecursionlimit(20_000)
    try:
        mid = build_symmetric_chain(6_000)
        t0 = time.perf_counter()
        r1 = sol.isSymmetric(mid)
        t1 = time.perf_counter()
        r2 = sol.isSymmetric_iterative(mid)
        t2 = time.perf_counter()
        r3 = sol.isSymmetric_bfs(mid)
        t3 = time.perf_counter()
        print(f"  recursive (raised limit): {r1}  {(t1 - t0) * 1000:.2f}ms")
        print(f"  iterative pair stack:     {r2}  {(t2 - t1) * 1000:.2f}ms")
        print(f"  BFS pair queue:           {r3}  {(t3 - t2) * 1000:.2f}ms")
        all_ok &= (r1 and r2 and r3)
    finally:
        sys.setrecursionlimit(saved)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
