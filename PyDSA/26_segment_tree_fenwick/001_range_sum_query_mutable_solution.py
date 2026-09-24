"""
================================================================================
SOLUTION · LeetCode 307 · Range Sum Query - Mutable                     [Medium]
https://leetcode.com/problems/range-sum-query-mutable/
================================================================================

THE CORE IDEA
--------------
A Fenwick tree (Binary Indexed Tree, "BIT") stores partial sums keyed off
each 1-indexed position's BINARY representation, not the raw values and not
one fully-materialized running total. Concretely: `tree[i]` holds the sum
of a range of the original array ending at index `i` (1-indexed), whose
LENGTH is exactly `i & (-i)` — the value of `i`'s lowest set bit. That one
fact is what makes both operations O(log n):

    update(i, delta):  walk UP the tree, adding delta to every node whose
                        covered range includes index i:
                            while i <= n: tree[i] += delta; i += i & (-i)

    prefix(i):         walk DOWN, accumulating tree nodes that together
                        cover exactly [1..i]:
                            while i > 0: s += tree[i]; i -= i & (-i)

Each walk visits at most `floor(log2(n)) + 1` nodes, because `i & -i`
strictly changes the binary representation in a way that terminates within
that many steps (going up, bits set above the lowest one only grow; going
down, the lowest set bit is repeatedly cleared).

`sumRange(l, r) = prefix(r) - prefix(l - 1)` is the SAME inclusion-exclusion
identity topic 04's static prefix sum uses — the only difference is that
`prefix(i)` here is computed on demand from O(log n) tree nodes instead of
read from a fully precomputed array, which is exactly what lets `update`
stay cheap.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, not coded): keep the raw array; `update` is
O(1) (just overwrite); `sumRange(l, r)` sums the slice directly, O(r - l).
Fails badly when `sumRange` is called ~30,000 times over a ~30,000-length
array — worst case ~9*10^8 element additions.

Approach 0b (full prefix-sum array, priced, not coded): precompute
`prefix[i] = sum(nums[0..i-1])` once; `sumRange` becomes O(1)
(`prefix[r+1] - prefix[l]`). But `update(index, val)` must add the delta to
EVERY `prefix[j]` for `j > index`, which is O(n) per update. Fails when
`update` is called ~30,000 times.

Approach 1 (chosen) — Fenwick tree / BIT: O(log n) for both `update` and
`sumRange`. See THE CORE IDEA. ~15 lines of real logic, one array of size
n+1, no recursion.

Approach 2 (alternative, not coded) — segment tree: also O(log n) for both
operations, and strictly more general (would ALSO support range min/max,
which sum doesn't need here). Costs more code (build/update/query, usually
recursive or with an explicit 2n/4n-sized array) for no benefit on a
SUM-only problem, since sum has a working inverse (subtraction) and a BIT
already exploits that. Segment tree is the right call for 005/006 in this
topic, where the aggregate (max) has no inverse — see topic guide Part 1.


================================================================================
STEP BY STEP TRACE — nums = [1, 3, 5], n = 3
================================================================================
Build: 1-indexed tree array of size n+1 = 4, all zero initially.
Insert each value via `update`.

    update(0, 1):  delta = 1 - 0 = 1.  i = index+1 = 1
        i=1: tree[1] += 1 -> tree[1]=1;  i += (1 & -1)=1 -> i=2
        i=2: tree[2] += 1 -> tree[2]=1;  i += (2 & -2)=2 -> i=4
        i=4: tree[4] += 1 -> tree[4]=1;  i += (4 & -4)=4 -> i=8 > n(3), stop
        tree = [_, 1, 1, 0, 1]     (index 0 unused)

    update(1, 3):  delta = 3 - 0 = 3.  i = 2
        i=2: tree[2] += 3 -> tree[2]=4;  i += 2 -> i=4
        i=4: tree[4] += 3 -> tree[4]=4;  i += 4 -> i=8, stop
        tree = [_, 1, 4, 0, 4]

    update(2, 5):  delta = 5 - 0 = 5.  i = 3
        i=3: tree[3] += 5 -> tree[3]=5;  i += (3 & -3)=1 -> i=4
        i=4: tree[4] += 5 -> tree[4]=9;  i += 4 -> i=8, stop
        tree = [_, 1, 4, 5, 9]

    Interpretation: tree[1] covers nums[0..0] (length 1&-1=1) = 1
                     tree[2] covers nums[0..1] (length 2&-2=2) = 1+3 = 4
                     tree[3] covers nums[2..2] (length 3&-3=1) = 5
                     tree[4] covers nums[0..3] (length 4&-4=4, clipped to
                                                  n=3) = 1+3+5 = 9

sumRange(0, 2) -> prefix(2) - prefix(-1... i.e. prefix(0), since left=0):
    prefix(3) [right+1=3]:
        i=3: s += tree[3] = 5;  i -= (3&-3)=1 -> i=2
        i=2: s += tree[2] = 4 -> s=9;  i -= 2 -> i=0, stop
        prefix(3) = 9
    prefix(0) [left=0]:
        i=0, loop doesn't run -> prefix(0) = 0
    sumRange(0,2) = 9 - 0 = 9                         MATCHES 1+3+5=9 [OK]

update(1, 2): delta = 2 - 3 = -1.  i = 2
    i=2: tree[2] += -1 -> tree[2]=3;  i += 2 -> i=4
    i=4: tree[4] += -1 -> tree[4]=8;  i += 4 -> i=8, stop
    tree = [_, 1, 3, 5, 8]
    nums (logical) now [1, 2, 5]

sumRange(0, 2) again:
    prefix(3): i=3: s=5; i=2: s+=tree[2]=3 -> s=8; i=0 stop. prefix(3)=8
    prefix(0) = 0
    sumRange(0,2) = 8 - 0 = 8                         MATCHES 1+2+5=8 [OK]


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                         update     sumRange   Space   Mutates input?
    --------------------------------------------------------------------------
    Raw array, resum each query      O(1)       O(n)       O(n)    n/a (design)
    Full prefix-sum array            O(n)       O(1)       O(n)    n/a (design)
    Fenwick tree / BIT ✅            O(log n)   O(log n)   O(n)    n/a (design)
    Segment tree (alt.)              O(log n)   O(log n)   O(n)    n/a (design)


================================================================================
EDGE CASES
================================================================================
    n == 1                     Single-element array; `i & -i` walk still
                                terminates correctly (tree size 2).
    left == right               Range of length 1; sumRange degenerates to
                                a single-element lookup via two prefix
                                queries one apart.
    update to the SAME value    delta == 0; the walk still runs (harmless,
                                adds zero everywhere) — no need to special-
                                case it, but it's a legal no-op call.
    negative values             `nums[i]` can be negative (-100..100);
                                sums and deltas must handle negative
                                numbers correctly (no assumption of
                                non-negativity anywhere in the bit walk).
    repeated updates to the
    same index                  Must always use `val - CURRENT nums[index]`
                                as the delta, not `val` itself, or not the
                                delta from the ORIGINAL value — the tracked
                                "current value" array must be kept in sync
                                on every update.


================================================================================
COMMON MISTAKES
================================================================================
1. Using `val` directly as the delta in `update`, instead of
   `val - nums[index]`. The BIT stores SUMS, not raw values — adding the
   new value (rather than the CHANGE) double-counts on every update after
   the first.

2. Forgetting the BIT is 1-indexed. Passing the raw 0-indexed `index`
   straight into the tree walk (instead of `index + 1`) either skips index
   0 entirely or corrupts the `i & -i` arithmetic (starting a walk at `i=0`
   loops forever, since `0 & -0 == 0`).

3. Off-by-one in `sumRange`: `prefix(right)` vs `prefix(right + 1)`.
   Since `prefix(i)` here is defined as "sum of the first `i` elements"
   (1-indexed COUNT, not a 0-indexed endpoint), `sumRange(l, r)` inclusive
   needs `prefix(r + 1) - prefix(l)`, NOT `prefix(r) - prefix(l - 1)` unless
   `prefix` is defined the other way — mixing the two conventions
   mid-implementation is the single most common bug in this topic.

4. Forgetting to keep a separate "current value" array in sync, and trying
   to reconstruct `nums[index]` by re-querying `sumRange(index, index)`
   before every update — works, but needless: track it directly, it's O(1).

5. Building the tree by looping over `nums` and calling `update` n times,
   which is O(n log n) to build — correct, and what's used here since n is
   small (≤ 3*10^4), but worth knowing there's an O(n) direct-build
   variant (propagate each raw value to its immediate BIT parent once, left
   to right) for when build time itself is the bottleneck.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
Q: Could you build the tree in O(n) instead of O(n log n)?
A: Yes — initialize `tree[i] = nums[i-1]` for all i, then for each i from 1
   to n, propagate `tree[i]` directly into its immediate parent
   `tree[i + (i & -i)]` if that parent is within bounds. This does one O(1)
   step per index instead of a full O(log n) update walk per index.

Q: What if range MIN or MAX were needed instead of sum?
A: A Fenwick tree can't do it directly — sum has an inverse (subtraction)
   that lets `sumRange = prefix(r) - prefix(l-1)` work; min/max don't, so
   there's no way to "remove" a range from a running min the way you can
   subtract a sum. Use a segment tree instead (see 005/006 in this topic).

Q: How would you support range UPDATE (add delta to every element in
   `[l, r]`) in addition to range query?
A: A second "difference-array BIT" trick: maintain a BIT over the
   DIFFERENCE array; a range update becomes two point updates
   (`+delta at l`, `-delta at r+1`), and a point query becomes a prefix sum
   over the difference BIT. Range-sum-of-range-update needs a pair of BITs
   (this is the standard "BIT of BITs" range-update-range-query trick).

Q: Why not just use a plain list and call `sum(nums[l:r+1])`?
A: That's Approach 0 — O(n) per query, which is what this problem's
   `update`+`sumRange` interleaving is specifically designed to make too
   slow at n, calls ~ 3*10^4 each (worst case ~9*10^8 total operations).


================================================================================
RELATED PROBLEMS
================================================================================
    LC 308  Range Sum Query 2D - Mutable    — this topic, 002, 2D BIT
    LC 493  Reverse Pairs                   — this topic, 003, BIT alt. to merge sort
    LC 327  Count of Range Sum              — this topic, 004, BIT alt. to merge sort
    LC 303  Range Sum Query - Immutable     — topic 04, the STATIC version of this exact problem
================================================================================
"""

