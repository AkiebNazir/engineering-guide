"""
================================================================================
SOLUTION · LeetCode 706 · Design HashMap                                  [Easy]
https://leetcode.com/problems/design-hashmap/
================================================================================

THE CORE IDEA
--------------
Design HashMap's direct sibling to Design HashSet (topic guide Part 0):
same bucket array + `key % NUM_BUCKETS` hash function, except each bucket
now stores `[key, value]` PAIRS instead of bare keys. `put` on an existing
key must find its pair and overwrite the value in place (not append a
duplicate); `get`/`remove` scan the bucket for a matching key the same way
`contains` did in HashSet.


================================================================================
APPROACH 1 · Python list of pairs, linear scan (brute force, priced, not coded)
================================================================================
One flat list of `[key, value]` pairs; every op scans the whole list for a
matching key.

    Time: O(n) per operation.     Space: O(n).

Exactly the "1 bucket" degenerate case of Approach 2 below — not coded
separately for the same reason as HashSet's Approach 1; the benchmark
demonstrates it by forcing the bucket count to 1 on the real chaining code.


================================================================================
APPROACH 2 · Separate chaining ✅ (the answer)
================================================================================
    NUM_BUCKETS = 769

    class MyHashMap:
        def __init__(self):
            self.buckets = [[] for _ in range(NUM_BUCKETS)]   # each: list of [key, value]

        def _bucket(self, key):
            return self.buckets[key % NUM_BUCKETS]

        def put(self, key, value):
            bucket = self._bucket(key)
            for pair in bucket:
                if pair[0] == key:
                    pair[1] = value          # overwrite in place
                    return
            bucket.append([key, value])       # not found -> insert new pair

        def get(self, key):
            for k, v in self._bucket(key):
                if k == key:
                    return v
            return -1

        def remove(self, key):
            bucket = self._bucket(key)
            for i, (k, _) in enumerate(bucket):
                if k == key:
                    bucket.pop(i)
                    return

    Time: O(1) average per op (O(load factor)).     Space: O(n + NUM_BUCKETS).


================================================================================
APPROACH 3 · Open addressing, linear probing (variant, coded as an oracle)
================================================================================
Same key-range trick as HashSet: since `0 <= key <= 10^6`, a flat array of
size `10**6 + 1`, direct-indexed by the key, needs no probing at all — one
slot per possible key, with a separate "presence" sentinel distinguishing
"value 0 stored" from "nothing stored" (both would otherwise look like 0).
Included as a correctness oracle, same rationale as HashSet's Approach 3:
the dense, bounded key range makes open addressing degenerate to direct
indexing, so chaining remains "the answer" for the general technique.


================================================================================
STEP BY STEP TRACE — NUM_BUCKETS = 5 (shrunk for a readable trace)
================================================================================
    put(1, 1)     bucket = 1 % 5 = 1     buckets[1] = [[1,1]]
    put(2, 2)     bucket = 2 % 5 = 2     buckets[2] = [[2,2]]
    get(1)        bucket = 1 % 5 = 1     scan -> [1,1] matches -> return 1
    get(3)        bucket = 3 % 5 = 3     scan -> [] -> return -1
    put(2, 1)     bucket = 2 % 5 = 2     scan -> [2,2] matches key -> overwrite value -> [[2,1]]
    get(2)        bucket = 2 % 5 = 2     scan -> [2,1] matches -> return 1
    remove(2)     bucket = 2 % 5 = 2     scan -> [2,1] matches -> pop it -> buckets[2] = []
    get(2)        bucket = 2 % 5 = 2     scan -> [] -> return -1

    ASCII, buckets after put(1,1), put(2,2), put(6,60):  (6 % 5 == 1, collides with key 1)

        buckets[0] = []
        buckets[1] = [[1, 1], [6, 60]]      <- collision, chained
        buckets[2] = [[2, 2]]
        buckets[3] = []
        buckets[4] = []


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time (per op)     Space           Mutates input?
    ---------------------------------  ----------------  --------------  ---------------
    Flat list of pairs, linear scan   O(n)              O(n)            n/a — design problem
    Separate chaining ✅              O(1) average       O(n + buckets)  n/a — design problem
    Open addressing (direct index)    O(1) worst case    O(key range)    n/a — design problem


================================================================================
EDGE CASES
================================================================================
    put on an EXISTING key            Must overwrite the value, never
                                       create a second pair for the same key.
    get on a never-inserted key       Must return -1, not raise/None.
    remove on an absent key           Silent no-op.
    value == 0                        Must be distinguishable from "key
                                       absent" — the sentinel is -1, not 0,
                                       precisely so a stored 0 stays valid.
    key == 0                          Valid per constraints; must not be
                                       treated as falsy/absent.


================================================================================
COMMON MISTAKES
================================================================================
1. `put` on an existing key appending a SECOND `[key, value]` pair instead
   of overwriting the first — `get` would then return whichever one the
   scan happens to hit first, silently nondeterministic-looking behavior.

2. Using 0 as the "not found" sentinel in a hand-rolled variant instead of
   -1 — collides with a legitimately stored value of 0 (constraints allow
   `0 <= value <= 10^6`).

3. Forgetting `remove` must delete the WHOLE pair from the bucket's list
   (not just clear the value) — a `[key, None]` ghost entry still shows up
   on `get` if the removal logic isn't precise about deleting the entry.

4. Same bucket-count pitfalls as HashSet: too few buckets (or non-prime
   with clustering keys) degrades toward O(n) per op while still
   "working."


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How is this different from Design HashSet?
A: Structurally identical (bucket array + modulus hash + chaining); the
   only change is each bucket stores a (key, value) pair instead of a bare
   key, and `put` must handle the "key already exists, update value" case
   that HashSet's `add` treats as a pure no-op.

Q: How would resizing/rehashing work here?
A: Same as HashSet: track load factor `n / NUM_BUCKETS`, and once it
   crosses a threshold (commonly ~0.75), allocate a bigger bucket array and
   re-insert every (key, value) pair — each pair's NEW bucket index changes
   because the modulus base changed.

Q: Could you use a `[key, value]` pair's position for O(1) removal instead
   of scanning the bucket?
A: Only by also maintaining a secondary key->bucket-position index (paying
   extra space for a speed you already have on average) — not worth it
   here since the bucket itself is expected to stay short if load factor
   is controlled; this is the same trade LRU Cache's dict->node reference
   makes, just not needed at this problem's scale.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 705  Design HashSet                  — the same machinery without values
    LC 146  LRU Cache (topic 08)            — dict (here: hand-built) + doubly linked list
    LC 460  LFU Cache (this topic, 008)     — dict + frequency-bucketed doubly linked lists
    Topic 01 · Arrays & Hashing             — every hashing pattern this topic hand-builds from scratch
================================================================================
"""

