"""
================================================================================
SOLUTION · LeetCode 572 · Subtree of Another Tree                       [Easy]
https://leetcode.com/problems/subtree-of-another-tree/
================================================================================

THE CORE IDEA
--------------
"Subtree" means a node together with ALL its descendants — so the question is
not "does this pattern appear somewhere" but "is there a node of `root` from
which the two trees are IDENTICAL". That is problem 007 (Same Tree) called at
every node:

    def isSubtree(root, sub):
        if not root:  return sub is None       # empty root can only host empty sub
        if isSameTree(root, sub):  return True
        return isSubtree(root.left, sub) or isSubtree(root.right, sub)

O(n * m) worst case: one `isSameTree` (O(m)) per node of `root`. O(h) space.
This is COMPOSITION — the entire content of the problem is recognising that
you already solved the hard half in 007, and knowing what it costs.

The alternative is to make it a STRING problem. Serialise both trees and ask
whether one string contains the other:

    return encode(sub) in encode(root)

That is O(n + m) with a linear substring search — and it is a false-positive
factory if the encoding is careless. Two real failures, both measured live
below:

    (a) NO NULL MARKERS. Encode preorder values only:
            root = [1,2]        (1 with a LEFT child 2)   -> "1,2"
            sub  = [1,null,2]   (1 with a RIGHT child 2)  -> "1,2"
        `"1,2" in "1,2"` is True, but `sub` is NOT a subtree of `root`. Without
        markers the encoding is not injective, so containment means nothing.

    (b) MARKERS BUT NO DELIMITER BEFORE EACH VALUE. Encode with `#` for null
        and nothing between values:
            root = [12]  -> "12##"
            sub  = [2]   -> "2##"
        `"2##" in "12##"` is True — the match starts INSIDE the digits of 12.

    The fix is both: a null marker for every empty child AND a delimiter in
    front of every value, so no token can begin mid-token:
            encode(None)  = ",#"
            encode(node)  = ",{val}" + encode(left) + encode(right)
        Now root=[12] gives ",12,#,#" and sub=[2] gives ",2,#,#", which is not
        a substring of it. Verified below on both false-positive cases and
        cross-checked against the recursive answer on thousands of random
        trees.

One more honesty note about the O(n + m) claim: `sub_str in root_str` in
CPython is a tuned two-way/Crochemore-Perrin hybrid, not a guaranteed-linear
KMP, so "O(n + m)" for the string route really means "O(n + m) with KMP or a
rolling hash; CPython's `in` is fast in practice". If an interviewer presses
on the guarantee, KMP is the answer to name.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (WRONG): check that every value of `sub` appears somewhere in
`root`, or that `sub`'s preorder is a sub-LIST of `root`'s preorder. Both
ignore the "and all its descendants" clause and the shape. Fails Example 2,
where node 4's subtree merely has one extra node.

Approach 1 (composition: isSameTree at every node) ✅ — the shape above.
   O(n * m) worst case, O(h) space. Lead with this: it is short, obviously
   correct, and reuses 007.

Approach 2 (serialise + substring search) ✅ — O(n + m) time and space with
   a proper encoding and a linear search. Give it as the follow-up when asked
   to beat O(n * m), and volunteer the delimiter/marker pitfall — that is what
   distinguishes someone who has *implemented* it from someone who has heard
   of it.

Approach 3 (prune by value before comparing) — only call `isSameTree` at
   nodes whose value equals `sub.val`. Same O(n * m) worst case (a tree of
   identical values defeats it), but a large constant-factor win on real
   inputs. Cheap, honest optimisation; the demo measures it.

Approach 4 (compare (height, hash) pairs / Merkle hashing) — compute a hash
   of each subtree bottom-up, and compare `sub`'s hash against every node's.
   O(n + m) expected, no string building, but it is a probabilistic answer
   unless you verify a hit with a real `isSameTree` call. Worth naming for a
   "what if the trees are huge and you must be fast" follow-up.

Approach 5 (prune by subtree SIZE and height) — a subtree match requires
   equal size and equal height, both computable in one O(n) pass. Reduces the
   candidate set to nodes that could possibly match; still O(n * m) worst
   case, but it turns the adversarial "all values identical" input from
   quadratic into near-linear when the sizes differ.


================================================================================
STEP BY STEP TRACE — root = [3,4,5,1,2], sub = [4,1,2]
================================================================================
            3                      4
          ╱   ╲                  ╱   ╲
         4     5                1     2
        ╱ ╲
       1   2

    isSubtree(3, sub)
      isSameTree(3, 4)         -> False   (3 != 4)
      isSubtree(4, sub)
        isSameTree(4, 4)
          vals equal
          isSameTree(1, 1) -> True
          isSameTree(2, 2) -> True
          -> True                          <- found it, `or` short-circuits
      -> True

    Now Example 2, where node 2 has an extra child 0:

    isSubtree(4, sub)
      isSameTree(4, 4)
        isSameTree(1, 1) -> True
        isSameTree(2, 2)
          vals equal
          isSameTree(0, None) -> False     <- one side empty: shapes differ
          -> False
        -> False
      isSubtree(1, sub) -> ... False
      isSubtree(2, sub) -> ... False
      -> False

    The single line that makes Example 2 come out False is `if not p or not q:
    return False` inside isSameTree. "All its descendants" is enforced by the
    STRUCTURE check, not by anything in this file.

    And the string route on the [12] vs [2] pair:

        encode with markers only : "12##"      contains  "2##"    -> True  ✗
        encode with delimiters    : ",12,#,#"   contains  ",2,#,#"? -> False ✓


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time         Space      Mutates?  Note
    -----------------------------  -----------  ---------  --------  -------------
    Values/sublist matching        O(n + m)     O(n + m)   no        WRONG ANSWER
    isSameTree at every node ✅    O(n * m)     O(h)       no        the answer
    + prune on root.val == sub.val O(n * m)     O(h)       no        same bound,
                                                                       big constant win
    Serialise + substring ✅       O(n + m)*    O(n + m)   no        needs markers AND
                                                                       delimiters
    Merkle / subtree hashing       O(n + m)     O(n)       no        probabilistic
                                                                       unless verified
    Prune on (size, height)        O(n * m)     O(n)       no        kills the
                                                                       adversarial input

    * with KMP or a rolling hash. CPython's `in` is not a linear-time
      guarantee, though it is very fast in practice.

    The O(n * m) worst case is real, not theoretical: `root` = a chain of
    2000 nodes all valued 1, `sub` = a chain of 1000 nodes all valued 1 plus
    one extra child at the bottom. Every node of `root` looks like a match for
    999 comparisons and then fails. The demo builds exactly that and measures
    the composition against the string route.


================================================================================
EDGE CASES
================================================================================
    sub is None              -> True by convention (the empty tree is a subtree
                                 of anything). LeetCode's constraints say
                                 m >= 1, so it never tests this — but your code
                                 must not crash if it does. `if not root:
                                 return sub is None` handles both ends.
    root is None, sub is not  -> False.
    root == sub               -> True: a tree is a subtree of itself.
    [1,1] with sub [1]         -> True, matched at the CHILD, not the root. A
                                 solution that only checks the root passes
                                 nothing; one that forgets to check the root
                                 fails `root == sub`.
    [12] with sub [2]          -> False. THE test case for the string route.
    [1,2] vs [1,null,2]        -> False. The other string-route test case.
    all values identical        -> the O(n * m) worst case; also where value
                                 pruning stops helping.
    subtree present TWICE       -> True; the `or` returns at the first hit.


================================================================================
COMMON MISTAKES
================================================================================
1. Matching a PATTERN rather than a whole subtree: accepting Example 2 because
   `[4,1,2]` "is in there". The definition includes every descendant.
2. Writing `isSameTree(root, sub) or isSubtree(...)` but forgetting the
   `if not root` base case, so a `None` root reaches `isSameTree` and then
   `root.left` raises AttributeError.
3. `if not root: return False` instead of `return sub is None` — technically
   fine under LeetCode's m >= 1 constraint, wrong in general, and it hides the
   question of what "empty subtree" means. Say the convention out loud.
4. Serialising WITHOUT null markers and using substring search. Produces
   false positives (demo (a) below), and the failing input is small enough
   that an interviewer will produce it instantly.
5. Serialising with markers but WITHOUT a delimiter before each value: `[2]`
   matches inside `[12]` (demo (b)). Multi-digit and negative values make this
   fire on ordinary inputs.
6. Building the serialisation with `str +=` inside the recursion. That is
   O(n^2) string copying in the general case and quietly destroys the O(n + m)
   claim you just made. Append to a list and `"".join` once.
7. Comparing `str(root)` / `repr(root)` — object addresses, not structure.
8. Claiming O(n + m) for the string route without qualifying the substring
   search. `in` is not KMP.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you do better than O(n * m)?
A: Yes — serialise both trees with null markers and delimiters, then run a
   linear substring search (KMP). O(n + m). Then immediately mention the
   false-positive pitfalls, because that is the part that gets it wrong in
   practice.

Q: Why does the naive serialisation fail?
A: Because it is not injective: two different trees can encode to the same
   string ([1,2] vs [1,null,2]), and a token can start mid-token ([2] inside
   [12]). Markers fix the first, delimiters the second.

Q: What if values can be arbitrary strings rather than ints?
A: Then the delimiter must be a character that cannot appear in a value, or
   you length-prefix each value (`3:abc`) — the same problem as LC 271
   Encode/Decode Strings, and the same fix.

Q: Avoid building strings entirely.
A: Merkle-style subtree hashing: hash each subtree from the bottom up as
   `hash((val, left_hash, right_hash))`, then compare `sub`'s hash against
   every node's. O(n + m) expected; verify a hit with `isSameTree` to make it
   exact.

Q: What if you must answer many queries against the same `root`?
A: Precompute the serialisation (or the hash map from subtree-hash to nodes)
   once in O(n), then each query costs O(m). This is the case where the string
   route clearly wins.

Q: Same question but for a general (non-binary, unordered) tree?
A: The subtree isomorphism problem — much harder, because children have no
   fixed order; canonical hashing (sort children's hashes) is the usual tool.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
    LC 100   Same Tree                    — the subroutine (007 here)
    LC 101   Symmetric Tree               — crossed pairing (012 here)
    LC 297   Serialize and Deserialize    — the lossless encoding (019 here)
    LC 271   Encode and Decode Strings    — the delimiter problem, standalone
    LC 652   Find Duplicate Subtrees      — serialise every subtree into a dict
    LC 1367  Linked List in Binary Tree   — the same "match at every node" shape
    LC 28    Find the Index of the First Occurrence in a String — KMP itself
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
    # Approach 1 — composition on problem 007.
    # ------------------------------------------------------------------
    def isSubtree(self, root: Optional[TreeNode],
                  subRoot: Optional[TreeNode]) -> bool:
        """isSameTree at every node. O(n*m) worst case, O(h) space."""
        if not root:
            return subRoot is None
        if self.isSameTree(root, subRoot):
            return True
        return (self.isSubtree(root.left, subRoot)
                or self.isSubtree(root.right, subRoot))

    def isSameTree(self, p: Optional[TreeNode], q: Optional[TreeNode]) -> bool:
        """Problem 007, verbatim."""
        if not p and not q:
            return True
        if not p or not q:
            return False
        if p.val != q.val:
            return False
        return (self.isSameTree(p.left, q.left)
                and self.isSameTree(p.right, q.right))

    # ------------------------------------------------------------------
    # Approach 3 — same bound, prune on the root value.
    # ------------------------------------------------------------------
    def isSubtree_pruned(self, root: Optional[TreeNode],
                         subRoot: Optional[TreeNode]) -> bool:
        """Only compare where the values already agree. Still O(n*m) worst
        case; much cheaper on inputs whose values are varied."""
        if subRoot is None:
            return True
        if not root:
            return False
        if root.val == subRoot.val and self.isSameTree(root, subRoot):
            return True
        return (self.isSubtree_pruned(root.left, subRoot)
                or self.isSubtree_pruned(root.right, subRoot))

    # ------------------------------------------------------------------
    # Approach 2 — serialise and search. The encoding is the whole problem.
    # ------------------------------------------------------------------
    def isSubtree_serialised(self, root: Optional[TreeNode],
                             subRoot: Optional[TreeNode]) -> bool:
        """Lossless encoding + substring search. O(n+m) with a linear search;
        CPython's `in` is fast but not a linear guarantee."""
        return self.encode(subRoot) in self.encode(root)

    @staticmethod
    def encode(node: Optional[TreeNode]) -> str:
        """Preorder, a `#` for every empty child, and a `,` BEFORE every
        value so no token can start mid-token. Built with join, not +=."""
        out: List[str] = []

        def walk(nd: Optional[TreeNode]) -> None:
            if nd is None:
                out.append(",#")
                return
            out.append(f",{nd.val}")
            walk(nd.left)
            walk(nd.right)

        walk(node)
        return "".join(out)

    # ------------------------------------------------------------------
    # Approach 2b — the same idea with a guaranteed-linear search (KMP).
    # ------------------------------------------------------------------
    def isSubtree_kmp(self, root: Optional[TreeNode],
                      subRoot: Optional[TreeNode]) -> bool:
        """Serialise, then KMP: O(n + m) guaranteed, not just in practice."""
        text, pattern = self.encode(root), self.encode(subRoot)
        if not pattern:
            return True
        # KMP failure function
        fail = [0] * len(pattern)
        k = 0
        for i in range(1, len(pattern)):
            while k and pattern[i] != pattern[k]:
                k = fail[k - 1]
            if pattern[i] == pattern[k]:
                k += 1
            fail[i] = k
        # scan
        k = 0
        for ch in text:
            while k and ch != pattern[k]:
                k = fail[k - 1]
            if ch == pattern[k]:
                k += 1
                if k == len(pattern):
                    return True
        return False

    # ------------------------------------------------------------------
    # Approach 4 — Merkle hashing, verified on a hit.
    # ------------------------------------------------------------------
    def isSubtree_hashed(self, root: Optional[TreeNode],
                         subRoot: Optional[TreeNode]) -> bool:
        """Hash every subtree bottom-up; compare hashes, then confirm with a
        real structural comparison so the answer stays exact."""
        if subRoot is None:
            return True
        if not root:
            return False

        target = self._subtree_hash(subRoot)
        found = False

        def walk(node: Optional[TreeNode]) -> int:
            nonlocal found
            if node is None:
                return hash(None)
            h = hash((node.val, walk(node.left), walk(node.right)))
            if h == target and self.isSameTree(node, subRoot):
                found = True
            return h

        walk(root)
        return found

    def _subtree_hash(self, node: Optional[TreeNode]) -> int:
        if node is None:
            return hash(None)
        return hash((node.val,
                     self._subtree_hash(node.left),
                     self._subtree_hash(node.right)))

    # ------------------------------------------------------------------
    # Deliberate breakage — the two false-positive encodings.
    # ------------------------------------------------------------------
    @staticmethod
    def encode_no_markers(node: Optional[TreeNode]) -> str:
        """✗ BROKEN ON PURPOSE — preorder values, comma-separated, no null
        markers. Not injective: different trees encode identically."""
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
    def encode_no_delimiter(node: Optional[TreeNode]) -> str:
        """✗ BROKEN ON PURPOSE — null markers but no delimiter before values,
        so a match can begin in the middle of a number."""
        out: List[str] = []

        def walk(nd):
            if nd is None:
                out.append("#")
                return
            out.append(f"{nd.val}")
            walk(nd.left)
            walk(nd.right)

        walk(node)
        return "".join(out)

    def isSubtree_broken_no_markers(self, root, subRoot) -> bool:
        return self.encode_no_markers(subRoot) in self.encode_no_markers(root)

    def isSubtree_broken_no_delimiter(self, root, subRoot) -> bool:
        return self.encode_no_delimiter(subRoot) in self.encode_no_delimiter(root)

    def isSubtree_broken_values_only(self, root, subRoot) -> bool:
        """✗ BROKEN ON PURPOSE — "every value of sub appears in root"."""
        def vals(node, acc):
            if node:
                acc.append(node.val)
                vals(node.left, acc)
                vals(node.right, acc)
            return acc
        return set(vals(subRoot, [])) <= set(vals(root, []))


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


