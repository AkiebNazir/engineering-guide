"""
================================================================================
SOLUTION · LeetCode 384 · Shuffle an Array                          [Medium]
https://leetcode.com/problems/shuffle-an-array/
================================================================================

THE CORE IDEA
--------------
Fisher-Yates (Knuth) shuffle: walk the array from the LAST index down to 1.
At step i, swap arr[i] with arr[j] where j is drawn uniformly from [0, i]
(the SHRINKING range of "not yet placed" slots). After each swap, index i
is finalized and never touched again.

Why this is uniform (proof sketch, by induction on the number of steps
finalized so far): before touching index n-1, every element is equally
likely (1/n) to be chosen for slot n-1, because j is uniform over all n
indices. After that swap, slot n-1 is fixed, and the remaining n-1 elements
are still in a uniformly random ORDER among themselves (nothing about the
swap that placed n-1 favored any relative ordering of the rest) -- so by
induction, applying the same argument to the shrinking prefix places every
remaining element in its slot with the correct probability too. The product
of these independent conditional probabilities is exactly 1/n! for any
target permutation.

O(n) time, O(1) extra space beyond the array itself.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (looks random, is NOT uniform -- name it, price it, do not ship
it): at each step i (from the end backwards, or even forwards), swap
arr[i] with arr[random.randrange(0, n)] -- i.e. draw the random index from
the FULL range every time instead of the shrinking range [0, i]. This is
still O(n) time and looks identical at a glance to Fisher-Yates. It is
NOT uniform: some permutations end up systematically more likely than
others, because early swaps can be "undone" by later ones in a
probability-imbalanced way. This is the single most common way this
problem goes wrong, and the bug is invisible without a frequency count --
see the runtime demo below, which actually counts permutation frequencies
over 100,000 trials on a 3-element array to expose the bias.

Approach 1 (chosen) -- Fisher-Yates, shrinking range [0, i] at each step i.
O(n) time, O(1) extra space. This is the only approach shipped in
`Solution`; the naive-range variant is kept ONLY as `_naive_shuffle_biased`
to power the comparison demo, never as the real `shuffle()`.


================================================================================
STEP BY STEP TRACE
================================================================================
arr = [1, 2, 3], indices 0, 1, 2. Fisher-Yates walks i from 2 down to 1.

    start:           [1, 2, 3]
    i=2: j=random in [0,2], say j=0
         swap arr[2], arr[0]     -> [3, 2, 1]
         slot 2 is now FINAL (holds 1)
    i=1: j=random in [0,1], say j=1
         swap arr[1], arr[1]     -> [3, 2, 1]   (no-op swap, j happened to equal i)
         slot 1 is now FINAL (holds 2)
    i=0: loop stops (range is down to i=1, exclusive of 0 -- nothing left
         to place, slot 0 gets whatever remains: 3)

    final: [3, 2, 1]

Each of the 3! = 6 permutations of [1,2,3] is reachable by exactly one
sequence of j-choices, and each sequence of j-choices has equal
probability (1/3 * 1/2), so every permutation has probability 1/6.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Operation                Time    Space   Mutates input?
    ------------------------  ------  ------  --------------
    __init__                  O(n)    O(n)    stores a COPY, does not mutate
    reset()                   O(n)    O(n)    returns a copy of the original
    shuffle() [Fisher-Yates]  O(n)    O(1)*   mutates internal array in place
                                              (*beyond the array itself)


================================================================================
EDGE CASES
================================================================================
    n == 1                 -> loop range is empty, shuffle() is a no-op,
                              still correctly "uniform" (only 1 permutation
                              exists).
    repeated shuffle() calls without reset() -> each call re-shuffles from
                              whatever the PREVIOUS shuffled state was, not
                              the original -- correct per the LC contract
                              (only reset() restores the original).
    reset() before any shuffle() -> must still return the original
                              unmodified array.
    negative numbers / large magnitude values -> shuffling permutes
                              positions, never touches the VALUES, so this
                              is a non-issue as long as equality comparisons
                              use value, not identity.


================================================================================
COMMON MISTAKES
================================================================================
1. Drawing the random index from the FULL range [0, n) at every step
   instead of the shrinking range [0, i] -- looks correct, silently biases
   the distribution (see runtime demo).
2. Storing a reference to the caller's original list instead of a COPY in
   __init__ -- then shuffle() corrupts the "original" and reset() can never
   recover it.
3. Calling Python's `random.shuffle()` directly and treating that as "the
   solution" without understanding it IS Fisher-Yates under the hood --
   fine to use in production code, but an interviewer asking this question
   wants you to implement and justify the algorithm, not name-drop a
   library call.
4. Off-by-one in the loop range: `for i in range(n-1, 0, -1)` swaps with
   `random.randint(0, i)` INCLUSIVE of i -- using `random.randrange(0, i)`
   (exclusive of i) instead silently shrinks the eligible range by one too
   many and biases the result.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Prove this is uniform." -> the induction argument above: at each step,
  every not-yet-placed element has equal probability of landing in the
  current slot, and this compounds multiplicatively to 1/n! per permutation.
- "Can you do it without extra space for the copy?" -> no, `reset()`
  requires remembering the original; the shuffle step ITSELF is O(1) extra
  space, just the stored original costs O(n).
- "What if nums has duplicate values?" -> Fisher-Yates still produces a
  uniform permutation of POSITIONS; duplicate values just make some
  resulting arrays indistinguishable from others, which does not affect
  correctness of the algorithm.


================================================================================
RELATED PROBLEMS
================================================================================
- 002 Random Pick Index (LC 398) -- reservoir sampling, same "prove
  uniformity" discipline, different technique.
- 003 Linked List Random Node (LC 382) -- reservoir sampling over a stream.
- Random Pick with Weight (LC 528) -- weighted uniform sampling.
================================================================================
"""

