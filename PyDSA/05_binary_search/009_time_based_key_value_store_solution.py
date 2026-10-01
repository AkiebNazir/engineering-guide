"""
================================================================================
SOLUTION · LeetCode 981 · Time Based Key-Value Store                   [Medium]
https://leetcode.com/problems/time-based-key-value-store/
================================================================================

THE CORE IDEA
--------------
No oracle function here, and no pre-existing sorted array either — but the
data BECOMES sorted for free, because the problem guarantees `set` is called
with STRICTLY INCREASING timestamps per key. So `store[key]` can simply be a
plain Python list that we append to on every `set` — it is sorted by
construction, with zero extra work.

`get(key, timestamp)` then asks: "what is the value at the LARGEST recorded
timestamp <= the query timestamp?" That is exactly `bisect_right`'s
job — find the insertion point for `timestamp` that keeps the list sorted
(inserting AFTER any equal entries), then step one back to land on the
last entry that is `<= timestamp`:

    store[key] = [(t1, v1), (t2, v2), ...]     # t1 < t2 < ... (append-only)

    idx = bisect_right(timestamps, timestamp) - 1
    return values[idx] if idx >= 0 else ""

This is topic guide §1.6's interactive-oracle-adjacent case: there's no
black-box function to call, but recognising "an append-only, always-sorted
list" as a binary-search target — rather than reaching for a linear scan or
building an interval tree — is the actual skill.


================================================================================
WHY `bisect_right(...) - 1`, NOT `bisect_left`
================================================================================
We want the RIGHTMOST timestamp `<= query`, not the leftmost `>= query` (that
would be problem 002's `bisect_left` shape, solving a different question).
`bisect_right(timestamps, t)` returns the index one past the last entry
equal to `t` (or the insertion point if `t` isn't present) — subtracting 1
lands exactly on "the last entry that is `<= t`," which is precisely what
"most recent value at or before this timestamp" means. Using `bisect_left`
instead would, on an EXACT timestamp match, point at that entry directly
(off by one in the other direction) — it happens to still work for an exact
match, but is wrong the moment the query timestamp falls strictly BETWEEN
two recorded timestamps, landing one entry too late instead of using the
most recent valid one.


================================================================================
STEP BY STEP TRACE
================================================================================
set("foo", "bar",  1)
set("foo", "bar2", 4)
set("foo", "bar3", 7)

    store["foo"] timestamps = [1, 4, 7]     values = ["bar", "bar2", "bar3"]

get("foo", 5):
    bisect_right([1,4,7], 5) = 2      (5 would insert between 4 and 7)
    idx = 2 - 1 = 1  ->  values[1] = "bar2"   ✓ (4 is the latest ts <= 5)

get("foo", 4):
    bisect_right([1,4,7], 4) = 2      (inserts AFTER the existing 4, since
                                        bisect_right places ties to the right)
    idx = 2 - 1 = 1  ->  values[1] = "bar2"   ✓ (exact match at ts=4)

get("foo", 0):
    bisect_right([1,4,7], 0) = 0      (0 would insert before everything)
    idx = 0 - 1 = -1  ->  no valid entry -> return ""   ✓


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              set        get         Space           Mutates input?
    -------------------------------------  ---------  ----------  --------------  ---------------
    Linear scan on get (list, unsorted     O(1)       O(m)        O(total sets)   no (own storage)
      lookup, m = entries for that key)
    Sorted list + bisect on get ✅         O(1)       O(log m)    O(total sets)   no (own storage)
                                           amortized*
    Balanced BST / sorted container per key O(log m)  O(log m)    O(total sets)   no

    * append() is O(1) amortized; the list is already sorted because `set`
      calls arrive in strictly increasing timestamp order per key — no
      re-sorting is ever needed.


================================================================================
EDGE CASES
================================================================================
    get() called before any set() for that key -> key missing entirely from
                                                    the dict; must return "",
                                                    not raise KeyError.
    get() with timestamp before the first set()  -> bisect_right returns 0,
                                                    idx becomes -1: no valid
                                                    entry, return "".
    get() with timestamp exactly matching a set() timestamp -> must return
                                                    THAT value (see the trace's
                                                    ts=4 case, the tie-breaking
                                                    detail bisect_right handles).
    get() with timestamp after every set()        -> bisect_right returns
                                                    len(timestamps), idx points
                                                    at the last entry, correct.
    Same key, many sets over time                  -> list only ever grows by
                                                    append; get() scales with
                                                    log(entries for THAT key),
                                                    not total entries overall.


================================================================================
COMMON MISTAKES
================================================================================
1. Using `bisect_left` instead of `bisect_right` — subtly wrong on non-exact
   matches (see WHY above); the two only coincide when the query timestamp
   happens to not be in the list at all... actually they coincide in FEWER
   cases than that. Trace both against ts=4 in the example above to see the
   divergence.
2. Re-sorting the list inside `get()` "to be safe" — unnecessary given the
   problem's strictly-increasing-timestamp guarantee, and turns every `get`
   into O(m log m) for no reason.
3. Storing entries in a dict keyed by timestamp instead of a list — loses
   the O(log m) binary-search access pattern entirely; a plain dict has no
   notion of "nearest key <= t" without also maintaining a sorted key list,
   which is exactly what the list-plus-bisect approach already is.
4. Forgetting the `idx < 0` guard — indexing `values[-1]` in Python silently
   wraps to the LAST element instead of raising, so an off-by-one here
   returns a plausible-looking WRONG answer instead of an obvious crash —
   a classic Python-specific footgun worth naming explicitly.
5. Using a single global list across all keys instead of one list per key —
   forces filtering by key on every get(), turning O(log m) into O(n) or
   O(n log n) across the whole store.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if `set` timestamps were NOT guaranteed increasing (could arrive out
   of order)?
A: `list.append` no longer keeps the list sorted; you'd need
   `bisect.insort` on every `set` (O(m) per insert, due to the shift), or
   switch to a balanced structure (e.g. a sorted-container / skip list) for
   O(log m) insert and O(log m) query.

Q: How would you support DELETE (removing a specific timestamped value)?
A: A plain list makes deletion O(m) (find + shift). A more delete-friendly
   structure (balanced BST, or a dict of timestamp -> value plus a separate
   sorted key structure like `sortedcontainers.SortedList`) trades some
   insert simplicity for O(log m) delete too.

Q: What if you needed the FIRST value at or after a timestamp instead of the
   most recent at or before?
A: Swap to `bisect_left(timestamps, t)` directly (no `-1`), landing on the
   first entry `>= t` — the mirror-image query.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 35   Search Insert Position         — the bare bisect_left mechanism (002)
                                              this problem's get() is bisect_right
                                              applied the other direction
    LC 729  My Calendar I                  — another "binary search over an
                                              append/insert-maintained sorted
                                              structure" design problem
    LC 1146 Snapshot Array                 — same "list of (timestamp, value)
                                              pairs per key + bisect" pattern,
                                              applied to array indices instead
                                              of string keys
================================================================================
"""

