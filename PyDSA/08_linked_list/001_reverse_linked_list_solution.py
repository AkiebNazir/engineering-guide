"""
================================================================================
SOLUTION · LeetCode 206 · Reverse Linked List                          [Easy]
https://leetcode.com/problems/reverse-linked-list/
================================================================================

THE CORE IDEA
--------------
Reversal is a walk that rewires each node's `.next` to point BACKWARD instead
of forward, one node at a time. The entire difficulty is a bookkeeping
problem, not an algorithmic one: the instant you write `curr.next = prev`,
you have destroyed the only reference this program held to "the rest of the
original list" (`curr.next`'s old value). So the rest of the list must be
saved into a temporary BEFORE that line runs — see topic guide Part 1.3.

    prev = None
    curr = head
    while curr:
        nxt = curr.next     # 1. SAVE first
        curr.next = prev    # 2. REWIRE (destroys the original .next)
        prev = curr          # 3. ADVANCE prev
        curr = nxt             # 4. ADVANCE curr using the SAVED reference
    return prev

O(n) time, O(1) space — no recursion frame, no auxiliary structure.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive, don't code it): copy every value into a Python list,
reverse the list, then either mutate the original nodes' `.val` in place or
build a brand-new chain from the reversed values. Works, but O(n) extra
space for zero algorithmic benefit — the whole point of a linked list is
O(1) rewiring, and this approach throws that away. Never the answer.

Approach 1 (iterative, three-pointer) ✅ — the answer, shown above.
O(n) time, O(1) space, in place.

Approach 2 (recursive) — reverses everything after `head`, then splices
`head` onto the back of that reversed sub-list:

    def reverseList_recursive(head):
        if head is None or head.next is None:
            return head
        new_head = reverseList_recursive(head.next)
        head.next.next = head    # the node after head now points BACK at head
        head.next = None         # sever head's old forward link
        return new_head

Same O(n) time, but O(n) SPACE — one stack frame per node. CPython's default
recursion limit (~1000) makes this an actual failure on long lists, not just
a theoretical space regression; the demo below proves it live.


================================================================================
⚠️  THE #1 MISTAKE IN THIS TOPIC, RUN LIVE — losing the reference before
    saving it (topic guide Part 1.3)
================================================================================
    def reverse_broken(head):
        prev = None
        curr = head
        while curr:
            curr.next = prev      # <-- the rest of the list is gone: curr.next
                                   #     WAS our only reference to it, and this
                                   #     line just overwrote it.
            prev = curr
            curr = curr.next      # this reads prev's value (just assigned),
                                   #     NOT the real "next" node
        return prev

Because `curr.next` is written before it is read again, the walk degenerates:
`curr` becomes `prev`, and the loop exits after touching only the ORIGINAL
first node. This is not a crash — it is a silently truncated, wrong-looking-
right answer, which is worse than a crash because the code keeps running.
The tests below build a real 5-node list, run this broken version on a COPY
of it, and print exactly what comes out (spoiler: a 1-node list), then run
the correct version on an untouched copy and show the real answer.


================================================================================
STEP BY STEP TRACE
================================================================================
head = 1 -> 2 -> 3 -> None

Before:  None <- prev   curr
                          [1] -> [2] -> [3] -> None

step 1:  nxt = [2]
step 2:  [1].next = None      prev=None  curr=[1]
         None <- [1]                      [1].next is now None (severed)
step 3:  prev = [1]
step 4:  curr = [2]

Repeat:  None <- [1] <- [2]          [3] -> None
                          prev=[1] curr=[2]
         nxt=[3]; [2].next=[1]; prev=[2]; curr=[3]

Repeat:  None <- [1] <- [2] <- [3]         None
                                 prev=[3] curr=None (loop ends, nxt=None)

return prev = [3] -> [2] -> [1] -> None


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                  Time    Space   Mutates input?  Note
    -------------------------  ------  ------  ---------------  ----------------------
    Copy to list, rebuild      O(n)    O(n)    no               throws away the point
    Iterative (3-pointer) ✅   O(n)    O(1)    yes (rewires .next)  the answer
    Recursive                  O(n)    O(n)    yes              stack depth = list length


================================================================================
EDGE CASES
================================================================================
    []            -> []     head is None; loop body never runs, returns None.
    [1]           -> [1]    single node: nxt=None, curr.next=None (already was),
                             prev=[1], curr=None. Returns the same node, unchanged.
    [1,2]         -> [2,1]  smallest case that actually exercises the swap.
    long list      -> exercises the CPython recursion-limit gap between the
                     iterative and recursive approaches; demoed below.


================================================================================
COMMON MISTAKES
================================================================================
1. Overwriting `curr.next` BEFORE saving it (`nxt = curr.next` must be the
   FIRST line of the loop body) — the single most common bug in this entire
   topic. Demonstrated live below: it does not crash, it silently truncates.

2. Returning `head` instead of `prev` — `head` still refers to the OLD first
   node, which after reversal is the new TAIL (or, on an empty list, `None`
   either way, which can mask the bug on that one input).

3. Forgetting to sever `head.next` in the recursive version
   (`head.next = None`) — leaves a stray forward pointer that turns the
   result into a cycle, and also keeps the old suffix reachable via a link
   nothing else in the algorithm expects (see the Go guide's "leak via
   reachability" framing, Part 1.2 — the Python analogue is a needless
   surviving reference, not a memory leak, but the same category of bug).

4. Choosing recursion by default for long lists without naming the ~1000-
   frame CPython recursion-limit ceiling out loud — correct on small inputs,
   `RecursionError` on large ones.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Implement it recursively too.
A: See Approach 2 above; note the O(n) space trade-off and the CPython
   recursion-limit ceiling explicitly — don't present it as a free variant.

Q: Reverse only nodes between positions `left` and `right` (LC 92).
A: Walk to the node before `left`, then run this exact three-pointer loop for
   `right - left + 1` iterations starting there, and splice the reversed
   sub-list back in using a dummy head so `left == 1` isn't a special case.

Q: Reverse in groups of k (LC 25, problem 015 in this folder).
A: Run this exact loop on bounded windows of length k, repeatedly, with
   bookkeeping to reconnect each reversed group to its neighbors — see topic
   guide Part 4.3.

Q: Can you reverse without breaking any existing references other code might
   hold to the original nodes?
A: No — reversal by definition rewrites `.next` on every node in place. If
   external code holds a reference to a node, it will observe the new
   `.next` (this is exactly the "one node, many references" model from the
   topic guide Part 1.1). Building a brand-new list of new nodes is the only
   way to avoid this, at O(n) extra space.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 92   Reverse Linked List II       — reverse a bounded sub-range
    LC 25   Reverse Nodes in k-Group      — this loop applied repeatedly (015)
    LC 143  Reorder List                  — this + find-middle + merge (008)
    LC 234  Palindrome Linked List        — this + find-middle + compare (007)
================================================================================
"""

