"""
================================================================================
SOLUTION · LeetCode 108 · Convert Sorted Array to BST                   [Easy]
https://leetcode.com/problems/convert-sorted-array-to-binary-search-tree/
================================================================================

THE CORE IDEA
--------------
A sorted array is exactly the in-order traversal of the BST you are being
asked for (topic guide §2 — the one big idea). Building the tree is
inverting that mapping, and the only decision at each step is "which element
is the root of this slice?"

**Take the middle one.** Then the left half (all smaller) becomes the left
subtree and the right half (all larger) becomes the right subtree, and both
sides get the same number of elements +/- 1 — which is precisely the
definition of height-balanced, applied recursively.

    def sortedArrayToBST(nums):
        def build(lo, hi):                  # closed range [lo, hi]
            if lo > hi:
                return None
            mid = (lo + hi) // 2
            node = TreeNode(nums[mid])
            node.left = build(lo, mid - 1)
            node.right = build(mid + 1, hi)
            return node
        return build(0, len(nums) - 1)

O(n) time — one node per element, O(1) work each. O(log n) recursion depth.
Note the `mid` computation is exactly topic 05's, and for the same reason:
splitting a sorted range down the middle. The difference is that topic 05
throws one half away and this keeps both.


================================================================================
WHY THE MIDPOINT IS THE ONLY BALANCING CHOICE
================================================================================
Any index could legally be the root — the BST invariant is satisfied by
"everything left of i" and "everything right of i" whichever i you pick.
What changes is the SHAPE:

    nums = [1,2,3,4,5,6,7]

    root = nums[0] (leftmost)        root = nums[mid] ✅
      1                                     4
       ╲                                  ╱   ╲
        2                                2     6
         ╲                              ╱ ╲   ╱ ╲
          3                            1   3 5   7
           ╲
            4                          height 3 = ceil(log2(8))
             ╲
              5                        height difference at every node <= 1
               ╲
                6
                 ╲
                  7

      height 7 == n. Still a valid
      BST! But not height-balanced,
      so it FAILS this problem.

Height with the midpoint is ceil(log2(n+1)); the demo below measures both
for n up to 8191 and confirms the leftmost-root build really does give
height == n.


================================================================================
THE ANSWER IS NOT UNIQUE — AND THE TESTS MUST NOT PRETEND IT IS
================================================================================
For an EVEN-length slice there is no single middle element. Both choices
balance:

    nums = [1,2,3]                nums = [1,2]
    mid=(0+2)//2=1 -> root 2      LEFT-mid  (lo+hi)//2      = 0 -> root 1
        2                             1                  height 2
       ╱ ╲                             ╲
      1   3                             2

                                  RIGHT-mid (lo+hi+1)//2    = 1 -> root 2
                                      2                  height 2
                                     ╱
                                    1

`(lo + hi) // 2` floors, giving the left-mid; `(lo + hi + 1) // 2` gives the
right-mid. LeetCode's judge for 108 is a special judge that accepts ANY
height-balanced BST, and the tests in this file behave the same way. They
assert three PROPERTIES instead of one shape:

    1. in-order traversal of the result == the input array
       (proves it is a BST AND that no element was lost or duplicated)
    2. height-balanced: |height(left) - height(right)| <= 1 at EVERY node
    3. height == ceil(log2(n+1))  (the minimum possible, a bonus check)

Property 1 is worth pausing on: because the input is strictly increasing,
"in-order == input" is a complete BST validity check on its own — that is
problem 006's second technique, reused here as an oracle.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive, price it and reject it): insert each element into an
initially empty BST with problem 003's insert. Sorted input, so every insert
goes to the rightmost leaf: O(n^2) time and a chain of height n. Wrong
answer AND quadratic. Named here because it is the reflex answer.

Approach 1 (index recursion) ✅ — the answer above. O(n) time, O(log n)
stack.

Approach 2 (slice recursion) — the same code with `build(nums[:mid])` and
`build(nums[mid+1:])`. Correct, but each level copies O(n) elements across
its slices, so it ALLOCATES O(n log n) total instead of O(n). Measured on
this machine (demo 3): the copy count really is n·log2(n) — 1,468,946
elements copied at n = 100,000, i.e. 14.7x n against log2(n) = 16.6 — while
the index version copies exactly zero.

Two honest caveats the demo turned up, both worth saying out loud rather
than bluffing past:
  · The wall-clock penalty is only ~1.2-1.4x, not the order of magnitude
    the asymptotics suggest, because a Python list slice is a C-level
    memcpy of pointers while allocating n TreeNode objects dominates both
    runs. Sell slicing's flaw as "allocates O(n log n)", not "much slower".
  · PEAK resident memory is only ~1.08x, because sibling slices are freed
    as the recursion unwinds — the slices alive along one path sum to
    n/2 + n/4 + ... = O(n). Total allocation O(n log n) and peak space O(n)
    are different claims and both are true.

Two more subtleties this variant exposes:
  · `len(nums) // 2` picks the RIGHT middle (index L//2), whereas
    `(lo + hi) // 2` on [0, L-1] picks the LEFT middle ((L-1)//2). So the
    slicing version builds a different (equally valid) tree from the index
    version, which will look like a bug in your own cross-check if you
    have not internalised "the answer is not unique".

Approach 3 (iterative, explicit stack) — push `(parent, side, lo, hi)`
triples instead of recursing. Same complexity; the only reason to write it
is to dodge the recursion limit, which n <= 10^4 never comes close to since
the depth is log2(10^4) ~= 14. Not worth the complexity here (contrast with
problem 001, where the depth really can be n).


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [-10, -3, 0, 5, 9]     indices 0..4

build(0,4)  mid=2  -> node(0)
    build(0,1)  mid=0  -> node(-10)
        build(0,-1) -> None                 (lo > hi)
        build(1,1)  mid=1 -> node(-3)
            build(1,0) -> None
            build(2,1) -> None
        so -10.right = -3
    build(3,4)  mid=3  -> node(5)
        build(3,2) -> None
        build(4,4)  mid=4 -> node(9)
        so 5.right = 9

Result:
              0
            ╱   ╲
        -10       5
           ╲        ╲
            -3        9

    level-order: [0, -10, 5, None, -3, None, 9]
    in-order:    [-10, -3, 0, 5, 9]  == the input ✅
    heights:     left subtree 2, right subtree 2 -> balanced ✅

(LeetCode's example prints [0,-3,9,-10,null,5], a DIFFERENT tree, because
their reference solution takes the right-mid. Both are accepted.)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time         Space (aux)   Mutates input?  Note
    --------------------------  -----------  ------------  --------------  ------------
    Repeated BST insert          O(n^2)       O(n) stack    no              WRONG shape
                                                                            (chain), too slow
    Index recursion ✅            O(n)         O(log n)      no              the answer
    Slice recursion              O(n)*        O(n) peak     no              ALLOCATES
                                                                            O(n log n) total;
                                                                            counted below
    Iterative + explicit stack   O(n)         O(log n)      no              same cost, more
                                                                            code

    * Slice recursion's time is O(n log n) by element count but measured at
      only 1.2-1.4x the index version on this machine — the node allocation
      dominates. Its peak space is O(n) (siblings are freed on unwind) even
      though total allocation is O(n log n). Do not conflate the two.
    The O(n) for the tree itself is unavoidable output size, and is excluded
    from the "Space (aux)" column above.
    "Mutates input?" is `no` for all of them — the array is only read, and
    it is worth saying so, because 003/004 (insert/delete) DO mutate.


================================================================================
EDGE CASES
================================================================================
    []              -> None. (LeetCode guarantees n >= 1, but `lo > hi` is the
                        recursion's own base case, so empty must work anyway.)
    [x]             -> a single node, both children None.
    [1,2]           -> the even-length case: two valid answers, both height 2.
                        Any test comparing to one fixed shape is broken here.
    n = 2^k - 1     -> a perfect tree; height == log2(n+1) exactly, no slack.
    n = 2^k         -> one level is partially filled; still balanced.
    all negatives    -> nothing special, but confirms no 0/positive assumption.
    duplicates in input -> outside this problem's constraints ("strictly
                        increasing"); with duplicates the in-order check still
                        passes but the tree's invariant needs a documented
                        tie-breaking side (see 006).


================================================================================
COMMON MISTAKES
================================================================================
1. Slicing (`nums[:mid]`, `nums[mid+1:]`) instead of passing indices. Not
   wrong, but it allocates O(n log n) elements for zero benefit — and if
   you then claim "the same complexity", that is the part interviewers
   push on. Measured here: 1.47M elements copied at n = 100,000, vs 0.

2. Off-by-one between the closed convention `[lo, hi]` with base case
   `lo > hi`, and the half-open `[lo, hi)` with base case `lo >= hi`. Mixing
   them (closed range, `lo >= hi` base) drops the last element of every
   slice — the tree comes out missing values, and only an in-order check
   catches it.

3. `node.left = build(lo, mid)` instead of `build(lo, mid - 1)` — includes
   `mid` in its own left subtree, which is either infinite recursion or a
   duplicated value.

4. Building by repeated insertion (Approach 0) and reporting it as O(n log n)
   "because BST insert is log n". On SORTED input every insert is O(depth)
   and the depth grows by one each time: that is O(n^2) total, and the demo
   proves it.

5. Writing a test that expects one exact level-order list and calling the
   other valid answer a failure. Test the properties.

6. Claiming the result is "a balanced BST" without saying which definition —
   height-balanced (this problem, AVL's definition) is not the same as
   weight-balanced or perfectly balanced.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: The input is a sorted LINKED LIST, not an array (LC 109).
A: You cannot index to the middle in O(1) any more. Two options:
   (a) copy the list into an array first, then this exact solution —
       O(n) time, O(n) extra space, and honestly the answer I would ship;
   (b) the elegant one: build the tree in-order, left-to-right, while
       walking the list forward with one shared pointer. Recurse over the
       COUNT of nodes (lo/hi as ordinals), build the left subtree first, then
       consume the current list node as the root, then the right subtree.
       O(n) time, O(log n) space, and it never needs random access — it
       relies on the fact that in-order construction and list order are the
       same order, which is the topic's big idea once more.

Q: Turn an arbitrary unbalanced BST into a balanced one (LC 1382).
A: In-order traverse to a sorted array (O(n)), then run this exact
   algorithm. That two-step "flatten and rebuild" is the standard answer and
   is why 108 matters beyond itself. The alternative, in-place Day-Stout-
   Warren algorithm, does it in O(n) time and O(1) space via rotations —
   worth naming.

Q: Why does a real database not rebuild like this?
A: Rebuilding is O(n) and takes the whole structure offline. Self-balancing
   trees (AVL, red-black) pay O(log n) per insert to keep the invariant
   incrementally, which is what you want for a live workload.

Q: Can you make it iterative?
A: Yes — push `(parent, which_side, lo, hi)` on an explicit stack. Not
   needed at n <= 10^4 (depth ~14) but a fair question.

Q: What is the minimum possible height for n nodes?
A: ceil(log2(n+1)). The tests below assert the built tree hits it exactly.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Pattern 4 of the topic guide's taxonomy: build-from-sorted-input.

    LC 109  Convert Sorted List to BST     — same idea, no random access
    LC 1382 Balance a Binary Search Tree   — in-order flatten + this
    LC 105  Build Tree from Preorder+Inorder — the general inverse-traversal
                                              problem (topic 10); 108 is the
                                              special case where in-order
                                              alone suffices because sorted
    LC 106  Build Tree from Inorder+Postorder — same family
    LC 449  Serialize and Deserialize BST   — a BST needs only ONE traversal to
                                              rebuild, unlike LC 297 for a
                                              plain tree; 108's logic in disguise
    LC 95   Unique Binary Search Trees II   — enumerate ALL BSTs over 1..n,
                                              i.e. every root choice, not just mid
    LC 96   Unique Binary Search Trees      — count them (Catalan numbers)
================================================================================
"""

