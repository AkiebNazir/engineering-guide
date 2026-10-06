"""
================================================================================
LeetCode 83 · Remove Duplicates from Sorted List                        [Easy]
https://leetcode.com/problems/remove-duplicates-from-sorted-list/
Topic: 08 · Linked List
================================================================================

PROBLEM
-------
Given the head of a SORTED linked list, delete all duplicates such that each
element appears only once. Return the linked list, still sorted.


EXAMPLES
--------
Example 1:
    Input:  head = [1,1,2]
    Output: [1,2]

Example 2:
    Input:  head = [1,1,2,3,3]
    Output: [1,2,3]


CONSTRAINTS
-----------
    The number of nodes in the list is in the range [0, 300].
    -100 <= Node.val <= 100
    The list is guaranteed to be SORTED in ascending order.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Because the list is SORTED, every duplicate of a value is guaranteed to sit
IMMEDIATELY next to some other copy of the same value — duplicates can never
be scattered apart. That collapses "remove duplicates" from a general
membership problem (which would need a hashset to remember every value ever
seen — that's LC 82's cousin problem territory, or an UNSORTED list) into a
simple adjacent-pair scan: look at `curr` and `curr.next`; if they're equal,
splice `curr.next` out and check again; otherwise move on.

    curr = head
    while curr and curr.next:
        if curr.val == curr.next.val:
            curr.next = curr.next.next     # skip the duplicate
        else:
            curr = curr.next                # advance past a KEPT node
    return head

Notice this does NOT need a dummy head (contrast problem 005): the value
being compared is always `curr.val` against `curr.next.val`, and the head
node itself is never a candidate for deletion — at most its LATER duplicates
get removed, and the head always survives untouched. There is nothing here
that "might change which node is first."


WHAT TO THINK ABOUT
--------------------
1. Why is a dummy head unnecessary here, when it was essential for problem
   005? What's structurally different about "delete adjacent duplicates" vs.
   "delete every node matching a value"?

2. This algorithm is SILENTLY WRONG on an unsorted list. Construct an input
   like [1, 2, 1] and trace what the adjacent-scan does to it — does it
   remove the duplicate 1's?

3. On a match, why must `curr` stay put instead of advancing? (Same
   reasoning as problem 005 — a run of 3+ identical values needs the check
   re-applied after each single deletion.)

4. What is the loop condition, precisely — `while curr and curr.next`, not
   just `while curr.next`? What input breaks the difference?


PROGRESSIVE HINTS
------------------
Hint 1: Only ONE pointer is needed, no dummy. Compare `curr.val` against
        `curr.next.val`.

Hint 2: On a match, `curr.next = curr.next.next` and do NOT advance `curr` —
        the new `curr.next` might be yet another duplicate of the same run.

Hint 3: On a non-match, `curr = curr.next`. Stop when `curr.next is None`
        (or `curr is None`, for the empty-list case).


COMPLEXITY TARGET
------------------
    Time:  O(n)   — one pass, given the sorted precondition
    Space: O(1)   — in place, no auxiliary structure
================================================================================
"""

from typing import List, Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def deleteDuplicates(self, head: Optional[ListNode]) -> Optional[ListNode]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 006_remove_duplicates_from_sorted_list_question.py
# ==============================================================================
def list_to_linked(values: List[int]) -> Optional[ListNode]:
    dummy = ListNode()
    curr = dummy
    for v in values:
        curr.next = ListNode(v)
        curr = curr.next
    return dummy.next


def linked_to_list(head: Optional[ListNode]) -> List[int]:
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out


def run_tests() -> None:
    sol = Solution()
    cases = [
        ([1, 1, 2], [1, 2]),
        ([1, 1, 2, 3, 3], [1, 2, 3]),
        ([], []),
        ([1], [1]),
        ([1, 1, 1, 1], [1]),
        ([1, 2, 3], [1, 2, 3]),
        ([-3, -3, -1, 0, 0, 0, 5], [-3, -1, 0, 5]),
    ]

    passed = 0
    for values, expected in cases:
        head = list_to_linked(values)
        got = linked_to_list(sol.deleteDuplicates(head))
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  head={values!r:<28} -> {got}  (want {expected})")

    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
