"""
================================================================================
SOLUTION · LeetCode 705 · Design HashSet                                  [Easy]
https://leetcode.com/problems/design-hashset/
================================================================================

THE CORE IDEA
--------------
A hash table is an ARRAY plus a HASH FUNCTION that maps a key to an array
index, plus a COLLISION-RESOLUTION policy for when two keys land on the same
index. With `0 <= key <= 10^6` and at most 10^4 calls, `key % NUM_BUCKETS`
for a modest prime `NUM_BUCKETS` (here 769) keeps the average bucket length
close to 1, which is exactly what makes "O(1) average" hold — it is an
AVERAGE, not a worst-case guarantee (an adversarial key set that's all
congruent mod 769 would still degrade to O(n)).


================================================================================
APPROACH 1 · Python list, linear scan (brute force, priced, not coded)
================================================================================
A single flat Python list; `add` appends if not already present (an O(n)
scan first, to respect the "no duplicates" contract), `remove`/`contains`
each do an O(n) scan.

    Time: O(n) per operation.     Space: O(n).

This is what every operation degrades to in the separate-chaining approach
below if you pick `NUM_BUCKETS = 1` — i.e. "one big bucket." It is not
coded here because it's a direct ancestor of Approach 2 with the bucket
count fixed at 1, and the benchmark below demonstrates the difference by
varying the bucket count on the SAME chaining implementation instead.


================================================================================
APPROACH 2 · Separate chaining ✅ (the answer)
================================================================================
    NUM_BUCKETS = 769   # prime, modest size relative to <=10^4 calls

    class MyHashSet:
        def __init__(self):
            self.buckets = [[] for _ in range(NUM_BUCKETS)]

        def _bucket(self, key):
            return self.buckets[key % NUM_BUCKETS]

        def add(self, key):
            bucket = self._bucket(key)
            if key not in bucket:
                bucket.append(key)

        def remove(self, key):
            bucket = self._bucket(key)
            if key in bucket:
                bucket.remove(key)

        def contains(self, key):
            return key in self._bucket(key)

Each bucket is an independent small list; `key % NUM_BUCKETS` routes each
op to exactly one bucket, and the scan inside that bucket costs O(bucket
length), which stays O(1) on average as long as the bucket count is on the
same order as the key count.

    Time: O(1) average per op (O(load factor) = O(n / NUM_BUCKETS)).
    Space: O(n + NUM_BUCKETS).


================================================================================
APPROACH 3 · Open addressing, linear probing (variant, coded as an oracle)
================================================================================
ONE flat array of fixed size (no buckets-of-lists). On collision, probe
`(h+1) % SIZE`, `(h+2) % SIZE`, ... until an empty or matching slot is
found. Deletion needs a TOMBSTONE marker (not just clearing the slot),
because clearing a slot outright would break the probe chain for keys
inserted after it that had to skip over it.

    SIZE = 10**6 + 1     # dense enough that direct indexing works cleanly
    EMPTY, TOMBSTONE = object(), object()

    class MyHashSetOpenAddressing:
        def __init__(self):
            self.slots = [EMPTY] * SIZE     # since key <= 10^6, key IS the slot

Because this problem's key range is small and dense (`<= 10^6`), open
addressing degenerates to "just index the array by the key directly" —
there's no real hashing left to demonstrate, so it's included below purely
as a correctness oracle for cross-checking, using DIRECT indexing (no
probing needed since one slot per possible key value already avoids all
collisions). This is why chaining, not open addressing, is "the answer"
for THIS problem — open addressing shines when the key space is either
unbounded or sparse relative to available memory, which forces a genuinely
smaller table and real probing; here the key space is small enough that
direct indexing is strictly simpler and equally correct.


================================================================================
STEP BY STEP TRACE — NUM_BUCKETS = 5 (shrunk for a readable trace)
================================================================================
    add(1)        bucket = 1 % 5 = 1        buckets[1] = [1]
    add(2)        bucket = 2 % 5 = 2        buckets[2] = [2]
    contains(1)   bucket = 1 % 5 = 1        1 in [1] -> True
    contains(3)   bucket = 3 % 5 = 3        3 in [] -> False
    add(2)        bucket = 2 % 5 = 2        2 already in [2] -> no-op
    contains(2)   bucket = 2 % 5 = 2        2 in [2] -> True
    remove(2)     bucket = 2 % 5 = 2        buckets[2] = []
    contains(2)   bucket = 2 % 5 = 2        2 in [] -> False

    ASCII, buckets after add(1), add(2), add(6):   (6 % 5 == 1, collides with 1)

        buckets[0] = []
        buckets[1] = [1, 6]      <- collision, chained in the same bucket's list
        buckets[2] = [2]
        buckets[3] = []
        buckets[4] = []


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time (per op)     Space           Mutates input?
    ---------------------------------  ----------------  --------------  ---------------
    Flat list, linear scan            O(n)              O(n)            n/a — design problem
    Separate chaining ✅              O(1) average       O(n + buckets)  n/a — design problem
    Open addressing (direct index)    O(1) worst case    O(key range)    n/a — design problem
                                       (key range small & dense here)


================================================================================
EDGE CASES
================================================================================
    add(key) already present          Must stay a no-op (no duplicate stored,
                                       and no crash).
    remove(key) not present           Must be a silent no-op, not an error.
    contains on a never-added key     Must return False, not raise.
    key == 0                          Valid per constraints; `0 % NUM_BUCKETS
                                       == 0` must route correctly, not be
                                       mistaken for "falsy = absent."
    Many keys colliding into one bucket  Correctness must hold even though
                                       that bucket's list grows long — this
                                       is what the benchmark stresses.


================================================================================
COMMON MISTAKES
================================================================================
1. Using `NUM_BUCKETS = 1` (or forgetting a modulus entirely) — collapses
   every operation to a full O(n) scan, defeating the entire point of
   hashing while still being "technically correct."

2. `add` appending a duplicate without checking `if key not in bucket`
   first — breaks the set invariant (no duplicates) even though `contains`
   might still accidentally "look" correct via short-circuiting on the
   first match.

3. Treating `key == 0` as falsy and special-casing it away — 0 is a valid
   key per constraints (`0 <= key <= 10^6`).

4. Picking a non-prime, round bucket count (e.g. 1000 or 1024) when keys
   are likely to share common factors with it (e.g. all multiples of 100)
   — systematically clusters keys into a small subset of buckets. A prime
   bucket count avoids this for arithmetic-progression key sets.

5. Forgetting a TOMBSTONE marker in open-addressing deletion (not an issue
   for the direct-index variant here, but a classic bug the moment probing
   is actually needed) — clearing a slot outright breaks the probe chain
   for any key inserted after it that had to skip past it.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if the key range were unbounded (any 64-bit integer, not just
   `<= 10^6`)?
A: Open addressing's "direct index the key" shortcut stops working; you'd
   need a real hash function (e.g. multiplicative hashing) plus either
   chaining or probing over a table sized well below the key range, and a
   resize/rehash policy once the load factor crosses a threshold.

Q: How would you resize the bucket array as more keys are added?
A: Track load factor `n / NUM_BUCKETS`; once it crosses ~0.75, allocate a
   new array roughly double the size and re-insert every existing key
   (rehash) — the classic dynamic-array-style amortized growth, applied to
   the bucket count instead of a single array's length.

Q: Thread safety for concurrent add/remove/contains?
A: Either one coarse lock around all three methods, or a lock PER BUCKET
   for finer-grained concurrency, given each bucket is already the unit of
   independent state — bucket-level locks let unrelated keys proceed in
   parallel.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 706  Design HashMap                  — same chaining/probing machinery, key->value
    LC 146  LRU Cache (topic 08)            — dict (here: hand-built) + doubly linked list
    LC 380  Insert Delete GetRandom O(1)    — array + index map, different O(1) goal (random access)
    Topic 01 · Arrays & Hashing             — every hashing pattern this topic hand-builds from scratch
================================================================================
"""

