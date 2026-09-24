"""
================================================================================
SOLUTION · LeetCode 707 · Design Linked List                            [Medium]
https://leetcode.com/problems/design-linked-list/
================================================================================

THE CORE IDEA
--------------
Two sentinel nodes (dummy head, dummy tail), a maintained `size` counter,
and `.prev`/`.next` on every real node. The sentinels eliminate every
empty-list / insert-at-boundary special case (same idiom as LRU Cache,
topic 08's 013, applied here to index-based traversal instead of
recency-based splicing); `size` turns index-validity checks into O(1)
arithmetic; and walking from whichever end (head or tail) is closer to the
target index roughly halves the average traversal distance versus always
walking from head.


================================================================================
APPROACH 1 · Python list as the backing store (works, but misses the point,
priced and coded as an oracle)
================================================================================
A plain Python `list`, using `.insert(index, val)` / `.pop(index)` /
indexing directly.

    get:            O(1)
    addAtHead:      O(n) — every existing element shifts right
    addAtTail:      O(1) amortized
    addAtIndex:     O(n) — shifts everything after `index`
    deleteAtIndex:  O(n) — shifts everything after `index`

This is not "wrong," but it defeats the exercise: the problem exists to
make you hand-build node-level splicing, and `list.insert`/`list.pop`
already do that internally in C. Used below purely as a correctness
oracle, not "the answer."


================================================================================
APPROACH 2 · Singly linked list with head + size (simpler, no addAtTail
shortcut)
================================================================================
One `.next` pointer per node, a `head` sentinel, a `size` counter, no tail
pointer. `addAtTail` must walk the FULL list every time (O(n)) since there
is no shortcut to the last node, and `deleteAtIndex`/`addAtIndex` must
always walk from `head` (no "walk from whichever end is closer" option,
since there's no way to walk backward from a tail reference).

    get / addAtIndex / deleteAtIndex:  O(index)
    addAtHead:                          O(1)
    addAtTail:                          O(n) — no tail pointer

Simpler to implement correctly (only one pointer per node to keep
consistent), but strictly worse on `addAtTail` and on average traversal
distance than Approach 3. Not the primary answer because the doubly
linked version is barely more code and asymptotically better across the
board.


================================================================================
APPROACH 3 · Doubly linked list, dummy head + dummy tail, maintained
size ✅ (the answer)
================================================================================
    class _Node:
        def __init__(self, val=0):
            self.val = val
            self.prev = self.next = None

    class MyLinkedList:
        def __init__(self):
            self.head = _Node()          # sentinel, before index 0
            self.tail = _Node()          # sentinel, after the last real node
            self.head.next = self.tail
            self.tail.prev = self.head
            self.size = 0

        def _node_at(self, index):
            # Walk from whichever end is closer to `index`.
            if index < self.size - index:
                node = self.head.next
                for _ in range(index):
                    node = node.next
            else:
                node = self.tail.prev
                for _ in range(self.size - 1 - index):
                    node = node.prev
            return node

        def get(self, index):
            if not (0 <= index < self.size):
                return -1
            return self._node_at(index).val

        def _insert_before(self, node, val):
            new = _Node(val)
            new.prev, new.next = node.prev, node
            node.prev.next = new
            node.prev = new
            self.size += 1

        def addAtHead(self, val):
            self._insert_before(self.head.next, val)

        def addAtTail(self, val):
            self._insert_before(self.tail, val)

        def addAtIndex(self, index, val):
            if index > self.size:
                return                       # per spec: do NOT insert
            if index < 0:
                index = 0                     # per spec: clamp to head
            self._insert_before(self._node_at(index) if index < self.size else self.tail, val)

        def deleteAtIndex(self, index):
            if not (0 <= index < self.size):
                return
            node = self._node_at(index)
            node.prev.next = node.next
            node.next.prev = node.prev
            self.size -= 1

Every splice touches only O(1) pointers once the target node is located —
the walking IS the O(index) cost, splicing itself is O(1).

    Time: get/addAtIndex/deleteAtIndex O(min(index, size-index)); addAtHead
          and addAtTail O(1).     Space: O(n).


================================================================================
STEP BY STEP TRACE
================================================================================
    addAtHead(1)     head <-> [1] <-> tail                     size=1
    addAtTail(3)     head <-> [1] <-> [3] <-> tail              size=2
    addAtIndex(1,2)  insert 2 BEFORE node-at-index-1 (=[3])
                     head <-> [1] <-> [2] <-> [3] <-> tail       size=3
    get(1)           node-at-index-1 = [2]  -> returns 2
    deleteAtIndex(1) unlink node-at-index-1 (=[2])
                     head <-> [1] <-> [3] <-> tail              size=2
    get(1)           node-at-index-1 = [3]  -> returns 3

    ASCII after addAtIndex(1, 2):

        head <-> [1] <-> [2] <-> [3] <-> tail
                  idx0    idx1    idx2


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     get/addAtIndex/delete   addAtHead   addAtTail   Space
    ----------------------------  -----------------------  ----------  ----------  ------
    Python list backing (oracle) O(1) get, O(n) others     O(n)        O(1) amort  O(n)
    Singly linked, head only     O(index)                  O(1)        O(n)        O(n)
    Doubly linked, head+tail ✅  O(min(index, size-index)) O(1)        O(1)        O(n)
    Mutates input? n/a — design problem in every row.


================================================================================
EDGE CASES
================================================================================
    get on an empty list              Must return -1 for ANY index,
                                       including 0.
    addAtIndex(size, val)              Per spec: appends at the tail — the
                                       boundary is INCLUSIVE of `size`.
    addAtIndex(index > size, val)      Per spec: no-op, node is NOT
                                       inserted — a common bug is inserting
                                       anyway (e.g. clamped to tail).
    addAtIndex(negative index, val)    Per spec: treated as inserting at
                                       the head (clamp to 0), not a no-op
                                       and not an error.
    deleteAtIndex out of range         Silent no-op (both `index < 0` and
                                       `index >= size`).
    Single-element list, delete it     Must correctly return to the
                                       empty-list state (head.next ==
                                       tail again), not leave a dangling
                                       sentinel link.
    Repeated addAtHead                Each call must become the NEW head,
                                       pushing the previous head back —
                                       exercises the sentinel splice at
                                       the very front repeatedly.


================================================================================
COMMON MISTAKES
================================================================================
1. Off-by-one on the THREE addAtIndex boundary cases (`index < 0`,
   `index == size`, `index > size`) — this problem's single most common
   source of wrong-answer submissions; each case has explicit,
   DIFFERENT-from-each-other required behavior in the spec.

2. Forgetting to update `size` on every insert/delete — subsequent
   `get`/`addAtIndex`/`deleteAtIndex` range checks then silently use a
   stale length, either rejecting valid indices or accepting invalid ones.

3. Walking always from `head` even in the doubly linked version — still
   correct, but throws away the whole point of maintaining `.prev`/tail
   (halving average traversal distance); a common "technically passes but
   misses the design intent" implementation.

4. Not using sentinel nodes and instead special-casing `if self.head is
   None` / `if index == 0` everywhere — reintroduces exactly the
   edge-case bugs sentinels exist to eliminate (same lesson as LRU
   Cache's mistake #4).

5. In `addAtIndex`, calling `_node_at(index)` when `index == size` — that
   index is OUT OF RANGE for `_node_at` (which assumes an existing node),
   and must instead insert-before the tail sentinel directly, not walk to
   a non-existent node.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Could you make `get` O(1) as well?
A: Not for arbitrary index access on a genuine LINKED list — that's an
   array's advantage, not a linked list's. If O(1) random access AND O(1)
   insert/delete were both required, the answer is "you need a different
   data structure" (e.g. an array-backed structure, or a skip list for
   O(log n) with ordered operations) — this is precisely the tension this
   problem exists to make concrete.

Q: How would you support reversing the whole list?
A: With a doubly linked list, reverse by walking every node and swapping
   its `.prev`/`.next` (then swap `self.head`/`self.tail`) — O(n) time,
   O(1) extra space; this is topic 08's classic in-place list reversal,
   just with an extra pointer to swap per node.

Q: What if `val` needed to be an arbitrary object, not an int in
   `[0, 1000]`?
A: Nothing in the design changes — `val` is stored opaquely in each node
   regardless of type; the only place a numeric assumption would leak in
   is if `get`'s -1 sentinel could collide with a legitimate value, which
   would then need a different "not found" signal (e.g. raising, or a
   sentinel object).


================================================================================
RELATED PROBLEMS
================================================================================
    LC 146  LRU Cache (topic 08, 013)        — same dummy-head/tail idiom, recency order not index order
    LC 25   Reverse Nodes in k-Group (topic 08) — splicing discipline on a real linked list
    LC 705  Design HashSet (this topic, 001) — same "hand-build what a library normally gives you" spirit
    Topic 08 · Linked List                   — every splice/traversal technique this problem composes
================================================================================
"""

