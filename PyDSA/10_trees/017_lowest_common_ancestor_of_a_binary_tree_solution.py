"""
================================================================================
SOLUTION · LeetCode 236 · Lowest Common Ancestor of a Binary Tree      [Medium]
https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/
================================================================================

THE CORE IDEA
--------------
A five-line postorder recursion where the RETURN VALUE means two different
things depending on where you read it — and that overloading is deliberate:

    def lca(node):
        if node is None or node is p or node is q:
            return node                      # found one, or ran out of tree
        left  = lca(node.left)
        right = lca(node.right)
        if left and right:
            return node                       # p and q split HERE -> the answer
        return left or right                  # pass up whatever was found

    "return value" reads as:
        None      -> neither p nor q is in this subtree
        p or q    -> exactly one of them is in this subtree (and this is it)
        any other -> the LCA has already been determined, inside this subtree

The last case is why the function is correct without any extra bookkeeping:
once `left and right` fires at some node, that node is returned upward and
every ancestor sees it as "exactly one thing found on this side", so it
propagates unchanged to the root. The answer is decided once and never
revised.

WHY `node is p` RETURNS IMMEDIATELY (without recursing): a node is a
descendant of itself, so if the current node IS p, then whether or not q is
below it, p is already the lowest common ancestor of the pair *within this
subtree*. Cutting the recursion there is not an optimisation — it is what
implements "a node may be a descendant of itself". Delete it and Example 2
returns None.

O(n) time, O(h) space.

THIS IS A BOTTOM-UP PROBLEM (topic guide Part 3): the answer at a node is a
function of its DESCENDANTS, so information travels upward in return values.
Nothing needs to be carried down. Contrast problem 015, where "good" depends
on ANCESTORS and the state must travel down as a parameter.


================================================================================
MULTIPLE APPROACHES
================================================================================
0. BRUTE FORCE — for every node, test "is p in my subtree AND is q in my
   subtree?", and among all nodes that pass, keep the DEEPEST. Each
   containment test is an O(n) subtree walk, so O(n^2) total. Correct, and
   worth stating because it is the literal definition of the problem. Coded
   below as the correctness oracle.

1. POSTORDER "RETURN NON-NULL FROM BOTH SIDES" ✅ — the version above. O(n)
   time, O(h) space. The answer.

2. PATHS FROM THE ROOT — find the root->p path and the root->q path as two
   lists of nodes, then walk them in lockstep and return the last node they
   agree on. O(n) time to find each path, O(h) extra space for the two
   lists. Concrete, easy to explain, and it generalises to "give me the
   distance between p and q" for free (LC 1740) because you keep the actual
   paths. Coded below.

3. PARENT POINTERS + ANCESTOR SET — one pass (BFS or DFS) recording
   `parent[node]` for every node, then walk up from p adding each ancestor
   to a set, then walk up from q and return the first node already in that
   set. O(n) time, O(n) space. This is the approach to reach for when:
     · the tree gives you `.parent` already (LC 1650), in which case you skip
       the first pass entirely and it becomes O(h) time, O(h) space;
     · you must answer MANY LCA queries on the same tree (the parent map is
       built once and reused);
     · the recursion depth is a problem — this version is fully iterative.
   Coded below.

4. ITERATIVE POSTORDER — approach 1 without recursion, using an explicit
   stack. More fiddly than approach 3 for the same benefit, so approach 3 is
   the better "no recursion" answer. Not coded; named so you can say why you
   picked 3 instead.

WHAT ABOUT A BST? (LC 235) — different problem, cheaper answer. See below.


================================================================================
LC 235 (BST) IS A DIFFERENT AND CHEAPER PROBLEM
================================================================================
In a plain binary tree there is NO way to know which subtree contains p
without looking, so you must be prepared to visit every node: O(n) is
optimal. A BST's ordering invariant removes the search entirely — at each
node you can decide by comparison alone:

    while node:
        if p.val < node.val and q.val < node.val:   both strictly LEFT
            node = node.left
        elif p.val > node.val and q.val > node.val:  both strictly RIGHT
            node = node.right
        else:
            return node        # they split here, or one of them IS this node

    Time O(h) — O(log n) on a balanced BST. Space O(1) iteratively.

The moment the two values fall on opposite sides of `node.val` (or one of
them equals it), the descent stops: that is the split point. No subtree is
ever explored, nothing is returned upward, and there is no recursion at all.

    plain binary tree LCA : O(n) time, O(h) space, must inspect everything
    BST LCA               : O(h) time, O(1) space, decided by comparisons

The benchmark below runs both on the same perfect BST of 131071 nodes.
Measured on this machine: the BST descent takes 0.25-1.0 us depending on how
deep the split point is, the general recursion takes 5-8 MILLIseconds every
time — a speedup of ~7500x to ~30000x. That is what "O(h) vs O(n)" looks like
at n ~ 10^5, and it is why "is it a BST?" is worth asking out loud before you
start coding any tree problem.

Note also which quantity each cost tracks: the BST descent's step count is
the DEPTH OF THE ANSWER (1 step when the pair splits at the root, 16 when it
splits just above the leaves), while the general recursion visits all 131071
nodes regardless. And the two are NOT interchangeable — running the BST
descent on a non-BST returns nonsense silently, which the demo also shows.


================================================================================
THE "WHAT IF A NODE MIGHT NOT EXIST" FOLLOW-UP (LC 1644)
================================================================================
LC 236 guarantees that p and q are both in the tree. Drop that guarantee and
the five-line recursion becomes WRONG — silently, in the most plausible way
possible:

    tree = [3,5,1,...],  p = node 5 (exists),  q = a node with value 99
                                                     (NOT in this tree)
    the recursion returns 5   — because it found p, found nothing else, and
                                dutifully passed p upward
    the correct answer is None — there is no common ancestor of a pair when
                                one of the pair does not exist

The failure mode is nasty because the returned node is a real node and looks
like a reasonable answer. Two fixes:

  (a) VERIFY FIRST — run the recursion, then separately confirm both p and q
      actually exist (two O(n) searches, or one that looks for both). Total
      still O(n), and it keeps the elegant recursion untouched.
  (b) COUNT WHILE YOU RECURSE — have the recursion also report how many of
      {p, q} it found, and only accept the candidate if the count is 2:

        def go(node):                  # returns (candidate, found_count)
            if node is None: return (None, 0)
            lc, ln = go(node.left)
            rc, rn = go(node.right)
            n = ln + rn + (1 if node is p or node is q else 0)
            if node is p or node is q:  return (node, n)
            if lc and rc:               return (node, n)
            return ((lc or rc), n)

      Note this version must NOT return early at `node is p` — it has to
      keep descending to discover whether q is below. That is the price of
      the extra guarantee: you lose the early cut. Both are coded below and
      the difference is measured.

Both are worth having ready; (b) is what LC 1644 wants.


================================================================================
STEP BY STEP TRACE — root=[3,5,1,6,2,0,8,null,null,7,4], p=7, q=4
================================================================================
                    3
              ┌─────┴─────┐
              5           1
           ┌──┴──┐     ┌──┴──┐
           6     2     0     8
               ┌─┴─┐
               7    4

    call        left    right   rule fired                     returns
    ----------  ------  ------  ----------------------------   -------
    lca(7)      -       -       node is p                       7
    lca(4)      -       -       node is q                       4
    lca(2)      7       4       left and right -> SPLIT HERE     2   <- the answer
    lca(6)      None    None    return left or right             None
    lca(5)      None    2       one side only, pass it up        2
    lca(0)      None    None                                     None
    lca(8)      None    None                                     None
    lca(1)      None    None    return left or right             None
    lca(3)      2       None    one side only, pass it up        2

    Read the last column bottom-up: the answer 2 is decided at lca(2) and
    then simply relayed through 5 and 3 without being re-examined.

    Now p=5, q=4 (Example 2 — a node that is its own ancestor):

    call        left    right   rule fired                     returns
    ----------  ------  ------  ----------------------------   -------
    lca(5)      -       -       node is p -> RETURN IMMEDIATELY  5
                                (never descends, never sees 4)
    lca(1)      None    None                                     None
    lca(3)      5       None    one side only, pass it up        5   <- the answer

    lca(5) returns before looking at its children. If instead you removed
    the early return and required `left and right`, node 5 would see 4 on
    one side and nothing on the other, return 4, and the final answer would
    be 4 — wrong. Printed live below.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                            Time      Space    Mutates input?  Note
    ----------------------------------  --------  -------  --------------  ---------------------
    Brute: deepest node containing both O(n^2)    O(h)     no              the definition,
                                                                            literally
    Postorder return-non-null ✅        O(n)      O(h)     no              the answer
    Root paths, compare in lockstep     O(n)      O(h)     no              also gives the
                                                                            DISTANCE (LC 1740)
    Parent map + ancestor set           O(n)      O(n)     no              iterative; best for
                                                                            repeated queries
    Given real .parent pointers         O(h)      O(h)     no              LC 1650 — no tree
                                                                            walk at all
    Counting variant (may not exist)    O(n)      O(h)     no              LC 1644; loses the
                                                                            early cut
    BST (LC 235) — different problem    O(h)      O(1)     no              comparisons only

    n = nodes, h = height. Nothing here mutates the tree; the parent-map
    version builds an auxiliary dict of n entries and leaves the tree alone.

    WHY O(n) IS OPTIMAL FOR A PLAIN BINARY TREE: an adversary can put q as
    the very last node you inspect, so any correct algorithm must be able to
    look at every node. The BST case escapes this only because the values
    tell you where to look.


================================================================================
EDGE CASES
================================================================================
    p IS an ancestor of q       -> the answer is p (Example 2). Handled by
                                   the early `node is p` return; this is the
                                   most-missed case.
    p is the ROOT                -> the answer is the root, immediately.
    p and q are siblings         -> their shared parent, via `left and right`.
    p and q in opposite halves   -> the root (or the first common branch).
    the two-node tree [1,2]       -> the only legal pair is (1, 2) and the
                                   answer is 1, an ancestor-of-itself case.
    a long chain, p at the top    -> answer is p; the recursion never
                                   descends past it — but the *counting*
                                   variant does, and on a 10^5 chain that
                                   means 10^5 frames. Demonstrated.
    duplicate VALUES              -> excluded by the constraints, and this is
                                   why nodes are passed as REFERENCES: with
                                   duplicate values, "the node with value 5"
                                   would be ambiguous while a reference never
                                   is. Comparing `node.val == p.val` instead
                                   of `node is p` is the bug this invites.
    p not in the tree              -> outside LC 236's constraints; the plain
                                   recursion returns a wrong non-None node.
                                   Demonstrated.


================================================================================
COMMON MISTAKES
================================================================================
1. Handling only case (a) — insisting that p and q sit in two DIFFERENT
   strict subtrees. Then no node ever qualifies when one of the pair is an
   ancestor of the other, and you return `None` for Example 2. Printed live
   below.

   ⚠️ A NON-mistake that looks like one: moving `if node is p or node is q:
   return node` from the base case to BELOW the two recursive calls. That is
   still correct — it out-ranks `return left or right`, so p is still passed
   upward. What it loses is the early cut: it explores the entire subtree
   under p before answering. Measured below on a 600-node chain: 1 node
   visited versus 600. A performance difference, not a correctness one; do
   not report it as a bug.

2. Comparing values (`node.val == p.val`) instead of identity (`node is p`).
   Works here only because the constraints promise unique values; it is the
   wrong comparison in principle, and it breaks immediately in any variant
   with duplicates. Also note `==` on TreeNode is identity anyway (no
   `__eq__` is defined), so `node == p` happens to be correct — but say `is`
   so the intent is unambiguous.

3. `return left if left else right` written as `return left and right` (or
   any other boolean slip). `left or right` is "whichever one was found";
   `left and right` returns `right` when both are truthy, which silently
   skips the split node.

4. Returning `node` when only ONE side is non-null. That makes every
   ancestor of the found node a "common ancestor", so the answer becomes
   the ROOT every time — technically a common ancestor, never the lowest.

5. Assuming both nodes exist when the problem does not say so (LC 1644).
   The plain recursion returns a plausible non-None node. See the section
   above.

6. Using the plain O(n) recursion on a BST and not mentioning LC 235's O(h)
   descent. Correct but leaves the interviewer's real question unanswered.

7. Recursing on a 10^5-node chain: h = 10^5 versus a default recursion
   limit of 1000. The parent-map approach (3) is the iterative escape.

8. In the parent-map approach, forgetting to add p ITSELF to the ancestor
   set before walking up from q. If p is an ancestor of q, p must be in the
   set for q's upward walk to hit it — otherwise you return p's parent.

9. In the root-paths approach, comparing the paths by VALUE lists and then
   returning a value rather than the node, or walking past the end of the
   shorter path (`while i < min(len(a), len(b))`, not `len(a)`).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if p or q might NOT be in the tree (LC 1644)?
A: The plain recursion is wrong — see the dedicated section above. Either
   verify existence separately, or return `(candidate, found_count)` and
   require the count to be 2. State that the counting version cannot take
   the early exit at `node is p`.

Q: What if the tree is a BST (LC 235)?
A: O(h) time, O(1) space by comparison-driven descent. See the section
   above. Do not run the O(n) recursion on a BST.

Q: What if each node has a `.parent` pointer (LC 1650)?
A: No tree walk at all. Either collect p's ancestors into a set and walk up
   from q (O(h) space), or use the two-pointer trick: walk both up, and when
   one hits the root, restart it from the other's original node — they meet
   at the LCA after at most 2h steps, in O(1) space. Exactly the LC 160
   "intersection of two linked lists" trick, which is what a parent-pointer
   tree really is.

Q: Many LCA queries on the same tree?
A: Preprocess. Binary lifting gives O(n log n) preprocessing and O(log n)
   per query; Euler tour + sparse-table RMQ gives O(n log n) / O(1); Tarjan's
   offline algorithm with union-find gives near-O(n + q) if all queries are
   known up front. Answering each query independently in O(n) is the thing
   to stop doing.

Q: LCA of a whole SET of nodes (LC 1123 / 1676)?
A: The same recursion generalises: return the node if any descendant is in
   the set, and "both sides non-null" still identifies the split. For LC 1123
   (deepest leaves) return `(depth, lca)` upward and take the deeper side, or
   the current node when the depths tie.

Q: The DISTANCE between p and q (LC 1740)?
A: `depth(p) + depth(q) - 2 * depth(lca)`. The root-paths approach (2) gives
   you all three quantities in one shot, which is why it is worth knowing
   even though it is longer than the five-line version.

Q: Do it iteratively.
A: Approach 3 (parent map + ancestor set). Say WHY: it is the natural
   iterative form, whereas an iterative postorder is more code for the same
   result.

Q: The nodes are given by VALUE, not by reference.
A: Find the nodes first (one O(n) pass), then run the same algorithm — and
   note that this only makes sense because values are unique.


================================================================================
RELATED PROBLEMS — the pattern family
================================================================================
  LCA VARIANTS:
    LC 236   LCA of a Binary Tree            — this problem
    LC 235   LCA of a Binary Search Tree      — O(h) by comparison (topic 11)
    LC 1644  LCA of a Binary Tree II          — p or q may not exist
    LC 1650  LCA of a Binary Tree III         — parent pointers given
    LC 1676  LCA of a Binary Tree IV          — a whole set of nodes
    LC 1123  LCA of Deepest Leaves            — return (depth, lca) upward
    LC 865   Smallest Subtree with all Deepest Nodes — 1123 restated
    LC 1740  Find Distance in a Binary Tree    — depths + LCA

  BOTTOM-UP POSTORDER, SAME SHAPE (this topic):
    LC 104   Maximum Depth                    — return the height up (005)
    LC 110   Balanced Binary Tree              — return height + a flag (009)
    LC 543   Diameter of Binary Tree           — return depth, global best (010)
    LC 124   Binary Tree Maximum Path Sum      — return gain, global best (018)
    LC 508   Most Frequent Subtree Sum          — return the subtree sum up
    LC 250   Count Univalue Subtrees            — return a bool up

  THE SAME "TWO POINTERS MEET" TRICK ELSEWHERE:
    LC 160   Intersection of Two Linked Lists  — LC 1650 with `.next` for
                                                  `.parent` (topic 08)
================================================================================
"""

