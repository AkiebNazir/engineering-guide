"""
================================================================================
SOLUTION · LeetCode 141 · Linked List Cycle                            [Easy]
https://leetcode.com/problems/linked-list-cycle/
================================================================================

THE CORE IDEA
--------------
Floyd's tortoise-and-hare: walk the list with two pointers at different
speeds, `slow` one step per iteration and `fast` two. If the list has NO
cycle, `fast` simply reaches `None` (or a node whose `.next` is `None`) and
the walk ends normally. If the list DOES have a cycle, once `slow` enters
it, `fast` is moving twice as fast around the SAME finite loop, so the gap
between them (measured forward, around the cycle) shrinks by exactly 1 every
step — `g, g-1, g-2, ..., 1, 0` — and cannot skip past 0 (topic guide §3.2).
`slow is fast` becoming true is therefore GUARANTEED inside a cycle, and
IMPOSSIBLE without one.

    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:      # IDENTITY, not value equality — see mistake #3
            return True
    return False

O(n) time, O(1) space — no visited-set needed.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive, don't code as the primary answer): walk the list with a
single pointer, remembering every visited node's IDENTITY in a `set()`
(`id(node)`, or the node objects themselves since ListNode has no custom
`__hash__`/`__eq__` and so hashes by identity already). The moment you're
about to visit a node already in the set, there's a cycle; reaching `None`
means there isn't. Correct, O(n) time, but O(n) SPACE — exactly what the
follow-up asks you to avoid. Priced and benchmarked below.

Approach 1 (Floyd's slow/fast) ✅ — the answer, shown above. O(n) time,
O(1) space.


================================================================================
⚠️  RUN LIVE — the unguarded-dereference panic, recovered
================================================================================
The loop condition is `while fast and fast.next:` — checked in THAT order,
every iteration, before `fast.next.next` is evaluated. Drop the guard (or
get the order wrong) and `fast.next.next` is evaluated on a node whose
`.next` is `None`, which raises `AttributeError: 'NoneType' object has no
attribute 'next'` IMMEDIATELY at that line — this is the Python analogue of
the Go guide's nil-pointer panic on `fast.Next.Next` (topic guide §1.2): no
silent wrong answer here, a loud, instant failure, because Python has no
Go-style "nil receiver that doesn't panic until dereferenced" subtlety —
every method/attribute access on `None` fails at the call site.

The demo below builds a real 4-node list with NO cycle, runs an UNGUARDED
version of the loop on it, catches the real `AttributeError` it raises,
prints the exact message, and then runs the correctly guarded version to
show it handles the same list without crashing.


================================================================================
STEP BY STEP TRACE
================================================================================
Cyclic list: 3 -> 2 -> 0 -> -4 -> (back to 2, i.e. tail.next = node at index 1)

    slow=3       fast=3
    slow=2       fast=0          (fast: 3->2->0, 2 steps)
    slow=0       fast=2          (fast: 0->-4->2, wrapped through the cycle)
    slow=-4      fast=-4         slow IS fast -> True

Non-cyclic list: 1 -> 2 -> None

    slow=1  fast=1
    slow=2  fast=None            (fast: 1->2->None, fast.next is None -> loop ends)
    loop condition `fast and fast.next` is now False (fast is None) -> return False


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                      Time    Space   Mutates input?  Note
    -----------------------------  ------  ------  ---------------  ----------------------
    Visited set of node identity   O(n)    O(n)    no               simple, extra memory
    Floyd's slow/fast ✅           O(n)    O(1)    no               the answer


================================================================================
EDGE CASES
================================================================================
    []                    -> False   head is None; loop body never runs.
    [1], no cycle          -> False   single node, fast.next is None immediately.
    [1], self-loop          -> True    tail.next points at itself; fast catches
                                     up to slow within one lap.
    [1,2], cycle at 0        -> True    smallest real cycle: two nodes, tail
                                     points back at the first.
    long list, cycle near end -> exercises many iterations before slow enters
                                     the cycle at all — still guaranteed to meet.


================================================================================
COMMON MISTAKES
================================================================================
1. Guarding only `fast` and not `fast.next` (or checking them in the wrong
   order) before computing `fast.next.next` — raises AttributeError on any
   list whose length has the wrong parity relative to where fast lands.
   Demonstrated live below.

2. Comparing `slow.val == fast.val` instead of `slow is fast` — two
   DIFFERENT nodes can legitimately hold equal values; only identity proves
   they're the same node in memory. See topic guide Part 8, mistake 3.

3. Starting `fast` one step ahead of `slow` "to save an iteration" — this
   still works for detection, but changes the exact meeting point used by
   the cycle-START algorithm (LC 142), so it's a correctness risk the moment
   you generalize past a plain yes/no answer. Start both at `head`.

4. Using a set of `node.val` instead of node identity for the O(n)-space
   alternative — two different nodes with the same value would falsely
   register as "already visited," reporting a cycle that doesn't exist.

5. Forgetting that a self-loop (`node.next = node`) IS a valid cycle input
   under the constraints, and not testing it — a naive walk-to-None check
   would infinite-loop on this without the slow/fast (or visited-set) safety
   net.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Not just whether there's a cycle — find the node where it BEGINS (LC 142).
A: After slow/fast first meet, restart one pointer at `head`, move both one
   step at a time; they meet again exactly at the cycle's entry node. See
   the Go topic guide §3.3 for the full distance-algebra proof (same math
   applies in Python).

Q: What's the length of the cycle?
A: Once slow/fast meet, keep one pointer fixed and walk the other around the
   cycle, counting steps until it returns to the fixed pointer's node.

Q: Could you detect this with a visited timestamp on each node instead of a
   set?
A: Only if you're allowed to mutate the nodes (e.g. add a `.visited` flag) —
   equivalent O(n) space cost to a set, and mutates input, which the
   set-based approach doesn't either. Floyd's is strictly better on both
   axes.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 142  Linked List Cycle II         — find the cycle's start node
    LC 202  Happy Number                  — the SAME algorithm on an implicit
                                          "linked list" formed by digit-square-sum
    LC 287  Find the Duplicate Number     — array-as-implicit-linked-list,
                                          Floyd's reused (problem 012 here)
================================================================================
"""