import random
import time


NUM_BUCKETS = 769  # prime; modest relative to <= 10^4 calls in constraints


class MyHashSet:
    """Separate chaining: array of buckets, each bucket a small list."""

    def __init__(self):
        self.buckets: list[list[int]] = [[] for _ in range(NUM_BUCKETS)]

    def _bucket(self, key: int) -> list[int]:
        return self.buckets[key % NUM_BUCKETS]

    def add(self, key: int) -> None:
        bucket = self._bucket(key)
        if key not in bucket:
            bucket.append(key)

    def remove(self, key: int) -> None:
        bucket = self._bucket(key)
        if key in bucket:
            bucket.remove(key)

    def contains(self, key: int) -> bool:
        return key in self._bucket(key)


# ------------------------------------------------------------------------
# Alternatives / oracles.
# ------------------------------------------------------------------------
class MyHashSetOpenAddressing:
    """Approach 3: direct-index array (key range is small & dense here, so
    no probing is ever actually needed) — used as a correctness oracle."""

    SIZE = 10**6 + 1

    def __init__(self):
        self.present = bytearray(self.SIZE)  # 0 = absent, 1 = present

    def add(self, key: int) -> None:
        self.present[key] = 1

    def remove(self, key: int) -> None:
        self.present[key] = 0

    def contains(self, key: int) -> bool:
        return bool(self.present[key])


