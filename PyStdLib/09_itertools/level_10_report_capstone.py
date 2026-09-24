"""
LEVEL 10 (advanced) - Capstone: a small grouped sales report generator
==========================================================================
You will learn
  * combining groupby (sorted first), accumulate, zip_longest, chain, islice,
    cycle, and starmap into one small, realistic reporting program

Run: python level_10_report_capstone.py
"""
from itertools import accumulate, chain, cycle, groupby, islice, starmap, zip_longest
from operator import itemgetter

WEST_SALES = [120, 80, 200]
EAST_SALES = [50, 60]            # deliberately shorter than WEST_SALES
RAW_RECORDS = [
    {"rep": "bob", "region": "east", "amount": 60},
    {"rep": "alice", "region": "west", "amount": 120},
    {"rep": "alice", "region": "west", "amount": 200},
    {"rep": "bob", "region": "east", "amount": 50},
    {"rep": "alice", "region": "west", "amount": 80},
]


def build_report(records: list[dict]):
    by_region = itemgetter("region")
    # groupby requires pre-sorted input by the same key -- sort first (level 9's lesson)
    sorted_records = sorted(records, key=by_region)
    region_totals = {}
    for region, group in groupby(sorted_records, key=by_region):
        region_totals[region] = sum(r["amount"] for r in group)
    return region_totals


if __name__ == "__main__":
    # ---- grouped totals (correct, because we sorted first) ------------------
    totals = build_report(RAW_RECORDS)
    assert totals == {"east": 110, "west": 400}

    # ---- running totals per region with accumulate ---------------------------
    west_running = list(accumulate(WEST_SALES))
    assert west_running == [120, 200, 400]
    running_max = list(accumulate(WEST_SALES, func=max))
    assert running_max == [120, 120, 200]   # running best-so-far, not a running sum

    # ---- pairing two regions' per-sale figures, uneven lengths ---------------
    # zip() would silently drop east's missing third sale; zip_longest keeps the slot
    paired = list(zip_longest(WEST_SALES, EAST_SALES, fillvalue=0))
    assert paired == [(120, 50), (80, 60), (200, 0)]

    # ---- combining all sale amounts from both regions into one stream --------
    all_sales = list(chain(WEST_SALES, EAST_SALES))
    assert sum(all_sales) == totals["west"] + totals["east"]

    # ---- top 3 sales overall, without fully sorting when we only need a peek -
    top_slice = list(islice(sorted(all_sales, reverse=True), 3))
    assert top_slice == [200, 120, 80]

    # ---- round-robin assigning the top sales to reviewers, bounded with islice
    reviewers = list(islice(cycle(["alice", "bob"]), len(top_slice)))
    assert reviewers == ["alice", "bob", "alice"]

    # ---- starmap to format each (reviewer, sale) pair in one line each -------
    lines = list(starmap(lambda name, amount: f"{name} reviews ${amount}", zip(reviewers, top_slice)))
    assert lines == ["alice reviews $200", "bob reviews $120", "alice reviews $80"]

    print(f"region totals: {totals}")
    print(f"west running total: {west_running}")
    print(f"paired west/east: {paired}")
    print("\n".join(lines))
    print("OK")