def build_skewed(n, side="left", val=None):
    if n == 0:
        return None
    root = TreeNode(0 if val is None else val)
    curr = root
    for i in range(1, n):
        node = TreeNode(i if val is None else val)
        if side == "left":
            curr.left = node
        else:
            curr.right = node
        curr = node
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


def all_nodes(root):
    out, stack = [], [root] if root else []
    while stack:
        node = stack.pop()
        out.append(node)
        if node.left:
            stack.append(node.left)
        if node.right:
            stack.append(node.right)
    return out


def deep_copy(node):
    if node is None:
        return None
    return TreeNode(node.val, deep_copy(node.left), deep_copy(node.right))


# ==============================================================================
# TESTS — run:  python 008_subtree_of_another_tree_solution.py
# ==============================================================================
CASES = [
    ([3, 4, 5, 1, 2], [4, 1, 2], True),
    ([3, 4, 5, 1, 2, None, None, None, None, 0], [4, 1, 2], False),
    ([1, 1], [1], True),
    ([1], [1], True),
    ([1, 2], [1, None, 2], False),
    ([12], [2], False),
    ([1, 2, 3], [1, 2, 3], True),
    ([1, 2, 3], [2], True),
    ([1, 2, 3], [4], False),
    ([3, 4, 5, 1, 2], [3, 4, 5, 1, 2], True),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: composition (isSameTree at every node) ---")
    for rv, sv, want in CASES:
        got = sol.isSubtree(build(rv), build(sv))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  root={rv!r:<40} sub={sv!r:<14} -> "
              f"{got}  (want {want})")

    print("\n--- correctness: pruned, serialised, KMP, hashed ---")
    impls = [
        ("pruned on root.val ", sol.isSubtree_pruned),
        ("serialised + `in`  ", sol.isSubtree_serialised),
        ("serialised + KMP   ", sol.isSubtree_kmp),
        ("Merkle hash + verify", sol.isSubtree_hashed),
    ]
    for name, fn in impls:
        ok = all(fn(build(rv), build(sv)) == want for rv, sv, want in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # ----------------------------------------------------------------------
    # ⚠️  FALSE POSITIVE (a): serialisation without null markers.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo (a): serialising WITHOUT null markers ---")
    root, sub = build([1, 2]), build([1, None, 2])
    print(f"  root = [1,2]        (1 with a LEFT child 2)")
    print(f"  sub  = [1,null,2]   (1 with a RIGHT child 2)")
    print(f"  encode_no_markers(root) = {Solution.encode_no_markers(root)!r}")
    print(f"  encode_no_markers(sub)  = {Solution.encode_no_markers(sub)!r}")
    fp_a = sol.isSubtree_broken_no_markers(root, sub)
    truth_a = sol.isSubtree(root, sub)
    print(f"  substring test -> {fp_a}   <- FALSE POSITIVE")
    print(f"  the truth       -> {truth_a}")
    print(f"  with markers+delimiters: {Solution.encode(sub)!r} in "
          f"{Solution.encode(root)!r} -> {sol.isSubtree_serialised(root, sub)}")
    all_ok &= (fp_a is True and truth_a is False
               and sol.isSubtree_serialised(root, sub) is False)

    # ----------------------------------------------------------------------
    # ⚠️  FALSE POSITIVE (b): markers but no delimiter.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo (b): null markers but NO delimiter before values ---")
    root, sub = build([12]), build([2])
    print(f"  root = [12]   sub = [2]")
    print(f"  encode_no_delimiter(root) = "
          f"{Solution.encode_no_delimiter(root)!r}")
    print(f"  encode_no_delimiter(sub)  = "
          f"{Solution.encode_no_delimiter(sub)!r}")
    fp_b = sol.isSubtree_broken_no_delimiter(root, sub)
    truth_b = sol.isSubtree(root, sub)
    print(f"  substring test -> {fp_b}   <- FALSE POSITIVE (the match starts "
          f"inside '12')")
    print(f"  the truth       -> {truth_b}")
    print(f"  with a delimiter: {Solution.encode(sub)!r} in "
          f"{Solution.encode(root)!r} -> {sol.isSubtree_serialised(root, sub)}")
    all_ok &= (fp_b is True and truth_b is False
               and sol.isSubtree_serialised(root, sub) is False)

    print("\n--- ⚠️  live demo (c): 'every value of sub appears in root' ---")
    root, sub = build([3, 4, 5, 1, 2, None, None, None, None, 0]), build([4, 1, 2])
    print(f"  Example 2 (node 2 has an extra child 0)")
    print(f"  value-containment test -> {sol.isSubtree_broken_values_only(root, sub)}"
          f"   <- WRONG")
    print(f"  structural answer      -> {sol.isSubtree(root, sub)}")
    print("  'Subtree' includes EVERY descendant, so an extra node anywhere")
    print("  below the match point disqualifies it. Only a structural")
    print("  comparison enforces that.")
    all_ok &= (sol.isSubtree_broken_values_only(root, sub) is True
               and sol.isSubtree(root, sub) is False)

    # ----------------------------------------------------------------------
    # Randomised hunt: how often does each broken encoding lie?
    # ----------------------------------------------------------------------
    # Values 0..12: single-digit AND two-digit values, so the no-delimiter
    # encoding gets a chance to match "2" inside "12". With only 0..2 (all
    # single digits) that bug can never trigger, and this check used to fail.
    print("\n--- randomised: 4000 (root, sub) pairs, values 0-12, "
          "how often is each version wrong? ---")
    rng = random.Random(572)
    counts = {"no markers": 0, "no delimiter": 0, "values only": 0}
    checked = 0
    for _ in range(4000):
        root = random_tree(rng.randint(1, 10), rng, vals=13)
        nodes = all_nodes(root)
        if rng.random() < 0.5 and nodes:
            sub = deep_copy(rng.choice(nodes))      # guaranteed real subtree
        else:
            sub = random_tree(rng.randint(1, 4), rng, vals=13)
        truth = sol.isSubtree(root, sub)
        checked += 1
        if sol.isSubtree_broken_no_markers(root, sub) != truth:
            counts["no markers"] += 1
        if sol.isSubtree_broken_no_delimiter(root, sub) != truth:
            counts["no delimiter"] += 1
        if sol.isSubtree_broken_values_only(root, sub) != truth:
            counts["values only"] += 1
    for label, wrong in counts.items():
        print(f"  {label:<14} wrong on {wrong:>5} / {checked} pairs "
              f"({100 * wrong / checked:.1f}%)")
    print("  These are not exotic inputs — small trees over three distinct")
    print("  values are enough to break every shortcut. The correct encoding")
    print("  agreed with the recursion on all of them (checked next).")
    all_ok &= all(v > 0 for v in counts.values())

    print("\n--- randomised cross-check: the four CORRECT implementations agree ---")
    rng = random.Random(9)
    mismatches = 0
    trials = 3000
    for _ in range(trials):
        root = random_tree(rng.randint(1, 14), rng, vals=3)
        nodes = all_nodes(root)
        if rng.random() < 0.5 and nodes:
            sub = deep_copy(rng.choice(nodes))
        else:
            sub = random_tree(rng.randint(1, 5), rng, vals=3)
        want = sol.isSubtree(root, sub)
        if any(fn(root, sub) != want for _, fn in impls):
            mismatches += 1
    print(f"  {trials} random pairs: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # RUNTIME: the O(n*m) worst case, built on purpose.
    # ----------------------------------------------------------------------
    print("\n--- measured: the O(n*m) worst case vs O(n+m) ---")
    print("  root = a LEFT chain of 2000 nodes, every value 1")
    print("  sub  = a LEFT chain of 1000 nodes, every value 1, plus one extra")
    print("         right child at the bottom, so it never matches")
    saved = sys.getrecursionlimit()
    sys.setrecursionlimit(60_000)
    try:
        root = build_skewed(2000, "left", val=1)
        sub = build_skewed(1000, "left", val=1)
        node = sub
        while node.left:
            node = node.left
        node.right = TreeNode(1)                 # the poison pill

        timings = {}
        for label, fn in (("composition", sol.isSubtree),
                          ("pruned on val", sol.isSubtree_pruned),
                          ("serialised `in`", sol.isSubtree_serialised),
                          ("serialised KMP", sol.isSubtree_kmp),
                          ("Merkle hash", sol.isSubtree_hashed)):
            t0 = time.perf_counter()
            result = fn(root, sub)
            timings[label] = ((time.perf_counter() - t0) * 1000, result)
        print(f"  {'approach':<18} {'result':>7} {'time':>12}")
        for label, (ms, result) in timings.items():
            print(f"  {label:<18} {str(result):>7} {ms:>10.2f}ms")
        comp_ms = timings["composition"][0]
        ser_ms = timings["serialised `in`"][0]
        print(f"  composition / serialised = {comp_ms / ser_ms:.0f}x")
        print("  Every value is 1, so pruning on `root.val == sub.val` prunes")
        print("  nothing — the pruned version is just as quadratic here. The")
        print("  string route reads each tree once and hands the repeated-prefix")
        print("  problem to the substring search, which is exactly what KMP's")
        print("  failure function is for.")
        all_ok &= all(result is False for _, result in timings.values())

        print("\n  ... and on a VARIED-value tree, where pruning does help:")
        bench_rng = random.Random(7)
        root = random_tree(20_000, bench_rng, vals=1000)
        sub = deep_copy(all_nodes(root)[-1])      # a real subtree, deep down
        for label, fn in (("composition", sol.isSubtree),
                          ("pruned on val", sol.isSubtree_pruned),
                          ("serialised `in`", sol.isSubtree_serialised),
                          ("Merkle hash", sol.isSubtree_hashed)):
            t0 = time.perf_counter()
            result = fn(root, sub)
            ms = (time.perf_counter() - t0) * 1000
            print(f"  {label:<18} {str(result):>7} {ms:>10.2f}ms")
    finally:
        sys.setrecursionlimit(saved)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
