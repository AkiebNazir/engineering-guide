"""
================================================================================
SOLUTION · LeetCode 167 · Two Sum II - Input Array Is Sorted            [Medium]
https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/
================================================================================

THE CORE IDEA
-------------
Start at both ends and let the sum steer you:

    l, r = 0, len(numbers) - 1
    while l < r:
        s = numbers[l] + numbers[r]
        if s == target: return [l + 1, r + 1]
        if s < target:  l += 1        # need MORE  -> abandon the smallest
        else:           r -= 1        # need LESS  -> abandon the largest

Three lines. The content is not the code — it is the proof that discarding an
endpoint is SAFE. That proof is called the elimination argument, and it is what
the interviewer is listening for.

    THE ELIMINATION ARGUMENT

    numbers = [2, 7, 11, 15]   target = 18
               l           r    s = 2 + 15 = 17 < 18

    The array is SORTED, so:
        numbers[l] is the smallest value still in play
        numbers[r] is the largest  value still in play

    So numbers[l] + numbers[r] is the LARGEST SUM numbers[l] can ever reach
    with any partner still in range. It is 17, and 17 < 18. Every other
    available partner is <= numbers[r], so every other pairing is even
    smaller.

        => numbers[l] can never be half of the answer. Discard it forever.

    Symmetrically, if s > target, numbers[r] paired with the smallest available
    value still overshoots, so numbers[r] is impossible and r -= 1.

Each comparison eliminates exactly one element, so at most n iterations happen.
That is the O(n), and it is why no element ever needs revisiting.

    ⚠️  "I move l because the sum is too small" is a DESCRIPTION.
        "I move l because numbers[l] paired with the largest remaining value
         still falls short, so it cannot work with anything" is the ANSWER.


================================================================================
LC 1 vs LC 167 — the fork you must be able to explain
================================================================================
                         LC 1 (Two Sum)          LC 167 (this problem)
    input                UNSORTED                SORTED
    must return          original indices        1-based positions
    space allowed        O(n)                    O(1) — REQUIRED
    correct tool         HASH MAP                TWO POINTERS
    time                 O(n)                    O(n)

Why you cannot just reuse the LC 1 hash map: it costs O(n) space, which this
problem forbids outright.

Why you cannot just reuse this two-pointer method on LC 1: sorting an unsorted
array DESTROYS the original indices, and LC 1 requires you to return them. You
could sort (value, index) pairs to preserve them — but that is O(n) space for
the pairs and O(n log n) time, strictly worse than the hash map.

    The constraint decides the tool. That sentence is the point of the pair.

Also note what SORTED buys beyond speed: with a hash map you would have to
handle "the same element used twice" explicitly. Here `while l < r` makes it
structurally impossible for the two pointers to land on the same index.


================================================================================
APPROACH 0 · Brute force (state it, price it, move on)
================================================================================
    for i in range(n):
        for j in range(i + 1, n):
            if numbers[i] + numbers[j] == target:
                return [i + 1, j + 1]

    Time: O(n²)   Space: O(1)

At n = 3·10^4 that is ~4.5·10^8 pairs. It is the baseline everything else is
measured against, and it is the only version that ignores sortedness entirely.


================================================================================
APPROACH 1 · Converging two pointers ✅✅ (the answer)
================================================================================

    Time: O(n)   Space: O(1)   Does not mutate the input.

STEP BY STEP for numbers = [2, 7, 11, 15], target = 18:

    l  r   numbers[l]  numbers[r]   sum   vs 18   action
    -  -   ----------  ----------   ---   -----   ----------------------------
    0  3        2          15        17     <     too small -> discard 2, l=1
    1  3        7          15        22     >     too big   -> discard 15, r=2
    1  2        7          11        18     ==    FOUND -> return [2, 3]      ✓

    Note both pointers moved. A greedy rule that only ever moves one of them
    cannot solve this input.

STEP BY STEP for numbers = [1, 3, 4, 5, 7, 11], target = 9:

    l  r   nums[l]  nums[r]   sum   vs 9   action
    -  -   -------  -------   ---   ----   -------------------------
    0  5      1        11      12     >     r=4
    0  4      1         7       8     <     l=1
    1  4      3         7      10     >     r=3
    1  3      3         5       8     <     l=2
    2  3      4         5       9     ==    return [3, 4]                    ✓

    Five iterations for six elements — each one killed exactly one candidate.

WHY THE SEARCH SPACE IS A STAIRCASE, NOT A SQUARE
    Brute force examines the whole n×n grid of pairs. Two pointers walks a
    single monotone path from the top-right corner of that grid to the
    diagonal:

              r →
        l   15  11   7   5   3   1
        ↓  ┌───┬───┬───┬───┬───┬───┐
        1  │ ● │ ● │ ● │   │   │   │     ● = actually examined
        3  │   │   │ ● │ ● │   │   │     the rest is eliminated wholesale,
        4  │   │   │   │ ● │   │   │     never even looked at
        ...

    Every step moves strictly left or strictly down, never back. That is why
    the path length is bounded by n, and it is the same shape of argument you
    will use again in LC 11 and LC 42.

⚠️  `while l < r`, NOT `l <= r`
    With `l <= r` the pointers can land on the same index and you would return
    a "pair" that uses one element twice — which the problem forbids. `l < r`
    makes that structurally impossible, so you need no separate check.

⚠️  BOTH INDICES NEED +1
    The problem is 1-INDEXED. `return [l + 1, r + 1]` — two plus-ones. Adding
    it to only one, or forgetting both, is the most common wrong submission on
    this problem and it is invisible in your head. Write a test with the answer
    at position [1, 2] so an off-by-one cannot hide.

⚠️  NEGATIVES AND DUPLICATES CHANGE NOTHING
    The elimination argument only ever uses "sorted", never "positive" and
    never "distinct". [-10,-8,-2,1,2,5] with target -18 works identically, and
    so does [0,0,3,4] with target 0 (the two zeroes are at distinct indices, so
    `l < r` is satisfied). Nothing special is needed — but be able to say WHY
    nothing special is needed.

⚠️  DO NOT `numbers.sort()` "just in case"
    It is already sorted; the problem says so in its title. Sorting would be
    O(n log n) for nothing, and if you sorted a COPY you would also blow the
    O(1) space requirement.


================================================================================
APPROACH 2 · Binary search for the complement
================================================================================
For each i, binary-search for `target - numbers[i]` in `numbers[i+1:]`:

    Time: O(n log n)   Space: O(1)

Worse than two pointers, but worth knowing for two reasons. First, it is the
natural answer if you have not spotted the converging trick, and it still beats
brute force. Second, it generalises to a case two pointers does NOT handle: if
you had to answer many different targets against the same array, the binary
search version needs no re-walk while the two-pointer version restarts each
time.

Mention it as the fallback, then give the O(n).


================================================================================
APPROACH 3 · Hash map (correct, but it violates the space requirement)
================================================================================
    seen = {}
    for i, v in enumerate(numbers):
        if target - v in seen:
            return [seen[target - v] + 1, i + 1]
        seen[v] = i

    Time: O(n)   Space: O(n)   ← DISQUALIFIED by "constant extra space"

This is the LC 1 answer transplanted. It works, it is the same time complexity,
and it throws away the sortedness. Say "the hash map from Two Sum still solves
this in O(n) time, but the problem caps space at O(1), so the sortedness is the
resource I should be spending instead."


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach              Time         Extra space   Uses sortedness?
    --------------------  -----------  ------------  ----------------
    Brute force           O(n²)        O(1)          no
    Hash map              O(n)         O(n)  ✗       no
    Binary search         O(n log n)   O(1)          yes
    Two pointers    ✅✅  O(n)         O(1)          yes

    Only the last row satisfies both stated requirements. None of them mutate
    the input.


================================================================================
EDGE CASES
================================================================================
    ([1,2], 3)               -> [1,2]
                                MINIMUM LENGTH. l=0, r=1, one iteration.
                                Also the case that exposes a missing +1: the
                                0-indexed answer would be [0,1].

    ([-1,0], -1)             -> [1,2]
                                NEGATIVES at the minimum length. LeetCode's own
                                example 3.

    ([0,0,3,4], 0)           -> [1,2]
                                DUPLICATES, and the two elements are equal.
                                Legal because the INDICES differ. Catches code
                                that guards with `numbers[l] != numbers[r]`.

    ([-10,-8,-2,1,2,5], -18) -> [1,2]
                                Both elements negative. The sum starts at
                                -10 + 5 = -5, which is greater than -18, so
                                the RIGHT pointer does all the moving.

    ([5,25,75], 100)         -> [2,3]
                                Answer sits at the far end; the left pointer
                                does all the moving.

    ([1,3,4,5,7,11], 9)      -> [3,4]
                                BOTH pointers must move, alternating. Defeats
                                any one-sided rule.


================================================================================
COMMON MISTAKES
================================================================================
1. Returning 0-based indices. The problem is 1-indexed and needs +1 on BOTH.

2. `while l <= r`, allowing the same element to pair with itself.

3. Re-sorting the array. It is already sorted; sorting costs O(n log n) and a
   sorted copy costs O(n) space.

4. Using the LC 1 hash map. Correct, but O(n) space — explicitly disallowed.

5. Moving both pointers on a mismatch. You have only proved ONE of them
   impossible; moving both can step over the answer. [1,3,4,5,7,11] target 9
   catches this — see the demo.

6. Moving the wrong pointer (l when the sum is too big). The sum then gets
   even bigger and you march away from the target.

7. Adding a `numbers[l] != numbers[r]` guard to "avoid using the same element".
   The elements may be EQUAL; it is the indices that must differ, and `l < r`
   already guarantees that. [0,0,3,4] target 0 breaks the guarded version.

8. Assuming the answer exists without the guarantee, and falling off the end of
   the function so it returns None. Return `[]` or `[-1,-1]` explicitly if the
   guarantee is lifted.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if the array is NOT sorted? (i.e. LC 1)
A: Hash map, O(n) time and O(n) space, and it returns the original indices.
   Sorting first would destroy those indices unless you sort (value, index)
   pairs — O(n log n) and O(n) space, strictly worse. The constraint picks the
   tool.

Q: What if there are MULTIPLE valid pairs and you must return all of them?
A: Same walk, but on a hit record the pair and then move BOTH pointers inward,
   skipping duplicates on at least one side — exactly the dedupe machinery from
   3Sum. Still O(n).

Q: THREE numbers summing to the target? (LC 15 / LC 16)
A: Fix the first element with an outer loop, then run this exact two-pointer
   scan on the remainder: O(n²). That is 3Sum, and it is the next problem in
   this folder. k-Sum generalises to O(n^(k-1)).

Q: Return the pair whose sum is CLOSEST to the target rather than equal?
A: Same walk; track the best difference seen instead of returning on equality,
   and never terminate early. LC 16 does this for triples.

Q: The array is enormous and lives on disk.
A: Two pointers is ideal — it is two sequential scans from opposite ends, which
   is exactly what spinning disks and read-ahead caches like. A hash map would
   need the whole thing resident.

Q: Prove your loop terminates.
A: Every iteration either returns or strictly decreases (r − l) by one. It
   starts at n−1 and the loop guard fails at 0, so at most n−1 iterations.


================================================================================
RELATED PROBLEMS — the converging-pointer family
================================================================================
    LC 1    Two Sum                  — the unsorted twin; hash map
    LC 15   3Sum                     — outer loop + this scan; problem 007 here
    LC 16   3Sum Closest             — track the best difference; problem 008
    LC 18   4Sum                     — two outer loops + this scan
    LC 11   Container With Most Water— converging pointers, different (and
                                        harder) elimination argument; problem 009
    LC 42   Trapping Rain Water      — the hardest elimination argument in the
                                        topic; problem 010
    LC 653  Two Sum IV (BST)         — same idea over an in-order traversal
    LC 1099 Two Sum Less Than K      — maximise instead of match
================================================================================
"""

