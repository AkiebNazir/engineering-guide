"""
LEVEL 02 (core) - Lazy slicing of iterators with itertools.islice
=====================================================================
You will learn
  * generators/iterators have no [start:stop] syntax -- islice provides it
  * islice only pulls as many items as needed, never the whole source
  * start, stop, and step all work like a normal slice

Run: python level_02_islice_lazy_slicing.py
"""
from itertools import count, islice

if __name__ == "__main__":
    # count(10) is an INFINITE iterator: 10, 11, 12, 13, ...
    # a plain list(count(10))[:5] would never finish -- islice never tries.
    first_five = list(islice(count(10), 5))
    assert first_five == [10, 11, 12, 13, 14]

    # start, stop: like sequence[2:5]
    letters = iter("abcdefgh")
    middle = list(islice(letters, 2, 5))
    assert middle == ["c", "d", "e"]
    # islice ADVANCED the underlying iterator -- the first 2 items are gone for good
    assert list(letters) == ["f", "g", "h"]

    # step: like sequence[::2]
    every_other = list(islice(range(10), 0, 10, 2))
    assert every_other == [0, 2, 4, 6, 8]

    # islice never materializes more than it's asked for -- proven by using it
    # on an infinite generator and getting back a finite, correct-sized result
    def naturals():
        n = 1
        while True:
            yield n
            n += 1

    first_three = list(islice(naturals(), 3))
    assert first_three == [1, 2, 3]

    print("OK")