import sys
from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def reverseList(self, head: Optional[ListNode]) -> Optional[ListNode]:
        """Iterative three-pointer reversal. O(n) time, O(1) space.
        The answer. See THE CORE IDEA above."""
        prev = None
        curr = head
        while curr:
            nxt = curr.next       # 1. SAVE first
            curr.next = prev      # 2. REWIRE
            prev = curr            # 3. ADVANCE prev
            curr = nxt               # 4. ADVANCE curr
        return prev

    def reverseList_recursive(self, head: Optional[ListNode]) -> Optional[ListNode]:
        """Recursive reversal. O(n) time, O(n) space (call stack). Correct,
        but CPython's default recursion limit (~1000) makes this an actual
        failure on long lists, not just theoretically worse. See the demo."""
        if head is None or head.next is None:
            return head
        new_head = self.reverseList_recursive(head.next)
        head.next.next = head   # the node after head now points BACK at head
        head.next = None        # sever head's old forward link
        return new_head

    # ------------------------------------------------------------------
    # Deliberate breakage — see the "#1 mistake" section above.
    # ------------------------------------------------------------------
    def reverse_broken(self, head: Optional[ListNode]) -> Optional[ListNode]:
        """✗ BROKEN ON PURPOSE — overwrites curr.next before saving it.
        Silently truncates the list instead of crashing."""
        prev = None
        curr = head
        while curr:
            curr.next = prev      # <-- destroys our only reference onward
            prev = curr
            curr = curr.next      # <-- reads the value JUST written above
        return prev


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
    seen = set()
    while head and id(head) not in seen:   # guard against an accidental cycle
        seen.add(id(head))
        out.append(head.val)
        head = head.next
    return out


