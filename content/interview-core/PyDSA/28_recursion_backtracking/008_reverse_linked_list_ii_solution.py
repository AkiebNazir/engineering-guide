"""
================================================================================
SOLUTION · LeetCode 92 · Reverse Linked List II                         [Medium]
https://leetcode.com/problems/reverse-linked-list-ii/
================================================================================

THE CORE IDEA
--------------
Split into two clean recursions: one that walks forward to REACH the start
of the region (decrementing both `left` and `right` together, since both
are relative to the current head), and one that reverses the first `n`
nodes of whatever it's handed, using the classic "successor" trick — the
node just past the reversed region is captured ONCE, at the deepest call,
and threaded back up unchanged through every shallower call.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. RECURSIVE, TWO HELPERS — `reverseBetween` walks to the start,
   `reverseFirstN` reverses in place with the successor trick. O(n) time,
   O(right) space (call stack). The version taught here.
2. ITERATIVE, ONE PASS — a dummy head, walk `left - 1` steps to a `prev`
   pointer, then repeatedly move the node right after `prev` to the front
   of the region ("head insertion"). O(n) time, O(1) space. The intended
   interview answer for the stated follow-up.
3. REVERSE-THEN-RECONNECT (three passes) — cut the region out, reverse it
   as a standalone list (like plain Reverse Linked List), splice it back
   in. Priced, not written: functionally equivalent to approach 2 but
   conceptually three separate steps instead of one interleaved pass.


================================================================================
STEP BY STEP TRACE — reverseBetween([1,2,3,4,5], left=2, right=4)
================================================================================
Phase 1 — walk to the start (decrementing left AND right each step):
    call reverseBetween(1->2->3->4->5, left=2, right=4)
      left != 1 -> recurse on (2->3->4->5, left=1, right=3)
        call reverseBetween(2->3->4->5, left=1, right=3)
          left == 1 -> hand off to reverseFirstN(2->3->4->5, n=3)

Phase 2 — reverseFirstN(2->3->4->5, n=3), reversing exactly 3 nodes:
    call reverseFirstN(head=2, n=3)
      call reverseFirstN(head=3, n=2)
        call reverseFirstN(head=4, n=1)   n==1 -> base case, return head=4
        successor = head(3).next.next = 5      [captured HERE, n==2, the deepest non-base call]
        head(3).next.next = head(3)  ->  4->3
        head(3).next = successor(5)   ->  3->5
        return rest = 4                   [unchanged from the base case]
      successor is NOT recomputed here — still 5, reused as-is
      head(2).next.next = head(2)  ->  3->2   (3's .next was just set to 5 above; now 3.next.next, i.e. 2, is set)
      head(2).next = successor(5)  wait -- actually head.next is reassigned using the SAME successor(5)
      return rest = 4  (unchanged, threaded straight through)

Result of reverseFirstN: head 4 -> 3 -> 2 -> 5.  Phase 1's `head.next` (node 1)
was untouched and still points at whatever reverseBetween(left==1) returned:
    1 -> 4 -> 3 -> 2 -> 5

Final list: [1, 4, 3, 2, 5] — matches the expected output.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time   Space          Mutates input?  Note
    ---------------------------  -----  -------------  ---------------  --------------------------------
    Recursive, two helpers      O(n)   O(right) stack  yes (relinks)    successor captured once, deepest call
    Iterative, one pass         O(n)   O(1)            yes (relinks)    the stated follow-up's answer
    Reverse-then-reconnect      O(n)   O(1)            yes (relinks)    same result, three explicit steps


================================================================================
EDGE CASES
================================================================================
    left == right           -> no reversal at all; `reverseFirstN`'s
                                `n == 1` base case fires immediately once
                                the region is reached, list unchanged.
    left == 1                -> region starts at the very head; the
                                `reverseBetween` walking phase does ZERO
                                steps, going straight to `reverseFirstN`.
    right == n (last node)   -> `successor` ends up `None` (there is no
                                node past the reversed region) — the
                                reversed segment's tail must correctly
                                point at `None`, not dangle or cycle.
    n == 1 (single-node list) -> only valid call is left=right=1; the
                                walking phase does nothing and
                                `reverseFirstN` immediately hits its
                                base case.


================================================================================
COMMON MISTAKES
================================================================================
1. Recomputing `successor = head.next.next` at EVERY level of
   `reverseFirstN` instead of only at the deepest call — by the time a
   shallower call runs, `head.next.next` has already been rewired by
   deeper calls to point INTO the reversed segment, so recomputing it
   captures garbage instead of the true node just past the region.
2. Decrementing only `left` (not `right`) in `reverseBetween`'s walking
   phase — `right` is also measured relative to the current head, so
   failing to decrement it causes `reverseFirstN` to reverse the wrong
   number of nodes once the walk reaches the start.
3. Returning `head` instead of the recursive call's result from
   `reverseFirstN` — the new head of the reversed segment is the node
   that was originally deepest (last), not the node the current call
   started with; `head` is now BURIED inside the reversed segment, not
   at its front.
4. Forgetting that `reverseBetween`'s non-base-case branch must return
   `head` (the node BEFORE the region, untouched), not the recursive
   call's result directly — position `left - 1`'s node must still point
   to itself in the chain; only its `.next` gets replaced by the
   recursive call's return value.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you do this in one pass with O(1) extra space?
A: Yes — the iterative version: walk `left - 1` steps with a `prev`
   pointer, then repeatedly detach the node right after `prev` and
   re-insert it at the front of the region ("head insertion"), for
   exactly `right - left` iterations.

Q: Why does `reverseFirstN` need the recursive call to happen BEFORE the
   pointer rewiring, not after?
A: The recursive call must fully reverse everything DEEPER first (and, on
   its way back up, hand back both the new sub-head and an already-valid
   `successor`) before the current level can safely redirect its own two
   `.next` pointers — reversing outside-in instead of inside-out would
   overwrite links still needed by deeper unresolved calls.

Q: How would you generalize this to reversing every disjoint length-k
   block in the list (not just one region)?
A: That's LC 25 (Reverse Nodes in k-Group) — recurse exactly like 007's
   pair-swap, but reverse a block of k instead of swapping a pair of 2,
   using this problem's `reverseFirstN` as the per-block reversal.


================================================================================
RELATED PROBLEMS
================================================================================
    Topic 28, 007 Swap Nodes in Pairs — the "reverse the rest first, then
                                        stitch this piece around it" shape,
                                        at pair granularity instead of a
                                        variable-length region.
    LC 206  Reverse Linked List       — the base case this problem's
                                        `reverseFirstN` reduces to when
                                        `left == 1, right == n`.
    LC 25   Reverse Nodes in k-Group  — the direct generalization to
                                        repeated fixed-size regions.
================================================================================
"""

