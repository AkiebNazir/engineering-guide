"""
================================================================================
QUESTION · LeetCode 206 · Reverse Linked List                          [Easy]
https://leetcode.com/problems/reverse-linked-list/
================================================================================

PROBLEM
-------
Given the `head` of a singly linked list, reverse the list, and return the
new head.


EXAMPLES
--------
Example 1:
    Input:  head = [1,2,3,4,5]
    Output: [5,4,3,2,1]

Example 2:
    Input:  head = [1,2]
    Output: [2,1]

Example 3:
    Input:  head = []
    Output: []


CONSTRAINTS
-----------
    The number of nodes in the list is in the range [0, 5000].
    -5000 <= Node.val <= 5000

FOLLOW UP
---------
    A linked list can be reversed either iteratively or recursively. Could
    you implement both?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Reversal means every node's `.next` must point at what USED to be before it,
not after it. The catch: the moment you write `curr.next = prev`, you have
destroyed your only way to reach the rest of the original list — unless you
saved a reference to it FIRST.

    1 -> 2 -> 3 -> None          (before)
    None <- 1 <- 2 <- 3          (after; head is now 3)

Three pointers, one loop, in a fixed order every time:
    1. nxt  = curr.next     # SAVE the rest of the list before touching it
    2. curr.next = prev     # REWIRE this node backward
    3. prev = curr           # ADVANCE prev
    4. curr = nxt              # ADVANCE curr using the SAVED reference

Do these out of order — especially save-before-rewire — and the list is
silently truncated, not crashed. See the topic guide Part 1.3 for the exact
broken version and why it fails quietly instead of loudly.


PROGRESSIVE HINTS
------------------
Hint 1: You need three names in flight at once: what came before the current
        node, the current node, and what comes after it.

Hint 2: Save `curr.next` into a temporary BEFORE you overwrite `curr.next`.
        If you rewire first, you lose the rest of the list forever.

Hint 3: The loop ends when `curr` is None. The answer is `prev`, not `head` —
        `head` is now the OLD tail (or None on empty input).


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1) iterative (O(n) if you choose the recursive variant)
================================================================================
"""

from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def reverseList(self, head: Optional[ListNode]) -> Optional[ListNode]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TEST HELPERS — do not need to be solved, just used by run_tests()
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
        ([1, 2, 3, 4, 5], [5, 4, 3, 2, 1]),
        ([1, 2], [2, 1]),
        ([], []),
        ([1], [1]),
    ]
    for values, want in cases:
        got = to_list(sol.reverseList(build_list(values)))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {values!r:<20} -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