class MyHashSetOneBucket:
    """✗ ANTI-PATTERN, priced on purpose — same chaining code as the real
    answer, but NUM_BUCKETS forced to 1, so every op is a full O(n) scan.
    Demonstrates exactly what a bad hash-function choice costs. See
    APPROACH 1 above."""

    def __init__(self):
        self.bucket: list[int] = []

    def add(self, key: int) -> None:
        if key not in self.bucket:
            self.bucket.append(key)

    def remove(self, key: int) -> None:
        if key in self.bucket:
            self.bucket.remove(key)

    def contains(self, key: int) -> bool:
        return key in self.bucket


# ==============================================================================
# TESTS — run:  python 001_design_hashset_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    # ------------------------------------------------------------------
    # Correctness: LeetCode's canonical example, cross-checked against
    # the open-addressing oracle.
    # ------------------------------------------------------------------
    print("--- correctness: separate chaining vs open-addressing oracle ---")
    script = [
        ("add", 1, None), ("add", 2, None),
        ("contains", 1, True), ("contains", 3, False),
        ("add", 2, None), ("contains", 2, True),
        ("remove", 2, None), ("contains", 2, False),
    ]
    impls = {
        "chaining   ": MyHashSet(),
        "open-addr  ": MyHashSetOpenAddressing(),
    }
    for name, impl in impls.items():
        results = []
        for op, key, _want in script:
            fn = getattr(impl, op)
            results.append(fn(key))
        wants = [want for _, _, want in script]
        ok = results == wants
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}  results={results}  (want {wants})")

    # ------------------------------------------------------------------
    # remove on an absent key, add of an existing key: both no-ops.
    # ------------------------------------------------------------------
    print("\n--- no-op edge cases ---")
    hs = MyHashSet()
    hs.remove(42)
    ok = hs.contains(42) is False
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  remove on never-added key is a no-op")

    hs.add(0)
    hs.add(0)
    ok = hs.contains(0) is True
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  key 0 (falsy-looking) handled correctly, double-add is a no-op")

    # ------------------------------------------------------------------
    # Randomized cross-check vs the open-addressing oracle.
    # ------------------------------------------------------------------
    print("\n--- randomized cross-check (3000 ops) ---")
    rng = random.Random(11)
    ours = MyHashSet()
    oracle = MyHashSetOpenAddressing()
    mismatch = False
    for _ in range(3000):
        key = rng.randint(0, 5000)
        op = rng.choice(["add", "remove", "contains"])
        r1 = getattr(ours, op)(key)
        r2 = getattr(oracle, op)(key)
        if r1 != r2:
            mismatch = True
    all_ok &= not mismatch
    print(f"{'PASS' if not mismatch else 'FAIL'}  3000 randomized ops, no mismatch vs oracle")

    # ------------------------------------------------------------------
    # BENCHMARK — chaining with a real bucket count vs chaining forced to
    # a single bucket (NUM_BUCKETS=1). REAL measured numbers.
    # ------------------------------------------------------------------
    print("\n--- benchmark: 769 buckets vs 1 bucket (same chaining code) ---")
    n_ops = 8000
    rng = random.Random(3)
    keys = [rng.randint(0, 20000) for _ in range(n_ops)]

    fast = MyHashSet()
    t0 = time.perf_counter()
    for k in keys:
        fast.add(k)
        fast.contains(k)
    t1 = time.perf_counter()
    fast_ms = (t1 - t0) * 1000

    slow = MyHashSetOneBucket()
    t0 = time.perf_counter()
    for k in keys:
        slow.add(k)
        slow.contains(k)
    t1 = time.perf_counter()
    slow_ms = (t1 - t0) * 1000

    slowdown = slow_ms / fast_ms if fast_ms > 0 else float("inf")
    print(f"  {n_ops} ops   769 buckets: {fast_ms:.2f}ms   1 bucket: {slow_ms:.2f}ms   {slowdown:.1f}x slower")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
