"""
================================================================================
SOLUTION · LeetCode 83 · Remove Duplicates from Sorted List             [Easy]
https://leetcode.com/problems/remove-duplicates-from-sorted-list/
================================================================================

THE CORE IDEA
--------------
Because the input is SORTED, duplicates of any value are always physically
ADJACENT — never scattered. So "remove duplicates" collapses from a general
membership problem into a one-pointer adjacent scan: compare `curr.val` with
`curr.next.val`; splice out a match; otherwise advance.

    curr = head
    while curr and curr.next:
        if curr.val == curr.next.val:
            curr.next = curr.next.next    # skip the duplicate; curr stays put
        else:
            curr = curr.next               # advance only past a KEPT node
    return head

No dummy head needed (contrast problem 005): the head node is never itself a
deletion candidate here, only its later duplicates are — `head` as a value is
always returned unchanged.


================================================================================
APPROACH 1 · Hashset of seen values (works on ANY list, priced not needed)
================================================================================
    seen = set()
    dummy = ListNode(next=head)
    curr = dummy
    while curr.next:
        if curr.next.val in seen:
            curr.next = curr.next.next
        else:
            seen.add(curr.next.val)
            curr = curr.next
    return dummy.next

Correct on unsorted input too (this is essentially LC 82's sibling problem
territory generalized). O(n) time, but O(n) EXTRA space for the set — the
sorted precondition specifically means we never need to remember anything
beyond "am I equal to the node right before me," so this generality is
wasted here. Priced, not coded as the primary answer.


================================================================================
APPROACH 2 · Adjacent-pointer scan ✅ (the answer — sorted input required)
================================================================================
As in THE CORE IDEA. O(n) time, O(1) space, one pointer, no dummy. This ONLY
works because the input is sorted — see the live demo below for what happens
if you apply it to an unsorted list anyway.


================================================================================
STEP BY STEP — head = [1, 1, 2, 3, 3]
================================================================================
    curr
    [1] -> 1 -> 2 -> 3 -> 3 -> None

    curr.val=1, curr.next.val=1  MATCH -> curr.next = curr.next.next
    curr
    [1] -> 2 -> 3 -> 3 -> None                (curr stays at the first 1)

    curr.val=1, curr.next.val=2  no match -> curr = curr.next
              curr
    1 -> [2] -> 3 -> 3 -> None

    curr.val=2, curr.next.val=3  no match -> curr = curr.next
                   curr
    1 -> 2 -> [3] -> 3 -> None

    curr.val=3, curr.next.val=3  MATCH -> curr.next = curr.next.next
                   curr
    1 -> 2 -> [3] -> None

    curr.next is None -> loop ends
    return head = 1 -> 2 -> 3 -> None    ✓


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time   Space   Mutates input?  Precondition
    ------------------------------ ------ ------  ---------------  ---------------
    Hashset of seen values          O(n)   O(n)    yes              none (any list)
    Adjacent-pointer scan ✅        O(n)   O(1)    yes              SORTED input
    Adjacent scan on unsorted data  O(n)   O(1)    yes              WRONG — misses
                                                                     non-adjacent dupes


================================================================================
EDGE CASES
================================================================================
    head = []              -> [].  `while curr and curr.next` is False
                                    immediately; nothing to do.
    single node              -> unchanged. `curr.next` is None from the start.
    all identical values      -> collapses to ONE node. [1,1,1,1] -> [1]; the
                                    "curr does not advance on a match" rule
                                    is what makes a run of any length collapse.
    no duplicates at all       -> unchanged; curr walks straight through.
    duplicates at the very END  -> [.., 3, 3] still collapses; the loop
                                    condition `curr.next` (not `curr.next.next`)
                                    correctly reaches the last pair.
    negative values             -> equality comparison doesn't care about
                                    sign; -3 == -3 works the same as 3 == 3.


================================================================================
COMMON MISTAKES
================================================================================
1. Applying this adjacent-scan directly to an UNSORTED list and expecting it
   to dedupe — it silently only catches duplicates that happen to already be
   next to each other, and leaves non-adjacent duplicates untouched. Live
   demo below on [1, 2, 1].
2. Advancing `curr` unconditionally even after a deletion — breaks a run of
   3+ identical values the same way problem 005's equivalent bug does; only
   the FIRST duplicate in the run gets removed.
3. Using `while curr.next:` without also checking `curr` first — fails
   immediately with an AttributeError on an empty list (`curr` is `None`,
   `None.next` raises). Guard both.
4. Reaching for a dummy head out of habit (problem 005's pattern) when it
   isn't needed here — harmless but adds an unnecessary allocation; the head
   is never a deletion target in THIS problem.
5. Confusing this with LC 82 (Remove Duplicates from Sorted List II), which
   removes ALL nodes that have ANY duplicate (including the first copy) —
   that variant genuinely needs a dummy head, because the original head
   itself might need deleting if it's part of a duplicate run.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if the list were NOT guaranteed sorted?
A: Either sort it first (O(n log n), and sorting a linked list in place is
   itself a nontrivial merge-sort exercise) or use the hashset approach
   (Approach 1), O(n) time / O(n) space, unconditionally correct regardless
   of order.

Q: LC 82 — remove nodes that have ANY duplicate entirely (not keep one copy).
A: Needs a dummy head (the original head might be part of a duplicate run
   that gets fully deleted) and a look-ahead: count how many consecutive
   nodes share a value, and if the count is more than 1, skip the WHOLE run
   instead of keeping one copy.

Q: Can you do this without mutating the input list?
A: Yes — build a brand new list, appending a node only when its value
   differs from the last value appended. O(n) time, O(n) space (new nodes),
   leaves the original list untouched. Trade-off: doubles memory for the
   list itself instead of just the O(1) rewiring this solution uses.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 82   Remove Duplicates from Sorted List II — deletes ALL copies of any
                                                      duplicated value; needs
                                                      a dummy head + look-ahead
    LC 26   Remove Duplicates from Sorted Array     — same adjacent-scan idea,
                                                      applied to an array with
                                                      an in-place write index
                                                      instead of pointer rewiring
    LC 203  Remove Linked List Elements              — deletes by VALUE match,
                                                      needs a dummy head
                                                      (problem 005 here)
================================================================================
"""

