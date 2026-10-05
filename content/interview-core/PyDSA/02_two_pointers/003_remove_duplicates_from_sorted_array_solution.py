"""
================================================================================
SOLUTION · LeetCode 26 · Remove Duplicates from Sorted Array              [Easy]
https://leetcode.com/problems/remove-duplicates-from-sorted-array/
================================================================================

THE CORE IDEA
-------------
Two facts, and the code writes itself:

    SORTED  ->  duplicates are ADJACENT, so you only ever compare against ONE
                previous value. No set. O(1) space.
    IN PLACE->  you cannot shrink an array, so "remove" means COMPACT the
                survivors to the front and return how many there are.

The mechanism is a READ pointer and a WRITE pointer, both moving forward:

    w = 1                                  # next slot to fill; nums[0] always stays
    for r in range(1, len(nums)):
        if nums[r] != nums[w - 1]:         # a value we have not kept yet
            nums[w] = nums[r]
            w += 1
    return w

    THE INVARIANT:  w <= r,  always.

That inequality is the whole reason this is safe. The write pointer only
advances when the read pointer does, and it starts no further ahead — so you
never overwrite a cell you have not already read. No temporary buffer is
needed, which is what makes it O(1) space.

    nums = [0, 0, 1, 1, 1, 2, 2, 3, 3, 4]

           w↓ r↓
           [0, 0, 1, 1, 1, 2, 2, 3, 3, 4]   r=1: 0 == nums[0], skip
              w↓  r↓
           [0, 0, 1, ...]                    r=2: 1 != 0  -> write at w=1
           [0, 1, 1, ...]  w=2
                                             ... and so on

    final: [0, 1, 2, 3, 4, |2, 3, 3, 4]      return 5
            └── valid ────┘ └─ garbage ─┘

THE PATTERN — "read/write pointers" or "slow/fast" — solves every in-place
compaction problem: remove duplicates, remove a value, move zeroes, partition.
Recognise it by the phrase "in place" plus "return the new length".


================================================================================
APPROACH 0 · Build a new list (what you must NOT do — and why)
================================================================================
    out = list(dict.fromkeys(nums))     # or sorted(set(nums))
    nums[:] = out
    return len(out)

Correct output, and `dict.fromkeys` even preserves order. But it allocates an
O(n) structure, which defeats the point of "in place" — the problem exists to
test whether you can compact without extra memory. Also `sorted(set(nums))`
throws away the fact that the input is ALREADY sorted, paying O(n log n) for
information you were handed for free.

Say it in one sentence to show you know the shortcut exists, then write the
real answer.


================================================================================
APPROACH 1 · Read/write pointers ✅✅ (the answer)
================================================================================

    if not nums:                       # not needed here (n >= 1) but harmless
        return 0
    w = 1
    for r in range(1, len(nums)):
        if nums[r] != nums[w - 1]:
            nums[w] = nums[r]
            w += 1
    return w

    Time:  O(n)      Space: O(1)      MUTATES the input (by design)

STEP BY STEP for nums = [0,0,1,1,1,2,2,3,3,4]:

    r   nums[r]  nums[w-1]  new?   action              w   array state
    --  -------  ---------  -----  ------------------  --  --------------------
    -      -         -        -    start               1   [0,0,1,1,1,2,2,3,3,4]
    1      0         0        no   skip                1   [0,0,1,1,1,2,2,3,3,4]
    2      1         0        YES  nums[1] = 1         2   [0,1,1,1,1,2,2,3,3,4]
    3      1         1        no   skip                2   [0,1,1,1,1,2,2,3,3,4]
    4      1         1        no   skip                2   [0,1,1,1,1,2,2,3,3,4]
    5      2         1        YES  nums[2] = 2         3   [0,1,2,1,1,2,2,3,3,4]
    6      2         2        no   skip                3   [0,1,2,1,1,2,2,3,3,4]
    7      3         2        YES  nums[3] = 3         4   [0,1,2,3,1,2,2,3,3,4]
    8      3         3        no   skip                4   [0,1,2,3,1,2,2,3,3,4]
    9      4         3        YES  nums[4] = 4         5   [0,1,2,3,4,2,2,3,3,4]

    return 5.  nums[:5] == [0,1,2,3,4]                                       ✓
    nums[5:] == [2,2,3,3,4] is GARBAGE — the caller must not look at it.

⚠️  START AT w = 1, NOT w = 0
    With `w = 0` the first comparison is `nums[0] != nums[-1]`, and Python
    reads `nums[-1]` as the LAST element rather than raising — so you are
    comparing the FIRST element against the LAST one.

    When they differ, the test says "new", slot 0 gets written, and the whole
    thing accidentally produces the right answer. When they are EQUAL, the test
    says "not new", nothing is written, and the function returns 0:

        [5,5,5]   ->  nums[0] != nums[-1]  is  5 != 5  ->  False  ->  k = 0  ✗

    So it works on [1,1,2] and on [0,0,...,4] and fails on any array that
    begins and ends with the same value. A bug that passes the problem's own
    examples is the kind that ships. Same negative-index hazard as LC 125.

    The reason w = 1 is correct: the first element has nothing before it, so it
    is unique by definition and is already in the right place.

⚠️  `nums[w-1]` vs `nums[r-1]` — BOTH WORK HERE, AND THAT IS A COINCIDENCE
    Compare against the last KEPT value (`nums[w-1]`) or the previous READ
    value (`nums[r-1]`)? For this problem they are equivalent, because a run of
    equal values means the previous read is either the kept one or an exact
    copy of it.

    They stop being equivalent the moment you allow k copies (LC 80). There the
    test becomes `nums[r] != nums[w - k]`, which is a statement about the
    OUTPUT, and `nums[r-1]` — a statement about the INPUT — cannot express it.

    Prefer `nums[w-1]`. It generalises, and it keeps you thinking about the
    array you are building rather than the one you are consuming.

⚠️  THE TAIL IS GARBAGE, AND THAT IS THE CONTRACT
    After the loop, `nums[w:]` holds leftovers from the original array. That is
    explicitly allowed. Do NOT "tidy up" by padding with zeroes or by calling
    `del nums[w:]` — the former is wasted work, and the latter changes the
    array's length, which is exactly what the in-place contract says you cannot
    rely on doing.

⚠️  `nums = something` DOES NOT MUTATE THE CALLER'S LIST
    Rebinding the local name is invisible outside the function. To write
    through to the caller you must either assign to elements (`nums[w] = ...`)
    or use slice assignment (`nums[:] = ...`). This is the #1 Python-specific
    trap on every "in place" problem; the demo at the bottom shows it live.


================================================================================
APPROACH 2 · The general "at most k copies" template (LC 80)
================================================================================
One character different, and it covers the whole family:

    def keep_at_most(nums, k):
        w = 0
        for x in nums:
            if w < k or x != nums[w - k]:
                nums[w] = x
                w += 1
        return w

    k = 1  ->  LC 26 (this problem)
    k = 2  ->  LC 80 (Remove Duplicates from Sorted Array II)

Why it works: `nums[w-k]` is the value k slots back IN THE OUTPUT. If the
incoming value differs from it, fewer than k copies have been written, so
there is room for another. The `w < k` guard handles the start, where there are
not yet k elements to look back at — and it also prevents the negative index
that would otherwise silently wrap.

Learn this form. It is strictly more useful than memorising LC 26 alone, and
being able to produce LC 80 instantly from it is a good signal.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                   Time         Extra space   Mutates input?
    -------------------------  -----------  ------------  --------------
    dict.fromkeys / set        O(n)/O(nlogn)  O(n)        via nums[:] =
    Read/write pointers  ✅✅  O(n)         O(1)          YES (by design)
    Generalised k-copies       O(n)         O(1)          YES

    Writes performed: exactly (number of unique values − 1) in the worst case,
    and 0 when the array has no duplicates at all... except that the naive form
    writes `nums[w] = nums[r]` even when w == r, which is a redundant
    self-assignment. Guarding with `if w != r` avoids it but costs a branch per
    element; on a Python list it is not worth it. On a huge array of large
    objects in another language, it might be. Mention the trade if asked.


================================================================================
EDGE CASES
================================================================================
    [1]              -> k=1, [1]
                        Single element. The loop body never runs; w stays 1.

    [1,1,1,1]        -> k=1, [1]
                        All identical. Nothing is ever written; w stays 1.
                        Catches code that unconditionally advances w.

    [1,2,3]          -> k=3, [1,2,3]
                        No duplicates. Every element is written, and every
                        write is `nums[r] = nums[r]` — a self-assignment.
                        Harmless, but see the complexity note above.

    [-100,-100,0,100]-> k=3, [-100,0,100]
                        NEGATIVE VALUES. They are only data here, never
                        indices, so nothing special happens — but this case
                        catches anyone who tried to use the value as an index
                        (an index-as-hash instinct carried over from LC 448).

    [2,2,3]          -> k=2, [2,3]
                        Duplicate at the FRONT. Confirms w = 1 is the right
                        start: nums[0] is kept without being compared.


================================================================================
COMMON MISTAKES
================================================================================
1. Starting `w = 0`, so the first comparison reads `nums[-1]` — the last
   element. No exception, silent corruption.

2. Using a `set` or `dict`. Correct but O(n) space, and it ignores the
   sortedness you were given.

3. `nums = list(dict.fromkeys(nums))` — rebinds the local name; the caller sees
   nothing. Must be `nums[:] = ...`.

4. Calling `nums.remove(v)` or `del nums[i]` inside a loop over the same list.
   Each deletion is O(n) (everything shifts), making it O(n²), AND mutating a
   list while iterating it skips elements.

5. Returning `w - 1` or `len(nums)` instead of `w`. `w` is already the count.

6. "Cleaning up" the tail. It is meant to be garbage.

7. Comparing `nums[r] != nums[r+1]` (looking forward) and running off the end
   on the last element.

8. Assuming the input is sorted when the problem does not say so. Here it does —
   quote it, because the whole O(1)-space argument rests on it.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Allow at most TWO copies of each element. (LC 80)
A: Approach 2 with k = 2: `if w < 2 or x != nums[w-2]`. One character of real
   change from the k=1 case.

Q: What if the array is NOT sorted?
A: Then duplicates are not adjacent and O(1) space is impossible in general —
   you need a set, O(n) space. Or sort first for O(n log n) time and O(1)
   space, but that destroys the original order, which the problem here requires
   you to preserve. Naming that trade-off IS the answer.

Q: Preserve original order, unsorted input, O(1) space?
A: Not achievable in linear time. You would need O(n²) — for each candidate,
   rescan the kept prefix. State the lower bound rather than hunting for a
   trick that does not exist.

Q: Return the removed elements too?
A: Swap instead of overwrite: `nums[w], nums[r] = nums[r], nums[w]`. Then the
   tail holds exactly the discarded values instead of arbitrary leftovers.
   Costs nothing extra and is strictly more informative — a nice thing to
   offer unprompted.

Q: The data is a linked list rather than an array. (LC 83)
A: Same logic, easier: relink `node.next = node.next.next` to drop a duplicate.
   No compaction is needed because a list CAN shrink, which is precisely the
   difference that makes the array version awkward.


================================================================================
RELATED PROBLEMS — the in-place compaction family
================================================================================
    LC 80   Remove Duplicates II       — at most 2 copies; approach 2, k=2
    LC 27   Remove Element             — same skeleton, different predicate;
                                          problem 004 in this folder
    LC 283  Move Zeroes                — compaction plus a zero-fill tail;
                                          problem 005 in this folder
    LC 83   Remove Duplicates from Sorted List — the linked-list version
    LC 75   Sort Colors                — three-way partition, Dutch national
                                          flag: read/write with TWO writers
    LC 88   Merge Sorted Array         — read/write running BACKWARDS, because
                                          the free space is at the end
    LC 905  Sort Array By Parity       — partition with the same skeleton
================================================================================
"""

