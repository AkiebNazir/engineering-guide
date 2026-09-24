"""
LEVEL 09 (advanced) - Production trap: groupby() silently misgroups unsorted input
======================================================================================
You will learn
  * groupby() only merges CONSECUTIVE equal keys -- it does not look ahead or behind
  * on unsorted input, the same key can produce MULTIPLE separate groups, with no error
  * the fix: sort by the exact same key first

Run: python level_09_groupby_unsorted_trap.py
"""
from itertools import groupby
from operator import itemgetter

UNSORTED_ORDERS = [
    {"status": "shipped", "id": 1},
    {"status": "pending", "id": 2},
    {"status": "shipped", "id": 3},   # "shipped" again, but NOT adjacent to id=1's group
    {"status": "pending", "id": 4},
]

if __name__ == "__main__":
    key = itemgetter("status")

    # ---- BUG: groupby on unsorted input --------------------------------------
    broken_groups = [(k, [o["id"] for o in g]) for k, g in groupby(UNSORTED_ORDERS, key=key)]

    # "shipped" appears as TWO separate groups (id 1 alone, then id 3 alone),
    # instead of one group with both -- this is silent, no exception is raised
    assert broken_groups == [
        ("shipped", [1]),
        ("pending", [2]),
        ("shipped", [3]),
        ("pending", [4]),
    ]
    shipped_group_count = sum(1 for k, _ in broken_groups if k == "shipped")
    assert shipped_group_count == 2   # WRONG: there is only one "shipped" status, not two groups of it

    # a naive "count orders per status" built on this loses data: the dict
    # comprehension just OVERWRITES the earlier "shipped" entry with the later one
    naive_totals = {k: len(ids) for k, ids in broken_groups}
    assert naive_totals == {"shipped": 1, "pending": 1}   # BUG: both counts wrong (should be 2 and 2)

    # ---- the fix: sort by the SAME key before grouping -----------------------
    sorted_orders = sorted(UNSORTED_ORDERS, key=key)
    fixed_groups = [(k, [o["id"] for o in g]) for k, g in groupby(sorted_orders, key=key)]

    assert fixed_groups == [
        ("pending", [2, 4]),
        ("shipped", [1, 3]),
    ]
    assert len(fixed_groups) == 2   # correctly one group per distinct status
    fixed_totals = {k: len(ids) for k, ids in fixed_groups}
    assert fixed_totals == {"pending": 2, "shipped": 2}   # correct counts now

    print("OK")
