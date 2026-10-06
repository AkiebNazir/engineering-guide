"""
================================================================================
SOLUTION · LeetCode 876 · Middle of the Linked List                    [Easy]
https://leetcode.com/problems/middle-of-the-linked-list/
================================================================================

THE CORE IDEA
--------------
"The middle" needs `n // 2`, but a linked list has no index — computing `n`
means one full walk. Floyd's slow/fast pointers (topic guide §3.1) collapse
this to a SINGLE pass: `slow` advances one node per iteration, `fast`
advances two. Because `fast` always covers exactly twice the distance `slow`
does, the moment `fast` falls off the end, `slow` has covered exactly half
the list — no length precomputation needed.

    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    return slow

O(n) time, O(1) space, one pass. The loop condition `fast and fast.next`
(rather than just `fast`) is what makes this land on the SECOND of the two
middles for even-length lists — exactly what LC 876 specifies.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (two-pass, count then walk): walk the whole list once to count
`n`, then walk again for `n // 2` steps to reach the middle node. Also O(n)
time and O(1) space — asymptotically tied with the one-pass version — but it
touches every node TWICE instead of once. Priced and benchmarked below: on
a linked list (no random access, so no early-exit tricks), two full
traversals cost roughly double the wall-clock time of one.

Approach 1 (slow/fast, one pass) ✅ — the answer, shown above.

Approach 2 (naive, don't code it): dump every node into a Python list, index
`values[len(values) // 2]`. Correct, but O(n) EXTRA space for something the
one-pass pointer approach does in O(1) — never the answer once the O(1)
constraint is understood, but worth naming as the "obvious first idea."


================================================================================
STEP BY STEP TRACE
================================================================================
Odd length: 1 -> 2 -> 3 -> 4 -> 5 -> None

    slow=1 fast=1
    slow=2 fast=3
    slow=3 fast=5
    fast.next is None -> loop ends. slow = 3 (the true middle). ✓

Even length: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> None

    slow=1 fast=1
    slow=2 fast=3
    slow=3 fast=5
    fast is not None but fast.next(=6).next is None, so this iteration still
    runs:  slow=4  fast=None (5.next.next steps past the end)
    loop condition `fast and fast.next` -> fast is None -> ends. slow = 4.
    That's the SECOND of the two middles (3, 4) — exactly what LC 876 wants.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time   Space   Mutates input?  Note
    ------------------------------  -----  ------  ---------------  ----------------------
    Collect into list, index         O(n)   O(n)    no               wastes space
    Two-pass: count then walk        O(n)   O(1)    no               touches every node TWICE
    Slow/fast, one pass ✅           O(n)   O(1)    no               the answer, ONE traversal


================================================================================
EDGE CASES
================================================================================
    [1]           -> [1]      single node: fast.next is None immediately,
                             loop body never runs, slow stays at head.
    [1,2]         -> [2]      two nodes: exercises the even-length "second
                             middle" rule on the smallest possible case.
    [1,2,3]       -> [2,3]    smallest odd case beyond a single node.
    long list      -> the one-pass vs two-pass timing gap is most visible
                     here; benchmarked below.


================================================================================
COMMON MISTAKES
================================================================================
1. Looping on `while fast:` instead of `while fast and fast.next:` —
   crashes with AttributeError the moment `fast.next` is None and the code
   tries to read `fast.next.next` anyway. Same class of bug as 003's
   unguarded cycle-detection loop.

2. Returning the FIRST of the two middles on an even-length list instead of
   the second — happens if you start `fast` one step ahead of `slow`, or use
   a `<` instead of `<=`-flavored stopping condition. Re-derive from the
   trace above rather than guessing.

3. Precomputing `n` with one pass and then walking `n // 2` steps with a
   SECOND, separate pass when a single-pass approach exists and is no more
   code — correct, but strictly more work for no benefit; see the benchmark.

4. Off-by-one when translating "walk n // 2 steps" into a loop bound in the
   two-pass approach — easy to return the node BEFORE the middle instead of
   the middle itself if the loop runs one too few or too many times.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the FIRST middle instead of the second, for even-length lists.
A: Start `fast` one node ahead of `slow` (i.e. `fast = head.next`) before
   the loop, or equivalently loop on `while fast.next and fast.next.next`
   with `slow` starting at `head` — re-derive from a small example rather
   than memorizing, since the exact off-by-one is easy to get backwards.

Q: What if you needed the node just BEFORE the middle (to split the list in
   two, e.g. for problem 008 Reorder List)?
A: Track one extra pointer, `prev`, that trails `slow` by one step (assign
   `prev = slow` right before `slow = slow.next` each iteration) — this is
   exactly what problem 008 needs to cleanly separate the first half from
   the second.

Q: Could binary search find the middle faster?
A: No — binary search needs O(1) random access to compare against a
   midpoint, which a linked list never has (topic guide §1.0). Any "search"
   on a linked list still costs O(n) to reach an arbitrary position.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 141  Linked List Cycle              — same slow/fast SHAPE, different
                                           stopping condition (identity match
                                           vs fast falling off the end)
    LC 143  Reorder List                    — needs the middle as step 1 (008)
    LC 234  Palindrome Linked List          — needs the middle as step 1 (007)
    LC 19   Remove Nth Node From End of List — a different two-pointer GAP
                                           pattern, not slow/fast (topic
                                           guide §3.3, problem 009)
================================================================================
"""