import math
import random
import time
import tracemalloc
from collections import deque
from typing import List, Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def sortedArrayToBST(self, nums: List[int]) -> Optional[TreeNode]:
        """✅ THE ANSWER — index recursion, left-mid. O(n) time, O(log n) stack."""
        def helper(lo: int, hi: int) -> Optional[TreeNode]:
            if lo > hi:                       # closed range [lo, hi]
                return None
            mid = (lo + hi) // 2              # floors -> the LEFT middle
            node = TreeNode(nums[mid])
            node.left = helper(lo, mid - 1)
            node.right = helper(mid + 1, hi)
            return node

        return helper(0, len(nums) - 1)

    # ------------------------------------------------------------------
    # Variants.
    # ------------------------------------------------------------------
    def sortedArrayToBST_rightmid(self, nums: List[int]) -> Optional[TreeNode]:
        """Equally correct: takes the RIGHT middle on even-length slices.
        Produces a DIFFERENT tree, also height-balanced. Exists to prove the
        answer is not unique."""
        def helper(lo: int, hi: int) -> Optional[TreeNode]:
            if lo > hi:
                return None
            mid = (lo + hi + 1) // 2          # ceils -> the RIGHT middle
            node = TreeNode(nums[mid])
            node.left = helper(lo, mid - 1)
            node.right = helper(mid + 1, hi)
            return node

        return helper(0, len(nums) - 1)

    def sortedArrayToBST_slicing(self, nums: List[int]) -> Optional[TreeNode]:
        """Correct, but copies the array at every level of the recursion.
        NOTE `len(nums) // 2` on a slice of length L is index L//2, which is
        the RIGHT middle — while `(lo + hi) // 2` on the closed range
        [0, L-1] is (L-1)//2, the LEFT middle. So this variant reproduces
        sortedArrayToBST_rightmid's tree, NOT sortedArrayToBST's. Same
        balance property, different shape. Cross-checked against the right
        one below; getting that cross-check wrong is how you convince
        yourself of a bug that is not there."""
        if not nums:
            return None
        mid = len(nums) // 2
        node = TreeNode(nums[mid])
        node.left = self.sortedArrayToBST_slicing(nums[:mid])
        node.right = self.sortedArrayToBST_slicing(nums[mid + 1:])
        return node

    def sortedArrayToBST_leftmost_root(self, nums: List[int]) -> Optional[TreeNode]:
        """✗ WRONG for this problem (correct BST, not height-balanced): always
        takes the FIRST element as the root. Kept to demonstrate that the
        midpoint choice is what buys the balance."""
        root = None
        tail = None
        for v in nums:                        # equivalent to the recursion,
            node = TreeNode(v)                # written iteratively so it does
            if root is None:                  # not blow the stack at n=8191
                root = tail = node
            else:
                tail.right = node
                tail = node
        return root

    def sortedArrayToBST_by_insertion(self, nums: List[int]) -> Optional[TreeNode]:
        """✗ WRONG shape and O(n^2) time: insert the sorted values one by one
        into an empty BST. Each insert walks the whole existing right spine."""
        root = None
        for v in nums:
            if root is None:
                root = TreeNode(v)
                continue
            curr = root
            while True:
                if v < curr.val:
                    if curr.left is None:
                        curr.left = TreeNode(v)
                        break
                    curr = curr.left
                else:
                    if curr.right is None:
                        curr.right = TreeNode(v)
                        break
                    curr = curr.right
        return root