import random
import time


class _Node:
    __slots__ = ("val", "prev", "next")

    def __init__(self, val: int = 0):
        self.val = val
        self.prev = None
        self.next = None


class MyLinkedList:
    """Doubly linked list, dummy head + dummy tail, maintained size.
    See THE CORE IDEA above."""

    def __init__(self):
        self.head = _Node()
        self.tail = _Node()
        self.head.next = self.tail
        self.tail.prev = self.head
        self.size = 0

    def _node_at(self, index: int) -> _Node:
        # Walk from whichever end is closer to `index`.
        if index < self.size - index:
            node = self.head.next
            for _ in range(index):
                node = node.next
        else:
            node = self.tail.prev
            for _ in range(self.size - 1 - index):
                node = node.prev
        return node

    def _insert_before(self, node: _Node, val: int) -> None:
        new = _Node(val)
        new.prev, new.next = node.prev, node
        node.prev.next = new
        node.prev = new
        self.size += 1

    def get(self, index: int) -> int:
        if not (0 <= index < self.size):
            return -1
        return self._node_at(index).val

    def addAtHead(self, val: int) -> None:
        self._insert_before(self.head.next, val)

    def addAtTail(self, val: int) -> None:
        self._insert_before(self.tail, val)

    def addAtIndex(self, index: int, val: int) -> None:
        if index > self.size:
            return  # per spec: do NOT insert
        if index < 0:
            index = 0  # per spec: clamp negative index to the head
        target = self._node_at(index) if index < self.size else self.tail
        self._insert_before(target, val)

    def deleteAtIndex(self, index: int) -> None:
        if not (0 <= index < self.size):
            return
        node = self._node_at(index)
        node.prev.next = node.next
        node.next.prev = node.prev
        self.size -= 1

    def _to_list(self) -> list:
        out = []
        node = self.head.next
        while node is not self.tail:
            out.append(node.val)
            node = node.next
        return out


