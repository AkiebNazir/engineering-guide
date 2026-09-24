"""
================================================================================
LeetCode 143 · Reorder List                                           [Medium]
https://leetcode.com/problems/reorder-list/
Topic: 08 · Linked List
================================================================================

PROBLEM
-------
Given the head of a singly linked list, reorder it in place from

    L0 -> L1 -> ... -> Ln-1 -> Ln

to

    L0 -> Ln -> L1 -> Ln-1 -> L2 -> Ln-2 -> ...

You may not modify the values in the list's nodes (only the .next pointers
may change). Solve without an O(n) auxiliary array of nodes if possible.


EXAMPLES
--------
Example 1:
    Input:  head = [1,2,3,4]
    Output: [1,4,2,3]

Example 2:
    Input:  head = [1,2,3,4,5]
    Output: [1,5,2,4,3]


CONSTRAINTS
-----------
    The number of nodes is in the range [1, 5 * 10^4].
    1 <= Node.val <= 1000


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is not a new algorithm — it is problem 004 (find the middle) and
problem 001 (reversal) from this exact topic, composed, plus one more step
(a merge/interleave). See the topic guide's §4.2 for the general argument
that reversal is a TEMPLATE, not a one-off trick.

    1. Find the middle of the list       (§3.1, slow/fast pointers)
    2. Reverse the second half in place   (§4.1, the reversal template)
    3. Merge the two halves, alternating ONE node from each

    1 -> 2 -> 3 -> 4 -> 5

    split at middle:            1 -> 2 -> 3        4 -> 5
    reverse second half:        1 -> 2 -> 3        5 -> 4
    merge alternating:          1 -> 5 -> 2 -> 4 -> 3

The merge step interleaves node-by-node: take one node from the first half,
then one from the (reversed) second half, repeat, until one side runs out.
Because the second half is the same length as the first half (or exactly one
shorter, for odd total length), the first half always has the leftover node
if there's an odd one out — that leftover simply becomes the new tail.


WHAT TO THINK ABOUT
--------------------
1. Why must you find the middle FIRST, before reversing anything? What would
   go wrong if you tried to reverse the second half of a list whose exact
   midpoint you hadn't located yet?

2. When merging, which list's nodes get "the extra one" when the total
   length is odd — the first half or the (reversed) second half? Why?

3. The problem says you may not modify VALUES, only pointers. Does the
   find-middle + reverse + merge approach ever need to touch a `.val`?

4. What is the classic bug when interleaving two lists by hand: losing a
   reference to "the rest of list B" because you overwrote `.next` on a node
   from list A before saving where list B continues? (This is topic guide
   Part 1.3's #1 bug, showing up again in a new shape.)


PROGRESSIVE HINTS
------------------
Hint 1: `slow, fast = head, head`; `while fast and fast.next: slow =
        slow.next; fast = fast.next.next`. `slow` is now the start of the
        second half (or the true middle, for odd length — either way, you
        can reverse from `slow` onward safely).

Hint 2: Reverse everything from `slow` to the end using the standard
        three-pointer dance (`prev`, `curr`, `nxt`).

Hint 3: Cut the first half's tail loose from the (now-reversed) second half
        BEFORE merging, or the merge loop will re-traverse into stale
        structure. Then walk two pointers, alternately saving each side's
        "next" reference before overwriting `.next` to point at the other
        list's current node.


COMPLEXITY TARGET
------------------
    Time:  O(n)   — find middle O(n) + reverse O(n) + merge O(n)
    Space: O(1)   — all rewiring, no auxiliary array of node references
================================================================================
"""

from typing import List, Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def reorderList(self, head: Optional[ListNode]) -> None:
        """
        Do not return anything, modify head in-place instead.
        """
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 008_reorder_list_question.py
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
        ([1, 2, 3, 4], [1, 4, 2, 3]),
        ([1, 2, 3, 4, 5], [1, 5, 2, 4, 3]),
        ([1], [1]),
        ([1, 2], [1, 2]),
        ([1, 2, 3], [1, 3, 2]),
    ]

    passed = 0
    for values, expected in cases:
        head = list_to_linked(values)
        sol.reorderList(head)
        got = linked_to_list(head)
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  input={values!r:<16} -> {got}  (want {expected})")

    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
