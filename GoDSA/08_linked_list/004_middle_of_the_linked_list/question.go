package main

/*
================================================================================
LeetCode 876 · Middle of the Linked List                                 [Easy]
https://leetcode.com/problems/middle-of-the-linked-list/
Topic: 08 · Linked List
================================================================================

PROBLEM
-------
Given the head of a singly linked list, return the middle node of the
linked list.

If there are two middle nodes, return the SECOND middle node.


EXAMPLES
--------
Example 1:
    Input:  head = [1,2,3,4,5]
    Output: [3,4,5]     (node 3 is the middle; shown as what's reachable from it)

Example 2:
    Input:  head = [1,2,3,4,5,6]
    Output: [4,5,6]     (two middles, 3 and 4 — return the SECOND one)


CONSTRAINTS
-----------
    The number of nodes in the list is in the range [1, 100].
    1 <= Node.Val <= 100


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Finding "the middle" of a slice is trivial with an index: n / 2. A linked
list has no index — jumping to position n / 2 needs n known first, which
needs a full walk. Floyd's slow/fast pointers (topic guide §3.1) avoid that
length-counting pass entirely: slow advances one node per iteration, fast
advances two. When fast falls off the end, slow has covered exactly half the
distance.

    1 -> 2 -> 3 -> 4 -> 5 -> nil      (odd length, 5 nodes)

    slow=1 fast=1
    slow=2 fast=3
    slow=3 fast=5
    fast.Next is nil -> stop. slow = 3 (the true middle). ✓

    1 -> 2 -> 3 -> 4 -> 5 -> 6 -> nil  (even length, 6 nodes)

    slow=1 fast=1
    slow=2 fast=3
    slow=3 fast=5
    slow=4 fast=nil (fast.Next.Next steps past the end) -> stop. slow = 4.
    That's the SECOND of the two middles (3 and 4) — exactly what LC 876 wants.


WHAT TO THINK ABOUT (Go specifically)
-------------------------------------
1. Loop condition must check BOTH `fast != nil` and `fast.Next != nil`,
   in that order — same nil-dereference concern as problem 003's cycle
   detection.

2. Return the `*ListNode`, not `.Val` — the problem wants the remaining
   sub-list starting at the middle node.

3. No allocation needed at all — two local `*ListNode` variables are enough,
   O(1) space genuinely means zero extra memory here, not "small."


PROGRESSIVE HINTS
------------------
Hint 1: You need n/2 without knowing n in advance and without a second pass.
        Two pointers at different speeds solve this in one pass.

Hint 2: Loop while `fast != nil && fast.Next != nil` — this naturally lands
        slow on the SECOND middle for even-length lists. Verify by hand on
        a 6-node example.

Hint 3: Return `slow`, the node itself — not a copy, not `slow.Val`.


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1)
================================================================================
*/

type ListNode struct {
	Val  int
	Next *ListNode
}

// YourMiddleNode is your attempt.
// Implement it, then run:  cd GoDSA && go run ./08_linked_list/004_middle_of_the_linked_list
func YourMiddleNode(head *ListNode) *ListNode {
	// YOUR CODE HERE
	return nil
}
