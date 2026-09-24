package main

import "fmt"

/*
================================================================================
LeetCode 24 · Swap Nodes in Pairs                                        [Medium]
https://leetcode.com/problems/swap-nodes-in-pairs/
Topic: 28 · Recursion Mastery
================================================================================
PROBLEM
-------
Given the head of a linked list, swap every two adjacent nodes and return
its head. You must solve the problem without modifying the values in the
list's nodes (only nodes themselves may be re-linked).

EXAMPLES
--------
Example 1:
    Input:  head = [1,2,3,4]
    Output: [2,1,4,3]

Example 2:
    Input:  head = []
    Output: []

Example 3:
    Input:  head = [1]
    Output: [1]

CONSTRAINTS
-----------
    The number of nodes in the list is in the range [0, 100].
    0 <= Node.val <= 100

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is the first linked-list problem in the folder — recursion moving
through `.next` links instead of an index range or a shrinking number,
but the shape is still "handle a small piece, then ask a strictly smaller
recursive call to handle the rest, then STITCH the two together."

The key insight: to swap the first PAIR, you need to know what the rest of
the (already-swapped) list looks like, because the second node of the pair
must point to that. So the recursive call happens FIRST, then the current
pair is wired around its result:

    swapPairs(head):
        if head is None or head.next is None: return head    <- 0 or 1 node left
        first, second = head, head.next
        first.next = swapPairs(second.next)                   <- swap the REST first
        second.next = first                                   <- then wire this pair around it
        return second                                          <- second is now the new head of this segment

WHAT TO THINK ABOUT
--------------------
1. What are the base cases for a linked-list recursion — how many of them,
   and why two rather than one? (Empty list, and a single leftover node
   with no pair.)
2. The recursive call must happen on `second.next` (the node AFTER the
   pair), not `head.next` — why? What would break if you passed the wrong
   node?
3. Why must `first.next` be reassigned to the recursive call's result
   BEFORE `second.next = first`? Trace what happens if the order is
   swapped — does anything actually break, or does it just look wrong?
4. What is "the new head of this segment" at each level, and why is it
   `second`, not `first`?

PROGRESSIVE HINTS
------------------
Hint 1: Base cases: `head is None` (empty) or `head.next is None` (one
        node left, nothing to pair with) — return `head` unchanged either
        way.
Hint 2: Name the pair `first = head`, `second = head.next`.
Hint 3: Recurse on the REST of the list, starting after the pair:
        `first.next = swapPairs(second.next)`.
Hint 4: Finish wiring: `second.next = first`, then `return second` — the
        pair is now second -> first -> (whatever the recursive call
        returned).

COMPLEXITY TARGET
------------------
    Recursive:  O(n) time, O(n/2) space (call stack, one frame per pair)
    Iterative:  O(n) time, O(1) space
================================================================================
*/

func main() {
	fmt.Println("Solution for Swap Nodes in Pairs not implemented yet")
}
