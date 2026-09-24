package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 382 · Linked List Random Node                   [Medium]
https://leetcode.com/problems/linked-list-random-node/
================================================================================

PROBLEM
-------
Given a singly linked list, design an algorithm that returns the value of a
random node from the linked list. Every node must have the SAME probability
of being chosen.

Implement the `Solution` class:
    Solution(head)   Initializes the object with the integer array
                     nums, represented as a singly linked list, given the
                     head node.
    getRandom()      Chooses a node randomly from the list and returns its
                     value. Each node must have an equal probability of
                     being chosen.


EXAMPLES
--------
Example 1:
    Input:
        ["Solution", "getRandom", "getRandom", "getRandom", "getRandom", "getRandom"]
        [[[1, 2, 3]], [], [], [], [], []]
    Output:
        [null, 1, 3, 2, 2, 3]
    Explanation:
        Solution solution = new Solution([1, 2, 3]);
        solution.getRandom(); // return 1, 2, or 3, each with 1/3 probability


CONSTRAINTS
-----------
    The number of nodes in the linked list will be in the range [1, 10^4].
    -10^4 <= Node.val <= 10^4
    At most 10^4 calls will be made to getRandom.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The tempting shortcut -- convert the linked list to an array once in
__init__, then getRandom() is random.choice(array) -- works, but it costs
O(n) EXTRA space to hold that array, on top of the list itself. This
problem exists to make you implement RESERVOIR SAMPLING directly over the
list: walk it once per getRandom() call, and by the time you reach the
end, you're holding a uniformly random node's value, all in O(1) extra
space. This is the general form of problem 002's technique (there the
"stream" was matches of a target value in an array; here the stream is
every node of a singly linked list of a priori UNKNOWN length -- you
cannot ask a linked list "how long are you" in O(1), so any approach that
needs the length up front already costs an O(n) pass just to find it).

PROGRESSIVE HINTS
------------------
Hint 1: Walk the list from head, maintaining node index m (1-indexed) and
        a running `result`. At the m-th node, replace `result` with this
        node's value with probability 1/m.
Hint 2: This is IDENTICAL in structure to problem 002's reservoir sampling
        -- the only difference is the stream is "all nodes" instead of
        "nodes matching a target."
Hint 3: Do not build a list/array of values first if the goal is O(1)
        extra space -- that defeats the point of this exercise (though it
        is a perfectly valid O(n)-space alternative worth naming and
        contrasting).

COMPLEXITY TARGET
------------------
    Time:  O(n) per getRandom() call (must walk the whole list)
    Space: O(1) extra (excluding the list itself)
================================================================================
*/

func main() {
	fmt.Println("Solution for Linked List Random Node not implemented yet")
}
