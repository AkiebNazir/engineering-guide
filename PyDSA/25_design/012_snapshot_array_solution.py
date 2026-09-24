"""
================================================================================
SOLUTION · LeetCode 1146 · Snapshot Array                               [Medium]
https://leetcode.com/problems/snapshot-array/
================================================================================

THE CORE IDEA
--------------
Never copy the array. Record, per index, only the CHANGES, tagged with the snap
id they belong to: history[i] = [(snap_id, value), ...] in increasing snap id.
set() writes under the current snap id (overwriting if that id is already the
last entry). get(i, snap_id) binary-searches for the last entry with id <=
snap_id. snap() just increments a counter. This is copy-on-write / MVCC in
miniature.


================================================================================
APPROACH 1 · Copy the whole array on snap
================================================================================
    snap(): self.snaps.append(self.arr[:]); return len(self.snaps) - 1
    get(i, s): return self.snaps[s][i]

    snap O(length), set O(1), get O(1)
    Space: O(length * snaps) — up to 2.5 * 10^9 cells at the limits.


================================================================================
APPROACH 2 · Per-index history + binary search ✅ (the answer)
================================================================================
    history = [[(-1, 0)] for _ in range(length)]
    snap_id = 0

    set(i, v):
        if history[i][-1][0] == snap_id:
            history[i][-1] = (snap_id, v)          # same snap: overwrite
        else:
            history[i].append((snap_id, v))
    snap():
        snap_id += 1
        return snap_id - 1
    get(i, s):
        j = bisect_right(history[i], (s, inf)) - 1
        return history[i][j][1]

WHY (s, inf). Tuples compare element by element. (s, inf) is greater than every
(s, value) and smaller than every (s + 1, ...), so bisect_right lands just past
all entries with snap id <= s. Minus one is the answer entry. The (-1, 0)
sentinel guarantees j >= 0.

WHY OVERWRITE WITHIN A SNAP. Only the LAST value set before snap() is visible
in that snapshot. Overwriting keeps history[i] strictly increasing in snap id,
which the binary search relies on, and bounds memory.

    set O(1), snap O(1), get O(log S_i)
    Space: O(length + set calls)


================================================================================
APPROACH 3 · Dict per snap of changed indices
================================================================================
Keep a dict of changes for the current snap; on snap(), push it. get walks
backwards through snap dicts until it finds the index. O(1) set/snap, but get
is O(snaps) in the worst case. Worse than Approach 2; mention it as the path
to Approach 2.


================================================================================
STEP BY STEP TRACE
================================================================================
    SnapshotArray(3)  history: [(-1,0)] [(-1,0)] [(-1,0)]   snap_id 0
    set(0, 5)         history[0]: [(-1,0), (0,5)]
    snap() -> 0       snap_id 1
    set(0, 6)         history[0]: [(-1,0), (0,5), (1,6)]
    get(0, 0)         bisect_right(history[0], (0, inf)) = 2 -> j = 1 -> 5
    get(1, 0)         bisect_right([(-1,0)], (0, inf)) = 1 -> j = 0 -> 0


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     set     snap         get           Space
    ---------------------------  ------  -----------  ------------  ----------------------
    Copy array on snap           O(1)    O(length)    O(1)          O(length * snaps)
    Per-index history ✅         O(1)    O(1)         O(log S_i)    O(length + sets)
    Dict of changes per snap     O(1)    O(1)         O(snaps)      O(sets)


================================================================================
EDGE CASES
================================================================================
    Index never set               Sentinel returns 0 for every snap.
    Many sets in one snap         Only the last is stored.
    Many snaps with no sets       snap is O(1); history untouched.
    Set after the last snap       Visible only to future snaps (tagged with the
                                  current, not-yet-returned id).


================================================================================
COMMON MISTAKES
================================================================================
1. Copying the array on snap. Correct, O(length) per snap. Demo measures memory.

2. Appending every set, even within the same snap, then binary-searching with
   bisect_left on the snap id: you land on the FIRST value set in that snap,
   not the last. Demo below.

3. Recording set() under snap_id - 1 (the last returned id), which rewrites
   history that a previous snapshot already froze. Demo below.

4. Forgetting the sentinel and crashing on history[i][-1] for untouched indices.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Also support rolling back to a snapshot?
A: Bump a "base" snap id and have get(i, s) treat entries after the rollback
   point as invisible, or truncate per-index histories lazily on access.

Q: How is this related to databases?
A: MVCC: each row version is tagged with a transaction id; a reader with
   snapshot id s sees the newest version with id <= s. Same binary search idea;
   old versions are garbage-collected (VACUUM) when no reader needs them.

Q: Persistent arrays with O(log n) everything?
A: Path-copying persistent segment tree: each set creates O(log n) new nodes,
   each snap stores a root pointer.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 981   Time Based Key-Value Store     — identical per-key history + bisect
    LC 359   Logger Rate Limiter (003)
    LC 2502  Design Memory Allocator
    SystemDesign building blocks: transactions & MVCC
================================================================================
"""

import bisect
import random
import time
import tracemalloc
from typing import Dict, List, Tuple

INF = float("inf")


