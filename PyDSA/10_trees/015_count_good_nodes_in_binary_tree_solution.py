"""
================================================================================
SOLUTION · LeetCode 1448 · Count Good Nodes in Binary Tree             [Medium]
https://leetcode.com/problems/count-good-nodes-in-binary-tree/
================================================================================

THE CORE IDEA
--------------
"Good" is a property of a node's ANCESTORS. Information cannot flow from an
ancestor to a descendant through a return value — return values go UP. It
flows through a PARAMETER. So: carry the max-so-far DOWN.

    def go(node, best):                # `best` = max value on the path ABOVE
        if node is None: return
        if node.val >= best:            # >= , not > : ties count
            count += 1
        best = max(best, node.val)      # extend the path with this node...
        go(node.left, best)             # ...and hand it to both children
        go(node.right, best)

    go(root, root.val)                  # root is trivially good

That is the whole solution. One integer of state, threaded downward. The
"answer" is a plain counter — because each node contributes independently,
there is nothing to aggregate on the way back up.

O(n) time, O(h) space (the call stack).

THE ONE-SENTENCE PATTERN TEST (topic guide Part 2):
    Does the answer at a node depend on what is ABOVE it?  -> top-down,
      pass state down as a parameter.
    Does it depend on what is BELOW it?                     -> bottom-up,
      return a value up (and record a global best in a `nonlocal`).
This problem is the purest example of the first; 018 (Max Path Sum) is the
purest example of the second.


================================================================================
WHY BOTTOM-UP CANNOT SOLVE THIS — a proof, not an opinion
================================================================================
A bottom-up (postorder) recursion computes `f(node)` from `f(node.left)` and
`f(node.right)` — that is, from the node's SUBTREE and nothing else. So if
bottom-up could decide goodness, then goodness would be a function of the
subtree alone. It is not:

    tree A:   1              tree B:   3
                └┐                       └┐
                 2  <- X                   2  <- X

X is the same node with the same (empty) subtree in both. In A the path max
above it is 1, so 2 >= 1 and X is GOOD. In B the path max is 3, so 2 < 3 and
X is NOT good. Same subtree, opposite answer => no function of the subtree
can compute it. The demo below constructs both trees and prints it.

This is not a claim that bottom-up is useless here — you can still count
bottom-up if you ALSO pass the ancestor max down as a parameter (approach 3
below returns the count upward instead of using a counter). The point is
narrower and more useful: the *ancestor* information has to come down as a
parameter no matter what you do with the result on the way back up.


================================================================================
MULTIPLE APPROACHES
================================================================================
0. BRUTE FORCE — for every node, walk the path from the root back down to it
   and take the max. O(n·h) time — O(n^2) on a skewed tree. Priced and CODED
   here (unusually), because it prices the reflex of re-deriving ancestor
   information instead of threading it down. Measured below on a LEFT CHAIN
   (h == n, the worst case): at n = 1000 the brute force runs ~1500x slower
   than the O(n) version on this machine, and the ratio keeps growing.

1. TOP-DOWN DFS, CARRY `best` AS A PARAMETER ✅ — the version above. O(n)
   time, O(h) space. The answer.

2. TOP-DOWN DFS, CARRY THE ANCESTOR PATH AS A LIST — `go(node, path)` with
   `path.append(node.val)` / `path.pop()` and `max(path)` at each node. This
   is the backtracking reflex bleeding into a tree problem, and it is
   strictly worse: `max(path)` is O(h) per node, so the whole thing is
   O(n·h) — asymptotically the same shape as brute force, for no benefit.
   Worth naming explicitly because it *feels* like the right move if you just
   came from topic 09. Measured below on a left chain: 6x slower at n = 250,
   growing to 91x at n = 4000 — while on a PERFECT tree it stays a flat ~2x,
   which is exactly why this bug survives testing. The single integer `best` is the entire optimisation, and the
   reason it works is that max is an *incremental* aggregate: you never need
   the path, only its running max. (Contrast: if the question were "no node
   on the path has value equal to X's value", a running max would not be
   enough and you WOULD need a set/counter carried down.)

3. TOP-DOWN DOWN + COUNT RETURNED UP — same `best` parameter, but instead of
   a counter, each call returns `(1 if good else 0) + go(left) + go(right)`.
   Identical O(n) / O(h), no mutable state at all, and it is the cleaner
   thing to write in an interview if you dislike `nonlocal`. Coded below.

4. ITERATIVE DFS WITH AN EXPLICIT STACK OF `(node, best)` — the same
   algorithm, no recursion, immune to Python's ~1000-frame recursion limit.
   Given n can be 10^5 here and a chain of 10^5 nodes is a legal input, this
   is not academic: the recursive version RAISES on it. Demonstrated below.

5. ITERATIVE BFS WITH A QUEUE OF `(node, best)` — also works. Level order is
   irrelevant to the answer (every node is independent), so BFS buys nothing
   over the stack except a different memory profile: O(w) instead of O(h).
   Coded for completeness, and it is the right pick if the tree is deep and
   narrow... which is precisely when the stack version is also fine. Mostly
   a reminder that "carry state down" is orthogonal to traversal order.


================================================================================
STEP BY STEP TRACE — root = [3,1,4,3,null,1,5]
================================================================================
            3
          ┌─┴──┐
          1    4
        ┌─┘  ┌─┴─┐
        3    1    5

    call                    best in  node.val  val >= best?  count  best out
    ----------------------  -------  --------  ------------  -----  --------
    go(3, best=3)           3        3         YES  (3>=3)   1      3
      go(1, best=3)         3        1         no   (1<3)    1      3
        go(3, best=3)       3        3         YES  (3>=3)   2      3
          go(None) x2       -        -         -             2      -
        go(None, best=3)    -        -         -             2      -
      go(4, best=3)         3        4         YES  (4>=3)   3      4
        go(1, best=4)       4        1         no   (1<4)    3      4
        go(5, best=4)       4        5         YES  (5>=4)   4      5
                                                              -> 4

    Read the `best out` column downward along any root-to-leaf path and you
    get a NON-DECREASING sequence. That monotonicity is why one integer
    suffices: once a big value is above you, nothing smaller can ever
    "un-shadow" a descendant.

    ⚠️ Compare `best` (max over the WHOLE path so far) with the parent's
    value alone. On this tree they happen to agree. On [5,1,null,3]:

            5           parent-only:  5 good; 1 < 5 not good;
        ┌───┘                         3 >= 1 (its parent) -> "good"  ✗
        1                             => 2
      ┌─┘             path-max:      5 good; 1 < 5 not; 3 < 5 not
      3                               => 1  ✓

    The parent-only version answers a different question ("is this node a
    local maximum relative to its parent"). Printed live below.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                             Time    Space (aux)  Mutates input?  Note
    -----------------------------------  ------  -----------  --------------  ------------------
    Brute: re-walk root->node per node   O(n·h)  O(h)         no              O(n^2) skewed
    Top-down, `best` parameter ✅        O(n)    O(h)         no              the answer
    Top-down, ancestor PATH + max(path)  O(n·h)  O(h)         no              backtracking reflex,
                                                                                same cost as brute
    Top-down, count returned upward      O(n)    O(h)         no              no mutable state
    Iterative DFS, stack of (node, best) O(n)    O(h)         no              recursion-limit proof
    Iterative BFS, queue of (node, best) O(n)    O(w)         no              order is irrelevant

    n = nodes, h = height, w = widest level. No approach mutates the tree;
    `best` is passed by value (an int is immutable, so `max(best, node.val)`
    rebinds a LOCAL name and the caller's `best` is untouched — see the
    topic guide Part 4 note on why this needs no explicit "undo" step).

    WHY THERE IS NO BACKTRACKING HERE (topic guide Part 3): in topic 09 you
    must `path.pop()` after recursing, because `path` is one shared mutable
    object. Here `best` is an int, rebinding is local, and each recursive
    call gets its own copy — so the "unchoose" step does not exist. If you
    carry a LIST down instead (approach 2), the undo comes back, which is a
    second reason not to.


================================================================================
EDGE CASES
================================================================================
    single node                 -> 1. The root is good by definition (empty
                                   path above it). Any answer of 0 for a
                                   one-node tree means `best` was initialised
                                   wrong.
    all values equal             -> EVERY node is good, because the test is
                                   `>=`. [2,2,2,2] -> 4. Using `>` returns 1.
    strictly increasing downward  -> every node good (n).
    strictly decreasing downward  -> only the root (1).
    ALL NEGATIVE values           -> initialising `best = 0` returns 0 good
                                   nodes instead of at least 1. Values are in
                                   [-10^4, 10^4]; use `root.val` or
                                   `float("-inf")`. Demonstrated below.
    a 10^5-node chain             -> legal per the constraints, and it kills
                                   the RECURSIVE version with RecursionError.
                                   Demonstrated below.
    root = None                   -> the constraints say n >= 1, so it cannot
                                   happen; still guard it (`return 0`) rather
                                   than reading `root.val` on `None`.


================================================================================
COMMON MISTAKES
================================================================================
1. `node.val > best` instead of `>=`. The problem says "no nodes with a
   value GREATER than X", so a node EQUAL to the running max is still good.
   On a tree of equal values this turns n into 1.

2. Comparing against the PARENT's value instead of the path maximum. Answers
   a different question, and agrees with the right answer on plenty of
   trees — including LeetCode's Example 1 — so it survives casual testing.
   Printed live below on [5,1,null,3].

3. Initialising `best = 0`. Values can be negative; a tree of all-negative
   values then reports 0 good nodes, when the root alone guarantees >= 1.
   Use `root.val` or `float("-inf")`.

4. Initialising `best = root.val` but then testing `node.val > best` at the
   root — the root fails its own test and the count is off by one.

5. Forgetting to EXTEND `best` when recursing — `go(node.left, best)`
   instead of `go(node.left, max(best, node.val))`. The current node's own
   value then never enters the path maximum, so a descendant is compared
   only against its *strict* ancestors minus its parent chain's peaks.
   Demonstrated live below.

   ⚠️ A NON-mistake worth knowing, because it looks like one: extending
   `best` BEFORE the comparison (`best = max(best, node.val)` and then
   `if node.val >= best`) is *equivalent*, not a bug. `val >= max(best, val)`
   is true exactly when `val >= best`, since `max(best, val)` is `val` in
   that case and `best` otherwise. The runtime demo below checks this on
   several trees and finds no divergence — it was written expecting a bug and
   the measurement said otherwise. Comparing first is still the clearer code
   (it says "am I good?" before "what do my children inherit?"), but do not
   claim it is a correctness fix.

6. Carrying the whole ancestor path and calling `max(path)` at every node —
   correct, O(n·h). Benchmarked below.

7. Recursing without a `None` guard as the FIRST statement, e.g. writing
   `if node.left: go(node.left, ...)` at every call site instead. Both work,
   but the guard-at-the-top form is one branch in one place, and it is what
   makes `go(root, ...)` safe on an empty tree. The topic guide (Part 4)
   makes this a house rule: every recursive tree function starts with a
   `None` check.

8. Using `nonlocal count` but writing `count = count + 1`... which is fine —
   whereas OMITTING the `nonlocal` and writing `count += 1` raises
   `UnboundLocalError`, because assigning to a name anywhere in a function
   makes it local to that function for the WHOLE function. Demonstrated
   below. (Approach 3, returning the count upward, sidesteps this entirely.)

9. Assuming O(h) stack space is safe. n <= 10^5 and a chain is legal, so
   h can be 10^5 against a default recursion limit of 1000. Either use the
   iterative version or raise the limit and say why.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Count nodes where every ancestor is STRICTLY smaller.
A: Change `>=` to `>`. One character — and worth noticing that this is the
   bug in mistake 1, which tells you the two questions differ by exactly
   that character.

Q: Return the good nodes themselves, not the count.
A: Append `node.val` (or the node) to a list instead of incrementing. Same
   traversal; the output becomes O(n).

Q: Count nodes whose value is greater than the MINIMUM on their root path.
A: Carry `min_so_far` down instead. The pattern is "carry an incremental
   aggregate of the ancestor path"; max and min are interchangeable.

Q: Count nodes whose value is greater than the AVERAGE of their root path.
A: Carry `(running_sum, depth)` down — two numbers instead of one. Still
   O(1) state per node, because sum and count are both incremental.

Q: Count nodes with no ancestor EQUAL to them.
A: A running max is not enough; carry a set (or a Counter) of ancestor
   values down, adding on the way in and removing on the way out — and NOW
   you genuinely do need the backtracking `undo`, because a set is mutable.
   This is the cleanest illustration of when the O(1)-state trick stops
   applying.

Q: n is 10^5 and the tree may be a chain. Will your solution work?
A: Not the recursive one — RecursionError at ~1000 frames. Give the explicit
   stack version, or `sys.setrecursionlimit(2 * 10**5)` while noting that
   the C stack can still be exhausted (a hard crash, not an exception).

Q: The tree is a BST. Faster?
A: Yes, and it becomes a different problem: in a BST every node in a right
   subtree exceeds the root, so "good" collapses to a structural condition
   (a node is good iff it is reached from the root by right-edges only, i.e.
   iff it is on the rightmost path... plus equal-value cases depending on
   the BST's duplicate policy). That is topic 11's territory: the ordering
   invariant, not the traversal, does the work.

Q: Same question, but "good" means no node with a greater value anywhere in
   the whole tree.
A: Then it is not a tree problem at all — one pass for the global max, a
   second to count equals. Worth saying out loud: it distinguishes an
   ancestor-relative property (this problem) from a global one.


================================================================================
RELATED PROBLEMS — the pattern family
================================================================================
  TOP-DOWN, carry state down as a parameter (this pattern):
    LC 1448  Count Good Nodes in Binary Tree     — this problem
    LC 112   Path Sum                            — carry the remaining target (011 here)
    LC 113   Path Sum II                         — 112 + carry the path list
    LC 129   Sum Root to Leaf Numbers            — carry the number built so far
    LC 1022  Sum of Root To Leaf Binary Numbers   — 129 in base 2
    LC 988   Smallest String Starting From Leaf   — carry the string down
    LC 1457  Pseudo-Palindromic Paths            — carry a parity BITMASK down
    LC 2265  Count Nodes Equal to Average of Subtree — needs BOTH directions
    LC 623   Add One Row to Tree                  — carry the depth down

  BOTTOM-UP, return a value up (the contrast — problems 005/009/010/018):
    LC 104   Maximum Depth                       — return the height up
    LC 110   Balanced Binary Tree                 — return height, flag imbalance
    LC 543   Diameter of Binary Tree              — return depth, keep a global best
    LC 124   Binary Tree Maximum Path Sum         — return gain, keep a global best
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
    def goodNodes(self, root: Optional[TreeNode]) -> int:
        """Top-down DFS carrying the path maximum down as a parameter.
        O(n) time, O(h) space. See THE CORE IDEA above."""
        if root is None:
            return 0
        count = 0

        def go(node: Optional[TreeNode], best: int) -> None:
            nonlocal count
            if node is None:
                return
            if node.val >= best:            # >= : ties are good
                count += 1
            best = max(best, node.val)      # compare FIRST, then extend
            go(node.left, best)
            go(node.right, best)

        go(root, root.val)                  # the root is trivially good
        return count

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def goodNodes_return_count(self, root: Optional[TreeNode]) -> int:
        """Approach 3: same `best` parameter, but the count is RETURNED
        upward. No mutable state, no `nonlocal`. O(n) time, O(h) space."""

        def go(node: Optional[TreeNode], best: int) -> int:
            if node is None:
                return 0
            here = 1 if node.val >= best else 0
            best = max(best, node.val)
            return here + go(node.left, best) + go(node.right, best)

        return 0 if root is None else go(root, root.val)

    def goodNodes_iterative_stack(self, root: Optional[TreeNode]) -> int:
        """Approach 4: explicit stack of (node, best). O(n) time, O(h)
        space, immune to the recursion limit."""
        if root is None:
            return 0
        count = 0
        stack = [(root, root.val)]
        while stack:
            node, best = stack.pop()
            if node.val >= best:
                count += 1
            nxt = best if best > node.val else node.val
            if node.left is not None:
                stack.append((node.left, nxt))
            if node.right is not None:
                stack.append((node.right, nxt))
        return count

    def goodNodes_iterative_bfs(self, root: Optional[TreeNode]) -> int:
        """Approach 5: BFS queue of (node, best). O(n) time, O(w) space.
        Level order is irrelevant — every node is independent."""
        if root is None:
            return 0
        count = 0
        q = deque([(root, root.val)])
        while q:
            node, best = q.popleft()
            if node.val >= best:
                count += 1
            nxt = max(best, node.val)
            if node.left is not None:
                q.append((node.left, nxt))
            if node.right is not None:
                q.append((node.right, nxt))
        return count

    def goodNodes_carry_path(self, root: Optional[TreeNode]) -> int:
        """Approach 2 / mistake 6: carry the whole ancestor PATH and call
        max() on it. Correct, O(n·h). Note the append/pop 'undo' that the
        integer version does not need."""
        if root is None:
            return 0
        count = 0
        path: List[int] = []

        def go(node: Optional[TreeNode]) -> None:
            nonlocal count
            if node is None:
                return
            if not path or node.val >= max(path):   # O(h) per node
                count += 1
            path.append(node.val)                    # CHOOSE
            go(node.left)
            go(node.right)
            path.pop()                               # UNCHOOSE — required now
        go(root)
        return count

    def goodNodes_brute(self, root: Optional[TreeNode]) -> int:
        """Approach 0: for every node, re-walk the root->node path to find
        its max. O(n·h). The correctness oracle for the benchmark."""
        if root is None:
            return 0

        def path_to(target: TreeNode) -> Optional[List[int]]:
            stack = [(root, [root.val])]
            while stack:
                node, acc = stack.pop()
                if node is target:
                    return acc
                if node.left is not None:
                    stack.append((node.left, acc + [node.left.val]))
                if node.right is not None:
                    stack.append((node.right, acc + [node.right.val]))
            return None

        nodes: List[TreeNode] = []
        stack = [root]
        while stack:
            node = stack.pop()
            nodes.append(node)
            if node.left is not None:
                stack.append(node.left)
            if node.right is not None:
                stack.append(node.right)

        count = 0
        for node in nodes:
            p = path_to(node)
            if len(p) == 1 or node.val >= max(p[:-1]):
                count += 1
        return count

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def goodNodes_broken_parent_only(self, root: Optional[TreeNode]) -> int:
        """✗ BROKEN ON PURPOSE — compares against the PARENT's value, not
        the path maximum. Answers "is this a local max?" instead."""
        if root is None:
            return 0
        count = 0

        def go(node, parent_val):
            nonlocal count
            if node is None:
                return
            if parent_val is None or node.val >= parent_val:
                count += 1
            go(node.left, node.val)
            go(node.right, node.val)

        go(root, None)
        return count

    def goodNodes_broken_zero_init(self, root: Optional[TreeNode]) -> int:
        """✗ BROKEN ON PURPOSE — `best` starts at 0, so an all-negative
        tree reports 0 good nodes."""
        if root is None:
            return 0
        count = 0

        def go(node, best):
            nonlocal count
            if node is None:
                return
            if node.val >= best:
                count += 1
            best = max(best, node.val)
            go(node.left, best)
            go(node.right, best)

        go(root, 0)
        return count

    def goodNodes_extend_first(self, root: Optional[TreeNode]) -> int:
        """NOT broken — extends `best` BEFORE comparing. Provably equivalent
        to the answer (`val >= max(best, val)` iff `val >= best`). Kept so
        the demo can verify that claim instead of asserting it."""
        if root is None:
            return 0
        count = 0

        def go(node, best):
            nonlocal count
            if node is None:
                return
            best = max(best, node.val)      # extended first...
            if node.val >= best:            # ...and it makes no difference
                count += 1
            go(node.left, best)
            go(node.right, best)

        go(root, root.val)
        return count

    def goodNodes_broken_never_extend(self, root: Optional[TreeNode]) -> int:
        """✗ BROKEN ON PURPOSE — passes `best` down UNCHANGED, so a node's
        own value never joins the path maximum its children see."""
        if root is None:
            return 0
        count = 0

        def go(node, best):
            nonlocal count
            if node is None:
                return
            if node.val >= best:
                count += 1
            go(node.left, best)             # should be max(best, node.val)
            go(node.right, best)

        go(root, root.val)
        return count

    def goodNodes_broken_strict(self, root: Optional[TreeNode]) -> int:
        """✗ BROKEN ON PURPOSE — `>` instead of `>=`; ties stop counting."""
        if root is None:
            return 0
        count = 0

        def go(node, best):
            nonlocal count
            if node is None:
                return
            if node.val > best:
                count += 1
            best = max(best, node.val)
            go(node.left, best)
            go(node.right, best)

        go(root, root.val)
        return count


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


# ==============================================================================
# TESTS — run:  python 015_count_good_nodes_in_binary_tree_solution.py
# ==============================================================================
CASES = [
    ([3, 1, 4, 3, None, 1, 5], 4),
    ([3, 3, None, 4, 2], 3),
    ([1], 1),
    ([5, 1, None, 3], 1),
    ([-1, -2, -3], 1),
    ([2, 4, 4, 4, None, None, 5, None, None, 4, 4], 5),
    ([9, None, 3, 6], 1),
    ([2, 2, 2, 2, 2, 2, 2], 7),
    ([-5, -6, -4], 2),
    ([1, 2, 3, 4, 5, 6, 7], 7),
    ([7, 6, 5, 4, 3, 2, 1], 1),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: six working implementations agree ---")
    impls = [
        ("top-down, best param  ", sol.goodNodes),
        ("top-down, count up    ", sol.goodNodes_return_count),
        ("iterative DFS stack   ", sol.goodNodes_iterative_stack),
        ("iterative BFS queue   ", sol.goodNodes_iterative_bfs),
        ("carry path + max()    ", sol.goodNodes_carry_path),
        ("brute: re-walk path   ", sol.goodNodes_brute),
    ]
    for name, fn in impls:
        ok = all(fn(build(vals)) == expected for vals, expected in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- per-case output ---")
    for vals, expected in CASES:
        got = sol.goodNodes(build(vals))
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {str(vals):<44} -> {got}  (want {expected})")

    # ----------------------------------------------------------------------
    # Live trace: the `best` parameter flowing down.
    # ----------------------------------------------------------------------
    print("\n--- trace: `best` carried DOWN, root = [3,1,4,null,null,1,5] shape ---")
    root = build([3, 1, 4, 3, None, 1, 5])
    print(f"  {'node':>5} {'depth':>6} {'best in':>8} {'val>=best':>10} {'best out':>9}  path")
    order = []

    def trace(node, best, depth, path):
        if node is None:
            return
        good = node.val >= best
        order.append((node.val, depth, best, good, max(best, node.val),
                      "->".join(str(v) for v in path + [node.val])))
        nb = max(best, node.val)
        trace(node.left, nb, depth + 1, path + [node.val])
        trace(node.right, nb, depth + 1, path + [node.val])

    trace(root, root.val, 0, [])
    for val, depth, bin_, good, bout, path in order:
        print(f"  {val:>5} {depth:>6} {bin_:>8} {'YES' if good else 'no':>10} "
              f"{bout:>9}  {path}")
    print(f"  good count = {sum(1 for r in order if r[3])}")
    print("  `best out` is NON-DECREASING down every path — that monotonicity is")
    print("  why a single integer captures everything the descendants need.")

    # ----------------------------------------------------------------------
    # PROOF that bottom-up cannot decide goodness: same subtree, both answers.
    # ----------------------------------------------------------------------
    print("\n--- proof: goodness is NOT a function of the subtree ---")
    x_a = TreeNode(2)
    tree_a = TreeNode(1, None, x_a)
    x_b = TreeNode(2)
    tree_b = TreeNode(3, None, x_b)
    print(f"  tree A = {to_level_order(tree_a)}   node X (val 2, no children): "
          f"good count {sol.goodNodes(tree_a)} of 2 nodes -> X IS good")
    print(f"  tree B = {to_level_order(tree_b)}   node X (val 2, no children): "
          f"good count {sol.goodNodes(tree_b)} of 2 nodes -> X is NOT good")
    proof = sol.goodNodes(tree_a) == 2 and sol.goodNodes(tree_b) == 1
    all_ok &= proof
    print(f"  identical node, identical (empty) subtree, opposite verdict: {proof}")
    print("  A postorder function sees only its own subtree, so no postorder")
    print("  return value can distinguish these. The ancestor max MUST come")
    print("  down as a parameter.")

    # ----------------------------------------------------------------------
    # The four deliberate bugs, each on a tree that exposes it.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  bug 1: compare against the PARENT instead of the path max ---")
    print(f"  {'tree':<32} {'correct':>8} {'parent-only':>12}  diverges?")
    seen = False
    for vals in ([3, 1, 4, 3, None, 1, 5], [5, 1, None, 3], [9, 5, None, 7],
                 [10, 5, None, 6, None, 7]):
        root = build(vals)
        a, b = sol.goodNodes(root), sol.goodNodes_broken_parent_only(root)
        seen |= a != b
        print(f"  {str(vals):<32} {a:>8} {b:>12}  {a != b}")
    all_ok &= seen
    print("  Row 1 is LeetCode's own Example 1 and it AGREES. The parent-only")
    print("  version answers 'is this node a local maximum', which coincides")
    print("  with the real answer whenever values only ever decrease downward.")

    print("\n--- ⚠️  bug 2: `best = 0` initialisation vs negative values ---")
    print(f"  {'tree':<28} {'correct':>8} {'best=0':>8}")
    neg_seen = False
    for vals in ([-1, -2, -3], [-5, -6, -4], [-10], [3, 1, 4, 3, None, 1, 5]):
        root = build(vals)
        a, b = sol.goodNodes(root), sol.goodNodes_broken_zero_init(root)
        neg_seen |= a != b
        print(f"  {str(vals):<28} {a:>8} {b:>8}")
    all_ok &= neg_seen
    print("  Node values are in [-10^4, 10^4]. A 0 initialiser silently asserts")
    print("  'all values are non-negative', which the constraints do not say.")

    print("\n--- ⚠️  bug 3: pass `best` down UNCHANGED (never extend it) ---")
    print(f"  {'tree':<32} {'correct':>8} {'never-extend':>13}  diverges?")
    ne_seen = False
    for vals in ([1, 5, None, 3], [1, 5, 2, 3, 4], [3, 1, 4, 3, None, 1, 5],
                 [2, 9, None, 4]):
        root = build(vals)
        a, b = sol.goodNodes(root), sol.goodNodes_broken_never_extend(root)
        ne_seen |= a != b
        print(f"  {str(vals):<32} {a:>8} {b:>13}  {a != b}")
    all_ok &= ne_seen
    print("  Every node is then compared against the ROOT's value only, so any")
    print("  node bigger than the root counts as good regardless of what sits")
    print("  between them. `max(best, node.val)` on the way down is the fix.")

    print("\n--- and a NON-bug: extend-then-compare == compare-then-extend ---")
    print(f"  {'tree':<32} {'compare first':>14} {'extend first':>13}  same?")
    equiv = True
    for vals, _exp in CASES:
        root = build(vals)
        a, b = sol.goodNodes(root), sol.goodNodes_extend_first(root)
        equiv &= (a == b)
        print(f"  {str(vals):<32} {a:>14} {b:>13}  {a == b}")
    all_ok &= equiv
    print(f"  identical on all {len(CASES)} cases: {equiv}")
    import random as _r
    _rng = _r.Random(5)
    eq_rand = all(
        sol.goodNodes(t) == sol.goodNodes_extend_first(t)
        for t in (build([_rng.choice([_rng.randint(-9, 9), None])
                         for _ in range(_rng.randint(1, 12))] or [1])
                  for _ in range(2000))
        if t is not None)
    all_ok &= eq_rand
    print(f"  and on 2000 random trees: {eq_rand}")
    print("  `val >= max(best, val)` is true exactly when `val >= best`. This")
    print("  demo was written expecting a bug; the measurement said otherwise,")
    print("  so the prose above says 'equivalent', not 'wrong'.")

    print("\n--- ⚠️  bug 4: `>` instead of `>=` (ties stop counting) ---")
    print(f"  {'tree':<32} {'correct':>8} {'strict >':>9}")
    strict_seen = False
    for vals in ([2, 2, 2, 2, 2, 2, 2], [3, 3, None, 4, 2], [3, 1, 4, 3, None, 1, 5]):
        root = build(vals)
        a, b = sol.goodNodes(root), sol.goodNodes_broken_strict(root)
        strict_seen |= a != b
        print(f"  {str(vals):<32} {a:>8} {b:>9}")
    all_ok &= strict_seen
    print("  The problem forbids ancestors STRICTLY GREATER, so equality is")
    print("  good. One character; on an all-equal tree it costs n-1 nodes.")

    # ----------------------------------------------------------------------
    # nonlocal: what happens without it.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  `count += 1` in a closure WITHOUT `nonlocal` ---")

    def good_no_nonlocal(root):
        count = 0

        def go(node, best):
            if node is None:
                return
            if node.val >= best:
                count += 1                   # no `nonlocal` -> count is LOCAL to go
            nb = max(best, node.val)
            go(node.left, nb)
            go(node.right, nb)

        go(root, root.val)
        return count

    err = None
    try:
        good_no_nonlocal(build([3, 1, 4, 3, None, 1, 5]))
    except UnboundLocalError as exc:
        err = f"{type(exc).__name__}: {exc}"
    print(f"  -> {err}")
    all_ok &= (err is not None)
    print("  Assigning to `count` ANYWHERE in `go` makes it local to `go` for")
    print("  the whole function body, so the read on the right-hand side of")
    print("  `+=` finds an unbound local. `nonlocal count` re-points the name")
    print("  at the enclosing scope's variable. (A mutable accumulator such as")
    print("  `count = [0]` and `count[0] += 1` also works — it MUTATES rather")
    print("  than rebinds — but `nonlocal` says what you mean.)")
    box = [0]

    def go_box(node, best):
        if node is None:
            return
        if node.val >= best:
            box[0] += 1                       # mutation, not rebinding: legal
        nb = max(best, node.val)
        go_box(node.left, nb)
        go_box(node.right, nb)

    go_box(build([3, 1, 4, 3, None, 1, 5]), 3)
    print(f"  the `count = [0]` / `count[0] += 1` workaround gives {box[0]} "
          f"(correct: 4)")
    all_ok &= (box[0] == 4)

    # ----------------------------------------------------------------------
    # BENCHMARK: O(1) state carried down vs carrying the path (O(n·h)).
    # ----------------------------------------------------------------------
    print("\n--- benchmark: one integer down vs the whole path down (LEFT CHAIN) ---")
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(60000)
    try:
        print(f"  {'n (h == n)':>11} {'best param (ms)':>16} {'carry path (ms)':>16} "
              f"{'brute (ms)':>12} {'path/param':>11}")
        for n in (250, 500, 1000, 2000, 4000):
            vals = [(i * 37) % 101 for i in range(n)]
            root = left_chain(vals)
            t0 = time.perf_counter()
            a = sol.goodNodes(root)
            t1 = time.perf_counter()
            b = sol.goodNodes_carry_path(root)
            t2 = time.perf_counter()
            c = sol.goodNodes_brute(root) if n <= 1000 else None
            t3 = time.perf_counter()
            all_ok &= (a == b) and (c is None or c == a)
            p_ms = (t1 - t0) * 1000
            c_ms = (t2 - t1) * 1000
            b_ms = (t3 - t2) * 1000 if c is not None else float("nan")
            brute_txt = f"{b_ms:>12.1f}" if c is not None else f"{'(skipped)':>12}"
            print(f"  {n:>11} {p_ms:>16.2f} {c_ms:>16.2f} {brute_txt} "
                  f"{c_ms / p_ms:>10.1f}x")
    finally:
        sys.setrecursionlimit(old_limit)
    print("  A left chain makes h == n, so `max(path)` costs O(n) per node and")
    print("  the ratio GROWS with n — the signature of an asymptotic gap, not a")
    print("  constant factor. On a BALANCED tree h is log n and the same code")
    print("  is only O(n log n), which is why this bug can hide in testing:")

    def perfect_tree(depth):
        if depth <= 0:
            return None
        root = TreeNode(0)
        frontier = [root]
        for _ in range(depth - 1):
            nxt = []
            for node in frontier:
                node.left = TreeNode((id(node) // 8) % 97)
                node.right = TreeNode((id(node) // 16) % 89)
                nxt.append(node.left)
                nxt.append(node.right)
            frontier = nxt
        return root

    print(f"  {'perfect depth':>13} {'nodes':>8} {'best param (ms)':>16} "
          f"{'carry path (ms)':>16} {'path/param':>11}")
    for depth in (10, 12, 14):
        root = perfect_tree(depth)
        t0 = time.perf_counter()
        a = sol.goodNodes(root)
        t1 = time.perf_counter()
        b = sol.goodNodes_carry_path(root)
        t2 = time.perf_counter()
        all_ok &= (a == b)
        p_ms, c_ms = (t1 - t0) * 1000, (t2 - t1) * 1000
        print(f"  {depth:>13} {2 ** depth - 1:>8} {p_ms:>16.2f} {c_ms:>16.2f} "
              f"{c_ms / p_ms:>10.1f}x")
    print("  On balanced input the ratio is roughly FLAT — the O(h) factor is")
    print("  only ~depth. Test on a chain or you will never see the problem.")

    # ----------------------------------------------------------------------
    # Recursion limit: a 10^5 chain is a LEGAL input here.
    # ----------------------------------------------------------------------
    print("\n--- the constraints allow a 10^5-node chain; recursion does not ---")
    print(f"  sys.getrecursionlimit() = {sys.getrecursionlimit()}")
    chain = left_chain([(i * 7) % 20001 - 10000 for i in range(100_000)])
    try:
        sol.goodNodes(chain)
        rec_msg, died = "ok (unexpected)", False
    except RecursionError as exc:
        rec_msg, died = f"{type(exc).__name__}: {exc}", True
    all_ok &= died
    print(f"  recursive, default limit -> {rec_msg}")
    it_stack = sol.goodNodes_iterative_stack(chain)
    it_bfs = sol.goodNodes_iterative_bfs(chain)
    print(f"  iterative DFS stack      -> ok, {it_stack} good nodes")
    print(f"  iterative BFS queue      -> ok, {it_bfs} good nodes")
    all_ok &= (it_stack == it_bfs)
    print("  Both iterative forms carry `best` in the stack/queue ENTRY, which")
    print("  is exactly what the call frame was doing implicitly.")

    # ----------------------------------------------------------------------
    # Randomised cross-check.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the brute-force oracle ---")
    import random
    rng = random.Random(1448)
    bad = 0
    for _ in range(3000):
        n = rng.randint(1, 12)
        vals = [rng.choice([rng.randint(-6, 6), None]) for _ in range(n)]
        vals[0] = rng.randint(-6, 6)
        root = build(vals)
        want = sol.goodNodes_brute(root)
        for _name, fn in impls:
            if fn(root) != want:
                bad += 1
    all_ok &= (bad == 0)
    print(f"  3000 random trees x {len(impls)} implementations: {bad} mismatches")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
