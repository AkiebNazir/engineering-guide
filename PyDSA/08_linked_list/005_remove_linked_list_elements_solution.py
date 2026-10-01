"""
================================================================================
SOLUTION · LeetCode 203 · Remove Linked List Elements                   [Easy]
https://leetcode.com/problems/remove-linked-list-elements/
================================================================================

THE CORE IDEA
--------------
Deleting a node whose `.val == val` is normally a one-line rewire:

    curr.next = curr.next.next

The catch is the HEAD: if the head itself matches, there is no "node before
it" to hold `curr`, so `curr.next = curr.next.next` cannot express "delete
the head" — you'd need to reassign `head` directly, which is a different
code path from every other deletion. A dummy node standing one slot before
the real head erases that difference: `dummy.next` IS the head, so "delete
the head" and "delete the middle node" become the exact same rewire. See the
topic guide's Part 2 for the general pattern.

    dummy = ListNode(next=head)
    curr = dummy
    while curr.next:
        if curr.next.val == val:
            curr.next = curr.next.next   # skip it; curr does NOT move
        else:
            curr = curr.next             # only advance past a KEPT node
    return dummy.next


================================================================================
APPROACH 1 · Without a dummy — special-case the head (priced, then shown broken)
================================================================================
The "obvious" approach without a dummy strips matches off the front in a
separate loop, then walks the rest:

    def remove_naive(head, val):
        while head and head.val == val:   # strip the front
            head = head.next
        if not head:
            return None
        curr = head
        while curr.next:
            if curr.next.val == val:
                curr.next = curr.next.next
            else:
                curr = curr.next
        return head

This is O(n) time / O(1) space too, and it is CORRECT if written carefully —
but "carefully" is exactly the trap: it is very easy to forget the `while`
(writing `if head and head.val == val: head = head.next` instead) and only
strip ONE matching node off the front instead of a whole run of them. The
live demo below builds exactly that broken variant and runs it on
`[6,6,6,1]` to show the wrong output land on the terminal, not just in prose.


================================================================================
APPROACH 2 · Dummy head ✅ (the answer)
================================================================================
As in THE CORE IDEA. O(n) time, O(1) extra space, one code path for every
position including the head. This is the version to write from memory.


================================================================================
STEP BY STEP — nums = [1, 2, 6, 3, 4, 5, 6], val = 6
================================================================================
    dummy -> 1 -> 2 -> 6 -> 3 -> 4 -> 5 -> 6 -> None
     ^curr

    curr.next=1, no match  -> curr = 1
    dummy -> [1] -> 2 -> 6 -> 3 -> 4 -> 5 -> 6 -> None
              ^curr

    curr.next=2, no match  -> curr = 2
    dummy -> 1 -> [2] -> 6 -> 3 -> 4 -> 5 -> 6 -> None
                   ^curr

    curr.next=6, MATCH     -> curr.next = curr.next.next (skip the 6)
    dummy -> 1 -> [2] -> 3 -> 4 -> 5 -> 6 -> None      (curr stays at 2!)
                   ^curr

    curr.next=3, no match  -> curr = 3
    curr.next=4, no match  -> curr = 4
    curr.next=5, no match  -> curr = 5
    curr.next=6, MATCH     -> curr.next = curr.next.next (skip the trailing 6)
    dummy -> 1 -> 2 -> 3 -> 4 -> [5] -> None
                                  ^curr

    curr.next is None -> loop ends
    return dummy.next = 1 -> 2 -> 3 -> 4 -> 5 -> None    ✓


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time   Space   Mutates input?  Note
    --------------------------  -----  ------  ---------------  ----------------
    Without dummy (careful)     O(n)   O(1)    yes              two code paths
    Without dummy (naive/buggy) O(n)   O(1)    yes              WRONG on head runs
    Dummy head ✅               O(n)   O(1)    yes              one code path
    Build a new list (copy)     O(n)   O(n)    no               never needed here


================================================================================
EDGE CASES
================================================================================
    head = []            -> [].   `while curr.next` never runs; dummy.next
                                   stays None. No special check needed.
    every node matches    -> [].   [7,7,7,7] must collapse to nothing — the
                                   "curr does not advance on a match" rule is
                                   what makes a whole run collapse in one pass.
    val matches nothing    -> unchanged. Every node is kept, curr walks to
                                   the real tail, dummy.next is still the
                                   original head object.
    single node, matches    -> [].
    single node, no match    -> unchanged, [x].
    matches ONLY at the head  -> the case that breaks a careless non-dummy
                                   version; demonstrated live below.


================================================================================
COMMON MISTAKES
================================================================================
1. Advancing `curr` unconditionally, even after a deletion. `curr.next` after
   a deletion is a NEW node that itself might match — advancing past it
   unchecked skips validating it and leaves a stray match in the output on
   runs of 2+ consecutive matches.
2. Without a dummy: stripping only ONE matching node off the front instead of
   a `while` loop, so a run of matches at the head ([6,6,6,1], val=6) leaves
   matching nodes behind. Demonstrated live below.
3. Overwriting `curr.next` before anything downstream still needs the old
   value — not an issue in this specific rewire (`curr.next.next` is read
   before the assignment completes), but the general topic-wide reflex
   (guide Part 1.3: save before you destroy) is worth restating here.
4. Returning `dummy` instead of `dummy.next` — the dummy is a plumbing node,
   never part of the real answer.
5. Comparing `val` incorrectly if it's off the typical [1,50] constraint
   range in a variant of this problem (e.g. `val` could need `None`/`null`
   handling in other languages) — not an issue in Python/this exact problem,
   but worth naming why the constraint bounds matter.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Could you do this recursively?
A: Yes — `head.next = removeElements(head.next, val)` then decide whether to
   keep or skip `head`, but that costs O(n) call-stack frames (topic guide
   Part 4.1) and CPython's default recursion limit makes it fail outright on
   very long lists. Default to iterative.

Q: What if you needed to remove nodes matching ANY of several values, not
   just one?
A: Same dummy-head skeleton; swap `curr.next.val == val` for
   `curr.next.val in val_set` (a set, for O(1) membership instead of O(k)
   per node).

Q: Can this be done without a dummy node at all, cleanly?
A: Yes, with the two-loop "strip the front, then walk the rest" version
   (Approach 1) — but it is strictly more code and more branches to get
   right, for the same asymptotic cost. The dummy costs one allocation and
   removes an entire category of off-by-one bugs.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 19   Remove Nth From End      — different pointer pattern (fixed-gap
                                        two pointers, §3.3), same dummy-head
                                        motivation (problem 009 in this folder)
    LC 83   Remove Duplicates        — adjacent-scan deletion, sorted input
            from Sorted List          only (problem 006 here)
    LC 21   Merge Two Sorted Lists   — dummy head for building a NEW list
                                        instead of deleting from an existing
                                        one
================================================================================
"""

