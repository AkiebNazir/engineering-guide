"""
================================================================================
SOLUTION · LeetCode 100 · Same Tree                                     [Easy]
https://leetcode.com/problems/same-tree/
================================================================================

THE CORE IDEA
--------------
Walk BOTH trees at once, one step in each per call, and compare node against
node:

    def isSameTree(p, q):
        if not p and not q:   return True      # both empty
        if not p or not q:    return False     # exactly one empty: shapes differ
        if p.val != q.val:    return False     # same shape so far, wrong value
        return (isSameTree(p.left,  q.left)
                and isSameTree(p.right, q.right))

O(min(n, m)) time — `and` short-circuits, so the walk stops at the first
difference and can never visit more nodes than the smaller tree holds.
O(min(h_p, h_q)) space for the call stack.

This is the TWO-TREE SIMULTANEOUS RECURSION pattern, and it is worth learning
as one pattern with a parameterised pairing, because the whole family is one
line apart:

    007 Same Tree        same(a.left, b.left) and same(a.right, b.right)
                          -> pair LEFT with LEFT, RIGHT with RIGHT
    012 Symmetric Tree   mirror(a.left, b.right) and mirror(a.right, b.left)
                          -> pair LEFT with RIGHT: CROSSED
    100 vs 951           flip-equivalent: try BOTH pairings at each node
    617 Merge Trees      same walk, but build a node instead of a bool

The base cases must be ordered `both-None`, `one-None`, `values`. Reading
`p.val` before the None checks is an `AttributeError`, and the tests below
trigger the real exception to prove it.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (WRONG, but everybody tries it): compare traversals. Collect the
preorder of each tree and compare the lists. It fails on `[1,2]` vs
`[1,null,2]` — both have preorder `[1,2]` — because a traversal without null
markers throws away the shape. Demonstrated live below.

Approach 0b (WRONG, more subtly): compare BOTH the preorder and the inorder.
For trees with DISTINCT values that is actually sound (it is the uniqueness
theorem problem 016 relies on). With duplicates it breaks: `[1,1]` (root with
a LEFT child) and `[1,null,1]` (root with a RIGHT child) have identical
preorder `[1,1]` AND identical inorder `[1,1]`. LeetCode 100's constraints
allow duplicates, so this is a real failure, and it is measured below. Knowing
*why* it breaks — duplicates destroy the uniqueness proof — is a genuinely
strong interview answer.

Approach 1 (two-tree recursion) ✅ — the shape above. O(min(n,m)) / O(h).
   The answer.

Approach 2 (serialise with null markers and compare strings) — a preorder
   walk that emits a marker for every empty child is a *lossless* encoding, so
   two trees are the same iff their encodings match. O(n + m) time and O(n + m)
   space, and it always walks both trees completely (no early exit). Correct,
   heavier, and the exact machinery problem 008 needs — including the
   delimiter pitfall covered there.

Approach 3 (iterative, one stack of PAIRS) ✅ — push `(p, q)`, pop a pair,
   apply the same three checks, push the two child pairs. O(min(n,m)) time,
   O(h) space, no recursion limit. The right answer to "now do it without
   recursion" on any two-tree problem.

Approach 4 (BFS with a deque of pairs) — same thing level by level; O(w)
   space. Occasionally nicer because a shape mismatch near the root is found
   before descending anywhere deep.


================================================================================
STEP BY STEP TRACE
================================================================================
p = [1,2,3]        q = [1,2,3]              -> True

    same(1, 1)  vals equal
      same(2, 2)  vals equal
        same(None, None) -> True
        same(None, None) -> True
        -> True
      same(3, 3)  vals equal
        same(None, None) -> True
        same(None, None) -> True
        -> True
      -> True and True = True

p = [1,2]          q = [1,null,2]           -> False

    same(1, 1)  vals equal
      same(p.left=2, q.left=None)
        p is not None, q is None -> False        <- caught HERE, at the shape
      `and` short-circuits: same(p.right, q.right) is never called

    Note what the second trace proves: the mismatch is a STRUCTURAL one, and
    the only reason it is caught is the `if not p or not q: return False`
    line. Any approach that compares values alone (Approach 0) walks straight
    past it.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time          Space       Mutates?  Note
    ------------------------------  ------------  ----------  --------  -------------
    Compare preorder value lists    O(n + m)      O(n + m)    no        WRONG ANSWER
    Compare preorder AND inorder    O(n + m)      O(n + m)    no        WRONG with
                                                                          duplicates
    Two-tree recursion ✅           O(min(n,m))   O(min(h))   no        the answer
    Serialise with null markers     O(n + m)      O(n + m)    no        correct, no
                                                                          early exit
    Iterative stack of pairs ✅     O(min(n,m))   O(min(h))   no        no rec. limit
    BFS deque of pairs              O(min(n,m))   O(min(w))   no        shape-first

    Why O(min(n, m)) and not O(n): the recursion advances in both trees
    together and returns False the moment they disagree, so it cannot make
    more calls than the smaller tree has nodes. Two identical trees are the
    worst case — you only pay full price when the answer is True. The demo
    measures the difference between "identical 50k-node trees" and "50k-node
    trees that differ at the root".


================================================================================
EDGE CASES
================================================================================
    both None          -> True    two empty trees are the same tree. This is the
                                    base case, so getting it wrong breaks
                                    everything below it too.
    one None            -> False   the check that catches every shape mismatch.
    [1,2] vs [1,null,2] -> False   THE structural test case. Same values, same
                                    count, different shape.
    [1,2,1] vs [1,1,2]   -> False   same shape, values swapped.
    duplicate values      -> the case that breaks preorder+inorder comparison:
                            [1,1] vs [1,null,1] agree on BOTH traversals.
    negative values        -> irrelevant; only `!=` is used, no arithmetic.
    two 10^5-node chains    -> RecursionError for the recursion; the pair-stack
                            version handles it.


================================================================================
COMMON MISTAKES
================================================================================
1. Comparing traversals instead of walking the trees together. `[1,2]` vs
   `[1,null,2]` is the counterexample, and it is the FIRST thing an
   interviewer will try.
2. Checking `p.val != q.val` before the None checks — `AttributeError` on
   `None.val`. The demo raises the real exception and catches it.
3. `if not p and not q: return False` (inverted) — reports two empty subtrees
   as different, so no tree is ever equal to itself.
4. Using `or` instead of `and` to combine the two subtree results. That
   reports trees as equal when only ONE side matches; the demo shows it
   passing a pair of trees that are obviously different.
5. `p == q` on TreeNode objects. Without `__eq__`, that is identity: it
   returns True only for the very same object, so `isSameTree(t, deep_copy(t))`
   would be False. (And if you DID define `__eq__` to recurse, you would have
   solved the problem — just say that out loud instead of relying on it.)
6. Writing four base cases (`p None and q None`, `p None`, `q None`, values)
   and getting one of the middle two backwards. Two checks cover it:
   both-None, then either-None.
7. Comparing `len(p) == len(q)` node counts first as a "fast path" — node
   count says nothing about shape, and it costs a full O(n+m) walk to compute,
   destroying the early exit that makes this O(min(n,m)).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Iteratively?
A: Approach 3 — a stack of node PAIRS. Same three checks per pop.

Q: What if the trees are the same shape but mirrored — should that count?
A: That is LC 101 (problem 012 here): cross the pairing to
   `(a.left, b.right)` and `(a.right, b.left)`. Same function, one pairing
   changed.

Q: What if either subtree may be flipped, at every node independently?
A: LC 951 Flip Equivalent: at each node, return True if the straight pairing
   works OR the crossed pairing does. Still O(n) because each node is only
   compared against its counterpart.

Q: Is `q` a SUBTREE of `p` somewhere?
A: Problem 008 (LC 572) — call this function at every node of `p`. That gives
   O(n*m) worst case, and the serialise-and-search alternative gets it to
   O(n+m) with an important pitfall.

Q: Compare two trees that may be huge and mostly identical — can you avoid
   walking everything?
A: Not in the worst case (proving equality requires reading both trees), but
   the early exit already means unequal trees usually cost far less. If the
   trees are persistent/structurally shared, an `is` identity check at the top
   of the recursion prunes whole shared subtrees in O(1) — worth mentioning
   for immutable-data-structure settings.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
    LC 101   Symmetric Tree                 — crossed pairing (012 here)
    LC 572   Subtree of Another Tree        — this, called everywhere (008 here)
    LC 951   Flip Equivalent Binary Trees   — try both pairings per node
    LC 617   Merge Two Binary Trees         — two-tree walk that BUILDS a tree
    LC 297   Serialize and Deserialize      — the lossless encoding (019 here)
    LC 105   Build Tree from Preorder+Inorder — why duplicates break uniqueness
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
    def isSameTree(self, p: Optional[TreeNode], q: Optional[TreeNode]) -> bool:
        """Two-tree simultaneous recursion. O(min(n,m)) time, O(h) space."""
        if not p and not q:
            return True
        if not p or not q:
            return False
        if p.val != q.val:
            return False
        return (self.isSameTree(p.left, q.left)
                and self.isSameTree(p.right, q.right))

    def isSameTree_iterative(self, p: Optional[TreeNode],
                             q: Optional[TreeNode]) -> bool:
        """One stack of PAIRS. O(min(n,m)) time, O(h) space, no recursion
        limit. The generic answer to 'now without recursion' for any
        two-tree problem."""
        stack = [(p, q)]
        while stack:
            a, b = stack.pop()
            if not a and not b:
                continue
            if not a or not b:
                return False
            if a.val != b.val:
                return False
            stack.append((a.left, b.left))
            stack.append((a.right, b.right))
        return True

    def isSameTree_bfs(self, p: Optional[TreeNode],
                       q: Optional[TreeNode]) -> bool:
        """BFS over pairs: finds shape mismatches nearest the root first."""
        queue = deque([(p, q)])
        while queue:
            a, b = queue.popleft()
            if not a and not b:
                continue
            if not a or not b:
                return False
            if a.val != b.val:
                return False
            queue.append((a.left, b.left))
            queue.append((a.right, b.right))
        return True

    def isSameTree_serialised(self, p: Optional[TreeNode],
                              q: Optional[TreeNode]) -> bool:
        """Compare LOSSLESS encodings: preorder with a marker for every empty
        child, and a delimiter before every value. O(n+m) time and space, and
        it always reads both trees fully (no early exit)."""
        return self._encode(p) == self._encode(q)

    @staticmethod
    def _encode(node: Optional[TreeNode]) -> str:
        out: List[str] = []

        def walk(nd):
            if nd is None:
                out.append(",#")            # null marker
                return
            out.append(f",{nd.val}")        # delimiter BEFORE every value
            walk(nd.left)
            walk(nd.right)

        walk(node)
        return "".join(out)

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def same_broken_preorder_values(self, p, q) -> bool:
        """✗ BROKEN ON PURPOSE — compares preorder VALUE lists, which throw
        the shape away."""
        def pre(node, out):
            if not node:
                return out
            out.append(node.val)
            pre(node.left, out)
            pre(node.right, out)
            return out
        return pre(p, []) == pre(q, [])

    def same_broken_pre_and_in(self, p, q) -> bool:
        """✗ BROKEN ON PURPOSE — compares preorder AND inorder. Sound for
        DISTINCT values; wrong as soon as values repeat."""
        def pre(node, out):
            if node:
                out.append(node.val)
                pre(node.left, out)
                pre(node.right, out)
            return out

        def ino(node, out):
            if node:
                ino(node.left, out)
                out.append(node.val)
                ino(node.right, out)
            return out
        return pre(p, []) == pre(q, []) and ino(p, []) == ino(q, [])

    def same_broken_val_first(self, p, q) -> bool:
        """✗ BROKEN ON PURPOSE — reads `.val` before ruling out None.
        Raises AttributeError on any shape mismatch."""
        if p is None and q is None:
            return True
        if p.val != q.val:                  # <-- p or q may be None
            return False
        return (self.same_broken_val_first(p.left, q.left)
                and self.same_broken_val_first(p.right, q.right))

    def same_broken_or(self, p, q) -> bool:
        """✗ BROKEN ON PURPOSE — `or` instead of `and`: one matching side is
        enough to declare the trees equal."""
        if not p and not q:
            return True
        if not p or not q:
            return False
        if p.val != q.val:
            return False
        return (self.same_broken_or(p.left, q.left)
                or self.same_broken_or(p.right, q.right))


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


def to_level_order(root):
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


def build_skewed(n, side="left"):
    if n == 0:
        return None
    root = TreeNode(0)
    curr = root
    for i in range(1, n):
        node = TreeNode(i)
        if side == "left":
            curr.left = node
        else:
            curr.right = node
        curr = node
    return root


def random_tree(n, rng, vals=6):
    """Random shape with a SMALL value alphabet, so duplicates are common."""
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


def deep_copy(node):
    if node is None:
        return None
    return TreeNode(node.val, deep_copy(node.left), deep_copy(node.right))


# ==============================================================================
# TESTS — run:  python 007_same_tree_solution.py
# ==============================================================================
CASES = [
    ([1, 2, 3], [1, 2, 3], True),
    ([1, 2], [1, None, 2], False),
    ([1, 2, 1], [1, 1, 2], False),
    ([], [], True),
    ([1], [], False),
    ([], [1], False),
    ([1], [1], True),
    ([1, 2, 3], [1, 2, 4], False),
    ([1, 1], [1, None, 1], False),
    ([10, 5, 15], [10, 5, 15], True),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: two-tree recursion ---")
    for pv, qv, want in CASES:
        got = sol.isSameTree(build(pv), build(qv))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  p={pv!r:<18} q={qv!r:<18} -> {got}  "
              f"(want {want})")

    print("\n--- correctness: iterative, BFS, serialised ---")
    impls = [
        ("iterative pair stack", sol.isSameTree_iterative),
        ("BFS pair queue      ", sol.isSameTree_bfs),
        ("serialised compare  ", sol.isSameTree_serialised),
    ]
    for name, fn in impls:
        ok = all(fn(build(pv), build(qv)) == want for pv, qv, want in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- randomised cross-check (small value alphabet -> many duplicates) ---")
    rng = random.Random(100)
    mismatches = 0
    trials = 800
    for _ in range(trials):
        a = random_tree(rng.randint(0, 12), rng)
        # half the time compare against a copy, half against a fresh tree
        b = deep_copy(a) if rng.random() < 0.5 else random_tree(rng.randint(0, 12), rng)
        want = sol.isSameTree(a, b)
        if any(fn(a, b) != want for _, fn in impls):
            mismatches += 1
    print(f"  {trials} random pairs, 4 implementations: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    print("\n--- property: a tree is the same as its own deep copy ---")
    rng = random.Random(3)
    copy_ok = True
    for _ in range(200):
        a = random_tree(rng.randint(0, 40), rng)
        copy_ok &= sol.isSameTree(a, deep_copy(a))
        copy_ok &= (a == a)                  # identity, for contrast
        if a is not None:
            copy_ok &= not (deep_copy(a) is a)
    print(f"  200 trees: isSameTree(t, deep_copy(t)) always True -> {copy_ok}")
    print("  (`t == deep_copy(t)` would be False — TreeNode has no __eq__, so")
    print("  `==` is identity. Do not lean on it.)")
    all_ok &= copy_ok

    # ----------------------------------------------------------------------
    # ⚠️  Comparing traversals: the structural blind spot.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: comparing PREORDER value lists ---")
    p_vals, q_vals = [1, 2], [1, None, 2]
    p, q = build(p_vals), build(q_vals)
    print(f"  p = {p_vals}   (root 1 with a LEFT child 2)")
    print(f"  q = {q_vals}   (root 1 with a RIGHT child 2)")
    print(f"  preorder of p : {[1, 2]}      preorder of q : {[1, 2]}   IDENTICAL")
    print(f"  compare preorders -> {sol.same_broken_preorder_values(p, q)}  <- WRONG")
    print(f"  walk both trees   -> {sol.isSameTree(p, q)}  <- correct")
    all_ok &= (sol.same_broken_preorder_values(p, q) is True
               and sol.isSameTree(p, q) is False)

    print("\n--- ⚠️  live demo: preorder AND inorder is still not enough (duplicates) ---")
    p, q = build([1, 1]), build([1, None, 1])
    print(f"  p = [1,1]        (root 1, LEFT child 1)")
    print(f"  q = [1,null,1]   (root 1, RIGHT child 1)")

    def pre(node, out=None):
        out = [] if out is None else out
        if node:
            out.append(node.val)
            pre(node.left, out)
            pre(node.right, out)
        return out

    def ino(node, out=None):
        out = [] if out is None else out
        if node:
            ino(node.left, out)
            out.append(node.val)
            ino(node.right, out)
        return out

    print(f"  preorder: p={pre(p)}  q={pre(q)}   inorder: p={ino(p)}  q={ino(q)}")
    print(f"  compare preorder+inorder -> {sol.same_broken_pre_and_in(p, q)}  <- WRONG")
    print(f"  walk both trees          -> {sol.isSameTree(p, q)}  <- correct")
    print("  With DISTINCT values, preorder + inorder does determine the tree")
    print("  uniquely — that theorem is what problem 016 (LC 105) is built on.")
    print("  Duplicates break the proof, and LC 100 permits duplicates.")
    dp, dq = build([1, 2]), build([1, None, 2])
    print(f"  same pair with distinct values ([1,2] vs [1,null,2]): "
          f"pre+in says {sol.same_broken_pre_and_in(dp, dq)} (correctly)")
    all_ok &= (sol.same_broken_pre_and_in(p, q) is True
               and sol.same_broken_pre_and_in(dp, dq) is False)

    print("\n--- and the encoding that IS lossless: preorder + null markers ---")
    print(f"  encode([1,2])      = {Solution._encode(build([1, 2]))!r}")
    print(f"  encode([1,null,2]) = {Solution._encode(build([1, None, 2]))!r}")
    print(f"  encode([1,1])      = {Solution._encode(build([1, 1]))!r}")
    print(f"  encode([1,null,1]) = {Solution._encode(build([1, None, 1]))!r}")
    print("  Distinct strings for distinct trees — that is the property problem")
    print("  008 needs, and the `,` before every value is not decoration: see")
    print("  the false positive it prevents there.")

    # ----------------------------------------------------------------------
    # ⚠️  Base-case ORDER: a real AttributeError.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: checking .val before the None checks ---")
    p, q = build([1, 2]), build([1, None, 2])
    raised = None
    try:
        sol.same_broken_val_first(p, q)
    except AttributeError as e:
        raised = e
    print(f"  same_broken_val_first([1,2], [1,null,2]) raised: {raised!r}")
    print(f"  the correct version returns {sol.isSameTree(p, q)} instead of crashing")
    all_ok &= isinstance(raised, AttributeError)

    print("\n--- ⚠️  live demo: `or` instead of `and` between the two subtrees ---")
    p, q = build([1, 2, 3]), build([1, 2, 99])
    print(f"  p = [1,2,3], q = [1,2,99]  (right children differ)")
    print(f"  ... and ... -> {sol.isSameTree(p, q)}   <- correct")
    print(f"  ... or  ... -> {sol.same_broken_or(p, q)}   <- WRONG: one matching "
          f"side was enough")
    all_ok &= (sol.same_broken_or(p, q) is True and sol.isSameTree(p, q) is False)

    # ----------------------------------------------------------------------
    # trace: the two-tree walk, printed.
    # ----------------------------------------------------------------------
    print("\n--- trace: walking [1,2,3] against [1,2,4] ---")
    calls = []

    def traced(a, b, depth=0):
        pv = a.val if a else None
        qv = b.val if b else None
        calls.append((pv, qv))
        pad = "  " * (depth + 1)
        if not a and not b:
            print(f"{pad}same(None, None) -> True")
            return True
        if not a or not b:
            print(f"{pad}same({pv}, {qv}) -> False (one side empty)")
            return False
        if a.val != b.val:
            print(f"{pad}same({pv}, {qv}) -> False (values differ)")
            return False
        print(f"{pad}same({pv}, {qv}): values match, descend")
        return traced(a.left, b.left, depth + 1) and traced(a.right, b.right, depth + 1)

    result = traced(build([1, 2, 3]), build([1, 2, 4]))
    print(f"  result {result} after {len(calls)} calls")

    # ----------------------------------------------------------------------
    # RUNTIME: the early exit is the whole complexity story.
    # ----------------------------------------------------------------------
    print("\n--- measured: True costs O(n), False can cost O(1) ---")
    saved = sys.getrecursionlimit()
    sys.setrecursionlimit(60_000)
    try:
        bench_rng = random.Random(7)
        big = random_tree(50_000, bench_rng, vals=1000)
        identical = deep_copy(big)
        differ_root = deep_copy(big)
        differ_root.val += 1                        # one changed value, at the root
        differ_left = deep_copy(big)
        node = differ_left
        while node.left or node.right:              # LEFTMOST leaf: found early
            node = node.left or node.right
        node.val += 1
        differ_right = deep_copy(big)
        node = differ_right
        while node.left or node.right:              # RIGHTMOST leaf: found last
            node = node.right or node.left
        node.val += 1

        reps = 5
        rows = [("identical (True)", identical),
                ("differs at ROOT", differ_root),
                ("differs leftmost leaf", differ_left),
                ("differs rightmost leaf", differ_right)]
        print(f"  {'pair':<24} {'result':>7} {'recursion':>12} {'serialised':>12}")
        for label, other in rows:
            t0 = time.perf_counter()
            for _ in range(reps):
                res = sol.isSameTree(big, other)
            t1 = time.perf_counter()
            for _ in range(reps):
                sol.isSameTree_serialised(big, other)
            t2 = time.perf_counter()
            print(f"  {label:<24} {str(res):>7} {(t1-t0)/reps*1000:>10.3f}ms "
                  f"{(t2-t1)/reps*1000:>10.2f}ms")
        print("  Read the rows: the cost of a False is set by WHERE the first")
        print("  difference falls in preorder, not by n. A mismatch at the root")
        print("  or on the leftmost path is found in microseconds; one on the")
        print("  rightmost path costs nearly as much as proving equality, since")
        print("  preorder reaches it last. Only True always pays full price.")
        print("  The serialise-and-compare version has no early exit at all: it")
        print("  encodes both trees in full every time, whatever the answer, and")
        print("  measures ~2x the cost of the worst case for the recursion.")

        print("\n--- and the recursion limit, on two 100,000-node chains ---")
        a = build_skewed(100_000, "left")
        b = build_skewed(100_000, "left")
        sys.setrecursionlimit(saved)                 # back to the default 1000
        raised = False
        try:
            sol.isSameTree(a, b)
        except RecursionError:
            raised = True
        print(f"  recursion at limit {sys.getrecursionlimit()}: "
              f"RecursionError = {raised}")
        it_ok = sol.isSameTree_iterative(a, b)
        print(f"  iterative pair stack: returned {it_ok} with no limit to hit")
        all_ok &= (raised and it_ok)
    finally:
        sys.setrecursionlimit(saved)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