import random
import time
from collections import Counter


class Solution:
    def __init__(self, nums: list[int]):
        self._original = list(nums)
        self._array = list(nums)

    def reset(self) -> list[int]:
        self._array = list(self._original)
        return self._array

    def shuffle(self) -> list[int]:
        arr = self._array
        n = len(arr)
        for i in range(n - 1, 0, -1):
            j = random.randint(0, i)  # inclusive of i -- correct shrinking range
            arr[i], arr[j] = arr[j], arr[i]
        return arr


def _naive_shuffle_biased(arr: list[int]) -> list[int]:
    """The 'looks random, isn't uniform' trap: draws j from the FULL range
    every step instead of the shrinking [0, i] range."""
    n = len(arr)
    arr = list(arr)
    for i in range(n - 1, 0, -1):
        j = random.randint(0, n - 1)  # BUG: full range, not [0, i]
        arr[i], arr[j] = arr[j], arr[i]
    return arr


def run_tests() -> None:
    all_ok = True

    sol = Solution([1, 2, 3])

    got = sol.reset()
    ok = got == [1, 2, 3]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  reset() -> {got}  (want [1, 2, 3])")

    shuffled = sol.shuffle()
    ok = sorted(shuffled) == [1, 2, 3]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  shuffle() is a permutation -> {shuffled}")

    got = sol.reset()
    ok = got == [1, 2, 3]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  reset() after shuffle -> {got}  (want [1, 2, 3])")

    # single-element edge case
    sol1 = Solution([42])
    ok = sol1.shuffle() == [42] and sol1.reset() == [42]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  n=1 shuffle/reset no-op")

    print()
    print("RUNTIME DEMO -- frequency table over 100,000 trials, n=3, measured live")
    print("-" * 72)
    trials = 100_000
    base = [1, 2, 3]

    t0 = time.perf_counter()
    fy_counts = Counter()
    fy_sol = Solution(base)
    for _ in range(trials):
        fy_sol.reset()
        fy_counts[tuple(fy_sol.shuffle())] += 1
    fy_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    naive_counts = Counter()
    for _ in range(trials):
        naive_counts[tuple(_naive_shuffle_biased(base))] += 1
    naive_ms = (time.perf_counter() - t0) * 1000

    expected = trials / 6  # 6 = 3! permutations
    print(f"expected count per permutation if uniform: {expected:.1f}\n")

    print("Fisher-Yates (shrinking range) frequencies:")
    fy_max_dev = 0.0
    for perm in sorted(fy_counts):
        count = fy_counts[perm]
        dev_pct = abs(count - expected) / expected * 100
        fy_max_dev = max(fy_max_dev, dev_pct)
        print(f"  {perm} -> {count:6d}  (dev {dev_pct:5.1f}%)")

    print("\nNaive full-range 'shuffle' frequencies:")
    naive_max_dev = 0.0
    for perm in sorted(naive_counts):
        count = naive_counts[perm]
        dev_pct = abs(count - expected) / expected * 100
        naive_max_dev = max(naive_max_dev, dev_pct)
        print(f"  {perm} -> {count:6d}  (dev {dev_pct:5.1f}%)")

    print(f"\nmax deviation from uniform: Fisher-Yates {fy_max_dev:.1f}%  "
          f"vs  naive {naive_max_dev:.1f}%")
    print(f"timing: Fisher-Yates {fy_ms:.1f} ms   naive {naive_ms:.1f} ms  "
          f"over {trials} trials each")

    # The naive full-range variant is a KNOWN-BIASED algorithm: some
    # permutations occur far more often than others because early swaps
    # get partially "undone" in a probability-imbalanced way. Assert that
    # this demo actually reproduces that bias (not just measures noise),
    # while Fisher-Yates stays close to uniform.
    bias_reproduced = naive_max_dev > 3 * fy_max_dev
    all_ok &= bias_reproduced
    print(f"{'PASS' if bias_reproduced else 'FAIL'}  "
          f"naive deviation is clearly larger than Fisher-Yates' -> "
          f"{naive_max_dev:.1f}% vs {fy_max_dev:.1f}%")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
