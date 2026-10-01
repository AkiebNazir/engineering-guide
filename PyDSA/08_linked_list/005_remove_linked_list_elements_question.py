"""
================================================================================
LeetCode 203 · Remove Linked List Elements                              [Easy]
https://leetcode.com/problems/remove-linked-list-elements/
Topic: 08 · Linked List
================================================================================

PROBLEM
-------
Given the head of a linked list and an integer `val`, remove all the nodes
whose value equals `val`, and return the new head.


EXAMPLES
--------
Example 1:
    Input:  head = [1,2,6,3,4,5,6], val = 6
    Output: [1,2,3,4,5]

Example 2:
    Input:  head = [], val = 1
    Output: []

Example 3:
    Input:  head = [7,7,7,7], val = 7
    Output: []


CONSTRAINTS
-----------
    The number of nodes in the list is in the range [0, 10^4].
    1 <= Node.val <= 50
    0 <= val <= 50


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is the topic guide's Part 2 case study, verbatim: deleting a node whose
`.val == val` is a one-line rewire (`curr.next = curr.next.next`) UNLESS the
matching node is the very head of the list — then there is no "node before
it" to rewire, and `head` itself must be reassigned instead.

Without a dummy node this needs two separate pieces of logic: a `while` loop
that strips matching values off the FRONT (because the new head might itself
need removing, and then the node after THAT might also match, arbitrarily
many times in a row — e.g. [6,6,6,1], val=6), and then a second loop for
everything after. With a dummy node standing one position before the real
head, "the head matches" and "some node in the middle matches" become the
exact same code path.

    dummy = ListNode(next=head)   # dummy.next is ALWAYS "the real head"
    curr = dummy
    while curr.next:
        if curr.next.val == val:
            curr.next = curr.next.next   # skip the matching node
        else:
            curr = curr.next             # only advance when we DIDN'T delete
    return dummy.next

Note the `else`: after a deletion, `curr` must NOT advance, because
`curr.next` is now a brand new node that also needs to be checked (this is
how a run of consecutive matches — [7,7,7,7] — collapses correctly in one
pass without re-entering the loop from a different state).


WHAT TO THINK ABOUT
--------------------
1. Why does deleting a match at the head require different code from
   deleting a match in the middle, if you don't use a dummy?

2. After `curr.next = curr.next.next` removes a match, why must `curr` stay
   put instead of advancing? Trace [7,7,7,7] by hand assuming you advance
   unconditionally and see what survives.

3. What happens to a fully-empty input, `head = None`? Should the dummy node
   approach need a special check for it, or does the `while curr.next` loop
   already handle it for free?

4. Can `val` simply not appear anywhere in the list? What should happen then
   (hint: nothing — the list should come back unchanged)?


PROGRESSIVE HINTS
------------------
Hint 1: Allocate `dummy = ListNode(next=head)` and start `curr` there instead
        of at `head`.

Hint 2: Loop `while curr.next:` — never dereference `curr` itself past the
        dummy, only ever look one node ahead through `curr.next`.

Hint 3: On a match, rewire and DO NOT move `curr`. On a non-match, move
        `curr = curr.next`. Return `dummy.next`, not `dummy`.


COMPLEXITY TARGET
------------------
    Time:  O(n)   — one pass
    Space: O(1)   — one extra dummy node, no auxiliary structure
================================================================================
"""

from typing import List, Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def removeElements(self, head: Optional[ListNode], val: int) -> Optional[ListNode]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 005_remove_linked_list_elements_question.py
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
        ([1, 2, 6, 3, 4, 5, 6], 6, [1, 2, 3, 4, 5]),
        ([], 1, []),
        ([7, 7, 7, 7], 7, []),
        ([1, 1, 1, 2], 1, [2]),
        ([2, 1, 1, 1], 1, [2]),
        ([1], 1, []),
        ([1], 2, [1]),
        ([1, 2, 3], 4, [1, 2, 3]),
    ]

    passed = 0
    for values, val, expected in cases:
        head = list_to_linked(values)
        got_head = sol.removeElements(head, val)
        got = linked_to_list(got_head)
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  head={values!r:<24} val={val:<3} -> {got}  "
              f"(want {expected})")

    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