import bisect
import random
import time
from collections import defaultdict
from typing import List, Tuple


class TimeMap:
    def __init__(self):
        """One append-only, timestamp-sorted list per key. O(1) init."""
        self._store: dict[str, List[Tuple[int, str]]] = defaultdict(list)

    def set(self, key: str, value: str, timestamp: int) -> None:
        """O(1) amortized: append only — timestamps arrive strictly
        increasing per key, per the problem's guarantee, so the list stays
        sorted with no extra work."""
        self._store[key].append((timestamp, value))

    def get(self, key: str, timestamp: int) -> str:
        """O(log m): bisect for the rightmost entry with ts <= timestamp.
        See THE CORE IDEA and WHY bisect_right above."""
        entries = self._store.get(key)
        if not entries:
            return ""
        # bisect on the timestamps; entries is a list of (ts, value) tuples,
        # and tuple comparison already orders correctly on ts as the first
        # element, so we bisect against (timestamp, chr(0x10FFFF)) to find
        # the insertion point strictly AFTER any (timestamp, *) entries —
        # equivalent to bisect_right on timestamps alone, without building a
        # separate parallel list.
        idx = bisect.bisect_right(entries, (timestamp, chr(0x10FFFF))) - 1
        return entries[idx][1] if idx >= 0 else ""


# ==============================================================================
# Alternatives, for comparison.
# ==============================================================================
class TimeMap_linear:
    """✗ SLOW ON PURPOSE — get() scans every entry for the key, O(m) per
    query instead of O(log m)."""

    def __init__(self):
        self._store: dict[str, List[Tuple[int, str]]] = defaultdict(list)

    def set(self, key: str, value: str, timestamp: int) -> None:
        self._store[key].append((timestamp, value))

    def get(self, key: str, timestamp: int) -> str:
        best_ts, best_val = -1, ""
        for ts, val in self._store.get(key, []):
            if ts <= timestamp and ts > best_ts:
                best_ts, best_val = ts, val
        return best_val


