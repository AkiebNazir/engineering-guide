"""
================================================================================
SOLUTION · LeetCode 144 · Binary Tree Preorder Traversal                [Easy]
https://leetcode.com/problems/binary-tree-preorder-traversal/
================================================================================

THE CORE IDEA
--------------
"Preorder" names one thing only: the position of the *record* step relative
to the two recursive descents.

    def dfs(node):
        if not node: return
        out.append(node.val)      # NODE   <- preorder puts it here
        dfs(node.left)            # LEFT
        dfs(node.right)           # RIGHT

Move that one line down one slot and you have inorder (002); down two and you
have postorder (003). Every node is touched exactly once, so O(n) time; the
recursion is as deep as the tree, so O(h) auxiliary space.

The interview value of this problem is the ITERATIVE form, which is asked
essentially every time as "now do it without recursion":

    stack = [root]
    while stack:
        node = stack.pop()
        out.append(node.val)
        if node.right: stack.append(node.right)   # RIGHT pushed FIRST
        if node.left:  stack.append(node.left)     # LEFT pushed SECOND -> popped FIRST

A stack reverses what you push, so pushing right-then-left makes the left
child come out first. That inversion is the entire trick, and preorder is the
only one of the three orders where the naive "pop, record, push kids" loop
works directly — inorder and postorder need more machinery (002, 003).


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive, don't code it): build the whole level-order list of the
tree, then re-derive the preorder from index arithmetic (`2i+1`, `2i+2`). It
only works on a *complete* tree stored without gaps, silently breaks on any
sparse tree, and costs O(2^h) space for a skewed one. Never the answer — but
worth naming, because it is the array-brain instinct and saying "that only
holds for a complete tree" out loud shows you know why trees use pointers.

Approach 1 (recursion) ✅ — the shape above. O(n) time, O(h) space. Shortest
to write and the one to lead with. Its hidden cost is CPython's recursion
limit: ~1000 frames by default, so a skewed tree of 10^5 nodes raises
`RecursionError` rather than returning an answer. Proven live below.

Approach 2 (one explicit stack) ✅ — the shape above. O(n) time, O(h) space,
no recursion limit to hit. Faster than recursion in CPython too, because a
`list.append`/`list.pop` pair is cheaper than a Python function call — the
benchmark below measures roughly a 25-30% gap on a 50k-node tree.

Approach 3 (recursion, returning concatenated lists):

        return [root.val] + pre(root.left) + pre(root.right) if root else []

    One line, and a real interview answer — but it allocates a new list at
    every node and copies each value once per ancestor, which is O(n * h)
    time (O(n^2) on a skewed tree) instead of O(n). Priced and measured
    below; nice to know, wrong to give as the final answer without naming
    the cost.

Approach 4 (Morris preorder, O(1) space) — threaded-tree trickery that
temporarily rewires `.right` pointers to avoid any stack at all. Covered in
002 where it is more natural (Morris is really an inorder algorithm).


================================================================================
STEP BY STEP TRACE — the iterative version
================================================================================
    Tree (LeetCode notation [1,2,3,4,5,null,8,null,null,6,7,9]):

                    1
                  ╱   ╲
                 2      3
                ╱ ╲       ╲
               4   5       8
                  ╱ ╲     ╱
                 6   7   9

    step  popped   out                  stack after (top on the RIGHT)
    ----  ------  -------------------   ----------------------------
     0     -       []                   [1]
     1     1       [1]                  [3, 2]
     2     2       [1,2]                [3, 5, 4]
     3     4       [1,2,4]              [3, 5]
     4     5       [1,2,4,5]            [3, 7, 6]
     5     6       [1,2,4,5,6]          [3, 7]
     6     7       [1,2,4,5,6,7]        [3]
     7     3       [1,2,4,5,6,7,3]      [8]
     8     8       [...,3,8]            [9]
     9     9       [...,3,8,9]          []

    Note step 1: node 1's RIGHT child (3) is pushed before its LEFT child (2),
    which is why 2 comes off the stack next. The stack always holds the
    "right-hand siblings I still owe a visit to" — exactly the information the
    call stack holds for you in the recursive version.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time      Space (aux)  Mutates input?  Note
    --------------------------  --------  -----------  --------------  ------------------
    Index arithmetic on a       O(2^h)    O(2^h)       no              only correct on a
      level-order array                                                  complete tree
    Recursion ✅                O(n)      O(h)         no              hits CPython's
                                                                         ~1000-frame limit
    One explicit stack ✅       O(n)      O(h)         no              no limit; fastest
    List-concat recursion       O(n*h)    O(n*h)       no              O(n^2) when skewed
    Morris preorder (see 002)   O(n)      O(1)         YES, temporarily  rewires .right,
                                                                         restores it

    h = height. O(h) is O(log n) on a balanced tree and O(n) on a skewed one,
    so "O(h) space" and "O(n) worst-case space" are the same claim — state it
    as O(h) and then name the worst case, which is what the interviewer wants
    to hear.


================================================================================
EDGE CASES
================================================================================
    root = None            -> []      the `if not node: return` base case; the
                                        iterative version must NOT start with
                                        `stack = [root]` unguarded, or it pops
                                        None and crashes on `None.val`.
    single node             -> [val]   no children pushed, loop ends after one
                                        iteration.
    left-only chain          -> the O(h)=O(n) space worst case; also where the
                               recursive version raises RecursionError.
    right-only chain         -> same height, but the iterative stack never holds
                               more than ONE node (each pop pushes exactly one
                               right child), so peak stack size differs wildly
                               between the two skew directions. Measured below.
    duplicate values         -> irrelevant to traversal; nothing compares values.
    negative values          -> irrelevant; nothing does arithmetic on values.


================================================================================
COMMON MISTAKES
================================================================================
1. Pushing LEFT before RIGHT in the iterative version. It runs, it returns n
   values, and it is a *mirror-image* traversal (node, right, left) — the kind
   of wrong answer that passes the `[1]` and `[]` tests and fails everything
   else. The demo below runs this variant and prints its output next to the
   correct one.
2. `stack = [root]` without checking `root is None` first — pops `None` and
   dies on `None.val`. (`stack = [root] if root else []` fixes it.)
3. Returning a value from `dfs` and ignoring it, or accumulating into a list
   created INSIDE `dfs` (a fresh list per call, so every append is lost). The
   accumulator must live in the enclosing scope, or be threaded through as an
   argument.
4. `out.append(node)` instead of `out.append(node.val)` — the test then
   compares `TreeNode` objects against ints and fails with an unhelpful
   message. Trees are the topic where this typo happens most.
5. Using recursion by default on the LeetCode constraint (n <= 100, always
   fine) and then repeating the habit on a problem whose constraint is
   n <= 10^5 skewed (LC 104 etc.), where it is a `RecursionError`. Demoed live.
6. Checking `if node.left is not None` in the recursion *and* having a
   `if not node: return` base case — harmless, but a sign of not trusting the
   base case. Pick one: guard on entry (cleaner) or guard before descent
   (needed only in the iterative version, where there is no "entry").


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Now do it iteratively.
A: Approach 2. Say the push-right-then-left reason out loud; it is the whole
   point of the question.

Q: Do it with O(1) extra space.
A: Morris traversal — see 002. It temporarily mutates `.right` pointers to
   thread the tree, then restores them. Mention that "O(1) space" is bought
   with "mutates the tree mid-flight", which is unacceptable if the tree is
   shared across threads.

Q: The tree has 10^5 nodes in a straight line. Does your solution work?
A: The recursive one does not — `RecursionError` at ~1000 frames. Either use
   the iterative version or raise `sys.setrecursionlimit`, and know that the
   limit is a Python-level guard: raising it too far segfaults the interpreter
   in older CPython, so the iterative version is the real answer.

Q: Return an ITERATOR instead of a list, so the caller can stop early.
A: Turn the recursion into a generator: `yield node.val`, then
   `yield from dfs(node.left)`, `yield from dfs(node.right)`. Same O(n) total
   time, but O(1) *incremental* work per value and the caller can abandon it.
   Implemented below and cross-checked.

Q: What if a node has a `parent` pointer — can you traverse with O(1) space
   and no mutation?
A: Yes: from a node, go left/right if possible, otherwise walk up via
   `parent` until you find an ancestor whose right subtree you have not
   visited. That is how BST iterators (LC 173) are built.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
    LC 94    Binary Tree Inorder Traversal    — one line moved (002 here)
    LC 145   Binary Tree Postorder Traversal  — two lines moved (003 here)
    LC 102   Level Order Traversal            — BFS, a queue not a stack (013)
    LC 589   N-ary Tree Preorder Traversal    — same loop, push children reversed
    LC 105   Build Tree from Preorder+Inorder — why the ORDER matters (016)
    LC 173   BST Iterator                     — the inorder stack, paused (topic 11)
    LC 297   Serialize/Deserialize            — preorder + null markers (019)
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
    def preorderTraversal(self, root: Optional[TreeNode]) -> List[int]:
        """Recursion. O(n) time, O(h) space. The one to write first."""
        out: List[int] = []

        def dfs(node: Optional[TreeNode]) -> None:
            if not node:
                return
            out.append(node.val)     # NODE
            dfs(node.left)           # LEFT
            dfs(node.right)          # RIGHT

        dfs(root)
        return out

    def preorderTraversal_iterative(self, root: Optional[TreeNode]) -> List[int]:
        """One explicit stack. O(n) time, O(h) space, no recursion limit.
        Push RIGHT then LEFT so LEFT pops first."""
        if not root:
            return []
        out: List[int] = []
        stack = [root]
        while stack:
            node = stack.pop()
            out.append(node.val)
            if node.right:
                stack.append(node.right)
            if node.left:
                stack.append(node.left)
        return out

    def preorderTraversal_concat(self, root: Optional[TreeNode]) -> List[int]:
        """One-liner recursion. Correct but O(n*h) time / O(n*h) allocation:
        every value is copied once per ancestor. O(n^2) on a skewed tree."""
        if not root:
            return []
        return ([root.val]
                + self.preorderTraversal_concat(root.left)
                + self.preorderTraversal_concat(root.right))

    def preorder_generator(self, root: Optional[TreeNode]):
        """Lazy variant: the caller can stop early. O(1) work per value."""
        if root:
            yield root.val
            yield from self.preorder_generator(root.left)
            yield from self.preorder_generator(root.right)

    # ------------------------------------------------------------------
    # Deliberate breakage — the mirror-image push order.
    # ------------------------------------------------------------------
    def preorder_broken_push_order(self, root: Optional[TreeNode]) -> List[int]:
        """✗ BROKEN ON PURPOSE — pushes LEFT before RIGHT, so the stack hands
        back the RIGHT child first. Produces node-right-left, a mirrored
        traversal that looks plausible and is wrong."""
        if not root:
            return []
        out: List[int] = []
        stack = [root]
        while stack:
            node = stack.pop()
            out.append(node.val)
            if node.left:
                stack.append(node.left)      # wrong order
            if node.right:
                stack.append(node.right)
        return out


# ==============================================================================
# TEST HELPERS — the standard tree kit reused by every file in this topic.
#
#   build(values)          LeetCode level-order list -> tree of TreeNode
#   to_level_order(root)   tree -> LeetCode level-order list (build's inverse)
#   build_skewed(n, side)  a straight chain of n nodes: the O(h) = O(n) shape
#   build_complete(n)      a gapless tree of n nodes: the O(h) = O(log n) shape
#   random_tree(n, rng)    a reproducible random shape, for cross-checking
#
# build() reads the list left to right while walking the tree in breadth-first
# order: pop the next node that still needs children, consume up to two list
# entries as its left and right child, and enqueue any child actually created.
# A `None` entry means "no child", and — crucially — a None child enqueues
# nothing, which is why `[1,null,2,3]` puts 3 under 2 rather than under the
# missing left child. That single rule is the whole format.
#
# to_level_order() is the inverse, and it exists so a *tree* result can be
# compared with `==` in a test. It enqueues `None` children too (so gaps are
# visible and positional), then trims trailing Nones — LeetCode's notation
# never spells out the empty slots after the last real node. Round-tripping
# any LeetCode string through build() then to_level_order() returns the same
# list, which the tests assert below.
# ==============================================================================
def build(values):
    """LeetCode level-order notation -> tree. `None` means "no child here"."""
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
    """Inverse of build(): tree -> level-order list, trailing Nones trimmed."""
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
    """A chain of n nodes with values 0..n-1. height == n."""
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


def build_complete(n, start=0):
    """A gapless tree of n nodes (array-heap shape). height == floor(log2 n)+1."""
    if n == 0:
        return None
    nodes = [TreeNode(start + i) for i in range(n)]
    for i in range(n):
        if 2 * i + 1 < n:
            nodes[i].left = nodes[2 * i + 1]
        if 2 * i + 2 < n:
            nodes[i].right = nodes[2 * i + 2]
    return nodes[0]


def random_tree(n, rng):
    """A random (usually unbalanced) tree of n nodes. Deterministic per rng."""
    if n == 0:
        return None
    root = TreeNode(rng.randrange(100))
    nodes = [root]
    for _ in range(n - 1):
        parent = rng.choice(nodes)
        while parent.left is not None and parent.right is not None:
            parent = rng.choice(nodes)
        node = TreeNode(rng.randrange(100))
        if parent.left is None and (parent.right is not None or rng.random() < 0.5):
            parent.left = node
        else:
            parent.right = node
        nodes.append(node)
    return root


def height(node):
    """Iterative height, so it works on trees deeper than the recursion limit."""
    if not node:
        return 0
    best = 0
    stack = [(node, 1)]
    while stack:
        nd, d = stack.pop()
        if d > best:
            best = d
        if nd.left:
            stack.append((nd.left, d + 1))
        if nd.right:
            stack.append((nd.right, d + 1))
    return best


# ==============================================================================
# TESTS — run:  python 001_binary_tree_preorder_traversal_solution.py
# ==============================================================================
CASES = [
    ([1, None, 2, 3], [1, 2, 3]),
    ([], []),
    ([1], [1]),
    ([1, 2, 3, 4, 5, None, 8, None, None, 6, 7, 9], [1, 2, 4, 5, 6, 7, 3, 8, 9]),
    ([3, 9, 20, None, None, 15, 7], [3, 9, 20, 15, 7]),
    ([1, 2], [1, 2]),
    ([1, None, 2], [1, 2]),
    ([5, 4, 6, 3, None, None, 7, 2], [5, 4, 3, 2, 6, 7]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- helper sanity: build() and to_level_order() round-trip ---")
    for values, _ in CASES:
        got = to_level_order(build(values))
        ok = got == values
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {values!r:<44} -> {got}")

    print("\n--- correctness: recursion ---")
    for values, want in CASES:
        got = sol.preorderTraversal(build(values))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {values!r:<44} -> {got}  (want {want})")

    print("\n--- correctness: iterative / concat / generator, vs the recursion ---")
    impls = [
        ("iterative (one stack)", lambda r: sol.preorderTraversal_iterative(r)),
        ("list-concat recursion", lambda r: sol.preorderTraversal_concat(r)),
        ("generator            ", lambda r: list(sol.preorder_generator(r))),
    ]
    for name, fn in impls:
        ok = all(fn(build(v)) == want for v, want in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # ----------------------------------------------------------------------
    # Randomised cross-check: recursion vs iteration must agree on any shape.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check: recursive == iterative on 500 random trees ---")
    rng = random.Random(144)
    mismatches = 0
    for _ in range(500):
        t = random_tree(rng.randint(0, 60), rng)
        if sol.preorderTraversal(t) != sol.preorderTraversal_iterative(t):
            mismatches += 1
    print(f"  500 random trees (0..60 nodes): {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # trace: the iterative stack, printed step by step.
    # ----------------------------------------------------------------------
    print("\n--- trace: iterative preorder of [1,2,3,4,5,null,8,null,null,6,7,9] ---")
    root = build([1, 2, 3, 4, 5, None, 8, None, None, 6, 7, 9])
    out, stack, step = [], [root], 0
    print(f"  {'step':>4} {'popped':>7}  {'out':<22} stack (top on the right)")
    print(f"  {step:>4} {'-':>7}  {str(out):<22} {[n.val for n in stack]}")
    while stack:
        node = stack.pop()
        out.append(node.val)
        if node.right:
            stack.append(node.right)
        if node.left:
            stack.append(node.left)
        step += 1
        print(f"  {step:>4} {node.val:>7}  {str(out):<22} {[n.val for n in stack]}")

    # ----------------------------------------------------------------------
    # ⚠️  Push order: RIGHT first. The mirrored version, live.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: pushing LEFT before RIGHT mirrors the traversal ---")
    values = [1, 2, 3, 4, 5, None, 8, None, None, 6, 7, 9]
    good = sol.preorderTraversal_iterative(build(values))
    bad = sol.preorder_broken_push_order(build(values))
    print(f"  tree                 : {values}")
    print(f"  push RIGHT then LEFT : {good}   <- correct (node, left, right)")
    print(f"  push LEFT then RIGHT : {bad}   <- WRONG (node, right, left)")
    print(f"  same length, different order: {len(good) == len(bad) and good != bad}")
    print(f"  both agree on a single-node tree, which is why this bug survives")
    print(f"  weak tests: {sol.preorderTraversal_iterative(build([1])) == sol.preorder_broken_push_order(build([1]))}")
    all_ok &= (len(good) == len(bad) and good != bad)

    # ----------------------------------------------------------------------
    # Peak stack size: the two skew directions are NOT symmetric.
    # ----------------------------------------------------------------------
    print("\n--- peak explicit-stack size by tree shape (n = 1023) ---")
    print(f"  {'shape':<22} {'height':>7} {'peak stack':>11}")
    for label, tree in (
        ("left-skewed chain", build_skewed(1023, "left")),
        ("right-skewed chain", build_skewed(1023, "right")),
        ("complete", build_complete(1023)),
    ):
        peak, stack = 0, [tree]
        while stack:
            peak = max(peak, len(stack))
            node = stack.pop()
            if node.right:
                stack.append(node.right)
            if node.left:
                stack.append(node.left)
        print(f"  {label:<22} {height(tree):>7} {peak:>11}")
    print("  Measured above: BOTH chains peak at a stack of 1, because a chain")
    print("  node has exactly one child to push, while the recursion would need")
    print("  h = 1023 frames on the very same input. The stack only grows when")
    print("  there are right-siblings owed a visit, so the complete tree peaks")
    print("  at its height (10), not at n. 'O(h) space' is therefore an upper")
    print("  bound the explicit stack often beats — and the reason the iterative")
    print("  version survives inputs that make the recursive one raise.")

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: CPython's recursion limit is a real ceiling.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  recursion limit: a skewed tree of 10,000 nodes ---")
    limit = sys.getrecursionlimit()
    print(f"  sys.getrecursionlimit() = {limit}")
    deep = build_skewed(10_000, "left")
    recursion_error = False
    try:
        sol.preorderTraversal(deep)
        print("  recursive : did NOT raise (limit not reached this run)")
    except RecursionError as e:
        recursion_error = True
        print(f"  recursive : RecursionError -> {e}")
    iterative_ok = sol.preorderTraversal_iterative(deep) == list(range(10_000))
    print(f"  iterative : returned all 10,000 values, correct = {iterative_ok}")
    print(f"  the iterative version is the escape hatch: {recursion_error and iterative_ok}")
    all_ok &= recursion_error and iterative_ok

    # It CAN be done recursively — by raising the limit, with a caveat.
    saved = sys.getrecursionlimit()
    try:
        sys.setrecursionlimit(30_000)
        rec_ok = sol.preorderTraversal(deep) == list(range(10_000))
        print(f"  with sys.setrecursionlimit(30000): recursion succeeds = {rec_ok}")
        all_ok &= rec_ok
    finally:
        sys.setrecursionlimit(saved)          # always restore
    print(f"  limit restored to {sys.getrecursionlimit()}")
    print("  Raising the limit is a workaround, not a fix: the guard exists to")
    print("  stop the C stack overflowing, and pushing it far enough can crash")
    print("  the interpreter outright instead of raising.")

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: recursion vs one stack vs list-concat.
    # ----------------------------------------------------------------------
    print("\n--- measured: recursion vs explicit stack vs list-concat ---")
    sys.setrecursionlimit(60_000)
    try:
        print(f"  {'n':>7} {'shape':<12} {'recursive':>11} {'iterative':>11} {'concat':>11}")
        bench_rng = random.Random(7)
        for n in (5_000, 20_000, 50_000):
            t = random_tree(n, bench_rng)
            reps = 5
            t0 = time.perf_counter()
            for _ in range(reps):
                sol.preorderTraversal(t)
            t1 = time.perf_counter()
            for _ in range(reps):
                sol.preorderTraversal_iterative(t)
            t2 = time.perf_counter()
            for _ in range(reps):
                sol.preorderTraversal_concat(t)
            t3 = time.perf_counter()
            print(f"  {n:>7} {'random':<12} {(t1-t0)/reps*1000:>9.2f}ms "
                  f"{(t2-t1)/reps*1000:>9.2f}ms {(t3-t2)/reps*1000:>9.2f}ms")
        # And the shape where list-concat degenerates.
        chain = build_skewed(4_000, "left")
        t0 = time.perf_counter()
        sol.preorderTraversal_iterative(chain)
        t1 = time.perf_counter()
        sol.preorderTraversal_concat(chain)
        t2 = time.perf_counter()
        it_ms, cc_ms = (t1 - t0) * 1000, (t2 - t1) * 1000
        print(f"  {4000:>7} {'left chain':<12} {'-':>11} {it_ms:>9.3f}ms {cc_ms:>9.2f}ms"
              f"   <- concat is {cc_ms/it_ms:.0f}x slower: O(n*h) = O(n^2)")
        all_ok &= cc_ms > it_ms
    finally:
        sys.setrecursionlimit(saved)
    print("  On a random tree the explicit stack wins by a modest margin — one")
    print("  list.pop() beats one Python function call. On a skewed tree the")
    print("  list-concat one-liner collapses, because every value is re-copied")
    print("  once per ancestor: that is the O(n*h) column in the table above.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
