"""
================================================================================
SOLUTION · LeetCode 283 · Move Zeroes                                    [Easy]
https://leetcode.com/problems/move-zeroes/
================================================================================

THE CORE IDEA
-------------
Same read/write skeleton as LC 26 and LC 27, with `keep = (x != 0)`. The one
new requirement is that the TAIL MUST BE CORRECT — LC 27 could leave garbage
past index k, but here the zeroes have to genuinely be there.

    PHASE 1   compact the non-zeroes forward, preserving order
    PHASE 2   fill from w to the end with 0

    nums = [0, 1, 0, 3, 12]

    phase 1:   [1, 3, 12, 3, 12]        w = 3, tail is stale leftovers
    phase 2:   [1, 3, 12, 0,  0]        write 0 into slots 3..4          ✓

Why phase 2 is provably right: phase 1 kept exactly the non-zeroes, so
(n − w) elements were zeroes. Writing zeroes into exactly those (n − w) tail
slots restores the correct multiset. No counting needed.

Then the SINGLE-PASS SWAP collapses both phases into one:

    w = 0
    for r in range(len(nums)):
        if nums[r] != 0:
            nums[w], nums[r] = nums[r], nums[w]
            w += 1

One swap moves a non-zero LEFT and carries a zero RIGHT simultaneously. This
is the version to write, and understanding why order survives it is the real
content of the problem.

⚠️  NOTE WHAT YOU MAY *NOT* DO HERE
    LC 27's "pull an element in from the back" trick is ILLEGAL in this
    problem — it scrambles order, and this statement requires relative order to
    be maintained. Three nearly identical problems, and the licence to
    reorder is the thing that differs. Always re-read that sentence.


================================================================================
APPROACH 1 · Two phases: compact, then fill ✅ (say this first)
================================================================================

    w = 0
    for r in range(len(nums)):          # phase 1: compact
        if nums[r] != 0:
            nums[w] = nums[r]
            w += 1
    for i in range(w, len(nums)):       # phase 2: fill
        nums[i] = 0

    Time: O(n)   Space: O(1)   Writes: always exactly n

Obviously correct and trivial to explain. Its weakness is the follow-up: it
writes to every single slot, including n self-assignments when there are no
zeroes at all.


================================================================================
APPROACH 2 · One pass, swap ✅✅ (the answer)
================================================================================

    w = 0                               # w = index of the leftmost zero
    for r in range(len(nums)):
        if nums[r] != 0:
            nums[w], nums[r] = nums[r], nums[w]
            w += 1

    Time: O(n)   Space: O(1)   Writes: 2 × (non-zeroes)

STEP BY STEP for nums = [0, 1, 0, 3, 12]:

    r  nums[r]  !=0?  action                      w   array
    -  -------  ----  --------------------------  --  ---------------
    0     0      no   nothing                     0   [0, 1, 0, 3,12]
    1     1     yes   swap slots 0 and 1          1   [1, 0, 0, 3,12]
    2     0      no   nothing                     1   [1, 0, 0, 3,12]
    3     3     yes   swap slots 1 and 3          2   [1, 3, 0, 0,12]
    4    12     yes   swap slots 2 and 4          3   [1, 3,12, 0, 0]

    done                                              [1, 3,12, 0, 0]   ✓

WHY THE ORDER OF THE NON-ZEROES SURVIVES
    Two invariants hold at the top of every iteration:

        (a) nums[0 .. w-1]  are the non-zeroes seen so far, IN ORDER
        (b) nums[w .. r-1]  are all zero

    Non-zeroes are appended to region (a) strictly left to right, in the order
    the read pointer meets them, so their relative order cannot change. And
    because region (b) is all zeroes, the value swapped OUT to position r is
    always a zero — never a non-zero that could jump forward and overtake
    something. That is the proof; it is short, and interviewers ask for it.

WHY IT IS ALSO THE "FEWEST OPERATIONS" ANSWER
    Each swap does the work of both phases at once. Compare on an array with
    z zeroes and (n − z) non-zeroes:

        two-phase:  n writes,              always
        swap:       2 × (n − z) writes

    Swap wins whenever z > n/2 (zero-heavy), loses when zeroes are rare. Which
    means neither is unconditionally better — and that is exactly why the
    guarded version below exists.

⚠️  THE `w == r` SELF-SWAP
    When no zeroes have been seen yet, w == r and the swap is
    `nums[r], nums[r] = nums[r], nums[r]` — a no-op that still builds a tuple
    and performs two stores. On [1,2,3,...] every iteration does this.

    Guard it:

        if nums[r] != 0:
            if w != r:
                nums[w], nums[r] = nums[r], nums[w]
            w += 1

    Now an array with no zeroes performs ZERO writes. That is the honest
    answer to "minimise the total number of operations": the guarded swap is
    the only version whose write count is proportional to the actual amount of
    displacement needed.

    ⚠️  Fewer writes is NOT the same as faster. The benchmark at the bottom of
        this file finds the guarded swap to be the SLOWEST of the three in
        CPython, because the extra branch costs more per element than the
        store it avoids. Writes are cheap here; bytecode is not. The guard
        earns its keep when a write is genuinely expensive — a memory-mapped
        file, flash storage, a contended cache line, or a language where the
        element is a large struct rather than a pointer. Know both halves.

        no zeroes      -> 0 writes
        all zeroes     -> 0 writes
        mixed          -> 2 per displaced non-zero

    The demo at the bottom counts all three variants across input shapes.


================================================================================
APPROACH 3 · The Pythonic one-liners (know why they fail the contract)
================================================================================
    nums.sort(key=bool, reverse=True)        # stable, so order survives!

Genuinely clever: `bool(0)` is False and `bool(x)` is True for any non-zero, and
Timsort is STABLE, so the non-zeroes keep their relative order. But it is
O(n log n) for a problem with an O(n) answer, and "I sorted it" is not the
signal you want.

    nums[:] = [x for x in nums if x != 0] + [0] * nums.count(0)

Correct and it does write through to the caller via slice assignment. But it
allocates two O(n) temporaries, so it is not in place in the sense meant here.

    nums = [x for x in nums if x] + ...      # ✗ rebinds; caller sees NOTHING

That last one is the classic Python trap: assigning to the parameter name does
not touch the caller's list. This function returns None, so a candidate who
makes that mistake gets a silently unchanged array and no error at all.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    n = len(nums), z = number of zeroes

    Approach                Time        Space   Writes          Order?
    ----------------------  ----------  ------  --------------  --------
    sort(key=bool)          O(n log n)  O(n)    n               kept
    comprehension + [:]     O(n)        O(n)    n               kept
    Two-phase           ✅  O(n)        O(1)    n  (always)     kept
    Swap              ✅✅  O(n)        O(1)    2(n − z)        kept
    Guarded swap    ✅✅✅  O(n)        O(1)    2 × displaced   kept

    All the O(1)-space versions mutate the input, which is the point.


================================================================================
EDGE CASES
================================================================================
    [0]            -> [0]
                      Single zero. w stays 0, nothing swaps, phase 2 writes
                      nums[0] = 0. Both approaches fine.

    [1]            -> [1]
                      Single non-zero. The swap is a self-swap — the case the
                      guard eliminates.

    [0,0,0]        -> [0,0,0]
                      ALL ZEROES. The swap version performs zero swaps (the
                      `if` never fires). Catches code that assumes w advances.

    [1,2,3]        -> [1,2,3]
                      NO ZEROES. Every iteration is a self-swap. This is the
                      case the follow-up is about.

    [0,0,1]        -> [1,0,0]
                      Zeroes at the FRONT, so the single non-zero must travel
                      the whole way. Verifies the swap carries a zero rightward
                      rather than overwriting.

    [1,0,0]        -> [1,0,0]
                      Already correct. Should require no displacement at all.

    [-1,0,-2,0]    -> [-1,-2,0,0]
                      NEGATIVES are non-zero. Code that tested `nums[r] > 0`
                      instead of `!= 0` moves the negatives to the back too.
                      This is the most common wrong predicate here.


================================================================================
COMMON MISTAKES
================================================================================
1. Testing `nums[r] > 0` instead of `nums[r] != 0`. Silently relocates every
   negative number. Caught by [-1,0,-2,0].

2. Using LC 27's swap-from-the-back trick. Fast, but it destroys relative
   order, which this problem forbids.

3. `nums = [...]` instead of `nums[:] = [...]`. Rebinds a local; the caller's
   array is untouched. Especially nasty here because the function returns None,
   so there is no return value to look wrong.

4. Returning the array. The signature returns None; LeetCode checks the
   mutated input. Returning something is not an error but signals you did not
   read the contract.

5. Forgetting phase 2 in the two-phase version, leaving stale leftovers in the
   tail instead of zeroes.

6. Counting zeroes and then writing them at the front instead of the back.

7. `nums.remove(0)` in a loop plus `append(0)` — O(n²) and it mutates while
   iterating.

8. Swapping unconditionally and then claiming "minimum operations" in the
   follow-up. Without the `w != r` guard, an array with no zeroes still does
   2n stores.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Minimise the total number of operations. (The stated follow-up.)
A: The guarded swap. Writes become proportional to the number of non-zeroes
   that actually need to move, so both degenerate inputs (no zeroes, all
   zeroes) cost zero writes. Say the numbers: two-phase is always n writes;
   unguarded swap is 2(n−z); guarded is 2 × displaced.

Q: Move zeroes to the FRONT instead, keeping non-zero order.
A: Mirror it: walk from the right with `w = n-1`, swapping non-zeroes
   rightward. Do not just reverse the array twice — that is 2n extra writes.

Q: Move all instances of an arbitrary value to the end.
A: Replace `!= 0` with `!= val`. Identical code — the same generalisation as
   LC 27, which is why these three problems are really one problem.

Q: Stable partition by an arbitrary predicate, in O(1) space?
A: This IS that, for a two-way split. For a three-way split it is Dutch
   National Flag (LC 75), but note DNF is NOT stable. A general stable
   in-place partition in O(n) time and O(1) space is not achievable with this
   technique — you would need O(n) space or O(n log n) time (block swapping).
   Knowing that boundary is a strong answer.

Q: The array is huge and on disk / in a memory-mapped file.
A: Then writes dominate everything and the guarded swap's advantage becomes
   the whole ballgame — each avoided write is an avoided dirty page.


================================================================================
RELATED PROBLEMS — the in-place compaction family
================================================================================
    LC 26   Remove Duplicates from Sorted Array — problem 003 in this folder
    LC 27   Remove Element             — problem 004; note the ORDER-FREE
                                          licence that this problem lacks
    LC 75   Sort Colors                — three-way partition, NOT stable
    LC 905  Sort Array By Parity       — two-way partition, order free
    LC 88   Merge Sorted Array         — read/write BACKWARDS, because the
                                          free space is at the end
    LC 2460 Apply Operations to an Array — do a transform, then move zeroes;
                                          literally this problem as a subroutine
    LC 1089 Duplicate Zeros            — the reverse operation, and it must be
                                          done right-to-left for the same
                                          overwrite reason as LC 88
================================================================================
"""

