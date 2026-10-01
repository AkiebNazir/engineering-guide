"""
================================================================================
SOLUTION · LeetCode 382 · Linked List Random Node                   [Medium]
https://leetcode.com/problems/linked-list-random-node/
================================================================================

THE CORE IDEA
--------------
Reservoir sampling, reservoir size 1, run directly over the linked list.
Walk from head, keeping a 1-indexed counter `m` of nodes visited so far. At
the m-th node, replace the held `result` with this node's value with
probability 1/m. By the time the walk reaches the end, `result` holds a
value chosen uniformly among all n nodes -- the exact same telescoping-
product proof as problem 002, just with "match" redefined as "any node."

This is the technique's natural habitat: a linked list's length is NOT
knowable in O(1) (you cannot index into it, and finding the length costs an
O(n) pass by itself), so reservoir sampling isn't just an elegant option
here -- it's the only way to solve this in ONE pass without first walking
the whole list to count it, and it does so in O(1) extra space regardless
of how long the list turns out to be.

O(n) time per getRandom() call, O(1) extra space.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (materialize to an array first, price it): in __init__, walk
the list once and store `self.values = [node.val for node in ...]`. Then
getRandom() is O(1): random.choice(self.values). Valid, and actually FASTER
per-call than reservoir sampling since each call becomes O(1) instead of
O(n) -- a real trade-off worth naming to the interviewer. Costs O(n) EXTRA
space held for the lifetime of the Solution object, on top of the linked
list itself, which reservoir sampling avoids entirely.

Approach 1 (chosen) -- reservoir sampling directly over the list in
getRandom(), no array ever materialized. O(n) time per call, O(1) extra
space. This is what's implemented below; `_array_precompute_values` exists
only to power the space-comparison demo, not as the real solution.


================================================================================
STEP BY STEP TRACE
================================================================================
list: 1 -> 2 -> 3 (head to tail). getRandom() walks it once.

    node=1 (m=1): keep with prob 1/1 -> always keep. result=1
    node=2 (m=2): keep with prob 1/2. say coin says "keep" -> result=2
    node=3 (m=3): keep with prob 1/3. say coin says "don't keep" -> result stays 2

    final: result = 2

By the same telescoping argument as problem 002 (K = n = 3 here, every
node is a "match"), each of the 3 nodes ends up held with probability
exactly 1/3.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time (per call)  Space   Mutates input?
    ---------------------------------  ---------------  ------  --------------
    Precompute array [priced, not shipped]  O(1)         O(n)    no
    Reservoir sampling [chosen]              O(n)         O(1)    no


================================================================================
EDGE CASES
================================================================================
    single-node list       -> m reaches 1 exactly once, kept with
                              probability 1/1 = certain, always returns
                              that one value.
    getRandom() called many times on the same Solution -> each call is an
                              independent full walk; no state persists
                              between calls beyond the stored head reference.
    very long list (10^4 nodes, per constraints) -> reservoir sampling
                              still only needs O(1) extra memory regardless
                              of length; the array-precompute alternative's
                              memory cost scales with n (see runtime demo).
    all node values equal   -> uniformity is over WHICH NODE is chosen, not
                              over distinct values, so this is a non-issue.


================================================================================
COMMON MISTAKES
================================================================================
1. Converting to an array in getRandom() itself (instead of once in
   __init__, or never) -- re-walks and re-allocates on every single call,
   the worst of both approaches (O(n) time AND O(n) space per call).
2. Off-by-one in the reservoir probability: using 1/(m+1) or 1/(m-1)
   instead of 1/m for the m-th node -- breaks the telescoping proof and
   produces measurably non-uniform output (same class of bug as problem
   001/002).
3. Forgetting the list could have just ONE node and mishandling an empty
   reservoir walk (though per constraints the list always has >= 1 node,
   defensive code should not assume `head` is never None if reused
   elsewhere).
4. Re-deriving the list's length with a separate O(n) pass "to be safe"
   before running reservoir sampling -- this defeats the entire point;
   reservoir sampling's whole value proposition is not needing the length
   in advance.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Which approach would you actually ship?" -> depends on the call
  pattern: many getRandom() calls against one list favors precomputing the
  array (amortized O(1) per call); a huge list with few calls, or a true
  streaming source you can't hold in memory, favors reservoir sampling.
- "Generalize to picking k random nodes." -> reservoir sampling of size k:
  keep the first k nodes, then for the m-th node (m > k) replace a
  uniformly random reservoir slot with probability k/m.
- "What if the list could be mutated concurrently while getRandom() runs?"
  -> reservoir sampling assumes a stable snapshot during the walk; a
  concurrently-mutating list needs external synchronization regardless of
  which approach is chosen.


================================================================================
RELATED PROBLEMS
================================================================================
- 002 Random Pick Index (LC 398) -- the array-based special case of this
  same reservoir-sampling technique.
- 001 Shuffle an Array (LC 384) -- Fisher-Yates, a different randomized
  technique with its own uniformity proof.
- Random Pick with Weight (LC 528) -- weighted variant, different technique
  entirely (prefix sum + binary search).
================================================================================
"""

