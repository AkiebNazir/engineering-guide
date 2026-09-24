"""
================================================================================
SOLUTION · LeetCode 148 · Sort List                                   [Medium]
https://leetcode.com/problems/sort-list/
================================================================================

THE CORE IDEA
--------------
Merge sort is the RIGHT sort for a linked list in a way it isn't
necessarily for an array: the merge step (LC 21's `mergeTwoLists`, topic
08 problem 002) splices existing nodes together via `.next` rewrites, no
new node allocation and no O(n) auxiliary array required for the merge
itself. The only thing a linked list can't do that an array can is O(1)
random access to the midpoint -- so splitting requires a fast/slow pointer
walk (topic 08's cycle-detection technique, repurposed) to physically find
and cut the list in half before recursing.

    def sortList(head):
        if not head or not head.next:
            return head
        # find the midpoint and CUT the list into two halves
        prev, slow, fast = None, head, head
        while fast and fast.next:
            prev = slow
            slow = slow.next
            fast = fast.next.next
        prev.next = None                # severs left half from right half
        left = sortList(head)
        right = sortList(slow)
        return merge(left, right)       # LC 21's merge, verbatim

`prev` trails one step behind `slow` specifically so that `prev.next =
None` can cut the link -- `slow` itself becomes the head of the right
half, and the left half is already correctly terminated at `prev`.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive, don't code it): walk the list, collect every `.val`
into a Python list, sort THAT list (or reuse problem 002's merge sort on
it), then walk the list again overwriting each node's `.val` in order.
Correct, O(n log n) time, but O(n) EXTRA space for the value array on top
of the list's own nodes, and it doesn't actually rearrange nodes (which
some variants of this problem, or a stricter interviewer, may object to)
-- it mutates VALUES in place rather than sorting the structure itself.

Approach 1 (chosen) -- top-down recursive merge sort: split via fast/slow
pointer, recurse on both halves, merge with LC 21's two-pointer splice.
O(n log n) time. Space is O(log n) for the RECURSION STACK only (no
auxiliary array) -- genuinely less extra memory than array merge sort's
O(n) merge buffers, because splicing existing nodes needs no new storage.
The answer for a first pass; shown above and coded below.

Approach 2 -- bottom-up iterative merge sort: instead of recursing down to
single nodes, iterate the merge WIDTH itself (1, 2, 4, 8, ... nodes per
run), repeatedly splitting the list into `width`-sized chunks and merging
adjacent pairs, doubling `width` each outer pass until it exceeds the list
length. O(n log n) time, and now genuinely O(1) EXTRA space (no recursion
stack at all -- the follow-up's exact ask). More intricate to get right
(manual chunk-splitting via a counted walk) but it's the real answer when
"O(1) memory, not counting the call stack" is taken literally. Coded below
as the follow-up variant.


================================================================================
STEP BY STEP TRACE
================================================================================
head = 4 -> 2 -> 1 -> 3 -> None

split (fast/slow, prev trails slow):
    prev=None slow=4 fast=4
    iter1: fast(4)&fast.next(2) exist -> prev=4, slow=2, fast=1
    iter2: fast(1)&fast.next(3) exist -> prev=2, slow=1, fast=None (3.next)
    fast is None -> stop
    prev(2).next = None  -> left = 4 -> 2 -> None      right = 1 -> 3 -> None

recurse left (4->2):
    split: prev=4, slow=2, fast=None immediately (2 elements) -> left=[4] right=[2]
    merge([4],[2]) -> 2 vs 4: take 2, then take 4 -> [2,4]

recurse right (1->3):
    split -> left=[1] right=[3]
    merge([1],[3]) -> 1 vs 3: take 1, then take 3 -> [1,3]

merge([2,4], [1,3]):
    2 vs 1 -> take 1          result=[1]
    2 vs 3 -> take 2          result=[1,2]
    4 vs 3 -> take 3          result=[1,2,3]
    right exhausted -> append left remainder [4]   result=[1,2,3,4]

final: 1 -> 2 -> 3 -> 4 -> None  ✓


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                         Time         Space           Mutates input?
    -----------------------------------------------------------------------------
    Collect values + sort + rewrite  O(n log n)   O(n) array       yes (values only)
    Top-down recursive merge sort ✅ O(n log n)   O(log n) stack   yes (splices nodes)
    Bottom-up iterative merge sort   O(n log n)   O(1)             yes (splices nodes)


================================================================================
EDGE CASES
================================================================================
    head is None (empty list)  -> `if not head or not head.next: return head`
                                  returns None immediately, no work done.
    single node                 -> same guard, returns the single node as-is;
                                  a size-1 list is trivially sorted.
    two nodes, already sorted    -> split still runs a full cut+merge cycle
                                  (no short-circuit for "already sorted"),
                                  correct but not adaptive like Timsort.
    all values equal              -> merge's `<=` tie-break always prefers
                                  the left half on ties, which happens to
                                  make this merge sort STABLE (equal values
                                  keep their original relative order) --
                                  worth naming even though the problem
                                  doesn't require stability.
    negative values                -> no special handling needed; comparison
                                  is generic `<=` on `.val`, sign-agnostic.
    odd-length list                -> fast/slow split gives the LEFT half
                                  one fewer node than the right half (e.g.
                                  n=5 splits into 2 and 3) -- verify this
                                  doesn't off-by-one the recursion base case.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting to CUT the list at the midpoint (`prev.next = None`) before
   recursing -- both recursive calls would then walk the SAME unbroken
   list, causing infinite/duplicated traversal or, worse, both halves
   silently sharing tail nodes and corrupting the final splice.
2. Splitting with `fast = fast.next` (single-step) instead of
   `fast = fast.next.next` (double-step) -- finds the wrong midpoint
   entirely, degrading the split from roughly balanced halves toward a
   1-and-(n-1) split, which turns O(n log n) into O(n^2).
3. Using `slow` itself (instead of a trailing `prev`) to perform the cut --
   cuts the WRONG link, since `slow` ends up in the middle of what should
   be the right half by the time the loop exits; you need the node ONE
   STEP BEFORE `slow` to sever cleanly.
4. In the bottom-up variant, forgetting to walk `curr` to the end of the
   just-merged run before setting `prev = curr` for the next pair -- silently
   truncates the list or double-links a node into two places.
5. Reusing LC 21's merge but forgetting the final
   `tail.next = list1 if list1 else list2` splice for the exhausted-list
   remainder -- same truncation bug as that problem, inherited here.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Can you sort the linked list in O(n log n) time and O(1) memory (not
  counting recursion)?" -> Yes -- bottom-up iterative merge sort, coded
  below. It replaces the recursive divide with an explicit outer loop over
  merge WIDTH (1, 2, 4, 8, ...), eliminating the call stack entirely.
- "Why not quicksort a linked list?" -> Quicksort's partition step relies
  on O(1) random access to swap distant elements; on a linked list,
  finding "the element at index i" is O(i), so partitioning degrades
  quicksort's practical performance badly, and in-place swapping is
  awkward with pointers instead of array slots. Merge sort's sequential
  splice-based merge fits the linked-list access pattern far better.
- "What if this were a doubly linked list?" -> No change to the split or
  merge logic (both only ever follow `.next`); you'd additionally need to
  keep `.prev` pointers consistent during the splice if anything downstream
  relies on backward traversal.
- "Insertion sort instead?" -> O(n^2) worst case, O(1) space, stable, and
  simple -- reasonable ONLY if you know the list is nearly sorted already
  or n is guaranteed small; not a general answer here given LeetCode's
  constraint of up to 5*10^4 nodes.


================================================================================
RELATED PROBLEMS
================================================================================
- Merge Two Sorted Lists (LC 21, topic 08, 002) -- the merge step reused
  verbatim here.
- Sort an Array (LC 912, this topic, 002) -- the same merge sort algorithm,
  array version; splitting is O(1) index arithmetic there instead of a
  fast/slow pointer walk, since arrays support random access.
- Middle of the Linked List (LC 876, topic 08, 004) -- the exact fast/slow
  pointer technique used here to find the split point, isolated as its own
  problem.
- Merge k Sorted Lists (LC 23, topic 08, 014) -- generalizes the pairwise
  merge here to k lists at once via a heap or pairwise merging.
- Insertion Sort List (LC 147) -- the O(n^2)/O(1)-space alternative named
  in the follow-ups above, not present in this curriculum but worth
  knowing the trade-off.
================================================================================
"""

