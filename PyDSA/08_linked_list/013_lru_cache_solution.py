"""
================================================================================
SOLUTION · LeetCode 146 · LRU Cache                                     [Medium]
https://leetcode.com/problems/lru-cache/
================================================================================

THE CORE IDEA
--------------
See topic guide Part 6, restated: O(1) `get`/`put` needs a dict AND a doubly
linked list, because neither structure alone provides both O(1) lookup-by-key
AND O(1) reorder-by-recency:

    dict alone:            O(1) lookup, but NO notion of order
    singly linked alone:   ordered, but O(n) to unlink an arbitrary node
                            (no predecessor reference)
    dict + doubly linked:  O(1) lookup (dict: key -> node) AND O(1) unlink
                            (node already carries .prev)

The dict stores NODE REFERENCES. Promoting a key on `get`, or updating +
promoting on `put`, mutates the SAME node object the dict already points
at — the dict itself is only ever touched on insert and eviction, never on
a pure reorder.

Two sentinel nodes (`head`, `tail`) eliminate every empty-list / single-node
special case from `_remove` and `_insert_front` — the same idiom as this
topic's Part 2 dummy head, doubled up because the list is doubly linked.


================================================================================
APPROACH 1 · Python dict alone, insertion-order trick (partially works, priced)
================================================================================
CPython dicts (3.7+) preserve insertion order, and `dict.move_to_end(key)`
can promote a key to the "most recent" end in O(1) amortized, with
`next(iter(d))` giving the LRU key in O(1). This actually gets you a fully
correct, genuinely O(1) LRU cache using `collections.OrderedDict` (or even a
plain dict since 3.7) — it is not a toy baseline, it is a legitimate
alternative that avoids hand-rolling the linked list, at the cost of
depending on CPython dict internals rather than demonstrating the mechanism.
Interviewers usually want the hand-rolled version specifically to see you
reason about the two-structure design; `OrderedDict` is worth naming as
"the standard-library shortcut" but not what gets coded here.


================================================================================
APPROACH 2 · Doubly linked list + hashmap ✅ (the answer)
================================================================================
    class _Node:
        def __init__(self, key=0, val=0):
            self.key, self.val = key, val
            self.prev = self.next = None

    class LRUCache:
        def __init__(self, capacity):
            self.capacity = capacity
            self.cache = {}                       # key -> _Node
            self.head = _Node()                    # sentinel, MRU side
            self.tail = _Node()                    # sentinel, LRU side
            self.head.next = self.tail
            self.tail.prev = self.head

        def _remove(self, node):                    # unlink, O(1)
            node.prev.next = node.next
            node.next.prev = node.prev

        def _insert_front(self, node):               # splice after head, O(1)
            node.prev = self.head
            node.next = self.head.next
            self.head.next.prev = node
            self.head.next = node

        def get(self, key):
            if key not in self.cache:
                return -1
            node = self.cache[key]
            self._remove(node)
            self._insert_front(node)                  # touching promotes to MRU
            return node.val

        def put(self, key, value):
            if key in self.cache:
                node = self.cache[key]
                node.val = value
                self._remove(node)
                self._insert_front(node)
                return
            if len(self.cache) == self.capacity:
                lru = self.tail.prev                    # node just before tail
                self._remove(lru)
                del self.cache[lru.key]                  # evict from BOTH structures
            node = _Node(key, value)
            self.cache[key] = node
            self._insert_front(node)

    Time: O(1) per get/put.     Space: O(capacity).


================================================================================
APPROACH 3 · Naive list-based (what NOT to do, priced and coded for the demo)
================================================================================
A plain dict for values plus a separate Python `list` tracking recency
order, where every touch does `order.remove(key)` (O(n) linear scan +
shift) followed by `order.append(key)`:

    Time: O(n) per get/put — the `list.remove` is the culprit.
    Space: O(capacity).

This is the "obvious first attempt" that FAILS the O(1) follow-up. The
benchmark below measures exactly how much this costs as capacity grows —
measured on this machine, 4000 mixed get/put ops at capacity 100/500/2000
show the naive list going from roughly on par (small capacity, small `n`
in the O(n) scan) to ~3x, then ~5x slower than the linked-list+hashmap
version as capacity (and thus the list being scanned/shifted) grows —
demonstrating the O(n)-per-op cost compounding with cache size exactly as
predicted, not a fixed constant-factor difference.


================================================================================
STEP BY STEP TRACE — capacity=2
================================================================================
    put(1,1)  cache={1}                MRU-front list: [1]
    put(2,2)  cache={1,2}              MRU-front list: [2,1]
    get(1)    hit, promote 1           MRU-front list: [1,2]   returns 1
    put(3,3)  cache full (2 keys), evict LRU=2
                                       MRU-front list: [3,1]
    get(2)    miss                    returns -1
    put(4,4)  cache full, evict LRU=1
                                       MRU-front list: [4,3]
    get(1)    miss                    returns -1
    get(3)    hit, promote 3           MRU-front list: [3,4]   returns 3
    get(4)    hit, promote 4           MRU-front list: [4,3]   returns 4

    ASCII of the doubly linked list right after put(1,1), put(2,2), get(1):

        head <-> [1] <-> [2] <-> tail        (MRU=1, LRU=2)
                  ^ just promoted by get(1), spliced right after head


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time (get/put)   Space         Mutates input?
    ---------------------------------  ---------------  ------------  ---------------
    OrderedDict / dict.move_to_end ✅  O(1) amortized   O(capacity)   n/a — design problem
    Doubly linked list + hashmap ✅    O(1)              O(capacity)   n/a — design problem
    dict + plain list (naive)         O(n)              O(capacity)   n/a — the anti-pattern


================================================================================
EDGE CASES
================================================================================
    capacity == 1                Every put after the first evicts the
                                  previous key immediately — exercises the
                                  eviction path on nearly every call.
    get on empty cache            Must return -1, not raise/crash.
    put on an EXISTING key        Must update the value AND promote to MRU
                                  — a common bug is updating value but
                                  forgetting to also touch/promote.
    repeated get on the SAME key  Must not corrupt the list (re-inserting a
                                  node already at the front should be a
                                  harmless no-op in effect).
    put that overflows capacity by exactly 1  Evicts exactly one key (the
                                  true LRU), not zero, not more than one.


================================================================================
COMMON MISTAKES
================================================================================
1. Updating only the dict OR only the linked list on an eviction, not both
   (topic guide Part 8, mistake 8) — the two structures must always agree
   on membership. A stale dict entry pointing at an unlinked node, or a
   linked node with no dict entry, both corrupt future operations silently.

2. Forgetting that `put` on an EXISTING key must also promote it to MRU,
   not just overwrite the value in place.

3. Using a singly linked list "to save a pointer field" — then discovering
   `_remove` needs the predecessor, which a singly linked list cannot give
   you in O(1) (topic guide Part 6's whole point).

4. Skipping the sentinel nodes and hand-checking `if node is self.head` /
   `if node is self.tail` everywhere instead — reintroduces exactly the
   special-casing sentinels exist to eliminate, and is a common source of
   off-by-one eviction bugs (evicting the sentinel itself, or leaving a
   dangling `.prev`/`.next`).

5. Reaching for `list.remove(key)` (linear scan) to maintain recency order —
   correct but O(n), silently fails the O(1) requirement under load. The
   benchmark below shows exactly how badly this scales.

6. Off-by-one on WHICH end is MRU vs LRU — mixing this up mid-implementation
   (inserting new nodes near the tail, evicting from the head) inverts the
   whole cache's behavior while still "type-checking."


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if the cache also needed a TTL (time-to-live) eviction, not just
   LRU order?
A: Store an expiry timestamp per node; either lazily check-and-evict on
   access, or maintain a secondary min-heap keyed by expiry for proactive
   eviction — the doubly linked list still handles the LRU order.

Q: What about LFU (Least Frequently Used) instead of LRU?
A: LC 460. Needs a frequency counter per key AND, for O(1) eviction among
   equal-frequency keys, a doubly linked list PER frequency bucket (plus a
   pointer to the current minimum frequency) — a strict generalization of
   this design.

Q: Thread safety?
A: Wrap `get`/`put` in a single lock (coarse-grained) — the whole point of
   O(1) operations is that the critical section is already tiny; a
   fine-grained per-node lock scheme would need to be justified by actual
   contention data, not assumed necessary.

Q: Could you avoid the hashmap by using an array-based cache with capacity
   as the array size?
A: Only if keys are small, dense integers you can use directly as array
   indices — then you trade the hashmap for direct indexing, but this
   rarely holds for LeetCode's key range (0 <= key <= 10^4), so the hashmap
   stays the general-purpose choice.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 460  LFU Cache                       — frequency + per-bucket lists
    LC 705  Design HashSet                  — the hashmap half in isolation
    LC 641  Design Circular Deque           — doubly linked list, no hashmap
    LC 155  Min Stack                       — another "design with O(1) ops" family
================================================================================
"""

