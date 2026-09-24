"""
================================================================================
SOLUTION · LeetCode 173 · Binary Search Tree Iterator                 [Medium]
https://leetcode.com/problems/binary-search-tree-iterator/
================================================================================

THE CORE IDEA
--------------
An iterative in-order traversal (problem 007) already IS a paused/resumable
process — the explicit stack it carries between iterations of its `while`
loop is exactly the state a caller would need to "come back later." The
only change this problem makes is to stop hiding that stack inside one
function and expose it as OBJECT STATE instead:

    class BSTIterator:
        def __init__(self, root):
            self.stack = []
            self._push_left_spine(root)

        def next(self):
            node = self.stack.pop()          # smallest not-yet-returned value
            if node.right:
                self._push_left_spine(node.right)
            return node.val

        def hasNext(self):
            return bool(self.stack)

        def _push_left_spine(self, node):
            while node:
                self.stack.append(node)
                node = node.left

The constructor primes the stack with the left spine from `root` (the path
to the smallest value). Each `next()` pops the smallest remaining node and,
if it has a right child, pushes THAT subtree's left spine — which is the
in-order successor's path. `hasNext()` needs no traversal: the stack is
non-empty iff there is a next value.


================================================================================
WHY next() IS O(1) AMORTIZED, NOT O(1) WORST CASE
================================================================================
A single `next()` call is NOT always O(1) — it can do up to O(h) work when
`node.right`'s left spine is long. The O(1) claim in the follow-up is about
the AVERAGE over the iterator's whole lifetime, and the proof is a clean
piece of amortized-analysis reasoning worth being able to state out loud:

    Every node in the tree is pushed onto the stack EXACTLY ONCE, ever
    (either during __init__'s initial spine, or during exactly one
    next() call that pushes its parent subtree's spine). Every node is
    also popped EXACTLY ONCE, ever (the call that returns it).

    So across a full traversal of n nodes: total pushes = n, total pops
    = n, total work = O(n) for the ENTIRE lifetime, spread across n calls
    to next(). Average work per call = O(n) / n = O(1).

This is the same accounting as amortized dynamic-array doubling or the
classic "two-pointer window never moves backward" argument: a bound on
TOTAL work across all calls, divided by the number of calls, beats trying
to bound any single call individually.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, price it and drop it): in the constructor, run a
full in-order traversal and store every value in a list; `next()` just
indexes `values[i]; i += 1`, `hasNext()` checks `i < len(values)`. This
gives TRUE O(1) worst-case (not just amortized) per call — strictly BETTER
time than the answer — but O(n) space, always, even if the caller only
ever calls `next()` once. It fails the follow-up's explicit O(h) memory
bound. Measured below: for large trees this is also slower to CONSTRUCT
and uses far more memory, in exchange for a per-call speed that turns out
not to matter much in practice (see Demo 2).

Approach 1 (lazy stack, push-as-you-go) ✅ — the answer, above. O(h)
memory, O(1) amortized time per `next()`.

Approach 2 (Morris-threaded, O(1) EXTRA memory beyond the tree itself) —
the follow-up-to-the-follow-up. Temporarily mutate the tree's `right`
pointers on leaves of the left spine to thread back to their in-order
successor, walk using those threads, and undo them as you pass. True O(1)
space at the cost of TEMPORARILY MUTATING the tree structure while the
iterator is in use (must be restored, and is not safe if another thread or
caller reads the tree concurrently). Named in follow-ups; not shipped,
because "correct but transiently mutates a data structure you don't own"
is a real production hazard worth flagging rather than silently coding.


================================================================================
STEP BY STEP TRACE
================================================================================
tree = [7,3,15,null,null,9,20]

              7
            ╱   ╲
          3       15
                 ╱   ╲
                9      20

__init__(root=7):
    _push_left_spine(7): push 7, go left -> 3, push 3, go left -> None, stop
    stack = [7, 3]   (top is 3, the smallest)

next() #1:
    pop 3  -> RETURN 3
    3 has no right child -> nothing pushed
    stack = [7]

next() #2:
    pop 7  -> RETURN 7
    7.right = 15 -> _push_left_spine(15): push 15, go left -> 9, push 9,
                     go left -> None, stop
    stack = [15, 9]

hasNext() -> stack non-empty -> True

next() #3:
    pop 9  -> RETURN 9
    9 has no right child -> nothing pushed
    stack = [15]

hasNext() -> True

next() #4:
    pop 15 -> RETURN 15
    15.right = 20 -> _push_left_spine(20): push 20, go left -> None, stop
    stack = [20]

hasNext() -> True

next() #5:
    pop 20 -> RETURN 20
    20 has no right child -> nothing pushed
    stack = []

hasNext() -> stack empty -> False

Sequence produced: 3, 7, 9, 15, 20 — matches the problem's example exactly,
and matches `sorted([7,3,15,9,20])`.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    __init__     next()        hasNext()  Space   Mutates?
    ----------------------------  -----------  ------------  ---------  ------  --------
    Precompute full list (brute)  O(n)         O(1) worst    O(1)       O(n)    no
    Lazy stack ✅                 O(h)         O(1) amort.*  O(1)       O(h)    no
                                                (O(h) worst
                                                single call)
    Morris-threaded (follow-up)   O(1)         O(1) amort.*  O(1)       O(1)    YES —
                                                                                 temporarily

    *amortized across the iterator's full lifetime; see the proof above.


================================================================================
EDGE CASES
================================================================================
    single-node tree               -> one `next()` returns the root's
                                     value, `hasNext()` then False.
    left-skewed tree (h == n)       -> __init__ pushes ALL n nodes at once
                                     (the whole tree IS the left spine) —
                                     O(n) space in this shape, matching the
                                     stated O(h) bound since h = n here.
    right-skewed tree               -> __init__ pushes only the root; every
                                     next() call does O(1) work AND pushes
                                     exactly one more node — worst case for
                                     "spread out" pushing, best case for
                                     initial memory.
    hasNext() called without any     -> must not mutate state; calling it
    intervening next()                 repeatedly gives the same answer.
    next() called exactly n times,   -> the LAST call must leave the stack
    exhausting the tree                empty and hasNext() must then return
                                     False, not raise or return garbage.
    calling next() past exhaustion   -> undefined per the problem's own
                                     guarantee ("next() will always be
                                     valid"); this solution does not guard
                                     against it, matching that guarantee.
    duplicate values (if the BST      -> the stack-based descent doesn't
    allowed them)                      care about value comparisons at all
                                     — it only follows child pointers, so
                                     duplicates (if legally present) come
                                     out in whatever order the tree stores
                                     them, still non-decreasing.


================================================================================
COMMON MISTAKES
================================================================================
1. Precomputing the full sorted list in `__init__` without realizing this
   fails the stated O(h)-memory follow-up. It is a VALID first answer —
   say so explicitly, then offer the lazy-stack version as the follow-up
   response, since interviewers usually ask for it directly after.

2. Forgetting to push the RIGHT child's entire left spine in `next()` —
   pushing just `node.right` itself (not descending its left spine first)
   skips ahead and returns values out of order.

3. Pushing the left spine in the wrong place — e.g. doing it in `hasNext()`
   instead of `next()`/`__init__()`, which either duplicates work or
   corrupts the stack if `hasNext()` is called multiple times between
   `next()` calls (it must be a pure query, not a mutator).

4. Re-deriving the whole left spine from `root` on every `next()` call
   instead of maintaining the stack incrementally — correct output, but
   O(h) work EVERY call instead of amortized O(1), and it throws away the
   entire point of keeping state between calls.

5. Using recursion to implement the traversal underneath the iterator —
   there is no clean way to "pause" a recursive call between two external
   method invocations without manually simulating a stack anyway, which is
   just the explicit-stack version with extra steps.

6. Mutating `node.val` or child pointers while iterating (as Morris
   traversal would, if done carelessly) — fine as an internal
   implementation detail ONLY if fully restored before control returns to
   the caller; leaving threads in place corrupts the tree for anyone else
   holding a reference to it.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: You already gave O(h) memory — can you get O(1) EXTRA memory, not
   counting the tree itself?
A: Morris-threaded traversal: temporarily rethread right-null pointers on
   the left spine to point back to their in-order successor, walk using
   those threads, restore them as you pass. True O(1) space, at the cost
   of transiently mutating the tree — flag this trade-off explicitly.

Q: What if you needed `hasPrevious()`/`prev()` too — a bidirectional
   iterator?
A: Maintain TWO stacks (or one stack plus direction tracking) — mirror the
   left-spine logic with a right-spine version for going backward. More
   state, same amortized argument in each direction independently.

Q: Multiple BSTIterator instances over the SAME mutable tree, one of them
   inserting new nodes mid-iteration — what breaks?
A: The stack holds node REFERENCES, so already-visited state stays valid,
   but the traversal's in-order guarantee for NOT-yet-visited nodes can be
   violated if an insert lands ahead of the iterator's current position
   with the wrong final position (e.g. a new min after iteration started).
   Most language iterator contracts (Python's `dict` included) simply
   forbid mutation during iteration for this reason — worth naming that
   this iterator has the same implicit contract.

Q: How does this differ from Python's own generator syntax
   (`yield`)?
A: A generator IS this exact pattern, built into the language — `yield`
   inside a recursive in-order walk pauses and resumes automatically,
   using the interpreter's own frame instead of a hand-rolled stack. It is
   arguably the more "Pythonic" answer; the explicit-stack class version is
   shown here because it matches what the problem's class-based API
   (`__init__`/`next`/`hasNext`) actually asks for, and generalizes to
   languages without generators.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Pattern 2 of the topic guide's taxonomy: in-order-is-sorted, used to RESUME
across an unbounded, externally-driven number of calls.

    LC 230  Kth Smallest Element in a BST     — in-order used to INDEX,
                                                a single call, not resumable (007)
    LC 98   Validate Binary Search Tree         — in-order used as a TEST (006)
    LC 281  Zigzag Iterator                     — same "external next()"
                                                shape, different source data
    LC 251  Flatten 2D Vector                   — same iterator-state
                                                discipline, array-backed
    LC 284  Peeking Iterator                    — adds a `peek()` that must
                                                not consume — same stack idea,
                                                buffer one extra value
================================================================================
"""

