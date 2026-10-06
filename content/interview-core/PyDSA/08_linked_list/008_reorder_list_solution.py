"""
================================================================================
SOLUTION · LeetCode 143 · Reorder List                                [Medium]
https://leetcode.com/problems/reorder-list/
================================================================================

THE CORE IDEA
--------------
Reorder List = problem 004 (find the middle) + problem 001 (reversal) +
one merge/interleave step. Not a new algorithm — a composition of two
techniques already in this topic's toolbox. See the topic guide's §4.2.

    1. find the middle              (§3.1, slow/fast)
    2. reverse the second half      (§4.1, the reversal template)
    3. merge the two halves, alternating one node from each

    1 -> 2 -> 3 -> 4 -> 5
    split at middle:      1 -> 2 -> 3        4 -> 5
    reverse second half:  1 -> 2 -> 3        5 -> 4
    merge alternating:    1 -> 5 -> 2 -> 4 -> 3


================================================================================
APPROACH 1 · Copy to array, index-based rebuild (O(n) space, priced not coded)
================================================================================
    nodes = []
    node = head
    while node:
        nodes.append(node)
        node = node.next
    lo, hi = 0, len(nodes) - 1
    while lo < hi:
        nodes[lo].next = nodes[hi]
        lo += 1
        if lo == hi:
            break
        nodes[hi].next = nodes[lo]
        hi -= 1
    nodes[lo].next = None

Correct and honestly simpler to write under pressure (random access via the
array sidesteps every pointer-chasing subtlety) — but O(n) EXTRA space for
the array of node references, when the problem explicitly invites an O(1)
in-place solution. Name it, then deliver Approach 2.


================================================================================
APPROACH 2 · Find middle + reverse + merge ✅ (O(1) space — the answer)
================================================================================
Three phases, each one a technique already proven correct elsewhere in this
topic:

    Phase 1 — find the middle (§3.1):
        slow = fast = head
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
        # slow is now the start of the second half

    Phase 2 — cut the list in two, then reverse the second half (§4.1):
        second = slow.next
        slow.next = None        # sever — first half now ends cleanly
        prev = None
        while second:
            nxt = second.next
            second.next = prev
            prev = second
            second = nxt
        second = prev           # head of the reversed second half

    Phase 3 — merge, alternating one node from each half:
        first = head
        while second:
            first_next = first.next    # SAVE before overwriting (topic Part 1.3)
            second_next = second.next  # SAVE before overwriting
            first.next = second
            second.next = first_next
            first = first_next
            second = second_next

The `while second:` condition (not `while first and second:`) is deliberate:
the first half is always the same length as the second half or exactly ONE
node longer (when total length is odd), so the first half never runs out
before the second half does — the loop naturally stops when the (shorter or
equal) second half is exhausted, leaving any odd-one-out first-half node as
the correct final tail with `.next` already `None` from how it was linked.


================================================================================
STEP BY STEP — head = [1, 2, 3, 4, 5]   (odd length)
================================================================================
    Phase 1 — find the middle:
        1 -> 2 -> 3 -> 4 -> 5 -> None
        slow ends at node 3 (fast fell off the end after 2 hops of 2)

    Phase 2 — cut at slow, reverse the second half:
        first half:   1 -> 2 -> 3 -> None
        second half (before reverse):  4 -> 5 -> None
        second half (after reverse):   5 -> 4 -> None

    Phase 3 — merge, alternating:
        first=1, second=5
          save first_next=2, second_next=4
          1.next = 5;  5.next = 2
          first=2, second=4
        first=2, second=4
          save first_next=3, second_next=None
          2.next = 4;  4.next = 3
          first=3, second=None
        second is None -> loop ends

    result: 1 -> 5 -> 2 -> 4 -> 3 -> None      ✓  (3.next was already None
                                                     from Phase 2's cut)


================================================================================
STEP BY STEP — head = [1, 2, 3, 4]   (even length)
================================================================================
    Phase 1: slow ends at node 2 (start of the second half, for even length)
    Phase 2: first half 1->2->None, second half reversed: 4->3->None
    Phase 3:
        first=1, second=4: save first_next=2, second_next=3;
                            1.next=4; 4.next=2; first=2, second=3
        first=2, second=3: save first_next=None, second_next=None;
                            2.next=3; 3.next=None; first=None, second=None
        loop ends (second is None)
    result: 1 -> 4 -> 2 -> 3 -> None      ✓


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time   Space   Mutates input?  Note
    ---------------------------------  -----  ------  ---------------  -----------------
    Copy to array, index rebuild       O(n)   O(n)    yes              simpler, more space
    Find middle + reverse + merge ✅   O(n)   O(1)    yes (in place)   the answer


================================================================================
EDGE CASES
================================================================================
    single node          -> unchanged. slow/fast never advances past head;
                                   the "second half" is empty; merge loop
                                   never runs.
    two nodes              -> unchanged. [1,2] -> [1,2] — the reorder of a
                                   two-node list IS the identity, since
                                   Ln == the second node already.
    three nodes              -> [1,2,3] -> [1,3,2]. Smallest case where the
                                   reorder actually changes anything.
    odd length                -> the middle node (found by slow/fast) ends
                                   up as the FIRST half's leftover tail —
                                   verified by the odd-length trace above.
    even length                 -> both halves are equal length; merge
                                   exhausts both pointers on the same step.
    all identical values           -> reorder still reshuffles POSITIONS
                                   even though every value looks the same;
                                   verify with node IDENTITY in tests, not
                                   just values, to catch a merge that
                                   silently no-ops.


================================================================================
COMMON MISTAKES
================================================================================
1. Reversing the second half BEFORE finding the correct split point, or
   reversing the WRONG portion — corrupts the list before the merge even
   starts. Always find the middle first (Phase 1), only then reverse
   (Phase 2).
2. Forgetting to sever `slow.next = None` after finding the middle — the
   "first half" then still trails into the second half's original (now
   partially reversed) structure, corrupting the merge.
3. THE classic bug from topic guide Part 1.3, in a new shape: overwriting
   `first.next` or `second.next` during the merge BEFORE saving the node
   each pointer needs to advance to next. Both `first_next` and
   `second_next` must be captured before either assignment in the merge
   loop body.
4. Using `while first and second:` instead of `while second:` — usually
   harmless since first never actually runs out first, but relying on the
   wrong invariant makes the loop's correctness accidental rather than
   reasoned; state explicitly why `second` is the one guaranteed to be
   shorter-or-equal.
5. Testing only with VALUES (`linked_to_list(head) == expected`) and never
   verifying with node IDENTITY — a reorder implementation that leaves the
   list untouched can still "pass" a values-only palindromic test input,
   masking a merge that does nothing.
6. Trying to reorder by modifying `.val` fields instead of `.next` pointers
   — technically produces the right sequence of values, but violates the
   problem's explicit constraint and defeats the point of the exercise
   (this topic is about pointer rewiring, not value shuffling).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you avoid reversing the second half, e.g. with a deque?
A: Yes — `collections.deque(nodes)`, then alternately `popleft()` and
   `pop()`. O(n) time, O(n) space (the deque holds every node reference) —
   trades the in-place reversal for a data structure, still not O(1) space.

Q: What if this needed to be done for a DOUBLY linked list?
A: The reversal step becomes unnecessary — you can walk the second half
   backward directly via `.prev`, so the merge can interleave `head`-forward
   and `tail`-backward pointers without ever rewriting the second half's
   direction first.

Q: How would you verify a merge implementation doesn't just leave the list
   unchanged for a palindromic values case?
A: Compare node IDENTITY (`is`), not just `.val` sequences, in tests — see
   COMMON MISTAKES #5 and this file's test suite, which checks identity to
   catch a no-op merge.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 206  Reverse Linked List        — Phase 2's reversal template
                                          (problem 001 here)
    LC 876  Middle of the Linked List  — Phase 1's slow/fast split
                                          (problem 004 here)
    LC 21   Merge Two Sorted Lists     — a different merge (by VALUE order,
                                          not strict alternation) using the
                                          same dummy-head + two-pointer shape
    LC 234  Palindrome Linked List     — the SAME find-middle + reverse
                                          composition, used for comparison
                                          instead of reordering (problem 007
                                          here)
================================================================================
"""

