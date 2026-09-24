package main

/*
================================================================================
LeetCode 138 · Copy List with Random Pointer                           [Medium]
https://leetcode.com/problems/copy-list-with-random-pointer/
Topic: 08 · Linked List
================================================================================

PROBLEM
-------
A linked list of length n is given, where each node contains an additional
random pointer, which could point to any node in the list, or nil.

Construct a DEEP COPY of the list. The deep copy should consist of exactly n
brand new nodes, where each new node has its value set to the value of its
corresponding original node. Both the next and random pointer of the new
nodes should point to new nodes in the copied list, such that the pointers
in the original list and copied list represent the same list state. None of
the pointers in the new list should point to nodes in the original list.

Return the head of the copied linked list.

EXAMPLES
--------
Example 1:
    Input:  head = [[7,null],[13,0],[11,4],[10,2],[1,0]]
    Output: [[7,null],[13,0],[11,4],[10,2],[1,0]]
    (each pair is [val, random-index], random-index may be null)

Example 2:
    Input:  head = [[1,1],[2,1]]
    Output: [[1,1],[2,1]]

CONSTRAINTS
-----------
    0 <= n <= 1000
    -10^4 <= Node.Val <= 10^4
    Node.Random is null or points to some node in the linked list.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The Random pointer can point ANYWHERE in the list, including forward to a
node not yet visited. That "forward reference" is the entire difficulty:
you cannot safely wire up copy.Random while walking .Next in order, because
the original node .Random points at might not have a copy yet.


PROGRESSIVE HINTS
------------------
Hint 1: A hashmap from old node -> new node, built in a first pass, then
        wired up in a second pass, solves the ordering problem directly.
Hint 2: For O(1) extra space, splice a copy of each node directly AFTER its
        original in the SAME list — now "the copy of X" is always reachable
        as X.Next, no map required.
Hint 3: Fix Random pointers on the copies using that property, then split
        the interleaved list back into two separate lists.


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1) extra (follow-up target; O(n) with a hashmap is acceptable
           as a first pass)
================================================================================
*/

// Node is the list node for this problem: a value, a next pointer, and a
// random pointer that may point to any node in the list (or nil).
type Node struct {
	Val    int
	Next   *Node
	Random *Node
}

// YourCopyRandomList is your attempt.
// Implement it, then run: cd GoDSA && go run ./08_linked_list/010_copy_list_with_random_pointer
func YourCopyRandomList(head *Node) *Node {
	// YOUR CODE HERE
	return nil
}