import random
import sys
import time
from collections import deque
from typing import Dict, List, Optional, Tuple


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def lowestCommonAncestor(self, root: Optional[TreeNode], p: TreeNode,
                             q: TreeNode) -> Optional[TreeNode]:
        """Postorder: return non-null from both sides. O(n) time, O(h)
        space. See THE CORE IDEA above."""
        if root is None or root is p or root is q:
            return root                        # found one, or ran out of tree
        left = self.lowestCommonAncestor(root.left, p, q)
        right = self.lowestCommonAncestor(root.right, p, q)
        if left is not None and right is not None:
            return root                         # p and q split HERE
        return left if left is not None else right

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def lca_root_paths(self, root: Optional[TreeNode], p: TreeNode,
                       q: TreeNode) -> Optional[TreeNode]:
        """Approach 2: build the root->p and root->q paths, then walk them
        in lockstep. O(n) time, O(h) space. Also yields the distance."""
        def path_to(target: TreeNode) -> Optional[List[TreeNode]]:
            stack = [(root, [root])] if root is not None else []
            while stack:
                node, acc = stack.pop()
                if node is target:
                    return acc
                if node.left is not None:
                    stack.append((node.left, acc + [node.left]))
                if node.right is not None:
                    stack.append((node.right, acc + [node.right]))
            return None

        a, b = path_to(p), path_to(q)
        if a is None or b is None:
            return None
        best = None
        for x, y in zip(a, b):                  # zip stops at the shorter path
            if x is y:
                best = x
            else:
                break
        return best

    def lca_parent_map(self, root: Optional[TreeNode], p: TreeNode,
                       q: TreeNode) -> Optional[TreeNode]:
        """Approach 3: one iterative pass to record every node's parent,
        then walk up from p into a set and up from q until a hit. O(n)
        time, O(n) space, no recursion at all."""
        if root is None:
            return None
        parent: Dict[int, Optional[TreeNode]] = {id(root): None}
        nodes: Dict[int, TreeNode] = {id(root): root}
        stack = [root]
        while stack:
            node = stack.pop()
            for child in (node.left, node.right):
                if child is not None:
                    parent[id(child)] = node
                    nodes[id(child)] = child
                    stack.append(child)
        if id(p) not in parent or id(q) not in parent:
            return None
        ancestors = set()
        node: Optional[TreeNode] = p
        while node is not None:
            ancestors.add(id(node))             # p ITSELF goes in (mistake 8)
            node = parent[id(node)]
        node = q
        while node is not None:
            if id(node) in ancestors:
                return node
            node = parent[id(node)]
        return None

    def lca_may_not_exist(self, root: Optional[TreeNode], p: TreeNode,
                          q: TreeNode) -> Optional[TreeNode]:
        """LC 1644: p or q may be absent. Returns (candidate, found_count)
        internally and only accepts a candidate when BOTH were found. Note
        it cannot take the early exit at `node is p`."""
        def go(node: Optional[TreeNode]) -> Tuple[Optional[TreeNode], int]:
            if node is None:
                return (None, 0)
            lc, ln = go(node.left)
            rc, rn = go(node.right)
            here = 1 if (node is p or node is q) else 0
            found = ln + rn + here
            if here:
                return (node, found)             # must NOT stop descending
            if lc is not None and rc is not None:
                return (node, found)
            return (lc if lc is not None else rc, found)

        cand, found = go(root)
        return cand if found == 2 else None

    def lca_bst(self, root: Optional[TreeNode], p: TreeNode,
                q: TreeNode) -> Optional[TreeNode]:
        """LC 235: a BST. O(h) time, O(1) space — comparisons only, no
        subtree is ever explored. A DIFFERENT problem, not an optimisation
        of the general one."""
        node = root
        while node is not None:
            if p.val < node.val and q.val < node.val:
                node = node.left
            elif p.val > node.val and q.val > node.val:
                node = node.right
            else:
                return node                      # they split here
        return None

    def lca_brute(self, root: Optional[TreeNode], p: TreeNode,
                  q: TreeNode) -> Optional[TreeNode]:
        """Approach 0: the definition, literally. For every node, test
        whether both p and q are in its subtree; keep the deepest such
        node. O(n^2). The correctness oracle."""
        def contains(node: Optional[TreeNode], target: TreeNode) -> bool:
            stack = [node] if node is not None else []
            while stack:
                cur = stack.pop()
                if cur is target:
                    return True
                if cur.left is not None:
                    stack.append(cur.left)
                if cur.right is not None:
                    stack.append(cur.right)
            return False

        best, best_depth = None, -1
        stack = [(root, 0)] if root is not None else []
        while stack:
            node, depth = stack.pop()
            if contains(node, p) and contains(node, q) and depth > best_depth:
                best, best_depth = node, depth
            if node.left is not None:
                stack.append((node.left, depth + 1))
            if node.right is not None:
                stack.append((node.right, depth + 1))
        return best

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def lca_broken_split_only(self, root: Optional[TreeNode], p: TreeNode,
                              q: TreeNode) -> Optional[TreeNode]:
        """✗ BROKEN ON PURPOSE — handles ONLY case (a): p and q must be in
        two DIFFERENT strict subtrees. Never considers that a node can be
        its own ancestor, so it returns None for Example 2 (mistake 1)."""
        def contains(node: Optional[TreeNode], target: TreeNode) -> bool:
            stack = [node] if node is not None else []
            while stack:
                cur = stack.pop()
                if cur is target:
                    return True
                if cur.left is not None:
                    stack.append(cur.left)
                if cur.right is not None:
                    stack.append(cur.right)
            return False

        if root is None:
            return None
        if ((contains(root.left, p) and contains(root.right, q))
                or (contains(root.right, p) and contains(root.left, q))):
            return root
        left = self.lca_broken_split_only(root.left, p, q)
        right = self.lca_broken_split_only(root.right, p, q)
        return left if left is not None else right

    def lca_selfcheck_after_recursion(self, root: Optional[TreeNode], p: TreeNode,
                                      q: TreeNode) -> Optional[TreeNode]:
        """NOT broken — the `node is p or node is q` test moved AFTER the two
        recursive calls. Still correct (it takes precedence over
        `left or right`), just slower: it always explores the whole subtree
        below p instead of cutting there. Kept so the demo can measure the
        difference rather than assert it."""
        if root is None:
            return None
        left = self.lca_selfcheck_after_recursion(root.left, p, q)
        right = self.lca_selfcheck_after_recursion(root.right, p, q)
        if left is not None and right is not None:
            return root
        if root is p or root is q:
            return root
        return left if left is not None else right

    def lca_broken_return_node(self, root: Optional[TreeNode], p: TreeNode,
                               q: TreeNode) -> Optional[TreeNode]:
        """✗ BROKEN ON PURPOSE — returns `root` whenever EITHER side is
        non-null, so every ancestor claims to be the answer and the root
        always wins (mistake 4)."""
        if root is None or root is p or root is q:
            return root
        left = self.lca_broken_return_node(root.left, p, q)
        right = self.lca_broken_return_node(root.right, p, q)
        if left is not None or right is not None:
            return root                          # `or`, not `and`
        return None