from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def hasCycle(self, head: Optional[ListNode]) -> bool:
        """Floyd's tortoise and hare. O(n) time, O(1) space.
        The answer. See THE CORE IDEA above."""
        slow = fast = head
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
            if slow is fast:
                return True
        return False

    def hasCycle_visited_set(self, head: Optional[ListNode]) -> bool:
        """Naive O(n) time, O(n) space: remember every visited node's
        identity. Priced above, not the answer under the O(1)-space follow-up."""
        seen = set()
        node = head
        while node:
            if id(node) in seen:
                return True
            seen.add(id(node))
            node = node.next
        return False

    # ------------------------------------------------------------------
    # Deliberate breakage — see the panic demo above.
    # ------------------------------------------------------------------
    def hasCycle_unguarded(self, head: Optional[ListNode]) -> bool:
        """✗ BROKEN ON PURPOSE — no `fast.next` guard before `fast.next.next`.
        Raises AttributeError the instant fast lands on a node whose .next
        is None, instead of ending the loop cleanly."""
        slow = fast = head
        while fast:                      # <-- missing `and fast.next`
            slow = slow.next
            fast = fast.next.next        # <-- AttributeError when fast.next is None
            if slow is fast:
                return True
        return False


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def build_cyclic_list(values, pos):
    if not values:
        return None
    nodes = [ListNode(v) for v in values]
    for i in range(len(nodes) - 1):
        nodes[i].next = nodes[i + 1]
    if pos != -1:
        nodes[-1].next = nodes[pos]
    return nodes[0]


# ==============================================================================
# TESTS — run:  python 003_linked_list_cycle_solution.py
# ==============================================================================
CASES = [
    ([3, 2, 0, -4], 1, True),
    ([1, 2], 0, True),
    ([1], -1, False),
    ([], -1, False),
    ([1], 0, True),
    ([1, 2, 3, 4], -1, False),
    ([1, 2, 3, 4, 5], 4, True),  # self-loop on tail
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: Floyd's slow/fast ---")
    for values, pos, want in CASES:
        got = sol.hasCycle(build_cyclic_list(values, pos))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  values={values!r:<20} pos={pos:<3} -> {got}  (want {want})")

    print("\n--- correctness: visited-set O(n)-space alternative, cross-checked ---")
    for values, pos, want in CASES:
        got = sol.hasCycle_visited_set(build_cyclic_list(values, pos))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  values={values!r:<20} pos={pos:<3} -> {got}  (want {want})")

    # ----------------------------------------------------------------------
    # ⚠️  Live panic demo: unguarded fast.next.next, RECOVERED.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: unguarded fast.next.next raises AttributeError (recovered) ---")
    no_cycle_list = build_cyclic_list([1, 2, 3, 4, 5], -1)  # odd length, no cycle:
    # fast lands exactly on the last node (non-None) with fast.next is None,
    # so the NEXT iteration's fast.next.next dereferences past the end.
    print(f"  input: 1 -> 2 -> 3 -> 4 -> 5 -> None  (no cycle, odd length)")
    panic_message = None
    try:
        sol.hasCycle_unguarded(no_cycle_list)
        print("  hasCycle_unguarded did NOT raise — unexpected")
    except AttributeError as e:
        panic_message = str(e)
        print(f"  hasCycle_unguarded RAISED (caught live): AttributeError: {panic_message}")

    correct_list = build_cyclic_list([1, 2, 3, 4, 5], -1)
    correct_result = sol.hasCycle(correct_list)
    print(f"  hasCycle (guarded)          -> {correct_result}   <- correct, no crash")

    panic_reproduced = panic_message is not None and "NoneType" in panic_message
    print(f"  unguarded version actually panicked as predicted: {panic_reproduced}")
    all_ok &= panic_reproduced   # we WANT to have proven the bug is real
    all_ok &= (correct_result is False)

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: 3 -> 2 -> 0 -> -4 -> (back to 2) ---")
    head = build_cyclic_list([3, 2, 0, -4], 1)
    slow = fast = head
    step = 0
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        print(f"  step {step}: slow={slow.val}  fast={fast.val if fast else None}  "
              f"same node? {slow is fast}")
        if slow is fast:
            break
        step += 1
    print(f"  cycle detected: {slow is fast}")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
