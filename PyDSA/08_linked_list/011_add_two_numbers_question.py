"""
================================================================================
LeetCode 2 · Add Two Numbers                                          [Medium]
https://leetcode.com/problems/add-two-numbers/
================================================================================

PROBLEM
-------
You are given two non-empty linked lists representing two non-negative
integers. The digits are stored in REVERSE order, and each of their nodes
contains a single digit. Add the two numbers and return the sum as a linked
list, in the same reverse-digit format.

You may assume the two numbers do not contain any leading zero, except the
number 0 itself.

EXAMPLES
--------
Example 1:
    Input:  l1 = [2,4,3], l2 = [5,6,4]
    Output: [7,0,8]
    Explanation: 342 + 465 = 807.

Example 2:
    Input:  l1 = [0], l2 = [0]
    Output: [0]

Example 3:
    Input:  l1 = [9,9,9,9,9,9,9], l2 = [9,9,9,9]
    Output: [8,9,9,9,0,0,0,1]
    Explanation: 9999999 + 9999 = 10009998.

CONSTRAINTS
-----------
    The number of nodes in each linked list is in the range [1, 100].
    0 <= Node.val <= 9
    It is guaranteed that the list represents a number that does not have
    leading zeros.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Digits are stored LEAST-significant-first, which is exactly the order you add
them in by hand (ones place, then tens, then hundreds, ...) — the reversed
storage is a gift, not an obstacle. Walk both lists simultaneously, add
corresponding digits plus a running carry, emit one new node per position.

The two lists can have different lengths, and there may be a final carry that
needs an EXTRA node past the end of both lists (e.g. 5 + 5 = 10, a two-digit
result from two one-digit inputs). A dummy head (topic guide Part 2) avoids
special-casing "the first node of the result."


PROGRESSIVE HINTS
------------------
Hint 1: Add digit by digit like grade-school addition, carrying into the
        next position. The reversed storage means you're already walking
        least-significant-first.

Hint 2: The two lists can be different lengths. Treat a missing node as
        digit 0 rather than stopping early.

Hint 3: After both lists are exhausted, check if there's still a carry left
        — if so, that's one more digit/node in the result.


COMPLEXITY TARGET
------------------
    Time:  O(max(m, n))
    Space: O(max(m, n)) for the output (required, not extra)
================================================================================
"""

from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def build(digits):
    dummy = ListNode()
    curr = dummy
    for d in digits:
        curr.next = ListNode(d)
        curr = curr.next
    return dummy.next


def to_list(head):
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out


CASES = [
    ([2, 4, 3], [5, 6, 4], [7, 0, 8]),
    ([0], [0], [0]),
    ([9, 9, 9, 9, 9, 9, 9], [9, 9, 9, 9], [8, 9, 9, 9, 0, 0, 0, 1]),
    ([9, 9], [1], [0, 0, 1]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for d1, d2, expected in CASES:
        got = to_list(sol.addTwoNumbers(build(d1), build(d2)))
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {d1!r} + {d2!r} -> {got}  (want {expected})")
    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