import time
from typing import List, Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def reorderList(self, head: Optional[ListNode]) -> None:
        """Find middle (§3.1) + reverse second half (§4.1) + merge/interleave.
        O(n) time, O(1) extra space, mutates in place. The answer."""
        if not head or not head.next:
            return

        # Phase 1: find the middle.
        slow = fast = head
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next

        # Phase 2: cut, then reverse the second half.
        second = slow.next
        slow.next = None
        prev = None
        while second:
            nxt = second.next
            second.next = prev
            prev = second
            second = nxt
        second = prev

        # Phase 3: merge, alternating one node from each half.
        first = head
        while second:
            first_next = first.next
            second_next = second.next
            first.next = second
            second.next = first_next
            first = first_next
            second = second_next

    # ------------------------------------------------------------------
    # Alternative: copy node references into an array, rebuild by index.
    # ------------------------------------------------------------------
    def reorderList_array(self, head: Optional[ListNode]) -> None:
        """O(n) time, O(n) space — random access via an array of node
        references sidesteps every pointer-chasing subtlety."""
        if not head:
            return
        nodes = []
        node = head
        while node:
            nodes.append(node)
            node = node.next
        lo, hi = 0, len(nodes) - 1
        while lo < hi:
            nodes[lo].next = nodes[hi]
            lo += 1
            if lo == hi:
                break
            nodes[hi].next = nodes[lo]
            hi -= 1
        nodes[lo].next = None


