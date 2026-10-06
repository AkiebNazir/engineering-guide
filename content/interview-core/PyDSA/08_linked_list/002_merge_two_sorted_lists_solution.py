"""
================================================================================
SOLUTION · LeetCode 21 · Merge Two Sorted Lists                        [Easy]
https://leetcode.com/problems/merge-two-sorted-lists/
================================================================================

THE CORE IDEA
--------------
This is merge sort's merge step, minus the array-allocation cost: because
both inputs are already sorted linked lists, you never need to compare more
than the two current front nodes at once, and "inserting" the winner costs
one pointer rewrite instead of an array write. A dummy/sentinel head (topic
guide Part 2) means the very first node of the result needs no special case
— `tail` starts ONE STEP BEFORE the real merged list, so attaching the first
real node is identical to attaching every subsequent one.

    dummy = ListNode()
    tail = dummy
    while list1 and list2:
        if list1.val <= list2.val:
            tail.next = list1
            list1 = list1.next
        else:
            tail.next = list2
            list2 = list2.next
        tail = tail.next
    tail.next = list1 if list1 else list2   # splice the remainder in one line
    return dummy.next

O(n + m) time, O(1) space — every node is REUSED, not copied.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive, don't code it): collect every value from both lists into
a Python list, `.sort()` it (or use `heapq.merge`), then build a brand-new
chain of new ListNode objects from the sorted values. Correct, but pays
O((n+m) log(n+m)) for a sort you don't need (both inputs are ALREADY
sorted — a comparison-based sort is strictly wasted work here) and O(n+m)
extra space for a new list of nodes when the existing nodes could simply be
rewired. Priced and shown in the benchmark below, never the answer.

Approach 1 (dummy head + two-pointer merge) ✅ — the answer, shown above.
O(n+m) time, O(1) space, reuses existing nodes in place.

Approach 2 (recursive) — `mergeTwoLists(l1, l2)` picks the smaller head and
recurses on the rest:

    def merge_recursive(l1, l2):
        if not l1: return l2
        if not l2: return l1
        if l1.val <= l2.val:
            l1.next = merge_recursive(l1.next, l2)
            return l1
        else:
            l2.next = merge_recursive(l1, l2.next)
            return l2

Same O(n+m) time, elegant to write, but O(n+m) stack frames — same CPython
recursion-limit ceiling risk as 001's recursive reversal. Default to
iterative for long lists.


================================================================================
STEP BY STEP TRACE
================================================================================
list1 = 1 -> 2 -> 4 -> None
list2 = 1 -> 3 -> 4 -> None

    dummy -> None            tail = dummy
    1 vs 1: tie, take list1  dummy -> 1(L1)                 tail=1(L1)  list1=2->4
    2 vs 1: take list2       dummy -> 1(L1) -> 1(L2)         tail=1(L2)  list2=3->4
    2 vs 3: take list1       dummy -> ... -> 1(L2) -> 2      tail=2      list1=4
    4 vs 3: take list2       dummy -> ... -> 2 -> 3          tail=3      list2=4
    4 vs 4: tie, take list1  dummy -> ... -> 3 -> 4(L1)      tail=4(L1)  list1=None
    list1 exhausted -> splice list2's remainder (4) directly:
    dummy -> ... -> 4(L1) -> 4(L2) -> None

result: 1 -> 1 -> 2 -> 3 -> 4 -> 4 -> None


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time            Space   Mutates input?  Note
    -------------------------------  --------------  ------  ---------------  ----------------------
    Collect + sort + rebuild         O((n+m)log(n+m)) O(n+m)  no               wasted sort, new nodes
    Dummy head + 2-pointer merge ✅  O(n+m)          O(1)    yes (rewires .next)  the answer
    Recursive                        O(n+m)          O(n+m)  yes              stack depth risk


================================================================================
EDGE CASES
================================================================================
    [], []              -> []       both empty; dummy.next stays None throughout.
    [], [0]              -> [0]      one empty; the while loop never runs, the
                                    "splice remainder" line does all the work.
    [1,2,3], []           -> [1,2,3]  the mirror of the above.
    equal values           -> tie-breaking must pick ONE list consistently
                             (<=, not <) so ties don't infinite-loop or drop
                             a node; either list winning a tie is fine since
                             both values are equal, but the comparison MUST
                             resolve every tie, not skip it.
    lists of very different lengths -> exercises the "splice the remainder
                             in one line" branch heavily.


================================================================================
COMMON MISTAKES
================================================================================
1. Not using a dummy head — forces special-casing "is this the first node of
   the result yet?" on every iteration, exactly the bug Part 2 of the topic
   guide exists to eliminate.

2. Using `<` instead of `<=` (or vice versa) and then ALSO writing buggy
   loop-advance logic that assumes one specific tie-breaking direction —
   either operator is fine on its own, the bug is inconsistency between the
   comparison and what you assume about it elsewhere.

3. Forgetting the final `tail.next = list1 if list1 else list2` — without
   it, whichever list still has nodes left when the other runs out is simply
   dropped, silently truncating the result exactly like 001's broken
   reversal truncates its list.

4. Allocating NEW ListNode objects for the merged result instead of
   rewiring the existing ones — technically correct output, but wastes
   O(n+m) space the problem doesn't require and isn't what "splicing
   together the nodes" (the problem's own wording) asks for.

5. Comparing `list1.val < list2.val` and using `elif` correctly but then
   forgetting `tail = tail.next` on one branch and not the other — leaves
   `tail` pointing at a stale node, and the next iteration's `tail.next =`
   overwrites the pointer to the node just appended.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Merge k sorted lists instead of 2.
A: LC 23 (problem 014 in this folder) — either merge pairwise (this
   function called log2(k) times, O(N log k)) or use a min-heap of the k
   current front nodes, O(N log k) either way, where N is the total node
   count across all lists.

Q: What if the lists are doubly linked?
A: No algorithmic change — the merge only ever follows `.next` forward; a
   `.prev` pointer would need updating too if you cared about it, but the
   comparison and splicing logic is identical.

Q: Can you avoid the dummy node?
A: Yes, by manually picking whichever of list1/list2 has the smaller head to
   seed `result`/`tail` before the loop, but that reintroduces exactly the
   "special case the first node" branching the dummy exists to remove — not
   recommended.

Q: Do it without mutating either input list.
A: Build entirely new nodes as you walk (copy `.val`, don't reuse the
   pointer) — O(n+m) time, O(n+m) space, and the "mutates input?" column
   flips to "no." Worth naming as the trade-off if the interviewer asks for
   non-destructive merging.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 23   Merge k Sorted Lists         — this generalised via a heap (014)
    LC 88   Merge Sorted Array            — the array analogue, merge from the back
    LC 148  Sort List                     — merge sort ON a linked list, this IS the merge step
    LC 143  Reorder List                  — a different kind of "merge" (alternating), problem 008
================================================================================
"""