# ==============================================================================
# TEST HELPERS — shared with topic 10 (plain binary trees), verbatim
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


def to_level_order(root):
    """Inverse of build(): level-order list with `None` for absent children,
    trailing `None`s trimmed."""
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


# ------------------------------------------------------------------------------
# PROPERTY CHECKERS — the answer is not unique, so these replace fixed
# expected outputs entirely.
# ------------------------------------------------------------------------------
def inorder_iterative(root):
    """In-order traversal, iterative (safe on chains of any depth)."""
    out, stack, node = [], [], root
    while stack or node:
        while node:
            stack.append(node)
            node = node.left
        node = stack.pop()
        out.append(node.val)
        node = node.right
    return out


def height_iterative(root):
    """Longest root-to-leaf node count. Iterative: the WRONG builders below
    produce chains thousands deep."""
    if root is None:
        return 0
    best, stack = 0, [(root, 1)]
    while stack:
        node, d = stack.pop()
        best = max(best, d)
        if node.left:
            stack.append((node.left, d + 1))
        if node.right:
            stack.append((node.right, d + 1))
    return best


def subtree_heights(root):
    """{id(node): height} for every node, computed bottom-up ITERATIVELY."""
    if root is None:
        return {}
    order, stack = [], [root]
    while stack:                              # collect nodes, parents first
        node = stack.pop()
        order.append(node)
        if node.left:
            stack.append(node.left)
        if node.right:
            stack.append(node.right)
    heights = {}
    for node in reversed(order):              # children before parents
        lh = heights.get(id(node.left), 0)
        rh = heights.get(id(node.right), 0)
        heights[id(node)] = max(lh, rh) + 1
    return heights


