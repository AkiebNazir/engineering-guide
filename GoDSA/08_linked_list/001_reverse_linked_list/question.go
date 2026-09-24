package main

/*
================================================================================
LeetCode 206 · Reverse Linked List                                       [Easy]
https://leetcode.com/problems/reverse-linked-list/
Topic: 08 · Linked List
================================================================================

PROBLEM
-------
Given the head of a singly linked list, reverse the list, and return the
reversed list's head.


EXAMPLES
--------
Example 1:
    Input:  head = [1,2,3,4,5]
    Output: [5,4,3,2,1]

Example 2:
    Input:  head = [1,2]
    Output: [2,1]

Example 3:
    Input:  head = []
    Output: []


CONSTRAINTS
-----------
    The number of nodes in the list is in the range [0, 5000].
    -5000 <= Node.Val <= 5000

FOLLOW UP
---------
    A linked list can be reversed either iteratively or recursively. Could
    you implement both?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Reversal rewires every node's Next to point BACKWARD instead of forward. The
danger: the moment you write `curr.Next = prev`, you've overwritten the only
pointer this program held to "the rest of the original list" — unless you
saved it first.

    1 -> 2 -> 3 -> nil            (before)
    nil <- 1 <- 2 <- 3            (after; head is now 3)

Three pointers, fixed order, every time:
    1. next := curr.Next     // SAVE the rest of the list before touching it
    2. curr.Next = prev      // REWIRE this node backward
    3. prev = curr             // ADVANCE prev
    4. curr = next               // ADVANCE curr using the SAVED reference


WHAT TO THINK ABOUT (Go specifically)
-------------------------------------
1. `var prev *ListNode` is nil by default — a real, safe zero value, not
   garbage. It becomes the new tail's Next.

2. Once `curr.Next = prev` runs, the old forward link is gone. If you didn't
   save `next` first, the rest of the list is unreachable — Go's GC would
   silently keep collecting nothing wrong per se, but the ALGORITHM is now
   broken: you've truncated the list, not crashed.

3. A recursive version exists but costs one stack frame per node. Go has no
   tail-call optimization, so this is a genuine (if generous, since
   goroutine stacks grow dynamically) depth concern on very long lists —
   default to iterative.


PROGRESSIVE HINTS
------------------
Hint 1: Track three pointers at once: what came before curr, curr itself,
        and what comes after curr.

Hint 2: Save `curr.Next` into a local variable BEFORE you overwrite
        `curr.Next`. Rewire first and the rest of the list is gone for good.

Hint 3: The loop ends when `curr == nil`. The answer is `prev`, not `head` —
        head is now the OLD tail (or nil on empty input).


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1) iterative (O(n) if you choose the recursive variant)
================================================================================
*/

type ListNode struct {
	Val  int
	Next *ListNode
}

// YourReverseList is your attempt.
// Implement it, then run:  cd GoDSA && go run ./08_linked_list/001_reverse_linked_list
func YourReverseList(head *ListNode) *ListNode {
	// YOUR CODE HERE
	return nil
}