import time
from typing import List


class Solution:
    def twoSum(self, numbers: List[int], target: int) -> List[int]:
        """Converging two pointers. O(n) time, O(1) space. Input untouched."""
        l, r = 0, len(numbers) - 1
        while l < r:                          # `<` so the two indices differ
            s = numbers[l] + numbers[r]
            if s == target:
                return [l + 1, r + 1]         # 1-INDEXED: +1 on BOTH
            if s < target:
                l += 1                        # numbers[l] can never reach target
            else:
                r -= 1                        # numbers[r] always overshoots
        return []                             # unreachable: a solution is promised

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def twoSum_bisect(self, numbers: List[int], target: int) -> List[int]:
        """Binary search for each complement. O(n log n), O(1)."""
        import bisect
        n = len(numbers)
        for i in range(n - 1):
            want = target - numbers[i]
            j = bisect.bisect_left(numbers, want, i + 1, n)
            if j < n and numbers[j] == want:
                return [i + 1, j + 1]
        return []

    def twoSum_hashmap(self, numbers: List[int], target: int) -> List[int]:
        """The LC 1 answer. O(n) time but O(n) space — disallowed here."""
        seen = {}
        for i, v in enumerate(numbers):
            if target - v in seen:
                return [seen[target - v] + 1, i + 1]
            seen[v] = i
        return []

    def twoSum_bruteforce(self, numbers: List[int], target: int) -> List[int]:
        """O(n^2) baseline for the benchmark."""
        n = len(numbers)
        for i in range(n):
            for j in range(i + 1, n):
                if numbers[i] + numbers[j] == target:
                    return [i + 1, j + 1]
        return []

    def twoSum_move_both(self, numbers: List[int], target: int) -> List[int]:
        """✗ BROKEN ON PURPOSE — moves both pointers on a mismatch."""
        l, r = 0, len(numbers) - 1
        while l < r:
            s = numbers[l] + numbers[r]
            if s == target:
                return [l + 1, r + 1]
            l += 1                            # THE BUG: only one is proved
            r -= 1                            #          impossible, not both
        return []

    def twoSum_distinct_guard(self, numbers: List[int], target: int) -> List[int]:
        """✗ BROKEN ON PURPOSE — refuses pairs of EQUAL values."""
        l, r = 0, len(numbers) - 1
        while l < r:
            s = numbers[l] + numbers[r]
            if s == target and numbers[l] != numbers[r]:   # THE BUG
                return [l + 1, r + 1]
            if s < target:
                l += 1
            else:
                r -= 1
        return []


