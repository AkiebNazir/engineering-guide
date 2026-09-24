"""
================================================================================
SOLUTION · LeetCode 862 · Shortest Subarray with Sum at Least K          [Hard]
https://leetcode.com/problems/shortest-subarray-with-sum-at-least-k/
================================================================================

THE CORE IDEA
--------------
Three topics collide in this one problem, and the whole difficulty is knowing
which tool each one contributes and which one it RETIRES.

    topic 03  sliding window   ->  INVALID here. Negatives break it.
    topic 04  prefix sums      ->  the right reformulation, but O(n^2) alone.
    topic 07  monotonic deque  ->  what restores O(n).

Step 1 — reformulate with prefix sums. With `prefix[0] = 0` and
`prefix[i] = nums[0] + ... + nums[i-1]`:

    sum(nums[l .. r-1]) = prefix[r] - prefix[l] >= k
                    <=>   prefix[l] <= prefix[r] - k

So for each right end `r`, you want the LARGEST index `l < r` whose prefix is
at most `prefix[r] - k`. Largest `l`, because `r - l` is the length and you
want it small.

Step 2 — notice that most `l` candidates are DEAD, permanently. Keep a deque of
candidate indices whose prefix values are strictly increasing, and both pruning
rules fall out of a domination argument rather than cleverness:

    FRONT  while dq and prefix[r] - prefix[dq[0]] >= k:
               best = min(best, r - dq.popleft())
           dq[0] is a VALID left end right now. Record the length and throw it
           away FOREVER: for every future r' > r the length r' - dq[0] is
           strictly longer. It has already produced its best answer.

    BACK   while dq and prefix[dq[-1]] >= prefix[r]:
               dq.pop()
           dq[-1] is DOMINATED ON BOTH AXES by r: r is more recent (shorter
           subarrays) and its prefix is smaller-or-equal (easier to satisfy
           `<= prefix[r'] - k`). Anything dq[-1] could ever win, r wins better.

Every index is appended once and removed at most once, from one end or the
other, so the total deque traffic is at most 2n operations. O(n). The tests
below COUNT those operations at n = 100,000 rather than asserting the bound.

WHY SLIDING WINDOW IS NOT MERELY SLOWER — IT IS WRONG
------------------------------------------------------
This is the sentence to have ready. A sliding window's shrink step
(`while sum >= k: record; sum -= nums[l]; l += 1`) is only sound when validity
is MONOTONE under growth: extending the right end can only push the sum in one
direction, so a left end that fails today can never be needed again. That is
true for LC 209 (all values positive) and false here, because `nums[i]` may be
as low as -100,000. With a negative in the array the sum is not monotone in the
window's right end, so "the window is currently too small, grow it" and "the
window is currently big enough, shrink it" stop being complementary — a left
end you discarded can become the best answer several elements later.

Two DIFFERENT failure modes show up, and the tests print both:

    nums = [84,-37,32,40,95], k = 167  -> window says 5, truth is 3
                                          (it answers, but too long)
    nums = [-28,81,-20,28,-29], k = 89 -> window says -1, truth is 3
                                          (it misses the answer entirely)

The second is the dangerous one: it reports "no such subarray" for an input
that has one. That is the demo to remember from this file.

================================================================================
MULTIPLE APPROACHES
================================================================================

1. ALL PAIRS (l, r), PRICED WITH PREFIX SUMS         (brute force — the baseline)
   Two nested loops over prefix indices, O(1) per pair thanks to the prefix
   array. O(n^2) time, O(n) space. Correct for every sign pattern, which is
   why the tests use it as the oracle. At n = 100,000 it is ~10^10 pair tests
   — hours. Priced and coded here ONLY because it is the oracle.

2. SLIDING WINDOW (topic 03's LC 209 solution, verbatim)              ✗ WRONG
   O(n) and beautiful, and it silently returns wrong answers. Coded on purpose
   below, and run side by side with the truth. Never state "sliding window
   doesn't work here" without being able to produce the counterexample.

3. PREFIX SUMS + SORTED CONTAINER + BINARY SEARCH               O(n log n)
   Keep the same strictly-increasing candidate list, but instead of popping
   the front, `bisect` it for the largest prefix <= prefix[r] - k. Correct,
   and a completely respectable interview answer if you get there first. The
   deque is strictly better, and the benchmark below shows by how much.

4. PREFIX SUMS + MONOTONIC DEQUE                                <- the answer
   O(n) time, O(n) space, two `while` loops, ten lines.

5. DIVIDE AND CONQUER / SEGMENT TREE OVER PREFIX MINIMA
   Build a segment tree of prefix minima and, for each r, descend to find the
   rightmost `l` with `prefix[l] <= prefix[r] - k`. O(n log n), far more code,
   no advantage. Worth naming as "yes, there are other O(n log n) routes" and
   then not writing.

================================================================================
STEP BY STEP  ·  nums = [84, -37, 32, 40, 95],  k = 167
================================================================================

    index    0    1    2    3    4
    nums    84  -37   32   40   95
    prefix   0   84   47   79  119  214       (prefix has n+1 = 6 entries)
             ^i=0 ^1   ^2   ^3   ^4   ^5

The deque holds INDICES INTO PREFIX, never into nums. Length of the subarray
answered by the pair (l, r) is r - l.

    i=0  p=0     front: deque empty
                 back : deque empty
                 push 0                                   dq=[0]        prefix: [0]

    i=1  p=84    front: 84 - prefix[0] = 84 < 167   stop
                 back : prefix[0]=0 < 84            keep
                 push 1                                   dq=[0,1]      prefix: [0,84]

    i=2  p=47    front: 47 - 0 = 47 < 167           stop
                 back : prefix[1]=84 >= 47   -> POP 1     dq=[0]
                        index 1 is dominated: index 2 is later AND its prefix
                        is smaller. No future r would ever prefer 1 over 2.
                        prefix[0]=0 < 47            keep
                 push 2                                   dq=[0,2]      prefix: [0,47]

    i=3  p=79    front: 79 - 0 = 79 < 167           stop
                 back : prefix[2]=47 < 79           keep
                 push 3                                   dq=[0,2,3]    prefix: [0,47,79]

    i=4  p=119   front: 119 - 0 = 119 < 167         stop
                 back : prefix[3]=79 < 119          keep
                 push 4                                   dq=[0,2,3,4]  prefix: [0,47,79,119]

    i=5  p=214   front: 214 - prefix[0] = 214 >= 167
                        -> best = 5 - 0 = 5, POPLEFT 0
                        214 - prefix[2] = 214 - 47 = 167 >= 167
                        -> best = min(5, 5 - 2) = 3, POPLEFT 2
                        214 - prefix[3] = 214 - 79 = 135 < 167   stop
                 back : prefix[4]=119 < 214         keep
                 push 5                                   dq=[3,4,5]

    best = 3   ->   nums[2..4] = [32, 40, 95],  sum = 167.  Correct.

NOTE THE TWO POPS AT i=5. That is why the front pruning must be a `while` and
not an `if`: the first pop found a length-5 answer, the second improved it to
3. An `if` would have returned 5 — a real answer, just not the shortest. There
is a runtime demo below that reproduces exactly that off-by-a-loop bug.

Now run the sliding window on the same input and watch it fail:

    l=0  r=0  sum=84                      84 < 167
    l=0  r=1  sum=47                      47 < 167
    l=0  r=2  sum=79                      79 < 167
    l=0  r=3  sum=119                    119 < 167
    l=0  r=4  sum=214                    214 >= 167 -> record length 5
              shrink: 214 - nums[0] = 130 < 167 -> STOP shrinking, l stays 0
    answer 5.

The window never considers starting at index 2, because its only test of
index 0 is local: "does dropping nums[0] keep me above k?" It does not, so
l stays at 0 forever and index 2 is never tried as a left end.

The deque, by contrast, is holding index 0 AND index 2 simultaneously at i=5
(prefix[0] = 0 and prefix[2] = 47 — neither dominates the other, since 2 is
more recent but its prefix is larger), and it examines BOTH. That is precisely
the capability a single left pointer cannot have: **more than one live left-end
candidate at a time.** With non-negative values the prefix array is
non-decreasing, so a later index always has a larger-or-equal prefix and can
never dominate an earlier one for the `<= prefix[r] - k` test — the earliest
surviving candidate is always the only one that matters, which is exactly why
one pointer suffices there and not here.

================================================================================
COMPLEXITY SUMMARY
================================================================================

    Approach                        Time         Space   Mutates input?  Correct?
    ------------------------------  -----------  ------  --------------  --------
    All pairs + prefix sums         O(n^2)       O(n)    no              yes
    Sliding window (topic 03)       O(n)         O(1)    no              NO
    Prefix + bisect over candidates O(n log n)   O(n)    no              yes
    Prefix + monotonic deque  ✅     O(n)         O(n)    no              yes
    Segment tree over prefix minima O(n log n)   O(n)    no              yes

    None of these mutate `nums`; the prefix array is a fresh allocation. If the
    interviewer asks for O(1) extra space, say plainly that it is impossible for
    this problem in the deque formulation — the deque can hold all n+1 indices
    (any strictly increasing array, e.g. [1,1,1,...], never triggers a back
    pop), so O(n) is a genuine lower bound for this approach.

    The O(n) claim for the deque is an AMORTIZED accounting argument, and the
    thing to say out loud: "the inner `while` loops look like they make this
    quadratic, but each index is pushed exactly once and popped at most once
    across the entire run, so total deque work is bounded by 2(n+1) regardless
    of how the loops distribute." The tests count the operations to confirm it.

================================================================================
EDGE CASES
================================================================================

    [1], k=1             -> 1. Single element that itself suffices. Catches an
                            off-by-one in `prefix` indexing: the answer uses
                            l=0, r=1.

    [1,2], k=4           -> -1. No answer exists at all; `best` must stay at
                            its sentinel and be translated to -1. A solution
                            that initialises `best = 0` or forgets the
                            translation returns 0 or n+1 here.

    [2,-1,2], k=3        -> 3. The whole array, and only via the negative in
                            the middle. This is the smallest input where the
                            negative actually matters.

    [-1,-1,-1], k=1      -> -1. All negative, so no prefix ever climbs by k.
                            The front `while` must never fire.

    [-28,81,-20,28,-29], k=89 -> 3. The sliding window returns -1 here. Keep
                            this input; it is the counterexample worth
                            memorising.

    all values equal and positive, e.g. [1]*8, k=4 -> 4. prefix is strictly
                            increasing, so the BACK loop never pops anything
                            and the deque grows to full size n+1. This is the
                            worst case for the deque's memory and the reason
                            the space bound is O(n), not O(1).

    k = 10^9, huge nums  -> Python ints are arbitrary precision, so there is no
                            overflow story here. Say so explicitly if asked;
                            in C++/Java `prefix` must be `long long`/`long`,
                            because 10^5 elements at 10^5 each is 10^10, well
                            past a 32-bit int.

================================================================================
COMMON MISTAKES
================================================================================

1. Reaching for a sliding window because the wording matches LC 209.
   The two statements are identical except for the sign constraint, and the
   sign constraint is the entire problem. Read `-10^5 <= nums[i]` first, every
   time. Demonstrated live below: it returns 5 instead of 3 on one input and
   -1 instead of 3 on another.

2. `if` instead of `while` on the FRONT pop.
   Several deque-front indices can all become valid at the same `r` when the
   prefix jumps. The `if` version records only the first (longest) of them.
   It returns a legal subarray length, never crashes, and is simply not the
   minimum — the worst kind of bug. Reproduced below on [1,1,1,100], k=4,
   where it answers 4 instead of 1.

3. Indices into `nums` instead of into `prefix`.
   The deque stores `l` values, and `l` ranges over 0..n inclusive — n+1
   possible values, not n. Mixing the two index spaces produces off-by-one
   answers on almost every input, most visibly on single-element arrays.

4. Recording `i - dq[0]` after the popleft, or `i - dq.popleft() + 1`.
   The length is `r - l` exactly (not `r - l + 1`), because `prefix[r]` is the
   sum of the first r elements — the subarray is `nums[l .. r-1]`. Do the +1
   version and every answer is one too big.

5. Popping the back with `<=` / `<` instead of `>=`.
   `prefix[dq[-1]] >= prefix[r]` is the domination test. Inverting it pops the
   good candidates and keeps the dominated ones, which breaks the invariant and
   the answers with it.

6. Forgetting to push `i` after the pops, or pushing before the pops.
   The order is: answer with the front, prune the back, THEN push. Pushing
   first makes the back loop pop the element you just added (`prefix[i] >=
   prefix[i]` is true), silently emptying the deque.

7. Assuming `>` also works on the back pop and that `>=` is load-bearing for
   correctness.
   Measured below: with a `while` front loop, `>` is still CORRECT — equal
   prefixes are both consumed at the same `r` and `min` picks the shorter. It
   is a waste of deque slots, not a bug. Worth knowing exactly which of the two
   comparisons you can be sloppy about and which you cannot (#5 you cannot).

8. Believing a sorted list plus `bisect` is asymptotically the same "because
   log n is small". It is O(n log n) and it is measurably slower here — see the
   benchmark — but it is the correct fallback if you cannot see the deque
   argument under pressure. Say that out loud instead of freezing.

================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================

Q: What changes if all `nums[i] >= 0`?
A: Then the prefix array is non-decreasing, the back-pop `while` never fires,
   the deque degenerates to "all indices in order", and the algorithm becomes
   exactly LC 209's sliding window with extra steps. Use the window: O(1)
   space instead of O(n). This is the right answer to "which of the two do I
   write?" — check the sign constraint, then pick.

Q: LONGEST subarray with sum at least k instead of shortest?
A: You now want the SMALLEST valid `l`, not the largest, and the front-pop
   "throw it away forever" argument dies (an early `l` stays useful). Build the
   monotonic candidate stack of prefix MINIMA left-to-right, then scan `r` from
   the RIGHT and pop. That is LC 1124 (Longest Well-Performing Interval), which
   is exactly this problem with k = 1 over a +1/-1 transform.

Q: Shortest subarray with sum EXACTLY k, negatives allowed?
A: Different tool: prefix sum + hashmap of last-seen index (topic 04's LC 560
   machinery, but storing the most recent index rather than a count). Equality
   is a lookup; inequality is a search. That distinction is the whole reason
   this problem needs a deque and LC 560 does not.

Q: Sum at most k?
A: Flip the sign of every element and it becomes "sum at least -k". Same code.

Q: Return the subarray itself, not just its length.
A: Keep `(best, best_l, best_r)` instead of `best`, updating all three
   together. No change to the algorithm or its complexity.

Q: The array arrives as a stream and k is fixed — can you answer online?
A: Yes, unchanged: the algorithm is already one left-to-right pass with O(1)
   amortized work per element. Prefix sums are computed incrementally, and the
   deque holds only live candidates. You cannot bound the deque below O(n) for
   an adversarial (increasing) stream, so memory is the only concession.

Q: Multiple queries with different k on the same array?
A: The deque's pruning is k-dependent (the front test uses k), so you cannot
   reuse one pass. Precompute the strictly-increasing prefix-minima candidate
   list ONCE — that part is k-independent — then binary search it per query:
   O(n) preprocessing plus O(n log n) per query, or O(log n) per (r, k) pair.

Q: Parallelise it?
A: Prefix sums are a textbook parallel scan (O(log n) depth). The deque pass is
   inherently sequential, but a divide-and-conquer variant works: solve each
   half, then handle crossing subarrays with the merge step. More code, and the
   sequential pass is already optimal for one machine.

================================================================================
RELATED PROBLEMS — the pattern family
================================================================================

    THE DECIDING QUESTION IS ALWAYS: are the values non-negative?

    LC 209  Minimum Size Subarray Sum      - topic 03/008. Same words, positive
                                             values, so sliding window. This is
                                             the problem this one is a trap for.
    LC 862  Shortest Subarray Sum >= K     - HERE. Negatives, so prefix + deque.
    LC 1124 Longest Well-Performing        - the LONGEST twin; monotone stack of
            Interval                         prefix minima, scanned from the
                                             right.
    LC 560  Subarray Sum Equals K          - topic 04/004. Equality, so hashmap.
    LC 974  Subarray Sums Divisible by K   - topic 04/007. Equality mod k.

    SAME MONOTONIC DEQUE MECHANISM, different quantity in the deque:
    LC 239  Sliding Window Maximum         - deque over VALUES, fixed window.
                                             The purest form of the mechanism.
    LC 1438 Longest Subarray with Abs Diff - TWO deques at once (max and min).
            <= Limit
    LC 84   Largest Rectangle in Histogram - topic 06. Monotonic STACK: the same
                                             domination argument with one end.

    The tell for a monotonic deque: you need the best candidate in a window
    that only ever slides forward, and you can prove that a candidate beaten on
    BOTH "how good" and "how recent" is dead forever. If you can state that
    two-axis domination argument for your problem, the deque is correct.
================================================================================
"""