from typing import List, Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def removeElements(self, head: Optional[ListNode], val: int) -> Optional[ListNode]:
        """Dummy head. O(n) time, O(1) space. The answer."""
        dummy = ListNode(next=head)
        curr = dummy
        while curr.next:
            if curr.next.val == val:
                curr.next = curr.next.next
            else:
                curr = curr.next
        return dummy.next

    # ------------------------------------------------------------------
    # Alternative: careful, correct version WITHOUT a dummy node.
    # ------------------------------------------------------------------
    def removeElements_no_dummy_careful(
        self, head: Optional[ListNode], val: int
    ) -> Optional[ListNode]:
        """Strips matches off the front with a while loop first (correctly
        handling a RUN of matching heads), then walks the rest. Correct, but
        two code paths instead of one."""
        while head and head.val == val:
            head = head.next
        if not head:
            return None
        curr = head
        while curr.next:
            if curr.next.val == val:
                curr.next = curr.next.next
            else:
                curr = curr.next
        return head

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def removeElements_naive_broken(
        self, head: Optional[ListNode], val: int
    ) -> Optional[ListNode]:
        """✗ BROKEN ON PURPOSE — strips only ONE matching node off the front
        (an `if`, not a `while`), so a RUN of matching values at the head is
        not fully removed. Everything after the front is handled correctly,
        which is exactly what makes this bug sneaky: it passes any test that
        doesn't have 2+ consecutive matches starting at index 0."""
        if head and head.val == val:      # only strips ONE, not a run
            head = head.next
        if not head:
            return None
        curr = head
        while curr.next:
            if curr.next.val == val:
                curr.next = curr.next.next
            else:
                curr = curr.next
        return head


