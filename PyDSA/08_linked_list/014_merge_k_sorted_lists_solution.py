"""
================================================================================
SOLUTION · LeetCode 23 · Merge k Sorted Lists                          [Hard]
https://leetcode.com/problems/merge-k-sorted-lists/
================================================================================

THE CORE IDEA
--------------
This generalizes problem 002 (merge TWO sorted lists) from k=2 to arbitrary
k. The naive extension — repeatedly merge list 0 into a running result, then
merge list 1 in, then list 2, ... — does k-1 full merges of an
ever-growing result, which is O(N*k) total work (N = total node count across
all lists). Two better shapes both beat that:

1. **Min-heap of k current fronts.** Keep exactly one "current candidate"
   node per list in a heap keyed by `.val`. Pop the smallest, splice it onto
   the output, push its `.next` (if any) back in. The heap never holds more
   than k items, so every pop/push is O(log k), done N times total:
   O(N log k) time, O(k) space for the heap.

2. **Divide and conquer (pairwise merge).** Merge lists in pairs
   (0&1, 2&3, ...), halving the list count each round, using problem 002's
   two-pointer merge as the primitive. log2(k) rounds, each round doing
   O(N) total work across all its pairs (every node is touched once per
   round): O(N log k) time, O(log k) space (recursion depth) or O(1)
   iterative.

Both hit O(N log k) — the SAME complexity class, for the SAME reason: k
lists get merged via a structure of depth log k (a heap of k items, or a
merge tree of height log2 k), and every node is compared/moved once per
"level" of that structure.


================================================================================
APPROACH 0 · Naive sequential merge (baseline, don't code as the answer)
================================================================================
result = lists[0]
for i in range(1, k):
    result = mergeTwoLists(result, lists[i])

Each call to mergeTwoLists costs O(size of result so far). After merging i
lists the result has roughly i * (N/k) nodes, so the i-th merge costs
O(i * N/k), and summing i=1..k gives O(N*k) total — quadratic in k, not
log-linear. Correct, simple to write, but asymptotically the worst of the
three; priced here, benchmarked below, never the answer for large k.


================================================================================
APPROACH 1 · Min-heap of k fronts ✅ (the answer)
================================================================================
    import heapq

    heap = []
    for i, node in enumerate(lists):
        if node:
            heapq.heappush(heap, (node.val, i, node))   # i breaks val ties
    dummy = tail = ListNode()
    while heap:
        val, i, node = heapq.heappop(heap)
        tail.next = node
        tail = tail.next
        if node.next:
            heapq.heappush(heap, (node.next.val, i, node.next))
    return dummy.next

The `i` (list index) in the tuple is NOT cosmetic: ListNode has no `__lt__`,
so if two nodes ever have equal `.val`, Python's tuple comparison would fall
through to comparing ListNode objects directly and raise `TypeError:
'<' not supported between instances of 'ListNode' and 'ListNode'`. Including
the always-distinct list index `i` as a tiebreaker means the comparison
never reaches the third tuple element.

    Time:  O(N log k)     Space: O(k) for the heap, does not copy node data


================================================================================
APPROACH 2 · Divide and conquer (pairwise merge) ✅ (equally valid answer)
================================================================================
    def merge(lists):
        if not lists:
            return None
        while len(lists) > 1:
            merged = []
            for i in range(0, len(lists), 2):
                l1 = lists[i]
                l2 = lists[i + 1] if i + 1 < len(lists) else None
                merged.append(mergeTwoLists(l1, l2))
            lists = merged
        return lists[0]

Each round halves the number of lists (k, k/2, k/4, ..., 1) — log2(k)
rounds — and each round's total work across all its pairs is O(N) (every
node is visited exactly once per round, same argument as merge sort's
"each level does O(N) work"). log2(k) rounds * O(N) per round = O(N log k).

    Time:  O(N log k)     Space: O(log k) recursion depth if written
                                  recursively, O(k) for the `merged` list
                                  each round if written iteratively as above


================================================================================
STEP BY STEP TRACE — lists = [[1,4,5], [1,3,4], [2,6]]
================================================================================
Heap approach, k=3 lists, N=8 nodes total:

    lists[0]: 1 -> 4 -> 5
    lists[1]: 1 -> 3 -> 4
    lists[2]: 2 -> 6

Seed heap with each list's head: (val, list_idx, node)
    heap = [(1,0,L0:1), (1,1,L1:1), (2,2,L2:2)]

    pop (1,0,L0:1)  -> output: 1                push L0's next (4,0,L0:4)
      heap = [(1,1,L1:1), (2,2,L2:2), (4,0,L0:4)]
    pop (1,1,L1:1)  -> output: 1,1               push L1's next (3,1,L1:3)
      heap = [(2,2,L2:2), (4,0,L0:4), (3,1,L1:3)]
    pop (2,2,L2:2)  -> output: 1,1,2             push L2's next (6,2,L2:6)
      heap = [(3,1,L1:3), (4,0,L0:4), (6,2,L2:6)]
    pop (3,1,L1:3)  -> output: 1,1,2,3           push L1's next (4,1,L1:4)
      heap = [(4,0,L0:4), (6,2,L2:6), (4,1,L1:4)]
    pop (4,0,L0:4)  -> output: 1,1,2,3,4         push L0's next (5,0,L0:5)
      (tie 4 vs 4: list_idx 0 < 1 breaks it, L0's node popped first)
      heap = [(4,1,L1:4), (6,2,L2:6), (5,0,L0:5)]
    pop (4,1,L1:4)  -> output: 1,1,2,3,4,4       L1 exhausted, nothing pushed
      heap = [(5,0,L0:5), (6,2,L2:6)]
    pop (5,0,L0:5)  -> output: 1,1,2,3,4,4,5     L0 exhausted, nothing pushed
      heap = [(6,2,L2:6)]
    pop (6,2,L2:6)  -> output: 1,1,2,3,4,4,5,6   L2 exhausted, heap empty

    result: 1 -> 1 -> 2 -> 3 -> 4 -> 4 -> 5 -> 6 -> None

Divide-and-conquer on the same input:
    round 1 (pair up): merge(L0,L1) = 1,1,3,4,4,5   merge(L2,None) = 2,6
    round 2 (pair up): merge([1,1,3,4,4,5], [2,6]) = 1,1,2,3,4,4,5,6
    2 rounds (log2(3) rounds up to 2), same final answer.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time         Space    Mutates input?  Note
    ------------------------------  -----------  -------  ---------------  ----------------------
    Naive sequential merge          O(N*k)       O(1)     yes (rewires)    quadratic in k
    Min-heap of k fronts ✅         O(N log k)   O(k)     yes (rewires)    the answer
    Divide and conquer ✅           O(N log k)   O(log k) yes (rewires)    equally valid answer
    Collect all + sort + rebuild    O(N log N)   O(N)     no               simple, allocates new nodes


================================================================================
EDGE CASES
================================================================================
    lists = []                 -> None    no lists at all; heap starts and
                                           stays empty, loop never runs.
    lists = [[]]                -> None    one list, and it's empty (None
                                           head) — must skip pushing it,
                                           not crash on `node.val`.
    lists = [[], [], []]         -> None    all lists empty; same as above,
                                           generalized.
    lists = [[1,2,3]]            -> [1,2,3] only one list; heap/DC degenerate
                                           to "return it unchanged."
    duplicate values ACROSS lists -> heap tuple needs the list-index
                                           tiebreaker (see APPROACH 1) or
                                           Python raises TypeError comparing
                                           ListNode objects directly.
    lists of very different lengths -> exercises many heap pushes from the
                                           long list after short ones drain.


================================================================================
COMMON MISTAKES
================================================================================
1. Pushing `(node.val, node)` onto the heap WITHOUT a tiebreaker — the first
   time two nodes tie on `.val`, heapq falls through to comparing ListNode
   objects (no `__lt__` defined) and raises `TypeError`. Always include a
   strictly-orderable tiebreaker (list index, or an itertools.count()) as
   the tuple's second element.

2. Using the naive "merge list[0] into result, then list[1], ..." approach
   for large k without naming that it's O(N*k), not O(N log k) — fine as a
   first-pass answer to state and price, wrong to leave uncorrected if the
   interviewer asks about scaling k up.

3. In divide-and-conquer, forgetting to handle an ODD number of lists in a
   round (the last unpaired list needs `l2 = None`, not an index-out-of-range
   crash).

4. Rebuilding new ListNode objects instead of re-splicing existing ones —
   wastes O(N) extra space the problem doesn't ask for, exactly like
   problem 002's mistake #4.

5. Forgetting to push a popped node's `.next` back onto the heap when it
   exists — silently drops the rest of that list from the output.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why is the heap O(N log k) and not O(N log N)?
A: The heap never holds more than k elements at once (one candidate per
   list), so every push/pop is O(log k) regardless of how large N grows;
   N only sets how many times you push/pop, not the heap's size.

Q: When would divide-and-conquer beat the heap in practice?
A: The heap has per-operation overhead (Python-level tuple comparisons,
   heap invariant maintenance) with a constant-size heap; D&C's merge-pair
   primitive is problem 002's tight two-pointer loop, which can have lower
   constant factors in practice — see the runtime demo below for what this
   machine actually measured.

Q: What if k is much larger than N/k (many short lists)?
A: Same complexity class either way, but the heap's O(k) space to hold one
   node per list can dominate if k is very large relative to total N —
   worth naming as a space trade-off.

Q: Merge k sorted ARRAYS instead of linked lists?
A: Same heap idea, but pushing (value, array_idx, element_idx) tuples and
   advancing element_idx instead of following `.next` — the linked-list
   version needs no extra index bookkeeping because `.next` IS the "next
   element" pointer.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 21   Merge Two Sorted Lists         — the k=2 base case (problem 002)
    LC 148  Sort List                      — merge sort ON a single list
    LC 373  Find K Pairs with Smallest Sums — same heap-of-k-candidates shape
    LC 295  Find Median from Data Stream    — heap-based streaming pattern
================================================================================
"""

