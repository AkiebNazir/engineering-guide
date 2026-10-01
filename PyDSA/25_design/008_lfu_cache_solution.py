"""
================================================================================
SOLUTION · LeetCode 460 · LFU Cache                                       [Hard]
https://leetcode.com/problems/lfu-cache/
================================================================================

THE CORE IDEA
--------------
LFU Cache is LRU Cache (topic 08, 013) generalized along a SECOND axis:
eviction order is (frequency ASC, then recency ASC within a tied
frequency), not recency alone. LRU's "dict + one doubly linked list"
becomes "dict + ONE DOUBLY LINKED LIST PER FREQUENCY BUCKET", plus a
running `min_freq` pointer so eviction never has to SEARCH for the lowest
frequency currently present — it's always exactly `self.min_freq`.

Three structures, kept in sync on every access:

    key_node:  dict, key -> node (node carries key, val, freq)
    freq_list: dict, freq -> doubly linked list of nodes AT that
               frequency, ordered by recency (front = most recently
               touched at this frequency, back = least)
    min_freq:  int, the smallest frequency with at least one node

A single `_bump(node)` helper does the shared work `get` (on a hit) and
`put` (on an existing key) both need: unlink the node from its CURRENT
frequency bucket, increment `node.freq`, insert it at the FRONT of the
(possibly newly-created) bucket for the new frequency — and advance
`min_freq` if the old bucket just emptied AND was the minimum.


================================================================================
APPROACH 1 · dict + min-heap keyed by (freq, timestamp) (naive, priced,
not coded as the primary — coded as an oracle for cross-checking)
================================================================================
Store `key -> (value, freq, last_used_time)` in a dict; maintain a
min-heap of `(freq, last_used_time, key)`. `get`/`put` on an existing key
push a NEW heap entry with updated freq/time (the old entry becomes
"stale," lazily discarded on pop by checking it against the dict's
current freq/time for that key — a standard lazy-deletion heap pattern).
Eviction pops the heap until it finds a non-stale entry.

    get / put:  O(log n) amortized (heap push/pop), NOT O(1) — fails the
                problem's explicit O(1) requirement, but is a legitimate,
                much-simpler-to-get-right fallback if O(1) weren't
                demanded, and is used below as a correctness oracle since
                it's far less error-prone to implement than Approach 2.
    Space: O(n) live + O(heap operations) stale entries accumulating
           until popped.


================================================================================
APPROACH 2 · dict + per-frequency doubly linked lists + min_freq ✅ (the answer)
================================================================================
    class _Node:
        def __init__(self, key=0, val=0):
            self.key, self.val, self.freq = key, val, 1
            self.prev = self.next = None

    class _DLList:                       # sentinel-headed doubly linked list
        def __init__(self):
            self.head, self.tail = _Node(), _Node()
            self.head.next, self.tail.prev = self.tail, self.head
            self.size = 0

        def push_front(self, node):
            node.prev, node.next = self.head, self.head.next
            self.head.next.prev = node
            self.head.next = node
            self.size += 1

        def remove(self, node):
            node.prev.next, node.next.prev = node.next, node.prev
            self.size -= 1

        def pop_back(self):              # evict: the LRU node AT this frequency
            lru = self.tail.prev
            self.remove(lru)
            return lru

    class LFUCache:
        def __init__(self, capacity):
            self.capacity = capacity
            self.min_freq = 0
            self.key_node = {}                        # key -> node
            self.freq_list = defaultdict(_DLList)      # freq -> _DLList

        def _bump(self, node):
            old_freq = node.freq
            self.freq_list[old_freq].remove(node)
            if not self.freq_list[old_freq].size and self.min_freq == old_freq:
                self.min_freq += 1
            node.freq += 1
            self.freq_list[node.freq].push_front(node)

        def get(self, key):
            if key not in self.key_node:
                return -1
            node = self.key_node[key]
            self._bump(node)
            return node.val

        def put(self, key, value):
            if self.capacity == 0:
                return
            if key in self.key_node:
                node = self.key_node[key]
                node.val = value
                self._bump(node)
                return
            if len(self.key_node) >= self.capacity:
                evict = self.freq_list[self.min_freq].pop_back()
                del self.key_node[evict.key]
            node = _Node(key, value)
            self.key_node[key] = node
            self.freq_list[1].push_front(node)
            self.min_freq = 1              # a new key always starts at freq 1

Why `min_freq = 1` unconditionally on every fresh insert: a brand-new
node's frequency is always exactly 1, and 1 is the smallest possible
frequency any node can ever have — so the new minimum is ALWAYS 1, no
comparison needed.

    Time: O(1) per get/put.     Space: O(capacity).


================================================================================
STEP BY STEP TRACE — capacity=2, the canonical LeetCode script
================================================================================
    put(1,1)   key_node={1}          freq_list={1:[1]}              min_freq=1
    put(2,2)   key_node={1,2}        freq_list={1:[2,1]}             min_freq=1
                                      (2 pushed to FRONT of freq-1 bucket)

    get(1)     bump(1): remove 1 from freq_list[1] -> freq_list[1]=[2] (not
               empty, min_freq unaffected). node1.freq=2.
               push 1 to freq_list[2] -> freq_list={1:[2], 2:[1]}
               returns 1

    put(3,3)   capacity full (2 keys). evict from freq_list[min_freq=1]
               .pop_back() -> that bucket has just [2] -> evict key 2.
               key_node={1,3}. Then insert 3: freq_list[1]=[3]. min_freq=1.
               freq_list={1:[3], 2:[1]}

    get(2)     2 not in key_node -> returns -1

    get(3)     bump(3): remove from freq_list[1] -> freq_list[1]=[] EMPTY,
               and min_freq(1) == old_freq(1) -> min_freq becomes 2.
               node3.freq=2. push to freq_list[2] FRONT -> freq_list[2]=[3,1]
               returns 3

    put(4,4)   capacity full. evict from freq_list[min_freq=2].pop_back()
               -> bucket is [3,1], back is 1 -> evict key 1 (LRU of the tie!)
               key_node={3,4}. insert 4: freq_list[1]=[4]. min_freq=1.
               freq_list={1:[4], 2:[3]}

    get(1)     1 not in key_node -> returns -1
    get(3)     bump(3): freq_list[2]=[] EMPTY but min_freq(1) != old_freq(2)
               -> min_freq stays 1. node3.freq=3. freq_list={1:[4], 3:[3]}
               returns 3
    get(4)     bump(4): freq_list[1]=[] EMPTY, min_freq(1)==old_freq(1) ->
               min_freq becomes... but wait, freq_list[3] still has 3, and
               there's nothing at freq 2 either — min_freq correctly becomes
               2 by the increment rule, even though the TRUE minimum live
               frequency is 3. This is fine: min_freq is only ever READ to
               select an eviction bucket, and freq_list[2] is empty, so
               pop_back() on it would find nothing — see COMMON MISTAKES
               item 3 for why this specific case needs care.
               node4.freq=2. freq_list={2:[4], 3:[3]}
               returns 4

    ASCII, freq_list state right after get(3) that empties freq_list[1]
    and advances min_freq from 1 to 2:

        freq_list[1]:  head <-> tail                (now empty)
        freq_list[2]:  head <-> [3] <-> [1] <-> tail  (3 pushed to front)
                                  ^MRU     ^LRU-of-tie


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                             get/put         Space           Mutates input?
    ------------------------------------  --------------  --------------  ---------------
    dict + min-heap, lazy deletion        O(log n) amort. O(n + stale)   n/a — design problem
    dict + per-freq DLLs + min_freq ✅    O(1)             O(capacity)   n/a — design problem


================================================================================
EDGE CASES
================================================================================
    capacity == 0                        No keys can ever be stored; every
                                          `put` must be a silent no-op
                                          (checked FIRST, before touching
                                          key_node), and `get` always
                                          returns -1.
    Tie at the SAME frequency            Must evict the LEAST RECENTLY
                                          USED among the tied keys — this
                                          is exactly what push-front +
                                          pop-back on the per-frequency
                                          list gives you for free.
    put on an EXISTING key               Counts as a "use" — must ALSO
                                          bump frequency, not just update
                                          the value in place (a common bug
                                          mirrors LRU Cache's mistake #2).
    A frequency bucket emptying that
      is NOT the current min_freq        Must NOT touch `min_freq` — only
                                          the bucket AT min_freq emptying
                                          triggers an increment (see trace
                                          step get(3) → get(4) above, where
                                          `min_freq` legitimately lags the
                                          true minimum live frequency for
                                          one call).
    capacity == 1                        Every put after the first key
                                          immediately evicts — exercises
                                          the eviction path on nearly
                                          every call, same as LRU Cache.
    get on a never-inserted key           Must return -1 and must NOT
                                          create a phantom frequency
                                          bucket entry.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting `put` on an EXISTING key must also bump frequency, not just
   overwrite the value — silently breaks eviction ordering for that key
   from that point on.

2. Advancing `min_freq` unconditionally whenever ANY bucket empties,
   rather than only when the EMPTIED bucket's frequency equals the
   CURRENT `min_freq` — over-advances min_freq and points eviction at the
   wrong (possibly non-existent, possibly wrong-priority) bucket.

3. Assuming `min_freq` always equals the TRUE minimum live frequency at
   every instant — it does not, and does not need to (see the trace's
   final `get(4)` step): it only needs to be correct AT THE MOMENT OF
   EVICTION, i.e. `put` never reads `min_freq` without having just either
   inserted a new key (which resets it to 1) or had the acting node's
   OWN bucket possibly trigger an advance via `_bump` immediately before.
   A DIFFERENT bucket can be transiently "more empty" than min_freq
   claims without breaking correctness, because eviction only ever reads
   `freq_list[min_freq]`, and that specific bucket's occupancy IS kept
   accurate by the increment rule.

4. Using a plain Python list (not a doubly linked list) per frequency
   bucket, with `list.remove(node)` for the "unlink from old bucket" step
   — O(bucket length) instead of O(1), silently reintroducing the exact
   problem LRU Cache's DLL solves, just now once per frequency bucket.

5. Not checking `capacity == 0` before any dict mutation in `put` — a
   `put` call would otherwise insert a node and then immediately need to
   evict it in the SAME call (since `len(key_node) > 0 == capacity`
   immediately), which is more fragile than just short-circuiting first.

6. Using `defaultdict(_DLList)` without ever cleaning up frequency
   buckets that permanently empty — harmless for correctness (an empty
   bucket is never read except by `min_freq`, and dict entries are cheap),
   but worth naming explicitly if an interviewer asks about unbounded
   memory growth in `freq_list`'s KEY SET (not its values) over a very
   long-running cache with many distinct frequencies ever reached.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How is this different from LRU Cache (topic 08, 013)?
A: LRU orders purely by recency (one doubly linked list). LFU adds a
   SECOND ordering axis (frequency) as the primary key and recency as the
   tiebreaker — implemented as one doubly linked list PER frequency value
   instead of one global list, plus the `min_freq` pointer to avoid
   O(distinct frequencies) eviction search.

Q: Could you implement LFU with a single sorted structure (e.g. a
   balanced BST or skip list keyed by (freq, recency)) instead of
   per-frequency linked lists?
A: Yes, but insert/delete/find-min on a balanced BST is O(log n), not
   O(1) — the per-frequency-bucket design exploits that frequencies only
   ever increase by exactly 1 per bump (never jump arbitrarily), which is
   what makes tracking `min_freq` as a simple integer (rather than
   re-deriving a "current minimum" from a general ordered structure)
   sufficient.

Q: How would "frequency decay over time" (so old high-frequency keys
   don't permanently dominate) change this design?
A: That's a materially different problem (often approximated with
   exponential decay / aging counters, e.g. halving all frequencies
   periodically) — it breaks the "frequency only increases by 1"
   invariant this O(1) design relies on, and would likely need
   revisiting the min-heap approach (Approach 1) or a probabilistic
   sketch instead.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 146  LRU Cache (topic 08, 013)        — the single-axis (recency-only) special case of this design
    LC 705  Design HashSet (this topic, 001) — the hashmap half of this design in isolation
    LC 895  Maximum Frequency Stack           — same per-frequency-bucket idea, applied to a stack instead of a cache
    Topic 08 · Linked List                    — the doubly linked splicing this design multiplies across buckets
    Topic 12 · Heap / Priority Queue          — Approach 1's lazy-deletion heap pattern, generally
================================================================================
"""

