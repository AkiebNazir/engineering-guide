"""
================================================================================
QUESTION · LeetCode 876 · Middle of the Linked List                    [Easy]
https://leetcode.com/problems/middle-of-the-linked-list/
================================================================================

PROBLEM
-------
Given the `head` of a singly linked list, return the middle node of the
linked list.

If there are two middle nodes, return the SECOND middle node.


EXAMPLES
--------
Example 1:
    Input:  head = [1,2,3,4,5]
    Output: [3,4,5]     (node 3 is the middle; this is what's reachable FROM it)

Example 2:
    Input:  head = [1,2,3,4,5,6]
    Output: [4,5,6]     (two middles, 3 and 4 — return the SECOND one)


CONSTRAINTS
-----------
    The number of nodes in the list is in the range [1, 100].
    1 <= Node.val <= 100


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Finding "the middle" of an array is trivial with an index: `n // 2`. A
linked list has no index — you cannot jump to position `n // 2` without
first knowing `n`, and finding `n` means a full walk. The one-pass trick
(Floyd's slow/fast, topic guide §3.1) avoids the length-counting walk
entirely: advance `slow` one step and `fast` two steps per iteration. When
`fast` falls off the end, `slow` has covered exactly half the distance.

    1 -> 2 -> 3 -> 4 -> 5 -> None      (odd length, 5 nodes)

    slow=1 fast=1
    slow=2 fast=3
    slow=3 fast=5
    fast.next is None -> stop. slow = 3 (the true middle). ✓

    1 -> 2 -> 3 -> 4 -> 5 -> 6 -> None  (even length, 6 nodes)

    slow=1 fast=1
    slow=2 fast=3
    slow=3 fast=5
    slow=4 fast is None (fast.next.next past the end) -> stop. slow = 4.
    That's the SECOND of the two middles (3 and 4) — exactly what LC 876 wants.


PROGRESSIVE HINTS
------------------
Hint 1: You need `n // 2` without knowing `n` in advance and without a
        second pass. Two pointers moving at different speeds solve this in
        one pass — see topic guide §3.1.

Hint 2: Loop while `fast and fast.next` — this naturally lands `slow` on the
        SECOND middle for even-length lists, which is exactly what the
        problem wants. Verify this by hand on a 6-node example.

Hint 3: Return `slow`, not `slow.val` — the problem wants the remaining
        sub-list starting at the middle node.


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
    def middleNode(self, head: Optional[ListNode]) -> Optional[ListNode]:
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
        ([1, 2, 3, 4, 5], [3, 4, 5]),
        ([1, 2, 3, 4, 5, 6], [4, 5, 6]),
        ([1], [1]),
        ([1, 2], [2]),
    ]
    for values, want in cases:
        got = to_list(sol.middleNode(build_list(values)))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {values!r:<20} -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