# ==============================================================================
# TESTS — run:  python 009_time_based_key_value_store_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    print("--- correctness: LeetCode example ---")
    tm = TimeMap()
    tm.set("foo", "bar", 1)
    checks = [
        (tm.get("foo", 1), "bar"),
        (tm.get("foo", 2), "bar"),
    ]
    tm.set("foo", "bar2", 4)
    checks += [
        (tm.get("foo", 4), "bar2"),
        (tm.get("foo", 5), "bar2"),
        (tm.get("foo", 0), ""),
        (tm.get("bar", 1), ""),
    ]
    for got, expected in checks:
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  -> {got!r}  (want {expected!r})")

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: set(foo,bar,1) set(foo,bar2,4) set(foo,bar3,7) ---")
    tm2 = TimeMap()
    tm2.set("foo", "bar", 1)
    tm2.set("foo", "bar2", 4)
    tm2.set("foo", "bar3", 7)
    timestamps = [1, 4, 7]
    for query in (0, 1, 3, 4, 5, 7, 9):
        idx = bisect.bisect_right(timestamps, query) - 1
        result = tm2.get("foo", query)
        print(f"  get(foo, {query}): bisect_right({timestamps}, {query}) - 1 = {idx}  -> {result!r}")

    # ----------------------------------------------------------------------
    # ⚠️ bisect_right vs bisect_left — the tie-breaking bug, demonstrated.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️ bisect_right vs bisect_left on an EXACT timestamp match ---")
    tm3 = TimeMap()
    tm3.set("k", "v_at_1", 1)
    tm3.set("k", "v_at_4", 4)
    ts_list = [1, 4]
    query = 4
    right_idx = bisect.bisect_right(ts_list, query) - 1
    left_idx = bisect.bisect_left(ts_list, query) - 1
    print(f"  timestamps={ts_list}, query={query}")
    print(f"  bisect_right - 1 = {right_idx}  -> would return value at ts={ts_list[right_idx]} (correct: exact match)")
    print(f"  bisect_left  - 1 = {left_idx}  -> would return value at ts={ts_list[left_idx]} (WRONG: skips the exact match)")
    bug_demonstrated = right_idx != left_idx
    print(f"  divergence demonstrated: {bug_demonstrated}")
    all_ok &= bug_demonstrated

    # ----------------------------------------------------------------------
    # Randomised cross-check vs. linear scan.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs. linear-scan oracle ---")
    random.seed(17)
    trials, mismatches = 300, 0
    for _ in range(trials):
        tm_fast = TimeMap()
        tm_slow = TimeMap_linear()
        ts = 0
        n_sets = random.randint(1, 15)
        for _ in range(n_sets):
            ts += random.randint(1, 5)          # strictly increasing per key
            val = f"v{ts}"
            tm_fast.set("k", val, ts)
            tm_slow.set("k", val, ts)
        for _ in range(10):
            q = random.randint(0, ts + 5)
            if tm_fast.get("k", q) != tm_slow.get("k", q):
                mismatches += 1
    print(f"  {trials} random key histories, 10 queries each: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: O(log m) bisect get() vs O(m) linear-scan get().
    # ----------------------------------------------------------------------
    print("\n--- O(log m) bisect get() vs O(m) linear-scan get(): measured runtime ---")
    print(f"  {'#entries':>9} {'bisect(us)':>12} {'linear(us)':>12} {'speedup':>10}")
    for m in (1_000, 20_000, 200_000):
        tm_fast = TimeMap()
        tm_slow = TimeMap_linear()
        ts = 0
        for _ in range(m):
            ts += 1
            tm_fast.set("k", f"v{ts}", ts)
            tm_slow.set("k", f"v{ts}", ts)
        query = ts // 2  # forces a real search into the middle of the history
        reps = 300
        t0 = time.perf_counter()
        for _ in range(reps):
            tm_fast.get("k", query)
        t1 = time.perf_counter()
        for _ in range(reps):
            tm_slow.get("k", query)
        t2 = time.perf_counter()
        bis_us = (t1 - t0) / reps * 1_000_000
        lin_us = (t2 - t1) / reps * 1_000_000
        speedup = lin_us / bis_us if bis_us > 0 else float("inf")
        print(f"  {m:>9} {bis_us:>10.2f}us {lin_us:>10.2f}us {speedup:>9.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
