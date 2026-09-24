package main

/*
================================================================================
LeetCode 146 · LRU Cache                                                [Medium]
https://leetcode.com/problems/lru-cache/
Topic: 08 · Linked List
================================================================================

PROBLEM
-------
Design a data structure that follows the constraints of a Least Recently
Used (LRU) cache.

Implement:

    Constructor(capacity int) LRUCache
    (c *LRUCache) Get(key int) int          -- return value, or -1 if absent
    (c *LRUCache) Put(key int, value int)   -- insert/update; evict LRU key
                                                if capacity would be exceeded

Both Get and Put must run in O(1) average time. Touching a key (via Get or
Put) makes it the most-recently-used key.


EXAMPLES
--------
    cache := Constructor(2)
    cache.Put(1, 1)   // {1=1}
    cache.Put(2, 2)   // {1=1, 2=2}
    cache.Get(1)      // returns 1, 1 becomes MRU
    cache.Put(3, 3)   // evicts key 2 (LRU)
    cache.Get(2)      // returns -1
    cache.Put(4, 4)   // evicts key 1 (LRU)
    cache.Get(1)      // returns -1
    cache.Get(3)      // returns 3
    cache.Get(4)      // returns 4


CONSTRAINTS
-----------
    1 <= capacity <= 3000
    0 <= key <= 10^4
    0 <= value <= 10^5
    At most 2*10^5 calls to Get and Put combined.

FOLLOW UP
---------
    Could you do Get and Put in O(1) time complexity?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Topic guide Part 10: O(1) Get/Put needs BOTH a map (O(1) lookup by key) AND
a doubly linked list (O(1) reordering to MRU, O(1) eviction of LRU). Neither
structure alone is sufficient — a map has no notion of order; a singly
linked list can't unlink an arbitrary node in O(1) without its predecessor,
which only a doubly linked list gives you for free on every node.

The map stores NODE POINTERS (map[int]*dNode), not values — promoting or
evicting a key mutates the SAME node the map already points at, so the map
itself only needs updating on insert and eviction, never on a pure reorder.

Two sentinel nodes (head, tail) eliminate all empty-list / single-node
special casing from remove/insertFront — the doubled-up version of this
topic's Part 2 dummy-node idiom.


PROGRESSIVE HINTS
------------------
Hint 1: You need map[int]*dNode AND a doubly linked list of dNode, not just
        one structure.
Hint 2: Sentinel head/tail nodes remove all empty/single-node special cases.
Hint 3: Write remove(n) and insertFront(n) as two small helpers first — Get
        and Put become compositions of those plus a map lookup/write.


COMPLEXITY TARGET
------------------
    Get:  O(1)
    Put:  O(1)
    Space: O(capacity)
================================================================================
*/

// YourLRUCache is a stub so this file compiles without a main(). Implement
// the real design in solution.go's LRUCache type.
type YourLRUCache struct{}