import random
import time


NUM_BUCKETS = 769  # prime; modest relative to <= 10^4 calls in constraints


class MyHashMap:
    """Separate chaining: array of buckets, each bucket a list of [key, value]."""

    def __init__(self):
        self.buckets: list[list[list[int]]] = [[] for _ in range(NUM_BUCKETS)]

    def _bucket(self, key: int) -> list[list[int]]:
        return self.buckets[key % NUM_BUCKETS]

    def put(self, key: int, value: int) -> None:
        bucket = self._bucket(key)
        for pair in bucket:
            if pair[0] == key:
                pair[1] = value
                return
        bucket.append([key, value])

    def get(self, key: int) -> int:
        for k, v in self._bucket(key):
            if k == key:
                return v
        return -1

    def remove(self, key: int) -> None:
        bucket = self._bucket(key)
        for i, (k, _v) in enumerate(bucket):
            if k == key:
                bucket.pop(i)
                return


# ------------------------------------------------------------------------
# Alternatives / oracles.
# ------------------------------------------------------------------------
class MyHashMapOpenAddressing:
    """Approach 3: direct-index array with an explicit presence sentinel
    (0 <= value <= 10^6, so -1 can't collide with a stored value) — used as
    a correctness oracle."""

    SIZE = 10**6 + 1

    def __init__(self):
        self.values = [-1] * self.SIZE

    def put(self, key: int, value: int) -> None:
        self.values[key] = value

    def get(self, key: int) -> int:
        return self.values[key]

    def remove(self, key: int) -> None:
        self.values[key] = -1