import random
import sys
import time
import tracemalloc
from collections import deque
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class BSTIterator:
    """✅ THE ANSWER — lazy explicit stack. O(h) space, O(1) amortized
    time per next(), O(1) time per hasNext()."""

    def __init__(self, root: Optional[TreeNode]):
        self.stack = []
        self._push_left_spine(root)

    def next(self) -> int:
        node = self.stack.pop()
        if node.right:
            self._push_left_spine(node.right)
        return node.val

    def hasNext(self) -> bool:
        return bool(self.stack)

    def _push_left_spine(self, node):
        while node:
            self.stack.append(node)
            node = node.left


class BSTIteratorBrute:
    """Precompute the full in-order sequence up front. True O(1) WORST
    CASE per next() (better than the answer's amortized bound!), but O(n)
    memory always — fails the stated O(h) follow-up."""

    def __init__(self, root: Optional[TreeNode]):
        self.values = []
        self._inorder(root)
        self.i = 0

    def _inorder(self, node):
        if node is None:
            return
        self._inorder(node.left)
        self.values.append(node.val)
        self._inorder(node.right)

    def next(self) -> int:
        v = self.values[self.i]
        self.i += 1
        return v

    def hasNext(self) -> bool:
        return self.i < len(self.values)


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


def bst_insert_iterative(root, val):
    node = TreeNode(val)
    if root is None:
        return node
    curr = root
    while True:
        if val < curr.val:
            if curr.left is None:
                curr.left = node
                return root
            curr = curr.left
        else:
            if curr.right is None:
                curr.right = node
                return root
            curr = curr.right