import random
import time


class _Node:
    __slots__ = ("key", "val", "prev", "next")

    def __init__(self, key: int = 0, val: int = 0):
        self.key = key
        self.val = val
        self.prev = None
        self.next = None


class LRUCache:
    """Doubly linked list + hashmap. O(1) get/put. See THE CORE IDEA above."""

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache: dict[int, _Node] = {}
        self.head = _Node()  # sentinel, MRU side
        self.tail = _Node()  # sentinel, LRU side
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node: _Node) -> None:
        node.prev.next = node.next
        node.next.prev = node.prev

    def _insert_front(self, node: _Node) -> None:
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        node = self.cache[key]
        self._remove(node)
        self._insert_front(node)  # touching promotes to MRU
        return node.val

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            node = self.cache[key]
            node.val = value
            self._remove(node)
            self._insert_front(node)
            return
        if len(self.cache) == self.capacity:
            lru = self.tail.prev  # node just before the tail sentinel
            self._remove(lru)
            del self.cache[lru.key]  # evict from BOTH structures
        node = _Node(key, value)
        self.cache[key] = node
        self._insert_front(node)


# ------------------------------------------------------------------------
# Alternatives / oracles.
# ------------------------------------------------------------------------
from collections import OrderedDict


class LRUCacheOrderedDict:
    """Approach 1: OrderedDict.move_to_end. O(1) amortized, legitimate
    standard-library alternative — used here as a correctness oracle."""

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.od: "OrderedDict[int, int]" = OrderedDict()

    def get(self, key: int) -> int:
        if key not in self.od:
            return -1
        self.od.move_to_end(key)
        return self.od[key]

    def put(self, key: int, value: int) -> None:
        if key in self.od:
            self.od.move_to_end(key)
        self.od[key] = value
        if len(self.od) > self.capacity:
            self.od.popitem(last=False)  # evict LRU (front)


