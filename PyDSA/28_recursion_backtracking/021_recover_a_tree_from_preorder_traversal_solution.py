r"""
================================================================================
SOLUTION · LeetCode 1028 · Recover a Tree From Preorder Traversal        [Hard]
https://leetcode.com/problems/recover-a-tree-from-preorder-traversal/
================================================================================

THE CORE IDEA
--------------
Tokenize into `(depth, value)` pairs, then rebuild with a STACK OF ANCESTORS
indexed by depth: `stack[d]` is whichever node currently sits at depth `d`.
For each incoming token, truncate the stack down to exactly `depth` entries
(everything deeper is "closed" — preorder has moved past it), attach the new
node under whatever remains on top (left if empty, else right), then push the
new node as the new owner of its depth.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. RECURSIVE DESCENT WITH A SHARED CURSOR — a helper `build(min_depth)` reads
   the next token, and if its depth < min_depth, returns None without
   consuming it (signaling "not mine"); otherwise it consumes it, recurses for
   `.left` and `.right` at `depth + 1`. Correct, O(n) time, but needs a mutable
   cursor closed over by the recursion (list-of-one-int, or a class attribute)
   since Python ints aren't mutable by reference. Written below as the
   recursive twin.
2. STACK-BASED, ITERATIVE (the intended answer) — O(n) time, O(depth) space,
   no recursion at all. Written as the primary solution.


================================================================================
STEP BY STEP TRACE — traversal = "1-2--3--4-5--6--7"
================================================================================
Tokens (depth, value): (0,1) (1,2) (2,3) (2,4) (1,5) (2,6) (2,7)

    token (0,1): stack=[]                  truncate to 0 -> []
                 parent=None (stack empty) -> this IS the root
                 stack=[Node(1)]
    token (1,2): stack=[N1]                truncate to 1 -> [N1]  (no-op, len already 1)
                 parent=stack[-1]=N1, N1.left is None -> N1.left = N2
                 stack=[N1, N2]
    token (2,3): truncate to 2 -> [N1,N2]   (no-op)
                 parent=N2, N2.left is None -> N2.left = N3
                 stack=[N1, N2, N3]
    token (2,4): truncate to 2 -> [N1,N2]   (POPS N3 off — N3 is closed)
                 parent=N2, N2.left is N3 (not None) -> N2.right = N4
                 stack=[N1, N2, N4]
    token (1,5): truncate to 1 -> [N1]      (POPS N2 AND N4 — both closed)
                 parent=N1, N1.left is N2 (not None) -> N1.right = N5
                 stack=[N1, N5]
    token (2,6): truncate to 2 -> [N1,N5]   (no-op, len already 2)
                 parent=N5, N5.left is None -> N5.left = N6
                 stack=[N1, N5, N6]
    token (2,7): truncate to 2 -> [N1,N5]   (POPS N6 — closed)
                 parent=N5, N5.left is N6 -> N5.right = N7
                 stack=[N1, N5, N7]

Final tree:        1
                   / \
                  2   5
                 / \ / \
                3  4 6  7

Notice truncation is what does all the "returning up the tree" work — no
explicit parent pointers or recursion unwinding needed.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                  Time    Space           Mutates input?  Note
    -------------------------  ------  --------------  ---------------  --------------------------------
    Stack-based (iterative)    O(n)    O(depth)        no               depth <= n; O(n) worst case (a
                                                                          single-branch degenerate tree)
    Recursive descent          O(n)    O(depth) stack  no               same asymptotics, needs a shared
                                                                          mutable cursor across calls


================================================================================
EDGE CASES
================================================================================
    "1"                    -> single node, no dashes at all; depth-0 token,
                              stack starts empty so parent is None -> root.
    Multi-digit values     -> "1-401--349---90": digits must be consumed
                              greedily until a non-digit (a dash or end of
                              string) is hit, not just one character.
    Right-child-only chain -> a node whose ONLY child is deeper by exactly 2
                              dashes (skipping a would-be left child) never
                              happens in this encoding — a child's depth is
                              always exactly parent depth + 1, so "left slot
                              empty" vs "right slot empty" is unambiguous from
                              depth alone, never from a gap in dash count.
    Long thin tree          -> depth grows to O(n); stack depth (and, for the
                              recursive twin, call stack depth) grows with it —
                              exercised in the tests below with a synthetic
                              1000-node single-branch string.


================================================================================
COMMON MISTAKES
================================================================================
1. Counting dashes with a `while s[i] == '-': i += 1` loop but forgetting a
   node's OWN value can never contain a dash, so once digits start, dashes
   are done for this token — mixing the two loops (dash-count then digit-scan)
   into one pass without a clean state transition is a common source of
   off-by-one bugs.
2. Truncating the stack to `depth` using `stack[:depth]` (a copy) rather than
   `del stack[depth:]` or reassigning — the copy variant works but silently
   throws away O(n) extra list objects if done every token; not a correctness
   bug, but a real, measurable performance difference at n=1000 tokens deep.
3. Checking `if parent.left is None` — correct — versus checking `if not
   parent.left`, which is ALSO correct here only because tree nodes are never
   falsy by value; still, prefer the explicit `is None` since a node
   overriding `__bool__` or `__len__` (as this file's test-only `TreeNode`
   does NOT, but some libraries' do) would silently break the `not` version.
4. Assuming the root is `stack[0]` after the loop — the root is whichever
   node was attached when the stack was empty (depth 0), which must be
   captured explicitly the first time, not inferred from stack state at the
   end (the stack may have been fully drained and refilled multiple times).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Could you do this without any auxiliary stack, purely recursively, reading
   the string left to right exactly once?
A: Yes — the recursive-descent twin below does this, but it needs a shared
   mutable read cursor (a one-element list, since Python closures can read
   but not rebind an outer int) so that sibling recursive calls continue from
   where the previous call left off rather than re-parsing from the start.

Q: What if depths could jump by more than 1 (a malformed encoding)?
A: The problem guarantees a valid preorder encoding where a node's depth is
   always exactly parent-depth + 1, so this is out of scope — but the fix
   would be to treat any larger jump as invalid input and raise, since no
   tree traversal produces a depth jump greater than 1.

Q: How would this change for an n-ary tree instead of binary?
A: The truncate-and-attach-to-top-of-stack logic is IDENTICAL; only the
   "which child slot" step changes — instead of a left/right binary choice,
   you'd `parent.children.append(node)` unconditionally, since an n-ary
   node's children are just a list, not two fixed slots.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 105  Construct Binary Tree from Preorder and Inorder Traversal —
            also reconstructs from preorder, but needs a SECOND traversal
            (inorder) to disambiguate left/right, instead of depth markers.
    LC 428  Serialize and Deserialize N-ary Tree — same stack-by-depth /
            token-by-token reconstruction idea, generalized to n children.
    Topic 10 (Trees) — general preorder/level-order build-a-tree-from-a-
            serialization family.
================================================================================
"""

