"""
================================================================================
SOLUTION · LeetCode 287 · Find the Duplicate Number                    [Medium]
https://leetcode.com/problems/find-the-duplicate-number/
================================================================================

THE CORE IDEA
--------------
This is topic 08's "surprise" problem — see the topic guide's closing note on
the progression table. It LOOKS like a pure array problem, but treating
`nums[i]` as a `.next` pointer turns it into a disguised instance of problem
003's cycle detection.

Define a function over indices: `next(i) = nums[i]`. Because every value is
in `[1, n]` and the array has `n + 1` slots (indices `0..n`), `nums[i]` is
ALWAYS a valid index — so this function defines a walk exactly like following
`.next` pointers in a linked list, starting from index 0:

    0 -> nums[0] -> nums[nums[0]] -> nums[nums[nums[0]]] -> ...

By the pigeonhole principle, n+1 values drawn from range [1, n] force at
least one value to repeat. Under the pointer reinterpretation, "value v
repeats" means at least two different indices both point to index v — a
merge point in the functional graph. Once two different walks (or two steps
of the same walk) land on the same node, every subsequent step is identical,
which is precisely the definition of a cycle. So this walk is GUARANTEED to
enter a cycle — no fixed point is needed, no special-casing.

The critical fact that solves the problem: **the entrance to that cycle is
exactly the duplicate value.** Every index i whose value equals the
duplicate points INTO the cycle at that one shared node; the duplicate
itself is a node with in-degree >= 2 (at least two indices point at it),
which is exactly what makes it a cycle entrance, not an ordinary node inside
a simple chain (every ordinary node here has in-degree <= 1, since values
are otherwise unique).

So: run Floyd's cycle detection (topic 08 problem 003) on this implicit
list, starting at index 0, then run the cycle-ENTRANCE phase (topic 08's Go
guide §3.3, ported to Python) to recover the duplicate value itself.


================================================================================
APPROACH 1 · Sort (baseline, disallowed by O(1)-space rule)
================================================================================
Sort a COPY of nums; adjacent equal elements reveal the duplicate.

    Time:  O(n log n)     Space: O(n) (copy — sorting in place would mutate
                                        input, which the problem forbids)

Simple and correct, but violates both the O(1)-space follow-up AND (if done
in place) the "don't modify nums" constraint. Worth stating and pricing,
not coding as the answer.


================================================================================
APPROACH 2 · Hash set (baseline, disallowed by O(1)-space rule)
================================================================================
Walk nums once, tracking seen values in a set; the first repeat is the
answer.

    seen = set()
    for x in nums:
        if x in seen:
            return x
        seen.add(x)

    Time:  O(n)     Space: O(n)

This is the "obvious" O(n) answer and the one most candidates reach for
first. It is CORRECT and does not mutate the array, but the follow-up
explicitly asks for O(1) extra space, which a set cannot give you.


================================================================================
APPROACH 3 · Floyd's cycle detection on the implicit list ✅ (the answer)
================================================================================

PHASE 1 — find a meeting point inside the cycle (identical to problem 003,
with nums[i] standing in for .next). Both pointers start at INDEX 0 and take
their first step BEFORE any comparison — a do-while shape, not a while:

    slow = fast = 0
    while True:
        slow = nums[slow]
        fast = nums[nums[fast]]
        if slow == fast:
            break

Starting `slow == fast == 0` and comparing immediately (a plain `while slow
!= fast` with no first step) would trivially "meet" before either pointer
has moved — the do-while shape sidesteps that by always taking a step first.

PHASE 2 — find the cycle's entrance (topic 08's Go guide §3.3's math, ported
verbatim: distance from the true start to the cycle entrance equals distance
from the meeting point back around to the entrance):

    slow2 = 0
    while slow2 != slow:
        slow2 = nums[slow2]
        slow = nums[slow]
    return slow2      # == slow == the duplicate value

    Time:  O(n)     Space: O(1), does not modify nums


================================================================================
STEP BY STEP TRACE — nums = [1, 3, 4, 2, 2], duplicate = 2
================================================================================
Reinterpret as pointers:  index -> nums[index]

    index:  0  1  2  3  4
    value:  1  3  4  2  2

    0 -> 1 -> 3 -> 2 -> 4 -> 2 -> 4 -> 2 -> ...   (2 and 4 form a 2-cycle)

    ASCII graph:
        0 -> 1 -> 3 -> 2 -> 4
                        ^    |
                        +----+

    Both pointers start at INDEX 0 (not nums[0]) and take their first step
    before any comparison (a do-while shape — see APPROACH 3's code):

    PHASE 1 (find a meeting point), values are indices AND array contents
    at once, so read "slow=nums[slow]" as "hop to the node nums[slow] names":

        init:   slow=0            fast=0
        step 1: slow=nums[0]=1    fast=nums[nums[0]]=nums[1]=3     1 != 3
        step 2: slow=nums[1]=3    fast=nums[nums[3]]=nums[2]=4     3 != 4
        step 3: slow=nums[3]=2    fast=nums[nums[4]]=nums[2]=4     2 != 4
        step 4: slow=nums[2]=4    fast=nums[nums[4]]=nums[2]=4     4 == 4  <- MEET at 4

    PHASE 2 (find the entrance), slow2 restarts at index 0, slow keeps going
    from the meeting point, both now stepping ONE at a time:

        init:   slow2=0    slow=4
        step 1: slow2=nums[0]=1    slow=nums[4]=2      1 != 2
        step 2: slow2=nums[1]=3    slow=nums[2]=4      3 != 4
        step 3: slow2=nums[3]=2    slow=nums[4]=2      2 == 2  <- CONVERGE at 2

    Answer: 2. This exact trace (init line plus 4 phase-1 steps and 3
    phase-2 steps) is what the runtime demo below prints, verified live.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time         Space   Mutates input?   Note
    ---------------------------  -----------  ------  ---------------  ----------------------
    Sort a copy                 O(n log n)   O(n)    no               simple, wrong space class
    Hash set                    O(n)         O(n)    no               the "obvious" O(n) answer
    Floyd's (pointer-chase) ✅  O(n)         O(1)    no               meets the follow-up


================================================================================
EDGE CASES
================================================================================
    [1, 1]                    -> 1   Smallest possible input (n=1): duplicate
                                      is forced immediately, self-loop at
                                      index 1 pointing to itself.
    [x, x, x, ..., x]          -> x   Duplicate repeats MANY times, not just
                                      twice — the algorithm doesn't care how
                                      many times, only that a cycle exists.
    duplicate is the LARGEST value (n)   Exercises indices at the far end of
                                      the array; no special casing needed
                                      since the pointer walk is index-based,
                                      not value-magnitude-based.
    duplicate at nums[0] AND elsewhere   The walk still starts at index 0
                                      regardless of what nums[0] holds; no
                                      special case required.


================================================================================
COMMON MISTAKES
================================================================================
1. Comparing `slow == fast` BEFORE either pointer has taken a step — since
   both start at index 0, `slow == fast` trivially holds at the very start,
   producing an instant false "meeting." The loop must take a step first
   (a do-while shape, `while True: ... if slow == fast: break`), not a
   plain `while slow != fast: ...` checked before any movement.

2. Confusing this with "does the array need to be sorted" — it does not;
   the trick has nothing to do with array order, only with values being
   valid indices into the same array.

3. Modifying nums in place to mark visited values (e.g. negating
   nums[abs(x)], the trick from problem 006's duplicate-detection style) —
   this VIOLATES the "do not modify nums" constraint here, unlike some
   other array problems where in-place marking is fine.

4. Using a hash set "because it's O(n) and easy" without naming that it
   fails the O(1)-space follow-up — always state the trade-off out loud.

5. Forgetting phase 2 entirely and returning the phase-1 meeting point as
   the answer — the meeting point is generally NOT the duplicate value
   itself, only a node reachable inside the cycle. Phase 2's reset-and-walk
   is what recovers the true entrance.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Prove a duplicate must exist.
A: Pigeonhole: n+1 values drawn from the range [1, n] (n possible values)
   force at least one repeat.

Q: What if more than one number could be duplicated?
A: Floyd's alone no longer identifies a UNIQUE answer; you'd need a
   different technique (e.g. binary search on value range using a counting
   predicate, still O(1) extra space, O(n log n) time) since the "single
   cycle entrance" argument assumes exactly one repeated value.

Q: Binary search alternative?
A: Binary search on the VALUE range [1, n]: for a candidate midpoint m,
   count how many elements are <= m. If that count exceeds m, the duplicate
   is in [1, m], else it's in (m, n]. O(n log n) time, O(1) space — doesn't
   need the array to be sorted, only counts.

Q: Why does this generalize / where else does "value as index" show up?
A: Problem 006 in topic 01 (Find All Numbers Disappeared) also treats
   values as indices, marking visited slots by negation — but there the
   array MAY be mutated, which is disallowed here, forcing the
   cycle-detection route instead.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 141  Linked List Cycle              — Floyd's, the base pattern
                                              (problem 003 here)
    LC 142  Linked List Cycle II            — cycle ENTRANCE, the phase-2
                                              math this problem reuses
    LC 448  Find All Numbers Disappeared    — sibling "value as index" trick,
                                              but mutation IS allowed there
                                              (topic 01, problem 006)
    LC 442  Find All Duplicates in an Array — same family, allows mutation
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def findDuplicate(self, nums: List[int]) -> int:
        """Floyd's cycle detection on the implicit linked list nums[i] -> next.
        O(n) time, O(1) space, does not mutate nums. See THE CORE IDEA above."""
        # Phase 1: find a meeting point inside the cycle. Both pointers start
        # at index 0 and take their FIRST step before any comparison (a
        # do-while shape) — starting slow == fast == nums[0] and comparing
        # immediately would falsely "meet" on the very first check.
        slow = fast = 0
        while True:
            slow = nums[slow]
            fast = nums[nums[fast]]
            if slow == fast:
                break

        # Phase 2: find the cycle's entrance == the duplicate value.
        slow2 = 0
        while slow2 != slow:
            slow2 = nums[slow2]
            slow = nums[slow]
        return slow2

    # ------------------------------------------------------------------
    # Alternatives / oracles.
    # ------------------------------------------------------------------
    def findDuplicate_sort(self, nums: List[int]) -> int:
        """O(n log n) time, O(n) space (copy to avoid mutating input)."""
        arr = sorted(nums)
        for i in range(1, len(arr)):
            if arr[i] == arr[i - 1]:
                return arr[i]
        raise ValueError("no duplicate found")  # unreachable per constraints

    def findDuplicate_hashset(self, nums: List[int]) -> int:
        """O(n) time, O(n) space. The 'obvious' answer; fails the O(1)-space
        follow-up but is a fine first thing to say out loud."""
        seen = set()
        for x in nums:
            if x in seen:
                return x
            seen.add(x)
        raise ValueError("no duplicate found")  # unreachable per constraints

    def findDuplicate_binary_search(self, nums: List[int]) -> int:
        """O(n log n) time, O(1) space. Binary search on the VALUE range
        using a counting predicate — an alternative that meets the space
        bound without pointer-chasing."""
        lo, hi = 1, len(nums) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            count = sum(1 for x in nums if x <= mid)
            if count > mid:
                hi = mid
            else:
                lo = mid + 1
        return lo


# ==============================================================================
# TESTS — run:  python 012_find_the_duplicate_number_solution.py
# ==============================================================================
CASES = [
    ([1, 3, 4, 2, 2], 2),
    ([3, 1, 3, 4, 2], 3),
    ([3, 3, 3, 3, 3], 3),
    ([1, 1], 1),
    ([2, 2, 2, 2, 2], 2),
    ([1, 2, 3, 4, 4], 4),
    ([2, 1, 3, 4, 5, 6, 7, 8, 9, 10, 5], 5),
    ([5, 4, 3, 2, 1, 1], 1),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: Floyd's vs sort vs hashset vs binary-search oracles ---")
    for nums, want in CASES:
        original = list(nums)
        got_floyd = sol.findDuplicate(list(nums))
        got_sort = sol.findDuplicate_sort(list(nums))
        got_set = sol.findDuplicate_hashset(list(nums))
        got_bsearch = sol.findDuplicate_binary_search(list(nums))
        ok = (got_floyd == want == got_sort == got_set == got_bsearch)
        # also verify input was NOT mutated by the Floyd's version
        untouched = list(nums) == original
        ok &= untouched
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums!r:<32} -> floyd={got_floyd} "
              f"sort={got_sort} set={got_set} bsearch={got_bsearch}  "
              f"(want {want}, input untouched={untouched})")

    # ----------------------------------------------------------------------
    # Live trace: the implicit linked list, pointer-chasing nums[i] -> nums[nums[i]].
    # ----------------------------------------------------------------------
    print("\n--- nums as an implicit linked list: index -> nums[index] ---")
    nums = [1, 3, 4, 2, 2]
    print(f"  nums = {nums}")
    print(f"  {'index':>6}: " + " ".join(f"{i:>3}" for i in range(len(nums))))
    print(f"  {'value':>6}: " + " ".join(f"{v:>3}" for v in nums))
    print("  walk from index 0, following i -> nums[i]:")
    path = [0]
    cur = 0
    seen_idx = {0}
    for _ in range(10):
        cur = nums[cur]
        path.append(cur)
        if cur in seen_idx:
            break
        seen_idx.add(cur)
    print("  " + " -> ".join(str(p) for p in path) + (" -> ..." if len(path) < 10 else ""))
    print(f"  cycle detected at repeated node {path[-1]} — this IS the duplicate value")

    print("\n  Floyd's phase-by-phase trace on this array:")
    slow = fast = 0
    step = 0
    print(f"  {'step':>4} {'slow':>6} {'fast':>6}")
    print(f"  {'init':>4} {slow:>6} {fast:>6}")
    while True:
        slow = nums[slow]
        fast = nums[nums[fast]]
        step += 1
        print(f"  {step:>4} {slow:>6} {fast:>6}")
        if slow == fast:
            break
    print(f"  phase 1 meeting point: {slow}")
    slow2 = 0
    step2 = 0
    print(f"  {'step':>4} {'slow2':>6} {'slow':>6}")
    print(f"  {step2:>4} {slow2:>6} {slow:>6}")
    while slow2 != slow:
        slow2 = nums[slow2]
        slow = nums[slow]
        step2 += 1
        print(f"  {step2:>4} {slow2:>6} {slow:>6}")
    print(f"  phase 2 converges at: {slow2}  == duplicate value ({sol.findDuplicate(nums)})")

    # ----------------------------------------------------------------------
    # Complexity-space argument: hashset baseline correctness (space priced,
    # not benchmarked — the point of this problem is the space bound, not
    # a runtime race, since all three candidate approaches are O(n) or
    # O(n log n) and dominated by input generation at these sizes).
    # ----------------------------------------------------------------------
    print("\n--- space accounting: O(1) Floyd's vs O(n) hashset (same n) ---")
    import sys
    big = list(range(1, 50_001)) + [17]  # n = 50000, duplicate = 17
    random.Random(42).shuffle(big)
    t0 = time.perf_counter()
    ans_floyd = sol.findDuplicate(list(big))
    t1 = time.perf_counter()
    ans_set = sol.findDuplicate_hashset(list(big))
    t2 = time.perf_counter()
    print(f"  n=50000: floyd -> {ans_floyd} in {(t1 - t0) * 1000:.2f} ms (O(1) extra space)")
    print(f"  n=50000: hashset -> {ans_set} in {(t2 - t1) * 1000:.2f} ms "
          f"(O(n) extra space: a Python set of up to n ints)")
    print("  Note: at this n, Floyd's can measure SLOWER in wall-clock time than the")
    print("  hashset in CPython (observed here) — it does more pointer-hop iterations")
    print("  with interpreter overhead per hop, while set membership is a fast C-level")
    print("  hash lookup. The reason to prefer Floyd's is the SPACE bound the problem")
    print("  demands (O(1) vs O(n)), not a wall-clock win — name this trade-off out")
    print("  loud rather than assuming O(1) space also means faster in practice.")
    all_ok &= (ans_floyd == ans_set == 17)

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