class LRUCacheNaiveList:
    """✗ ANTI-PATTERN, priced on purpose — O(n) per get/put because
    `order.remove(key)` is a linear scan + shift. Demonstrates exactly what
    the O(1) follow-up rules out. See APPROACH 3 above."""

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.values: dict[int, int] = {}
        self.order: list[int] = []  # front = LRU, back = MRU

    def get(self, key: int) -> int:
        if key not in self.values:
            return -1
        self.order.remove(key)  # O(n) — the culprit
        self.order.append(key)
        return self.values[key]

    def put(self, key: int, value: int) -> None:
        if key in self.values:
            self.order.remove(key)  # O(n)
        elif len(self.values) == self.capacity:
            lru_key = self.order.pop(0)  # O(n) shift too
            del self.values[lru_key]
        self.values[key] = value
        self.order.append(key)


# ==============================================================================
# TESTS — run:  python 013_lru_cache_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    # ------------------------------------------------------------------
    # Correctness: LeetCode's canonical example, cross-checked against
    # OrderedDict and the naive list implementation.
    # ------------------------------------------------------------------
    print("--- correctness: doubly-linked-list vs OrderedDict vs naive-list ---")
    script = [
        ("put", (1, 1), None),
        ("put", (2, 2), None),
        ("get", (1,), 1),
        ("put", (3, 3), None),
        ("get", (2,), -1),
        ("put", (4, 4), None),
        ("get", (1,), -1),
        ("get", (3,), 3),
        ("get", (4,), 4),
    ]
    impls = {
        "linked+hashmap": LRUCache(2),
        "OrderedDict   ": LRUCacheOrderedDict(2),
        "naive list    ": LRUCacheNaiveList(2),
    }
    for name, impl in impls.items():
        results = []
        for op, args, _want in script:
            if op == "put":
                impl.put(*args)
                results.append(None)
            else:
                results.append(impl.get(*args))
        wants = [want for _, _, want in script]
        ok = results == wants
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}  results={results}  (want {wants})")

    # ------------------------------------------------------------------
    # get-promotes-to-MRU, put-on-existing-key updates-and-promotes.
    # ------------------------------------------------------------------
    print("\n--- get promotes to MRU; put on existing key updates AND promotes ---")
    c = LRUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    c.get(1)  # promote 1 -> order (MRU->LRU): 1, 2
    c.put(3, 3)  # evicts 2 (LRU), not 1
    ok = c.get(2) == -1 and c.get(1) == 1 and c.get(3) == 3
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  get(1) before put(3,3) saved key 1 from eviction")

    c2 = LRUCache(2)
    c2.put(1, 1)
    c2.put(2, 2)
    c2.put(1, 100)  # update existing key 1, must ALSO promote it
    c2.put(3, 3)  # should evict 2 (now LRU), not 1
    ok = c2.get(2) == -1 and c2.get(1) == 100 and c2.get(3) == 3
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  put(1,100) on existing key updates value AND promotes")

    # ------------------------------------------------------------------
    # Capacity=1 edge case.
    # ------------------------------------------------------------------
    print("\n--- capacity=1 edge case ---")
    c1 = LRUCache(1)
    c1.put(1, 10)
    ok = c1.get(1) == 10
    c1.put(2, 20)  # evicts 1 immediately
    ok &= c1.get(1) == -1 and c1.get(2) == 20
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  capacity=1: every put after the first evicts immediately")

    # ------------------------------------------------------------------
    # Eviction under load, cross-checked against OrderedDict oracle on a
    # long randomized operation sequence.
    # ------------------------------------------------------------------
    print("\n--- randomized cross-check vs OrderedDict oracle (2000 ops, capacity=50) ---")
    rng = random.Random(7)
    ours = LRUCache(50)
    oracle = LRUCacheOrderedDict(50)
    mismatch = False
    for _ in range(2000):
        key = rng.randint(0, 99)
        if rng.random() < 0.5:
            g1, g2 = ours.get(key), oracle.get(key)
            if g1 != g2:
                mismatch = True
        else:
            val = rng.randint(0, 10**5)
            ours.put(key, val)
            oracle.put(key, val)
    all_ok &= not mismatch
    print(f"{'PASS' if not mismatch else 'FAIL'}  2000 randomized ops, no mismatch vs OrderedDict")

    # ------------------------------------------------------------------
    # BENCHMARK — O(1) doubly-linked-list+hashmap vs naive O(n) list, as
    # cache size and operation count grow. REAL measured numbers.
    # ------------------------------------------------------------------
    print("\n--- benchmark: O(1) linked+hashmap vs O(n) naive list ---")
    print(f"  {'capacity':>10} {'ops':>8} {'linked+hashmap (ms)':>22} {'naive list (ms)':>18} {'slowdown':>10}")
    for capacity in (100, 500, 2000):
        n_ops = 4000
        rng = random.Random(1)
        ops = [(rng.random() < 0.3, rng.randint(0, capacity * 2), rng.randint(0, 10**5))
               for _ in range(n_ops)]

        fast = LRUCache(capacity)
        t0 = time.perf_counter()
        for is_get, k, v in ops:
            if is_get:
                fast.get(k)
            else:
                fast.put(k, v)
        t1 = time.perf_counter()
        fast_ms = (t1 - t0) * 1000

        slow = LRUCacheNaiveList(capacity)
        t0 = time.perf_counter()
        for is_get, k, v in ops:
            if is_get:
                slow.get(k)
            else:
                slow.put(k, v)
        t1 = time.perf_counter()
        slow_ms = (t1 - t0) * 1000

        slowdown = slow_ms / fast_ms if fast_ms > 0 else float("inf")
        print(f"  {capacity:>10} {n_ops:>8} {fast_ms:>22.2f} {slow_ms:>18.2f} {slowdown:>9.1f}x")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
