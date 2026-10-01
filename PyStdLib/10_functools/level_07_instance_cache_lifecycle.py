"""
LEVEL 07 (advanced) - lru_cache on instance methods: a real memory leak
==========================================================================
You will learn
  * @lru_cache on a method caches on (self, *args) -- the cache itself
    holds a strong reference to `self`, keeping instances alive
  * this is demonstrated for real with weakref: an instance that SHOULD be
    garbage-collected stays alive because the class-level cache still
    references it
  * the fix: cache_clear() releases the references; the safer long-term fix
    is caching a plain function of hashable values instead of a bound method

Run: python level_07_instance_cache_lifecycle.py
"""
import gc
import weakref
from functools import lru_cache


class Report:
    """Represents the leak: lru_cache decorates a bound method here."""

    def __init__(self, value: int):
        self.value = value

    @lru_cache(maxsize=None)
    def double(self):
        return self.value * 2


def double_value(value: int) -> int:
    """The fix: cache a plain function of the hashable data, not `self`."""
    return value * 2


cached_double_value = lru_cache(maxsize=None)(double_value)


def main() -> None:
    # --- demonstrate the leak ------------------------------------------
    report = Report(21)
    watcher = weakref.ref(report)  # observe collection without keeping report alive

    assert report.double() == 42
    assert watcher() is not None  # still alive, unsurprisingly -- we hold `report`

    del report
    gc.collect()

    # The instance is NOT collected: Report.double's lru_cache still holds
    # a strong reference to it as part of its cache key (self, ).
    assert watcher() is not None, "instance leaked: lru_cache is holding a reference"

    # --- the fix: clearing the method's cache releases the reference -----
    Report.double.cache_clear()
    gc.collect()
    assert watcher() is None, "cache_clear() should release the leaked instance"

    # --- the safer long-term fix: cache plain, hashable data instead -----
    # Cache a free function of a plain int, never a bound method of `self`.
    report2 = Report(10)
    watcher2 = weakref.ref(report2)

    assert cached_double_value(report2.value) == 20
    info = cached_double_value.cache_info()
    assert info.misses == 1 and info.hits == 0

    assert cached_double_value(report2.value) == 20  # same int -> cache hit
    info = cached_double_value.cache_info()
    assert info.hits == 1

    del report2
    gc.collect()
    # The cache only ever held the int 10, never `report2` itself, so the
    # instance is free to be collected immediately -- no leak at all.
    assert watcher2() is None

    print("OK")


if __name__ == "__main__":
    main()