def is_height_balanced(root):
    """|height(left) - height(right)| <= 1 at EVERY node. Iterative."""
    heights = subtree_heights(root)
    stack = [root] if root else []
    while stack:
        node = stack.pop()
        lh = heights.get(id(node.left), 0)
        rh = heights.get(id(node.right), 0)
        if abs(lh - rh) > 1:
            return False
        if node.left:
            stack.append(node.left)
        if node.right:
            stack.append(node.right)
    return True


def is_valid_bst(root):
    """In-order must be strictly increasing (problem 006's technique)."""
    io = inorder_iterative(root)
    return all(io[i] < io[i + 1] for i in range(len(io) - 1))


def _count_slice_copies(nums):
    """Total number of list elements copied by the slicing build. Mirrors
    sortedArrayToBST_slicing exactly, counting instead of building."""
    total = 0

    def walk(arr):
        nonlocal total
        if not arr:
            return
        mid = len(arr) // 2
        left, right = arr[:mid], arr[mid + 1:]
        total += len(left) + len(right)       # the elements this call copied
        walk(left)
        walk(right)

    walk(nums)
    return total


def min_possible_height(n):
    """ceil(log2(n+1)) — the floor on any binary tree's height for n nodes."""
    return 0 if n == 0 else math.ceil(math.log2(n + 1))


