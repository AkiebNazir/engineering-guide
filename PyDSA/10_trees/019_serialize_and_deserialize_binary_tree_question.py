"""
================================================================================
QUESTION · LeetCode 297 · Serialize and Deserialize Binary Tree        [Hard]
https://leetcode.com/problems/serialize-and-deserialize-binary-tree/
================================================================================

Serialization is the process of converting a data structure or object into a
sequence of bits so that it can be stored in a file or memory buffer, or
transmitted across a network connection link to be reconstructed later in the
same or another computer environment.

Design an algorithm to serialize and deserialize a binary tree. There is no
restriction on how your serialization/deserialization algorithm should work.
You just need to ensure that a binary tree can be serialized to a string and
this string can be deserialized to the original tree structure.

--------------------------------------------------------------------------------
EXAMPLE 1
--------------------------------------------------------------------------------
Input:  root = [1,2,3,null,null,4,5]

            1
          ╱   ╲
         2      3
              ╱   ╲
             4      5

Your Codec's serialize(root) can produce any string you like (LeetCode's own
UI happens to show "1,2,3,null,null,4,5" as ONE example, not a requirement).
Calling deserialize(serialize(root)) must return a tree that is structurally
identical to the original — same shape, same values at the same positions.

--------------------------------------------------------------------------------
EXAMPLE 2
--------------------------------------------------------------------------------
Input:  root = []
Output: []
(The empty tree must round-trip too.)

--------------------------------------------------------------------------------
CONSTRAINTS
--------------------------------------------------------------------------------
    The number of nodes in the tree is in the range [0, 10^4].
    -1000 <= Node.val <= 1000

--------------------------------------------------------------------------------
HINTS (progressive — try not to read past the one you need)
--------------------------------------------------------------------------------
1. You get to choose the string format. What information do you need in it to
   rebuild not just the VALUES but the exact SHAPE?

2. Any single traversal that just lists non-null values loses the shape.
   `[1,2]` (1 with a left child 2) and `[1,null,2]` (1 with a right child 2)
   both have the preorder value-sequence "1,2" if you don't record nulls.
   Reconstruction from "1,2" alone is ambiguous — which side did 2 go on?

3. Preorder traversal (root, then left, then right) has a special property:
   the root always comes before its own subtrees in the stream. If you ALSO
   write an explicit marker (e.g. "#") for every missing child, the stream
   becomes unambiguous — decoding can read one token at a time and always
   knows whether it just saw a leaf-that-continues or a dead end.

4. That's the same lesson problem 008 (Subtree of Another Tree) needed for
   substring search: a null marker for every empty child, so different trees
   never produce the same token sequence. Here you need one more thing that
   008 also needed: a delimiter in front of (or between) every token, so that
   multi-digit or negative values never collide once concatenated — is "12"
   followed by "#" the same characters as "1" followed by "2#"? Choose your
   separator so no token can be misread as a prefix or suffix of another.

5. Deserializing needs a single shared "position in the stream" that
   advances as you consume tokens — a plain array index (or an iterator)
   works. Read one token: if it's the marker, this subtree is empty; the
   caller doesn't build a node here and returns; otherwise it's a value, and
   the just-consumed value's node gets its LEFT subtree from continuing to
   read the NEXT tokens, then its RIGHT subtree from continuing to read
   whatever tokens are next after that (recursively).

--------------------------------------------------------------------------------
YOUR TASK
--------------------------------------------------------------------------------
LeetCode's actual class name for this problem is `Codec` (not `Solution`).
Implement:

    class Codec:
        def serialize(self, root):   # Encode a tree to a single string.
            ...

        def deserialize(self, data):  # Decode your encoded data to tree.
            ...

serialize and deserialize must be inverses of each other: for any tree,
`deserialize(serialize(root))` must be structurally identical to `root`.
================================================================================
"""

from collections import deque
from typing import List, Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Codec:
    def serialize(self, root: Optional[TreeNode]) -> str:
        """Encode a tree to a single string."""
        # YOUR CODE HERE
        pass

    def deserialize(self, data: str) -> Optional[TreeNode]:
        """Decode your encoded data to tree."""
        # YOUR CODE HERE
        pass


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


CASES = [
    [1, 2, 3, None, None, 4, 5],
    [],
    [1],
    [1, 2],
    [1, None, 2],
    [5, 4, 7, 3, None, 2, None, -1, None, 9],
    [0, 0, 0, 0, 0],
    [-1, -2, -3],
]


def run_tests() -> None:
    codec = Codec()
    all_ok = True
    for values in CASES:
        root = build(values)
        data = codec.serialize(root)
        back = codec.deserialize(data)
        got = to_level_order(back)
        ok = same_tree(root, back)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  values={values!r:<45} "
              f"roundtrip={got!r}")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
