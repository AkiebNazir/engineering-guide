"""
================================================================================
SOLUTION · LeetCode 710 · Random Pick with Blacklist                  [Hard]
https://leetcode.com/problems/random-pick-with-blacklist/
================================================================================

THE CORE IDEA
--------------
Let `whitelist_size = n - len(blacklist)` -- the count of valid (non-
blacklisted) numbers. If we draw a uniform random integer in the SHRUNK range
`[0, whitelist_size - 1]` instead of the full `[0, n - 1]`, every draw is
automatically a "hit" -- no rejection needed, no unbounded resampling. The
only problem: some numbers INSIDE `[0, whitelist_size - 1]` might themselves
be blacklisted. Fix each one individually, once, in the constructor: for
every blacklisted number `b < whitelist_size`, remap it to some valid,
non-blacklisted number `>= whitelist_size` (numbers at or above
`whitelist_size` that AREN'T blacklisted are exactly as numerous as the
blacklisted numbers below `whitelist_size`, by a counting argument -- see
below -- so every one of them finds a home). Build that remap dict once in
O(B) (B = len(blacklist)); every `pick()` afterward does ONE random() call
plus an O(1) dict lookup.

Counting argument for why the remap always balances: split `[0, n-1]` into
"low" = `[0, whitelist_size)` and "high" = `[whitelist_size, n)`. Let
`k` = number of blacklisted values in "low". "high" has exactly
`len(blacklist) - k` blacklisted values (since blacklist has
`len(blacklist)` total), and "high" has `n - whitelist_size = len(blacklist)`
slots, so "high" has `len(blacklist) - (len(blacklist) - k) = k` VALID
(non-blacklisted) values -- exactly enough to give each of the `k` low-side
blacklisted numbers a distinct valid remap target.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (reject-and-resample, price it): draw uniformly from
`[0, n-1]`; if the draw is blacklisted, draw again. Correct -- every
non-blacklisted value still ends up equally likely -- and O(1) extra space
beyond the blacklist set. But the EXPECTED number of random() calls per
pick is `n / whitelist_size`, which is unbounded as the blacklist fraction
approaches 1 (no upper bound on any single call's retry count, just
increasingly small probability of a long streak). Fine when blacklist is
small relative to n; actively bad when it's large. `_RejectResample` below
implements this, instrumented to COUNT actual attempts, for the runtime demo.

Approach 1 (chosen) -- shrink the range + O(B) one-time remap. Draw
uniformly from `[0, whitelist_size - 1]` (always a hit), remap the handful
of blacklisted values that land inside that shrunk range to valid values
outside it, built once in the constructor. O(B) preprocessing, O(1) time and
EXACTLY ONE random() call per pick -- the asymptotically and practically
superior approach, and the one this problem is explicitly designed to elicit
("minimize calls to the random function" in the prompt is the tell).


================================================================================
STEP BY STEP TRACE
================================================================================
n = 7, blacklist = [2, 3, 5]. whitelist_size = 7 - 3 = 4.
Valid (whitelisted) numbers: {0, 1, 4, 6}.
"low" range for picks: [0, 3]. Blacklisted numbers inside low range: {2, 3}
(5 is already >= whitelist_size=4, so it needs no remap).

Build remap: blackset = {2, 3, 5}. Start hi = n - 1 = 6.
    b = 2 (< 4, needs remap):
        hi=6 not in blackset -> remap[2] = 6, hi becomes 5
    b = 3 (< 4, needs remap):
        hi=5 IS in blackset -> hi becomes 4
        hi=4 not in blackset -> remap[3] = 4, hi becomes 3
    b = 5 (>= whitelist_size=4, no remap needed) -> skipped

Final remap = {2: 6, 3: 4}.

pick(): draw idx uniformly in [0, 3].
    idx=0 -> not in remap -> return 0
    idx=1 -> not in remap -> return 1
    idx=2 -> remap[2]=6   -> return 6
    idx=3 -> remap[3]=4   -> return 4

Every draw of idx in {0,1,2,3} (each probability 1/4) maps to a DISTINCT
element of {0, 1, 6, 4} -- exactly the whitelist, each with probability
exactly 1/4. Number 5, though blacklisted, was never a valid pick target
to begin with (it's outside the draw range and not a remap target), and
numbers 2 and 3 (blacklisted, inside the draw range) are never RETURNED --
only used as lookup keys that redirect to 6 and 4.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time (pick)         Space   Mutates input?
    -------------------------------  ------------------  ------  --------------
    Reject-and-resample [priced]     O(n/whitelist_size)  O(B)    no
                                      expected, UNBOUNDED
                                      worst case per call
    Shrink-range + O(B) remap [chosen] O(1), exactly       O(B)    no
                                      1 random() call

    Constructor cost for the chosen approach: O(B) time (one pass building
    the remap dict), O(B) space (blackset + remap dict, both bounded by
    len(blacklist)) -- independent of n, which matters since n can be 10^9
    and can never be materialized as an array.


================================================================================
EDGE CASES
================================================================================
    blacklist is empty          -> whitelist_size == n, remap dict stays
                                    empty, pick() degenerates to a plain
                                    random.randint(0, n-1).
    blacklist covers almost all
    of [0, n-1]                 -> exactly the case that breaks reject-and-
                                    resample's expected call count; the
                                    chosen approach is UNAFFECTED, since its
                                    per-pick cost never depends on the
                                    blacklist fraction, only preprocessing
                                    does (O(B)).
    n == 1 (blacklist must be
    empty per constraints)      -> whitelist_size == 1, only 0 is ever
                                    drawn.
    a blacklisted value already
    >= whitelist_size           -> correctly needs NO remap entry (it was
                                    never going to be drawn since draws are
                                    restricted to [0, whitelist_size-1]) --
                                    skipping it is what keeps the remap
                                    O(B) instead of O(n).
    duplicate hi values          -> the `while hi in blackset: hi -= 1`
                                    scan-back guarantees hi always lands on
                                    a valid, previously-unused number before
                                    being consumed as a remap target.


================================================================================
COMMON MISTAKES
================================================================================
1. Reject-and-resample as the FINAL answer without acknowledging its
   unbounded-per-call cost -- correct in expectation, but the problem
   explicitly asks to minimize random() calls; this is the wrong asymptotic
   answer once blacklist is large relative to n.
2. Remapping EVERY blacklisted value, including ones already
   `>= whitelist_size` -- wasted work (they're never drawn) and, worse, can
   corrupt the remap if you're not careful, since a "remap target" search
   might collide with a low-range blacklisted number that also needs a
   target.
3. Letting the remap-target search (`hi`) forget to skip values already
   blacklisted OR already claimed as another remap target -- without the
   `while hi in blackset: hi -= 1` guard (and decrementing hi after each
   assignment), two low-range blacklisted numbers can be remapped to the
   SAME high-range number, breaking uniformity (that number becomes twice
   as likely to be picked).
4. Materializing the whitelist as an explicit array (`[x for x in
   range(n) if x not in blackset]`) -- correct but O(n) space and O(n)
   construction time, infeasible when n is 10^9; the whole point of this
   problem is doing it in O(B).


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "What if pick() needs to be thread-safe / called concurrently?" -> the
  remap dict is read-only after construction, so concurrent pick() calls
  are safe as long as the underlying random source is (Python's `random`
  module is not guaranteed thread-safe for perfectly uniform interleaving,
  but no shared mutable state is written by pick() itself here).
- "What if blacklist can change after construction (add/remove entries)?"
  -> the O(B) remap would need to be rebuilt (or incrementally patched),
  losing the "build once" guarantee; this problem's constraints assume a
  fixed blacklist for the object's lifetime.
- "Why not just use reservoir sampling here?" -> reservoir sampling solves
  "pick uniformly from a STREAM of unknown length in one pass" (this
  topic's 002/003); here the domain size n and exclusions are known
  upfront, so the shrink-and-remap approach is strictly better (O(1) pick,
  vs reservoir's O(1) space but requiring a full pass per pick if replayed
  from scratch).


================================================================================
RELATED PROBLEMS
================================================================================
- 002 Random Pick Index / 003 Linked List Random Node (this topic) --
  reservoir sampling for unknown-length streams, a different tool for a
  different constraint (domain unknown vs domain known-but-punctured).
- 004 Random Pick with Weight (this topic) -- prefix sum + binary search;
  both problems share the "O(1) or O(log n) pick after O(n)-ish
  preprocessing" shape, but weight buckets vs blacklist remapping are
  different bijections.
- Insert Delete GetRandom O(1) (LC 380) -- another "O(1) uniform pick"
  design problem, solved with an array + index map instead of a remap dict.
================================================================================
"""