import heapq
import random
import time
from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def mergeTwoLists(
        self, list1: Optional[ListNode], list2: Optional[ListNode]
    ) -> Optional[ListNode]:
        """Dummy head + two-pointer merge. O(n+m) time, O(1) space.
        The answer. See THE CORE IDEA above."""
        dummy = ListNode()
        tail = dummy
        while list1 and list2:
            if list1.val <= list2.val:
                tail.next = list1
                list1 = list1.next
            else:
                tail.next = list2
                list2 = list2.next
            tail = tail.next
        tail.next = list1 if list1 else list2
        return dummy.next

    def mergeTwoLists_recursive(
        self, list1: Optional[ListNode], list2: Optional[ListNode]
    ) -> Optional[ListNode]:
        """Recursive merge. O(n+m) time, O(n+m) space (call stack)."""
        if not list1:
            return list2
        if not list2:
            return list1
        if list1.val <= list2.val:
            list1.next = self.mergeTwoLists_recursive(list1.next, list2)
            return list1
        else:
            list2.next = self.mergeTwoLists_recursive(list1, list2.next)
            return list2

    # ------------------------------------------------------------------
    # Naive baseline — priced, not the answer.
    # ------------------------------------------------------------------
    def mergeTwoLists_collect_sort(
        self, list1: Optional[ListNode], list2: Optional[ListNode]
    ) -> Optional[ListNode]:
        """✗ NAIVE — collect all values, sort, rebuild fresh nodes.
        O((n+m) log(n+m)) time, O(n+m) space. Wastes a sort on data that
        was already sorted, and allocates new nodes instead of reusing."""
        values = []
        node = list1
        while node:
            values.append(node.val)
            node = node.next
        node = list2
        while node:
            values.append(node.val)
            node = node.next
        values.sort()

        dummy = ListNode()
        tail = dummy
        for v in values:
            tail.next = ListNode(v)
            tail = tail.next
        return dummy.next


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