import heapq
import itertools
import random
import time
from collections import defaultdict


class _Node:
    __slots__ = ("key", "val", "freq", "prev", "next")

    def __init__(self, key: int = 0, val: int = 0):
        self.key = key
        self.val = val
        self.freq = 1
        self.prev = None
        self.next = None


class _DLList:
    """Sentinel-headed doubly linked list: push_front (MRU end), pop_back
    (LRU end), O(1) remove of an arbitrary known node."""

    def __init__(self):
        self.head = _Node()
        self.tail = _Node()
        self.head.next = self.tail
        self.tail.prev = self.head
        self.size = 0

    def push_front(self, node: _Node) -> None:
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node
        self.size += 1

    def remove(self, node: _Node) -> None:
        node.prev.next = node.next
        node.next.prev = node.prev
        self.size -= 1

    def pop_back(self) -> _Node:
        lru = self.tail.prev
        self.remove(lru)
        return lru


class LFUCache:
    """dict + per-frequency doubly linked lists + min_freq. O(1) get/put.
    See THE CORE IDEA above."""

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.min_freq = 0
        self.key_node: dict[int, _Node] = {}
        self.freq_list: dict[int, _DLList] = defaultdict(_DLList)

    def _bump(self, node: _Node) -> None:
        old_freq = node.freq
        self.freq_list[old_freq].remove(node)
        if self.freq_list[old_freq].size == 0 and self.min_freq == old_freq:
            self.min_freq += 1
        node.freq += 1
        self.freq_list[node.freq].push_front(node)

    def get(self, key: int) -> int:
        if key not in self.key_node:
            return -1
        node = self.key_node[key]
        self._bump(node)
        return node.val

    def put(self, key: int, value: int) -> None:
        if self.capacity == 0:
            return
        if key in self.key_node:
            node = self.key_node[key]
            node.val = value
            self._bump(node)
            return
        if len(self.key_node) >= self.capacity:
            evict = self.freq_list[self.min_freq].pop_back()
            del self.key_node[evict.key]
        node = _Node(key, value)
        self.key_node[key] = node
        self.freq_list[1].push_front(node)
        self.min_freq = 1