# ==============================================================================
# TESTS — run:  python 008_reorder_list_solution.py
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


CASES = [
    ([1, 2, 3, 4], [1, 4, 2, 3]),
    ([1, 2, 3, 4, 5], [1, 5, 2, 4, 3]),
    ([1], [1]),
    ([1, 2], [1, 2]),
    ([1, 2, 3], [1, 3, 2]),
    ([1, 2, 3, 4, 5, 6], [1, 6, 2, 5, 3, 4]),
    ([7], [7]),
    ([5, 5, 5, 5], [5, 5, 5, 5]),   # identical values — verified by IDENTITY below
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: find-middle+reverse+merge vs array-rebuild (values) ---")
    for values, expected in CASES:
        h1 = list_to_linked(values)
        sol.reorderList(h1)
        got1 = linked_to_list(h1)

        h2 = list_to_linked(values)
        sol.reorderList_array(h2)
        got2 = linked_to_list(h2)

        ok = got1 == expected and got2 == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  input={values!r:<20} -> {got1}  (want {expected})")

    # ----------------------------------------------------------------------
    # ⚠️  Identity check: a no-op "merge" would still pass a palindromic
    # values-only test. Verify the actual NODE ORDER changed by identity.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  verifying by node IDENTITY, not just values (common mistake #5) ---")
    values = [5, 5, 5, 5]
    head = list_to_linked(values)
    original_nodes = []
    node = head
    while node:
        original_nodes.append(node)
        node = node.next
    sol.reorderList(head)
    reordered_nodes = []
    node = head
    while node:
        reordered_nodes.append(node)
        node = node.next
    # Expected reorder of positions [0,1,2,3] -> [0,3,1,2]
    expected_order = [original_nodes[i] for i in (0, 3, 1, 2)]
    identity_ok = reordered_nodes == expected_order
    print(f"  values look identical before/after: {values} -> {linked_to_list(head)}")
    print(f"  but node OBJECT order is [0,3,1,2] of the original chain: {identity_ok}")
    all_ok &= identity_ok

    # ----------------------------------------------------------------------
    # Step-by-step trace, phase by phase.
    # ----------------------------------------------------------------------
    print("\n--- trace: reorderList([1,2,3,4,5]), phase by phase ---")
    head = list_to_linked([1, 2, 3, 4, 5])
    print(f"  input: {linked_to_list(head)}")

    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    print(f"  Phase 1 (find middle): slow.val={slow.val}")

    second = slow.next
    slow.next = None
    print(f"  Phase 2a (cut): first half={linked_to_list(head)}  "
          f"second half (pre-reverse)={linked_to_list(second)}")
    prev = None
    while second:
        nxt = second.next
        second.next = prev
        prev = second
        second = nxt
    second = prev
    print(f"  Phase 2b (reverse 2nd half): second half (reversed)={linked_to_list(second)}")

    first = head
    step = 0
    while second:
        step += 1
        first_next = first.next
        second_next = second.next
        first.next = second
        second.next = first_next
        print(f"  Phase 3 step {step}: link {first.val}->{second.val}, "
              f"then {second.val}->{first_next.val if first_next else None}")
        first = first_next
        second = second_next
    print(f"  final: {linked_to_list(head)}")

    # ----------------------------------------------------------------------
    # In-place O(1) space vs array-rebuild O(n) space: measured runtime.
    # ----------------------------------------------------------------------
    print("\n--- in-place O(1) space vs array-rebuild O(n) space: measured runtime ---")
    print(f"  {'n':>8} {'in-place O(1)':>16} {'array O(n)':>14} {'ratio':>8}")
    for n in (10_000, 100_000, 500_000):
        vals = list(range(n))
        h1 = list_to_linked(vals)
        t0 = time.perf_counter()
        sol.reorderList(h1)
        t1 = time.perf_counter()
        h2 = list_to_linked(vals)
        t2 = time.perf_counter()
        sol.reorderList_array(h2)
        t3 = time.perf_counter()
        ip_ms = (t1 - t0) * 1000
        arr_ms = (t3 - t2) * 1000
        ratio = arr_ms / ip_ms if ip_ms > 0 else float("inf")
        print(f"  {n:>8} {ip_ms:>14.2f}ms {arr_ms:>12.2f}ms {ratio:>7.2f}x")
    print("  Both are O(n) time in practice; the array version's extra list")
    print("  allocation shows up as modestly higher cost, and — the real point —")
    print("  O(n) extra memory that the in-place three-phase version avoids.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