from typing import List


class Solution:
    def removeDuplicates(self, nums: List[int]) -> int:
        """Read/write pointers. Time O(n), space O(1). MUTATES nums."""
        if not nums:
            return 0
        w = 1                                  # nums[0] is always unique
        for r in range(1, len(nums)):
            if nums[r] != nums[w - 1]:         # differs from the last KEPT value
                nums[w] = nums[r]
                w += 1
        return w

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def keep_at_most(self, nums: List[int], k: int) -> int:
        """Generalised template. k=1 is LC 26, k=2 is LC 80."""
        w = 0
        for x in nums:
            if w < k or x != nums[w - k]:
                nums[w] = x
                w += 1
        return w

    def removeDuplicates_prev_read(self, nums: List[int]) -> int:
        """Compares against the previous READ instead of the last KEPT."""
        if not nums:
            return 0
        w = 1
        for r in range(1, len(nums)):
            if nums[r] != nums[r - 1]:
                nums[w] = nums[r]
                w += 1
        return w

    def removeDuplicates_w0(self, nums: List[int]) -> int:
        """✗ BROKEN ON PURPOSE — w starts at 0, so nums[-1] is read."""
        w = 0
        for r in range(len(nums)):
            if nums[r] != nums[w - 1]:         # r=0, w=0 -> nums[-1] == LAST elem
                nums[w] = nums[r]
                w += 1
        return w


