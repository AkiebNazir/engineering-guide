package main

/*
================================================================================
LeetCode 203 · Remove Linked List Elements                              [Easy]
https://leetcode.com/problems/remove-linked-list-elements/
Topic: 08 · Linked List
================================================================================

PROBLEM
-------
Given the head of a linked list and an integer val, remove all the nodes
whose Val equals val, and return the new head.


EXAMPLES
--------
Example 1:
    Input:  head = [1,2,6,3,4,5,6], val = 6
    Output: [1,2,3,4,5]

Example 2:
    Input:  head = [], val = 1
    Output: []

Example 3:
    Input:  head = [7,7,7,7], val = 7
    Output: []


CONSTRAINTS
-----------
    The number of nodes in the list is in the range [0, 10^4].
    1 <= Node.Val <= 50
    0 <= val <= 50


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

The Go guide's Part 2 case study, verbatim: deleting a node whose Val equals
val is normally a one-line rewire, `curr.Next = curr.Next.Next` — UNLESS the
matching node is the head itself, in which case there is no "node before it"
to hold curr, and head must be reassigned directly instead. A dummy node
standing one slot before the real head erases that distinction entirely:

    dummy := &ListNode{Next: head}   // dummy.Next is ALWAYS "the real head"
    curr := dummy
    for curr.Next != nil {
        if curr.Next.Val == val {
            curr.Next = curr.Next.Next   // skip it; curr does NOT move
        } else {
            curr = curr.Next             // only advance past a KEPT node
        }
    }
    return dummy.Next

Note the else: after a deletion, curr must stay put, because curr.Next is
now a fresh node that itself might also match — this is what lets a whole
RUN of consecutive matches ([7,7,7,7]) collapse in a single pass.


WHAT TO THINK ABOUT
--------------------
1. Why does deleting a match at the head require different code from
   deleting a match in the middle, without a dummy?

2. After curr.Next = curr.Next.Next removes a match, why must curr NOT
   advance? Trace [7,7,7,7] assuming you advance unconditionally.

3. What happens on head == nil? Does `for curr.Next != nil` already handle
   it, or does it need an explicit guard?


PROGRESSIVE HINTS
------------------
Hint 1: dummy := &ListNode{Next: head}; start curr there instead of at head.
Hint 2: Loop `for curr.Next != nil`; never dereference curr itself past the
        dummy, only ever look one node ahead through curr.Next.
Hint 3: On a match, rewire and do NOT move curr. On a non-match, curr =
        curr.Next. Return dummy.Next, not dummy.


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1)
================================================================================
*/

// ListNode is the canonical LeetCode singly linked list node.
type ListNode struct {
	Val  int
	Next *ListNode
}

// YourRemoveElements is your attempt.
// Implement it, then run:  cd GoDSA && go run ./08_linked_list/005_remove_linked_list_elements
func YourRemoveElements(head *ListNode, val int) *ListNode {
	// YOUR CODE HERE
	return nil
}