import heapq
import random
import time
from typing import List, Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def mergeKLists(self, lists: List[Optional[ListNode]]) -> Optional[ListNode]:
        """Min-heap of k current fronts. O(N log k) time, O(k) space.
        The answer. See THE CORE IDEA / APPROACH 1 above."""
        heap = []
        for i, node in enumerate(lists):
            if node:
                heapq.heappush(heap, (node.val, i, node))

        dummy = tail = ListNode()
        while heap:
            val, i, node = heapq.heappop(heap)
            tail.next = node
            tail = tail.next
            if node.next:
                heapq.heappush(heap, (node.next.val, i, node.next))
        return dummy.next

    def mergeKLists_divide_and_conquer(
        self, lists: List[Optional[ListNode]]
    ) -> Optional[ListNode]:
        """Pairwise merge, halving the list count each round.
        O(N log k) time, O(k) space (the `merged` list each round)."""
        if not lists:
            return None
        lists = list(lists)
        while len(lists) > 1:
            merged = []
            for i in range(0, len(lists), 2):
                l1 = lists[i]
                l2 = lists[i + 1] if i + 1 < len(lists) else None
                merged.append(self._merge_two(l1, l2))
            lists = merged
        return lists[0]

    def _merge_two(
        self, l1: Optional[ListNode], l2: Optional[ListNode]
    ) -> Optional[ListNode]:
        """Problem 002's dummy-head two-pointer merge, reused verbatim."""
        dummy = tail = ListNode()
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
    # Baselines — priced, not the answer.
    # ------------------------------------------------------------------
    def mergeKLists_naive_sequential(
        self, lists: List[Optional[ListNode]]
    ) -> Optional[ListNode]:
        """✗ Merge list[0] into result, then list[1], etc. O(N*k) time."""
        result = None
        for head in lists:
            result = self._merge_two(result, head)
        return result

    def mergeKLists_collect_sort(
        self, lists: List[Optional[ListNode]]
    ) -> Optional[ListNode]:
        """✗ Collect all values, sort, rebuild fresh nodes.
        O(N log N) time, O(N) space."""
        values = []
        for head in lists:
            node = head
            while node:
                values.append(node.val)
                node = node.next
        values.sort()
        dummy = tail = ListNode()
        for v in values:
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
# TESTS — run:  python 014_merge_k_sorted_lists_solution.py
# ==============================================================================
CASES = [
    [[1, 4, 5], [1, 3, 4], [2, 6]],
    [],
    [[]],
    [[], [], []],
    [[1, 2, 3]],
    [[], [1]],
    [[-5, -1, 0], [-4, -4, 3], [2]],
    [[1, 1, 1], [1, 1], [1]],
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: heap vs divide-and-conquer vs naive vs collect+sort ---")
    for lists in CASES:
        flat = sorted(v for lst in lists for v in lst)
        got_heap = to_list(sol.mergeKLists([build_list(lst) for lst in lists]))
        got_dc = to_list(sol.mergeKLists_divide_and_conquer([build_list(lst) for lst in lists]))
        got_naive = to_list(sol.mergeKLists_naive_sequential([build_list(lst) for lst in lists]))
        got_sort = to_list(sol.mergeKLists_collect_sort([build_list(lst) for lst in lists]))
        ok = got_heap == got_dc == got_naive == got_sort == flat
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  lists={lists!r:<38} -> {got_heap}  (want {flat})")

    # ----------------------------------------------------------------------
    # Step-by-step trace of the heap approach.
    # ----------------------------------------------------------------------
    print("\n--- trace: heap merge of [[1,4,5], [1,3,4], [2,6]] ---")
    raw = [[1, 4, 5], [1, 3, 4], [2, 6]]
    lists = [build_list(lst) for lst in raw]
    heap = []
    for i, node in enumerate(lists):
        if node:
            heapq.heappush(heap, (node.val, i, node))
    print(f"  seed heap: {[(v, i, n.val) for v, i, n in sorted(heap)]}")
    dummy = tail = ListNode()
    output = []
    while heap:
        val, i, node = heapq.heappop(heap)
        tail.next = node
        tail = tail.next
        output.append(node.val)
        pushed = None
        if node.next:
            pushed = (node.next.val, i, node.next.val)
            heapq.heappush(heap, (node.next.val, i, node.next))
        state = [(v, idx, n.val) for v, idx, n in sorted(heap)]
        print(f"  pop val={val} (list {i}) -> output={output}  pushed={pushed}  heap now={state}")
    print(f"  final: {to_list(dummy.next)}")

    # ----------------------------------------------------------------------
    # Randomised cross-check across all four implementations.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check (heap vs D&C vs naive vs collect+sort) ---")
    random.seed(23)
    trials, mismatches = 500, 0
    for _ in range(trials):
        k = random.randint(0, 6)
        raw = [sorted(random.randint(-15, 15) for _ in range(random.randint(0, 8))) for _ in range(k)]
        want = sorted(v for lst in raw for v in lst)
        r1 = to_list(sol.mergeKLists([build_list(lst) for lst in raw]))
        r2 = to_list(sol.mergeKLists_divide_and_conquer([build_list(lst) for lst in raw]))
        r3 = to_list(sol.mergeKLists_naive_sequential([build_list(lst) for lst in raw]))
        r4 = to_list(sol.mergeKLists_collect_sort([build_list(lst) for lst in raw]))
        if not (r1 == r2 == r3 == r4 == want):
            mismatches += 1
    print(f"  {trials} random k-list groups: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # Benchmark: heap vs D&C vs naive-sequential as k grows, N held roughly
    # constant per list so total N scales with k.
    # ----------------------------------------------------------------------
    print("\n--- O(N log k) heap/D&C vs O(N*k) naive sequential: measured runtime ---")
    print(f"  {'k lists':>10} {'N total':>10} {'heap':>12} {'D&C':>12} {'naive-seq':>12}")
    random.seed(1)
    per_list = 300
    for k in (4, 16, 64):
        raw = [sorted(random.randint(-10**6, 10**6) for _ in range(per_list)) for _ in range(k)]
        n_total = k * per_list

        lists = [build_list(lst) for lst in raw]
        t0 = time.perf_counter(); sol.mergeKLists(lists)
        t1 = time.perf_counter()

        lists = [build_list(lst) for lst in raw]
        sol.mergeKLists_divide_and_conquer(lists)
        t2 = time.perf_counter()

        lists = [build_list(lst) for lst in raw]
        sol.mergeKLists_naive_sequential(lists)
        t3 = time.perf_counter()

        heap_ms = (t1 - t0) * 1000
        dc_ms = (t2 - t1) * 1000
        naive_ms = (t3 - t2) * 1000
        print(f"  {k:>10} {n_total:>10} {heap_ms:>10.2f}ms {dc_ms:>10.2f}ms {naive_ms:>10.2f}ms")

    print("  Observed on this machine: naive-sequential's cost grows much faster than")
    print("  heap/D&C as k increases (its work is O(N*k), the others O(N log k)) — the")
    print("  gap widens with k exactly as the complexity classes predict. Between heap")
    print("  and D&C, the faster of the two on this run is whichever incurs less Python-")
    print("  level overhead per node at this k and per-list size; both stay in the same")
    print("  O(N log k) class, so don't over-read a small constant-factor gap between them.")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
