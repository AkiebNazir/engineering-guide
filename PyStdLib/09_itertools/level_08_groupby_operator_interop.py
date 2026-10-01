"""
LEVEL 08 (advanced) - Interop: groupby + operator.itemgetter for record grouping
====================================================================================
You will learn
  * operator.itemgetter/attrgetter as a reusable, named "key function"
  * sorting by that key first, then grouping with itertools.groupby
  * accumulate for a running total per group, combined with starmap for formatting

Run: python level_08_groupby_operator_interop.py
"""
from itertools import groupby, starmap
from operator import itemgetter

SALES = [
    {"region": "west", "amount": 100},
    {"region": "east", "amount": 200},
    {"region": "west", "amount": 150},
    {"region": "north", "amount": 75},
    {"region": "east", "amount": 50},
]

if __name__ == "__main__":
    by_region = itemgetter("region")

    # groupby REQUIRES consecutive equal keys -- sort first using the SAME key function
    sorted_sales = sorted(SALES, key=by_region)
    assert [by_region(s) for s in sorted_sales] == ["east", "east", "north", "west", "west"]

    totals: dict[str, int] = {}
    for region, records in groupby(sorted_sales, key=by_region):
        totals[region] = sum(r["amount"] for r in records)

    assert totals == {"east": 250, "north": 75, "west": 250}

    # itemgetter also works as a sort/group key for tuples, by index
    pairs = [(3, "c"), (1, "a"), (1, "b"), (3, "d")]
    grouped_pairs = {
        key: [v for _, v in group]
        for key, group in groupby(sorted(pairs, key=itemgetter(0)), key=itemgetter(0))
    }
    assert grouped_pairs == {1: ["a", "b"], 3: ["c", "d"]}

    # starmap applies a function to each *pre-packed* tuple of arguments --
    # handy right after groupby/zip, which both produce tuples
    formatted = list(starmap(lambda region, total: f"{region}: ${total}", sorted(totals.items())))
    assert formatted == ["east: $250", "north: $75", "west: $250"]

    print("OK")
