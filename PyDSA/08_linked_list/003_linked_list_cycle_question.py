"""
================================================================================
QUESTION · LeetCode 141 · Linked List Cycle                            [Easy]
https://leetcode.com/problems/linked-list-cycle/
================================================================================

PROBLEM
-------
Given `head`, the head of a linked list, determine if the linked list has a
cycle in it.

There is a cycle in a linked list if some node in the list can be reached
again by continuously following the `next` pointer. Internally, `pos` is
used to denote the index of the node that the tail's `next` pointer is
connected to. Note that `pos` is NOT passed as a parameter.

Return `True` if there is a cycle in the linked list. Otherwise, return
`False`.


EXAMPLES
--------
Example 1:
    Input:  head = [3,2,0,-4], pos = 1  (tail connects to node index 1)
    Output: True

Example 2:
    Input:  head = [1,2], pos = 0
    Output: True

Example 3:
    Input:  head = [1], pos = -1  (no cycle)
    Output: False


CONSTRAINTS
-----------
    The number of nodes in the list is in the range [0, 10^4].
    -10^5 <= Node.val <= 10^5
    pos is -1 or a valid index in the linked list.

FOLLOW UP
---------
    Can you solve it using O(1) (i.e. constant) memory?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
A cycle means some node's `.next` chain loops back on itself instead of ever
reaching `None`. Walking with a single pointer and a `set()` of visited node
identities would detect this in O(n) time but O(n) space. The O(1)-space
trick is Floyd's tortoise-and-hare: two pointers starting at `head`, one
moving 1 step per iteration (`slow`), one moving 2 (`fast`). If there's a
cycle, `fast` is lapping `slow` inside a finite loop and is GUARANTEED to
land on the exact same node as `slow` eventually — see topic guide §3.2 for
the "gap shrinks by one" proof. If there's no cycle, `fast` simply falls off
the end.

    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:      # IDENTITY compare, not value equality
            return True
    return False

Note `fast.next.next` needs BOTH `fast` and `fast.next` to be non-None
before it's safe to dereference — the loop condition checks both, in that
order, every iteration.


PROGRESSIVE HINTS
------------------
Hint 1: Two pointers, different speeds. If there's a loop, the faster one
        will eventually "lap" the slower one inside it.

Hint 2: Compare with `is`, not `==` — you care whether it's the SAME node
        object, not whether two different nodes happen to hold equal values.

Hint 3: Guard `fast.next.next` with `fast and fast.next` in the loop
        condition, checked in that order (short-circuit) — reading past a
        None `.next` raises AttributeError immediately in Python.


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1)
================================================================================
"""

from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def hasCycle(self, head: Optional[ListNode]) -> bool:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def build_cyclic_list(values, pos):
    """pos = -1 means no cycle; otherwise tail.next points at index pos."""
    if not values:
        return None
    nodes = [ListNode(v) for v in values]
    for i in range(len(nodes) - 1):
        nodes[i].next = nodes[i + 1]
    if pos != -1:
        nodes[-1].next = nodes[pos]
    return nodes[0]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([3, 2, 0, -4], 1, True),
        ([1, 2], 0, True),
        ([1], -1, False),
        ([], -1, False),
        ([1], 0, True),  # self-loop
    ]
    for values, pos, want in cases:
        got = sol.hasCycle(build_cyclic_list(values, pos))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  values={values!r:<16} pos={pos:<3} -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
