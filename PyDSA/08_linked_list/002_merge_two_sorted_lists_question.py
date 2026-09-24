"""
================================================================================
QUESTION · LeetCode 21 · Merge Two Sorted Lists                        [Easy]
https://leetcode.com/problems/merge-two-sorted-lists/
================================================================================

PROBLEM
-------
You are given the heads of two sorted linked lists `list1` and `list2`.
Merge the two lists into one SORTED list. The list should be made by
splicing together the nodes of the first two lists.

Return the head of the merged linked list.


EXAMPLES
--------
Example 1:
    Input:  list1 = [1,2,4], list2 = [1,3,4]
    Output: [1,1,2,3,4,4]

Example 2:
    Input:  list1 = [], list2 = []
    Output: []

Example 3:
    Input:  list1 = [], list2 = [0]
    Output: [0]


CONSTRAINTS
-----------
    The number of nodes in both lists is in the range [0, 50].
    -100 <= Node.val <= 100
    Both list1 and list2 are sorted in NON-DECREASING order.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Two sorted lists, merge them into one sorted list, IN PLACE (reuse the
existing nodes — do not build fresh ones). This is the linked-list analogue
of the merge step in merge sort, except you never need extra memory for the
merged array because you can just rewire `.next` pointers.

The catch is the SAME catch every linked-list problem in this topic has:
either input list might be empty, or might run out first, so whichever node
you're "standing on" needs a way to attach the next winner without a special
case for "am I still at the very first node of the result?" That's exactly
what a dummy/sentinel head is for (topic guide Part 2).

    list1:  1 -> 2 -> 4
    list2:  1 -> 3 -> 4

    dummy -> ...            tail starts at dummy
    compare 1 vs 1: tie, take list1's -> dummy -> 1(from list1)
    compare 2 vs 1: take list2's       -> ... -> 1 -> 1
    compare 2 vs 3: take list1's       -> ... -> 1 -> 1 -> 2
    compare 4 vs 3: take list2's       -> ... -> 1 -> 1 -> 2 -> 3
    list2 exhausted: attach the REST of list1 (4)
    result: 1 -> 1 -> 2 -> 3 -> 4 -> 4


PROGRESSIVE HINTS
------------------
Hint 1: Use a dummy head so "the merged list has no nodes yet" is not a
        special case — always have a `tail` pointer that starts on the dummy.

Hint 2: Advance whichever list has the SMALLER current value, and advance
        `tail` right along with it.

Hint 3: When one list runs out, splice the ENTIRE remainder of the other
        list onto `tail.next` in one line — no need to keep looping node by
        node, since it's already sorted.


COMPLEXITY TARGET
------------------
    Time:  O(n + m)
    Space: O(1) — reuse existing nodes, do not allocate new ones
================================================================================
"""

from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def mergeTwoLists(
        self, list1: Optional[ListNode], list2: Optional[ListNode]
    ) -> Optional[ListNode]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def build_list(values):
    dummy = ListNode()
    curr = dummy
    for v in values:
        curr.next = ListNode(v)
        curr = curr.next
    return dummy.next


def to_list(head):
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([1, 2, 4], [1, 3, 4], [1, 1, 2, 3, 4, 4]),
        ([], [], []),
        ([], [0], [0]),
        ([1, 2, 3], [], [1, 2, 3]),
    ]
    for a, b, want in cases:
        got = to_list(sol.mergeTwoLists(build_list(a), build_list(b)))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {a!r} + {b!r} -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
