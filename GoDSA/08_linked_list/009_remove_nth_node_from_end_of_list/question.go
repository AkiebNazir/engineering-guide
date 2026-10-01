package main

/*
================================================================================
LeetCode 19 · Remove Nth Node From End of List                        [Medium]
https://leetcode.com/problems/remove-nth-node-from-end-of-list/
Topic: 08 · Linked List
================================================================================

PROBLEM
-------
Given the head of a linked list, remove the n-th node from the END of the
list, and return its head.

EXAMPLES
--------
Example 1:
    Input:  head = [1,2,3,4,5], n = 2
    Output: [1,2,3,5]

Example 2:
    Input:  head = [1], n = 1
    Output: []

Example 3:
    Input:  head = [1,2], n = 1
    Output: [1]

CONSTRAINTS
-----------
    The number of nodes in the list is sz.
    1 <= sz <= 30
    0 <= Node.Val <= 100
    1 <= n <= sz

FOLLOW UP
---------
    Could you do this in one pass?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Two-pass is easy: count the length, walk to the predecessor of the target,
rewire Next. The follow-up wants one pass.

Fixed-gap two pointers (Go guide's Part on two-pointer patterns, mirroring
the Python topic guide §3.3): advance a `fast` pointer n steps first, then
walk `fast` and `slow` together. When `fast` reaches the last node, `slow`
sits exactly n nodes behind it — i.e. right before the node to remove.

Since the target might be the HEAD itself (n == length), use a dummy node so
"remove the head" needs no special-case branch.


WHAT TO THINK ABOUT (Go specifically)
--------------------------------------
1. `*ListNode` is a real, safe nil — advancing `fast` past the end must be
   guarded by checking `fast != nil` (or `fast.Next != nil`) before
   dereferencing, or you get a nil-pointer panic, not silent wrong output.

2. The dummy node is a real heap allocation: `dummy := &ListNode{Next: head}`.
   `slow` starts there, not at `head`.


PROGRESSIVE HINTS
------------------
Hint 1: Open a gap of exactly n nodes between two pointers before walking
        them together.

Hint 2: Use a dummy node ahead of head so the pointer landing "n nodes
        behind" can rewire Next even when the target is the real head.

Hint 3: Loop condition for the second phase: `for fast.Next != nil`.


COMPLEXITY TARGET
------------------
    Time:  O(L)   (one pass)
    Space: O(1)
================================================================================
*/

type ListNode struct {
	Val  int
	Next *ListNode
}

// YourRemoveNthFromEnd is your attempt.
// Implement it, then run:  cd GoDSA && go run ./08_linked_list/009_remove_nth_node_from_end_of_list
func YourRemoveNthFromEnd(head *ListNode, n int) *ListNode {
	// YOUR CODE HERE
	return nil
}