import random
import sys
import time
from collections import Counter


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def build_list(values: list[int]) -> ListNode | None:
    head = None
    tail = None
    for v in values:
        node = ListNode(v)
        if head is None:
            head = node
            tail = node
        else:
            tail.next = node
            tail = node
    return head


class Solution:
    def __init__(self, head: ListNode | None):
        self.head = head

    def getRandom(self) -> int:
        result = None
        count = 0
        node = self.head
        while node is not None:
            count += 1
            if random.randint(1, count) == 1:
                result = node.val
            node = node.next
        return result


def _array_precompute_values(head: ListNode | None) -> list[int]:
    """The O(n)-space alternative: materialize every value up front."""
    values = []
    node = head
    while node is not None:
        values.append(node.val)
        node = node.next
    return values


def run_tests() -> None:
    all_ok = True

    head = build_list([1, 2, 3])
    sol = Solution(head)

    valid = {1, 2, 3}
    for _ in range(20):
        got = sol.getRandom()
        if got not in valid:
            all_ok = False
            print(f"FAIL  getRandom() -> {got} not in {valid}")
            break
    else:
        print(f"PASS  20 getRandom() calls all in {valid}")

    head1 = build_list([42])
    sol1 = Solution(head1)
    got = sol1.getRandom()
    ok = got == 42
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  single-node list -> {got}  (want 42)")

    print()
    print("RUNTIME DEMO -- uniformity + O(1) vs O(n) space, measured live")
    print("-" * 72)
    n = 6
    values = list(range(n))
    head_n = build_list(values)
    sol_n = Solution(head_n)
    trials = 30_000

    t0 = time.perf_counter()
    counts = Counter()
    for _ in range(trials):
        counts[sol_n.getRandom()] += 1
    elapsed_ms = (time.perf_counter() - t0) * 1000

    expected = trials / n
    print(f"n = {n} nodes, expected count each if uniform: {expected:.1f}\n")
    max_dev = 0.0
    for v in sorted(counts):
        c = counts[v]
        dev_pct = abs(c - expected) / expected * 100
        max_dev = max(max_dev, dev_pct)
        print(f"  value {v} -> {c:6d}  (dev {dev_pct:5.1f}%)")
    print(f"\nmax deviation from uniform: {max_dev:.1f}%  over {trials} trials  "
          f"({elapsed_ms:.1f} ms total)")

    uniform_enough = max_dev < 10.0
    all_ok &= uniform_enough
    print(f"{'PASS' if uniform_enough else 'FAIL'}  "
          f"empirical frequencies stay within 10% of uniform")

    # Space comparison: reservoir sampling never materializes an array;
    # the alternative approach's array grows linearly with list length.
    big_n = 10_000
    big_values = list(range(big_n))
    big_head = build_list(big_values)
    materialized = _array_precompute_values(big_head)
    array_bytes = sys.getsizeof(materialized) + sum(
        sys.getsizeof(v) for v in materialized[:100]
    ) / 100 * len(materialized)  # rough per-element estimate
    print(f"\nfor a {big_n}-node list: precomputed array occupies "
          f"~{array_bytes / 1024:.1f} KB of EXTRA memory;")
    print("reservoir sampling's getRandom() holds only a few scalars "
          "(result, count, node pointer) -- O(1) regardless of n.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