# ------------------------------------------------------------------------
# Alternatives / oracles.
# ------------------------------------------------------------------------
class MyLinkedListArrayOracle:
    """Approach 1: plain Python list. Simple and correct, but defeats the
    exercise (list.insert/pop already do the splicing in C). Correctness
    oracle only."""

    def __init__(self):
        self.data: list[int] = []

    def get(self, index: int) -> int:
        if not (0 <= index < len(self.data)):
            return -1
        return self.data[index]

    def addAtHead(self, val: int) -> None:
        self.data.insert(0, val)

    def addAtTail(self, val: int) -> None:
        self.data.append(val)

    def addAtIndex(self, index: int, val: int) -> None:
        if index > len(self.data):
            return
        if index < 0:
            index = 0
        self.data.insert(index, val)

    def deleteAtIndex(self, index: int) -> None:
        if 0 <= index < len(self.data):
            self.data.pop(index)


class MyLinkedListSinglyHeadOnly:
    """Approach 2: singly linked, head sentinel only, no tail pointer —
    addAtTail must walk the full list every time. Used for the benchmark."""

    def __init__(self):
        self.head = _Node()  # sentinel
        self.size = 0

    def _node_before(self, index: int) -> _Node:
        node = self.head
        for _ in range(index):
            node = node.next
        return node

    def get(self, index: int) -> int:
        if not (0 <= index < self.size):
            return -1
        return self._node_before(index).next.val

    def addAtHead(self, val: int) -> None:
        self.addAtIndex(0, val)

    def addAtTail(self, val: int) -> None:
        self.addAtIndex(self.size, val)

    def addAtIndex(self, index: int, val: int) -> None:
        if index > self.size:
            return
        if index < 0:
            index = 0
        prev = self._node_before(index)
        new = _Node(val)
        new.next = prev.next
        prev.next = new
        self.size += 1

    def deleteAtIndex(self, index: int) -> None:
        if not (0 <= index < self.size):
            return
        prev = self._node_before(index)
        prev.next = prev.next.next
        self.size -= 1