import random
import time
from typing import List, Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def sortList(self, head: Optional[ListNode]) -> Optional[ListNode]:
        """Top-down recursive merge sort. O(n log n) time, O(log n) extra
        space (recursion stack only, no auxiliary array). The first-pass
        answer. See THE CORE IDEA above."""
        if not head or not head.next:
            return head

        prev, slow, fast = None, head, head
        while fast and fast.next:
            prev = slow
            slow = slow.next
            fast = fast.next.next
        prev.next = None  # cut: left half ends at prev, right half starts at slow

        left = self.sortList(head)
        right = self.sortList(slow)
        return self._merge(left, right)

    @staticmethod
    def _merge(l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        dummy = ListNode()
        tail = dummy
        while l1 and l2:
            if l1.val <= l2.val:
                tail.next = l1
                l1 = l1.next
            else:
                tail.next = l2
                l2 = l2.next
            tail = tail.next
        tail.next = l1 if l1 else l2
        return dummy.next

    # ------------------------------------------------------------------
    # Follow-up variant: bottom-up iterative merge sort. O(n log n) time,
    # TRUE O(1) extra space -- no recursion stack at all.
    # ------------------------------------------------------------------
    def sortList_bottom_up(self, head: Optional[ListNode]) -> Optional[ListNode]:
        if not head or not head.next:
            return head

        length = 0
        node = head
        while node:
            length += 1
            node = node.next

        dummy = ListNode(0, head)
        width = 1
        while width < length:
            prev = dummy
            curr = dummy.next
            while curr:
                left_chunk = curr
                right_chunk = self._split(left_chunk, width)
                curr = self._split(right_chunk, width)
                prev = self._merge_and_reattach(left_chunk, right_chunk, prev)
            width *= 2
        return dummy.next

    @staticmethod
    def _split(head: Optional[ListNode], n: int) -> Optional[ListNode]:
        """Advance n-1 steps from head, cut the link, and return the node
        just after the cut (the start of the next chunk, or None)."""
        for _ in range(n - 1):
            if not head:
                return None
            head = head.next
        if not head:
            return None
        rest = head.next
        head.next = None
        return rest

    @staticmethod
    def _merge_and_reattach(
        l1: Optional[ListNode], l2: Optional[ListNode], prev: ListNode
    ) -> ListNode:
        """Merge two chunks and splice the result in after `prev`. Returns
        the new tail (the node `prev` should become for the next pair)."""
        curr = prev
        while l1 and l2:
            if l1.val <= l2.val:
                curr.next = l1
                l1 = l1.next
            else:
                curr.next = l2
                l2 = l2.next
            curr = curr.next
        curr.next = l1 if l1 else l2
        while curr.next:
            curr = curr.next
        return curr

    # ------------------------------------------------------------------
    # Naive baseline -- priced, not the answer.
    # ------------------------------------------------------------------
    def sortList_collect_and_overwrite(
        self, head: Optional[ListNode]
    ) -> Optional[ListNode]:
        """✗ NAIVE -- collect values, sort, overwrite in place. O(n log n)
        time but O(n) extra space for the values list, and doesn't
        rearrange the actual node structure."""
        values = []
        node = head
        while node:
            values.append(node.val)
            node = node.next
        values.sort()
        node = head
        for v in values:
            node.val = v
            node = node.next
        return head


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def build_list(values: List[int]) -> Optional[ListNode]:
    dummy = ListNode()
    curr = dummy
    for v in values:
        curr.next = ListNode(v)
        curr = curr.next
    return dummy.next


def to_list(head: Optional[ListNode]) -> List[int]:
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out


# ==============================================================================
# TESTS -- run:  python 004_sort_list_solution.py
# ==============================================================================
CASES = [
    [4, 2, 1, 3],
    [-1, 5, 3, 4, 0],
    [],
    [1],
    [2, 1],
    [1, 1, 1, 1],
    [5, 4, 3, 2, 1],
    [3, -3, 3, -3, 0],
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: top-down recursive merge sort ---")
    for vals in CASES:
        want = sorted(vals)
        got = to_list(sol.sortList(build_list(vals)))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  sortList({vals!r}) -> {got}")

    print("\n--- correctness: bottom-up iterative merge sort, cross-checked ---")
    for vals in CASES:
        want = sorted(vals)
        got = to_list(sol.sortList_bottom_up(build_list(vals)))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  bottom_up({vals!r}) -> {got}")

    print("\n--- correctness: naive collect+overwrite, cross-checked ---")
    for vals in CASES:
        want = sorted(vals)
        got = to_list(sol.sortList_collect_and_overwrite(build_list(vals)))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  naive({vals!r}) -> {got}")

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: [4,2,1,3] ---")

    def traced_sort(head, depth=0):
        indent = "  " * depth
        vals = to_list(head)
        if not head or not head.next:
            print(f"{indent}base case: {vals}")
            return head
        prev, slow, fast = None, head, head
        while fast and fast.next:
            prev = slow
            slow = slow.next
            fast = fast.next.next
        prev.next = None
        print(f"{indent}split {vals} -> {to_list(head)} | {to_list(slow)}")
        left = traced_sort(head, depth + 1)
        right = traced_sort(slow, depth + 1)
        left_vals, right_vals = to_list(left), to_list(right)
        merged = sol._merge(left, right)
        print(f"{indent}merge {left_vals} + {right_vals} -> {to_list(merged)}")
        return merged

    traced_sort(build_list([4, 2, 1, 3]))

    # ----------------------------------------------------------------------
    # Randomised cross-check, all three implementations.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check (recursive vs bottom-up vs naive), 1000 trials ---")
    random.seed(148)
    mismatches = 0
    for _ in range(1000):
        n = random.randint(0, 40)
        vals = [random.randint(-200, 200) for _ in range(n)]
        want = sorted(vals)
        r1 = to_list(sol.sortList(build_list(vals)))
        r2 = to_list(sol.sortList_bottom_up(build_list(vals)))
        r3 = to_list(sol.sortList_collect_and_overwrite(build_list(vals)))
        if not (r1 == r2 == r3 == want):
            mismatches += 1
    print(f"  1000 random lists: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # Benchmark: recursion stack cost vs bottom-up, on a long list.
    # ----------------------------------------------------------------------
    print("\n--- top-down recursion vs bottom-up iteration: measured runtime ---")
    print(f"  {'n':>10} {'top-down':>12} {'bottom-up':>12} {'ratio':>8}")
    random.seed(21)
    for n in (5_000, 20_000, 80_000):
        vals = [random.randint(-10**6, 10**6) for _ in range(n)]
        h1 = build_list(vals)
        t0 = time.perf_counter(); sol.sortList(h1); t1 = time.perf_counter()
        h2 = build_list(vals)
        sol.sortList_bottom_up(h2); t2 = time.perf_counter()
        td_ms = (t1 - t0) * 1000
        bu_ms = (t2 - t1) * 1000
        ratio = td_ms / bu_ms if bu_ms > 0 else float("inf")
        print(f"  {n:>10} {td_ms:>10.2f}ms {bu_ms:>10.2f}ms {ratio:>7.2f}x")
    print("  (both are O(n log n); the interesting number is Python's recursion")
    print("   limit, not wall-clock -- top-down needs ~log2(n) stack frames, well")
    print("   under sys.getrecursionlimit() even at n=80,000, so it doesn't crash")
    print("   here, but a language/runtime with a smaller default stack could.)")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