import random
import time


class NumArray:
    """Fenwick tree (BIT). O(log n) update / sumRange. See THE CORE IDEA."""

    def __init__(self, nums: list[int]):
        self.n = len(nums)
        self.nums = [0] * self.n  # current values, kept in sync for deltas
        self.tree = [0] * (self.n + 1)  # 1-indexed; index 0 unused
        for i, v in enumerate(nums):
            self.update(i, v)

    def update(self, index: int, val: int) -> None:
        delta = val - self.nums[index]
        self.nums[index] = val
        i = index + 1
        while i <= self.n:
            self.tree[i] += delta
            i += i & (-i)

    def _prefix(self, i: int) -> int:
        """Sum of the first i elements (1-indexed count), i.e. nums[0..i-1]."""
        s = 0
        while i > 0:
            s += self.tree[i]
            i -= i & (-i)
        return s

    def sumRange(self, left: int, right: int) -> int:
        return self._prefix(right + 1) - self._prefix(left)


# ------------------------------------------------------------------------
# Oracles / alternatives used only for the tests and benchmark below.
# ------------------------------------------------------------------------
class NumArrayNaive:
    """✗ Priced-not-shipped: O(1) update, O(n) sumRange. Correctness oracle
    and the subject of the benchmark below."""

    def __init__(self, nums: list[int]):
        self.nums = list(nums)

    def update(self, index: int, val: int) -> None:
        self.nums[index] = val

    def sumRange(self, left: int, right: int) -> int:
        return sum(self.nums[left : right + 1])