import random
import time


class Solution:
    def __init__(self, n: int, blacklist: list[int]):
        self.whitelist_size = n - len(blacklist)
        blackset = set(blacklist)
        self.remap: dict[int, int] = {}

        hi = n - 1
        for b in blacklist:
            if b >= self.whitelist_size:
                # Already outside the shrunk draw range -- never drawn,
                # no remap needed.
                continue
            while hi in blackset:
                hi -= 1
            self.remap[b] = hi
            hi -= 1

    def pick(self) -> int:
        idx = random.randint(0, self.whitelist_size - 1)
        return self.remap.get(idx, idx)


class _RejectResample:
    """The O(1)-space-ish naive alternative: draw from the full range,
    reject and redraw on a blacklist hit. Instrumented to COUNT attempts
    per pick for the runtime demo -- never the shipped answer."""

    def __init__(self, n: int, blacklist: list[int]):
        self.n = n
        self.blackset = set(blacklist)
        self.last_attempts = 0

    def pick(self) -> int:
        attempts = 0
        while True:
            attempts += 1
            v = random.randint(0, self.n - 1)
            if v not in self.blackset:
                self.last_attempts = attempts
                return v


def run_tests() -> None:
    all_ok = True

    def check_uniform_over_whitelist(n: int, blacklist: list[int], trials: int = 20_000) -> bool:
        sol = Solution(n, blacklist)
        whitelist = set(range(n)) - set(blacklist)
        seen = set()
        for _ in range(trials):
            v = sol.pick()
            if v in blacklist or not (0 <= v < n):
                return False
            seen.add(v)
        return seen == whitelist

    cases = [
        (7, [2, 3, 5]),
        (5, [0, 1, 2, 3]),
        (10, []),
        (2, [0]),
        (1_000, list(range(950, 1000))),
    ]
    for n, blacklist in cases:
        ok = check_uniform_over_whitelist(n, blacklist)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n}, blacklist={blacklist} -- "
              f"20000 picks all valid and every whitelisted value observed")

    print()
    print("UNIFORMITY DEMO -- empirical pick frequency vs 1/whitelist_size")
    print("-" * 72)
    n, blacklist = 20, [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]  # 10 whitelisted values
    sol = Solution(n, blacklist)
    whitelist_size = n - len(blacklist)
    counts: dict[int, int] = {}
    trials = 200_000
    random.seed(42)
    for _ in range(trials):
        v = sol.pick()
        counts[v] = counts.get(v, 0) + 1
    expected_frac = 1 / whitelist_size
    max_dev = max(abs(c / trials - expected_frac) / expected_frac for c in counts.values())
    uniform_ok = len(counts) == whitelist_size and max_dev < 0.05
    all_ok &= uniform_ok
    print(f"n={n}, blacklist={blacklist}, {trials} picks, whitelist_size={whitelist_size}")
    print(f"  expected frequency per value: {expected_frac:.4f}")
    print(f"  max deviation from expected:  {max_dev * 100:.2f}%")
    print(f"{'PASS' if uniform_ok else 'FAIL'}  all {whitelist_size} whitelisted values seen, "
          f"within 5% of uniform")

    print()
    print("RUNTIME DEMO -- reject-and-resample attempt counts vs O(1) remap, "
          "large blacklist fraction")
    print("-" * 72)
    n = 10_000
    blacklist = list(range(1, n))  # blacklist 9999 of 10000 -> only {0} whitelisted
    random.seed(5)

    naive = _RejectResample(n, blacklist)
    naive_attempts_total = 0
    naive_picks = 500
    t0 = time.perf_counter()
    for _ in range(naive_picks):
        naive.pick()
        naive_attempts_total += naive.last_attempts
    naive_ms = (time.perf_counter() - t0) * 1000

    fast = Solution(n, blacklist)
    t0 = time.perf_counter()
    for _ in range(naive_picks):
        fast.pick()
    fast_ms = (time.perf_counter() - t0) * 1000

    avg_attempts = naive_attempts_total / naive_picks
    print(f"n={n}, blacklist covers {len(blacklist)}/{n} values "
          f"(whitelist_size={n - len(blacklist)}):")
    print(f"  reject-and-resample: {naive_picks} picks, "
          f"{naive_attempts_total} total random() calls "
          f"({avg_attempts:.1f} avg attempts/pick), {naive_ms:8.2f} ms")
    print(f"  O(1) remap:          {naive_picks} picks, "
          f"{naive_picks} total random() calls (1.0 avg attempts/pick), "
          f"{fast_ms:8.2f} ms")
    demo_ok = avg_attempts > 50  # with whitelist_size=1/10000, expected ~10000 attempts/pick
    all_ok &= demo_ok
    print(f"{'PASS' if demo_ok else 'FAIL'}  measured: reject-and-resample needed "
          f"{avg_attempts:.1f}x more random() calls per pick on average than the "
          f"O(1) remap approach's constant 1 -- exactly the unbounded-blowup "
          f"failure mode the chosen approach avoids")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