# ==============================================================================
# TEST HELPERS
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


def find(root: Optional[TreeNode], val: int) -> Optional[TreeNode]:
    """Locate the NODE with the given value (values are unique here)."""
    stack = [root] if root is not None else []
    while stack:
        node = stack.pop()
        if node.val == val:
            return node
        if node.left is not None:
            stack.append(node.left)
        if node.right is not None:
            stack.append(node.right)
    return None


def all_nodes(root: Optional[TreeNode]) -> List[TreeNode]:
    out, stack = [], [root] if root is not None else []
    while stack:
        node = stack.pop()
        out.append(node)
        if node.left is not None:
            stack.append(node.left)
        if node.right is not None:
            stack.append(node.right)
    return out


def balanced_bst(depth: int) -> Tuple[Optional[TreeNode], List[TreeNode]]:
    """A perfect BST whose inorder is 1..2^depth-1, built iteratively.
    Returns (root, nodes-in-inorder)."""
    n = 2 ** depth - 1
    values = list(range(1, n + 1))

    root: Optional[TreeNode] = None
    if n:
        # build level by level from the value ranges, no recursion
        root = TreeNode(0)
        work = [(root, 0, n - 1)]
        while work:
            node, lo, hi = work.pop()
            mid = (lo + hi) // 2
            node.val = values[mid]
            if lo <= mid - 1:
                node.left = TreeNode(0)
                work.append((node.left, lo, mid - 1))
            if mid + 1 <= hi:
                node.right = TreeNode(0)
                work.append((node.right, mid + 1, hi))
    # inorder collection, iteratively
    inorder, stack, node = [], [], root
    while stack or node is not None:
        while node is not None:
            stack.append(node)
            node = node.left
        node = stack.pop()
        inorder.append(node)
        node = node.right
    return root, inorder


