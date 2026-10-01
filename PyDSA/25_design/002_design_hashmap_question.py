"""
================================================================================
LeetCode 706 · Design HashMap                                             [Easy]
https://leetcode.com/problems/design-hashmap/
Topic: 25 · Design
================================================================================

PROBLEM
-------
Design a HashMap WITHOUT using any built-in hash table libraries (no `dict`,
no `collections.*`).

Implement the `MyHashMap` class:

    MyHashMap()                    Initializes the object.
    put(key, value) -> None        Inserts (key, value). If `key` already
                                    exists, updates its value.
    get(key) -> int                Returns the value for `key`, or -1 if
                                    `key` does not exist.
    remove(key) -> None            Removes `key` and its value. No-op if
                                    `key` does not exist.


EXAMPLES
--------
Example 1:
    Input:
        ["MyHashMap", "put", "put", "get", "get", "put", "get", "remove", "get"]
        [[], [1, 1], [2, 2], [1], [3], [2, 1], [2], [2], [2]]
    Output:
        [null, null, null, 1, -1, null, 1, null, -1]

    Explanation:
        m = MyHashMap()
        m.put(1, 1)        # {1=>1}
        m.put(2, 2)        # {1=>1, 2=>2}
        m.get(1)           # 1
        m.get(3)           # -1 (not present)
        m.put(2, 1)        # {1=>1, 2=>1}, overwrite existing key's value
        m.get(2)           # 1
        m.remove(2)        # {1=>1}
        m.get(2)           # -1 (removed)


CONSTRAINTS
-----------
    0 <= key, value <= 10^6
    At most 10^4 calls will be made to put, get, and remove.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is Design HashSet's direct sibling (topic guide Part 0) — same bucket
array + `key % NUM_BUCKETS` hash function, except each bucket now stores
(key, value) PAIRS instead of bare keys, because `get` must return a VALUE,
and `put` on an existing key must UPDATE in place rather than being a no-op.

Every bucket operation (`put`/`get`/`remove`) needs to SCAN its bucket
looking for a matching key — the difference from HashSet is just that once
found, you read/overwrite the second element of the pair instead of
treating presence as a boolean.


WHAT TO THINK ABOUT
--------------------
1. `put` on an EXISTING key must overwrite its value, not append a
   duplicate (key, value) pair into the bucket — a common bug is treating
   `put` as always-append.

2. Same bucket-count trade-off as HashSet: too few buckets degrades toward
   O(n) per op; a bucket count on the order of the expected key count
   keeps buckets short.

3. `get` on a missing key returns -1, not `None`/exception — a sentinel
   value baked into the LeetCode signature.


PROGRESSIVE HINTS
------------------
Hint 1: Reuse the bucket-array-of-lists idea from Design HashSet, but each
        bucket entry is now a `[key, value]` pair (or a small node), not a
        bare key.

Hint 2: `put` must first SCAN the target bucket for an existing `key` — if
        found, update its value in place; only append a new pair if not
        found.

Hint 3: `get`/`remove` also scan the target bucket for a matching key;
        `remove` deletes that one element from the bucket's list.


COMPLEXITY TARGET
------------------
    put / get / remove:  O(1) average time
    Space: O(n + b)  where n = number of keys stored, b = bucket count
================================================================================
"""


class MyHashMap:
    def __init__(self):
        # YOUR CODE HERE
        pass

    def put(self, key: int, value: int) -> None:
        # YOUR CODE HERE
        pass

    def get(self, key: int) -> int:
        # YOUR CODE HERE
        pass

    def remove(self, key: int) -> None:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 002_design_hashmap_question.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    m = MyHashMap()
    m.put(1, 1)
    m.put(2, 2)
    ops = [
        (m.get(1), 1),
        (m.get(3), -1),
        (m.put(2, 1), None),
        (m.get(2), 1),
        (m.remove(2), None),
        (m.get(2), -1),
    ]
    for got, want in ops:
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  got={got}  want={want}")

    # remove on a key that was never inserted should be a silent no-op.
    m2 = MyHashMap()
    m2.remove(99)
    ok = m2.get(99) == -1
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  remove on absent key is a no-op")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
