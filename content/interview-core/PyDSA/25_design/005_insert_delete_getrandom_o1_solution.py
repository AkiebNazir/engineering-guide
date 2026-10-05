"""
================================================================================
SOLUTION · LeetCode 380 · Insert Delete GetRandom O(1)                  [Medium]
https://leetcode.com/problems/insert-delete-getrandom-o1/
================================================================================

THE CORE IDEA
--------------
Neither a set nor an array alone gives O(1) for all three operations:

    set alone:     O(1) insert/remove/contains, but NO O(1) random access
                   (no indexing into a set; materializing it into a list
                   just to pick one element is O(n)).
    array alone:   O(1) random access (`arr[randrange(len(arr))]`), but
                   O(n) removal by VALUE (find it, then shift everything
                   after it left).
    array + dict:  O(1) random access (array) AND O(1) removal (dict maps
                   value -> index, so no scan is needed to FIND it) — the
                   remaining problem, shifting on removal, is solved by
                   SWAP-WITH-LAST-THEN-POP instead of shifting.

Swap-pop deletion: to remove `arr[i]`, swap it with `arr[-1]` (the array's
last element), update the dict entry for whichever value just moved INTO
position `i`, then `arr.pop()` the now-redundant last slot. This is O(1)
and — critically — leaves the array with NO gaps, which is exactly what
`getRandom`'s uniform `randrange(len(arr))` needs to stay uniform.


================================================================================
APPROACH 1 · Python set + list(set) for getRandom (brute force, priced,
not coded)
================================================================================
A plain `set` for insert/remove/contains; `getRandom` does
`random.choice(list(self.set))`.

    insert / remove:  O(1) average.
    getRandom:         O(n) — materializing the set into a list every call.

Fails the O(1) requirement on exactly the operation the problem exists to
test. Not coded because it's the direct motivation for Approach 2, not a
distinct technique worth cross-checking against.


================================================================================
APPROACH 2 · Array + value->index dict, swap-with-last-then-pop ✅ (the answer)
================================================================================
    class RandomizedSet:
        def __init__(self):
            self.arr = []            # dense array of current values
            self.index = {}          # value -> its position in self.arr

        def insert(self, val):
            if val in self.index:
                return False
            self.index[val] = len(self.arr)
            self.arr.append(val)
            return True

        def remove(self, val):
            if val not in self.index:
                return False
            i = self.index[val]
            last_val = self.arr[-1]
            self.arr[i] = last_val           # move last element into the gap
            self.index[last_val] = i          # fix its index in the dict
            self.arr.pop()                    # drop the now-redundant last slot
            del self.index[val]
            return True

        def getRandom(self):
            return random.choice(self.arr)    # uniform, array is dense (no gaps)

The self-swap edge case (removing the array's OWN last element) is handled
correctly for free: `last_val == val` in that case, so `self.arr[i] =
last_val` and `self.index[last_val] = i` are harmless no-ops before the
pop — no special branch needed.

    Time: O(1) average per op.     Space: O(n).


================================================================================
VARIANT · What does NOT work: tombstones / "clear the slot" deletion
================================================================================
A tempting alternative deletion: set `arr[i] = None` (a tombstone) instead
of swap-popping, avoiding the "move the last element" bookkeeping.

This BREAKS `getRandom`'s uniformity guarantee — `random.randrange` would
still pick uniformly among ALL indices including tombstoned ones, and
retry-on-`None` skews the distribution toward whichever elements happen
not to be adjacent to recently-tombstoned slots (and degrades toward O(n)
retries as more elements are removed, since the array never actually
shrinks). This is why swap-pop — which keeps the array PHYSICALLY dense,
not just logically dense — is required, not merely convenient.


================================================================================
STEP BY STEP TRACE
================================================================================
    insert(1)   arr=[1]        index={1:0}                returns True
    remove(2)   2 not in index                              returns False
    insert(2)   arr=[1,2]      index={1:0, 2:1}             returns True
    remove(1)   i = index[1] = 0
                last_val = arr[-1] = 2
                arr[0] = 2          -> arr=[2,2] (before pop)
                index[2] = 0
                arr.pop()           -> arr=[2]
                del index[1]        -> index={2:0}           returns True
    insert(2)   2 already in index                          returns False
    getRandom() arr=[2]  -> only choice is 2

    ASCII of remove(1) — 1 is at index 0, last element (2) is swapped in:

        before:  arr = [1, 2]        index = {1:0, 2:1}
                         ^-- remove this (index 0)
        swap:    arr = [2, 2]        (arr[0] overwritten with arr[-1]=2)
        fix idx: index = {1:0, 2:0}  (2's index corrected to 0)
        pop:     arr = [2]           index = {2:0}   (1's entry deleted)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          insert    remove    getRandom   Space   Mutates input?
    ---------------------------------  --------  --------  ----------  ------  ---------------
    set + list(set) per getRandom     O(1)      O(1)      O(n)        O(n)    n/a — design problem
    array + dict, swap-pop ✅         O(1)      O(1)      O(1)        O(n)    n/a — design problem
    array + tombstones (broken)       O(1)      O(1)      O(1)*       O(n)    *not uniform, degrades


================================================================================
EDGE CASES
================================================================================
    remove(val) not present            Must return False, and must not
                                        touch the array/dict at all.
    insert(val) already present        Must return False, no duplicate
                                        stored.
    Removing the array's OWN last
      element                          `last_val == val` — the swap
                                        becomes a harmless self-assignment;
                                        must not corrupt the dict (this is
                                        the boundary case most naive
                                        implementations get wrong first).
    getRandom with exactly one
      element                          Must always return that element,
                                        never raise (constraints guarantee
                                        at least one element exists at
                                        call time, so no empty-array case
                                        to handle).
    Negative values / 0                Valid per constraints
                                        (`-2^31 <= val <= 2^31-1`); a dict
                                        keyed by value handles this with
                                        no special range assumptions
                                        (unlike HashSet/HashMap's
                                        `key % NUM_BUCKETS`, which relied
                                        on a small nonnegative range).


================================================================================
COMMON MISTAKES
================================================================================
1. Using an array-index-based "delete by shifting" (`arr.pop(i)` on an
   arbitrary middle index) — correct, but O(n), defeating the entire O(1)
   requirement; this is the single most common wrong approach for this
   problem.

2. Swap-popping but FORGETTING to update `index[last_val]` — leaves the
   dict pointing the moved value at its OLD index, which is now either
   out of range (if it was the very last index) or holds a DIFFERENT
   value — silently corrupts every future lookup for that value.

3. Deleting `index[val]` BEFORE reading `self.index[val]` to get `i` —
   an ordering bug that loses the index needed to perform the swap at all.

4. Trying to "just clear the slot" (tombstone) instead of swap-popping —
   breaks `getRandom`'s uniformity (see the VARIANT above) even though
   insert/remove still look correct in isolation.

5. Using `random.random()` or a non-uniform selection scheme for
   `getRandom` instead of `random.choice`/`randrange` over the DENSE
   array — any scheme that isn't uniform over the array's live indices
   violates "each element has EQUAL probability."


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: LC 381, "Insert Delete GetRandom O(1) - Duplicates allowed" — how does
   the design change?
A: The dict must map `value -> SET of indices` (not a single index) since
   a value can now occupy multiple array slots. Removal picks ANY one of
   that value's indices to swap-pop (arbitrary choice is fine — duplicates
   are interchangeable), and the moved element's index set must be updated
   the same way, just against a set of indices instead of one.

Q: How would `getRandom` need to change if elements had different
   WEIGHTS (a element should be returned more often than another)?
A: LC 528 "Random Pick with Weight" (topic 27) — prefix sums over the
   weights plus a binary search on a uniform `[0, total)` draw, replacing
   the flat uniform index pick here.

Q: Thread safety for concurrent insert/remove/getRandom?
A: A single coarse lock around all three, same reasoning as LRU Cache —
   each operation's critical section is already O(1), so lock contention
   cost is small relative to correctness risk from fine-grained locking.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 381  Insert Delete GetRandom O(1) - Duplicates allowed — value -> SET of indices
    LC 528  Random Pick with Weight (topic 27)     — prefix sum + binary search, non-uniform picks
    LC 146  LRU Cache (topic 08)                    — same "two structures, kept in sync" discipline
    Topic 01 · Arrays & Hashing                     — the array+dict combination pattern generally
================================================================================
"""