def left_chain(n: int) -> Tuple[Optional[TreeNode], List[TreeNode]]:
    """A left-only chain of n nodes; returns (root, nodes top-to-bottom)."""
    root = TreeNode(0)
    nodes = [root]
    cur = root
    for i in range(1, n):
        cur.left = TreeNode(i)
        cur = cur.left
        nodes.append(cur)
    return root, nodes


def random_tree(n: int, rng: random.Random) -> Optional[TreeNode]:
    if n == 0:
        return None
    vals = rng.sample(range(-1000, 1000), n)
    root = TreeNode(vals[0])
    nodes = [root]
    for v in vals[1:]:
        while True:
            parent = rng.choice(nodes)
            if parent.left is None and (parent.right is None or rng.random() < 0.5):
                parent.left = TreeNode(v)
                nodes.append(parent.left)
                break
            if parent.right is None:
                parent.right = TreeNode(v)
                nodes.append(parent.right)
                break
    return root


# ==============================================================================
# TESTS — run:  python 017_lowest_common_ancestor_of_a_binary_tree_solution.py
# ==============================================================================
TREE = [3, 5, 1, 6, 2, 0, 8, None, None, 7, 4]
CASES = [
    (TREE, 5, 1, 3),
    (TREE, 5, 4, 5),
    (TREE, 7, 4, 2),
    (TREE, 6, 4, 5),
    (TREE, 7, 8, 3),
    (TREE, 3, 7, 3),
    (TREE, 2, 7, 2),
    ([1, 2], 1, 2, 1),
    ([1, 2, 3], 2, 3, 1),
    ([1, 2, None, 3, None, 4], 3, 4, 3),
    ([1, 2, None, 3, None, 4], 2, 4, 2),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: four working implementations agree ---")
    impls = [
        ("postorder return-non-null", sol.lowestCommonAncestor),
        ("root paths in lockstep   ", sol.lca_root_paths),
        ("parent map + ancestor set", sol.lca_parent_map),
        ("counting (LC 1644 form)  ", sol.lca_may_not_exist),
        ("brute: deepest container ", sol.lca_brute),
    ]
    for name, fn in impls:
        ok = True
        for vals, pv, qv, want in CASES:
            root = build(vals)
            got = fn(root, find(root, pv), find(root, qv))
            ok &= (got is not None and got.val == want)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- per-case output ---")
    for vals, pv, qv, want in CASES:
        root = build(vals)
        got = sol.lowestCommonAncestor(root, find(root, pv), find(root, qv))
        gv = got.val if got is not None else None
        ok = gv == want
        all_ok &= ok
        note = " (p is an ancestor of q)" if want in (pv, qv) else ""
        print(f"{'PASS' if ok else 'FAIL'}  tree={str(vals):<42} p={pv:<3} q={qv:<3} "
              f"-> {gv}{note}")

    # ----------------------------------------------------------------------
    # Live trace: what each call returns, and why.
    # ----------------------------------------------------------------------
    for pv, qv in ((7, 4), (5, 4)):
        print(f"\n--- trace: p={pv}, q={qv} ---")
        root = build(TREE)
        p, q = find(root, pv), find(root, qv)
        print(f"  {'call':<10} {'left':>6} {'right':>6}  {'rule':<34} returns")
        log = []

        def trace(node):
            if node is None:
                return None
            if node is p or node is q:
                log.append((node.val, "-", "-",
                            f"node is {'p' if node is p else 'q'} -> return NOW",
                            node.val))
                return node
            left = trace(node.left)
            right = trace(node.right)
            if left is not None and right is not None:
                log.append((node.val, left.val, right.val,
                            "left AND right -> SPLIT HERE", node.val))
                return node
            res = left if left is not None else right
            log.append((node.val,
                        left.val if left else None,
                        right.val if right else None,
                        "one side only -> pass it up",
                        res.val if res else None))
            return res

        ans = trace(root)
        for val, l, r, rule, ret in log:
            print(f"  lca({val}){'':<{max(0, 4 - len(str(val)))}} {str(l):>6} "
                  f"{str(r):>6}  {rule:<34} {ret}")
        ok = ans is not None and ans.val == (2 if (pv, qv) == (7, 4) else 5)
        all_ok &= ok
        print(f"  answer = {ans.val}   correct: {ok}")

    # ----------------------------------------------------------------------
    # ⚠️ Bug 1: no early return -> "a node is a descendant of itself" broken.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  bug: handle only case (a), the strict split (mistake 1) ---")
    print(f"  {'p':>3} {'q':>3} {'correct':>8} {'split-only':>11}  diverges?")
    seen = False
    for pv, qv in [(5, 4, ), (5, 6, ), (3, 7, ), (7, 4, ), (5, 1, ), (2, 7, )]:
        root = build(TREE)
        p, q = find(root, pv), find(root, qv)
        a = sol.lowestCommonAncestor(root, p, q)
        b = sol.lca_broken_split_only(root, p, q)
        av = a.val if a else None
        bv = b.val if b else None
        seen |= av != bv
        print(f"  {pv:>3} {qv:>3} {str(av):>8} {str(bv):>11}  {av != bv}")
    all_ok &= seen
    print("  It diverges exactly when one of the pair is an ANCESTOR of the")
    print("  other — LeetCode's Example 2 — and then it returns None, because no")
    print("  node ever has p on one side and q on the other. On unrelated pairs")
    print("  it is correct, so this bug survives any suite omitting that case.")

    print("\n--- a NON-bug: the self-check placed AFTER the recursion ---")
    print("  Writing `if node is p or node is q: return node` BELOW the two")
    print("  recursive calls (instead of as the base case) is still CORRECT —")
    print("  it out-ranks `return left or right`, so p is still passed up. What")
    print("  it loses is the early cut: it explores everything under p first.")
    print(f"  {'p':>3} {'q':>3} {'base-case form':>15} {'after-recursion':>16}  same?")
    same_all = True
    for pv, qv in ((5, 4), (5, 6), (3, 7), (7, 4), (5, 1)):
        root = build(TREE)
        p, q = find(root, pv), find(root, qv)
        a = sol.lowestCommonAncestor(root, p, q)
        b = sol.lca_selfcheck_after_recursion(root, p, q)
        same_all &= (a is b)
        print(f"  {pv:>3} {qv:>3} {str(a.val if a else None):>15} "
              f"{str(b.val if b else None):>16}  {a is b}")
    all_ok &= same_all
    chain_root, chain_nodes = left_chain(600)
    pp, qq = chain_nodes[0], chain_nodes[-1]
    v = [0, 0]

    def visit_base(node):
        if node is None:
            return None
        v[0] += 1
        if node is pp or node is qq:
            return node
        left = visit_base(node.left)
        right = visit_base(node.right)
        if left is not None and right is not None:
            return node
        return left if left is not None else right

    def visit_after(node):
        if node is None:
            return None
        v[1] += 1
        left = visit_after(node.left)
        right = visit_after(node.right)
        if left is not None and right is not None:
            return node
        if node is pp or node is qq:
            return node
        return left if left is not None else right

    visit_base(chain_root)
    visit_after(chain_root)
    print(f"  600-node chain, p = the ROOT: base-case form visits {v[0]} node(s),")
    print(f"  after-recursion form visits {v[1]} — the early cut is a real saving,")
    print("  but it is a saving, not a correctness fix. Both answer p.")
    all_ok &= (v[0] == 1 and v[1] == 600)

    print("\n--- ⚠️  bug: `left or right` -> return node (mistake 4) ---")
    print(f"  {'p':>3} {'q':>3} {'correct':>8} {'or-instead-of-and':>18}")
    or_seen = False
    for pv, qv in ((7, 4), (6, 4), (5, 1)):
        root = build(TREE)
        p, q = find(root, pv), find(root, qv)
        a = sol.lowestCommonAncestor(root, p, q)
        b = sol.lca_broken_return_node(root, p, q)
        or_seen |= a.val != b.val
        print(f"  {pv:>3} {qv:>3} {a.val:>8} {b.val:>18}")
    all_ok &= or_seen
    print("  Every ancestor now claims the answer, so the ROOT always wins — a")
    print("  common ancestor, never the LOWEST one.")

    # ----------------------------------------------------------------------
    # ⚠️ The "node might not exist" follow-up (LC 1644).
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  what if q is NOT in the tree? (LC 1644) ---")
    root = build(TREE)
    ghost = TreeNode(99)                       # a node that is NOT in `root`
    print(f"  tree = {TREE}")
    print(f"  p = node 5 (in the tree), q = node 99 (NOT in the tree)")
    p = find(root, 5)
    plain = sol.lowestCommonAncestor(root, p, ghost)
    counted = sol.lca_may_not_exist(root, p, ghost)
    print(f"  plain LC 236 recursion  -> {plain.val if plain else None}   "
          f"<- a REAL node, and wrong")
    print(f"  counting variant (1644) -> {counted.val if counted else None}   "
          f"<- correct: no such pair")
    bug_shown = (plain is not None and plain.val == 5) and counted is None
    all_ok &= bug_shown
    print(f"  the plain recursion returned p itself: {bug_shown}")
    print("  It found p, found nothing on the other side, and dutifully passed p")
    print("  upward. The return value cannot distinguish 'this is the answer'")
    print("  from 'this is the only thing I found' — which is fine under LC 236's")
    print("  guarantee and wrong without it.")
    print("  Both nodes absent, and both present, for completeness:")
    ghost2 = TreeNode(98)
    c2 = sol.lca_may_not_exist(root, ghost, ghost2)
    c3 = sol.lca_may_not_exist(root, find(root, 7), find(root, 4))
    print(f"    q=99, p=98 (neither exists) -> {c2}")
    print(f"    p=7, q=4  (both exist)      -> {c3.val if c3 else None}")
    all_ok &= (c2 is None and c3 is not None and c3.val == 2)

    print("\n  and the cost of that guarantee: the counting version cannot exit")
    print("  early, so on a chain with p at the TOP it descends the whole tree.")
    chain_root, chain_nodes = left_chain(900)
    p, q = chain_nodes[0], chain_nodes[-1]
    visits = [0, 0]

    def count_plain(node):
        if node is None:
            return None
        visits[0] += 1
        if node is p or node is q:
            return node
        left = count_plain(node.left)
        right = count_plain(node.right)
        if left is not None and right is not None:
            return node
        return left if left is not None else right

    def count_counting(node):
        if node is None:
            return (None, 0)
        visits[1] += 1
        lc, ln = count_counting(node.left)
        rc, rn = count_counting(node.right)
        here = 1 if (node is p or node is q) else 0
        found = ln + rn + here
        if here:
            return (node, found)
        if lc is not None and rc is not None:
            return (node, found)
        return ((lc if lc is not None else rc), found)

    count_plain(chain_root)
    count_counting(chain_root)
    print(f"  900-node chain, p = the ROOT, q = the deepest node:")
    print(f"    plain LC 236 recursion visits {visits[0]} node(s) "
          f"(stops at p immediately)")
    print(f"    counting variant visits       {visits[1]} node(s) "
          f"(must confirm q exists)")
    all_ok &= (visits[0] == 1 and visits[1] == 900)

    # ----------------------------------------------------------------------
    # BST: the ordering invariant changes the problem.
    # ----------------------------------------------------------------------
    print("\n--- LC 235 (BST) vs LC 236 (plain tree): the invariant's payoff ---")
    bst, inorder_nodes = balanced_bst(17)
    n = len(inorder_nodes)
    print(f"  a PERFECT BST with {n} nodes, height 17")
    print(f"  {'p, q (inorder positions)':<26} {'LCA':>8} {'BST steps':>10} "
          f"{'BST us':>9} {'general us':>12} {'general nodes':>14} {'speedup':>9}")
    reps = 10
    for label, i, j in (("adjacent, deepest", 1, 2),
                        ("adjacent, mid-depth", n // 4, n // 4 + 1),
                        ("opposite ends", 1, n - 2)):
        p, q = inorder_nodes[i], inorder_nodes[j]
        t0 = time.perf_counter()
        for _ in range(reps):
            a = sol.lca_bst(bst, p, q)
        t1 = time.perf_counter()
        for _ in range(reps):
            b = sol.lowestCommonAncestor(bst, p, q)
        t2 = time.perf_counter()
        all_ok &= (a is b)
        bst_us = (t1 - t0) / reps * 1e6
        gen_us = (t2 - t1) / reps * 1e6
        steps = 0
        node = bst
        while node is not None:
            steps += 1
            if p.val < node.val and q.val < node.val:
                node = node.left
            elif p.val > node.val and q.val > node.val:
                node = node.right
            else:
                break
        print(f"  {label:<26} {a.val:>8} {steps:>10} {bst_us:>9.2f} "
              f"{gen_us:>12.1f} {n:>14} {gen_us / bst_us:>8.0f}x")
    print("  The BST descent's cost tracks the DEPTH of the answer (1 step when")
    print("  the pair splits at the root, ~17 when it splits at a leaf's parent).")
    print("  The general recursion's cost is the same 131071 nodes every time,")
    print("  because it cannot know where to look.")
    print("  The BST version compares values and DESCENDS; the general version")
    print("  has no way to know which side holds p, so it must be prepared to")
    print("  look everywhere. That is the whole difference between topic 10 and")
    print("  topic 11 in one measurement.")
    print("  ⚠️ And it is not interchangeable: run the BST descent on a NON-BST")
    print("  and it silently returns nonsense —")
    plain_tree = build(TREE)
    pp, qq = find(plain_tree, 7), find(plain_tree, 4)
    wrong = sol.lca_bst(plain_tree, pp, qq)
    right = sol.lowestCommonAncestor(plain_tree, pp, qq)
    print(f"    tree={TREE}, p=7, q=4: BST descent -> "
          f"{wrong.val if wrong else None}, correct -> {right.val}")
    all_ok &= (wrong is None or wrong.val != right.val)

    # ----------------------------------------------------------------------
    # Recursion depth on a legal 10^5 chain.
    # ----------------------------------------------------------------------
    print("\n--- n can be 10^5 and a chain is legal: recursion vs parent map ---")
    print(f"  sys.getrecursionlimit() = {sys.getrecursionlimit()}")
    chain_root, chain_nodes = left_chain(100_000)
    p, q = chain_nodes[50_000], chain_nodes[99_999]
    try:
        r = sol.lowestCommonAncestor(chain_root, p, q)
        rec_msg, died = f"ok -> {r.val}", False
    except RecursionError as exc:
        rec_msg, died = f"{type(exc).__name__}: {exc}", True
    all_ok &= died
    print(f"  recursive postorder  -> {rec_msg}")
    pm = sol.lca_parent_map(chain_root, p, q)
    print(f"  parent map + set     -> ok -> {pm.val}  (expected {p.val}, "
          f"since p is an ancestor of q)")
    all_ok &= (pm is p)
    print("  The parent-map approach is the natural iterative answer, and it is")
    print("  also the right structure when there are MANY queries to answer.")

    # ----------------------------------------------------------------------
    # Randomised cross-check against the O(n^2) oracle, ALL pairs.
    # ----------------------------------------------------------------------
    print("\n--- exhaustive cross-check: every (p, q) pair of random trees ---")
    rng = random.Random(236)
    pairs = 0
    bad = 0
    for _ in range(120):
        root = random_tree(rng.randint(2, 12), rng)
        nodes = all_nodes(root)
        for p in nodes:
            for q in nodes:
                if p is q:
                    continue
                pairs += 1
                want = sol.lca_brute(root, p, q)
                for _name, fn in impls[:4]:
                    got = fn(root, p, q)
                    if got is not want:
                        bad += 1
    all_ok &= (bad == 0)
    print(f"  {pairs} ordered (p, q) pairs across 120 random trees x 4 "
          f"implementations: {bad} mismatches")
    print("  Includes every ancestor/descendant pair, which is the case the")
    print("  broken version above fails on.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
