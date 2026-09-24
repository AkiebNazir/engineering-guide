"""
================================================================================
SOLUTION · LeetCode 297 · Serialize and Deserialize Binary Tree        [Hard]
https://leetcode.com/problems/serialize-and-deserialize-binary-tree/
================================================================================

THE CORE IDEA
--------------
Preorder traversal (root, then left, then right) visits a node BEFORE either
of its subtrees. That single fact is what makes reconstruction possible: the
first unconsumed token in a preorder stream is always "the next thing to
build", so a decoder can read the stream left to right, in lock-step with how
it was written, and never needs to look ahead or backtrack.

But preorder values ALONE are not enough — you also need to know where a
subtree ENDS. Write an explicit marker (e.g. "#") for every missing child and
the ambiguity disappears: reading one token now tells you unconditionally
whether you just consumed a dead end (marker -> this subtree is empty, return)
or a real node (value -> build it, then recursively consume its left subtree
out of the SAME stream, then its right subtree out of whatever's left after
that). This is topic guide Part 2.1's whole point, and it's exactly what
problem 008's serialization sub-story needed for substring search — this
problem needs the same two ingredients (null markers + a delimiter) but for
full round-trip reconstruction instead of "does one string contain another".

    encode(None)  = "#,"
    encode(node)  = "{val},"  + encode(node.left) + encode(node.right)

Decoding shares a single cursor across all recursive calls (an index, or an
iterator) — not a value copy — because the calls must consume the token
stream in the exact order it was produced. See the Go topic guide
(`GoDSA/10_trees/_TOPIC_GUIDE.md`, Part 7) for a full Go implementation of
this exact algorithm; the shape below is the same idea in Python.

WHY INORDER ALONE CANNOT DO THIS
---------------------------------
Preorder always puts the root FIRST, so decoding always knows where to start.
Inorder puts the root somewhere in the MIDDLE (left subtree, then root, then
right subtree) with no marker telling you where the split is — many different
trees share the same inorder sequence. Demonstrated live below: two
structurally different trees both produce inorder [1, 2, 3].


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (BFS / level-order, like LeetCode's own display) ✅ — encode
   level by level with `collections.deque` (topic guide Part 3 / topic 07),
   writing "null" for every missing child, e.g. "1,2,3,null,null,4,5". This
   is literally what LeetCode's UI shows you when it prints a tree. Decode by
   walking the same queue-driven process in reverse: pop a value, attach it
   to the next parent waiting for a child. Correct and simple, but its "null"
   spelling costs more bytes per empty child than preorder+null's
   single-character marker, and on trees with a wide live level followed by
   mostly-empty levels it also emits more TOKENS than preorder+null needs
   (measured below on a right-chain tree, where token counts tie but BFS
   still costs more characters).

Approach 1 (preorder + null markers, recursive) ✅ — THE PRIMARY SOLUTION.
   One preorder pass to encode (O(n)), one linear scan with a shared cursor
   to decode (O(n)). Implemented in full as `Codec` below.

Approach 2 (preorder + inorder, no markers needed) — a follow-up-relevant
   fact, not implemented in depth here: if you already have BOTH a preorder
   and an inorder listing of the SAME tree, and there are no duplicate
   values, you can reconstruct without any null markers at all — the preorder
   root splits the inorder sequence into left/right subtrees exactly as
   problem 016 (Construct Binary Tree from Preorder and Inorder Traversal)
   does. The catch: you'd have to WRITE both orders to reconstruct from them,
   which is more bytes than preorder+markers for the equivalent information,
   so this is really "what LC 105 already solved", named here as the
   connection, not a serialization scheme worth adopting for its own sake.

Approach 3 (preorder + null markers, ITERATIVE with an explicit stack) ✅ —
   ties to topic guide §2.2's recursion-limit warning. Encode with an
   explicit stack instead of the call stack; decode by pushing placeholder
   "pending" nodes and filling in children as tokens arrive. Implemented in
   full below, and used to survive a chain deep enough to blow the recursive
   version's stack (measured below, not asserted).


================================================================================
THE PITFALL DEMONSTRATIONS — the whole point of this file
================================================================================
Demo (a) — LONE LEFT vs LONE RIGHT, no null markers
    root = [1,2]        1 with a LEFT child 2
    sub  = [1,None,2]   1 with a RIGHT child 2

    A naive encoder that just lists preorder VALUES with no marker for a
    missing child produces "1,2" for BOTH trees — there is no way to tell,
    from "1,2" alone, whether the 2 belongs on the left or the right. Built,
    run, and the ACTUAL wrong round-trip is printed below.

Demo (b) — delimiter pitfall, values 12 and 2
    Null markers alone are not enough either: if there's no delimiter
    separating tokens, "12" followed by two null markers and "2" followed by
    two null markers can become ambiguous once concatenated character-by-
    character (exactly the [12] vs [2] case from problem 008, adapted here to
    full round-trip serialize/deserialize instead of substring search). Built,
    run, and the actual wrong output is printed below.

The FIX for both: a null marker for EVERY empty child, AND a delimiter so
tokens of different lengths never collide once concatenated. The `Codec`
below survives both cases via an actual serialize -> deserialize ->
structural-compare round-trip, PASS/FAIL printed live.


================================================================================
STEP BY STEP TRACE — [1,2,3,null,null,4,5]
================================================================================
            1
          ╱   ╲
         2      3
              ╱   ╲
             4      5

ENCODE (preorder, "#" for every empty child):
    visit 1 -> "1,"
      visit 2 -> "2,"
        visit 2.left  (None) -> "#,"
        visit 2.right (None) -> "#,"
      visit 3 -> "3,"
        visit 4 -> "4,"
          visit 4.left  (None) -> "#,"
          visit 4.right (None) -> "#,"
        visit 5 -> "5,"
          visit 5.left  (None) -> "#,"
          visit 5.right (None) -> "#,"

    token stream:  1,2,#,#,3,4,#,#,5,#,#,

DECODE — a single shared cursor `idx` advances token by token:

    idx=0  read "1"  -> build node(1)
             idx=1  read "2"  -> build node(2), this is node(1).left
                       idx=2  read "#" -> None, this is node(2).left;  idx=3
                       idx=3  read "#" -> None, this is node(2).right; idx=4
             idx=4  read "3"  -> build node(3), this is node(1).right
                       idx=5  read "4"  -> build node(4), this is node(3).left
                                idx=6  read "#" -> None (4.left);  idx=7
                                idx=7  read "#" -> None (4.right); idx=8
                       idx=8  read "5"  -> build node(5), this is node(3).right
                                idx=9  read "#" -> None (5.left);  idx=10
                                idx=10 read "#" -> None (5.right); idx=11
    idx=11, stream exhausted -> reconstructed tree matches the original.

Note the shape of the recursion: `node.left = decode()` runs to completion
(consuming however many tokens node 2's ENTIRE left subtree needs) BEFORE
`node.right = decode()` even starts reading — that ordering is exactly why a
SHARED, mutating cursor (not a value copied into each call) is required.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          serialize        deserialize      Mutates?
    ------------------------------    --------------   --------------   --------
    BFS / level-order                 O(n) time/space  O(n) time/space  no
    Preorder + null, recursive ✅     O(n) time/space  O(n) time/space  no
    Preorder + null, iterative ✅     O(n) time/space  O(n) time/space  no
    Preorder + inorder (no markers)   O(n) time, O(n)   O(n^2) worst      no
                                       space (2 lists)   case naive split
                                                          (O(n) with a
                                                          value->index map,
                                                          see 016)

    Recursive space also carries an O(h) CALL-STACK cost on top of the O(n)
    output — O(log n) balanced, O(n) skewed (this is exactly what the
    recursion-limit demo below hits). The iterative version's stack lives on
    the heap instead and pays the same O(h) bound without touching Python's
    C call-stack limit.


================================================================================
EDGE CASES
================================================================================
    root = None                 -> serialize must emit *something*
                                 deserialize can read back as None; tested.
    single node                 -> "5,#,#," round-trips to one node, no
                                 children.
    negative / zero values      -> "-3" and "0" must not collide with the
                                 marker "#" or the delimiter ",". Using "#"
                                 (not a digit or "-") as the marker and ","
                                 as the delimiter keeps both safe; tested
                                 with a tree containing 0 and negative values.
    duplicate values throughout -> the encoding never relies on VALUES being
                                 distinct, only on POSITION in the stream, so
                                 duplicates cause no ambiguity; tested with a
                                 tree of all-0 values.
    deeply skewed / chain tree  -> the case that breaks recursive encode and
                                 decode via Python's call-stack limit; the
                                 iterative version is built specifically to
                                 survive it (measured below).


================================================================================
COMMON MISTAKES
================================================================================
1. No null markers — preorder VALUES alone are ambiguous. [1,2] (left child)
   and [1,null,2] (right child) both serialize to "1,2" without markers, and
   there is no way to decode which side 2 belongs on (demo (a) below).
2. Markers but no delimiter between tokens — multi-digit or negative values
   can collide once concatenated (demo (b) below; the same [12] vs [2] trap
   as problem 008, here breaking a full round-trip instead of a substring
   search).
3. Assuming ANY single traversal order suffices. Inorder alone reconstructs
   nothing — many different trees share one inorder sequence (demonstrated
   live below with two concretely different 3-node trees).
4. Building the output string with `+=` in a loop instead of appending to a
   list and `"".join`-ing once. Only worth stating as a real cost if actually
   measured to matter at the sizes tested — see the runtime demo below, which
   checks this rather than asserting it.
5. Off-by-one / index bugs in the shared-cursor deserializer: advancing the
   cursor at the wrong point (e.g. incrementing before reading, or reading
   `node.right`'s tokens before `node.left`'s finish being consumed) misaligns
   every subsequent subtree. The trace above exists specifically to make the
   correct order concrete.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Serialize an N-ary tree (children is a list, not left/right)?
A: Same idea, one extra piece of information: after each value, also write
   the CHILD COUNT (or a single end-of-children marker), since "how many
   children follow" isn't fixed at 2 anymore. Preorder + null markers'
   "always know when a subtree ends" property still carries over — LC 428.

Q: Make the encoding more compact for a mostly-full tree?
A: For a NEAR-COMPLETE tree, BFS/level-order with implicit index-based
   parent/child math (child of i at 2i+1/2i+2, like a heap) needs no markers
   or delimiters at all for the "live" nodes — but it degrades badly the
   moment the tree isn't complete (exactly what the sparse-tree demo below
   shows for plain level-order). A middle ground: preorder + null markers,
   but store an index (varint-encoded) instead of nulls at the shape gaps.

Q: Handle non-integer / string values?
A: The delimiter must be a character guaranteed absent from any value, or
   switch to length-prefixing each token ("3:abc") — same fix LC 271
   (Encode and Decode Strings) uses, since a plain comma delimiter breaks the
   moment a string value can legally contain a comma.

Q: Streaming / incremental deserialization (can't hold the whole string)?
A: Feed tokens to the same recursive-descent decoder one at a time from a
   generator/iterator instead of a pre-split list — the shared-cursor idea is
   unchanged, only its source becomes lazy. The recursion still needs the
   tree's height in stack frames, so pair this with the iterative decoder for
   very deep trees.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
    LC 105   Construct Binary Tree from Preorder and Inorder Traversal
             (016 here) — reconstruction WITHOUT null markers, using two
             traversal orders together instead.
    LC 572   Subtree of Another Tree (008 here) — the sibling pitfall: the
             SAME null-marker + delimiter lessons, applied to substring
             search instead of full round-trip reconstruction.
    LC 449   Serialize and Deserialize BST — a simpler variant: a BST's
             INORDER is sorted, so preorder ALONE (no markers at all) is
             enough to rebuild it, because "insert values in preorder order
             into a BST" recreates the same shape. Only a fact worth naming
             here, not implemented — this problem's tree has no ordering
             guarantee, so markers are mandatory.
    LC 428   Serialize and Deserialize N-ary Tree — see follow-up above.
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


NULL_MARKER = "#"
DELIM = ","


class Codec:
    """Approach 1 — preorder + null markers, recursive. THE ANSWER."""

    def serialize(self, root: Optional[TreeNode]) -> str:
        """Preorder: root, left, right. A '#' token for every empty child.
        Built as a list and joined once, not with string '+='."""
        out: List[str] = []

        def walk(node: Optional[TreeNode]) -> None:
            if node is None:
                out.append(NULL_MARKER)
                return
            out.append(str(node.val))
            walk(node.left)
            walk(node.right)

        walk(root)
        return DELIM.join(out)

    def deserialize(self, data: str) -> Optional[TreeNode]:
        """A single shared cursor into the token list — recursive calls
        consume the stream in the exact order it was written."""
        tokens = data.split(DELIM)
        idx = [0]  # box, so the nested function can mutate it without `nonlocal`

        def build() -> Optional[TreeNode]:
            tok = tokens[idx[0]]
            idx[0] += 1
            if tok == NULL_MARKER:
                return None
            node = TreeNode(int(tok))
            node.left = build()
            node.right = build()
            return node

        return build()


# ------------------------------------------------------------------
# Approach 0 — BFS / level-order, like LeetCode's own display format.
# ------------------------------------------------------------------
class CodecBFS:
    def serialize(self, root: Optional[TreeNode]) -> str:
        if root is None:
            return ""
        out: List[str] = []
        q = deque([root])
        while q:
            node = q.popleft()
            if node is None:
                out.append("null")
                continue
            out.append(str(node.val))
            q.append(node.left)
            q.append(node.right)
        return DELIM.join(out)

    def deserialize(self, data: str) -> Optional[TreeNode]:
        if not data:
            return None
        tokens = data.split(DELIM)
        root = TreeNode(int(tokens[0]))
        q = deque([root])
        i = 1
        while q and i < len(tokens):
            node = q.popleft()
            if i < len(tokens) and tokens[i] != "null":
                node.left = TreeNode(int(tokens[i]))
                q.append(node.left)
            i += 1
            if i < len(tokens) and tokens[i] != "null":
                node.right = TreeNode(int(tokens[i]))
                q.append(node.right)
            i += 1
        return root


# ------------------------------------------------------------------
# Approach 3 — preorder + null markers, ITERATIVE with an explicit stack.
# Survives trees too deep for the recursive version (measured below).
# ------------------------------------------------------------------
class CodecIterative:
    def serialize(self, root: Optional[TreeNode]) -> str:
        out: List[str] = []
        stack = [root]
        while stack:
            node = stack.pop()
            if node is None:
                out.append(NULL_MARKER)
                continue
            out.append(str(node.val))
            stack.append(node.right)  # push right first so left is processed
            stack.append(node.left)   # first -> preserves preorder ON OUTPUT
        return DELIM.join(out)

    def deserialize(self, data: str) -> Optional[TreeNode]:
        tokens = iter(data.split(DELIM))

        def next_tok():
            return next(tokens)

        root_tok = next_tok()
        if root_tok == NULL_MARKER:
            return None
        root = TreeNode(int(root_tok))
        # each stack entry: (node, "left"|"right") = which child slot is
        # still pending on that node, consumed in preorder-matching order.
        # Only ONE pending entry is ever created per node per slot — a
        # child's own subtree is pushed as (child, "left") and expands
        # itself as it's processed, never pre-pushed by its parent.
        stack = [(root, "left")]
        while stack:
            node, slot = stack.pop()
            tok = next_tok()
            child = None
            if tok != NULL_MARKER:
                child = TreeNode(int(tok))
            setattr(node, slot, child)
            if slot == "left":
                stack.append((node, "right"))  # this node still needs a right
            if child is not None:
                stack.append((child, "left"))  # start the child's own subtree
        return root


# ------------------------------------------------------------------
# Deliberate breakage — the two false-positive encodings (demos a, b).
# ------------------------------------------------------------------
class CodecNoMarkers:
    """BROKEN ON PURPOSE — preorder VALUES only, no null markers."""

    def serialize(self, root: Optional[TreeNode]) -> str:
        out: List[str] = []

        def walk(node):
            if node is None:
                return
            out.append(str(node.val))
            walk(node.left)
            walk(node.right)

        walk(root)
        return DELIM.join(out)

    def deserialize(self, data: str) -> Optional[TreeNode]:
        """No way to know which values were left-children vs right-children,
        so this naively (and wrongly) always attaches the next value as a
        LEFT child, building a left-only chain."""
        if not data:
            return None
        tokens = data.split(DELIM)
        root = TreeNode(int(tokens[0]))
        curr = root
        for tok in tokens[1:]:
            curr.left = TreeNode(int(tok))
            curr = curr.left
        return root


class CodecNoDelimiter:
    """BROKEN ON PURPOSE — null markers present, but NO delimiter between
    tokens, so multi-digit values can be misread once concatenated."""

    def serialize(self, root: Optional[TreeNode]) -> str:
        out: List[str] = []

        def walk(node):
            if node is None:
                out.append(NULL_MARKER)
                return
            out.append(str(node.val))
            walk(node.left)
            walk(node.right)

        walk(root)
        return "".join(out)  # <- no delimiter

    def deserialize(self, data: str) -> Optional[TreeNode]:
        """Reads ONE CHARACTER at a time, so any value >= 10 is sliced into
        separate single-digit tokens instead of staying whole."""
        idx = [0]

        def build():
            ch = data[idx[0]]
            idx[0] += 1
            if ch == NULL_MARKER:
                return None
            node = TreeNode(int(ch))
            node.left = build()
            node.right = build()
            return node

        return build()


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


def same_tree(p, q):
    if p is None and q is None:
        return True
    if p is None or q is None:
        return False
    return (p.val == q.val
            and same_tree(p.left, q.left)
            and same_tree(p.right, q.right))


def build_chain(n, val_fn=lambda i: i):
    """A left-only chain of n nodes: 0 -> 1 -> 2 -> ... (n-1), each via .left."""
    if n == 0:
        return None
    root = TreeNode(val_fn(0))
    curr = root
    for i in range(1, n):
        curr.left = TreeNode(val_fn(i))
        curr = curr.left
    return root


CASES = [
    [1, 2, 3, None, None, 4, 5],
    [],
    [1],
    [1, 2],
    [1, None, 2],
    [5, 4, 7, 3, None, 2, None, -1, None, 9],
    [0, 0, 0, 0, 0],
    [-1, -2, -3],
    [12, 2, None, None, 120],
]


def run_tests() -> None:
    codec = Codec()
    bfs = CodecBFS()
    itr = CodecIterative()
    all_ok = True

    # ----------------------------------------------------------------------
    # Correctness: recursive Codec round-trips every hand-picked case.
    # ----------------------------------------------------------------------
    print("--- correctness: preorder + null markers, recursive ---")
    for values in CASES:
        root = build(values)
        data = codec.serialize(root)
        back = codec.deserialize(data)
        got = to_level_order(back)
        ok = same_tree(root, back)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  values={values!r:<45} "
              f"encoded={data!r:<30} roundtrip={got!r}")

    # ----------------------------------------------------------------------
    # Cross-check: BFS and iterative implementations agree with the answer.
    # ----------------------------------------------------------------------
    print("\n--- cross-check: BFS and iterative Codecs agree with the recursive one ---")
    for name, impl in [("BFS/level-order", bfs), ("iterative (stack)", itr)]:
        ok_all = True
        for values in CASES:
            root = build(values)
            back = impl.deserialize(impl.serialize(root))
            if not same_tree(root, back):
                ok_all = False
        all_ok &= ok_all
        print(f"{'PASS' if ok_all else 'FAIL'}  {name} round-trips all "
              f"{len(CASES)} cases")

    # ----------------------------------------------------------------------
    # ⚠️  Demo (a): lone LEFT vs lone RIGHT child, no null markers.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  demo (a): no null markers -> lone-left vs lone-right ambiguity ---")
    broken = CodecNoMarkers()
    left_only = build([1, 2])         # 1 with a LEFT child 2
    right_only = build([1, None, 2])  # 1 with a RIGHT child 2
    enc_left = broken.serialize(left_only)
    enc_right = broken.serialize(right_only)
    print(f"  left_only  = [1,2]        -> no-marker encoding: {enc_left!r}")
    print(f"  right_only = [1,null,2]   -> no-marker encoding: {enc_right!r}")
    print(f"  SAME STRING: {enc_left == enc_right}")
    decoded_from_right = broken.deserialize(enc_right)
    got_shape = to_level_order(decoded_from_right)
    print(f"  decoding right_only's own string back -> {got_shape!r} "
          f"(want [1,null,2], a RIGHT child)")
    print(f"  the naive decoder always builds a LEFT-only chain, so it silently "
          f"returns the WRONG tree for right_only")
    fixed_left = codec.deserialize(codec.serialize(left_only))
    fixed_right = codec.deserialize(codec.serialize(right_only))
    print(f"  with null markers: left_only round-trips correctly = "
          f"{same_tree(left_only, fixed_left)}, "
          f"right_only round-trips correctly = "
          f"{same_tree(right_only, fixed_right)}")
    assert enc_left == enc_right, "demo (a) setup: encodings should collide"
    assert got_shape != [1, None, 2], "demo (a): naive decode should be wrong"
    assert same_tree(left_only, fixed_left) and same_tree(right_only, fixed_right)

    # ----------------------------------------------------------------------
    # ⚠️  Demo (b): delimiter pitfall, values 12 and 2.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  demo (b): null markers but NO delimiter -> 12 vs 2 collide ---")
    broken_delim = CodecNoDelimiter()
    twelve = build([12])
    two = build([2])
    enc_twelve = broken_delim.serialize(twelve)
    enc_two = broken_delim.serialize(two)
    print(f"  tree=[12] -> no-delimiter encoding: {enc_twelve!r}")
    print(f"  tree=[2]  -> no-delimiter encoding: {enc_two!r}")
    try:
        decoded_twelve = broken_delim.deserialize(enc_twelve)
        got_val = decoded_twelve.val if decoded_twelve else None
        broke = False
    except IndexError as e:
        got_val = None
        broke = True
        print(f"  decoding {enc_twelve!r} back -> IndexError: {e} "
              f"(the decoder read '1' as node.val, then '2' as a LEFT child,")
        print(f"    consuming the two real '#' markers as 2's children, then "
              f"ran off the end of the string looking for 1's right subtree)")
    if not broke:
        print(f"  decoding {enc_twelve!r} back -> root.val = {got_val!r} "
              f"(want 12, got a single digit because the decoder reads ONE "
              f"CHARACTER at a time)")
    fixed_twelve = codec.deserialize(codec.serialize(twelve))
    print(f"  with a delimiter: root.val = {fixed_twelve.val!r} (correct)")
    assert broke or got_val != 12, "demo (b): naive single-char decode should be wrong"
    assert fixed_twelve.val == 12

    # ----------------------------------------------------------------------
    # ⚠️  Inorder alone is ambiguous: two different trees, same inorder.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  inorder ALONE cannot reconstruct: two different trees, same inorder ---")

    def inorder(node, out):
        if node is None:
            return
        inorder(node.left, out)
        out.append(node.val)
        inorder(node.right, out)

    tree_a = build([2, 1, 3])   # balanced: 1 and 3 are children of 2
    tree_b = build([1, None, 2, None, 3])  # a right-only chain 1 -> 2 -> 3

    in_a, in_b = [], []
    inorder(tree_a, in_a)
    inorder(tree_b, in_b)
    print(f"  tree_a = [2,1,3]                (balanced)      inorder = {in_a}")
    print(f"  tree_b = [1,null,2,null,3]      (right chain)   inorder = {in_b}")
    print(f"  same inorder sequence: {in_a == in_b}")
    print(f"  same shape:            {same_tree(tree_a, tree_b)}")
    print("  inorder alone cannot tell these apart; preorder+null markers can,")
    print("  because preorder always records the root BEFORE its subtrees.")
    assert in_a == in_b and not same_tree(tree_a, tree_b)

    # ----------------------------------------------------------------------
    # Measured: BFS vs preorder+null token count on a SPARSE (right-chain) tree.
    # ----------------------------------------------------------------------
    print("\n--- measured: BFS vs preorder+null token count on a sparse "
          "(20-node right-chain) tree ---")
    sparse = TreeNode(1)
    curr = sparse
    for v in range(2, 21):
        curr.right = TreeNode(v)
        curr = curr.right
    bfs_str = bfs.serialize(sparse)
    pre_str = codec.serialize(sparse)
    bfs_tokens = bfs_str.split(DELIM)
    pre_tokens = pre_str.split(DELIM)
    print(f"  BFS/level-order   : {len(bfs_tokens)} tokens, {len(bfs_str)} chars")
    print(f"  preorder+null     : {len(pre_tokens)} tokens, {len(pre_str)} chars")
    print(f"  On this shape both encodings need the SAME number of tokens "
          f"({len(bfs_tokens)} each — every node still needs exactly one "
          f"null for its missing left child either way), but BFS's token is "
          f"the word 'null' (4 chars) where preorder's is '#' (1 char), so "
          f"BFS costs {len(bfs_str) - len(pre_str)} more characters "
          f"({len(bfs_str)} vs {len(pre_str)}) for the identical tree — a "
          f"marker-spelling cost here, not a wasted-node cost. BFS's real "
          f"token-count waste shows up on a tree with a wide LIVE level "
          f"followed by mostly-empty levels below it, where it must still "
          f"emit a null for every dead slot at the next level down before it "
          f"can stop, while preorder's null costs exactly one token per "
          f"empty child, no matter the tree's shape.")
    all_ok &= (bfs.deserialize(bfs_str) and same_tree(sparse, bfs.deserialize(bfs_str)))

    # ----------------------------------------------------------------------
    # Measured: recursion-limit failure on a deep chain, iterative survives it.
    # ----------------------------------------------------------------------
    print("\n--- measured: recursive Codec vs a deep chain, at Python's "
          "DEFAULT recursion limit ---")
    default_limit = sys.getrecursionlimit()
    print(f"  sys.getrecursionlimit() on this machine = {default_limit}")

    def try_recursive(n):
        try:
            root = build_chain(n)
            data = codec.serialize(root)
            codec.deserialize(data)
            return True
        except RecursionError:
            return False

    def same_tree_iterative(p, q):
        """Non-recursive structural compare — needed here because a deep
        enough chain would blow up plain recursive `same_tree` too, and
        that would defeat the point of this exact demo."""
        stack = [(p, q)]
        while stack:
            a, b = stack.pop()
            if a is None and b is None:
                continue
            if a is None or b is None or a.val != b.val:
                return False
            stack.append((a.left, b.left))
            stack.append((a.right, b.right))
        return True

    # Find the boundary LIVE on this machine/call stack, rather than
    # hardcoding a number measured elsewhere — the exact N that breaks
    # depends on how many frames are already on the stack when this file
    # runs (a standalone script vs. nested inside run_tests() differ by a
    # handful of frames), so hardcoding would silently go stale.
    n_break = None
    for n in range(100, 5001, 100):
        if not try_recursive(n):
            n_break = n
            break
    assert n_break is not None, "expected SOME n to break the recursive Codec"
    n_ok = n_break - 100
    ok_result = try_recursive(n_ok)
    break_result = try_recursive(n_break)
    print(f"  recursive Codec on a {n_ok}-node chain  -> "
          f"{'succeeded' if ok_result else 'RecursionError'}")
    print(f"  recursive Codec on a {n_break}-node chain -> "
          f"{'succeeded' if break_result else 'RecursionError'}")

    root_break = build_chain(n_break)
    itr_data = itr.serialize(root_break)
    itr_back = itr.deserialize(itr_data)
    itr_ok = same_tree_iterative(root_break, itr_back)
    print(f"  iterative Codec on that SAME {n_break}-node chain -> "
          f"{'PASS, round-tripped correctly' if itr_ok else 'FAIL'}")
    all_ok &= (ok_result is True and break_result is False and itr_ok is True)

    # ----------------------------------------------------------------------
    # Randomised cross-check: recursive and iterative Codecs agree, at scale.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check: recursive vs iterative Codec, "
          "1000 random trees ---")
    import random

    def random_tree(n, rng, vals=50):
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

    rng = random.Random(297)
    mismatches = 0
    trials = 1000
    for _ in range(trials):
        root = random_tree(rng.randint(0, 30), rng)
        rec_back = codec.deserialize(codec.serialize(root))
        it_back = itr.deserialize(itr.serialize(root))
        if not same_tree(root, rec_back) or not same_tree(root, it_back):
            mismatches += 1
    print(f"  {trials} random trees: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # Measured: does list-append+join beat str += at these sizes?
    # ----------------------------------------------------------------------
    print("\n--- measured: list-append+join vs str += for serialize, "
          "on a 20,000-node random tree ---")

    def serialize_join(root):
        out = []

        def walk(node):
            if node is None:
                out.append(NULL_MARKER)
                return
            out.append(str(node.val))
            walk(node.left)
            walk(node.right)

        walk(root)
        return DELIM.join(out)

    def serialize_plusequals(root):
        s = [""]

        def walk(node):
            if node is None:
                s[0] += NULL_MARKER + DELIM
                return
            s[0] += str(node.val) + DELIM
            walk(node.left)
            walk(node.right)

        walk(root)
        return s[0][:-1]

    big_rng = random.Random(11)
    big = random_tree(20_000, big_rng, vals=1000)
    saved_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(60_000)
    try:
        t0 = time.perf_counter()
        s1 = serialize_join(big)
        t_join = (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter()
        s2 = serialize_plusequals(big)
        t_plus = (time.perf_counter() - t0) * 1000
        print(f"  list-append + join : {t_join:8.2f} ms  ({len(s1)} chars)")
        print(f"  str +=             : {t_plus:8.2f} ms  ({len(s2)} chars)")
        same_output = (s1 == s2)
        print(f"  identical output: {same_output}")
        if t_plus > t_join * 1.3:
            print(f"  join is faster here ({t_plus / t_join:.2f}x) — measured, "
                  f"not assumed.")
        else:
            print(f"  NOT a measurable win at this size on this machine "
                  f"({t_plus / t_join:.2f}x) — CPython's `s = s + x` in-place "
                  f"optimisation (refcount==1) keeps str += competitive here; "
                  f"see CONTEXT.md's note on this exact trap. Prefer join "
                  f"anyway for the guarantee, not a speed claim.")
        all_ok &= same_output
    finally:
        sys.setrecursionlimit(saved_limit)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