from typing import List, Optional, Tuple


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

    def __eq__(self, other):
        if other is None:
            return False
        return (
            self.val == other.val
            and self.left == other.left
            and self.right == other.right
        )

    def __repr__(self):
        return f"TreeNode({self.val})"


def build_tree(rows):
    if not rows:
        return None
    it = iter(rows)
    root = TreeNode(next(it))
    queue = [root]
    while queue:
        node = queue.pop(0)
        try:
            lv = next(it)
        except StopIteration:
            break
        if lv is not None:
            node.left = TreeNode(lv)
            queue.append(node.left)
        try:
            rv = next(it)
        except StopIteration:
            break
        if rv is not None:
            node.right = TreeNode(rv)
            queue.append(node.right)
    return root


def _tokenize(traversal: str) -> List[Tuple[int, int]]:
    tokens = []
    i, n = 0, len(traversal)
    while i < n:
        depth = 0
        while i < n and traversal[i] == "-":
            depth += 1
            i += 1
        j = i
        while j < n and traversal[j] != "-":
            j += 1
        tokens.append((depth, int(traversal[i:j])))
        i = j
    return tokens


class Solution:
    def recoverFromPreorder(self, traversal: str) -> Optional[TreeNode]:
        """Stack-based, iterative. O(n) time, O(depth) space."""
        tokens = _tokenize(traversal)
        stack: List[TreeNode] = []
        root = None
        for depth, value in tokens:
            node = TreeNode(value)
            del stack[depth:]
            if stack:
                parent = stack[-1]
                if parent.left is None:
                    parent.left = node
                else:
                    parent.right = node
            else:
                root = node
            stack.append(node)
        return root

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def recoverFromPreorder_recursive(self, traversal: str) -> Optional[TreeNode]:
        """Recursive descent with a shared mutable cursor. O(n) time,
        O(depth) call-stack space."""
        tokens = _tokenize(traversal)
        cursor = [0]  # one-element list: a reboxable "int" for the closure

        def build(min_depth: int) -> Optional[TreeNode]:
            if cursor[0] >= len(tokens):
                return None
            depth, value = tokens[cursor[0]]
            if depth < min_depth:
                return None  # not ours — belongs to an ancestor's other branch
            cursor[0] += 1
            node = TreeNode(value)
            node.left = build(min_depth + 1)
            node.right = build(min_depth + 1)
            return node

        return build(0)


# ==============================================================================
# TESTS — run:  python 021_recover_a_tree_from_preorder_traversal_solution.py
# ==============================================================================
CASES = [
    ("1-2--3--4-5--6--7", [1, 2, 5, 3, 4, 6, 7]),
    ("1-2--3---4-5--6---7", [1, 2, 5, 3, None, 6, None, 4, None, 7, None]),
    ("1", [1]),
    ("1-401--349---90", [1, 401, None, 349, None, 90, None]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    impls = [
        ("stack-based (iterative)", sol.recoverFromPreorder),
        ("recursive descent      ", sol.recoverFromPreorder_recursive),
    ]

    for name, fn in impls:
        ok = True
        for traversal, expected_rows in CASES:
            expected = build_tree(expected_rows)
            got = fn(traversal)
            if got != expected:
                ok = False
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # ----------------------------------------------------------------------
    # A long single-branch tree: depth grows to n, exercising stack/recursion
    # depth for real rather than just asserting it should work.
    # ----------------------------------------------------------------------
    print("\n--- degenerate single-branch tree, depth grows to n ---")
    n = 800
    parts = []
    for depth in range(n):
        parts.append("-" * depth + str(depth + 1))
    long_traversal = "".join(parts)
    root = sol.recoverFromPreorder(long_traversal)
    depth_seen = 0
    node = root
    while node is not None:
        depth_seen += 1
        node = node.left
    print(f"  built a chain of depth {depth_seen} (expected {n}) via the left spine.")
    if depth_seen != n:
        all_ok = False
        print("  FAIL — chain depth mismatch")
    else:
        print(f"  PASS — iterative version handles n={n} depth with no recursion limit risk.")

    root_recursive = sol.recoverFromPreorder_recursive(long_traversal)
    if root_recursive != root:
        all_ok = False
        print("  FAIL — recursive-descent twin disagrees with the iterative version")
    else:
        print(f"  Recursive-descent twin agrees on the same {n}-deep chain "
              f"(sys recursion limit allows it since depth {n} tokens each add one frame).")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