class SnapshotArray:
    def __init__(self, length: int):
        self.history: List[List[Tuple[int, int]]] = [[(-1, 0)] for _ in range(length)]
        self.snap_id = 0

    def set(self, index: int, val: int) -> None:
        h = self.history[index]
        if h[-1][0] == self.snap_id:
            h[-1] = (self.snap_id, val)
        else:
            h.append((self.snap_id, val))

    def snap(self) -> int:
        self.snap_id += 1
        return self.snap_id - 1

    def get(self, index: int, snap_id: int) -> int:
        h = self.history[index]
        return h[bisect.bisect_right(h, (snap_id, INF)) - 1][1]


# ------------------------------------------------------------------------
# Alternatives / broken versions for the demos.
# ------------------------------------------------------------------------
class SnapshotArrayCopy:
    def __init__(self, length: int):
        self.arr = [0] * length
        self.snaps: List[List[int]] = []

    def set(self, index: int, val: int) -> None:
        self.arr[index] = val

    def snap(self) -> int:
        self.snaps.append(self.arr[:])
        return len(self.snaps) - 1

    def get(self, index: int, snap_id: int) -> int:
        return self.snaps[snap_id][index]


class SnapshotArrayFirstValueBug:
    """Mistake 2: appends every set and finds the FIRST entry for the snap."""

    def __init__(self, length: int):
        self.ids: List[List[int]] = [[-1] for _ in range(length)]
        self.vals: List[List[int]] = [[0] for _ in range(length)]
        self.snap_id = 0

    def set(self, index: int, val: int) -> None:
        self.ids[index].append(self.snap_id)
        self.vals[index].append(val)

    def snap(self) -> int:
        self.snap_id += 1
        return self.snap_id - 1

    def get(self, index: int, snap_id: int) -> int:
        ids = self.ids[index]
        j = bisect.bisect_left(ids, snap_id)
        if j < len(ids) and ids[j] == snap_id:
            return self.vals[index][j]                   # BUG: first of several
        return self.vals[index][j - 1]


class SnapshotArrayWrongIdBug(SnapshotArray):
    """Mistake 3: tags sets with the last RETURNED snap id."""

    def set(self, index: int, val: int) -> None:
        tag = self.snap_id - 1                           # BUG
        h = self.history[index]
        if h[-1][0] == tag:
            h[-1] = (tag, val)
        else:
            h.append((tag, val))


# ==============================================================================
# TESTS — run:  python 012_snapshot_array_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    print("--- correctness: examples ---")
    for cls in (SnapshotArray, SnapshotArrayCopy):
        a = cls(3)
        a.set(0, 5)
        s0 = a.snap()
        a.set(0, 6)
        got = [s0, a.get(0, 0), a.get(1, 0)]
        b = cls(2)
        b.snap(); b.snap()
        b.set(1, 7); b.set(1, 8)
        s2 = b.snap()
        b.set(1, 9)
        got += [s2, b.get(1, 0), b.get(1, 1), b.get(1, 2)]
        ok = got == [0, 5, 0, 2, 0, 0, 8]
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {cls.__name__:<18} {got}")

    print("\n--- randomized cross-check vs copy-on-snap (300 scripts) ---")
    rng = random.Random(1146)
    bad = 0
    for _ in range(300):
        n = rng.randint(1, 6)
        fast, slow = SnapshotArray(n), SnapshotArrayCopy(n)
        snaps = 0
        for _ in range(rng.randint(1, 80)):
            r = rng.random()
            if r < 0.5:
                i, v = rng.randrange(n), rng.randint(0, 9)
                fast.set(i, v); slow.set(i, v)
            elif r < 0.75:
                if fast.snap() != slow.snap():
                    bad += 1
                snaps += 1
            elif snaps:
                i, s = rng.randrange(n), rng.randrange(snaps)
                if fast.get(i, s) != slow.get(i, s):
                    bad += 1
                    break
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  300 random scripts agree")

    print("\n--- mistakes LIVE ---")
    for label, cls in (("first value in the snap", SnapshotArrayFirstValueBug),
                       ("tag with last returned id", SnapshotArrayWrongIdBug)):
        good, bug = SnapshotArray(1), cls(1)
        for obj in (good, bug):
            obj.set(0, 1)
            obj.snap()          # snap 0 sees 1
            obj.set(0, 2)
            obj.set(0, 3)
            obj.snap()          # snap 1 sees 3
        g = [good.get(0, 0), good.get(0, 1)]
        b = [bug.get(0, 0), bug.get(0, 1)]
        ok = g == [1, 3] and b != g
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {label:<26}: get(0,0), get(0,1) -> {b}  (want {g})")

    print("\n--- memory: length 50,000, 1,000 snaps, 1,000 sets ---")
    for name, cls in (("copy on snap     ", SnapshotArrayCopy), ("per-index history", SnapshotArray)):
        tracemalloc.start()
        arr = cls(50_000)
        t0 = time.perf_counter()
        for k in range(1000):
            arr.set(rng.randrange(50_000), k)
            arr.snap()
        dt = time.perf_counter() - t0
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"      {name}  peak {peak / 2**20:8.1f} MiB   {dt * 1000:7.1f} ms")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
