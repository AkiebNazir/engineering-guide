"""
================================================================================
SOLUTION · LeetCode 199 · Binary Tree Right Side View                  [Medium]
https://leetcode.com/problems/binary-tree-right-side-view/
================================================================================

THE CORE IDEA
--------------
The answer is a LEVEL property, not a POINTER property:

    right side view = [ the last node of each level, in left-to-right order ]

Two ways to say "last of the level", and both are worth being able to write:

    (a) BFS — problem 013's level-size loop, keeping only the final pop of
        each level:
            for i in range(len(q)):
                node = q.popleft()
                if i == len(level_size) - 1: out.append(node.val)
        O(n) time, O(w) space.

    (b) DFS, RIGHT CHILD FIRST, carrying depth — the FIRST node reached at
        any depth is that depth's rightmost node, because visiting right
        before left means every node to the right of the current one has
        already been visited:
            def go(node, depth):
                if node is None: return
                if depth == len(out): out.append(node.val)   # first arrival
                go(node.right, depth + 1)
                go(node.left,  depth + 1)
        O(n) time, O(h) space — better than BFS on a WIDE tree, worse on a
        DEEP one (topic guide Part 5).


================================================================================
⚠️ THE TRAP — "rightmost path" IS NOT "right side view"
================================================================================
The intuitive-but-wrong algorithm is to walk `.right` from the root:

    node = root
    while node:
        out.append(node.val)
        node = node.right          # ✗ WRONG

It passes the LeetCode example and fails the moment the tree is uneven:

            1
          ┌─┴─┐
          2   3
        ┌─┘
        4

    correct right side view : [1, 3, 4]
    follow-.right path      : [1, 3]        <- 4 is missing

Node 4 is a LEFT child of a LEFT child, and it is still visible from the
right, because it is the ONLY node on level 2 — there is nothing to its
right to hide behind. "Visible from the right" means "nothing on my level is
further right", which has nothing to do with which pointer you arrived
through.

The failure is not even bounded: a tree whose right subtree is a single node
and whose left subtree is a long chain misses EVERY level below the first.
The demo below builds exactly that and prints the two answers side by side.

The mirror-image trap: "follow `.left` for the LEFT side view" fails the
same way, symmetrically.


================================================================================
MULTIPLE APPROACHES
================================================================================
0. BRUTE FORCE — full level order (013), then `[level[-1] for level in
   levels]`. O(n) time, O(n) space. Not really "brute force" so much as
   "solve the parent problem and project": completely correct, and the
   fastest thing to say out loud in an interview. It only costs extra
   MEMORY (it materialises every level, O(n), instead of O(w) or O(h)).
   Coded below as `rightSideView_via_levels`.

1. BFS, KEEP LAST OF EACH LEVEL ✅ — the answer. O(n) time, O(w) space.
   Never materialises a level list; just records the pop where
   `i == width - 1`.

2. DFS, RIGHT-FIRST, FIRST-ARRIVAL-WINS ✅ — the answer when the tree is
   wide and shallow, or when the interviewer asks for O(h) space. O(n) time,
   O(h) space.

3. DFS, LEFT-FIRST, LAST-WRITE-WINS — same recursion, children visited
   left-then-right, and instead of "record only on first arrival" you
   OVERWRITE the entry for that depth every time:
        if depth == len(out): out.append(node.val)
        else:                 out[depth] = node.val
   Correct, because the last node written at each depth is the rightmost
   one. Slightly more code and one more mutation per node; useful to know
   because it converts to the LEFT side view by just deleting the `else`.

4. FOLLOW `.right` FROM THE ROOT — ✗ wrong, see the trap above. Coded and
   run below precisely so the wrong answer is visible.


================================================================================
STEP BY STEP TRACE — root = [1,2,3,null,5,null,4]
================================================================================
            1
          ┌─┴─┐
          2   3
           └┐   └┐
            5    4

  BFS, level-size loop:

    pass  queue at top   width  i=0..width-1 pops   recorded (i == width-1)
    ----  -------------  -----  ------------------  ----------------------
    1     [1]            1      1                   1
    2     [2, 3]         2      2, 3                3
    3     [5, 4]         2      5, 4                4
                                                     -> [1, 3, 4]

  DFS, right child first, first arrival at each depth wins:

    call                       depth  len(out)  first arrival?  out
    -------------------------  -----  --------  --------------  ---------
    go(1, 0)                   0      0         YES             [1]
      go(3, 1)     (RIGHT!)    1      1         YES             [1,3]
        go(4, 2)               2      2         YES             [1,3,4]
          go(None,3) x2                          -               [1,3,4]
        go(None, 2)                              -               [1,3,4]
      go(2, 1)     (left)      1      3         no (3 already)   [1,3,4]
        go(None, 2)                              -               [1,3,4]
        go(5, 2)               2      3         no (4 already)   [1,3,4]
                                                     -> [1, 3, 4]

  Note the DFS visits 4 BEFORE 5 and 3 BEFORE 2 — that ordering is the whole
  mechanism. Swap the two recursive calls and you compute the LEFT side view.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time   Space (aux)  Mutates input?  Note
    --------------------------------  -----  -----------  --------------  ----------------------
    Full level order, then level[-1]  O(n)   O(n)         no              materialises every level
    BFS, last of each level ✅        O(n)   O(w)         no              the answer
    DFS right-first, first wins ✅    O(n)   O(h)         no              O(h) space; the answer
                                                                            when h << w
    DFS left-first, last write wins   O(n)   O(h)         no              one write per node
    Follow .right from the root       O(h)   O(1)         no              ✗ WRONG (see the trap)

    n = nodes, h = height, w = widest level. Output is O(h) values (one per
    level) in every case and is not counted as auxiliary.

    WHICH SPACE BOUND IS BETTER DEPENDS ON THE SHAPE, and the two are exact
    opposites (topic guide Part 5):
        perfect tree, n = 10^6   ->  h ~ 20,     w ~ 500000  ->  DFS wins big
        single chain, n = 10^6   ->  h = 10^6,   w = 1       ->  BFS wins big
                                     (and DFS does not merely use more
                                      memory — it hits Python's recursion
                                      limit and raises)


================================================================================
EDGE CASES
================================================================================
    root = None            -> []. First line of both versions.
    single node             -> [1]: one level, one visible node.
    right-only chain        -> every node visible; this is the ONE shape where
                              the broken "follow .right" version is correct,
                              which is exactly why that bug survives casual
                              testing.
    left-only chain         -> every node visible too (each is alone on its
                              level). "Follow .right" returns just [root] —
                              maximum divergence.
    uneven: deep left, shallow right -> the counterexample above; the whole
                              point of the problem.
    a node with only a LEFT child, on a level where the right subtree ended
                            -> that left child IS the view for its level.
    duplicate / negative / zero values -> irrelevant; `if node.left is not
                              None` tests identity, never truthiness, so
                              `TreeNode(0)` is a real node.


================================================================================
COMMON MISTAKES
================================================================================
1. Following `.right` from the root (the trap above). Passes LC 199's own
   Example 1, fails `[1,2,3,4]`. Printed live below.

2. In the DFS version, recursing LEFT first while still recording only on
   FIRST arrival. That computes the LEFT side view and silently returns a
   plausible-looking wrong answer. The pairing is fixed: right-first goes
   with first-arrival-wins; left-first goes with last-write-wins.

3. In the BFS version, recording `q[-1]` (the back of the queue) instead of
   the last POP of the level. Once children have been enqueued, `q[-1]` is
   a node of the NEXT level. Recording on `i == width - 1` reads the level
   whose width was snapshotted.

4. Recomputing `len(q)` as the loop bound inside the level loop, so the
   "width" grows as children are appended — the same level-collapse bug as
   013's mistake 2.

5. Taking `level[0]` instead of `level[-1]` (that is the left side view), or
   building the level then forgetting the tree may be empty and indexing
   `[-1]` into `[]`.

6. Assuming the answer's length equals the number of RIGHT edges from the
   root. It equals the HEIGHT — one entry per level, always.

7. Using a mutable default (`def go(node, depth, out=[])`) to accumulate.
   The default is evaluated once per execution of the `def` STATEMENT, and
   it is stored on the function object in `go.__defaults__`. The subtlety
   worth knowing, and demonstrated live below:
     · if `go` is NESTED inside `rightSideView`, the `def` re-executes on
       every call, so each call gets a fresh list and the bug HIDES;
     · the moment you hoist `go` to module level or make it a method — a
       routine refactor — the `def` runs once at import and the list is
       shared by every call, so the second call returns the first call's
       answer.
   That is what makes it dangerous: it is latent until an unrelated tidy-up
   activates it. Pass the accumulator explicitly or close over it. Topic
   guide Part 4.

8. Reaching for `nonlocal out` and then `out = out + [x]` inside the
   recursion. Rebinding a closed-over name needs `nonlocal`; MUTATING it
   (`out.append(x)`) does not. Appending is what you want here — see the
   topic guide Part 4 note on why bottom-up aggregates need `nonlocal` and
   list accumulators do not.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the LEFT side view instead.
A: BFS: record the FIRST pop of each level (`i == 0`). DFS: recurse LEFT
   child first, keep first-arrival-wins. One character of change in each.

Q: Do it in O(h) space instead of O(w).
A: Approach 2, the right-first DFS. State the trade explicitly: O(h) space
   but it recurses, so a 10^5-deep chain needs `sys.setrecursionlimit` or an
   explicit stack.

Q: Do it iteratively but still in O(h) space.
A: Right-first DFS with an explicit stack of `(node, depth)` pairs. The
   stack holds at most O(h) entries if you push the left child before the
   right so the right is popped first.

Q: Both views at once — leftmost and rightmost per level.
A: One BFS pass, record `i == 0` and `i == width - 1`. When width is 1 they
   are the same node — decide up front whether it appears once or twice.

Q: What is the "boundary" of the tree (LC 545)?
A: Strictly harder and NOT this: the boundary is left boundary + leaves +
   reversed right boundary, where "boundary" there really IS a root-down
   path, plus every leaf. Worth naming because candidates conflate the two.

Q: Which nodes are visible from the TOP (LC 314 vertical order / "top
   view")?
A: A different projection: group nodes by horizontal COLUMN
   (`col - 1` left, `col + 1` right) instead of by level, and take the
   shallowest node per column. Same "BFS while carrying a coordinate"
   machinery, different coordinate.

Q: The tree is an N-ary tree.
A: BFS version is unchanged (`level[-1]` still means "last child visited on
   this level"); the DFS version must iterate `reversed(node.children)` to
   preserve right-first order.


================================================================================
RELATED PROBLEMS — the pattern family
================================================================================
    LC 102   Binary Tree Level Order Traversal   — the parent problem (013 here)
    LC 107   Level Order Traversal II             — same loop, reversed output
    LC 103   Zigzag Level Order                   — same loop, alternate levels
    LC 637   Average of Levels                    — same loop, mean per level
    LC 515   Find Largest Value in Each Tree Row   — same loop, max per level
    LC 1161  Maximum Level Sum                    — same loop, argmax of sums
    LC 662   Maximum Width of Binary Tree          — level + positional index
    LC 314   Binary Tree Vertical Order Traversal   — group by COLUMN, not level
    LC 987   Vertical Order Traversal II            — 314 with a tie-break rule
    LC 545   Boundary of Binary Tree               — genuinely path-based, unlike
                                                       this problem
    LC 116   Populating Next Right Pointers        — the "who is to my right"
                                                       question, answered by wiring
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


# ------------------------------------------------------------------------
# ✗ MODULE-LEVEL helper with a mutable default — the `def` runs ONCE, at
# import time, so `out=[]` is shared by every call for the life of the
# process. Used by the mistake-7 demo below.
# ------------------------------------------------------------------------
def _rsv_go(node, depth, out=[]):
    if node is None:
        return out
    if depth == len(out):
        out.append(node.val)
    _rsv_go(node.right, depth + 1, out)
    _rsv_go(node.left, depth + 1, out)
    return out


def rsv_module_level_default(root):
    return _rsv_go(root, 0)


class Solution:
    def rightSideView(self, root: Optional[TreeNode]) -> List[int]:
        """BFS keeping the LAST pop of each level. O(n) time, O(w) space.
        See THE CORE IDEA (a)."""
        if root is None:
            return []
        out: List[int] = []
        q = deque([root])
        while q:
            width = len(q)                     # snapshot: this level's width
            for i in range(width):
                node = q.popleft()
                if i == width - 1:              # the rightmost node of this level
                    out.append(node.val)
                if node.left is not None:
                    q.append(node.left)
                if node.right is not None:
                    q.append(node.right)
        return out

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def rightSideView_dfs_right_first(self, root: Optional[TreeNode]) -> List[int]:
        """DFS, RIGHT child first, first arrival at each depth wins.
        O(n) time, O(h) space. See THE CORE IDEA (b)."""
        out: List[int] = []

        def go(node: Optional[TreeNode], depth: int) -> None:
            if node is None:
                return
            if depth == len(out):               # first node ever seen at this depth
                out.append(node.val)
            go(node.right, depth + 1)           # RIGHT first — this is the mechanism
            go(node.left, depth + 1)

        go(root, 0)
        return out

    def rightSideView_dfs_left_first(self, root: Optional[TreeNode]) -> List[int]:
        """DFS, LEFT child first, last write at each depth wins. Correct for
        the opposite reason. Delete the `else` branch and it becomes the
        LEFT side view."""
        out: List[int] = []

        def go(node: Optional[TreeNode], depth: int) -> None:
            if node is None:
                return
            if depth == len(out):
                out.append(node.val)
            else:
                out[depth] = node.val           # overwrite: the last one wins
            go(node.left, depth + 1)
            go(node.right, depth + 1)

        go(root, 0)
        return out

    def rightSideView_iterative_dfs(self, root: Optional[TreeNode]) -> List[int]:
        """Right-first DFS with an EXPLICIT stack of (node, depth). O(n)
        time, O(h) space, and immune to the recursion limit."""
        if root is None:
            return []
        out: List[int] = []
        stack = [(root, 0)]
        while stack:
            node, depth = stack.pop()
            if depth == len(out):
                out.append(node.val)
            # push LEFT first so RIGHT is popped first
            if node.left is not None:
                stack.append((node.left, depth + 1))
            if node.right is not None:
                stack.append((node.right, depth + 1))
        return out

    def rightSideView_via_levels(self, root: Optional[TreeNode]) -> List[int]:
        """Approach 0: solve 013 in full, then project. O(n) time, O(n)
        space — correct, just memory-hungry."""
        if root is None:
            return []
        levels: List[List[int]] = []
        q = deque([root])
        while q:
            level: List[int] = []
            for _ in range(len(q)):
                node = q.popleft()
                level.append(node.val)
                if node.left is not None:
                    q.append(node.left)
                if node.right is not None:
                    q.append(node.right)
            levels.append(level)
        return [level[-1] for level in levels]

    def leftSideView(self, root: Optional[TreeNode]) -> List[int]:
        """The mirror problem, for contrast: FIRST pop of each level."""
        if root is None:
            return []
        out: List[int] = []
        q = deque([root])
        while q:
            width = len(q)
            for i in range(width):
                node = q.popleft()
                if i == 0:                       # the leftmost node of this level
                    out.append(node.val)
                if node.left is not None:
                    q.append(node.left)
                if node.right is not None:
                    q.append(node.right)
        return out

    # ------------------------------------------------------------------
    # Deliberate breakage — the "rightmost path" misreading.
    # ------------------------------------------------------------------
    def rightSideView_broken_follow_right(self, root: Optional[TreeNode]) -> List[int]:
        """✗ BROKEN ON PURPOSE — walks `.right` from the root. Correct only
        when every level's rightmost node happens to be reachable by right
        pointers alone."""
        out: List[int] = []
        node = root
        while node is not None:
            out.append(node.val)
            node = node.right
        return out

    def rightSideView_broken_queue_back(self, root: Optional[TreeNode]) -> List[int]:
        """✗ BROKEN ON PURPOSE — records `q[-1]` (the BACK of the queue)
        after enqueueing children, which is a node of the NEXT level."""
        if root is None:
            return []
        out: List[int] = []
        q = deque([root])
        while q:
            for _ in range(len(q)):
                node = q.popleft()
                if node.left is not None:
                    q.append(node.left)
                if node.right is not None:
                    q.append(node.right)
            if q:
                out.append(q[-1].val)           # back of the queue != last of level
            else:
                out.append(node.val)
        return out


# ==============================================================================
# TEST HELPERS — level-order (de)serialisation, LeetCode's array format
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
    """Root -> level-order list with `None`s, trailing `None`s trimmed."""
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


def levels_of(root: Optional[TreeNode]) -> List[List[int]]:
    """Reference level grouping, used as the oracle for `level[-1]`."""
    if root is None:
        return []
    out: List[List[int]] = []
    q = deque([root])
    while q:
        level = []
        for _ in range(len(q)):
            node = q.popleft()
            level.append(node.val)
            if node.left is not None:
                q.append(node.left)
            if node.right is not None:
                q.append(node.right)
        out.append(level)
    return out


def left_spine_with_right_stub(depth: int) -> Optional[TreeNode]:
    """Root with a single right child, and a long LEFT chain: the shape that
    makes `follow .right` miss every level below the first."""
    root = TreeNode(0)
    root.right = TreeNode(-1)
    cur = root
    for i in range(1, depth):
        cur.left = TreeNode(i)
        cur = cur.left
    return root


# ==============================================================================
# TESTS — run:  python 014_binary_tree_right_side_view_solution.py
# ==============================================================================
CASES = [
    ([1, 2, 3, None, 5, None, 4], [1, 3, 4]),
    ([1, 2, 3, 4], [1, 3, 4]),
    ([1, None, 3], [1, 3]),
    ([], []),
    ([1], [1]),
    ([1, 2], [1, 2]),
    ([1, 2, 3, 4, None, None, None, 5], [1, 3, 4, 5]),
    ([1, 2, 3, 4, 5, 6, 7], [1, 3, 7]),
    ([0, 0, None, 0], [0, 0, 0]),
    ([1, 2, None, 3, None, 4, None], [1, 2, 3, 4]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: five working implementations agree ---")
    impls = [
        ("BFS last-of-level    ", sol.rightSideView),
        ("DFS right-first      ", sol.rightSideView_dfs_right_first),
        ("DFS left-first       ", sol.rightSideView_dfs_left_first),
        ("DFS explicit stack   ", sol.rightSideView_iterative_dfs),
        ("full levels, [-1]    ", sol.rightSideView_via_levels),
    ]
    for name, fn in impls:
        ok = all(fn(build(vals)) == expected for vals, expected in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- per-case output, with the level grouping it comes from ---")
    for vals, expected in CASES:
        root = build(vals)
        got = sol.rightSideView(root)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {str(vals):<34} -> {str(got):<16} "
              f"levels={levels_of(root)}")

    print("\n--- cross-check: answer == [level[-1] for level in levels] ---")
    mismatches = 0
    for vals, _ in CASES:
        root = build(vals)
        if sol.rightSideView(root) != [lvl[-1] for lvl in levels_of(root)]:
            mismatches += 1
    all_ok &= (mismatches == 0)
    print(f"  {len(CASES)} cases, {mismatches} mismatches against the level oracle")

    # ----------------------------------------------------------------------
    # ⚠️ THE TRAP: "rightmost path" != "right side view".
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  follow-.right vs the real right side view ---")
    print(f"  {'tree':<38} {'correct':<18} {'follow .right':<16} same?")
    trap_seen = False
    for vals in ([1, 2, 3, None, 5, None, 4],
                 [1, 2, 3, 4],
                 [1, 2, 3, 4, None, None, None, 5],
                 [1, None, 2, None, 3],
                 [1, 2, None, 3, None, 4, None]):
        root = build(vals)
        good = sol.rightSideView(root)
        bad = sol.rightSideView_broken_follow_right(root)
        same = good == bad
        trap_seen |= not same
        print(f"  {str(vals):<38} {str(good):<18} {str(bad):<16} {same}")
    all_ok &= trap_seen
    print("  Row 1 (LeetCode's own Example 1) AGREES — which is exactly why this")
    print("  bug ships. Rows 2, 3 and 5 diverge. Row 4 (right-only chain) is the")
    print("  one shape where following .right is genuinely correct.")

    print("\n--- how bad does it get? deep LEFT chain + a single right child ---")
    print(f"  {'chain depth':>11} {'correct len':>12} {'follow .right':>15} {'nodes missed':>13}")
    for depth in (2, 5, 10, 50, 200):
        root = left_spine_with_right_stub(depth)
        good = sol.rightSideView(root)
        bad = sol.rightSideView_broken_follow_right(root)
        print(f"  {depth:>11} {len(good):>12} {str(bad):>15} {len(good) - len(bad):>13}")
    root = left_spine_with_right_stub(5)
    good = sol.rightSideView(root)
    bad = sol.rightSideView_broken_follow_right(root)
    print(f"  depth 5 in full: correct={good}  follow-.right={bad}")
    print("  The error is UNBOUNDED — it grows with the height of the tree, so")
    print("  no amount of small-case testing puts a ceiling on it.")

    print("\n--- ⚠️  recording q[-1] (back of queue) instead of the last POP ---")
    for vals in ([1, 2, 3, None, 5, None, 4], [1, 2, 3, 4, 5, 6, 7]):
        root = build(vals)
        good = sol.rightSideView(root)
        bad = sol.rightSideView_broken_queue_back(root)
        print(f"  {str(vals):<32} correct={str(good):<14} q[-1] version={bad}")
    bad_seen = (sol.rightSideView_broken_queue_back(build([1, 2, 3, 4, 5, 6, 7]))
                != sol.rightSideView(build([1, 2, 3, 4, 5, 6, 7])))
    all_ok &= bad_seen
    print("  Once children are enqueued, q[-1] belongs to the NEXT level, so the")
    print("  view is shifted one level down and the last level is duplicated.")

    # ----------------------------------------------------------------------
    # right-first vs left-first: the pairing is fixed.
    # ----------------------------------------------------------------------
    print("\n--- DFS: right-first + first-arrival vs left-first + first-arrival ---")

    def dfs_left_first_first_arrival(root):
        """✗ the mismatched pairing — this is the LEFT side view."""
        out = []

        def go(node, depth):
            if node is None:
                return
            if depth == len(out):
                out.append(node.val)
            go(node.left, depth + 1)
            go(node.right, depth + 1)

        go(root, 0)
        return out

    print(f"  {'tree':<34} {'right-first':<14} {'left-first':<14} {'leftSideView':<14}")
    pairing_ok = True
    for vals in ([1, 2, 3, None, 5, None, 4], [1, 2, 3, 4, 5, 6, 7], [1, 2, 3, 4]):
        root = build(vals)
        rf = sol.rightSideView_dfs_right_first(root)
        lf = dfs_left_first_first_arrival(root)
        lsv = sol.leftSideView(root)
        pairing_ok &= (lf == lsv)
        print(f"  {str(vals):<34} {str(rf):<14} {str(lf):<14} {str(lsv):<14}")
    all_ok &= pairing_ok
    print("  Swapping the two recursive calls without also swapping the record")
    print("  rule silently computes the OTHER problem. left-first + "
          "first-arrival")
    print(f"  == leftSideView on every case above: {pairing_ok}")

    # ----------------------------------------------------------------------
    # Mutable default argument, demonstrated (mistake 7).
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  mutable default argument as the accumulator (mistake 7) ---")
    print("  (a) the helper NESTED inside the entry point — the trap does NOT fire:")

    def rsv_nested_default(root):
        def go(node, depth, out=[]):            # a NEW default list per outer call
            if node is None:
                return out
            if depth == len(out):
                out.append(node.val)
            go(node.right, depth + 1, out)
            go(node.left, depth + 1, out)
            return out
        return go(root, 0)

    a1 = rsv_nested_default(build([1, 2, 3, None, 5, None, 4]))
    a2 = rsv_nested_default(build([9, 8, 7]))
    print(f"      first  call -> {a1}")
    print(f"      second call -> {a2}   (want [9, 7])  clean: {a2 == [9, 7]}")
    all_ok &= (a2 == [9, 7])
    print("      Why: `def go(...)` RE-EXECUTES on every call to the outer")
    print("      function, and the default is evaluated at DEF time — so each")
    print("      outer call gets its own fresh list. This is why the bug hides.")

    print("  (b) the SAME helper hoisted to module level — the trap fires:")
    b1 = rsv_module_level_default(build([1, 2, 3, None, 5, None, 4]))
    b2 = rsv_module_level_default(build([9, 8, 7]))
    print(f"      first  call -> {b1}")
    print(f"      second call -> {b2}   (want [9, 7])")
    leaked = b2 != [9, 7]
    all_ok &= leaked
    print(f"      the second call inherited the first call's list: {leaked}")
    print(f"      _rsv_go.__defaults__ is now {_rsv_go.__defaults__} — the list")
    print("      lives on the FUNCTION OBJECT and outlives every call.")
    print("  Hoisting a nested helper to module level (or turning it into a")
    print("  method) is a routine, innocuous-looking refactor. That refactor is")
    print("  what converts (a) into (b). Never default an accumulator to `[]`;")
    print("  pass it explicitly, or close over it.")

    # ----------------------------------------------------------------------
    # BFS vs DFS: opposite space profiles, measured.
    # ----------------------------------------------------------------------
    print("\n--- BFS O(w) vs DFS O(h): opposite worst cases ---")
    print(f"  sys.getrecursionlimit() = {sys.getrecursionlimit()}")

    def left_spine(n):
        root = TreeNode(0)
        cur = root
        for i in range(1, n):
            cur.left = TreeNode(i)
            cur = cur.left
        return root

    spine = left_spine(3000)
    try:
        n_dfs = len(sol.rightSideView_dfs_right_first(spine))
        dfs_msg, dfs_died = f"ok, {n_dfs} levels", False
    except RecursionError as exc:
        dfs_msg, dfs_died = f"{type(exc).__name__}: {exc}", True
    all_ok &= dfs_died
    print(f"  3000-deep left chain, recursive DFS -> {dfs_msg}")
    print(f"  3000-deep left chain, BFS           -> ok, "
          f"{len(sol.rightSideView(spine))} levels")
    print(f"  3000-deep left chain, DFS+explicit stack -> ok, "
          f"{len(sol.rightSideView_iterative_dfs(spine))} levels")
    all_ok &= (len(sol.rightSideView(spine)) == 3000)
    all_ok &= (len(sol.rightSideView_iterative_dfs(spine)) == 3000)

    def perfect_tree(depth):
        if depth <= 0:
            return None
        root = TreeNode(0)
        frontier = [root]
        for _ in range(depth - 1):
            nxt = []
            for node in frontier:
                node.left = TreeNode(0)
                node.right = TreeNode(0)
                nxt.append(node.left)
                nxt.append(node.right)
            frontier = nxt
        return root

    print(f"\n  {'shape':<26} {'nodes':>8} {'peak BFS queue':>15} {'DFS depth':>10}")
    for label, root, n in (("perfect, depth 14", perfect_tree(14), 2 ** 14 - 1),
                           ("left chain, 3000", spine, 3000)):
        peak, q = 0, deque([root])
        while q:
            peak = max(peak, len(q))
            for _ in range(len(q)):
                node = q.popleft()
                if node.left is not None:
                    q.append(node.left)
                if node.right is not None:
                    q.append(node.right)
        depth = len(sol.rightSideView_iterative_dfs(root))
        print(f"  {label:<26} {n:>8} {peak:>15} {depth:>10}")
    print("  Neither approach dominates; pick by the shape you expect. The")
    print("  explicit-stack DFS is the only one that is O(h) space AND immune")
    print("  to the recursion limit.")

    # ----------------------------------------------------------------------
    # Randomised cross-check of every implementation against the oracle.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the level oracle (4000 random trees) ---")
    import random
    rng = random.Random(199)
    bad = 0
    for _ in range(4000):
        n = rng.randint(0, 14)
        vals = [rng.choice([rng.randint(-9, 9), None]) for _ in range(n)]
        if vals and vals[0] is None:
            vals[0] = 1
        root = build(vals)
        want = [lvl[-1] for lvl in levels_of(root)]
        for _name, fn in impls:
            if fn(root) != want:
                bad += 1
    all_ok &= (bad == 0)
    print(f"  4000 random trees x {len(impls)} implementations: {bad} mismatches")

    # ----------------------------------------------------------------------
    # Timing, for completeness.
    # ----------------------------------------------------------------------
    print("\n--- timing on a perfect tree (all correct approaches) ---")
    root = perfect_tree(16)
    print(f"  {'approach':<26} {'ms':>9}")
    for name, fn in [("BFS last-of-level", sol.rightSideView),
                     ("DFS right-first", sol.rightSideView_dfs_right_first),
                     ("DFS explicit stack", sol.rightSideView_iterative_dfs),
                     ("full levels then [-1]", sol.rightSideView_via_levels)]:
        t0 = time.perf_counter()
        fn(root)
        t1 = time.perf_counter()
        print(f"  {name:<26} {(t1 - t0) * 1000:>9.2f}")
    print("  All O(n); the differences are constant factors (recursion overhead")
    print("  vs deque ops vs building n-element level lists nobody reads).")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