import random
import time
from collections import Counter


class RandomizedSet:
    """Array + value->index dict, swap-with-last-then-pop deletion.
    See THE CORE IDEA above."""

    def __init__(self):
        self.arr: list[int] = []
        self.index: dict[int, int] = {}

    def insert(self, val: int) -> bool:
        if val in self.index:
            return False
        self.index[val] = len(self.arr)
        self.arr.append(val)
        return True

    def remove(self, val: int) -> bool:
        if val not in self.index:
            return False
        i = self.index[val]
        last_val = self.arr[-1]
        self.arr[i] = last_val  # move last element into the gap (no-op if val IS the last element)
        self.index[last_val] = i
        self.arr.pop()
        del self.index[val]
        return True

    def getRandom(self) -> int:
        return random.choice(self.arr)


# ------------------------------------------------------------------------
# Alternatives / oracles.
# ------------------------------------------------------------------------
class RandomizedSetBruteForce:
    """Approach 1: plain set + list(set) materialized on every getRandom.
    O(n) getRandom. Used as a correctness oracle for insert/remove."""

    def __init__(self):
        self.s: set[int] = set()

    def insert(self, val: int) -> bool:
        if val in self.s:
            return False
        self.s.add(val)
        return True

    def remove(self, val: int) -> bool:
        if val not in self.s:
            return False
        self.s.remove(val)
        return True

    def getRandom(self) -> int:
        return random.choice(list(self.s))


