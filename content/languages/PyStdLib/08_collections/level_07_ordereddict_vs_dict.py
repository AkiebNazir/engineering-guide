"""
LEVEL 07 (advanced) - OrderedDict vs a plain dict's insertion-order guarantee
=================================================================================
You will learn
  * a plain dict has preserved insertion order since Python 3.7 -- it's a language guarantee
  * OrderedDict adds behavior a plain dict doesn't have: move_to_end() and order-sensitive equality
  * popitem(last=...) to pop from either end of an OrderedDict

Run: python level_07_ordereddict_vs_dict.py
"""
from collections import OrderedDict

if __name__ == "__main__":
    # ---- plain dict: insertion order is preserved (guaranteed since 3.7) --
    plain = {}
    plain["z"] = 1
    plain["a"] = 2
    plain["m"] = 3
    assert list(plain.keys()) == ["z", "a", "m"]   # NOT alphabetical -- insertion order

    # ---- but plain dict equality does NOT care about order -----------------
    reordered = {"a": 2, "m": 3, "z": 1}
    assert plain == reordered   # same keys/values -> equal, regardless of order

    # ---- OrderedDict equality DOES care about order ------------------------
    od1 = OrderedDict(z=1, a=2, m=3)
    od2 = OrderedDict(a=2, m=3, z=1)
    assert od1 != od2                 # different order -> not equal for OrderedDict
    assert dict(od1) == dict(od2)     # but as plain dicts, they ARE equal

    # ---- move_to_end(): a plain dict has no equivalent method --------------
    od1.move_to_end("z")               # move "z" to the end (default last=True)
    assert list(od1.keys()) == ["a", "m", "z"]
    od1.move_to_end("z", last=False)   # move it back to the front
    assert list(od1.keys()) == ["z", "a", "m"]

    # ---- popitem(last=...): pop from either end ----------------------------
    od3 = OrderedDict(one=1, two=2, three=3)
    last_item = od3.popitem(last=True)     # LIFO: pop the most recently added
    assert last_item == ("three", 3)
    first_item = od3.popitem(last=False)   # FIFO: pop the oldest
    assert first_item == ("one", 1)
    assert list(od3.items()) == [("two", 2)]

    # a plain dict's popitem() only supports LIFO (no `last` parameter at all)
    plain_lifo = {"a": 1, "b": 2}
    assert plain_lifo.popitem() == ("b", 2)   # always last-in, first-out

    print("OK")