import random
import time
from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def middleNode(self, head: Optional[ListNode]) -> Optional[ListNode]:
        """Slow/fast pointers, one pass. O(n) time, O(1) space.
        The answer. See THE CORE IDEA above."""
        slow = fast = head
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
        return slow

    def middleNode_two_pass(self, head: Optional[ListNode]) -> Optional[ListNode]:
        """Two-pass: count n, then walk n // 2 steps. Same O(n)/O(1)
        complexity class, but touches every node TWICE."""
        n = 0
        node = head
        while node:
            n += 1
            node = node.next
        node = head
        for _ in range(n // 2):
            node = node.next
        return node

    # ------------------------------------------------------------------
    # Naive baseline — priced, not the answer.
    # ------------------------------------------------------------------
    def middleNode_collect(self, head: Optional[ListNode]) -> Optional[ListNode]:
        """✗ NAIVE — collects every node into a Python list, O(n) extra space."""
        nodes = []
        node = head
        while node:
            nodes.append(node)
            node = node.next
        return nodes[len(nodes) // 2]


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
# TESTS — run:  python 004_middle_of_the_linked_list_solution.py
# ==============================================================================
CASES = [
    ([1, 2, 3, 4, 5], [3, 4, 5]),
    ([1, 2, 3, 4, 5, 6], [4, 5, 6]),
    ([1], [1]),
    ([1, 2], [2]),
    ([1, 2, 3], [2, 3]),
    (list(range(1, 21)), list(range(11, 21))),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: slow/fast, one pass ---")
    for values, want in CASES:
        got = to_list(sol.middleNode(build_list(values)))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={len(values):<3} -> {got}  (want {want})")

    print("\n--- correctness: two-pass count-then-walk, cross-checked ---")
    for values, want in CASES:
        got = to_list(sol.middleNode_two_pass(build_list(values)))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={len(values):<3} -> {got}  (want {want})")

    print("\n--- correctness: naive collect-into-list, cross-checked ---")
    for values, want in CASES:
        got = to_list(sol.middleNode_collect(build_list(values)))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={len(values):<3} -> {got}  (want {want})")

    # ----------------------------------------------------------------------
    # Step-by-step trace, even and odd.
    # ----------------------------------------------------------------------
    for values in ([1, 2, 3, 4, 5], [1, 2, 3, 4, 5, 6]):
        print(f"\n--- trace: {values} ({'odd' if len(values) % 2 else 'even'} length) ---")
        slow = fast = build_list(values)
        step = 0
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
            print(f"  step {step}: slow={slow.val}  fast={fast.val if fast else None}")
            step += 1
        print(f"  middle: {slow.val}")

    # ----------------------------------------------------------------------
    # Randomised cross-check, all three implementations.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check (one-pass vs two-pass vs collect) ---")
    random.seed(3)
    trials, mismatches = 3000, 0
    for _ in range(trials):
        n = random.randint(1, 30)
        values = [random.randint(-50, 50) for _ in range(n)]
        r1 = to_list(sol.middleNode(build_list(values)))
        r2 = to_list(sol.middleNode_two_pass(build_list(values)))
        r3 = to_list(sol.middleNode_collect(build_list(values)))
        if not (r1 == r2 == r3):
            mismatches += 1
    print(f"  {trials} random lists (length 1-30): {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # Benchmark: one pass vs two passes over the same list.
    # ----------------------------------------------------------------------
    print("\n--- one-pass slow/fast vs two-pass count-then-walk: measured runtime ---")
    print(f"  {'n':>9} {'one-pass':>12} {'two-pass':>12} {'ratio':>8}")
    for n in (50_000, 200_000, 800_000):
        values = list(range(n))
        head = build_list(values)
        t0 = time.perf_counter(); sol.middleNode(head)
        t1 = time.perf_counter()
        head = build_list(values)
        sol.middleNode_two_pass(head)
        t2 = time.perf_counter()
        one_ms = (t1 - t0) * 1000
        two_ms = (t2 - t1) * 1000
        ratio = two_ms / one_ms if one_ms > 0 else float("inf")
        print(f"  {n:>9} {one_ms:>10.2f}ms {two_ms:>10.2f}ms {ratio:>7.2f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
