package main

/*
================================================================================
LeetCode 707 · Design Linked List                                       [Medium]
https://leetcode.com/problems/design-linked-list/
Topic: 25 · Design
================================================================================

PROBLEM
-------
Design your own implementation of a linked list. It can be singly or
doubly linked. A node should have `val` and a `next` pointer (and,
optionally, a `prev` pointer if doubly linked).

Implement the `MyLinkedList` class:

    MyLinkedList()                     Initializes the object (empty list).
    get(index) -> int                  Return the value of the `index`-th
                                        node (0-indexed). Return -1 if
                                        invalid.
    addAtHead(val) -> None             Insert a node with value `val`
                                        before the first element.
    addAtTail(val) -> None             Append a node with value `val` to
                                        the end.
    addAtIndex(index, val) -> None     Insert a node with value `val`
                                        BEFORE the `index`-th node.
                                        - `index == length`: append at tail.
                                        - `index > length`: node is NOT
                                          inserted.
                                        - `index < 0`: treated as inserting
                                          at the head.
    deleteAtIndex(index) -> None       Delete the `index`-th node if valid.


EXAMPLES
--------
Example 1:
    Input:
        ["MyLinkedList", "addAtHead", "addAtTail", "addAtIndex", "get",
         "deleteAtIndex", "get"]
        [[], [1], [3], [1, 2], [1], [1], [1]]
    Output:
        [null, null, null, null, 2, null, 3]

    Explanation:
        ll = MyLinkedList()
        ll.addAtHead(1)        # list: 1
        ll.addAtTail(3)        # list: 1 -> 3
        ll.addAtIndex(1, 2)    # list: 1 -> 2 -> 3   (insert 2 before index 1)
        ll.get(1)              # returns 2
        ll.deleteAtIndex(1)    # list: 1 -> 3         (remove index 1, was 2)
        ll.get(1)              # returns 3


CONSTRAINTS
-----------
    0 <= index, val <= 1000
    Please do NOT use the built-in LinkedList library.
    At most 2000 calls will be made to get, addAtHead, addAtTail,
    addAtIndex, and deleteAtIndex.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is a from-scratch linked-list implementation with INDEX-based access,
unlike most linked-list problems in topic 08 which operate on node
REFERENCES directly. The core design decision: singly vs. doubly linked,
and whether to maintain a `size` counter and a `tail` pointer alongside
`head` — all three of those are what make `addAtTail` and out-of-range
checks O(1)/O(range-checked) instead of requiring a full traversal first
just to find the end or validate the index.

Two sentinel (dummy) nodes — a dummy head AND a dummy tail — eliminate
every empty-list / insert-at-boundary special case, the exact idiom from
topic 08's LRU Cache (013), doubled up here for index-based traversal
instead of recency-based splicing.


WHAT TO THINK ABOUT
--------------------
1. Maintaining a running `size` (incremented/decremented on every
   insert/delete) turns "is this index valid?" into an O(1) comparison
   instead of walking the list to discover its length first.

2. `addAtIndex` has THREE distinct index-range cases baked into the spec:
   `index < 0` (clamp to head), `index == size` (append at tail), `index >
   size` (no-op, do nothing) — get these three boundaries wrong and half
   the LeetCode test cases fail on off-by-ones.

3. A DOUBLY linked list with a tail pointer makes `addAtTail` O(1) instead
   of O(n) (no need to walk from head to find the last node), at the cost
   of maintaining `.prev` pointers on every splice.

4. `get`/`addAtIndex`/`deleteAtIndex` all need to walk from `head` to reach
   position `index` — with a doubly linked list, walking from whichever
   end (head or tail) is CLOSER to `index` roughly halves the average
   traversal distance.


PROGRESSIVE HINTS
------------------
Hint 1: Track a `size` field. Every insert/delete updates it — this turns
        index-validity checks into O(1) arithmetic instead of a traversal.

Hint 2: Two sentinel nodes (dummy head, dummy tail) remove all "is the list
        empty" / "am I inserting at the very front/back" special casing —
        same idiom as LRU Cache (topic 08, 013), just walked by index here
        instead of by recency.

Hint 3: Write one internal helper, `_node_at(index)`, that walks from head
        (or from whichever end is closer, if doubly linked) to the node
        currently at that index — `get`, `addAtIndex`, and
        `deleteAtIndex` are all thin wrappers around it plus a splice.


COMPLEXITY TARGET
------------------
    get / addAtIndex / deleteAtIndex:  O(min(index, size - index)) time
                                        (O(n) worst case; O(1) is NOT
                                        achievable for arbitrary index
                                        access on a linked list)
    addAtHead:                          O(1) time
    addAtTail:                          O(1) time (WITH a maintained tail
                                        pointer — O(n) without one)
    Space: O(n)
================================================================================
*/

// TODO: Implement the stub
