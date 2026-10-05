"""
================================================================================
LeetCode 146 · LRU Cache                                                [Medium]
https://leetcode.com/problems/lru-cache/
Topic: 08 · Linked List
================================================================================

PROBLEM
-------
Design a data structure that follows the constraints of a Least Recently
Used (LRU) cache.

Implement the `LRUCache` class:

    LRUCache(capacity)      Initialize the LRU cache with positive size
                             `capacity`.
    get(key) -> int         Return the value of `key` if it exists,
                             otherwise return -1.
    put(key, value) -> None Update the value of `key` if it exists.
                             Otherwise, add the key-value pair. If the number
                             of keys exceeds `capacity` from this operation,
                             EVICT the least recently used key.

Both `get` and `put` must run in O(1) AVERAGE time complexity.

A key is considered "used" (and becomes most-recently-used) whenever it is
read via `get` OR written via `put`.


EXAMPLES
--------
Example 1:
    Input:
        ["LRUCache", "put", "put", "get", "put", "get", "put", "get", "get", "get"]
        [[2], [1,1], [2,2], [1], [3,3], [2], [4,4], [1], [3], [4]]
    Output:
        [null, null, null, 1, null, -1, null, -1, 3, 4]

    Explanation:
        cache = LRUCache(2)
        cache.put(1, 1)   # cache: {1=1}
        cache.put(2, 2)   # cache: {1=1, 2=2}
        cache.get(1)      # return 1, 1 becomes MRU -> order: {2=2, 1=1}
        cache.put(3, 3)   # evicts key 2 (LRU) -> cache: {1=1, 3=3}
        cache.get(2)      # return -1 (not found)
        cache.put(4, 4)   # evicts key 1 (LRU) -> cache: {3=3, 4=4}
        cache.get(1)      # return -1 (not found)
        cache.get(3)      # return 3
        cache.get(4)      # return 4


CONSTRAINTS
-----------
    1 <= capacity <= 3000
    0 <= key <= 10^4
    0 <= value <= 10^5
    At most 2 * 10^5 calls will be made to get and put.

FOLLOW UP
---------
    Could you do get and put in O(1) time complexity?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is a DESIGN problem, not a search/transform-one-input problem — the
signature is fixed by LeetCode (a class with __init__, get, put), and the
grading harness calls these methods directly, unlike every other problem in
this topic where you implement one free function.

The core insight (topic guide Part 6): O(1) get/put needs TWO data
structures working together, because neither alone is sufficient:

    - A plain dict gives O(1) lookup by key, but has NO notion of order —
      nothing in a dict tells you which key was used longest ago.
    - A SINGLY linked list can order nodes by recency (front = MRU, back =
      LRU), but cannot delete an ARBITRARY node in O(1) — unlinking a node
      requires updating its predecessor's `.next`, and a singly linked list
      gives you no way to find that predecessor without an O(n) scan from
      the head.

A DOUBLY linked list fixes exactly that gap: every node already carries a
reference to its own predecessor, so removing any node you already have a
reference to is O(1) — no scan needed. Combine it with a dict that maps
key -> NODE (not key -> value), so a cache hit gives you the exact node to
unlink and re-splice, in O(1).


WHAT TO THINK ABOUT
--------------------
1. Two sentinel nodes (a dummy head and a dummy tail) eliminate ALL
   empty-list / single-node special casing — the same idiom as this topic's
   Part 2 dummy head, doubled up for a doubly linked list.

2. The dict stores NODE REFERENCES, not values. Promoting or evicting a key
   mutates the SAME node object the dict already points at — you never need
   to touch the dict on a `get`-triggered reorder, only on insert/eviction.

3. Every `get` on an existing key, and every `put` (whether inserting new or
   updating existing), must move that key's node to the MOST-recent end.

4. Eviction on a full cache removes the node adjacent to the TAIL sentinel
   (the least-recently-used end) and must delete it from BOTH the dict and
   the linked list — forgetting one leaves the two structures disagreeing
   about membership (topic guide Part 8, mistake 8).


PROGRESSIVE HINTS
------------------
Hint 1: You need a dict AND a doubly linked list, not just one. Neither
        alone gives O(1) for both lookup-by-key and reorder-by-recency.

Hint 2: The dict maps key -> node object. Two sentinel nodes (head, tail)
        remove all empty/single-node special casing from insert/remove.

Hint 3: Write two small linked-list helpers first — `_remove(node)` (unlink
        a node given a reference to it) and `_insert_front(node)` (splice a
        node in right after the head sentinel) — then `get` and `put` are
        just compositions of these two helpers plus a dict lookup/write.


COMPLEXITY TARGET
------------------
    get:  O(1) time
    put:  O(1) time
    Space: O(capacity)
================================================================================
"""


class LRUCache:
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
# TESTS — run:  python 013_lru_cache_question.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    # Example from LeetCode.
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    ops = [
        (cache.get(1), 1),
        (cache.put(3, 3), None),
        (cache.get(2), -1),
        (cache.put(4, 4), None),
        (cache.get(1), -1),
        (cache.get(3), 3),
        (cache.get(4), 4),
    ]
    for got, want in ops:
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  got={got}  want={want}")

    # Capacity 1 edge case.
    c1 = LRUCache(1)
    c1.put(1, 10)
    ok = c1.get(1) == 10
    c1.put(2, 20)  # evicts 1
    ok &= c1.get(1) == -1
    ok &= c1.get(2) == 20
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  capacity=1 eviction behavior")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