import random
import time
from bisect import bisect_right
from collections import deque
from typing import List


class Solution:
    def shortestSubarray(self, nums: List[int], k: int) -> int:
        """Prefix sums + monotonic deque. O(n) time, O(n) space. The answer."""
        n = len(nums)
        prefix = [0] * (n + 1)
        for i, x in enumerate(nums):
            prefix[i + 1] = prefix[i] + x

        dq: deque = deque()          # indices into prefix, increasing prefix values
        best = n + 1
        for i, p in enumerate(prefix):
            # FRONT: answer, then discard permanently — must be a while.
            while dq and p - prefix[dq[0]] >= k:
                best = min(best, i - dq.popleft())
            # BACK: drop candidates dominated on both axes by i.
            while dq and prefix[dq[-1]] >= p:
                dq.pop()
            dq.append(i)
        return best if best <= n else -1

    # ------------------------------------------------------------------
    # Alternatives, kept for the comparisons the tests run.
    # ------------------------------------------------------------------
    def shortestSubarray_brute(self, nums: List[int], k: int) -> int:
        """O(n^2) over all (l, r) pairs, each priced O(1) by the prefix array.
        Correct for every sign pattern — the oracle."""
        n = len(nums)
        prefix = [0] * (n + 1)
        for i, x in enumerate(nums):
            prefix[i + 1] = prefix[i] + x
        best = n + 1
        for r in range(1, n + 1):
            pr = prefix[r]
            # scan l DOWNWARD from r-1: the first hit is the largest valid l,
            # i.e. the shortest subarray ending at r, so we can stop there.
            for l in range(r - 1, -1, -1):
                if pr - prefix[l] >= k:
                    best = min(best, r - l)
                    break
        return best if best <= n else -1

    def shortestSubarray_bisect(self, nums: List[int], k: int) -> int:
        """O(n log n): keep the SAME strictly-increasing candidate list, but
        binary search it instead of popping the front. Correct, and the honest
        fallback if the deque argument does not come to you."""
        n = len(nums)
        prefix = [0] * (n + 1)
        for i, x in enumerate(nums):
            prefix[i + 1] = prefix[i] + x

        idx: List[int] = []        # candidate indices, prefix values increasing
        vals: List[int] = []       # prefix[idx[j]], kept parallel for bisect
        best = n + 1
        for i, p in enumerate(prefix):
            # largest candidate prefix <= p - k  ->  rightmost, i.e. largest l
            j = bisect_right(vals, p - k) - 1
            if j >= 0:
                best = min(best, i - idx[j])
            while vals and vals[-1] >= p:
                vals.pop()
                idx.pop()
            vals.append(p)
            idx.append(i)
        return best if best <= n else -1

    # ------------------------------------------------------------------
    # Deliberately broken — the tests prove these are wrong at runtime.
    # ------------------------------------------------------------------
    def shortestSubarray_sliding_window(self, nums: List[int], k: int) -> int:
        """✗ WRONG ON PURPOSE — topic 03's LC 209 sliding window, verbatim.
        Sound only when every value is non-negative. Two different failure
        modes are demonstrated below."""
        n = len(nums)
        best = n + 1
        left = 0
        total = 0
        for right in range(n):
            total += nums[right]
            while total >= k:
                best = min(best, right - left + 1)
                total -= nums[left]
                left += 1
        return best if best <= n else -1

    def shortestSubarray_front_if(self, nums: List[int], k: int) -> int:
        """✗ BROKEN ON PURPOSE — MISTAKE 2: the front pop is an `if`, so only
        the FIRST (longest) of several simultaneously-valid left ends is used."""
        n = len(nums)
        prefix = [0] * (n + 1)
        for i, x in enumerate(nums):
            prefix[i + 1] = prefix[i] + x
        dq: deque = deque()
        best = n + 1
        for i, p in enumerate(prefix):
            if dq and p - prefix[dq[0]] >= k:        # BUG: `if`, not `while`
                best = min(best, i - dq.popleft())
            while dq and prefix[dq[-1]] >= p:
                dq.pop()
            dq.append(i)
        return best if best <= n else -1

    def shortestSubarray_back_strict(self, nums: List[int], k: int) -> int:
        """MISTAKE 7 candidate — back pop uses `>` instead of `>=`, so equal
        prefixes are all kept. Is it wrong, or only wasteful? Measured below;
        do not guess."""
        n = len(nums)
        prefix = [0] * (n + 1)
        for i, x in enumerate(nums):
            prefix[i + 1] = prefix[i] + x
        dq: deque = deque()
        best = n + 1
        for i, p in enumerate(prefix):
            while dq and p - prefix[dq[0]] >= k:
                best = min(best, i - dq.popleft())
            while dq and prefix[dq[-1]] > p:          # `>` not `>=`
                dq.pop()
            dq.append(i)
        return best if best <= n else -1


