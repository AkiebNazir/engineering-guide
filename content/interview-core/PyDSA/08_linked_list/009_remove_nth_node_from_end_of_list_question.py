"""
================================================================================
LeetCode 19 · Remove Nth Node From End of List                        [Medium]
https://leetcode.com/problems/remove-nth-node-from-end-of-list/
================================================================================

PROBLEM
-------
Given the head of a linked list, remove the n-th node from the END of the
list, and return its head.

EXAMPLES
--------
Example 1:
    Input:  head = [1,2,3,4,5], n = 2
    Output: [1,2,3,5]
    Explanation: the 2nd node from the end is 4; remove it.

Example 2:
    Input:  head = [1], n = 1
    Output: []

Example 3:
    Input:  head = [1,2], n = 1
    Output: [1]

CONSTRAINTS
-----------
    The number of nodes in the list is sz.
    1 <= sz <= 30
    0 <= Node.val <= 100
    1 <= n <= sz

FOLLOW UP
---------
    Could you do this in one pass?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The obvious approach is two passes: walk once to count the length `L`, then
walk again to the (L - n)-th node (0-indexed) and unlink its successor. That
works, but the follow-up explicitly asks for one pass.

The one-pass trick is a FIXED-GAP two-pointer: advance one pointer `n` steps
ahead first, then walk both pointers together. When the lead pointer falls
off the end, the trailing pointer sits exactly `n` nodes behind it — i.e.
right before the node to remove. See the topic guide §3.3 for the full
derivation.

Because the node to remove might be the HEAD itself (n == length), use a
dummy head (topic guide Part 2) so "delete the head" needs no special case.


PROGRESSIVE HINTS
------------------
Hint 1: Two-pass is easy: count the length, then walk to the node BEFORE the
        target and rewire `.next`. Can you avoid the first pass?

Hint 2: Open a gap of exactly n nodes between two pointers before starting
        the "walk together" phase.

Hint 3: Use a dummy node ahead of head so the pointer that ends up "n nodes
        behind" can rewire `.next` even when the target is the real head.


COMPLEXITY TARGET
------------------
    Time:  O(L)   (one pass)
    Space: O(1)
================================================================================
"""

from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def removeNthFromEnd(self, head: Optional[ListNode], n: int) -> Optional[ListNode]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def build(values):
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


CASES = [
    ([1, 2, 3, 4, 5], 2, [1, 2, 3, 5]),
    ([1], 1, []),
    ([1, 2], 1, [1]),
    ([1, 2], 2, [2]),
    ([1, 2, 3, 4, 5], 5, [2, 3, 4, 5]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for values, n, expected in CASES:
        head = build(values)
        got = to_list(sol.removeNthFromEnd(head, n))
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  values={values!r:<20} n={n} -> {got}  (want {expected})")
    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