# ==============================================================================
# TESTS — run:  python 003_remove_duplicates_from_sorted_array_solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ([1, 1, 2], 2, [1, 2]),
        ([0, 0, 1, 1, 1, 2, 2, 3, 3, 4], 5, [0, 1, 2, 3, 4]),
        ([1], 1, [1]),
        ([1, 1, 1, 1], 1, [1]),
        ([1, 2, 3], 3, [1, 2, 3]),
        ([-100, -100, 0, 100], 3, [-100, 0, 100]),
        ([1, 2, 2], 2, [1, 2]),
        ([2, 2, 3], 2, [2, 3]),
        ([1, 1, 2, 2, 3, 3], 3, [1, 2, 3]),
    ]
    impls = [
        ("read/write   ", sol.removeDuplicates),
        ("prev-read    ", sol.removeDuplicates_prev_read),
        ("generalised k=1", lambda a: sol.keep_at_most(a, 1)),
    ]
    all_ok = True
    for name, fn in impls:
        ok = True
        for nums, want_k, want_prefix in cases:
            arr = list(nums)
            k = fn(arr)
            ok &= (k == want_k and arr[:k] == want_prefix)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(cases)} cases)")

    # ----------------------------------------------------------------------
    # Watch w and r move, and watch the tail turn to garbage.
    # ----------------------------------------------------------------------
    print("\n--- read/write walk for [0,0,1,1,1,2,2,3,3,4] ---")
    nums = [0, 0, 1, 1, 1, 2, 2, 3, 3, 4]
    w = 1
    print(f"  {'r':>2} {'nums[r]':>8} {'nums[w-1]':>10} {'new?':>5} {'w':>3}  array")
    print(f"  {'-':>2} {'-':>8} {'-':>10} {'-':>5} {w:>3}  {nums}")
    for r in range(1, len(nums)):
        prev_kept = nums[w - 1]
        is_new = nums[r] != prev_kept
        if is_new:
            nums[w] = nums[r]
            w += 1
        print(f"  {r:>2} {nums[r] if not is_new else nums[w-1]:>8} {prev_kept:>10} "
              f"{'YES' if is_new else 'no':>5} {w:>3}  {nums}")
    print(f"  return {w}")
    print(f"  valid   nums[:{w}] = {nums[:w]}")
    print(f"  garbage nums[{w}:]  = {nums[w:]}   <- the caller must ignore this")

    # ----------------------------------------------------------------------
    # The invariant that makes in-place overwriting safe.
    # ----------------------------------------------------------------------
    print("\n--- the invariant: w <= r, always ---")
    nums = [0, 0, 1, 1, 1, 2, 2, 3, 3, 4]
    w = 1
    violations = 0
    rows = []
    for r in range(1, len(nums)):
        if nums[r] != nums[w - 1]:
            nums[w] = nums[r]
            w += 1
        violations += (w > r)
        rows.append(f"r={r} w={w}")
    print(f"  {'  '.join(rows)}")
    print(f"  w > r ever? {bool(violations)}")
    print("  Because w never overtakes r, every slot you write has already been")
    print("  read. That is why no temporary buffer is needed — and it is the")
    print("  one sentence to say when asked 'why is overwriting safe here?'.")

    # ----------------------------------------------------------------------
    # ⚠️  w = 0 silently reads nums[-1].
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  starting w at 0 instead of 1 ---")
    for probe in ([1, 1, 2], [0, 0, 1, 1, 1, 2, 2, 3, 3, 4], [5, 5, 5]):
        a, b = list(probe), list(probe)
        k_good = sol.removeDuplicates(a)
        k_bad = sol.removeDuplicates_w0(b)
        flag = "" if (k_good == k_bad and a[:k_good] == b[:k_bad]) else "   ✗"
        print(f"  {str(probe):<30} w=1 -> k={k_good} {a[:k_good]}"
              f"    w=0 -> k={k_bad} {b[:k_bad]}{flag}")
    print("  With w=0, the very first test is `nums[0] != nums[-1]` — it compares")
    print("  the FIRST element against the LAST. No IndexError; Python is happy")
    print("  to read nums[-1].")
    print("  It then breaks exactly when first == last, because the test says")
    print("  'not new' and slot 0 is never written: [5,5,5] returns k=0.")
    print("  When first != last it accidentally works, which is why this bug")
    print("  survives casual testing — the two example inputs above both pass.")

    # ----------------------------------------------------------------------
    # ⚠️  Rebinding vs mutating — the in-place trap.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  `nums = ...` does not reach the caller ---")

    def rebind(nums):
        nums = list(dict.fromkeys(nums))       # rebinds the LOCAL name only
        return len(nums)

    def slice_assign(nums):
        uniq = list(dict.fromkeys(nums))
        nums[:] = uniq + nums[len(uniq):]      # writes THROUGH to the caller
        return len(uniq)

    for fn, label in ((rebind, "nums = ...   "), (slice_assign, "nums[:] = ... ")):
        arr = [1, 1, 2, 2, 3]
        k = fn(arr)
        print(f"  {label} returned k={k}, caller sees {arr}"
              f"{'   ✗ unchanged!' if arr == [1, 1, 2, 2, 3] else ''}")

    # ----------------------------------------------------------------------
    # ⚠️  del/remove inside the loop is O(n^2) AND skips elements.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  deleting while iterating skips elements ---")
    print(f"  {'start':<22} {'want':<14} {'got (mutating in the loop)':<28} ok?")
    for start in ([2, 2, 4, 4, 6], [1, 1, 2, 2, 3, 3], [1, 2, 2, 3]):
        bad = list(start)
        for x in bad:                          # mutating the list being iterated
            if x % 2 == 0:
                bad.remove(x)
        want = [v for v in start if v % 2]
        print(f"  {str(start):<22} {str(want):<14} {str(bad):<28} "
              f"{'yes' if bad == want else 'NO  ✗'}")
    print("  The iterator holds an INDEX. Deleting shifts everything left, so")
    print("  the next element slides into the slot just consumed and is never")
    print("  visited. Every survivor after a deletion is a coin flip.")
    print("  Each .remove() is also O(n), so the whole loop is O(n^2).")
    print("  Read/write pointers have neither problem: nothing is ever deleted.")

    # ----------------------------------------------------------------------
    # The generalised template covers LC 80 for free.
    # ----------------------------------------------------------------------
    print("\n--- one template, any k (k=2 is LC 80) ---")
    print(f"  {'input':<28} {'k=1':<20} {'k=2':<22} k=3")
    for probe in ([1, 1, 1, 2, 2, 3], [0, 0, 1, 1, 1, 1, 2, 3, 3], [5, 5, 5, 5]):
        out = []
        for k in (1, 2, 3):
            a = list(probe)
            n = sol.keep_at_most(a, k)
            out.append(f"{a[:n]}")
        print(f"  {str(probe):<28} {out[0]:<20} {out[1]:<22} {out[2]}")
    print("  `x != nums[w-k]` asks 'are there already k copies in the OUTPUT?'.")
    print("  Comparing against nums[r-1] (the INPUT) cannot express that — which")
    print("  is why nums[w-1] is the form worth memorising.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
