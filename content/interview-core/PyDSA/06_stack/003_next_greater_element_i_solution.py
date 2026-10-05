"""
================================================================================
SOLUTION · LeetCode 496 · Next Greater Element I                         [Easy]
https://leetcode.com/problems/next-greater-element-i/
================================================================================

THE CORE IDEA
--------------
This is topic 06's canonical monotonic-stack problem — see the topic guide's
Part 2 for the full argument, restated here. Strip away the nums1/nums2
indirection: the real computation is "for every value in nums2, what is its
next greater element to the right?" — answered ONCE over nums2, then looked
up per nums1 query.

Walk nums2 left to right with a stack that holds values still WAITING for
their next-greater element, kept in decreasing order bottom-to-top. When a
new value `x` arrives bigger than the stack's top, that top value has just
found its answer — pop it, record `x` as its next-greater, and repeat (one
new value can resolve several waiting values at once).

    next_greater = {}
    stack = []                      # values, decreasing top-down
    for x in nums2:
        while stack and stack[-1] < x:
            next_greater[stack.pop()] = x
        stack.append(x)
    # anything left on the stack at the end never found one -> -1
    return [next_greater.get(v, -1) for v in nums1]

O(n + m) time (n = len(nums2), m = len(nums1)), O(n) space.


================================================================================
WHY THIS IS O(n), NOT O(n^2) — the amortized argument
================================================================================
Topic guide §2.1: the nested `while` inside the `for` looks like O(n) work
per iteration, but every value is PUSHED exactly once (once per outer loop
iteration) and POPPED at most once (once popped, it's resolved and gone
forever — nothing is ever pushed back). So the while loop's total
iterations across the WHOLE run is bounded by the total number of pops,
which is <= n. n pushes + at most n pops = O(n) total, not O(n) per
iteration times n iterations.

Compare this to the brute-force scan — for every element, scan forward
until a bigger value appears (or the array ends): that IS O(n^2) worst case
(strictly decreasing nums2: every scan runs to the end). The monotonic
stack computes the identical answer in O(n) because each element is only
ever compared against, and consumed by, the value that actually resolves
it — never re-examined by anything after that. The runtime demo below
measures the real crossover.


================================================================================
ONE NEW VALUE CAN RESOLVE MANY WAITING VALUES AT ONCE
================================================================================
nums2 = [5, 4, 3, 10]:

    x=5    stack: [5]
    x=4    4 < 5, no pop        stack: [5, 4]
    x=3    3 < 4, no pop        stack: [5, 4, 3]
    x=10   10 > 3: pop 3, ng[3]=10
           10 > 4: pop 4, ng[4]=10
           10 > 5: pop 5, ng[5]=10
           stack now empty -> push 10   stack: [10]

    ONE arrival (10) resolved THREE waiting values in a single step. This is
    exactly why the while loop can legitimately run more than once per
    outer iteration without breaking the O(n) bound — those extra
    iterations are "spent" pops that will never be spent again.


================================================================================
STEP BY STEP TRACE
================================================================================
nums2 = [1, 3, 4, 2]

    i  x    stack before      action                          stack after   next_greater
    -  -    ------------      ------                          -----------   ------------
    0  1    []                1 has nothing to compare, push   [1]           {}
    1  3    [1]               3 > 1: pop 1, ng[1]=3; push 3    [3]           {1:3}
    2  4    [3]               4 > 3: pop 3, ng[3]=4; push 4    [4]           {1:3, 3:4}
    3  2    [4]               2 < 4, no pop; push 2            [4, 2]        {1:3, 3:4}

    end: 4 and 2 never resolved -> ng[4]=-1, ng[2]=-1 (via .get default)

    nums1 = [4, 1, 2] -> [ng[4], ng[1], ng[2]] = [-1, 3, -1]   ✓ matches example 1


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time      Space   Mutates input?  Note
    -------------------------------------  --------  ------  ---------------  ----------------------
    Brute: for each nums1 elt, scan nums2  O(n*m)    O(1)    no               re-finds index, then
           forward from its index                                            scans right again
    Precompute via forward scan per elt    O(n^2)    O(n)    no               one O(n) pass over
                                                                               ALL of nums2, still
                                                                               O(n^2) total
    Monotonic stack ✅                     O(n+m)    O(n)    no               the answer


================================================================================
EDGE CASES
================================================================================
    nums2 strictly decreasing, e.g. [4,3,2,1] -> every element's answer is
        -1; the stack only ever grows, never pops — worst case for the
        stack's SPACE (holds all n values) but still O(n) time.
    nums2 strictly increasing, e.g. [1,2,3,4] -> every element resolves
        immediately against its successor; the stack never holds more than
        1 element at a time — worst case for the WHILE loop firing on
        every single iteration, still O(n) total per the amortized bound.
    A single shared maximum resolves everything, e.g. nums2=[5,4,3,10] ->
        one value (10) pops the entire stack in one step (see above).
    nums1 == nums2 (same order) -> every query is answered, nothing
        defaults to -1 unless nums2 itself has an unresolved tail.
    nums1 has length 1 -> exercises the dict lookup path alone, independent
        of the stack-building pass.


================================================================================
COMMON MISTAKES
================================================================================
1. Re-finding each nums1 element's index in nums2 and re-scanning forward
   for every query — this ignores that "next greater in nums2" is a
   property of nums2 ALONE and should be computed once, not once per query.

2. Using `while stack and stack[-1] <= x` (non-strict) instead of `< x` —
   the problem defines "next GREATER," not "next greater-or-equal"; since
   all values are guaranteed distinct here it happens not to matter for
   THIS problem's inputs, but writing `<=` out of habit breaks on problems
   that allow duplicates (state the distinction even though it's moot here).

3. Popping from the stack without recording the answer for the popped
   value — the whole point of the pop is that `x` IS that value's answer;
   forgetting to write it into the map silently drops results.

4. Forgetting the `-1` default for values that survive to the end of the
   stack — either prefill or use `.get(v, -1)`; a plain `next_greater[v]`
   raises KeyError for anything unresolved.

5. Pushing INDICES onto the stack when VALUES would do (or vice versa) and
   then mixing up which one gets compared vs. which one gets stored —
   values are safe here specifically because the problem guarantees
   uniqueness; with duplicates allowed, indices become necessary (see the
   follow-up below).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if nums2 contained duplicate values?
A: Values can no longer double as a unique dict key. Push (index, value)
   pairs, or just indices, and store answers in an array indexed by
   position rather than a value->answer dict — same algorithm, different
   payload (topic guide §2.3's "payload" column).

Q: LC 503 (Next Greater Element II) wraps the array circularly — how does
   that change this?
A: Conceptually iterate the array twice (`for i in range(2 * n): x = nums[i % n]`)
   without actually doubling memory, so an element near the end can still
   find a next-greater that wraps around to the front. The stack logic is
   otherwise unchanged.

Q: Can you find the next SMALLER element instead?
A: Flip the comparison: `while stack and stack[-1] > x` — the stack becomes
   increasing instead of decreasing. Same O(n) argument.

Q: What if you needed the next greater element to the LEFT instead of the
   right?
A: Run the same algorithm scanning right to left instead of left to right —
   the stack still represents "elements still waiting," just processed in
   the mirrored direction.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 503  Next Greater Element II    — circular array, see follow-up above
    LC 739  Daily Temperatures         — problem 007 here: same template,
                                        answer is a DISTANCE, not a value
    LC 901  Online Stock Span          — problem 009 here: same template,
                                        STREAMING input
    LC 84   Largest Rectangle in
            Histogram                  — problem 010 here: same template,
                                        answer is an AREA
    LC 853  Car Fleet                  — problem 008 here: the template in
                                        disguise
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def nextGreaterElement(self, nums1: List[int], nums2: List[int]) -> List[int]:
        """Monotonic decreasing stack over nums2, O(n+m) time, O(n) space.
        The answer. See THE CORE IDEA above."""
        next_greater = {}
        stack: List[int] = []
        for x in nums2:
            while stack and stack[-1] < x:
                next_greater[stack.pop()] = x
            stack.append(x)
        return [next_greater.get(v, -1) for v in nums1]

    # ------------------------------------------------------------------
    # Alternatives / oracles.
    # ------------------------------------------------------------------
    def nextGreaterElement_brute(self, nums1: List[int], nums2: List[int]) -> List[int]:
        """O(n*m) reference: for each nums1 query, find its index in nums2
        then scan forward for the first bigger value. No stack at all."""
        result = []
        for v in nums1:
            idx = nums2.index(v)
            found = -1
            for j in range(idx + 1, len(nums2)):
                if nums2[j] > v:
                    found = nums2[j]
                    break
            result.append(found)
        return result

    def _next_greater_map_brute(self, nums2: List[int]) -> dict:
        """O(n^2) reference: for EVERY value in nums2 (not just nums1's
        subset), scan forward once. Precomputes the same map the stack
        version builds in O(n), used for the runtime benchmark below."""
        n = len(nums2)
        ng = {}
        for i in range(n):
            found = -1
            for j in range(i + 1, n):
                if nums2[j] > nums2[i]:
                    found = nums2[j]
                    break
            ng[nums2[i]] = found
        return ng


# ==============================================================================
# TESTS — run:  python 003_next_greater_element_i_solution.py
# ==============================================================================
CASES = [
    ([4, 1, 2], [1, 3, 4, 2], [-1, 3, -1]),
    ([2, 4], [1, 2, 3, 4], [3, -1]),
    ([1, 3, 5, 2, 4], [6, 5, 4, 3, 2, 1, 7], [7, 7, 7, 7, 7]),
    ([1], [1], [-1]),
    ([3], [3, 2, 1], [-1]),
    ([1], [1, 2], [2]),
    ([4, 3, 2, 1], [1, 2, 3, 4], [-1, 4, 3, 2]),
    ([5], [5, 4, 3, 10], [10]),
    ([4, 3, 2], [5, 4, 3, 10, 2], [10, 10, -1]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: monotonic stack vs O(n*m) brute force ---")
    for nums1, nums2, expected in CASES:
        want = sol.nextGreaterElement_brute(list(nums1), list(nums2))
        got = sol.nextGreaterElement(list(nums1), list(nums2))
        ok = got == expected and want == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums1={nums1!r:<18} nums2={nums2!r:<24} "
              f"-> {got}  (want {expected})")

    # ----------------------------------------------------------------------
    # One value resolving many, demonstrated live.
    # ----------------------------------------------------------------------
    print("\n--- one arrival resolving multiple waiting values: nums2=[5,4,3,10] ---")
    stack: List[int] = []
    ng = {}
    for x in [5, 4, 3, 10]:
        resolved = []
        while stack and stack[-1] < x:
            popped = stack.pop()
            ng[popped] = x
            resolved.append(popped)
        stack.append(x)
        print(f"  x={x:<3} resolved this step: {resolved or '(none)'}   stack: {stack}")
    print(f"  final map: {ng}")

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: nums2 = [1, 3, 4, 2] ---")
    stack = []
    ng = {}
    for i, x in enumerate([1, 3, 4, 2]):
        popped_list = []
        while stack and stack[-1] < x:
            p = stack.pop()
            ng[p] = x
            popped_list.append(p)
        stack.append(x)
        popped_str = str(popped_list) if popped_list else "-"
        print(f"  i={i} x={x:<3} popped/resolved: {popped_str:<10} "
              f"stack: {stack!s:<12} next_greater: {ng}")

    # ----------------------------------------------------------------------
    # Randomised cross-check vs the O(n*m) oracle.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n*m) oracle ---")
    random.seed(3)
    trials, mismatches = 2000, 0
    for _ in range(trials):
        n = random.randint(1, 15)
        nums2 = random.sample(range(1, 100), n)
        m = random.randint(1, n)
        nums1 = random.sample(nums2, m)
        if (sol.nextGreaterElement(list(nums1), list(nums2))
                != sol.nextGreaterElement_brute(list(nums1), list(nums2))):
            mismatches += 1
    print(f"  {trials} random (nums1, nums2) pairs: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # O(n) monotonic stack vs O(n^2) brute-force forward scan: measured.
    # ----------------------------------------------------------------------
    print("\n--- O(n) monotonic stack vs O(n^2) brute-force scan: measured runtime ---")
    print("  (worst case: strictly decreasing array — every brute-force scan")
    print("   runs all the way to the end, and the stack only ever grows)")
    print(f"  {'n':>7} {'stack O(n)':>14} {'brute O(n^2)':>14} {'ratio':>8}")
    for n in (500, 2_000, 4_000):
        nums2 = list(range(n, 0, -1))     # strictly decreasing: true worst case for both
        t0 = time.perf_counter()
        stack_ng = {}
        st = []
        for x in nums2:
            while st and st[-1] < x:
                stack_ng[st.pop()] = x
            st.append(x)
        t1 = time.perf_counter()
        sol._next_greater_map_brute(nums2)
        t2 = time.perf_counter()
        st_ms = (t1 - t0) * 1000
        br_ms = (t2 - t1) * 1000
        ratio = br_ms / st_ms if st_ms > 0 else float("inf")
        print(f"  {n:>7} {st_ms:>12.2f}ms {br_ms:>12.2f}ms {ratio:>7.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
