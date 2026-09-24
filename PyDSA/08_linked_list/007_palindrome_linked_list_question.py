"""
================================================================================
LeetCode 234 · Palindrome Linked List                                   [Easy]
https://leetcode.com/problems/palindrome-linked-list/
Topic: 08 · Linked List
================================================================================

PROBLEM
-------
Given the head of a singly linked list, return True if it is a palindrome
(reads the same forwards and backwards).


EXAMPLES
--------
Example 1:
    Input:  head = [1,2,2,1]
    Output: True

Example 2:
    Input:  head = [1,2]
    Output: False


CONSTRAINTS
-----------
    The number of nodes in the list is in the range [1, 10^5].
    0 <= Node.val <= 9

FOLLOW UP
---------
    Could you do it in O(n) time and O(1) space?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

A palindrome check normally wants to compare from BOTH ends inward — but a
singly linked list has no backward pointer, so you can't walk from the tail.
Two genuinely different strategies close that gap:

1. O(n) SPACE: copy every value into an array (or Python list), then run the
   familiar two-pointer palindrome check (topic 02) on the array, which DOES
   support backward indexing. Simple, always correct, costs an extra buffer
   the size of the list.

2. O(1) SPACE: this topic's two earlier techniques, composed —
     a. find the middle (§3.1, slow/fast pointers)
     b. reverse the second half in place (§4.1, the reversal template)
     c. walk the first half and the reversed second half together, comparing
        values pointer-by-pointer
   No extra array. The trade is that it temporarily destroys the list's
   original shape — restoring it (re-reversing the second half and
   re-attaching) is a nice touch to mention even though LeetCode itself
   doesn't require it, because a "pure" function normally shouldn't leave a
   caller's structure altered as a side effect of a read-only-sounding query.


WHAT TO THINK ABOUT
--------------------
1. Why can't you use the topic 02 two-pointer palindrome check DIRECTLY on
   the linked list, without an array or a reversal?

2. For O(1) space: after finding the middle with slow/fast, EXACTLY which
   node should the second half start at when the list has an ODD number of
   nodes vs. an EVEN number? If you include the middle node in the reversed
   second half (rather than starting one node past it), what happens to the
   comparison loop on an odd-length list — does it produce a wrong answer,
   or just one harmless extra comparison?

3. What breaks if you compare the wrong number of nodes because of an
   off-by-one in step 2 — will it ever produce a false positive, a false
   negative, or an IndexError-equivalent (AttributeError from walking off
   the end)?

4. Is a single node always a palindrome? Is an empty list (not reachable
   under this problem's constraints, but worth naming)?


PROGRESSIVE HINTS
------------------
Hint 1 (O(n) space): `vals = []`; walk the list appending `.val`; then
        `vals == vals[::-1]`.

Hint 2 (O(1) space): slow/fast to find the middle (§3.1 in the topic guide).

Hint 3 (O(1) space): reverse everything from the middle onward (§4.1), then
        walk two pointers — one from `head`, one from the reversed second
        half's new head — comparing `.val` at each step. Stop when either
        pointer runs out (handles odd length automatically, since the true
        middle node has no partner to compare against).


COMPLEXITY TARGET
------------------
    Time:  O(n)              — one or two passes either way
    Space: O(1) is achievable — the follow-up asks for it explicitly
================================================================================
"""

from typing import List, Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def isPalindrome(self, head: Optional[ListNode]) -> bool:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 007_palindrome_linked_list_question.py
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
        ([1, 2, 2, 1], True),
        ([1, 2], False),
        ([1], True),
        ([1, 2, 3, 2, 1], True),
        ([1, 2, 3, 4], False),
        ([1, 1], True),
        ([1, 2, 1, 1], False),
        ([0], True),
    ]

    passed = 0
    for values, expected in cases:
        head = list_to_linked(values)
        got = sol.isPalindrome(head)
        # Verify the input wasn't destroyed as a side effect.
        preserved = linked_to_list(head) == values
        ok = got == expected and preserved
        passed += ok
        note = "" if preserved else "  <- INPUT MUTATED!"
        print(f"{'PASS' if ok else 'FAIL'}  head={values!r:<20} -> {got}  "
              f"(want {expected}){note}")

    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
