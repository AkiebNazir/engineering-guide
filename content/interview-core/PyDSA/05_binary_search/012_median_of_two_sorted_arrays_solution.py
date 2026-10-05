"""
================================================================================
SOLUTION · LeetCode 4 · Median of Two Sorted Arrays                      [Hard]
https://leetcode.com/problems/median-of-two-sorted-arrays/
================================================================================

THE CORE IDEA
--------------
Every other problem in this folder binary-searches for a VALUE (Family A,
an index into a sorted array) or for an ANSWER (Family B, a candidate
capacity/speed/sum). This one binary-searches for a **PARTITION** — a
place to cut. That is the third thing binary search can hunt for, and this
is the problem that teaches it.

The median is not defined by any comparison against a target. It is
defined *positionally*: split the combined 2000-element multiset into a
LEFT half and a RIGHT half of the correct sizes, and the median is read
off the boundary. So do not look for the median's value — look for the
CUT that produces the correct halves.

Cut `A` after `i` elements and `B` after `j` elements, with `i + j` fixed
at exactly half the total. Then you never have to merge anything: the two
cuts already define the halves.

    A:  A[0] ... A[i-1] | A[i] ... A[m-1]
    B:  B[0] ... B[j-1] | B[j] ... B[n-1]
        '------ v -----'   '------ v -----'
             LEFT half          RIGHT half     i + j == (m+n+1)//2

**The partition is CORRECT iff every element left of a cut is <= every
element right of a cut.** Within each array that is free (they are
sorted), so only the two CROSS conditions can fail:

    A[i-1] <= B[j]      (A's last left element fits before B's first right)
    B[j-1] <= A[i]      (B's last left element fits before A's first right)

And that is the whole problem. `i` alone determines `j = half - i`, so
there is exactly ONE unknown, ranging over `[0, m]`. Binary search it:

    A[i-1] > B[j]   ->  I took too much from A   ->  move i LEFT   (hi = i-1)
    B[j-1] > A[i]   ->  I took too little from A ->  move i RIGHT  (lo = i+1)
    neither         ->  correct partition, read off the median

Both failure conditions are monotone in `i` (raising `i` raises `A[i-1]`
and lowers `B[j-1]`), which is precisely what licenses the halving. The
runtime demo prints the whole `i = 0..m` strip to show the
too-left / VALID / too-right structure with no interleaving.

Once the cut is found:

    total odd   -> the left half holds one extra element, and the median IS
                   the largest left element:   max(A[i-1], B[j-1])
    total even  -> the median straddles the cut:
                   (max(A[i-1], B[j-1]) + min(A[i], B[j])) / 2

O(log(min(m, n))) time, O(1) space.


================================================================================
APPROACH 0 · THE MERGE BASELINE — state it, price it, then beat it
================================================================================
Always open with this. It shows you understand the problem before you
optimise it, and it gives you a correctness oracle for free:

    def median_merge(A, B):
        merged = sorted(A + B)          # or a manual two-pointer merge
        t = len(merged)
        return merged[t // 2] if t % 2 else (merged[t//2 - 1] + merged[t//2]) / 2

    Time  O(m + n)   — a manual merge; `sorted(A+B)` is O((m+n) log(m+n))
                        but with a tiny C constant, so in CPython it is
                        actually FASTER than a hand-written Python merge
                        (the demo measures both: at m = n = 400,000 the
                        hand-written merge takes ~110ms while
                        `sorted(A+B)` takes ~21ms).
    Space O(m + n)   — the merged array.

You do not even need to materialise the merge: walking two pointers and
stopping after `(m+n)//2 + 1` steps is O(m + n) time and **O(1) space**,
which is the honest baseline to quote. The problem explicitly asks for
O(log(m+n)), so the baseline is a stepping stone, not an answer — but a
candidate who cannot write it quickly will not survive the real thing.


================================================================================
APPROACH 1 · THE kth-ELEMENT RECURSION — O(log(m+n)), easier to derive
================================================================================
A strictly weaker but much more memorable trick, and a legitimate answer
to "O(log(m+n))". Solve the general problem "find the k-th smallest of two
sorted arrays", then call it once (odd total) or twice (even total).

Compare the `k/2`-th candidate from each array. Whichever is SMALLER, its
entire `k/2`-element prefix is provably too small to be the k-th element,
so discard it and reduce `k` accordingly:

    kth(A, B, k):
        if A is exhausted: return B[k-1]
        if B is exhausted: return A[k-1]
        if k == 1:          return min(A[0], B[0])
        pa = min(k // 2, len(A));  pb = k - pa      (clamped to len(B))
        if A[pa-1] <= B[pb-1]:  drop A's first pa   ->  kth(A[pa:], B, k - pa)
        else:                    drop B's first pb   ->  kth(A, B[pb:], k - pb)

**Why the discard is safe:** if `A[pa-1] <= B[pb-1]`, then each of
`A[0..pa-1]` has at most `(pa-1) + (pb-1)` elements below it in the merged
order — strictly fewer than `k-1` — so none of them can be the k-th. It
throws away half of `k` per step: **O(log k) = O(log(m+n))**.

⚠️ **The slicing trap.** `A[pa:]` looks free and is not: it COPIES. That
turns an O(log k) algorithm into O(m + n) memory traffic and destroys the
whole point. Pass integer offsets instead. The demo measures it: on
m = n = 400,000 the offset version runs in ~0.01ms while the identical
algorithm written with slices takes ~20-27ms — **thousands of times slower
for a purely cosmetic difference.** This is the single most common way a
correct O(log) solution gets marked down.

Approach 1 is `O(log(m+n))`; Approach 2 below is `O(log(min(m,n)))`. When
one array is tiny (m = 1, n = 10^6) that is 20 steps versus 1 — and it is
what the interviewer is actually fishing for.


================================================================================
APPROACH 2 · THE PARTITION SEARCH — the real answer, in detail
================================================================================
    def findMedianSortedArrays(A, B):
        if len(A) > len(B):
            A, B = B, A                     # ALWAYS search the shorter one
        m, n = len(A), len(B)
        half = (m + n + 1) // 2             # size of the LEFT half
        lo, hi = 0, m                       # note: hi = m, not m - 1
        while lo <= hi:
            i = (lo + hi) // 2              # take i from A
            j = half - i                    # ... so take j from B
            a_left  = A[i-1] if i > 0 else -inf
            a_right = A[i]   if i < m else  inf
            b_left  = B[j-1] if j > 0 else -inf
            b_right = B[j]   if j < n else  inf
            if a_left <= b_right and b_left <= a_right:
                if (m + n) % 2:
                    return float(max(a_left, b_left))
                return (max(a_left, b_left) + min(a_right, b_right)) / 2
            if a_left > b_right:
                hi = i - 1                  # took too much from A
            else:
                lo = i + 1                  # took too little from A

Four details, each of which is a bug if you get it wrong.

**(a) `half = (m + n + 1) // 2`, and why it handles odd AND even.**
It is the size of the left half. For an even total, `(m+n+1)//2 == (m+n)/2`
and the halves are equal. For an odd total it rounds UP, so the left half
carries the one extra element — which makes the odd-case median simply
`max(a_left, b_left)`, with no second lookup. Using `(m+n)//2` instead
forces the extra element into the RIGHT half and the odd-case answer
becomes `min(a_right, b_right)`; that also works, but you must then flip
the odd branch too. Pick one and be consistent; mixing them is a
guaranteed off-by-one.

**(b) `lo, hi = 0, m` — the search space is CUT POSITIONS, not indices.**
There are `m + 1` places to cut an m-element array (before everything,
between each adjacent pair, after everything), so `hi = m`, and
`while lo <= hi` explores all of them. Writing `hi = m - 1` (the reflex
from Family A) makes the valid partition unreachable whenever the answer
needs ALL of A on the left — exactly what happens when A is entirely
smaller than B, e.g. `A=[1,2], B=[3,4]`, whose correct cut is `i = 2 = m`.

**(c) The ±inf sentinels.** When `i == 0` there is no `A[i-1]`; when
`i == m` there is no `A[i]`. Substituting `-inf` and `+inf` makes the
cross conditions automatically true on the missing side, which is exactly
the right semantics: "an empty left part can't be too big; an empty right
part can't be too small." Without them you need four `if` branches, and
the naive fix — just index anyway — is worse than a crash in Python,
because `A[-1]` is legal and silently reads the LAST element. The demo
runs a sentinel-free version: it raises `IndexError` on 5 of the 7
standard cases, and would silently mis-answer the rest.

**(d) `if len(A) > len(B): A, B = B, A` — NOT an optimisation. Required.**
`j = half - i` must land inside `[0, n]` for every `i` the search tries.
    j >= 0  needs  i <= half.  Since `half >= m` when `m <= n`, and
            `i <= m`, this holds automatically.
    j <= n  needs  i >= half - n = (m - n + 1) // 2, which is `<= 0`
            when `m <= n`, so `i >= 0` suffices.
Both hold *because A is the shorter array*. Search the LONGER array and
`j` goes out of range — and in Python that means a NEGATIVE index, which
does not crash, it silently reads from the wrong end. The demo:
`A=[1,2,3,4,5,6], B=[7]` searched without the swap returns **5.0**; the
true median is **4.0**. A wrong answer with no exception is the worst
possible failure mode, and it is why the swap is line one.
The swap also buys the better complexity: `O(log(min(m,n)))`.


================================================================================
STEP BY STEP TRACE 1 · ODD TOTAL
================================================================================
A = [1, 3, 8, 9, 15]                (m = 5)
B = [7, 11, 18, 19, 21, 25]         (n = 6)
m <= n, so no swap. total = 11 (odd), half = (11+1)//2 = 6.
lo, hi = 0, 5

  --- step 1: i = (0+5)//2 = 2,  j = 6-2 = 4 ---

        A:  1   3  |  8   9  15
                   ^ i=2
        B:  7  11  18  19  |  21  25
                           ^ j=4

        a_left = A[1] = 3     a_right = A[2] = 8
        b_left = B[3] = 19    b_right = B[4] = 21

        a_left <= b_right ?   3 <= 21   YES
        b_left <= a_right ?  19 <=  8   NO  <-- B's left half reaches too high
        => I took too LITTLE from A (B is having to donate 4 elements and
           its 4th, 19, is bigger than A's next, 8).  lo = i + 1 = 3

  --- step 2: i = (3+5)//2 = 4,  j = 6-4 = 2 ---

        A:  1   3   8   9  |  15
                           ^ i=4
        B:  7  11  |  18  19  21  25
                   ^ j=2

        a_left = A[3] =  9    a_right = A[4] = 15
        b_left = B[1] = 11    b_right = B[2] = 18

        a_left <= b_right ?   9 <= 18   YES
        b_left <= a_right ?  11 <= 15   YES
        => VALID PARTITION.

        LEFT  half = {1, 3, 8, 9} ∪ {7, 11}  = 6 elements  ✓ == half
        RIGHT half = {15} ∪ {18, 19, 21, 25} = 5 elements

        total is ODD -> median = max(a_left, b_left) = max(9, 11) = 11

  Check against the merge: [1,3,7,8,9,11,15,18,19,21,25], 11 elements,
  index 5 -> 11.   ✓


================================================================================
STEP BY STEP TRACE 2 · EVEN TOTAL, AND BOTH SENTINELS FIRING
================================================================================
A = [1, 2], B = [3, 4].   m = n = 2, total = 4 (even), half = (4+1)//2 = 2.
lo, hi = 0, 2

  --- step 1: i = 1,  j = 1 ---

        A:  1  |  2          a_left = A[0] = 1   a_right = A[1] = 2
        B:  3  |  4          b_left = B[0] = 3   b_right = B[1] = 4

        a_left <= b_right ?  1 <= 4  YES
        b_left <= a_right ?  3 <= 2  NO
        => took too little from A.  lo = i + 1 = 2

  --- step 2: i = (2+2)//2 = 2,  j = 0 ---

        A:  1   2  |                 <- cut AFTER everything: i == m
                   ^ i=2                a_right has no element -> +inf
        B:  |  3   4                 <- cut BEFORE everything: j == 0
            ^ j=0                       b_left has no element -> -inf

        a_left = A[1] =  2    a_right = +inf   (sentinel: A exhausted)
        b_left = -inf         b_right = B[0] = 3   (sentinel: nothing left of B)

        a_left <= b_right ?     2 <= 3     YES
        b_left <= a_right ?  -inf <= +inf  YES
        => VALID.

        total is EVEN -> median = (max(a_left, b_left) + min(a_right, b_right)) / 2
                                = (max(2, -inf) + min(+inf, 3)) / 2
                                = (2 + 3) / 2 = 2.5   ✓

  Note this trace needs BOTH `hi = m` (the cut i=2 is only reachable if hi
  is m, not m-1) AND both sentinels. Drop either and this two-line input
  fails. It is the best 10-second sanity check for this problem.


================================================================================
THE PREDICATE STRIP — WHY BINARY SEARCH IS LEGAL HERE
================================================================================
For trace 1's arrays, classify every possible cut i = 0..5:

    i:                0    1    2    3    4    5
    j = 6 - i:        6    5    4    3    2    1
    verdict:        low  low  low  low  OK   high

    "low"  = b_left > a_right  (took too little from A) -> go right
    "high" = a_left > b_right  (took too much from A)   -> go left

The strip is `low...low, OK, high...high` — never interleaved. Raising `i`
moves `a_left`/`a_right` UP (A is sorted) and `b_left`/`b_right` DOWN
(j shrinks), so "took too little" can only turn into "took too much" once.
That single flip is the monotone predicate this whole topic is built on
(topic guide §1.0) — the runtime demo prints this exact strip and asserts
it has no interleaving.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time                 Space     Mutates input?  Note
    --------------------------------  -------------------  --------  --------------  ------------------------
    sorted(A + B), read the middle    O((m+n) log(m+n))    O(m+n)    no              1 line; C-fast in
                                                                                       CPython despite the log
    Manual two-pointer merge,         O(m + n)             O(1)      no              the honest baseline;
      stop at the middle                                                               O(1) space, but linear
    kth-element recursion             O(log(m+n))          O(1)      no              easy to derive; O(m+n)
      (integer offsets)                                                                if you SLICE — see the
                                                                                       demo: ~2000x slower at
                                                                                       m = n = 400,000
    Partition binary search ✅        O(log(min(m, n)))    O(1)      no              the answer. ~11 steps
                                                                                       for m = n = 1000; 1 step
                                                                                       when m = 1

    All four are non-mutating: the swap `A, B = B, A` rebinds local names,
    it does not reorder any caller's list. If you had to SORT the inputs
    first the whole approach would collapse to O((m+n) log(m+n)) — the
    algorithm's entire premise is that both inputs arrive sorted.


================================================================================
EDGE CASES
================================================================================
    One array EMPTY, e.g. A=[], B=[1]      -> after the swap m = 0, so
        `lo == hi == 0`, `i = 0`, `j = half`; a_left = -inf and
        a_right = +inf make both cross conditions trivially true on the
        first probe, and the median comes entirely from B. The sentinels
        are what make the empty case need no special-casing at all.
    A entirely BELOW B, e.g. [1,2] / [3,4] -> the cut must be at i = m
        (all of A on the left). Needs `hi = m`; trace 2 above.
    A entirely ABOVE B, e.g. [3,4] / [1,2] -> the mirror: the cut is at
        i = 0 (none of A on the left), needing the `i > 0` sentinel.
    ALL VALUES EQUAL, e.g. [0,0] / [0,0]   -> every cross condition is
        `0 <= 0`, true; the first probe is already valid. Confirms the
        conditions must be `<=`, not `<` — with strict `<` this input has
        NO valid partition and the loop falls off the end.
    Single element total, e.g. [] / [1]     -> odd path, median = 1.0.
    m == n                                  -> `half == m`, so `j = m - i`;
        nothing special, but it is the case where both sentinels are least
        likely to fire, which is why it is a bad case to test first.
    Negative values (-10^6 allowed)          -> only comparisons are used;
        `-inf` is still strictly below any real value, so the sentinels
        hold. Do NOT use a "big negative int" like -10**7 as a sentinel:
        it is a landmine the moment constraints change. `float('-inf')`
        is unconditionally correct.
    Return type                              -> the median of an odd total
        is an existing integer; the problem wants a FLOAT (2.00000), so
        cast. `/ 2` in Python 3 already yields a float for the even case;
        `// 2` would silently truncate (see mistake 6).


================================================================================
COMMON MISTAKES
================================================================================
1. **Searching the longer array** (skipping `if len(A) > len(B)`). `j`
   leaves `[0, n]`, Python happily accepts the negative index, and you get
   a plausible WRONG NUMBER instead of an exception. Measured in the demo:
   `[1,2,3,4,5,6]` / `[7]` returns 5.0 instead of 4.0.

2. **Dropping the ±inf sentinels** and indexing directly. `IndexError` on
   the high side (`A[m]`), and worse, silent nonsense on the low side
   (`A[-1]` is the last element, not "nothing"). The demo raises
   IndexError on 5 of 7 standard cases with sentinels removed.

3. **`hi = m - 1`** instead of `hi = m` — carrying over the Family A
   reflex. Makes "all of A on the left" unreachable; `[1,2]` / `[3,4]`
   fails.

4. **`half = (m+n)//2` paired with the odd-case `max(a_left, b_left)`.**
   The two choices are coupled: round the left half UP and the extra
   element is on the left (use `max` of the lefts); round DOWN and it is
   on the right (use `min` of the rights). Mixing them is off-by-one on
   every odd input.

5. **Strict `<` in the cross conditions.** Duplicates across the two
   arrays (`[0,0]` / `[0,0]`) then have no valid partition and the loop
   exits without returning — `None`, or a crash downstream. It must be
   `<=`.

6. **`// 2` for the even-case average.** `(2 + 3) // 2 == 2`, not `2.5`.
   Use `/ 2`. Related: returning an `int` for the odd case when the
   signature promises `float`.

7. **Slicing in the kth-element recursion** (`kth(A[pa:], B, k-pa)`).
   Correct answer, wrong complexity — O(m+n) copying hidden inside an
   O(log k) recursion. Measured at m = n = 400,000: ~0.01ms with offsets
   versus ~20-27ms with slices.

8. **Binary-searching the VALUE space instead of the partition.** It is
   possible ("how many elements are <= x" is monotone in x, so bisect on
   x), but it costs `O(log(max-min) · log(min(m,n)))`, needs care with
   duplicates, and cannot be adapted to real-valued inputs. Recognising
   that this problem is about a CUT, not a VALUE, is the insight being
   tested.

9. **Merging first "just to be safe."** O(m+n) fails the stated
   requirement. State the baseline, then beat it — do not submit it.

10. **`while lo < hi`** instead of `while lo <= hi`. Here the loop RETURNS
    from inside on success; it is not a converge-then-read loop, so it must
    be allowed to probe the single remaining position `lo == hi`. This is
    the one place in this folder where `<=` is right and the Family B
    template's `<` is wrong.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Generalise to the k-th smallest instead of the median.
A: The partition method generalises directly — replace `half` with `k` and
   return `max(a_left, b_left)`; that IS "the k-th smallest". Or use
   Approach 1's recursion, which is already stated in terms of k.

Q: Now do it for K sorted arrays.
A: The partition trick does not extend (K-1 free cut variables instead of
   one). Two standard answers: a min-heap merge stopping at the median —
   O((m+n) log K); or binary search on the VALUE and count how many
   elements across all K arrays are `<= x`, each count itself a binary
   search — O(log(range) · K log(max length)). The second is the one to
   reach for when the arrays are huge and K is small.

Q: What if the arrays are on disk / behind an API and you can only make
   O(log n) random reads?
A: The partition method is already read-optimal: it touches at most 4
   elements per step and takes ~log2(min(m,n)) steps — 11 probes for
   m = n = 1000. Approach 0 would need to stream everything.

Q: What if they are sorted DESCENDING?
A: Reverse the comparison senses (or read them back to front). Same
   algorithm; do not physically reverse the arrays — that is O(n) and
   throws away the whole win.

Q: What if duplicates span both arrays heavily, e.g. both are all zeros?
A: Nothing changes, provided the cross conditions use `<=`. There may be
   several valid partitions; any of them yields the same median, and the
   search returns the first one it lands on.

Q: Can you do it in O(1) time?
A: No. You cannot even confirm which array holds the median without
   looking at it; `Ω(log(min(m,n)))` is the known lower bound for
   comparison-based algorithms here, which the partition method matches.

Q: Why is `O(log(min(m,n)))` better than `O(log(m+n))` in practice?
A: The skew case. m = 1, n = 10^6: `log2(min) = 0` steps versus
   `log2(m+n) = 20`. Same big-O family, but the partition method's cost
   is bounded by the SMALL array, which is exactly the input shape where
   a merge is most tempting and most wasteful.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
"Binary-search a CUT / a k-th position across sorted structures":

    LC 4     Median of Two Sorted Arrays   — THIS FILE. The canonical
                                              partition search
    LC 378   Kth Smallest Element in a      — binary search on the VALUE +
             Sorted Matrix                    a counting predicate; the
                                              value-space alternative
                                              discussed in mistake 8
    LC 668   Kth Smallest Number in a        — same value-space + count shape,
             Multiplication Table              no array materialised at all
    LC 719   Find K-th Smallest Pair          — value-space binary search with
             Distance                           a two-pointer counter inside
    LC 786   K-th Smallest Prime Fraction     — value-space search, or a heap
    LC 295   Find Median from Data Stream     — the STREAMING cousin: two
                                              heaps instead of a cut (topic
                                              12 · Heap)
    LC 480   Sliding Window Median            — 295's technique under a moving
                                              window
    LC 23    Merge k Sorted Lists             — the "just merge them" family
                                              this problem refuses to join

    Same-folder siblings (the other two things binary search hunts for):
    LC 704 / 35 / 74  (001, 002, 005)  — search for a VALUE   (Family A)
    LC 875 / 1011 / 410 (006, 010, 011) — search for an ANSWER (Family B)
    LC 4              (012, this file)  — search for a CUT
================================================================================
"""