from typing import List, Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def deleteDuplicates(self, head: Optional[ListNode]) -> Optional[ListNode]:
        """Adjacent-pointer scan. O(n) time, O(1) space. Requires SORTED input.
        The answer."""
        curr = head
        while curr and curr.next:
            if curr.val == curr.next.val:
                curr.next = curr.next.next
            else:
                curr = curr.next
        return head

    # ------------------------------------------------------------------
    # Alternative: hashset, works on any order but costs O(n) space.
    # ------------------------------------------------------------------
    def deleteDuplicates_hashset(self, head: Optional[ListNode]) -> Optional[ListNode]:
        """Correct regardless of sort order. O(n) time, O(n) space."""
        seen = set()
        dummy = ListNode(next=head)
        curr = dummy
        while curr.next:
            if curr.next.val in seen:
                curr.next = curr.next.next
            else:
                seen.add(curr.next.val)
                curr = curr.next
        return dummy.next


# ==============================================================================
# TESTS — run:  python 006_remove_duplicates_from_sorted_list_solution.py
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
    ([1, 1, 2], [1, 2]),
    ([1, 1, 2, 3, 3], [1, 2, 3]),
    ([], []),
    ([1], [1]),
    ([1, 1, 1, 1], [1]),
    ([1, 2, 3], [1, 2, 3]),
    ([-3, -3, -1, 0, 0, 0, 5], [-3, -1, 0, 5]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: adjacent-scan answer vs hashset oracle (sorted input) ---")
    for values, expected in CASES:
        got = linked_to_list(sol.deleteDuplicates(list_to_linked(values)))
        got_hs = linked_to_list(sol.deleteDuplicates_hashset(list_to_linked(values)))
        ok = got == expected and got_hs == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  head={values!r:<28} -> {got}  (want {expected})")

    # ----------------------------------------------------------------------
    # ⚠️  Live bug: the precondition. Adjacent scan on UNSORTED data.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  adjacent scan on UNSORTED data: the precondition, demonstrated live ---")
    unsorted_cases = [
        [1, 2, 1],           # the classic: duplicate 1's are NOT adjacent
        [3, 1, 3, 2, 1],
        [5, 5, 1, 5],        # some duplicates adjacent, one is not
    ]
    print(f"  {'input':<18} {'adjacent-scan':>14} {'hashset (correct)':>18}  ok?")
    precondition_mismatch = False
    for values in unsorted_cases:
        scan_result = linked_to_list(sol.deleteDuplicates(list_to_linked(values)))
        hashset_result = linked_to_list(sol.deleteDuplicates_hashset(list_to_linked(values)))
        mismatch = scan_result != hashset_result
        precondition_mismatch |= mismatch
        print(f"  {str(values):<18} {str(scan_result):>14} {str(hashset_result):>18}  "
              f"{'yes' if not mismatch else 'NO  <- non-adjacent dupes survive'}")
    print(f"  unsorted-precondition violation reproduced: {precondition_mismatch}")
    all_ok &= precondition_mismatch  # we WANT to have proven the precondition matters

    print("\n  [1, 2, 1] traced through the adjacent-scan algorithm:")
    print("    curr=1, curr.next=2: no match  -> curr advances to 2")
    print("    curr=2, curr.next=1: no match  -> curr advances to 1 (the SECOND 1)")
    print("    curr.next is None              -> loop ends")
    print(f"    result: {linked_to_list(sol.deleteDuplicates(list_to_linked([1, 2, 1])))}"
          "   <- WRONG if the intent was 'dedupe regardless of position': both"
          " 1's survive because they were never ADJACENT to compare.")
    print("    This is not a bug in the algorithm — it is the algorithm correctly")
    print("    doing exactly what it promises (adjacent-only), on an input that")
    print("    violates the precondition it was built for.")

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: deleteDuplicates([1,1,2,3,3]) ---")
    curr = list_to_linked([1, 1, 2, 3, 3])
    step = 0
    while curr and curr.next:
        step += 1
        if curr.val == curr.next.val:
            print(f"  step {step}: curr.val={curr.val} == curr.next.val={curr.next.val}"
                  f" -> SKIP duplicate, curr stays")
            curr.next = curr.next.next
        else:
            print(f"  step {step}: curr.val={curr.val} != curr.next.val={curr.next.val}"
                  f" -> advance")
            curr = curr.next

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
