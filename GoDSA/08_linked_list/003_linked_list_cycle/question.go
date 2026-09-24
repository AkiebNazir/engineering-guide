package main

/*
================================================================================
LeetCode 141 · Linked List Cycle                                         [Easy]
https://leetcode.com/problems/linked-list-cycle/
Topic: 08 · Linked List
================================================================================

PROBLEM
-------
Given head, the head of a linked list, determine if the linked list has a
cycle in it.

There is a cycle in a linked list if some node in the list can be reached
again by continuously following the Next pointer. Internally, pos is used to
denote the index of the node that the tail's Next pointer connects to. Note
that pos is NOT passed as a parameter.

Return true if there is a cycle in the linked list, otherwise return false.


EXAMPLES
--------
Example 1:
    Input:  head = [3,2,0,-4], pos = 1  (tail connects to node index 1)
    Output: true

Example 2:
    Input:  head = [1,2], pos = 0
    Output: true

Example 3:
    Input:  head = [1], pos = -1  (no cycle)
    Output: false


CONSTRAINTS
-----------
    The number of nodes in the list is in the range [0, 10^4].
    -10^5 <= Node.Val <= 10^5
    pos is -1 or a valid index in the linked list.

FOLLOW UP
---------
    Can you solve it using O(1) (constant) memory?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

A cycle means some node's Next chain loops back on itself instead of ever
reaching nil. Floyd's tortoise-and-hare: two pointers starting at head, one
moving 1 step per iteration (slow), one moving 2 (fast). If there's a cycle,
fast is lapping slow inside a finite loop and is GUARANTEED to land on the
exact same node eventually (topic guide §3.2 — the gap shrinks by exactly 1
every step and cannot skip past 0). If there's no cycle, fast simply falls
off the end.

    slow, fast := head, head
    for fast != nil && fast.Next != nil {
        slow = slow.Next
        fast = fast.Next.Next
        if slow == fast {      // pointer equality — same node, not same value
            return true
        }
    }
    return false


WHAT TO THINK ABOUT (Go specifically)
-------------------------------------
1. `fast.Next.Next` needs BOTH `fast != nil` and `fast.Next != nil` checked,
   IN THAT ORDER, before it's safe to evaluate. Skip either check (or the
   order) and this panics: "runtime error: invalid memory address or nil
   pointer dereference" — a REAL, loud panic, not a silent wrong answer.

2. `slow == fast` compares POINTER VALUES (addresses) here, since both are
   `*ListNode` — this is identity comparison, exactly what you want. Two
   different nodes holding equal `Val` fields are NOT `==` as pointers.

3. Go structs are dereferenced automatically through pointers for field
   access (`fast.Next` is shorthand for `(*fast).Next`), which is why the
   nil check has to come before the field access, not after.


PROGRESSIVE HINTS
------------------
Hint 1: Two pointers, different speeds. If there's a loop, the faster one
        eventually "laps" the slower one inside it.

Hint 2: Compare pointers directly with `==` — you want to know if it's the
        SAME node, not whether two nodes happen to hold equal values.

Hint 3: Guard `fast.Next.Next` with `fast != nil && fast.Next != nil` in the
        loop condition, checked in that order (Go's `&&` short-circuits).


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

// YourHasCycle is your attempt.
// Implement it, then run:  cd GoDSA && go run ./08_linked_list/003_linked_list_cycle
func YourHasCycle(head *ListNode) bool {
	// YOUR CODE HERE
	return false
}
