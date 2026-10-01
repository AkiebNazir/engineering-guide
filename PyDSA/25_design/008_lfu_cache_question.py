"""
================================================================================
LeetCode 460 · LFU Cache                                                  [Hard]
https://leetcode.com/problems/lfu-cache/
Topic: 25 · Design
================================================================================

PROBLEM
-------
Design and implement a Least Frequently Used (LFU) cache.

Implement the `LFUCache` class:

    LFUCache(capacity)       Initializes with positive size `capacity`.
    get(key) -> int          Returns the value of `key` if it exists,
                              otherwise -1.
    put(key, value) -> None  Update the value of `key` if it exists.
                              Otherwise, add the (key, value) pair. If the
                              number of keys exceeds `capacity` from this
                              operation, EVICT the LEAST FREQUENTLY USED
                              key. If there is a TIE (multiple keys with
                              the same lowest use-frequency), evict the
                              LEAST RECENTLY USED among the tied keys.

The use-frequency (usage counter) of a key increments by 1 every time it
is accessed via `get` OR `put` (a `put` on an existing key counts as a use
too, not just an update).

Both `get` and `put` must run in O(1) AVERAGE time complexity.


EXAMPLES
--------
Example 1:
    Input:
        ["LFUCache", "put", "put", "get", "put", "get", "get", "put",
         "get", "get", "get"]
        [[2], [1,1], [2,2], [1], [3,3], [2], [3], [4,4], [1], [3], [4]]
    Output:
        [null, null, null, 1, null, -1, 3, null, -1, 3, 4]

    Explanation:
        c = LFUCache(2)
        c.put(1, 1)   # cache={1=1}                     freq: 1->1
        c.put(2, 2)   # cache={1=1, 2=2}                 freq: 1->1, 2->1
        c.get(1)      # returns 1                        freq: 1->2, 2->1
        c.put(3, 3)   # capacity full, evict LFU. 1 and 2 are TIED at
                       # freq... wait, 1 has freq 2, 2 has freq 1 -> evict
                       # key 2 (freq 1 is strictly lower)
                       # cache={1=1, 3=3}                 freq: 1->2, 3->1
        c.get(2)      # returns -1 (evicted)
        c.get(3)      # returns 3                         freq: 1->2, 3->2
        c.put(4, 4)   # capacity full, 1 and 3 TIED at freq 2 -> evict
                       # the LEAST RECENTLY USED of the tie, which is 1
                       # (3 was touched more recently by the get(3) above)
                       # cache={3=3, 4=4}                 freq: 3->2, 4->1
        c.get(1)      # returns -1 (evicted)
        c.get(3)      # returns 3                         freq: 3->3
        c.get(4)      # returns 4                         freq: 4->2


CONSTRAINTS
-----------
    1 <= capacity <= 10^4
    0 <= key <= 10^5
    0 <= value <= 10^9
    At most 2 * 10^5 calls will be made to get and put.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is a strict generalization of LRU Cache (topic 08, 013) — instead of
ONE recency-ordered list, you need eviction ordered by (frequency, then
recency-within-that-frequency). The O(1) trick: a doubly linked list PER
FREQUENCY BUCKET (dict: `freq -> doubly linked list of nodes at that
frequency, ordered by recency`), plus a `key -> node` dict for O(1)
lookup, plus a running `min_freq` pointer so eviction never has to SEARCH
for the lowest frequency present.


WHAT TO THINK ABOUT
--------------------
1. Every access (`get` on a hit, OR `put` on an existing key) bumps that
   key's frequency by 1 — which means REMOVING the node from its OLD
   frequency bucket's list and INSERTING it at the FRONT (MRU position) of
   the NEW frequency bucket's list.

2. If a bucket becomes EMPTY after removing a node from it, and that
   bucket's frequency equals the current `min_freq`, `min_freq` must
   advance — but only in that specific circumstance; buckets emptying at
   a frequency ABOVE `min_freq` don't affect it.

3. On any `put`, a bumped-frequency node's OLD frequency was, until this
   moment, the definition of `min_freq` in the common case of a
   freshly-inserted key (freq 1) — new insertions ALWAYS reset
   `min_freq = 1`, since a brand-new key starts at frequency 1, which can
   only be `<=` whatever the current minimum was.

4. Eviction removes the LRU (tail) node of the bucket AT `min_freq` — never
   search for "the lowest frequency bucket," since `min_freq` is already
   tracked.


PROGRESSIVE HINTS
------------------
Hint 1: You need THREE things kept in sync: `key -> node` dict, `freq ->
        doubly-linked-list-of-nodes` dict, and a `min_freq` integer.

Hint 2: Write one helper, `_bump(node)`, that removes a node from its
        current frequency bucket, increments its `freq`, and re-inserts it
        at the front of the (possibly new) bucket for that frequency —
        both `get` (on a hit) and `put` (on an existing key) are just
        calls to this helper.

Hint 3: `min_freq` only ever does two things: reset to 1 on a brand-new
        key insertion, or increment by 1 when the CURRENT min_freq
        bucket's list becomes empty as a direct result of a `_bump`.


COMPLEXITY TARGET
------------------
    get:  O(1) time
    put:  O(1) time
    Space: O(capacity)
================================================================================
"""


class LFUCache:
    def __init__(self, capacity: int):
        # YOUR CODE HERE
        pass

    def get(self, key: int) -> int:
        # YOUR CODE HERE
        pass

    def put(self, key: int, value: int) -> None:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 008_lfu_cache_question.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    c = LFUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    ops = [
        (c.get(1), 1),
        (c.put(3, 3), None),
        (c.get(2), -1),
        (c.get(3), 3),
        (c.put(4, 4), None),
        (c.get(1), -1),
        (c.get(3), 3),
        (c.get(4), 4),
    ]
    for got, want in ops:
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  got={got}  want={want}")

    # capacity=1 edge case: every put after the first evicts the previous key.
    c1 = LFUCache(1)
    c1.put(1, 10)
    ok = c1.get(1) == 10
    c1.put(2, 20)  # evicts key 1 immediately (only key present)
    ok &= c1.get(1) == -1 and c1.get(2) == 20
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  capacity=1: every put after the first evicts immediately")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