# ==============================================================================
# TESTS — run:  python 004_design_linked_list_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    # ------------------------------------------------------------------
    # Correctness: LeetCode's canonical example, cross-checked against
    # both alternates.
    # ------------------------------------------------------------------
    print("--- correctness: doubly-linked vs array oracle vs singly-linked ---")
    def run_script(impl):
        impl.addAtHead(1)
        impl.addAtTail(3)
        impl.addAtIndex(1, 2)
        results = [impl.get(1)]
        impl.deleteAtIndex(1)
        results.append(impl.get(1))
        return results

    wants = [2, 3]
    impls = {
        "doubly-linked ": MyLinkedList(),
        "array oracle  ": MyLinkedListArrayOracle(),
        "singly-linked ": MyLinkedListSinglyHeadOnly(),
    }
    for name, impl in impls.items():
        results = run_script(impl)
        ok = results == wants
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}  results={results}  (want {wants})")

    # ------------------------------------------------------------------
    # addAtIndex boundary cases.
    # ------------------------------------------------------------------
    print("\n--- addAtIndex boundary cases ---")
    ll = MyLinkedList()
    ll.addAtHead(10)
    ll.addAtIndex(1, 20)   # index == size -> append
    ll.addAtIndex(99, 30)  # index > size -> no-op
    ll.addAtIndex(-5, 5)   # index < 0 -> clamp to head
    ok = ll._to_list() == [5, 10, 20]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  == size appends, > size no-ops, < 0 clamps to head  got={ll._to_list()}")

    # ------------------------------------------------------------------
    # Empty-list and single-element-delete edge cases.
    # ------------------------------------------------------------------
    print("\n--- empty list / delete-to-empty ---")
    empty = MyLinkedList()
    ok = empty.get(0) == -1
    empty.deleteAtIndex(0)  # no-op, must not crash
    ok &= empty.get(0) == -1
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  get/delete on empty list are safe no-ops")

    single = MyLinkedList()
    single.addAtHead(7)
    single.deleteAtIndex(0)
    ok = single.get(0) == -1 and single.head.next is single.tail and single.tail.prev is single.head
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  deleting the only node restores the empty sentinel link")

    # ------------------------------------------------------------------
    # Randomized cross-check vs the array oracle.
    # ------------------------------------------------------------------
    print("\n--- randomized cross-check vs array oracle (2000 ops) ---")
    rng = random.Random(13)
    ours = MyLinkedList()
    oracle = MyLinkedListArrayOracle()
    mismatch = False
    for _ in range(2000):
        op = rng.choice(["get", "addAtHead", "addAtTail", "addAtIndex", "deleteAtIndex"])
        cur_size = len(oracle.data)
        if op == "get":
            idx = rng.randint(-2, cur_size + 2)
            if ours.get(idx) != oracle.get(idx):
                mismatch = True
        elif op == "addAtHead":
            val = rng.randint(0, 1000)
            ours.addAtHead(val)
            oracle.addAtHead(val)
        elif op == "addAtTail":
            val = rng.randint(0, 1000)
            ours.addAtTail(val)
            oracle.addAtTail(val)
        elif op == "addAtIndex":
            idx = rng.randint(-2, cur_size + 2)
            val = rng.randint(0, 1000)
            ours.addAtIndex(idx, val)
            oracle.addAtIndex(idx, val)
        else:
            idx = rng.randint(-2, cur_size + 2)
            ours.deleteAtIndex(idx)
            oracle.deleteAtIndex(idx)
        if ours._to_list() != oracle.data:
            mismatch = True
    all_ok &= not mismatch
    print(f"{'PASS' if not mismatch else 'FAIL'}  2000 randomized ops, state matches array oracle throughout")

    # ------------------------------------------------------------------
    # BENCHMARK — addAtTail: doubly linked (O(1), tail pointer) vs singly
    # linked head-only (O(n), full walk every time). REAL measured numbers.
    # ------------------------------------------------------------------
    print("\n--- benchmark: addAtTail x N — doubly linked (tail ptr) vs singly linked (no tail) ---")
    for n in (500, 1500, 3000):
        fast = MyLinkedList()
        t0 = time.perf_counter()
        for i in range(n):
            fast.addAtTail(i)
        t1 = time.perf_counter()
        fast_ms = (t1 - t0) * 1000

        slow = MyLinkedListSinglyHeadOnly()
        t0 = time.perf_counter()
        for i in range(n):
            slow.addAtTail(i)
        t1 = time.perf_counter()
        slow_ms = (t1 - t0) * 1000

        slowdown = slow_ms / fast_ms if fast_ms > 0 else float("inf")
        print(f"  n={n:>5}   doubly-linked: {fast_ms:>8.2f}ms   singly-linked: {slow_ms:>8.2f}ms   {slowdown:>6.1f}x slower")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