# ==============================================================================
# TESTS — run:  python 002_convert_sorted_array_to_binary_search_tree_solution.py
# ==============================================================================
CASES = [
    [-10, -3, 0, 5, 9],
    [1, 3],
    [0],
    [1, 2],
    [1, 2, 3],
    [1, 2, 3, 4, 5, 6, 7],
    list(range(-5, 6)),
    list(range(100)),
    [-10000, 0, 10000],
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: PROPERTIES, not a fixed shape ---")
    print("    (in-order == input) AND height-balanced AND height == minimum")
    for nums in CASES:
        root = sol.sortedArrayToBST(nums)
        io = inorder_iterative(root)
        bal = is_height_balanced(root)
        h = height_iterative(root)
        hmin = min_possible_height(len(nums))
        ok = io == nums and bal and h == hmin
        all_ok &= ok
        shown = nums if len(nums) <= 11 else f"[0..{len(nums) - 1}] (n={len(nums)})"
        print(f"{'PASS' if ok else 'FAIL'}  nums={str(shown):<26} "
              f"inorder_ok={io == nums!s:<5} balanced={bal!s:<5} "
              f"height={h} (min {hmin})")

    # ----------------------------------------------------------------------
    # The answer is NOT unique: left-mid and right-mid differ, both valid.
    # ----------------------------------------------------------------------
    print("\n--- the answer is NOT unique: left-mid vs right-mid ---")
    for nums in ([1, 2], [1, 2, 3, 4], [-10, -3, 0, 5, 9]):
        a = sol.sortedArrayToBST(nums)
        b = sol.sortedArrayToBST_rightmid(nums)
        la, lb = to_level_order(a), to_level_order(b)
        both_valid = (is_valid_bst(a) and is_height_balanced(a)
                      and is_valid_bst(b) and is_height_balanced(b)
                      and inorder_iterative(a) == nums
                      and inorder_iterative(b) == nums)
        differ = la != lb
        print(f"  nums={nums!r}")
        print(f"    left-mid  -> {la}")
        print(f"    right-mid -> {lb}")
        print(f"    shapes differ={differ}  both height-balanced BSTs={both_valid}")
        all_ok &= both_valid
    print("  => a test that compares against ONE level-order list is broken.")
    print("     LeetCode uses a special judge here for exactly this reason.")

    # ----------------------------------------------------------------------
    # Slicing variant: same answer shape, worse cost. Cross-check first.
    # ----------------------------------------------------------------------
    print("\n--- slicing variant cross-check: it matches the RIGHT-mid, not the left ---")
    same_right = all(to_level_order(sol.sortedArrayToBST_rightmid(n))
                     == to_level_order(sol.sortedArrayToBST_slicing(n))
                     for n in CASES)
    same_left = all(to_level_order(sol.sortedArrayToBST(n))
                    == to_level_order(sol.sortedArrayToBST_slicing(n))
                    for n in CASES)
    print(f"  slicing == right-mid index recursion: {same_right}")
    print(f"  slicing == left-mid  index recursion: {same_left}")
    print("  `len(nums)//2` is L//2 (right middle); `(lo+hi)//2` is (L-1)//2")
    print("  (left middle). Both are height-balanced; the SHAPES differ. This is")
    print("  the answer-is-not-unique fact biting inside your own test suite.")
    all_ok &= same_right and not same_left

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 1: the balance property, asserted programmatically at scale.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 1: midpoint builds a MINIMUM-height tree; leftmost-root "
          "builds a chain ---")
    print(f"  {'n':>6} {'mid height':>11} {'min possible':>13} {'balanced?':>10} "
          f"{'leftmost-root height':>21}")
    demo_ok = True
    for n in (7, 15, 1_023, 8_191, 10_000):
        nums = list(range(n))
        good = sol.sortedArrayToBST(nums)
        bad = sol.sortedArrayToBST_leftmost_root(nums)
        hg, hb = height_iterative(good), height_iterative(bad)
        bal = is_height_balanced(good)
        bad_bal = is_height_balanced(bad)
        demo_ok &= bal and hg == min_possible_height(n) and hb == n and not bad_bal
        print(f"  {n:>6} {hg:>11} {min_possible_height(n):>13} {str(bal):>10} "
              f"{hb:>21}")
    print("  The midpoint build hits the theoretical minimum height every time.")
    print("  The leftmost-root build gives height == n: a valid BST that FAILS")
    print("  the height-balanced requirement (checked above, balanced=False).")
    all_ok &= demo_ok

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 2: build-by-insertion is O(n^2) on sorted input.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 2: build-by-insertion on SORTED input is O(n^2), measured ---")
    print(f"  {'n':>6} {'midpoint ms':>12} {'by-insert ms':>13} {'ratio':>8} "
          f"{'insert height':>14}")
    for n in (1_000, 2_000, 4_000):
        nums = list(range(n))
        t0 = time.perf_counter()
        good = sol.sortedArrayToBST(nums)
        t1 = time.perf_counter()
        bad = sol.sortedArrayToBST_by_insertion(nums)
        t2 = time.perf_counter()
        g_ms, b_ms = (t1 - t0) * 1000, (t2 - t1) * 1000
        ratio = b_ms / g_ms
        print(f"  {n:>6} {g_ms:>11.2f}  {b_ms:>12.2f}  {ratio:>7.0f}x "
              f"{height_iterative(bad):>14}")
    print("  Doubling n roughly QUADRUPLES the by-insertion time (O(n^2)) while")
    print("  the midpoint build only doubles (O(n)) — so the ratio itself keeps")
    print("  growing. And the by-insertion tree is a chain of height n anyway.")

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 3: slicing costs O(n log n) space + time for nothing.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 3: index recursion vs slice recursion ---")
    print("  (a) elements COPIED while building — the asymptotic difference, counted")
    print(f"  {'n':>7} {'index copies':>13} {'slicing copies':>15} "
          f"{'slicing / n':>12} {'log2(n)':>8}")
    for n in (1_000, 10_000, 100_000):
        nums = list(range(n))
        copied = _count_slice_copies(nums)
        print(f"  {n:>7} {0:>13} {copied:>15} {copied / n:>11.1f}x "
              f"{math.log2(n):>8.1f}")
    print("  Index recursion copies ZERO elements — it passes two ints per call.")
    print("  Slicing copies ~n elements per level, ~n*log2(n) in total. That")
    print("  ratio column IS log2(n), measured, which is the extra factor.")

    print("\n  (b) wall clock, measured without tracemalloc running")
    print(f"  {'n':>7} {'index ms':>10} {'slicing ms':>12} {'ratio':>8}")
    for n in (10_000, 100_000, 400_000):
        nums = list(range(n))
        t0 = time.perf_counter()
        sol.sortedArrayToBST(nums)
        t1 = time.perf_counter()
        sol.sortedArrayToBST_slicing(nums)
        t2 = time.perf_counter()
        i_ms, s_ms = (t1 - t0) * 1000, (t2 - t1) * 1000
        print(f"  {n:>7} {i_ms:>9.1f}  {s_ms:>11.1f}  {s_ms / i_ms:>7.2f}x")
    print("  Only a modest wall-clock gap, and it is worth knowing WHY: list")
    print("  slicing is a C-level memcpy of pointers, while allocating n")
    print("  TreeNode objects dominates BOTH runs. The O(n log n) copying is")
    print("  real (counted above) but cheap per element in CPython. Do not")
    print("  oversell it in an interview as a 'much slower' solution; sell it")
    print("  as the one that allocates O(n log n) instead of O(n).")

    print("\n  (c) peak traced memory, tracemalloc")
    print(f"  {'n':>7} {'index peak KB':>14} {'slicing peak KB':>16} {'ratio':>8}")
    for n in (10_000, 100_000, 400_000):
        nums = list(range(n))
        tracemalloc.start()
        keep = sol.sortedArrayToBST(nums)
        _, peak_a = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        del keep
        tracemalloc.start()
        keep = sol.sortedArrayToBST_slicing(nums)
        _, peak_b = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        del keep
        print(f"  {n:>7} {peak_a / 1024:>13.0f}  {peak_b / 1024:>15.0f}  "
              f"{peak_b / peak_a:>7.2f}x")
    print("  The n TreeNodes dominate the peak in both, so the ratio is small —")
    print("  the live slices along one recursion path sum to only ~n pointers")
    print("  (n/2 + n/4 + ... ), not n*log n, because siblings are freed as the")
    print("  recursion unwinds. Total ALLOCATION is O(n log n); peak RESIDENT")
    print("  is O(n). Both statements are true and they are not the same claim.")

    # ----------------------------------------------------------------------
    # Randomised property check on arbitrary sorted inputs.
    # ----------------------------------------------------------------------
    print("\n--- randomised property check: 3000 random sorted arrays ---")
    random.seed(108)
    bad_count = 0
    for _ in range(3000):
        n = random.randint(1, 40)
        nums = sorted(random.sample(range(-500, 500), n))
        for builder in (sol.sortedArrayToBST, sol.sortedArrayToBST_rightmid):
            root = builder(nums)
            if (inorder_iterative(root) != nums
                    or not is_height_balanced(root)
                    or height_iterative(root) != min_possible_height(n)):
                bad_count += 1
    print(f"  property violations across both mid choices: {bad_count}")
    all_ok &= (bad_count == 0)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
