"""
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
"""

import random


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def build_list(values: list[int]) -> ListNode | None:
    head = None
    tail = None
    for v in values:
        node = ListNode(v)
        if head is None:
            head = node
            tail = node
        else:
            tail.next = node
            tail = node
    return head


class Solution:
    def __init__(self, head: ListNode | None):
        # YOUR CODE HERE
        pass

    def getRandom(self) -> int:
        # YOUR CODE HERE
        pass


def run_tests() -> None:
    all_ok = True

    head = build_list([1, 2, 3])
    sol = Solution(head)

    valid = {1, 2, 3}
    for _ in range(20):
        got = sol.getRandom()
        if got not in valid:
            all_ok = False
            print(f"FAIL  getRandom() -> {got} not in {valid}")
            break
    else:
        print(f"PASS  20 getRandom() calls all in {valid}")

    head1 = build_list([42])
    sol1 = Solution(head1)
    got = sol1.getRandom()
    ok = got == 42
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  single-node list -> {got}  (want 42)")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