# ==============================================================================
# TESTS — run:  python 001_reverse_linked_list_solution.py
# ==============================================================================
CASES = [
    [1, 2, 3, 4, 5],
    [1, 2],
    [],
    [1],
    [1, 2, 3],
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: iterative reversal ---")
    for values in CASES:
        want = list(reversed(values))
        got = to_list(sol.reverseList(build_list(values)))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {values!r:<20} -> {got}  (want {want})")

    print("\n--- correctness: recursive reversal, cross-checked against iterative ---")
    for values in CASES:
        want = to_list(sol.reverseList(build_list(values)))
        got = to_list(sol.reverseList_recursive(build_list(values)))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {values!r:<20} -> {got}  (want {want})")

    # ----------------------------------------------------------------------
    # ⚠️  The #1 mistake, demonstrated LIVE on a real list.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: the #1 mistake — overwrite-before-save (topic guide Part 1.3) ---")
    original = [1, 2, 3, 4, 5]
    broken_head = build_list(original)      # a fresh, independent copy
    broken_result = to_list(sol.reverse_broken(broken_head))
    print(f"  input:            {original}")
    print(f"  reverse_broken -> {broken_result}   <- WRONG: truncated, not a real reversal")

    correct_head = build_list(original)     # a second, untouched copy
    correct_result = to_list(sol.reverseList(correct_head))
    print(f"  reverseList    -> {correct_result}   <- correct")

    truncated = broken_result != list(reversed(original)) and len(broken_result) < len(original)
    print(f"  broken version actually truncated the list: {truncated}")
    all_ok &= truncated   # we WANT to have proven the bug is real

    # ----------------------------------------------------------------------
    # Step-by-step trace, small list.
    # ----------------------------------------------------------------------
    print("\n--- trace: head = 1 -> 2 -> 3 -> None ---")
    prev, curr = None, build_list([1, 2, 3])
    step = 0
    while curr:
        nxt = curr.next
        print(f"  step {step}: nxt={nxt.val if nxt else None}  "
              f"before-rewire curr={curr.val}  prev={prev.val if prev else None}")
        curr.next = prev
        prev = curr
        curr = nxt
        step += 1
    print(f"  final: {to_list(prev)}")

    # ----------------------------------------------------------------------
    # Recursion depth: CPython's limit is a REAL ceiling, not just "worse".
    # ----------------------------------------------------------------------
    print("\n--- iterative vs recursive: CPython recursion limit is a real ceiling ---")
    limit = sys.getrecursionlimit()
    print(f"  sys.getrecursionlimit() = {limit}")
    long_n = limit + 500          # comfortably past the ceiling
    long_values = list(range(long_n))

    iterative_ok = True
    try:
        result = to_list(sol.reverseList(build_list(long_values)))
        iterative_ok = result == list(reversed(long_values))
        print(f"  iterative on n={long_n}: succeeded, correct={iterative_ok}")
    except RecursionError as e:
        iterative_ok = False
        print(f"  iterative on n={long_n}: unexpectedly raised {e!r}")

    recursion_error_raised = False
    try:
        sol.reverseList_recursive(build_list(long_values))
        print(f"  recursive on n={long_n}: did NOT raise (limit not hit this run)")
    except RecursionError as e:
        recursion_error_raised = True
        print(f"  recursive on n={long_n}: raised RecursionError as expected -> {e!r}")

    print(f"  iterative succeeded where recursive failed: "
          f"{iterative_ok and recursion_error_raised}")
    all_ok &= iterative_ok
    all_ok &= recursion_error_raised

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
