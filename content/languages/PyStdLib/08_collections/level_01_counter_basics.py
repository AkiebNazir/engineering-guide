"""
LEVEL 01 (basic) - Counting things with collections.Counter
==============================================================
You will learn
  * the problem Counter solves: tallying occurrences without a manual dict loop
  * building a Counter from any iterable
  * .most_common() for the top-N items by count

Run: python level_01_counter_basics.py
"""
from collections import Counter

if __name__ == "__main__":
    votes = ["red", "blue", "red", "green", "blue", "red"]

    tally = Counter(votes)
    assert tally["red"] == 3
    assert tally["blue"] == 2
    assert tally["green"] == 1

    # a missing key returns 0 instead of raising KeyError -- unlike a plain dict
    assert tally["purple"] == 0
    assert "purple" not in tally   # and looking it up did NOT insert it (see level 9 for the defaultdict version of this)

    # most_common() sorts by count, descending
    assert tally.most_common(1) == [("red", 3)]
    assert tally.most_common() == [("red", 3), ("blue", 2), ("green", 1)]

    # Counter is a dict subclass -- everything about dicts still works
    assert isinstance(tally, dict)
    assert sum(tally.values()) == len(votes)

    print("OK")