class MyHashMapOneBucket:
    """✗ ANTI-PATTERN, priced on purpose — same chaining code as the real
    answer, but NUM_BUCKETS forced to 1, so every op is a full O(n) scan.
    See APPROACH 1 above."""

    def __init__(self):
        self.bucket: list[list[int]] = []

    def put(self, key: int, value: int) -> None:
        for pair in self.bucket:
            if pair[0] == key:
                pair[1] = value
                return
        self.bucket.append([key, value])

    def get(self, key: int) -> int:
        for k, v in self.bucket:
            if k == key:
                return v
        return -1

    def remove(self, key: int) -> None:
        for i, (k, _v) in enumerate(self.bucket):
            if k == key:
                self.bucket.pop(i)
                return


# ==============================================================================
# TESTS — run:  python 002_design_hashmap_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    # ------------------------------------------------------------------
    # Correctness: LeetCode's canonical example, cross-checked against the
    # open-addressing oracle.
    # ------------------------------------------------------------------
    print("--- correctness: separate chaining vs open-addressing oracle ---")
    script = [
        ("put", (1, 1), None), ("put", (2, 2), None),
        ("get", (1,), 1), ("get", (3,), -1),
        ("put", (2, 1), None), ("get", (2,), 1),
        ("remove", (2,), None), ("get", (2,), -1),
    ]
    impls = {
        "chaining   ": MyHashMap(),
        "open-addr  ": MyHashMapOpenAddressing(),
    }
    for name, impl in impls.items():
        results = []
        for op, args, _want in script:
            fn = getattr(impl, op)
            results.append(fn(*args))
        wants = [want for _, _, want in script]
        ok = results == wants
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}  results={results}  (want {wants})")

    # ------------------------------------------------------------------
    # value == 0 must not be confused with "absent" (-1 is the sentinel).
    # ------------------------------------------------------------------
    print("\n--- value=0 distinguished from absent (-1 sentinel) ---")
    m = MyHashMap()
    m.put(5, 0)
    ok = m.get(5) == 0 and m.get(6) == -1
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  stored value 0 != sentinel -1 for a truly absent key")

    m.remove(999)  # never inserted -> silent no-op
    ok = m.get(999) == -1
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  remove on never-inserted key is a no-op")

    # ------------------------------------------------------------------
    # Randomized cross-check vs the open-addressing oracle.
    # ------------------------------------------------------------------
    print("\n--- randomized cross-check (3000 ops) ---")
    rng = random.Random(21)
    ours = MyHashMap()
    oracle = MyHashMapOpenAddressing()
    mismatch = False
    for _ in range(3000):
        key = rng.randint(0, 5000)
        op = rng.choice(["put", "get", "remove"])
        if op == "put":
            val = rng.randint(0, 10**5)
            ours.put(key, val)
            oracle.put(key, val)
        else:
            r1 = getattr(ours, op)(key)
            r2 = getattr(oracle, op)(key)
            if r1 != r2:
                mismatch = True
    all_ok &= not mismatch
    print(f"{'PASS' if not mismatch else 'FAIL'}  3000 randomized ops, no mismatch vs oracle")

    # ------------------------------------------------------------------
    # BENCHMARK — chaining with a real bucket count vs forced-to-1-bucket.
    # REAL measured numbers.
    # ------------------------------------------------------------------
    print("\n--- benchmark: 769 buckets vs 1 bucket (same chaining code) ---")
    n_ops = 6000
    rng = random.Random(4)
    keys = [rng.randint(0, 15000) for _ in range(n_ops)]

    fast = MyHashMap()
    t0 = time.perf_counter()
    for k in keys:
        fast.put(k, k)
        fast.get(k)
    t1 = time.perf_counter()
    fast_ms = (t1 - t0) * 1000

    slow = MyHashMapOneBucket()
    t0 = time.perf_counter()
    for k in keys:
        slow.put(k, k)
        slow.get(k)
    t1 = time.perf_counter()
    slow_ms = (t1 - t0) * 1000

    slowdown = slow_ms / fast_ms if fast_ms > 0 else float("inf")
    print(f"  {n_ops} ops   769 buckets: {fast_ms:.2f}ms   1 bucket: {slow_ms:.2f}ms   {slowdown:.1f}x slower")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
