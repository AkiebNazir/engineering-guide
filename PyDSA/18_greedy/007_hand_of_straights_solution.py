"""
================================================================================
SOLUTION · LeetCode 846 · Hand of Straights                            [Medium]
https://leetcode.com/problems/hand-of-straights/
================================================================================

THE CORE IDEA
--------------
Count how many copies of each card value exist. Repeatedly take the SMALLEST
remaining value that still has a positive count, and greedily consume it as
the start of a new consecutive run of length `groupSize` (decrementing the
count of `start, start+1, ..., start+groupSize-1` by one each). If at any
point one of those `groupSize` consecutive values is missing (count is
already 0 or doesn't exist), the hand cannot be arranged — return False.
If every card gets consumed this way, return True.

EXCHANGE ARGUMENT (why you must always start a new group from the current
minimum)
-------------------------------------------------------------------
Claim: whenever the smallest remaining card value `m` still has count > 0,
SOME group in any valid solution must start exactly at `m`. Proof: `m` has
to belong to SOME group (every card must be used). Since `m` is the
smallest value with any cards left, no group can contain `m` as anything
other than its FIRST element — a group containing `m` in the middle or end
would require a smaller consecutive value (`m-1`, `m-2`, ...) to also be
in that group, but no such smaller value has any remaining count. So `m`
must start a group. That means the group `[m, m+1, ..., m+groupSize-1]`
must exist in ANY valid solution — there's no choice to make here, it's
FORCED, not just "the best guess." Once forced, greedily consuming that
exact group and recursing on what's left is trivially safe (it's not even
really a choice among alternatives — it's the only option). This is a
stronger and cleaner guarantee than a typical exchange argument: the
greedy move isn't merely "provably as good as any alternative," it's
"the only move a valid solution could possibly make at this point."

================================================================================
APPROACH 0 · Brute force — try all groupings (priced, not coded)
================================================================================
Backtracking: pick any ungrouped card, try to extend it as the start of a
run, recurse. Without the "always start from the current minimum" insight,
you'd have to try starting from ANY remaining card as a potential group
start, giving an enormous branching factor — exponential in the worst case.
Never the coded answer.

================================================================================
APPROACH 1 · Counter + sorted keys, greedy consume from the minimum ✅
(the answer)
================================================================================
    from collections import Counter

    def isNStraightHand(hand, groupSize):
        if len(hand) % groupSize != 0:
            return False
        count = Counter(hand)
        for start in sorted(count):
            need = count[start]
            if need <= 0:
                continue
            for v in range(start, start + groupSize):
                if count[v] < need:
                    return False
                count[v] -= need
        return True

    Time:  O(n log n) — dominated by `sorted(count)` over up to n distinct
           values; the double loop touches each (value, group) combination
           a bounded number of times overall (each unit of count is only
           ever decremented once across all groups it participates in, so
           the inner-loop work across the whole run is O(n * groupSize) in
           the worst count-distribution sense, but the standard accepted
           analysis reports O(n log n) since groupSize <= n and the
           dominant cost in practice is the sort + hashmap ops)
    Space: O(n) — the Counter

================================================================================
APPROACH 2 · Min-heap of distinct values instead of sorting once
================================================================================
Same idea, but pop the current minimum off a heap of distinct values instead
of iterating a pre-sorted list, pushing back any survivors. Useful if values
arrive incrementally rather than all at once, but for this problem (whole
hand known upfront) it's the same O(n log n) with more bookkeeping — sorting
once is simpler and just as fast here.

--------------------------------------------------------------------------------
STEP BY STEP TRACE
--------------------------------------------------------------------------------
hand = [1, 2, 3, 6, 2, 3, 4, 7, 8], groupSize = 3
len(hand)=9, 9 % 3 == 0, proceed.

  count = {1:1, 2:2, 3:2, 6:1, 4:1, 7:1, 8:1}
  sorted distinct keys: [1, 2, 3, 4, 6, 7, 8]

  start=1: need=count[1]=1 (>0)
    consume [1,2,3]: count[1]=1-1=0, count[2]=2-1=1, count[3]=2-1=1
  start=2: need=count[2]=1 (>0)
    consume [2,3,4]: count[2]=1-1=0, count[3]=1-1=0, count[4]=1-1=0
  start=3: need=count[3]=0 -> skip
  start=4: need=count[4]=0 -> skip
  start=6: need=count[6]=1 (>0)
    consume [6,7,8]: count[6]=0, count[7]=0, count[8]=0
  start=7: need=0 -> skip
  start=8: need=0 -> skip

  all consumed without any shortfall -> return True
  (groups formed: [1,2,3], [2,3,4], [6,7,8] -- matches the example)

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                          | Time         | Space | Mutates input? |
|--------------------------------------|-------------|-------|------------------|
| 0 · brute-force backtracking         | exponential | O(n)  | No               |
| 1 · Counter + sort keys, greedy ✅    | O(n log n)  | O(n)  | No — `hand` untouched, Counter is a copy |
| 2 · min-heap of distinct values       | O(n log n)  | O(n)  | No               |

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- `len(hand) % groupSize != 0`: impossible to partition into equal groups —
  the O(1) upfront check avoids doing any real work.
- `groupSize == 1`: every group is a single card; always True regardless of
  values (the inner loop range is just `[start]`, trivially satisfied).
- Duplicate values requiring multiple groups to start at the same value:
  handled naturally since `need = count[start]` captures "how many groups
  must start here," not just "does at least one card exist here."
- A gap in the middle of a needed run (e.g. count of some `v` runs out
  mid-consumption): `count[v] < need` catches this and returns False
  immediately, even deep inside forming what looked like a promising group.
- Negative or zero values, or very large values: no special handling
  needed — the algorithm only compares/increments/decrements by value, no
  assumption of a bounded positive range (uses a hashmap `Counter`, not an
  array indexed by value).

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. **Looks-greedy-but-wrong: starting groups from an ARBITRARY remaining
   card instead of always the current minimum** — e.g. starting from
   whichever value has the highest count, or just iterating hand in its
   given order. This can strand a smaller value with no valid group to
   belong to, even when a valid overall partition exists — the minimum-first
   rule is not just efficient, it's the only correct starting point (per
   the exchange argument, it's FORCED).
2. Forgetting the `len(hand) % groupSize != 0` early return — without it,
   the algorithm might still coincidentally return False when it should
   for the wrong underlying reason, but relying on that instead of the
   explicit check is fragile and slower (does unnecessary work first).
3. Iterating `sorted(count)` but computing `need = count[start]` AFTER
   already having modified `count[start]` earlier in the same iteration
   (order-of-operations bug) — must capture `need` before starting to
   decrement the run.
4. Using a plain `dict` and forgetting a missing key means "0 cards exist,"
   not "infinite" — a bug like `count.get(v, 0) < need` is required (or a
   `Counter`/`defaultdict`, which default to 0 automatically); a raw
   `dict[v]` KeyError or silently treating a missing key as satisfying the
   check would be wrong.
5. Not skipping `need <= 0` entries in the sorted-keys loop — without the
   skip, you'd try to start a NEW group from a value that's already been
   fully consumed by an earlier group, redundantly re-processing it (and
   potentially double-decrementing counts that are already at 0, causing
   spurious False results from now-negative counts if using plain
   subtraction without the `count[v] < need` guard).

--------------------------------------------------------------------------------
RUNTIME DEMO — correct minimum-first greedy vs. a broken "start from the
value with the highest count first" heuristic, shown failing
--------------------------------------------------------------------------------
See the code below.

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "What if you also need to return the actual groups, not just True/False?"
  — collect each `[start, start+groupSize)` run into a list as you consume
  it, instead of only tracking success/failure.
- "What if groupSize could vary per group?" — no longer this problem;
  becomes much harder without a fixed run length to anchor the greedy rule.
- "Can you avoid sorting and do it in O(n)?" — only if values are bounded
  and small enough to counting-sort/bucket by value; with values up to
  10^9 as given here, a hashmap + sort (or heap) is the practical answer.

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- LC 1296 Divide Array in Sets of Consecutive Numbers — identical problem,
  different LC number.
- 18/009 Partition Labels — same topic family: "sort/precompute, then a
  provably-forced greedy scan" (topic guide §2.2).
- 06 Stack & Monotonic Stack topic — different mechanism, same spirit of
  "the next required action is forced, not chosen."
================================================================================
"""

