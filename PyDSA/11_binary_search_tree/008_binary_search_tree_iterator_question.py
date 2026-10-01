"""
================================================================================
QUESTION · LeetCode 173 · Binary Search Tree Iterator                [Medium]
https://leetcode.com/problems/binary-search-tree-iterator/
================================================================================

PROBLEM
-------
Implement the `BSTIterator` class that represents an iterator over the
in-order traversal of a binary search tree (BST):

    BSTIterator(TreeNode root)   Initializes an object of the BSTIterator
                                  class. The `root` of the BST is given as
                                  part of the constructor. The pointer
                                  should be initialized to a non-existent
                                  number smaller than any element in the
                                  BST.
    boolean hasNext()             Returns `true` if there exists a number in
                                  the traversal to the right of the pointer,
                                  otherwise returns `false`.
    int next()                    Moves the pointer to the right, then
                                  returns the number at the pointer.

Notice that by initializing the pointer to a non-existent smallest number,
the first call to `next()` will return the smallest element in the BST.

You may assume that `next()` calls will always be valid — that is, there
will be at least one next number in the in-order traversal when `next()` is
called.


EXAMPLE
-------
Input:
    ["BSTIterator", "next", "next", "hasNext", "next", "hasNext", "next",
     "hasNext", "next", "hasNext"]
    [[[7, 3, 15, null, null, 9, 20]], [], [], [], [], [], [], [], [], []]

Output:
    [null, 3, 7, true, 9, true, 15, true, 20, false]

Explanation:
              7
            ╱   ╲
          3       15
                 ╱   ╲
                9      20

    BSTIterator bSTIterator = new BSTIterator([7, 3, 15, null, null, 9, 20]);
    bSTIterator.next();     // return 3
    bSTIterator.next();     // return 7
    bSTIterator.hasNext();  // return True
    bSTIterator.next();     // return 9
    bSTIterator.hasNext();  // return True
    bSTIterator.next();     // return 15
    bSTIterator.hasNext();  // return True
    bSTIterator.next();     // return 20
    bSTIterator.hasNext();  // return False


CONSTRAINTS
-----------
    The number of nodes in the tree is in the range [1, 10^5].
    0 <= Node.val <= 10^6
    At most 10^5 calls will be made to `hasNext` and `next`.

Follow up: Could you implement `next()` and `hasNext()` to run in average
O(1) time and use O(h) memory, where `h` is the height of the tree?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Problem 007 stopped an in-order traversal early, but it was still ONE
function call that ran to completion or returned. This problem is
different in kind: `next()` is called repeatedly from OUTSIDE, an unknown
number of times, possibly interleaved with other work by the caller. The
traversal has to be PAUSED after producing one value and RESUMED — exactly
where it left off — on the next call.

You cannot use recursion for this directly: a recursive in-order walk has
no way to "return a value now, but remember exactly where I was for next
time" — the call stack would need to be captured and restored, which is
precisely what an EXPLICIT stack (a Python list, not the recursion's call
stack) gives you for free. The stack itself becomes the iterator's saved
state between calls.

Think back to problem 007's iterative in-order pattern: push all left
children, pop one (that's the next in-order value), then push all left
children of its right subtree. The only new idea here is: don't do all of
that inside one function — split it so the constructor primes the stack,
`next()` pops ONE value and re-primes, and `hasNext()` just checks whether
the stack is empty.


PROGRESSIVE HINTS
------------------
Hint 1: The constructor should NOT walk the whole tree and collect every
        value into a list — that defeats the follow-up's O(h) memory bound
        and makes `next()` merely index into a precomputed array (a valid
        but different, worse-memory design — try the O(h) one first).

Hint 2: Keep one field: a stack (Python list) of nodes still "owed" a
        visit — every node on the LEFT SPINE from the current position
        downward.

Hint 3: The constructor pushes the left spine from `root`. `next()` pops
        the top of the stack (that's the answer), and if that node has a
        right child, pushes the ENTIRE left spine of that right child
        before returning.

Hint 4: `hasNext()` needs no traversal at all — the stack is non-empty
        exactly when there is a next value.

Hint 5: For the follow-up ("average O(1) time"), think about it in terms of
        the WHOLE lifetime of the iterator rather than any single call: how
        many times, in total across every `next()` call, is any one node
        pushed onto the stack? Popped?


COMPLEXITY TARGET
------------------
    Time:  O(1) amortized per `next()` call (each node is pushed and
           popped exactly once across the iterator's entire lifetime —
           a single `next()` call can still do up to O(h) work when it
           needs to push a long left spine, but that cost is paid once
           per node, not once per call)
    Space: O(h) for the stack, not O(n) for the whole tree
================================================================================
"""

from collections import deque
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class BSTIterator:
    def __init__(self, root: Optional[TreeNode]):
        # YOUR CODE HERE
        pass

    def next(self) -> int:
        # YOUR CODE HERE
        pass

    def hasNext(self) -> bool:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TEST HELPERS — shared with topic 10; not part of the exercise
# ==============================================================================
def build(values):
    """LeetCode level-order list (with `None` holes) -> root TreeNode."""
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


def run_tests() -> None:
    all_ok = True

    print("--- correctness: full example from the problem statement ---")
    tree = [7, 3, 15, None, None, 9, 20]
    it = BSTIterator(build(tree))
    expected_seq = [
        ("next", 3), ("next", 7), ("hasNext", True), ("next", 9),
        ("hasNext", True), ("next", 15), ("hasNext", True), ("next", 20),
        ("hasNext", False),
    ]
    for op, want in expected_seq:
        got = it.next() if op == "next" else it.hasNext()
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {op}() -> {got}  (want {want})")

    print("\n--- correctness: full in-order sequence matches sorted values ---")
    cases = [
        [7, 3, 15, None, None, 9, 20],
        [1],
        [2, 1, 3],
        [5, 3, 8, 1, 4, 7, 9, 0, 2],
    ]
    for values in cases:
        it = BSTIterator(build(values))
        produced = []
        while it.hasNext():
            produced.append(it.next())
        expected = sorted(v for v in values if v is not None)
        ok = produced == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  tree={values!r:<35} -> "
              f"{produced} (want {expected})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
