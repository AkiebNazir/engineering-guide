"""
================================================================================
SOLUTION · LeetCode 24 · Swap Nodes in Pairs                             [Medium]
https://leetcode.com/problems/swap-nodes-in-pairs/
================================================================================

THE CORE IDEA
--------------
Recurse on the rest of the list FIRST (everything after the current pair),
then wire the current pair around whatever the recursion returns. This is
the first "handle the rest, then stitch the front onto it" recursion in
the folder using real object references (`.next` pointers) instead of an
index or a number — the combine step is pointer rewiring, not arithmetic.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. RECURSIVE — swap the current pair around the recursively-swapped rest
   of the list. O(n) time, O(n/2) space (call stack, one frame per pair).
   The version taught here.
2. ITERATIVE with a dummy head — walk the list with a `prev` pointer that
   trails the pair being swapped, rewiring three `.next` links per pair.
   O(n) time, O(1) space. What to actually write in an interview.
3. VALUE-SWAP (violates the constraint) — swap `.val` fields instead of
   node pointers. O(n) time, O(1) space, but explicitly disallowed by the
   problem statement ("you must solve the problem without modifying the
   values") and included only to name why it's wrong.


================================================================================
STEP BY STEP TRACE — swapPairs([1,2,3,4])
================================================================================
    call swapPairs(1->2->3->4)
      first=1, second=2
      call swapPairs(3->4)          [recurse on rest, i.e. second.next]
        first=3, second=4
        call swapPairs(None)          [rest after this pair is empty]
          base case: head is None -> return None
        first(3).next = None   (recursive result)
        second(4).next = first(3)   -> 4->3->None
        return second = 4
      first(1).next = 4->3->None   (recursive result, wired here)
      second(2).next = first(1)   -> 2->1->4->3->None
      return second = 2

Final list: 2 -> 1 -> 4 -> 3 -> None. Each level only ever touches its OWN
pair's two `.next` pointers; everything deeper is already correctly wired
by the time this level's stitching runs — the leap-of-faith recursion
principle applied to pointers instead of numbers.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                Time   Space          Mutates input?  Note
    -----------------------  -----  -------------  ---------------  --------------------------------
    Recursive               O(n)   O(n/2) stack   yes (relinks)    one frame per pair
    Iterative (dummy head)   O(n)   O(1)           yes (relinks)    the interview answer
    Value-swap (disallowed) O(n)   O(1)           yes (values!)    violates the stated constraint


================================================================================
EDGE CASES
================================================================================
    head = None        -> None    empty list; base case fires immediately,
                                   zero pair-swaps.
    head = [1]          -> [1]     a single leftover node with no pair;
                                   the SECOND base case (`head.next is
                                   None`) must fire here, distinct from
                                   the empty-list case.
    head = [1,2,3]      -> [2,1,3] odd length: the last node has no
                                   partner and passes through unswapped —
                                   exercises the single-node base case
                                   one level DEEP in the recursion, not
                                   just at the top call.
    head = [1,2]         -> [2,1]  smallest case that actually performs
                                   one real swap.


================================================================================
COMMON MISTAKES
================================================================================
1. Recursing on `head.next.next` (i.e. `second.next`, correct) but then
   assigning `second.next = first.next` (the OLD, pre-recursion value)
   instead of `first.next = <recursive result>` first — the order matters
   because `first.next` must be updated to point at the correctly-swapped
   rest BEFORE `second.next` is set to `first`, otherwise the two
   assignments read/write the wrong intermediate state and either lose
   the rest of the list or create a 2-node cycle.
2. Forgetting the single-node base case (`head.next is None`) and only
   checking `head is None` — this crashes with an `AttributeError` on
   `head.next.next` for a list of odd length once recursion reaches the
   final unpaired node.
3. Swapping VALUES instead of relinking nodes — passes simple test cases
   (the output list "looks" right) but violates the explicit "do not
   modify Node.val" constraint, and fails if the grader inspects node
   identity rather than just printed values.
4. Losing track of which variable is "the new head to return" — returning
   `first` instead of `second` produces a list where the pair's ORDER
   in the returned structure doesn't match the swap (the values print
   correctly by coincidence in some cases but the head pointer returned
   to the caller is wrong).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you do this in O(1) space?
A: Yes — the iterative version with a dummy head node and a trailing
   `prev` pointer, rewiring three links per pair with no recursion.

Q: What if you had to swap every K nodes instead of every 2?
A: The same recursive shape generalizes (LC 25, Reverse Nodes in k-Group):
   reverse/rewire the current group of k, then recurse on the rest and
   wire the group's tail to the recursive result — the pattern here scales
   directly.

Q: Why is the recursive call made on `second.next`, and not on `first.next`
   or `head.next`?
A: `second.next` is the first node of the NEXT pair to be swapped — it is
   the exact boundary between "this pair" and "everything left to
   process," which is what a correct recursive call must operate on.


================================================================================
RELATED PROBLEMS
================================================================================
    Topic 28, 008 Reverse Linked List II — another linked-list recursion
                                           that rewires pointers around a
                                           recursive call on "the rest."
    LC 25   Reverse Nodes in k-Group      — the direct generalization to
                                           groups of size k.
    Topic 08 Linked List (topic-level)    — the full linked-list pointer-
                                           manipulation pattern family,
                                           mostly taught iteratively there.
================================================================================
"""

from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def swapPairs(self, head: Optional[ListNode]) -> Optional[ListNode]:
        """Recursive: swap the rest first, then wire this pair around it."""
        if head is None or head.next is None:
            return head
        first, second = head, head.next
        first.next = self.swapPairs(second.next)
        second.next = first
        return second

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def swapPairs_iterative(self, head: Optional[ListNode]) -> Optional[ListNode]:
        """Iterative, dummy head + trailing prev pointer. O(1) space."""
        dummy = ListNode(0, head)
        prev = dummy
        while prev.next and prev.next.next:
            first = prev.next
            second = first.next
            first.next = second.next
            second.next = first
            prev.next = second
            prev = first
        return dummy.next


# ==============================================================================
# TESTS — run:  python 007_swap_nodes_in_pairs_solution.py
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
    ([1, 2, 3, 4], [2, 1, 4, 3]),
    ([], []),
    ([1], [1]),
    ([1, 2], [2, 1]),
    ([1, 2, 3], [2, 1, 3]),
    ([1, 2, 3, 4, 5, 6], [2, 1, 4, 3, 6, 5]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    impls = [
        ("recursive          ", sol.swapPairs),
        ("iterative dummy head", sol.swapPairs_iterative),
    ]

    for name, fn in impls:
        ok = True
        for values, expected in CASES:
            head = build(values)
            got = to_list(fn(head))
            ok &= got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