# ------------------------------------------------------------------------
# Alternatives / oracles.
# ------------------------------------------------------------------------
class LFUCacheHeap:
    """Approach 1: dict + min-heap of (freq, timestamp, key), lazy
    deletion of stale heap entries. O(log n) amortized, NOT O(1) — used
    purely as a correctness oracle since it's much harder to get the
    min_freq bookkeeping subtly wrong here."""

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.data: dict[int, tuple[int, int, int]] = {}  # key -> (value, freq, last_used)
        self.heap: list[tuple[int, int, int]] = []  # (freq, last_used, key)
        self.clock = itertools.count()

    def _touch(self, key: int) -> None:
        value, freq, _ = self.data[key]
        new_freq = freq + 1
        t = next(self.clock)
        self.data[key] = (value, new_freq, t)
        heapq.heappush(self.heap, (new_freq, t, key))

    def get(self, key: int) -> int:
        if key not in self.data:
            return -1
        self._touch(key)
        return self.data[key][0]

    def put(self, key: int, value: int) -> None:
        if self.capacity == 0:
            return
        if key in self.data:
            _, freq, _ = self.data[key]
            t = next(self.clock)
            self.data[key] = (value, freq, t)
            self._touch(key)
            return
        if len(self.data) >= self.capacity:
            while True:
                freq, t, k = heapq.heappop(self.heap)
                if k in self.data and self.data[k][1] == freq and self.data[k][2] == t:
                    del self.data[k]
                    break
        t = next(self.clock)
        self.data[key] = (value, 1, t)
        heapq.heappush(self.heap, (1, t, key))