# ==============================================================================
# TESTS — run:  python 005_insert_delete_getrandom_o1_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    # ------------------------------------------------------------------
    # Correctness: LeetCode's canonical example (insert/remove booleans).
    # ------------------------------------------------------------------
    print("--- correctness: insert/remove return values ---")
    rs = RandomizedSet()
    script = [
        ("insert", 1, True), ("remove", 2, False), ("insert", 2, True),
        ("remove", 1, True), ("insert", 2, False),
    ]
    results = [getattr(rs, op)(val) for op, val, _ in script]
    wants = [w for _, _, w in script]
    ok = results == wants
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  results={results}  (want {wants})")
    ok = rs.getRandom() == 2
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  getRandom() with single remaining element == 2")

    # ------------------------------------------------------------------
    # Self-swap edge case: removing the array's own last element.
    # ------------------------------------------------------------------
    print("\n--- self-swap edge case (removing the array's last element) ---")
    rs2 = RandomizedSet()
    rs2.insert(5)
    rs2.insert(9)  # arr=[5,9], index={5:0, 9:1}
    ok = rs2.remove(9) is True  # 9 IS arr[-1]; swap is a self-assignment
    ok &= rs2.arr == [5] and rs2.index == {5: 0}
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  removing the last element doesn't corrupt state  arr={rs2.arr} index={rs2.index}")

    # ------------------------------------------------------------------
    # Randomized structural cross-check vs the brute-force set oracle
    # (compares the SET of live elements after each op, not raw internals).
    # ------------------------------------------------------------------
    print("\n--- randomized cross-check vs set oracle (3000 ops) ---")
    rng = random.Random(17)
    ours = RandomizedSet()
    oracle = RandomizedSetBruteForce()
    mismatch = False
    for _ in range(3000):
        val = rng.randint(0, 200)
        op = rng.choice(["insert", "remove"])
        r1 = getattr(ours, op)(val)
        r2 = getattr(oracle, op)(val)
        if r1 != r2:
            mismatch = True
        if set(ours.arr) != oracle.s or len(ours.arr) != len(set(ours.arr)):
            mismatch = True  # array must be a dense, duplicate-free mirror of the set
    all_ok &= not mismatch
    print(f"{'PASS' if not mismatch else 'FAIL'}  3000 randomized ops, live-element set matches oracle, array stays dense/dedup'd")

    # ------------------------------------------------------------------
    # getRandom uniformity — chi-square-flavored sanity check: with a
    # dense array of 5 elements and swap-pop deletion never leaving gaps,
    # every element should get roughly equal draws over many samples.
    # ------------------------------------------------------------------
    print("\n--- getRandom() uniformity over 50,000 draws, 5 elements ---")
    rs3 = RandomizedSet()
    for v in range(5):
        rs3.insert(v)
    counts = Counter(rs3.getRandom() for _ in range(50_000))
    expected = 50_000 / 5
    max_dev_pct = max(abs(counts[v] - expected) / expected * 100 for v in range(5))
    ok = max_dev_pct < 5.0  # generous tolerance; true uniform draw should land well under this
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  counts={dict(counts)}  max deviation from uniform: {max_dev_pct:.2f}%")

    # ------------------------------------------------------------------
    # Also demonstrate WHY tombstoning breaks uniformity: after removing
    # most elements via tombstones (None placeholders, no compaction), a
    # naive retry-on-None getRandom skews toward whichever value happens
    # to still occupy a low index, and burns increasingly many retries.
    # ------------------------------------------------------------------
    print("\n--- why tombstones break getRandom: retry count grows as the array fills with gaps ---")
    arr_with_gaps = [None] * 9998 + [777, 888]  # 9998 tombstones, 2 live values
    retries = 0
    rng2 = random.Random(5)
    picks = []
    for _ in range(20):
        while True:
            retries += 1
            candidate = arr_with_gaps[rng2.randrange(len(arr_with_gaps))]
            if candidate is not None:
                picks.append(candidate)
                break
    avg_retries_per_pick = retries / 20
    print(f"  20 picks needed {retries} total draws ({avg_retries_per_pick:.0f} retries/pick on average) "
          f"once {len(arr_with_gaps) - 2} of {len(arr_with_gaps)} slots are stale tombstones — "
          f"this is why swap-pop (keeping the array PHYSICALLY dense) is required, not optional.")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