# ==============================================================================
# TESTS — run:  python 006_two_sum_ii_input_array_is_sorted_solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ([2, 7, 11, 15], 9, [1, 2]),
        ([2, 3, 4], 6, [1, 3]),
        ([-1, 0], -1, [1, 2]),
        ([1, 2], 3, [1, 2]),
        ([0, 0, 3, 4], 0, [1, 2]),
        ([2, 7, 11, 15], 18, [2, 3]),
        ([5, 25, 75], 100, [2, 3]),
        ([-10, -8, -2, 1, 2, 5], -18, [1, 2]),
        ([-3, 3, 4, 90], 0, [1, 2]),
        ([1, 3, 4, 5, 7, 11], 9, [3, 4]),
        ([1, 2, 3, 4, 4, 9, 56, 90], 8, [4, 5]),
    ]
    impls = [
        ("two pointers ", sol.twoSum),
        ("binary search", sol.twoSum_bisect),
        ("hash map     ", sol.twoSum_hashmap),
        ("brute force  ", sol.twoSum_bruteforce),
    ]
    all_ok = True
    for name, fn in impls:
        ok = all(fn(list(a), t) == e for a, t, e in cases)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(cases)} cases)")

    # ----------------------------------------------------------------------
    # The elimination argument, spelled out step by step.
    # ----------------------------------------------------------------------
    print("\n--- the elimination argument, numbers=[1,3,4,5,7,11] target=9 ---")
    numbers, target = [1, 3, 4, 5, 7, 11], 9
    l, r = 0, len(numbers) - 1
    print(f"  {'l':>2} {'r':>2} {'nums[l]':>8} {'nums[r]':>8} {'sum':>5} "
          f"{'vs':>3}  what it proves")
    while l < r:
        s = numbers[l] + numbers[r]
        if s == target:
            print(f"  {l:>2} {r:>2} {numbers[l]:>8} {numbers[r]:>8} {s:>5} "
                  f"{'==':>3}  FOUND -> return [{l+1}, {r+1}]")
            break
        if s < target:
            why = (f"{numbers[l]} + (its largest possible partner "
                   f"{numbers[r]}) = {s} < {target}, so {numbers[l]} is "
                   f"impossible")
            print(f"  {l:>2} {r:>2} {numbers[l]:>8} {numbers[r]:>8} {s:>5} "
                  f"{'<':>3}  {why}")
            l += 1
        else:
            why = (f"{numbers[r]} + (its smallest possible partner "
                   f"{numbers[l]}) = {s} > {target}, so {numbers[r]} is "
                   f"impossible")
            print(f"  {l:>2} {r:>2} {numbers[l]:>8} {numbers[r]:>8} {s:>5} "
                  f"{'>':>3}  {why}")
            r -= 1

    # ----------------------------------------------------------------------
    # The search space is a path, not a grid.
    # ----------------------------------------------------------------------
    print("\n--- pairs examined: two pointers vs brute force ---")
    print(f"  {'n':>6} {'brute force pairs':>18} {'two-pointer steps':>18} "
          f"{'ratio':>10}")
    for n in (10, 100, 1_000, 30_000):
        # WORST case for two pointers on arr = range(n): put the answer at
        # (0, 1) so the right pointer must walk the entire way down.
        # (Careful: the "centre" target is the BEST case here, not the worst —
        # arr[0] + arr[n-1] == n-1 == arr[n//2-1] + arr[n//2], so a centred
        # answer is found on the very first comparison.)
        arr = list(range(n))
        tgt = arr[0] + arr[1]
        steps = 0
        l, r = 0, n - 1
        while l < r:
            steps += 1
            s = arr[l] + arr[r]
            if s == tgt:
                break
            if s < tgt:
                l += 1
            else:
                r -= 1
        pairs = n * (n - 1) // 2
        print(f"  {n:>6} {pairs:>18,} {steps:>18,} {pairs / steps:>10,.0f}x")
    print("  Brute force walks an n^2 grid; two pointers walks one monotone")
    print("  path across it, so the step count is bounded by n — here exactly")
    print("  n-1, the worst case. The ratio grows linearly with n.")

    # ----------------------------------------------------------------------
    # ⚠️  Moving both pointers steps over the answer.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  moving BOTH pointers on a mismatch ---")
    print(f"  {'input':<30} {'target':>7} {'correct':<10} {'move-both':<11} ok?")
    for a, t, _ in cases[:8]:
        good = sol.twoSum(list(a), t)
        bad = sol.twoSum_move_both(list(a), t)
        print(f"  {str(a):<30} {t:>7} {str(good):<10} {str(bad):<11} "
              f"{'yes' if good == bad else 'NO  ✗'}")
    print("  A mismatch proves exactly ONE endpoint impossible. Discarding both")
    print("  throws away a candidate you never ruled out, and the walk sails")
    print("  straight past the answer.")

    # ----------------------------------------------------------------------
    # ⚠️  The "don't reuse an element" guard, misapplied to VALUES.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  guarding on numbers[l] != numbers[r] ---")
    for a, t in (([0, 0, 3, 4], 0), ([1, 1], 2), ([-2, -2, 5], -4),
                 ([2, 7, 11, 15], 9)):
        good = sol.twoSum(list(a), t)
        bad = sol.twoSum_distinct_guard(list(a), t)
        print(f"  {str(a):<18} target={t:<4} correct {str(good):<8} "
              f"guarded {str(bad):<8} {'' if good == bad else '✗'}")
    print("  The problem forbids reusing the same ELEMENT, not the same VALUE.")
    print("  `l < r` already guarantees two distinct indices; the extra guard")
    print("  only rejects legitimate answers like the two zeroes in [0,0,3,4].")

    # ----------------------------------------------------------------------
    # ⚠️  The +1s.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  the 1-indexed +1, on BOTH indices ---")
    numbers, target = [1, 2], 3
    l, r = 0, 1
    print(f"  numbers={numbers} target={target}: the pair is at 0-based (l={l}, r={r})")
    print(f"    return [l, r]         -> {[l, r]}       ✗ 0-indexed")
    print(f"    return [l + 1, r]     -> {[l + 1, r]}       ✗ only one +1")
    print(f"    return [l + 1, r + 1] -> {[l + 1, r + 1]}       ✓")
    print("  A test whose answer is [1,2] makes all three visibly different.")
    print("  If your only test answer is [2,4], the 'only one +1' bug looks")
    print("  almost right and is easy to miss.")

    # ----------------------------------------------------------------------
    # O(n) vs O(n log n) vs O(n^2).
    # ----------------------------------------------------------------------
    print("\n--- at the constraint size, n = 30000 ---")
    n = 30_000
    arr = list(range(0, n))
    # Probe choice matters enormously, and an unfair probe makes a fast method
    # look slow. Two shapes, labelled:
    #   (0, 1)     -> WORST for two pointers (r walks the whole way down),
    #                 BEST for the hash map and binary search (found at i=1).
    #   (n-2, n-1) -> WORST for all three: every method must traverse the array.
    probes = [
        ("answer at (0, 1)", arr[0] + arr[1]),
        ("answer at (n-2, n-1)", arr[n - 2] + arr[n - 1]),
    ]
    print(f"  {'probe':<24} {'two pointers':>14} {'binary search':>15} "
          f"{'hash map':>11}")
    for label, tgt in probes:
        row = []
        for fn in (sol.twoSum, sol.twoSum_bisect, sol.twoSum_hashmap):
            t0 = time.perf_counter()
            fn(arr, tgt)
            row.append((time.perf_counter() - t0) * 1000)
        print(f"  {label:<24} {row[0]:>12.2f}ms {row[1]:>13.2f}ms "
              f"{row[2]:>9.2f}ms")
    print("  Row 1 flatters the hash map: it hits the answer at i=1 and stops.")
    print("  Row 2 is the honest comparison — all three must cross the array.")
    print("  There, two pointers and the hash map are NECK AND NECK (the hash")
    print("  map is often marginally ahead: its loop is a C-level dict store")
    print("  per element, while two pointers runs more interpreted branches).")
    print("  Binary search is clearly last — it really does pay the log n.")
    print()
    print("  So two pointers does NOT win on wall clock here. It wins on SPACE:")
    print("  O(1) versus O(n), which is the requirement the problem actually")
    print("  states. That is the honest case for it — not a speed claim.")
    print()
    small = list(range(3_000))
    t0 = time.perf_counter()
    sol.twoSum_bruteforce(small, small[-2] + small[-1])   # worst case: last pair
    t_bf = time.perf_counter() - t0
    print(f"  brute force, worst case, n=3000 (10x smaller): {t_bf * 1000:7.1f}ms")
    print(f"  quadratic, so n=30000 would be ~100x that = ~{t_bf * 100:.1f}s")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