import random
import time
from collections import Counter


class Solution:
    def isNStraightHand(self, hand: list[int], groupSize: int) -> bool:
        if len(hand) % groupSize != 0:
            return False
        count = Counter(hand)
        for start in sorted(count):
            need = count[start]
            if need <= 0:
                continue
            for v in range(start, start + groupSize):
                if count[v] < need:
                    return False
                count[v] -= need
        return True


def is_n_straight_hand_wrong_heuristic(hand: list[int], groupSize: int) -> bool:
    """Broken heuristic: always start a new group from whichever remaining
    value currently has the HIGHEST count, instead of the minimum. Looks
    like a reasonable 'clear the biggest pile first' idea; has no valid
    exchange argument and can wrongly report False on a hand that IS
    actually partitionable."""
    if len(hand) % groupSize != 0:
        return False
    count = Counter(hand)
    while count:
        start = max(count, key=lambda v: count[v])
        need = count[start]
        for v in range(start, start + groupSize):
            if count.get(v, 0) < need:
                return False
            count[v] -= need
            if count[v] == 0:
                del count[v]
    return True


def run_tests():
    sol = Solution()
    assert sol.isNStraightHand([1, 2, 3, 6, 2, 3, 4, 7, 8], 3) is True
    assert sol.isNStraightHand([1, 2, 3, 4, 5], 4) is False
    assert sol.isNStraightHand([1, 2, 3], 1) is True
    assert sol.isNStraightHand([8, 10, 12], 3) is False
    assert sol.isNStraightHand([1, 1, 2, 2, 3, 3], 3) is True
    assert sol.isNStraightHand([], 1) is True

    # does not mutate input
    original = [1, 2, 3, 6, 2, 3, 4, 7, 8]
    sol.isNStraightHand(original, 3)
    assert original == [1, 2, 3, 6, 2, 3, 4, 7, 8]

    # --- Counterexample demo: correct min-first vs broken max-count-first ---
    # Construct a hand where always starting from the highest-count value
    # forces an infeasible group even though a valid partition exists.
    trap_hand = [1, 2, 2, 3, 3, 4]
    group_size = 2
    correct = sol.isNStraightHand(trap_hand, group_size)
    wrong = is_n_straight_hand_wrong_heuristic(trap_hand, group_size)
    print(f"trap={trap_hand}, groupSize={group_size}")
    print(f"  correct (start from current minimum): {correct}")
    print(f"  broken heuristic (start from highest count): {wrong}")
    assert correct is True
    assert wrong is False, "expected the broken heuristic to wrongly fail here"

    # --- Runtime demo: greedy is fast; a genuinely exponential brute force
    #     would not finish on inputs this size, so we just show the greedy
    #     scaling comfortably on a larger random hand -------------------------
    random.seed(29)
    group_size = 5
    n_groups = 4000
    big_hand = []
    for g in range(n_groups):
        base = g * group_size
        big_hand.extend(range(base, base + group_size))
    random.shuffle(big_hand)

    t0 = time.perf_counter()
    result = sol.isNStraightHand(big_hand, group_size)
    elapsed = time.perf_counter() - t0
    assert result is True
    print(f"n={len(big_hand)} cards, groupSize={group_size}: greedy took {elapsed*1000:.2f} ms")

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