import time
from typing import List


class Solution:
    def moveZeroes(self, nums: List[int]) -> None:
        """Guarded one-pass swap. O(n) time, O(1) space, minimal writes.

        Modifies nums IN PLACE and returns None.
        """
        w = 0                                  # index of the leftmost zero
        for r in range(len(nums)):
            if nums[r] != 0:                   # != 0, NOT > 0 (negatives count)
                if w != r:                     # skip the no-op self-swap
                    nums[w], nums[r] = nums[r], nums[w]
                w += 1

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def moveZeroes_two_phase(self, nums: List[int]) -> None:
        """Compact, then fill. Always exactly n writes."""
        w = 0
        for r in range(len(nums)):
            if nums[r] != 0:
                nums[w] = nums[r]
                w += 1
        for i in range(w, len(nums)):
            nums[i] = 0

    def moveZeroes_swap_unguarded(self, nums: List[int]) -> None:
        """One-pass swap with no w != r guard. 2(n - z) writes."""
        w = 0
        for r in range(len(nums)):
            if nums[r] != 0:
                nums[w], nums[r] = nums[r], nums[w]
                w += 1

    def moveZeroes_sort(self, nums: List[int]) -> None:
        """Stable sort on truthiness. Correct, but O(n log n)."""
        nums.sort(key=bool, reverse=True)

    def moveZeroes_positive_bug(self, nums: List[int]) -> None:
        """✗ BROKEN ON PURPOSE — tests > 0 instead of != 0."""
        w = 0
        for r in range(len(nums)):
            if nums[r] > 0:                    # THE BUG: negatives are non-zero
                if w != r:
                    nums[w], nums[r] = nums[r], nums[w]
                w += 1

    def moveZeroes_rebind_bug(self, nums: List[int]) -> None:
        """✗ BROKEN ON PURPOSE — rebinds the parameter name."""
        nums = [x for x in nums if x != 0] + [0] * nums.count(0)