from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def reverseBetween(self, head: Optional[ListNode], left: int, right: int) -> Optional[ListNode]:
        """Recursive, two helpers, successor captured once. O(n) time, O(right) space."""
        self._successor: Optional[ListNode] = None
        return self._reverse_between(head, left, right)

    def _reverse_between(self, head, left, right):
        if left == 1:
            return self._reverse_first_n(head, right)
        head.next = self._reverse_between(head.next, left - 1, right - 1)
        return head

    def _reverse_first_n(self, head, n):
        if n == 1:
            self._successor = head.next
            return head
        rest = self._reverse_first_n(head.next, n - 1)
        head.next.next = head
        head.next = self._successor
        return rest

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def reverseBetween_iterative(self, head: Optional[ListNode], left: int, right: int) -> Optional[ListNode]:
        """Iterative, one pass, head-insertion. O(n) time, O(1) space."""
        dummy = ListNode(0, head)
        prev = dummy
        for _ in range(left - 1):
            prev = prev.next
        curr = prev.next
        for _ in range(right - left):
            nxt = curr.next
            curr.next = nxt.next
            nxt.next = prev.next
            prev.next = nxt
        return dummy.next


# ==============================================================================
# TESTS — run:  python 008_reverse_linked_list_ii_solution.py
# ==============================================================================
def build(values):
    head = None
    for v in reversed(values):
        head = ListNode(v, head)
    return head


def to_list(head):
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out


CASES = [
    ([1, 2, 3, 4, 5], 2, 4, [1, 4, 3, 2, 5]),
    ([5], 1, 1, [5]),
    ([1, 2, 3], 1, 3, [3, 2, 1]),
    ([1, 2, 3, 4], 1, 2, [2, 1, 3, 4]),
    ([1, 2, 3, 4], 3, 4, [1, 2, 4, 3]),
    ([1, 2, 3, 4, 5], 1, 5, [5, 4, 3, 2, 1]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    impls = [
        ("recursive          ", sol.reverseBetween),
        ("iterative one-pass ", sol.reverseBetween_iterative),
    ]

    for name, fn in impls:
        ok = True
        for values, left, right, expected in CASES:
            head = build(values)
            got = to_list(fn(head, left, right))
            ok &= got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