import random
import time
from typing import List, Tuple

INF = float("inf")


class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        """Partition binary search over the SHORTER array.
        O(log(min(m,n))) time, O(1) space. The answer.
        See THE CORE IDEA above."""
        A, B = nums1, nums2
        if len(A) > len(B):
            A, B = B, A                      # REQUIRED, not an optimisation
        m, n = len(A), len(B)
        half = (m + n + 1) // 2              # size of the LEFT half
        lo, hi = 0, m                        # cut positions: m + 1 of them
        while lo <= hi:
            i = (lo + hi) // 2               # take i elements from A
            j = half - i                     # ... hence j from B
            a_left = A[i - 1] if i > 0 else -INF
            a_right = A[i] if i < m else INF
            b_left = B[j - 1] if j > 0 else -INF
            b_right = B[j] if j < n else INF
            if a_left <= b_right and b_left <= a_right:
                if (m + n) % 2:
                    return float(max(a_left, b_left))
                return (max(a_left, b_left) + min(a_right, b_right)) / 2.0
            if a_left > b_right:
                hi = i - 1                   # took too much from A
            else:
                lo = i + 1                   # took too little from A
        raise ValueError("no valid partition — inputs were not sorted")

    # ------------------------------------------------------------------
    # Alternatives / oracles.
    # ------------------------------------------------------------------
    def findMedianSortedArrays_merge(self, nums1: List[int], nums2: List[int]) -> float:
        """Approach 0 oracle: merge and read the middle. O(m+n) time,
        O(m+n) space with a materialised merge."""
        out: List[int] = []
        i = j = 0
        while i < len(nums1) and j < len(nums2):
            if nums1[i] <= nums2[j]:
                out.append(nums1[i]); i += 1
            else:
                out.append(nums2[j]); j += 1
        out.extend(nums1[i:])
        out.extend(nums2[j:])
        t = len(out)
        return float(out[t // 2]) if t % 2 else (out[t // 2 - 1] + out[t // 2]) / 2.0

    def findMedianSortedArrays_sorted(self, nums1: List[int], nums2: List[int]) -> float:
        """Approach 0, one-liner flavour: sorted(A+B). C-coded, so fast in
        CPython despite the extra log factor."""
        merged = sorted(nums1 + nums2)
        t = len(merged)
        return float(merged[t // 2]) if t % 2 else (merged[t // 2 - 1] + merged[t // 2]) / 2.0

    def findMedianSortedArrays_kth(self, nums1: List[int], nums2: List[int]) -> float:
        """Approach 1: the kth-element recursion, with integer OFFSETS (no
        slicing). O(log(m+n)) time, O(1) space."""
        total = len(nums1) + len(nums2)
        if total % 2:
            return float(self._kth_offsets(nums1, nums2, total // 2 + 1))
        a = self._kth_offsets(nums1, nums2, total // 2)
        b = self._kth_offsets(nums1, nums2, total // 2 + 1)
        return (a + b) / 2.0

    @staticmethod
    def _kth_offsets(A: List[int], B: List[int], k: int) -> int:
        """1-indexed k-th smallest of two sorted arrays. Iterative, offsets
        only — never slices."""
        ia = ib = 0
        while True:
            if ia == len(A):
                return B[ib + k - 1]
            if ib == len(B):
                return A[ia + k - 1]
            if k == 1:
                return min(A[ia], B[ib])
            pa = min(k // 2, len(A) - ia)
            pb = k - pa
            if pb > len(B) - ib:             # clamp, then re-derive pa
                pb = len(B) - ib
                pa = k - pb
            if A[ia + pa - 1] <= B[ib + pb - 1]:
                ia += pa; k -= pa            # A's first pa can't be the k-th
            else:
                ib += pb; k -= pb            # B's first pb can't be the k-th

    def findMedianSortedArrays_kth_slicing(self, nums1: List[int], nums2: List[int]) -> float:
        """✗ Same algorithm as _kth_offsets but written with SLICES — the
        classic way to turn O(log k) into O(m+n). Kept to measure it."""
        def kth(A: List[int], B: List[int], k: int) -> int:
            if not A:
                return B[k - 1]
            if not B:
                return A[k - 1]
            if k == 1:
                return min(A[0], B[0])
            pa = min(k // 2, len(A))
            pb = k - pa
            if pb > len(B):
                pb = len(B); pa = k - pb
            if A[pa - 1] <= B[pb - 1]:
                return kth(A[pa:], B, k - pa)     # <-- COPIES
            return kth(A, B[pb:], k - pb)         # <-- COPIES

        total = len(nums1) + len(nums2)
        if total % 2:
            return float(kth(nums1, nums2, total // 2 + 1))
        return (kth(nums1, nums2, total // 2) + kth(nums1, nums2, total // 2 + 1)) / 2.0

    # ------------------------------------------------------------------
    # Deliberately broken variants, used by the runtime demos.
    # ------------------------------------------------------------------
    def _partition_no_swap(self, nums1: List[int], nums2: List[int]) -> float:
        """✗ Identical to the real solution MINUS the shorter-array swap.
        j escapes [0, n]; Python's negative indexing hides it."""
        A, B = nums1, nums2
        m, n = len(A), len(B)
        half = (m + n + 1) // 2
        lo, hi = 0, m
        while lo <= hi:
            i = (lo + hi) // 2
            j = half - i
            a_left = A[i - 1] if i > 0 else -INF
            a_right = A[i] if i < m else INF
            b_left = B[j - 1] if j > 0 else -INF
            b_right = B[j] if j < n else INF
            if a_left <= b_right and b_left <= a_right:
                if (m + n) % 2:
                    return float(max(a_left, b_left))
                return (max(a_left, b_left) + min(a_right, b_right)) / 2.0
            if a_left > b_right:
                hi = i - 1
            else:
                lo = i + 1
        raise ValueError("no valid partition found")

    def _partition_no_sentinel(self, nums1: List[int], nums2: List[int]) -> float:
        """✗ Identical to the real solution MINUS the ±inf sentinels."""
        A, B = nums1, nums2
        if len(A) > len(B):
            A, B = B, A
        m, n = len(A), len(B)
        half = (m + n + 1) // 2
        lo, hi = 0, m
        while lo <= hi:
            i = (lo + hi) // 2
            j = half - i
            a_left = A[i - 1]       # no guard: A[-1] is the LAST element
            a_right = A[i]          # no guard: A[m] raises IndexError
            b_left = B[j - 1]
            b_right = B[j]
            if a_left <= b_right and b_left <= a_right:
                if (m + n) % 2:
                    return float(max(a_left, b_left))
                return (max(a_left, b_left) + min(a_right, b_right)) / 2.0
            if a_left > b_right:
                hi = i - 1
            else:
                lo = i + 1
        raise ValueError("no valid partition found")

    @staticmethod
    def classify_cut(A: List[int], B: List[int], i: int) -> Tuple[int, str]:
        """For the predicate strip: classify cut position i of A as
        'low' (took too little from A), 'OK', or 'high' (took too much)."""
        m, n = len(A), len(B)
        half = (m + n + 1) // 2
        j = half - i
        if j < 0 or j > n:
            return j, "out-of-range"
        a_left = A[i - 1] if i > 0 else -INF
        a_right = A[i] if i < m else INF
        b_left = B[j - 1] if j > 0 else -INF
        b_right = B[j] if j < n else INF
        if a_left > b_right:
            return j, "high"
        if b_left > a_right:
            return j, "low"
        return j, "OK"


# ==============================================================================
# TESTS — run:  python 012_median_of_two_sorted_arrays_solution.py
# ==============================================================================
CASES = [
    ([1, 3], [2], 2.0),
    ([1, 2], [3, 4], 2.5),
    ([], [1], 1.0),
    ([2], [], 2.0),
    ([1, 2, 3], [], 2.0),
    ([1, 3], [2, 7], 2.5),
    ([0, 0], [0, 0], 0.0),
    ([1, 3, 8, 9, 15], [7, 11, 18, 19, 21, 25], 11.0),
    ([3, 4], [1, 2], 2.5),
    ([1, 2, 3, 4, 5, 6], [7], 4.0),
    ([-1000000, 0], [-5, 1000000], -2.5),
    ([1], [1], 1.0),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: partition binary search ---")
    for a, b, expected in CASES:
        got = sol.findMedianSortedArrays(list(a), list(b))
        ok = abs(got - expected) < 1e-9
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums1={a!r:<24} nums2={b!r:<20} -> {got}  (want {expected})")

    print("\n--- all four approaches must agree ---")
    print(f"  {'nums1':<22} {'nums2':<25} {'partition':>10} {'merge':>8} {'sorted':>8} {'kth':>8}")
    for a, b, expected in CASES:
        p = sol.findMedianSortedArrays(list(a), list(b))
        mg = sol.findMedianSortedArrays_merge(list(a), list(b))
        st = sol.findMedianSortedArrays_sorted(list(a), list(b))
        kt = sol.findMedianSortedArrays_kth(list(a), list(b))
        ok = max(abs(p - expected), abs(mg - expected), abs(st - expected), abs(kt - expected)) < 1e-9
        all_ok &= ok
        print(f"  {str(a):<22} {str(b):<25} {p:>10} {mg:>8} {st:>8} {kt:>8}  {'PASS' if ok else 'FAIL'}")

    # ----------------------------------------------------------------------
    # The predicate strip: low...low, OK, high...high — never interleaved.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️ the cut is a MONOTONE predicate: every i classified ---")
    A, B = [1, 3, 8, 9, 15], [7, 11, 18, 19, 21, 25]
    print(f"  A={A}  B={B}   half=(5+6+1)//2={(len(A) + len(B) + 1) // 2}")
    verdicts = []
    print(f"  {'i':>2} {'j':>3}  {'verdict':<12} meaning")
    meaning = {"low": "b_left > a_right -> took too little from A -> go right",
               "OK": "both cross conditions hold -> READ THE MEDIAN HERE",
               "high": "a_left > b_right -> took too much from A -> go left"}
    for i in range(len(A) + 1):
        j, v = sol.classify_cut(A, B, i)
        verdicts.append(v)
        print(f"  {i:>2} {j:>3}  {v:<12} {meaning.get(v, '')}")
    strip_ok = (verdicts.count("OK") >= 1
                and verdicts == sorted(verdicts, key=lambda v: {"low": 0, "OK": 1, "high": 2}[v]))
    all_ok &= strip_ok
    print(f"  strip reads low...low, OK, high...high with no interleaving: {strip_ok}")
    print("  -> exactly one flip, so halving is safe. This is topic guide §1.0.")

    # ----------------------------------------------------------------------
    # Trace 1: odd total.
    # ----------------------------------------------------------------------
    print("\n--- trace 1 (ODD total): A=[1,3,8,9,15] B=[7,11,18,19,21,25] ---")
    _trace(A, B)

    # ----------------------------------------------------------------------
    # Trace 2: even total, both sentinels firing.
    # ----------------------------------------------------------------------
    print("\n--- trace 2 (EVEN total, both ±inf sentinels fire): A=[1,2] B=[3,4] ---")
    _trace([1, 2], [3, 4])

    # ----------------------------------------------------------------------
    # ⚠️ RUNTIME DEMO 1: drop the shorter-array swap -> silent wrong answer.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️ searching the LONGER array (no swap): silent wrong answers ---")
    print(f"  {'nums1 (the LONGER one)':<32} {'nums2':<12} {'no-swap':>11} {'correct':>8}  verdict")
    swap_demo_ok = False
    for a, b in ([[1, 2, 3, 4, 5, 6], [7]],
                 [[7, 9, 11, 11, 15, 19], [18]],
                 [[0, 1, 2, 2, 3, 6, 7, 12], [12]],
                 [[1, 3, 12, 14, 15, 19, 19], [20]],
                 [[15, 16, 17, 19], [0, 1, 15]],
                 [[1, 2, 3, 4, 5, 6, 7, 8, 9], [4]]):
        try:
            bad = sol._partition_no_swap(list(a), list(b))
        except Exception as exc:                      # noqa: BLE001 - demo
            bad = f"{type(exc).__name__}"
        good = sol.findMedianSortedArrays_merge(list(a), list(b))
        wrong = not (isinstance(bad, float) and abs(bad - good) < 1e-9)
        if wrong:
            swap_demo_ok = True
        verdict = ("CRASH" if isinstance(bad, str)
                   else "WRONG — and no exception!" if wrong else "happens to agree")
        print(f"  {str(a):<32} {str(b):<12} {str(bad):>11} {good:>8}  {verdict}")
    all_ok &= swap_demo_ok
    random.seed(0)
    no_swap_wrong = 0
    for _ in range(4000):
        mm = random.randint(2, 9)
        nn = random.randint(0, mm - 1)
        a = sorted(random.randint(0, 20) for _ in range(mm))
        b = sorted(random.randint(0, 20) for _ in range(nn))
        good = sol.findMedianSortedArrays_merge(a, b)
        try:
            wrong = abs(sol._partition_no_swap(a, b) - good) > 1e-9
        except Exception:                             # noqa: BLE001 - demo
            wrong = True
        no_swap_wrong += wrong
    print(f"  randomised: no-swap is wrong (or crashes) on {no_swap_wrong} of 4000")
    print("  random inputs in which nums1 is the longer array.")
    all_ok &= (no_swap_wrong > 0)
    print("  Cause: j = half - i leaves [0, n]. A NEGATIVE j does not raise in")
    print("  Python — B[j-1] silently reads from the far end of B, so the")
    print("  'valid partition' test passes on a partition that does not exist.")
    print("  The swap is line one of the function for exactly this reason.")

    # ----------------------------------------------------------------------
    # ⚠️ RUNTIME DEMO 2: drop the ±inf sentinels -> IndexError.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️ dropping the ±inf sentinels: IndexError / silent nonsense ---")
    print(f"  {'nums1':<22} {'nums2':<18} {'no-sentinel result':<34} {'correct':>8}")
    crashes = 0
    for a, b, expected in CASES[:7]:
        try:
            got = repr(sol._partition_no_sentinel(list(a), list(b)))
        except Exception as exc:                       # noqa: BLE001 - demo
            got = f"{type(exc).__name__}: {exc}"
            crashes += 1
        print(f"  {str(a):<22} {str(b):<18} {got:<34} {expected:>8}")
    print(f"  {crashes} of 7 standard cases CRASH without the sentinels.")
    print("  A[m] raises IndexError; A[-1] does NOT — it silently returns the")
    print("  last element, so the low side fails quietly instead of loudly.")
    all_ok &= (crashes > 0)

    # ----------------------------------------------------------------------
    # Randomised cross-check vs the merge oracle.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the merge oracle ---")
    random.seed(4)
    trials, mismatches = 4000, 0
    for _ in range(trials):
        m = random.randint(0, 9)
        n = random.randint(0, 9)
        if m + n == 0:
            continue
        a = sorted(random.randint(-12, 12) for _ in range(m))
        b = sorted(random.randint(-12, 12) for _ in range(n))
        want = sol.findMedianSortedArrays_merge(a, b)
        if (abs(sol.findMedianSortedArrays(a, b) - want) > 1e-9
                or abs(sol.findMedianSortedArrays_kth(a, b) - want) > 1e-9):
            mismatches += 1
    print(f"  {trials} random pairs (len 0-9, heavy duplicates): {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # ⚠️ RUNTIME DEMO 3: O(log min(m,n)) vs the O(m+n) baselines, and the
    # cost of SLICING inside the kth recursion.
    # ----------------------------------------------------------------------
    print("\n--- O(log min(m,n)) partition vs the O(m+n) baselines: measured ---")
    print(f"  {'m = n':>8} {'partition':>11} {'kth(offsets)':>14} {'kth(SLICES)':>13} "
          f"{'merge(py)':>11} {'sorted(A+B)':>12}")
    random.seed(3)
    for n in (20_000, 100_000, 400_000):
        a = sorted(random.randint(-10 ** 6, 10 ** 6) for _ in range(n))
        b = sorted(random.randint(-10 ** 6, 10 ** 6) for _ in range(n))
        t0 = time.perf_counter(); r1 = sol.findMedianSortedArrays(a, b)
        t1 = time.perf_counter(); r2 = sol.findMedianSortedArrays_kth(a, b)
        t2 = time.perf_counter(); r3 = sol.findMedianSortedArrays_kth_slicing(a, b)
        t3 = time.perf_counter(); r4 = sol.findMedianSortedArrays_merge(a, b)
        t4 = time.perf_counter(); r5 = sol.findMedianSortedArrays_sorted(a, b)
        t5 = time.perf_counter()
        agree = r1 == r2 == r3 == r4 == r5
        all_ok &= agree
        print(f"  {n:>8} {(t1 - t0) * 1000:>10.3f}ms {(t2 - t1) * 1000:>13.3f}ms "
              f"{(t3 - t2) * 1000:>12.2f}ms {(t4 - t3) * 1000:>10.2f}ms "
              f"{(t5 - t4) * 1000:>11.2f}ms  {'agree' if agree else 'MISMATCH'}")
    print("  Read the first column against the last two: the partition search's")
    print("  cost barely moves as n grows 20x (it does ~log2(n) probes and")
    print("  touches 4 elements each), while every O(m+n) approach scales")
    print("  linearly. kth(SLICES) is the same algorithm as kth(offsets) with")
    print("  one cosmetic change and is hundreds-to-thousands of times slower —")
    print("  the ratio grows with n because the slices")
    print("  copy the arrays, reintroducing the O(m+n) the recursion removed.")
    print("  Note also that C-coded sorted(A+B) beats a hand-written Python")
    print("  merge despite the extra log factor — the same CPython lesson as")
    print("  topic 01's problems 008/012: constants dominate at these sizes.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


def _trace(A: List[int], B: List[int]) -> None:
    """Print the partition search step by step for one input."""
    if len(A) > len(B):
        A, B = B, A
    m, n = len(A), len(B)
    half = (m + n + 1) // 2
    lo, hi = 0, m
    print(f"  A={A} (m={m})  B={B} (n={n})  total={m + n}  half={half}")
    print(f"  {'lo':>2} {'hi':>2} {'i':>2} {'j':>2}  {'a_left':>7} {'a_right':>7} "
          f"{'b_left':>7} {'b_right':>7}  action")
    while lo <= hi:
        i = (lo + hi) // 2
        j = half - i
        al = A[i - 1] if i > 0 else -INF
        ar = A[i] if i < m else INF
        bl = B[j - 1] if j > 0 else -INF
        br = B[j] if j < n else INF
        if al <= br and bl <= ar:
            if (m + n) % 2:
                med = float(max(al, bl))
                act = f"VALID (odd)  -> max({al}, {bl}) = {med}"
            else:
                med = (max(al, bl) + min(ar, br)) / 2.0
                act = f"VALID (even) -> (max({al},{bl}) + min({ar},{br})) / 2 = {med}"
            print(f"  {lo:>2} {hi:>2} {i:>2} {j:>2}  {al:>7} {ar:>7} {bl:>7} {br:>7}  {act}")
            print(f"  left half = {A[:i]} + {B[:j]}  ({i + j} elements == half)")
            print(f"  right half= {A[i:]} + {B[j:]}")
            return
        if al > br:
            act = f"a_left {al} > b_right {br}: too much from A -> hi = {i - 1}"
            print(f"  {lo:>2} {hi:>2} {i:>2} {j:>2}  {al:>7} {ar:>7} {bl:>7} {br:>7}  {act}")
            hi = i - 1
        else:
            act = f"b_left {bl} > a_right {ar}: too little from A -> lo = {i + 1}"
            print(f"  {lo:>2} {hi:>2} {i:>2} {j:>2}  {al:>7} {ar:>7} {bl:>7} {br:>7}  {act}")
            lo = i + 1


if __name__ == "__main__":
    run_tests()
