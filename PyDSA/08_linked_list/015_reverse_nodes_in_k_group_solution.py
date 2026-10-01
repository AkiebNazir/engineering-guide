"""
================================================================================
SOLUTION · LeetCode 25 · Reverse Nodes in k-Group                      [Hard]
https://leetcode.com/problems/reverse-nodes-in-k-group/
================================================================================

THE CORE IDEA
--------------
This is problem 001's full-list reversal (reverse the WHOLE list) applied
repeatedly to consecutive GROUPS of k nodes instead of the whole list at
once — with one extra rule that makes it harder than "reverse, then
repeat": if the final group has FEWER than k nodes remaining, it must be
left AS-IS, not reversed.

The algorithm is three moving parts per group:
1. Check the group has k nodes available (walk k steps ahead; if you fall
   off the end, STOP — the trailing partial group stays untouched).
2. Reverse exactly those k nodes using problem 001's in-place pointer
   reversal, bounded to stop after k nodes instead of running to the end.
3. Reconnect: the node BEFORE the group must now point at the group's new
   head (the old tail), and the group's new tail (the old head) must point
   at wherever the NEXT group's reversal will begin.

A dummy head (topic guide Part 2, reused from problems 002/005/009) makes
"the node before the group" uniform even for the very first group, exactly
like it uniformed "the first node of the result" in problem 002.


================================================================================
APPROACH 1 · Iterative, group-by-group with a dummy head ✅ (the answer)
================================================================================
    dummy = ListNode(next=head)
    group_prev = dummy
    while True:
        # 1. Check k nodes exist ahead of group_prev.
        kth = group_prev
        for _ in range(k):
            kth = kth.next
            if not kth:
                return dummy.next          # fewer than k left: stop, don't reverse
        group_next = kth.next               # node right after this group

        # 2. Reverse exactly k nodes starting at group_prev.next.
        prev, curr = group_next, group_prev.next
        for _ in range(k):
            nxt = curr.next
            curr.next = prev
            prev = curr
            curr = nxt
        # prev is now the group's new head (was kth); group_prev.next is the
        # group's new tail (the old head) — reconnect both ends.
        new_prev_next = group_prev.next     # save BEFORE overwriting group_prev.next
        group_prev.next = prev
        group_prev = new_prev_next          # this node is now the group's tail

    Time:  O(n)     Space: O(1), reverses in place


================================================================================
APPROACH 2 · Recursive
================================================================================
    def reverseKGroup(self, head, k):
        node = head
        for _ in range(k):
            if not node:
                return head                 # fewer than k nodes: leave as-is
            node = node.next
        # node now points to the first node AFTER this group (or None).
        new_head = self._reverse_bounded(head, node)   # reverse head..node(excl)
        head.next = self.reverseKGroup(node, k)         # head is now the group's TAIL
        return new_head

Reverses the current group, then recurses on the remainder and splices the
recursive result onto the (now-tail) old head. Same O(n) time, but O(n/k)
stack depth from the recursion — worth naming the trade-off, same shape as
problem 001's "recursive reversal risks the recursion-limit ceiling" note.

    Time:  O(n)     Space: O(n/k) call stack


================================================================================
APPROACH 0 · Collect into arrays, reverse each k-chunk, rebuild (baseline)
================================================================================
Walk the list into a Python list of values, reverse each length-k chunk
in the array, rebuild a fresh linked list from the result. Correct and easy
to reason about, but allocates O(n) new nodes when the problem's pointer-
surgery nature (like problem 001) asks for in-place rewiring, and it is not
what interviewers are testing when they pick this problem — priced here,
not the answer.

    Time:  O(n)     Space: O(n), and does not reuse existing nodes


================================================================================
STEP BY STEP TRACE — head = 1->2->3->4->5->6->7->8, k = 3
================================================================================
    dummy -> 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> None
    group_prev = dummy

GROUP 1 (nodes 1,2,3):
    check: walk 3 steps from dummy: dummy->1->2->3, kth=3 (exists) OK
    group_next = kth.next = 4
    reverse 1->2->3 bounded by group_next=4:
        prev=4, curr=1
        step1: nxt=2, 1.next=4,      prev=1, curr=2      (1 -> 4)
        step2: nxt=3, 2.next=1,      prev=2, curr=3      (2 -> 1)
        step3: nxt=4, 3.next=2,      prev=3, curr=4      (3 -> 2)
    prev is now 3 (new group head). reconnect:
        new_prev_next = group_prev.next = 1   (the OLD head, now the group's tail)
        group_prev.next = prev = 3
        group_prev = 1
    list so far: dummy -> 3 -> 2 -> 1 -> 4 -> 5 -> 6 -> 7 -> 8
                                     ^group_prev

GROUP 2 (nodes 4,5,6):
    check: walk 3 steps from group_prev(=1): 1->4->5->6, kth=6 (exists) OK
    group_next = kth.next = 7
    reverse 4->5->6 bounded by group_next=7:
        prev=7, curr=4
        step1: 4.next=7, prev=4, curr=5
        step2: 5.next=4, prev=5, curr=6
        step3: 6.next=5, prev=6, curr=7
    reconnect: new_prev_next = group_prev.next = 4; group_prev.next = 6; group_prev = 4
    list so far: dummy -> 3 -> 2 -> 1 -> 6 -> 5 -> 4 -> 7 -> 8
                                                    ^group_prev

GROUP 3 (nodes 7,8 — only 2 left, k=3):
    check: walk 3 steps from group_prev(=4): 4->7->8->None, kth=None -> STOP
    Fewer than k nodes remain: 7,8 are left UNTOUCHED, in original order.

    FINAL: 3 -> 2 -> 1 -> 6 -> 5 -> 4 -> 7 -> 8 -> None
                                     ^^^^ trailing partial group, NOT reversed


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time   Space    Mutates input?  Note
    ---------------------------------  -----  -------  ---------------  ----------------------
    Collect into array, chunk-reverse  O(n)   O(n)     no               new nodes, simple
    Iterative, dummy head + bounded reversal ✅  O(n)   O(1)     yes (rewires .next)  the answer
    Recursive                          O(n)   O(n/k)   yes (rewires .next)  stack depth risk


================================================================================
EDGE CASES
================================================================================
    head = None, any k        -> None    empty list; the k-node check fails
                                          immediately, dummy.next stays None.
    k = 1                      -> unchanged  every "group" is a single node;
                                          reversing a 1-node group is a no-op,
                                          the algorithm should degrade to
                                          identity without special-casing.
    k == len(list)             -> whole list reversed once, exactly problem
                                          001's full reversal — one group,
                                          no trailing partial group.
    k > len(list)              -> unchanged  the very first group-existence
                                          check fails, so nothing is reversed
                                          at all — the WHOLE list is the
                                          "leftover partial group."
    len(list) % k == 0          -> every group reverses cleanly, no trailing
                                          partial group ever triggers the
                                          "leave as-is" branch — worth a test
                                          that explicitly exercises the OTHER
                                          branch too (a remainder).
    len(list) % k != 0          -> the trailing len%k nodes must stay in
                                          their ORIGINAL relative order —
                                          this is the case most naive
                                          "reverse everything, always" bugs
                                          get wrong.


================================================================================
COMMON MISTAKES
================================================================================
1. Reversing a trailing group that has FEWER than k nodes — the problem
   explicitly requires leaving it untouched. The k-node existence check
   MUST happen before any pointer rewiring for that group starts, not
   after (rewiring then trying to "undo" a partial reversal is fragile and
   unnecessary).

2. Losing `group_next` (the node right after the current group) — the
   reversal loop's `prev` must be SEEDED with `group_next`, not `None`,
   otherwise the group's new tail (old head) ends up pointing at None,
   truncating the rest of the list exactly like problem 001's "starting
   prev at the wrong value" mistake, generalized to groups.

3. Reading `group_prev.next` AFTER overwriting it — the code must save
   `new_prev_next = group_prev.next` (the group's new tail) BEFORE the line
   `group_prev.next = prev` overwrites that pointer, or you lose the
   reference needed to advance `group_prev` to the next group.

4. Off-by-one in the k-node existence check — walking k steps from
   `group_prev` should land exactly on the k-th node of the group (`kth`);
   walking k-1 or k+1 steps miscounts group boundaries by one node.

5. Forgetting the bounded reversal must STOP after exactly k nodes (using
   `group_next` as the loop's implicit boundary) — an unbounded reversal
   (problem 001's version, unmodified) would reverse the ENTIRE remainder
   of the list, not just the current group.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you do it recursively?
A: Yes — see APPROACH 2. Same O(n) time, trades O(1) space for O(n/k) stack
   depth (one frame per group, not per node — shallower than a fully
   recursive single-node reversal like problem 001's recursive variant).
   This is not just theoretical: the runtime demo below actually crashes
   the recursive variant with a real `RecursionError` at n=20000, k=4
   (n/k = 5000 frames, over Python's default 1000-frame limit) while the
   iterative version handles the same input with no trouble — measured on
   this machine, not assumed.

Q: What if the trailing partial group should ALSO be reversed (a variant
   rule)?
A: Drop the "does a full k-node group exist" check's early-return and
   instead reverse whatever nodes remain (fewer than k) using the same
   bounded-reversal loop with a smaller trip count — a one-line change to
   how many iterations the last group's reversal loop runs.

Q: Constant extra space — does this satisfy that?
A: Yes: O(1) auxiliary space in the iterative version (a fixed number of
   pointer variables), independent of n or k; only the recursive version
   spends extra (call-stack) space.

Q: How does this relate to problem 001 (full reversal)?
A: Full reversal is the special case k == len(list) — exactly one group,
   no trailing partial group ever triggers. This problem is "problem 001,
   chunked, with a rule for incomplete trailing chunks."


================================================================================
RELATED PROBLEMS
================================================================================
    LC 206  Reverse Linked List             — the k=n special case (problem 001)
    LC 92   Reverse Linked List II           — reverse a single bounded range
                                              [left, right], the "one group at
                                              a known position" cousin
    LC 24   Swap Nodes in Pairs              — the k=2 special case
    LC 23   Merge k Sorted Lists             — this folder's other Hard, a
                                              different kind of "operate on k
                                              things at once" (problem 014)
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
    def reverseKGroup(self, head: Optional[ListNode], k: int) -> Optional[ListNode]:
        """Iterative, dummy head + bounded in-place reversal per group.
        O(n) time, O(1) space. The answer. See THE CORE IDEA above."""
        dummy = ListNode(next=head)
        group_prev = dummy

        while True:
            # 1. Check k nodes exist ahead of group_prev; if not, stop
            #    (the trailing partial group is left untouched).
            kth = group_prev
            for _ in range(k):
                kth = kth.next
                if not kth:
                    return dummy.next
            group_next = kth.next

            # 2. Reverse exactly k nodes, bounded by group_next.
            prev, curr = group_next, group_prev.next
            for _ in range(k):
                nxt = curr.next
                curr.next = prev
                prev = curr
                curr = nxt

            # 3. Reconnect: group_prev must now point at the new head
            #    (prev, the old kth); the old head becomes the new tail
            #    and is where the next group's reversal starts from.
            new_prev_next = group_prev.next
            group_prev.next = prev
            group_prev = new_prev_next

    def reverseKGroup_recursive(
        self, head: Optional[ListNode], k: int
    ) -> Optional[ListNode]:
        """Recursive: reverse this group, recurse on the remainder, splice.
        O(n) time, O(n/k) call stack."""
        node = head
        for _ in range(k):
            if not node:
                return head
            node = node.next
        # node now points to the first node AFTER this group (or None).
        new_head = self._reverse_bounded(head, node)
        head.next = self.reverseKGroup_recursive(node, k)
        return new_head

    def _reverse_bounded(
        self, head: Optional[ListNode], stop: Optional[ListNode]
    ) -> Optional[ListNode]:
        """Reverse nodes from head up to (not including) stop."""
        prev, curr = stop, head
        while curr is not stop:
            nxt = curr.next
            curr.next = prev
            prev = curr
            curr = nxt
        return prev

    # ------------------------------------------------------------------
    # Baseline — priced, not the answer.
    # ------------------------------------------------------------------
    def reverseKGroup_collect_rebuild(
        self, head: Optional[ListNode], k: int
    ) -> Optional[ListNode]:
        """✗ Collect values, reverse each k-chunk in an array, rebuild
        fresh nodes. O(n) time, O(n) space."""
        values = []
        node = head
        while node:
            values.append(node.val)
            node = node.next

        out = []
        for i in range(0, len(values), k):
            chunk = values[i:i + k]
            if len(chunk) == k:
                chunk.reverse()
            out.extend(chunk)

        dummy = tail = ListNode()
        for v in out:
            tail.next = ListNode(v)
            tail = tail.next
        return dummy.next


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def build_list(values):
    dummy = tail = ListNode()
    for v in values:
        tail.next = ListNode(v)
        tail = tail.next
    return dummy.next


def to_list(head):
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out


# ==============================================================================
# TESTS — run:  python 015_reverse_nodes_in_k_group_solution.py
# ==============================================================================
CASES = [
    ([1, 2, 3, 4, 5], 2, [2, 1, 4, 3, 5]),
    ([1, 2, 3, 4, 5], 3, [3, 2, 1, 4, 5]),
    ([1, 2, 3, 4, 5, 6, 7, 8], 3, [3, 2, 1, 6, 5, 4, 7, 8]),
    ([1, 2, 3, 4, 5, 6], 3, [3, 2, 1, 6, 5, 4]),
    ([1, 2, 3, 4, 5], 1, [1, 2, 3, 4, 5]),
    ([1, 2, 3, 4, 5], 5, [5, 4, 3, 2, 1]),
    ([1, 2, 3, 4, 5], 6, [1, 2, 3, 4, 5]),
    ([], 3, []),
    ([1], 1, [1]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: iterative vs recursive vs collect+rebuild ---")
    for values, k, want in CASES:
        got_iter = to_list(sol.reverseKGroup(build_list(values), k))
        got_rec = to_list(sol.reverseKGroup_recursive(build_list(values), k))
        got_arr = to_list(sol.reverseKGroup_collect_rebuild(build_list(values), k))
        ok = got_iter == want == got_rec == got_arr
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  values={values!r:<28} k={k} -> {got_iter}  (want {want})")

    # ----------------------------------------------------------------------
    # Step-by-step pointer-surgery trace, matching THE header's worked example.
    # ----------------------------------------------------------------------
    print("\n--- trace: head=1..8, k=3 (group-by-group pointer surgery) ---")
    head = build_list([1, 2, 3, 4, 5, 6, 7, 8])
    k = 3
    dummy = ListNode(next=head)
    group_prev = dummy
    group_num = 1
    while True:
        kth = group_prev
        steps_ok = True
        for _ in range(k):
            kth = kth.next
            if not kth:
                steps_ok = False
                break
        if not steps_ok:
            print(f"  group {group_num}: fewer than k={k} nodes remain -> LEFT AS-IS, stop")
            break
        group_next = kth.next
        group_vals = []
        node = group_prev.next
        for _ in range(k):
            group_vals.append(node.val)
            node = node.next
        print(f"  group {group_num}: nodes {group_vals} found (group_next={getattr(group_next, 'val', None)})")

        prev, curr = group_next, group_prev.next
        for _ in range(k):
            nxt = curr.next
            curr.next = prev
            prev = curr
            curr = nxt
        new_prev_next = group_prev.next
        group_prev.next = prev
        group_prev = new_prev_next
        print(f"    after reversal+reconnect: list so far = {to_list(dummy.next)}")
        group_num += 1
    print(f"  FINAL: {to_list(dummy.next)}")

    # ----------------------------------------------------------------------
    # Edge case demo: trailing partial group must NOT be reversed.
    # ----------------------------------------------------------------------
    print("\n--- edge case: trailing group shorter than k is left untouched ---")
    demo = build_list([1, 2, 3, 4, 5, 6, 7, 8])
    result = to_list(sol.reverseKGroup(demo, 3))
    tail_untouched = result[-2:] == [7, 8]
    print(f"  [1..8], k=3 -> {result}")
    print(f"  trailing 2 nodes (7,8), fewer than k=3, kept in original order: {tail_untouched}")
    all_ok &= tail_untouched

    # ----------------------------------------------------------------------
    # Randomised cross-check across all three implementations.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check (iterative vs recursive vs collect+rebuild) ---")
    random.seed(25)
    trials, mismatches = 1000, 0
    for _ in range(trials):
        values = [random.randint(-20, 20) for _ in range(random.randint(0, 12))]
        k = random.randint(1, 6)
        r1 = to_list(sol.reverseKGroup(build_list(values), k))
        r2 = to_list(sol.reverseKGroup_recursive(build_list(values), k))
        r3 = to_list(sol.reverseKGroup_collect_rebuild(build_list(values), k))
        if not (r1 == r2 == r3):
            mismatches += 1
    print(f"  {trials} random (list, k) pairs: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # Benchmark: iterative O(1)-space vs recursive O(n/k)-stack, same work.
    # ----------------------------------------------------------------------
    print("\n--- iterative vs recursive: measured runtime (same O(n) time class) ---")
    print(f"  {'n':>10} {'k':>4} {'iterative':>12} {'recursive':>12}")
    random.seed(2)
    for n, k in ((2_000, 4), (2_000, 50), (4_000, 50)):
        values = [random.randint(-10**6, 10**6) for _ in range(n)]
        head = build_list(values)
        t0 = time.perf_counter(); sol.reverseKGroup(head, k)
        t1 = time.perf_counter()
        head = build_list(values)
        sol.reverseKGroup_recursive(head, k)
        t2 = time.perf_counter()
        iter_ms = (t1 - t0) * 1000
        rec_ms = (t2 - t1) * 1000
        print(f"  {n:>10} {k:>4} {iter_ms:>10.2f}ms {rec_ms:>10.2f}ms")
    print("  Both are O(n) time; the iterative version's real advantage is O(1)")
    print("  auxiliary space vs the recursive version's O(n/k) call-stack frames.")

    # ----------------------------------------------------------------------
    # Live demonstration: the recursive variant's O(n/k) stack depth is not
    # just a theoretical concern — it actually blows Python's default
    # recursion limit (1000) for a small k on a moderately long list,
    # while the iterative version handles the same input with no issue.
    # ----------------------------------------------------------------------
    print("\n--- stack-depth risk: recursive variant actually crashes at n=20000, k=4 ---")
    n, k = 20_000, 4
    values = list(range(n))
    iter_result = to_list(sol.reverseKGroup(build_list(values), k))
    print(f"  iterative:  n={n}, k={k} -> completed fine, {len(iter_result)} nodes, "
          f"O(n/k)={n // k} groups, O(1) stack frames used")
    try:
        sol.reverseKGroup_recursive(build_list(values), k)
        print("  recursive:  completed (unexpected on this Python's recursion limit)")
        recursion_crashed = False
    except RecursionError as e:
        print(f"  recursive:  n={n}, k={k} -> RecursionError: {e}")
        print(f"  n/k = {n // k} nested call frames needed, exceeding the default "
              f"recursion limit (sys.getrecursionlimit()={__import__('sys').getrecursionlimit()})")
        recursion_crashed = True
    print("  This is the real, measured cost of the recursive variant's O(n/k) space:")
    print("  not just 'more memory' in the abstract, it can crash outright on inputs")
    print("  the iterative O(1)-space version handles without any trouble.")
    all_ok &= recursion_crashed

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
