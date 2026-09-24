"""
================================================================================
LeetCode 1146 · Snapshot Array                                          [Medium]
https://leetcode.com/problems/snapshot-array/
Topic: 25 · Design
================================================================================

PROBLEM
-------
Implement a SnapshotArray that supports the following interface:

    SnapshotArray(length)      Initializes an array-like data structure with
                               the given length. Initially, each element is 0.
    set(index, val)            Sets the element at index to val.
    snap() -> int              Takes a snapshot of the array and returns the
                               snap_id: the total number of times snap() was
                               called, minus 1.
    get(index, snap_id) -> int Returns the value at index at the time the
                               snapshot with that snap_id was taken.


EXAMPLES
--------
    ["SnapshotArray","set","snap","set","get"]
    [[3],[0,5],[],[0,6],[0,0]]
    Output: [null,null,0,null,5]

    arr = SnapshotArray(3)   # [0, 0, 0]
    arr.set(0, 5)            # [5, 0, 0]
    arr.snap()               # returns 0
    arr.set(0, 6)            # [6, 0, 0]
    arr.get(0, 0)            # 5 — the value at snap 0


CONSTRAINTS
-----------
    1 <= length <= 5 * 10^4
    0 <= index < length
    0 <= val <= 10^9
    0 <= snap_id < (the total number of times we call snap())
    At most 5 * 10^4 calls will be made to set, snap, and get.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Copying the whole array on every snap is O(length) per snap: up to
5 * 10^4 * 5 * 10^4 = 2.5 * 10^9 element copies. Too much.

Instead, store HISTORY PER INDEX, only for indices that actually change:

    history[index] = [(snap_id, value), (snap_id, value), ...]   sorted by snap_id

set() records the value under the CURRENT snap id (the id the next snap() will
return). get(index, snap_id) finds the last entry with snap_id <= the requested
id: binary search.

This is the same idea as multi-version concurrency control (MVCC) in databases,
and as persistent / copy-on-write data structures: never copy what didn't
change.


WHAT TO THINK ABOUT
--------------------
1. Several set() calls on the same index before one snap(): which value should
   a get for that snap return? How do you avoid storing all of them?

2. What does get return for an index that was never set before that snap?

3. bisect on a list of tuples: which key do you search for so you land AFTER
   all entries with snap_id <= target?


PROGRESSIVE HINTS
------------------
Hint 1: history = [[(-1, 0)] for _ in range(length)], snap_id = 0.
        The (-1, 0) sentinel means "0 before any snap".

Hint 2: set: if history[i][-1][0] == snap_id, overwrite it; else append
        (snap_id, val).

Hint 3: get: j = bisect_right(history[i], (snap_id, inf)) - 1;
        return history[i][j][1].


COMPLEXITY TARGET
------------------
    set O(1), snap O(1), get O(log S) where S = sets on that index
    Space: O(length + number of set calls)
================================================================================
"""


class SnapshotArray:
    def __init__(self, length: int):
        # YOUR CODE HERE
        pass

    def set(self, index: int, val: int) -> None:
        # YOUR CODE HERE
        pass

    def snap(self) -> int:
        # YOUR CODE HERE
        pass

    def get(self, index: int, snap_id: int) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 012_snapshot_array_question.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    a = SnapshotArray(3)
    a.set(0, 5)
    s0 = a.snap()
    a.set(0, 6)
    checks = [(s0, 0), (a.get(0, 0), 5), (a.get(1, 0), 0)]

    b = SnapshotArray(2)
    b.snap(); b.snap()                 # snaps 0, 1 with nothing set
    b.set(1, 7); b.set(1, 8)           # two sets before snap 2
    s2 = b.snap()
    b.set(1, 9)
    checks += [(s2, 2), (b.get(1, 0), 0), (b.get(1, 1), 0), (b.get(1, 2), 8)]

    for got, want in checks:
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  got={got}  want={want}")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