# ==============================================================================
# TESTS — run:  python 008_lfu_cache_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    # ------------------------------------------------------------------
    # Correctness: LeetCode's canonical example, cross-checked against
    # the heap oracle.
    # ------------------------------------------------------------------
    print("--- correctness: DLL-buckets vs heap oracle ---")
    script = [
        ("put", (1, 1), None), ("put", (2, 2), None),
        ("get", (1,), 1), ("put", (3, 3), None),
        ("get", (2,), -1), ("get", (3,), 3),
        ("put", (4, 4), None), ("get", (1,), -1),
        ("get", (3,), 3), ("get", (4,), 4),
    ]
    for name, impl in (("DLL-buckets ", LFUCache(2)), ("heap oracle  ", LFUCacheHeap(2))):
        results = []
        for op, args, _want in script:
            results.append(getattr(impl, op)(*args))
        wants = [w for _, _, w in script]
        ok = results == wants
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}  results={results}  (want {wants})")

    # ------------------------------------------------------------------
    # capacity == 0: every put is a no-op, every get is -1.
    # ------------------------------------------------------------------
    print("\n--- capacity == 0 ---")
    c0 = LFUCache(0)
    c0.put(1, 1)
    ok = c0.get(1) == -1
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  capacity=0: put is a no-op, get always -1")

    # ------------------------------------------------------------------
    # capacity == 1 edge case.
    # ------------------------------------------------------------------
    print("\n--- capacity == 1 ---")
    c1 = LFUCache(1)
    c1.put(1, 10)
    ok = c1.get(1) == 10
    c1.put(2, 20)  # evicts 1 (only key present)
    ok &= c1.get(1) == -1 and c1.get(2) == 20
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  capacity=1: every put after the first evicts immediately")

    # ------------------------------------------------------------------
    # Tie-breaking: equal frequency, must evict the LEAST recently used
    # of the tied keys.
    # ------------------------------------------------------------------
    print("\n--- tie-break: equal frequency, evict LRU among the tie ---")
    c = LFUCache(3)
    c.put(1, 1)
    c.put(2, 2)
    c.put(3, 3)
    c.get(1)  # freq: 1->2, 2->1, 3->1
    c.get(2)  # freq: 1->2, 2->2, 3->1
    # Now put(3,33) bumps 3 to freq 2 as well — all three now tied at freq 2,
    # in recency order (most-recent-first): 3, 2, 1.
    c.put(3, 33)
    c.put(4, 4)  # capacity full (3), all tied at freq 2 -> evict LRU of tie = key 1
    ok = c.get(1) == -1 and c.get(2) == 2 and c.get(3) == 33 and c.get(4) == 4
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  three-way frequency tie evicts the least-recently-touched key (1)")

    # ------------------------------------------------------------------
    # put on an existing key counts as a use (bumps frequency).
    # ------------------------------------------------------------------
    print("\n--- put on an existing key bumps frequency, not just value ---")
    c2 = LFUCache(2)
    c2.put(1, 1)
    c2.put(2, 2)
    c2.put(1, 100)  # key 1: freq 1->2 via put, not just a value overwrite
    c2.put(3, 3)  # capacity full; 1 has freq 2, 2 has freq 1 -> evict 2
    ok = c2.get(2) == -1 and c2.get(1) == 100 and c2.get(3) == 3
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  put(1,100) bumped key 1's frequency, saving it from eviction over key 2")

    # ------------------------------------------------------------------
    # Randomized cross-check vs the heap oracle on a long operation
    # sequence, capacity small enough that eviction fires constantly.
    # ------------------------------------------------------------------
    print("\n--- randomized cross-check vs heap oracle (3000 ops, capacity=20) ---")
    rng = random.Random(41)
    ours = LFUCache(20)
    oracle = LFUCacheHeap(20)
    mismatch = False
    for _ in range(3000):
        key = rng.randint(0, 40)
        if rng.random() < 0.5:
            r1, r2 = ours.get(key), oracle.get(key)
            if r1 != r2:
                mismatch = True
        else:
            val = rng.randint(0, 10**6)
            ours.put(key, val)
            oracle.put(key, val)
    all_ok &= not mismatch
    print(f"{'PASS' if not mismatch else 'FAIL'}  3000 randomized ops, no mismatch vs heap oracle")

    # ------------------------------------------------------------------
    # BENCHMARK — O(1) DLL-buckets vs O(log n) heap, as call count grows.
    # REAL measured numbers.
    # ------------------------------------------------------------------
    print("\n--- benchmark: DLL-buckets O(1) vs heap O(log n), capacity=500 ---")
    print(f"  {'ops':>8} {'DLL-buckets (ms)':>18} {'heap (ms)':>12} {'speedup':>10}")
    for n_ops in (5000, 20000, 60000):
        rng = random.Random(2)
        ops = [(rng.random() < 0.5, rng.randint(0, 2000), rng.randint(0, 10**6))
               for _ in range(n_ops)]

        fast = LFUCache(500)
        t0 = time.perf_counter()
        for is_get, k, v in ops:
            if is_get:
                fast.get(k)
            else:
                fast.put(k, v)
        t1 = time.perf_counter()
        fast_ms = (t1 - t0) * 1000

        slow = LFUCacheHeap(500)
        t0 = time.perf_counter()
        for is_get, k, v in ops:
            if is_get:
                slow.get(k)
            else:
                slow.put(k, v)
        t1 = time.perf_counter()
        slow_ms = (t1 - t0) * 1000

        speedup = slow_ms / fast_ms if fast_ms > 0 else float("inf")
        print(f"  {n_ops:>8} {fast_ms:>18.2f} {slow_ms:>12.2f} {speedup:>9.1f}x")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