# ==============================================================================
# TESTS — run:  python 005_move_zeroes_solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ([0, 1, 0, 3, 12], [1, 3, 12, 0, 0]),
        ([0], [0]),
        ([1], [1]),
        ([0, 0, 0], [0, 0, 0]),
        ([1, 2, 3], [1, 2, 3]),
        ([0, 0, 1], [1, 0, 0]),
        ([1, 0, 0], [1, 0, 0]),
        ([4, 2, 4, 0, 0, 3, 0, 5, 1, 0], [4, 2, 4, 3, 5, 1, 0, 0, 0, 0]),
        ([-1, 0, -2, 0], [-1, -2, 0, 0]),
        ([0, -1], [-1, 0]),
        ([0, 0, 1, 0, 2], [1, 2, 0, 0, 0]),
    ]
    impls = [
        ("guarded swap  ", sol.moveZeroes),
        ("two phase     ", sol.moveZeroes_two_phase),
        ("swap unguarded", sol.moveZeroes_swap_unguarded),
        ("sort(key=bool)", sol.moveZeroes_sort),
    ]
    all_ok = True
    for name, fn in impls:
        ok = True
        for nums, exp in cases:
            arr = list(nums)
            ret = fn(arr)
            ok &= (arr == exp and ret is None)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(cases)} cases)")

    # ----------------------------------------------------------------------
    # The swap walk, and the two invariants.
    # ----------------------------------------------------------------------
    print("\n--- swap walk for [0,1,0,3,12] ---")
    nums = [0, 1, 0, 3, 12]
    w = 0
    print(f"  {'r':>2} {'nums[r]':>8} {'action':<22} {'w':>2}  array")
    print(f"  {'-':>2} {'-':>8} {'start':<22} {w:>2}  {nums}")
    for r in range(len(nums)):
        if nums[r] != 0:
            act = f"swap slots {w} and {r}" if w != r else "self-swap, skipped"
            if w != r:
                nums[w], nums[r] = nums[r], nums[w]
            w += 1
        else:
            act = "zero, leave it"
        print(f"  {r:>2} {nums[r]:>8} {act:<22} {w:>2}  {nums}")
    print(f"  invariants at the end:  nums[:{w}] = {nums[:w]} (non-zeroes, in order)")
    print(f"                          nums[{w}:] = {nums[w:]} (all zero)")

    # ----------------------------------------------------------------------
    # ⚠️  `> 0` instead of `!= 0`.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  testing `> 0` instead of `!= 0` ---")
    print(f"  {'input':<24} {'correct':<22} {'with > 0':<22} ok?")
    for probe in ([-1, 0, -2, 0], [0, -1], [1, 2, 3], [-5, -6], [0, 1, 0, 3, 12]):
        a, b = list(probe), list(probe)
        sol.moveZeroes(a)
        sol.moveZeroes_positive_bug(b)
        print(f"  {str(probe):<24} {str(a):<22} {str(b):<22} "
              f"{'yes' if a == b else 'NO  ✗'}")
    print("  `> 0` treats every NEGATIVE number as if it were a zero and shoves")
    print("  it to the back. The constraint allows nums[i] down to -2^31, so")
    print("  negatives are not a corner case — they are half the input space.")

    # ----------------------------------------------------------------------
    # ⚠️  Rebinding the parameter: silent no-op.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  rebinding `nums` inside a function that returns None ---")
    arr = [0, 1, 0, 3, 12]
    ret = sol.moveZeroes_rebind_bug(arr)
    print(f"  after moveZeroes_rebind_bug: {arr}   returned {ret!r}")
    arr2 = [0, 1, 0, 3, 12]
    sol.moveZeroes(arr2)
    print(f"  after moveZeroes:            {arr2}")
    print("  The buggy version computes the RIGHT list and then throws it away.")
    print("  There is no return value and no exception — nothing to notice.")
    print("  Use nums[:] = ... for slice assignment, or write elements directly.")

    # ----------------------------------------------------------------------
    # The follow-up, measured: writes per input shape.
    # ----------------------------------------------------------------------
    print("\n--- 'minimise the total number of operations', counted ---")

    class Counter(list):
        """A list that counts __setitem__ calls."""

        def __init__(self, data):
            super().__init__(data)
            self.writes = 0

        def __setitem__(self, i, v):
            self.writes += 1
            super().__setitem__(i, v)

    n = 1000
    shapes = [
        ("no zeroes", [1] * n),
        ("all zeroes", [0] * n),
        ("already correct", [1] * (n // 2) + [0] * (n // 2)),
        ("worst case (0s first)", [0] * (n // 2) + [1] * (n // 2)),
        ("alternating", [0, 1] * (n // 2)),
    ]
    print(f"  n = {n}")
    print(f"  {'shape':<24} {'two-phase':>10} {'swap':>8} {'guarded swap':>14}")
    for label, data in shapes:
        row = []
        for fn in (sol.moveZeroes_two_phase, sol.moveZeroes_swap_unguarded,
                   sol.moveZeroes):
            c = Counter(data)
            fn(c)
            row.append(c.writes)
        print(f"  {label:<24} {row[0]:>10,} {row[1]:>8,} {row[2]:>14,}")
    print("  two-phase is always exactly n — it writes every slot regardless.")
    print("  unguarded swap pays 2 per non-zero, so it LOSES badly when zeroes")
    print("  are rare (2000 writes vs 1000 on the no-zeroes row).")
    print("  guarded swap is the only one that does no work when no work is")
    print("  needed: 0 writes on both degenerate shapes. That is the follow-up.")

    # ----------------------------------------------------------------------
    # O(n) vs the O(n log n) sort.
    # ----------------------------------------------------------------------
    print("\n--- O(n) vs O(n log n) sort(key=bool) ---")
    import random
    random.seed(3)
    data = [random.choice([0, 0, 1, 2, 3]) for _ in range(200_000)]
    for name, fn in (("guarded swap  ", sol.moveZeroes),
                     ("two phase     ", sol.moveZeroes_two_phase),
                     ("sort(key=bool)", sol.moveZeroes_sort)):
        d = list(data)
        t0 = time.perf_counter()
        fn(d)
        print(f"  {name} {(time.perf_counter() - t0) * 1000:8.1f}ms")
    print("  Read that carefully, because it inverts the usual story:")
    print("   - sort(key=bool) is O(n log n) and the FASTEST here. Timsort is C.")
    print("   - guarded swap does the FEWEST writes and is the SLOWEST. The")
    print("     `if w != r` branch costs more per element than the store it")
    print("     saves, because in CPython a branch is bytecode and a list")
    print("     store is a single C-level pointer write.")
    print("  So 'minimise operations' has two different answers depending on")
    print("  what an operation costs. The guard is right when writes are")
    print("  expensive (mmap'd file, flash, cache-line contention, a language")
    print("  where the element is a big struct). It is wrong in a CPython list")
    print("  of small ints, where writes are nearly free and branches are not.")
    print("  Give the guarded swap as the interview answer — it is what the")
    print("  follow-up asks for — and be able to say when it stops paying off.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
