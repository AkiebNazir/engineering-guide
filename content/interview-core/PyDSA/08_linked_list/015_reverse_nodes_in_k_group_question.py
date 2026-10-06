"""
================================================================================
LeetCode 25 · Reverse Nodes in k-Group                                 [Hard]
https://leetcode.com/problems/reverse-nodes-in-k-group/
Topic: 08 · Linked List
================================================================================

PROBLEM
-------
Given the head of a linked list, reverse the nodes of the list k at a time,
and return the modified list.

k is a positive integer and is less than or equal to the length of the
linked list. If the number of nodes is not a multiple of k, then the nodes
left out at the end (fewer than k of them) should remain AS-IS — do not
reverse them.

You may not alter the values in the list's nodes, only the nodes themselves
may be changed.


EXAMPLES
--------
Example 1:
    Input:  head = [1,2,3,4,5], k = 2
    Output: [2,1,4,3,5]

Example 2:
    Input:  head = [1,2,3,4,5], k = 3
    Output: [3,2,1,4,5]


CONSTRAINTS
-----------
    The number of nodes in the list is n.
    1 <= k <= n <= 5000
    0 <= Node.val <= 1000

FOLLOW UP
---------
    Could you solve the problem in O(1) extra memory space?
    You may not reverse the nodes' values, only rewire the nodes.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is problem 001's full-list reversal applied repeatedly to consecutive
GROUPS of k nodes instead of the whole list at once — with one extra rule:
if the FINAL group has fewer than k nodes remaining, it must be left as-is,
not reversed.

Three moving parts per group:
1. Check the group has k nodes available (walk k steps ahead; if you fall
   off the end, STOP — the trailing partial group stays untouched).
2. Reverse exactly those k nodes, using problem 001's in-place pointer
   reversal, bounded to stop after k nodes.
3. Reconnect: the node BEFORE the group must now point at the group's new
   head (the old tail), and the group's new tail (the old head) must point
   at wherever the NEXT group begins.


WHAT TO THINK ABOUT
--------------------
1. How do you check "does a full group of k nodes exist here" WITHOUT
   destroying pointers you'll need if the answer turns out to be no?

2. In problem 001's reversal, `prev` starts at None. Here, a group's
   reversal must NOT end by pointing at None — what should it point at
   instead, and why?

3. A dummy head made problem 002's "first node of the result" uniform.
   What role does it play here for "the node before the very first group"?


PROGRESSIVE HINTS
------------------
Hint 1: Reuse problem 001's in-place reversal as your primitive, but bound
        it to stop after exactly k nodes instead of running to the end of
        the list.

Hint 2: Before reversing a group, walk k steps ahead from the node BEFORE
        it to confirm k nodes exist; if you run out early, stop and return
        without touching that trailing group at all.

Hint 3: Seed the reversal loop's `prev` with the node AFTER the group
        (not None) — that's what the group's new tail (the old head) must
        end up pointing at. Save a reference to the node before the group
        so you can rewire it to point at the group's new head afterward.


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1), nodes rewired in place, no new nodes allocated
================================================================================
"""

from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def reverseKGroup(self, head: Optional[ListNode], k: int) -> Optional[ListNode]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def build_list(values):
    dummy = tail = ListNode()
    for v in values:
        tail.next = ListNode(v)
        tail = tail.next
    return dummy.next


def to_list(head):
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out


# ==============================================================================
# TESTS — run:  python 015_reverse_nodes_in_k_group_question.py
# ==============================================================================
CASES = [
    ([1, 2, 3, 4, 5], 2, [2, 1, 4, 3, 5]),
    ([1, 2, 3, 4, 5], 3, [3, 2, 1, 4, 5]),
    ([1, 2, 3, 4, 5, 6, 7, 8], 3, [3, 2, 1, 6, 5, 4, 7, 8]),
    ([1, 2, 3, 4, 5, 6], 3, [3, 2, 1, 6, 5, 4]),
    ([1, 2, 3, 4, 5], 1, [1, 2, 3, 4, 5]),
    ([1, 2, 3, 4, 5], 5, [5, 4, 3, 2, 1]),
    ([1], 1, [1]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for values, k, want in CASES:
        got = to_list(sol.reverseKGroup(build_list(values), k))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  values={values!r:<28} k={k} -> {got}  (want {want})")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