def run_tests() -> None:
    all_ok = True

    # ------------------------------------------------------------------
    # LeetCode's example.
    # ------------------------------------------------------------------
    print("--- LeetCode example ---")
    na = NumArray([1, 3, 5])
    ok = na.sumRange(0, 2) == 9
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  sumRange(0,2) before update -> {na.sumRange(0, 2)} (want 9)")

    na.update(1, 2)
    ok = na.sumRange(0, 2) == 8
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  sumRange(0,2) after update(1,2) -> {na.sumRange(0, 2)} (want 8)")

    # ------------------------------------------------------------------
    # Edge cases.
    # ------------------------------------------------------------------
    print("\n--- edge cases ---")
    single = NumArray([42])
    ok = single.sumRange(0, 0) == 42
    single.update(0, -5)
    ok &= single.sumRange(0, 0) == -5
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  n=1, update to negative value")

    neg = NumArray([-3, 7, -8, 2])
    ok = neg.sumRange(0, 3) == (-3 + 7 - 8 + 2)
    ok &= neg.sumRange(1, 2) == (7 - 8)
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  negative values sum correctly")

    same = NumArray([5, 5, 5])
    same.update(1, 5)  # update to the SAME value -> delta 0, no-op effect
    ok = same.sumRange(0, 2) == 15
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  update to same value is a harmless no-op")

    # ------------------------------------------------------------------
    # Randomized cross-check vs the O(n) naive oracle.
    # ------------------------------------------------------------------
    print("\n--- randomized cross-check vs naive oracle (500 ops, n=200) ---")
    rng = random.Random(26)
    n = 200
    start = [rng.randint(-100, 100) for _ in range(n)]
    fast = NumArray(start)
    slow = NumArrayNaive(start)
    mismatch = False
    for _ in range(500):
        if rng.random() < 0.5:
            idx = rng.randint(0, n - 1)
            val = rng.randint(-100, 100)
            fast.update(idx, val)
            slow.update(idx, val)
        else:
            l = rng.randint(0, n - 1)
            r = rng.randint(l, n - 1)
            if fast.sumRange(l, r) != slow.sumRange(l, r):
                mismatch = True
    ok = not mismatch
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  500 randomized ops, no mismatch vs naive oracle")

    # ------------------------------------------------------------------
    # BENCHMARK — O(log n) BIT vs O(n) naive resum, measured live.
    # ------------------------------------------------------------------
    print("\n--- benchmark: BIT O(log n) vs naive O(n) resum, mixed workload ---")
    print(f"  {'n':>8} {'ops':>8} {'BIT (ms)':>12} {'naive (ms)':>12} {'speedup':>10}")
    for n in (1_000, 10_000, 30_000):
        rng = random.Random(1)
        start = [rng.randint(-100, 100) for _ in range(n)]
        n_ops = 5_000
        ops = []
        for _ in range(n_ops):
            if rng.random() < 0.5:
                ops.append(("update", rng.randint(0, n - 1), rng.randint(-100, 100)))
            else:
                l = rng.randint(0, n - 1)
                r = rng.randint(l, n - 1)
                ops.append(("query", l, r))

        fast = NumArray(start)
        t0 = time.perf_counter()
        for op, a, b in ops:
            if op == "update":
                fast.update(a, b)
            else:
                fast.sumRange(a, b)
        bit_ms = (time.perf_counter() - t0) * 1000

        slow = NumArrayNaive(start)
        t0 = time.perf_counter()
        for op, a, b in ops:
            if op == "update":
                slow.update(a, b)
            else:
                slow.sumRange(a, b)
        naive_ms = (time.perf_counter() - t0) * 1000

        speedup = naive_ms / bit_ms if bit_ms > 0 else float("inf")
        print(f"  {n:>8} {n_ops:>8} {bit_ms:>12.2f} {naive_ms:>12.2f} {speedup:>9.1f}x")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