def balanced_bst(lo, hi):
    if lo >= hi:
        return None
    mid = (lo + hi) // 2
    node = TreeNode(mid)
    node.left = balanced_bst(lo, mid)
    node.right = balanced_bst(mid + 1, hi)
    return node


def height_iterative(root):
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


# ==============================================================================
# TESTS — run:  python 008_binary_search_tree_iterator_solution.py
# ==============================================================================
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

    print("\n--- correctness: lazy-stack and brute agree on random BSTs ---")
    random.seed(173)
    mismatches, trials = 0, 500
    for _ in range(trials):
        vals = random.sample(range(-1000, 1000), random.randint(1, 50))
        root = None
        for v in vals:
            root = bst_insert_iterative(root, v)
        a_out, b_out = [], []
        it_a, it_b = BSTIterator(root), BSTIteratorBrute(root)
        while it_a.hasNext():
            a_out.append(it_a.next())
        while it_b.hasNext():
            b_out.append(it_b.next())
        expected = sorted(vals)
        if not (a_out == b_out == expected):
            mismatches += 1
    print(f"  {trials} random BSTs, both implementations vs sorted(): "
          f"{mismatches} mismatches")
    all_ok &= (mismatches == 0)

    print("\n--- correctness: interleaved hasNext()/next() calls ---")
    root = build([5, 3, 8, 1, 4, 7, 9])
    it = BSTIterator(root)
    interleave_ok = True
    for _ in range(3):
        interleave_ok &= it.hasNext() is True   # repeated hasNext, no mutation
        interleave_ok &= it.hasNext() is True
    out = []
    while it.hasNext():
        out.append(it.next())
    interleave_ok &= (out == sorted([5, 3, 8, 1, 4, 7, 9]))
    print(f"  repeated hasNext() calls don't mutate state, "
          f"full sequence correct: {interleave_ok}")
    all_ok &= interleave_ok

    # ----------------------------------------------------------------------
    # STEP BY STEP trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: [7,3,15,null,null,9,20] ---")
    root = build([7, 3, 15, None, None, 9, 20])
    it = BSTIterator(root)
    print(f"  after __init__: stack = {[n.val for n in it.stack]}")
    while it.hasNext():
        v = it.next()
        print(f"  next() -> {v:<3}  stack now = {[n.val for n in it.stack]}")

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 1: peak memory, lazy stack (O(h)) vs precompute (O(n)).
    # ----------------------------------------------------------------------
    print("\n--- DEMO 1: peak memory — lazy stack O(h) vs precompute O(n) ---")
    n = 60_000
    root = balanced_bst(0, n)
    h = height_iterative(root)
    print(f"  n={n} nodes, height={h}")

    tracemalloc.start()
    it_lazy = BSTIterator(root)
    _, peak_lazy = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    tracemalloc.start()
    it_brute = BSTIteratorBrute(root)
    _, peak_brute = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"  lazy stack __init__ peak extra memory:   {peak_lazy:>9,} bytes "
          f"(stack holds up to {h} nodes)")
    print(f"  precompute __init__ peak extra memory:   {peak_brute:>9,} bytes "
          f"(list holds all {n} values)")
    print(f"  ratio: {peak_brute / peak_lazy:.1f}x more memory for the brute "
          f"version's __init__")
    demo1_ok = peak_brute > peak_lazy
    all_ok &= demo1_ok

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 2: amortized O(1) — total work over a full traversal.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 2: amortized O(1) — total pushes/pops across full traversal ---")

    class InstrumentedBSTIterator(BSTIterator):
        def __init__(self, root):
            self.pushes = 0
            self.pops = 0
            super().__init__(root)

        def _push_left_spine(self, node):
            while node:
                self.stack.append(node)
                self.pushes += 1
                node = node.left

        def next(self):
            node = self.stack.pop()
            self.pops += 1
            if node.right:
                self._push_left_spine(node.right)
            return node.val

    it = InstrumentedBSTIterator(root)
    calls = 0
    while it.hasNext():
        it.next()
        calls += 1
    print(f"  n={n} nodes, {calls} next() calls over the full traversal")
    print(f"  total pushes = {it.pushes}, total pops = {it.pops}")
    print(f"  average pushes/call = {it.pushes / calls:.3f}, "
          f"average pops/call = {it.pops / calls:.3f}")
    print("  Both averages sit at essentially 1.0 regardless of n — each node")
    print("  is pushed once and popped once across the WHOLE lifetime, so the")
    print("  O(n) total work spread over n calls averages to O(1) per call,")
    print("  even though any single call (a long right-subtree spine) can")
    print("  individually cost up to O(h).")
    demo2_ok = (it.pushes == n and it.pops == n and calls == n)
    all_ok &= demo2_ok

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 3: wall clock, __init__ cost — O(h) vs O(n).
    # ----------------------------------------------------------------------
    print("\n--- DEMO 3: wall clock — __init__ cost scales with h vs n ---")
    print(f"  {'n':>8} {'height':>7} {'lazy __init__ us':>18} "
          f"{'brute __init__ us':>19} {'ratio':>8}")
    ratio_grows = []
    for size in (1_000, 10_000, 60_000):
        t = balanced_bst(0, size)
        th = height_iterative(t)
        reps = 200 if size <= 10_000 else 30
        t0 = time.perf_counter()
        for _ in range(reps):
            BSTIterator(t)
        t1 = time.perf_counter()
        for _ in range(reps):
            BSTIteratorBrute(t)
        t2 = time.perf_counter()
        lazy_us = (t1 - t0) / reps * 1e6
        brute_us = (t2 - t1) / reps * 1e6
        ratio = brute_us / lazy_us
        ratio_grows.append(ratio)
        print(f"  {size:>8} {th:>7} {lazy_us:>18.2f} {brute_us:>19.2f} "
              f"{ratio:>7.1f}x")
    print("  __init__ cost for the lazy stack tracks HEIGHT (grows barely at")
    print("  all as n grows 60x: height goes from ~10 to ~17); the brute")
    print("  version's __init__ must visit and store every one of the n")
    print("  nodes every time, so its cost — and the gap — grows with n.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