# ==============================================================================
# TESTS — run:  python 005_remove_linked_list_elements_solution.py
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
    ([1, 2, 6, 3, 4, 5, 6], 6, [1, 2, 3, 4, 5]),
    ([], 1, []),
    ([7, 7, 7, 7], 7, []),
    ([1, 1, 1, 2], 1, [2]),
    ([2, 1, 1, 1], 1, [2]),
    ([1], 1, []),
    ([1], 2, [1]),
    ([1, 2, 3], 4, [1, 2, 3]),
    ([6, 6, 6, 1], 6, [1]),          # a RUN of matches at the very head
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: dummy-head answer vs careful no-dummy variant ---")
    for values, val, expected in CASES:
        got = linked_to_list(sol.removeElements(list_to_linked(values), val))
        got2 = linked_to_list(
            sol.removeElements_no_dummy_careful(list_to_linked(values), val)
        )
        ok = got == expected and got2 == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  head={values!r:<20} val={val:<3} -> {got}  "
              f"(want {expected})")

    # ----------------------------------------------------------------------
    # ⚠️  Live bug: naive "if, not while" front-strip on a run of head matches.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  naive (if, not while) front-strip vs dummy-head: live bug ---")
    bug_cases = [
        ([6, 6, 6, 1], 6),   # THREE matching nodes at the head, in a row
        ([9, 9, 2, 9], 9),   # two matching at the head, one matching later
        ([5], 5),            # single matching node — still a "run of 1" at the head
    ]
    print(f"  {'input':<16} {'val':>4} {'dummy-head':>12} {'naive (buggy)':>14}  ok?")
    bug_reproduced = False
    for values, val in bug_cases:
        correct = linked_to_list(sol.removeElements(list_to_linked(values), val))
        broken = linked_to_list(sol.removeElements_naive_broken(list_to_linked(values), val))
        mismatch = correct != broken
        bug_reproduced |= mismatch
        print(f"  {str(values):<16} {val:>4} {str(correct):>12} {str(broken):>14}  "
              f"{'yes' if not mismatch else 'NO  <- naive leaves matches behind'}")
    print(f"  naive front-strip bug reproduced on a multi-match run: {bug_reproduced}")
    all_ok &= bug_reproduced  # we WANT to have proven the bug is real

    print("\n  [6,6,6,1], val=6 traced through the naive (if, not while) version:")
    print("    dummy-free naive strips ONLY the first 6 off the front, then walks")
    print("    the rest starting from the SECOND 6 (now treated as 'head') without")
    print("    re-checking it against val — the remaining two 6's are never")
    print("    revisited as head candidates, only as `curr.next` targets, so the")
    print("    result keeps a 6 that should have been removed.")
    naive_head = sol.removeElements_naive_broken(list_to_linked([6, 6, 6, 1]), 6)
    print(f"    naive result:      {linked_to_list(naive_head)}   <- WRONG, want [1]")
    dummy_head = sol.removeElements(list_to_linked([6, 6, 6, 1]), 6)
    print(f"    dummy-head result: {linked_to_list(dummy_head)}   <- correct")

    # ----------------------------------------------------------------------
    # Step-by-step trace, dummy-head version.
    # ----------------------------------------------------------------------
    print("\n--- trace: dummy-head removeElements([1,2,6,3,4,5,6], val=6) ---")
    head = list_to_linked([1, 2, 6, 3, 4, 5, 6])
    dummy = ListNode(next=head)
    curr = dummy
    step = 0
    while curr.next:
        step += 1
        action = "SKIP (match)" if curr.next.val == 6 else "advance"
        before = curr.val if curr is not dummy else "dummy"
        target = curr.next.val
        if curr.next.val == 6:
            curr.next = curr.next.next
        else:
            curr = curr.next
        print(f"  step {step}: curr={before!r:<8} looked at {target} -> {action}")
    print(f"  result: {linked_to_list(dummy.next)}")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