# ==============================================================================
# TESTS — run:  python 002_merge_two_sorted_lists_solution.py
# ==============================================================================
CASES = [
    ([1, 2, 4], [1, 3, 4]),
    ([], []),
    ([], [0]),
    ([1, 2, 3], []),
    ([5], [1, 2, 3]),
    ([1, 1, 1], [1, 1]),
    ([-3, 0, 5], [-2, -1, 4]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: dummy-head merge ---")
    for a, b in CASES:
        want = sorted(a + b)
        got = to_list(sol.mergeTwoLists(build_list(a), build_list(b)))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {a!r} + {b!r} -> {got}  (want {want})")

    print("\n--- correctness: recursive merge, cross-checked ---")
    for a, b in CASES:
        want = to_list(sol.mergeTwoLists(build_list(a), build_list(b)))
        got = to_list(sol.mergeTwoLists_recursive(build_list(a), build_list(b)))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {a!r} + {b!r} -> {got}  (want {want})")

    print("\n--- correctness: naive collect+sort, cross-checked ---")
    for a, b in CASES:
        want = to_list(sol.mergeTwoLists(build_list(a), build_list(b)))
        got = to_list(sol.mergeTwoLists_collect_sort(build_list(a), build_list(b)))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {a!r} + {b!r} -> {got}  (want {want})")

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: list1=[1,2,4], list2=[1,3,4] ---")
    l1, l2 = build_list([1, 2, 4]), build_list([1, 3, 4])
    dummy = ListNode()
    tail = dummy
    step = 0
    while l1 and l2:
        if l1.val <= l2.val:
            print(f"  step {step}: {l1.val} <= {l2.val} -> take list1's {l1.val}")
            tail.next = l1
            l1 = l1.next
        else:
            print(f"  step {step}: {l2.val} < {l1.val} -> take list2's {l2.val}")
            tail.next = l2
            l2 = l2.next
        tail = tail.next
        step += 1
    tail.next = l1 if l1 else l2
    remainder = "list1" if l1 else ("list2" if l2 else "neither")
    print(f"  loop ends; splice remainder from {remainder}")
    print(f"  final: {to_list(dummy.next)}")

    # ----------------------------------------------------------------------
    # Randomised cross-check, all three implementations.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check (dummy-head vs recursive vs collect+sort) ---")
    random.seed(11)
    trials, mismatches = 2000, 0
    for _ in range(trials):
        a = sorted(random.randint(-20, 20) for _ in range(random.randint(0, 10)))
        b = sorted(random.randint(-20, 20) for _ in range(random.randint(0, 10)))
        r1 = to_list(sol.mergeTwoLists(build_list(a), build_list(b)))
        r2 = to_list(sol.mergeTwoLists_recursive(build_list(a), build_list(b)))
        r3 = to_list(sol.mergeTwoLists_collect_sort(build_list(a), build_list(b)))
        if not (r1 == r2 == r3 == sorted(a + b)):
            mismatches += 1
    print(f"  {trials} random pairs of sorted lists: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # Benchmark: dummy-head O(n) reuse vs collect+sort O(n log n) rebuild.
    # ----------------------------------------------------------------------
    print("\n--- dummy-head O(n) merge vs collect+sort O(n log n) rebuild: measured runtime ---")
    print(f"  {'n (each list)':>14} {'dummy-head':>14} {'collect+sort':>14} {'ratio':>8}")
    random.seed(0)
    for n in (2_000, 8_000, 32_000):
        a = sorted(random.randint(-10**6, 10**6) for _ in range(n))
        b = sorted(random.randint(-10**6, 10**6) for _ in range(n))
        head1, head2 = build_list(a), build_list(b)
        t0 = time.perf_counter(); sol.mergeTwoLists(head1, head2)
        t1 = time.perf_counter()
        head1, head2 = build_list(a), build_list(b)
        sol.mergeTwoLists_collect_sort(head1, head2)
        t2 = time.perf_counter()
        dh_ms = (t1 - t0) * 1000
        cs_ms = (t2 - t1) * 1000
        ratio = cs_ms / dh_ms if dh_ms > 0 else float("inf")
        print(f"  {n:>14} {dh_ms:>12.2f}ms {cs_ms:>12.2f}ms {ratio:>7.2f}x")
    print("  (heapq.merge would land between these two: O((n+m) log 2) here since k=2,")
    print("   i.e. effectively O(n+m) — but it still allocates fresh nodes like collect+sort.)")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