def _oracle(nums: List[int], k: int) -> int:
    """Independent O(n^2) reference written a different way from the one in
    Solution: no early break, plain double loop over every (l, r)."""
    n = len(nums)
    prefix = [0] * (n + 1)
    for i, x in enumerate(nums):
        prefix[i + 1] = prefix[i] + x
    best = n + 1
    for r in range(1, n + 1):
        for l in range(r):
            if prefix[r] - prefix[l] >= k:
                best = min(best, r - l)
    return best if best <= n else -1


CASES = [
    ([1], 1),
    ([1, 2], 4),
    ([2, -1, 2], 3),
    ([84, -37, 32, 40, 95], 167),
    ([-28, 81, -20, 28, -29], 89),
    ([1, 2, 3, 4, 5], 11),
    ([-1, -1, -1], 1),
    ([5, -5, 5], 5),
    ([1, 1, 1, 1, 1, 1, 1, 1], 4),
    ([1, 1, 1, 100], 4),
    ([17], 100),
    ([-1, 2, -1, 2, -1, 2], 3),
]


# ==============================================================================
# TESTS — run:  python 006_shortest_subarray_with_sum_at_least_k_solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    all_ok = True

    # ----------------------------------------------------------------------
    # 1. Correctness of the three CORRECT implementations, vs the oracle.
    # ----------------------------------------------------------------------
    print("--- correctness vs the O(n^2) all-pairs oracle ---")
    impls = [
        ("prefix + monotonic deque ", sol.shortestSubarray),
        ("prefix + all pairs       ", sol.shortestSubarray_brute),
        ("prefix + bisect (n log n)", sol.shortestSubarray_bisect),
    ]
    for name, fn in impls:
        ok = True
        for nums, k in CASES:
            want = _oracle(nums, k)
            got = fn(list(nums), k)
            if got != want:
                ok = False
                print(f"      nums={nums} k={k}: got {got} want {want}")
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # ----------------------------------------------------------------------
    # 2. ⚠️ THE DEMO — sliding window vs the deque, side by side.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  sliding window (topic 03) vs prefix+deque (topic 07) ---")
    print(f"  {'nums':<28} {'k':>5} {'truth':>6} {'window':>7} {'deque':>6}  verdict")
    window_wrong = 0
    for nums, k in CASES:
        truth = _oracle(nums, k)
        win = sol.shortestSubarray_sliding_window(list(nums), k)
        dqa = sol.shortestSubarray(list(nums), k)
        bad = win != truth
        window_wrong += bad
        verdict = "window WRONG" if bad else "agree"
        print(f"  {str(nums):<28} {k:>5} {truth:>6} {win:>7} {dqa:>6}  {verdict}")
    print(f"  the sliding window is wrong on {window_wrong}/{len(CASES)} of these"
          f" cases; the deque on 0.")
    print("  Read the two failure modes: on [84,-37,32,40,95] it returns a")
    print("  subarray that is too LONG; on [-28,81,-20,28,-29] it returns -1 for")
    print("  an input that has a valid answer of length 3. The second is the one")
    print("  that will cost you the interview — 'no solution exists' is a much")
    print("  more confident wrong answer than 'here is a longer one'.")
    all_ok &= window_wrong >= 2

    # ----------------------------------------------------------------------
    # 3. How often is the window wrong on random data with negatives?
    # ----------------------------------------------------------------------
    print("\n--- randomised differential: how often does the window lie? ---")
    random.seed(862)
    print(f"  {'value range':<22} {'trials':>7} {'window wrong':>13} "
          f"{'deque wrong':>12} {'bisect wrong':>13}")
    for lo, hi, label in ((0, 9, "non-negative [0,9]"),
                          (-2, 9, "mostly positive"),
                          (-9, 9, "mixed [-9,9]"),
                          (-9, 2, "mostly negative")):
        trials = 400
        w_bad = d_bad = b_bad = 0
        for _ in range(trials):
            n = random.randint(1, 12)
            nums = [random.randint(lo, hi) for _ in range(n)]
            k = random.randint(1, 20)
            truth = _oracle(nums, k)
            w_bad += sol.shortestSubarray_sliding_window(nums, k) != truth
            d_bad += sol.shortestSubarray(nums, k) != truth
            b_bad += sol.shortestSubarray_bisect(nums, k) != truth
        print(f"  {label:<22} {trials:>7} {w_bad:>13} {d_bad:>12} {b_bad:>13}")
        all_ok &= (d_bad == 0 and b_bad == 0)
        if lo >= 0:
            all_ok &= (w_bad == 0)
    print("  The window is exactly right on non-negative data (that is LC 209)")
    print("  and starts lying the moment a negative can appear. It is not")
    print("  'usually fine' — the failure rate above is the measured number.")

    # ----------------------------------------------------------------------
    # 4. ⚠️ MISTAKE 2 — `if` instead of `while` on the front pop.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  front pop: `while` vs `if` ---")
    print(f"  {'nums':<28} {'k':>5} {'while (right)':>14} {'if (wrong)':>11}")
    if_bug = 0
    for nums, k in ([1, 1, 1, 100], 4), ([1, 1, 1, 1, 50], 3), ([2, -1, 2], 3), \
                   ([1, 2, 3, 4, 5], 11):
        good = sol.shortestSubarray(list(nums), k)
        bad = sol.shortestSubarray_front_if(list(nums), k)
        if_bug += good != bad
        print(f"  {str(nums):<28} {k:>5} {good:>14} {bad:>11}"
              f"{'   <- too long' if good != bad else ''}")
    print(f"  reproduced on {if_bug} of 4 inputs. On [1,1,1,100] with k=4 the")
    print("  prefix jumps from 3 to 103 in one step, so FOUR left ends become")
    print("  valid at the same r. The `while` walks all four and lands on")
    print("  length 1; the `if` takes only the first and reports 4.")
    all_ok &= if_bug >= 1

    # ----------------------------------------------------------------------
    # 5. Back pop: is `>` actually a bug, or only wasteful? MEASURED.
    # ----------------------------------------------------------------------
    print("\n--- back pop `>=` vs `>`: correctness AND deque size, measured ---")
    random.seed(7)
    strict_wrong = 0
    for _ in range(3000):
        n = random.randint(1, 14)
        nums = [random.choice([-2, -1, 0, 0, 1, 1, 2]) for _ in range(n)]
        k = random.randint(1, 8)
        if sol.shortestSubarray_back_strict(nums, k) != _oracle(nums, k):
            strict_wrong += 1
    print(f"  3000 randomised inputs with many equal prefixes: `>` disagreed")
    print(f"  with the oracle {strict_wrong} times.")

    def peak_deque(nums, k, strict):
        prefix = [0] * (len(nums) + 1)
        for i, x in enumerate(nums):
            prefix[i + 1] = prefix[i] + x
        dq: deque = deque()
        peak = 0
        for i, p in enumerate(prefix):
            while dq and p - prefix[dq[0]] >= k:
                dq.popleft()
            if strict:
                while dq and prefix[dq[-1]] > p:
                    dq.pop()
            else:
                while dq and prefix[dq[-1]] >= p:
                    dq.pop()
            dq.append(i)
            peak = max(peak, len(dq))
        return peak

    flat = [0] * 2000                      # every prefix identical
    print(f"  peak deque size on [0]*2000, k=1:  `>=` keeps "
          f"{peak_deque(flat, 1, False)}, `>` keeps {peak_deque(flat, 1, True)}")
    print("  So `>` is NOT a correctness bug here, and this is worth being")
    print("  precise about: because the FRONT pop is a `while`, every one of the")
    print("  equal-prefix duplicates is examined at the same r and `min` picks")
    print("  the shortest. What `>` costs is memory — it retains every duplicate")
    print("  instead of one. Contrast MISTAKE 5 (inverting the back test), which")
    print("  IS a correctness bug. Know which comparison is load-bearing.")
    all_ok &= (strict_wrong == 0)

    # ----------------------------------------------------------------------
    # 6. The O(n) accounting argument, counted rather than asserted.
    # ----------------------------------------------------------------------
    print("\n--- deque operations vs n (the amortized argument, counted) ---")

    def count_ops(nums, k):
        prefix = [0] * (len(nums) + 1)
        for i, x in enumerate(nums):
            prefix[i + 1] = prefix[i] + x
        dq: deque = deque()
        pushes = pops = 0
        for i, p in enumerate(prefix):
            while dq and p - prefix[dq[0]] >= k:
                dq.popleft()
                pops += 1
            while dq and prefix[dq[-1]] >= p:
                dq.pop()
                pops += 1
            dq.append(i)
            pushes += 1
        return pushes, pops

    print(f"  {'n':>8} {'shape':<20} {'pushes':>8} {'pops':>8} {'total':>8} {'2(n+1)':>8}")
    random.seed(1)
    shapes = [
        ("increasing (worst)", lambda n: [1] * n),
        ("decreasing", lambda n: [-1] * n),
        ("random mixed", lambda n: [random.randint(-100, 100) for _ in range(n)]),
        ("big jumps", lambda n: [1 if i % 50 else 5000 for i in range(n)]),
    ]
    bound_ok = True
    for n in (10_000, 100_000):
        for label, gen in shapes:
            nums = gen(n)
            pu, po = count_ops(nums, 1000)
            bound_ok &= (pu + po) <= 2 * (n + 1)
            print(f"  {n:>8} {label:<20} {pu:>8} {po:>8} {pu + po:>8} "
                  f"{2 * (n + 1):>8}")
    print("  Every row is at or under 2(n+1): pushed once, popped at most once.")
    print("  The nested `while` loops cannot make this quadratic no matter what")
    print("  the data looks like — that IS the proof, and it is the same")
    print("  accounting as topic 03's sliding window and topic 06's monotonic")
    print("  stack.")
    all_ok &= bound_ok

    # ----------------------------------------------------------------------
    # 7. Wall clock: deque vs bisect vs brute.
    # ----------------------------------------------------------------------
    print("\n--- wall clock (ms), random values in [-100, 100], k = 500 ---")
    print(f"  {'n':>8} {'deque O(n)':>12} {'bisect O(n log n)':>19} "
          f"{'brute O(n^2)':>14} {'brute/deque':>12}")
    random.seed(42)
    for n in (1_000, 2_000, 4_000):
        nums = [random.randint(-100, 100) for _ in range(n)]
        t0 = time.perf_counter(); sol.shortestSubarray(nums, 500)
        t1 = time.perf_counter(); sol.shortestSubarray_bisect(nums, 500)
        t2 = time.perf_counter(); _oracle(nums, 500)
        t3 = time.perf_counter()
        d_ms, b_ms, br_ms = (t1 - t0) * 1e3, (t2 - t1) * 1e3, (t3 - t2) * 1e3
        print(f"  {n:>8} {d_ms:>11.2f}ms {b_ms:>18.2f}ms {br_ms:>13.2f}ms "
              f"{br_ms / d_ms:>11.0f}x")

    print("\n--- the deque at LeetCode's maximum input size ---")
    random.seed(5)
    big = [random.randint(-100_000, 100_000) for _ in range(100_000)]
    t0 = time.perf_counter()
    ans = sol.shortestSubarray(big, 1_000_000)
    t1 = time.perf_counter()
    print(f"  n = 100,000, k = 1,000,000 -> {ans} in {(t1 - t0) * 1e3:.1f} ms")
    print("  The brute force on the same input would be ~5*10^9 pair tests.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
