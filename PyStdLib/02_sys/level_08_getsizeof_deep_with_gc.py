"""
LEVEL 08 (advanced) - Interop: sys.getsizeof() + gc.get_referents() for a REAL deep size
============================================================================================
You will learn
  * sys.getsizeof(obj) alone only ever reports one object's own memory
  * gc's object graph (gc.get_referents) lets you walk what an object points
    to, so you can add up a true "deep" size instead of a misleading shallow one
  * a visited-id set is required, or shared/cyclic references get double-counted
    (or recurse forever)

Run: python level_08_getsizeof_deep_with_gc.py
"""
import gc
import sys


def deep_size(obj, seen: set[int] | None = None) -> int:
    """Sum sys.getsizeof() over obj and everything it (transitively) refers
    to, visiting each object id at most once."""
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)

    size = sys.getsizeof(obj)
    for referent in gc.get_referents(obj):
        size += deep_size(referent, seen)
    return size


if __name__ == "__main__":
    # a list holding one big string: getsizeof(list) is just pointer-slot
    # overhead, it does NOT include the string's own 100,000 characters
    huge_string = "x" * 100_000
    wrapper = [huge_string]

    shallow = sys.getsizeof(wrapper)
    deep = deep_size(wrapper)

    assert shallow < 200                 # just list overhead for one element
    assert deep > 100_000                # the string's real bytes are now counted
    assert deep == shallow + sys.getsizeof(huge_string)

    # nested containers make the shallow number even more misleading: a list
    # of 50 separate 100,000-byte strings still reports a shallow size of
    # under 1 KB -- just 50 pointer slots -- nowhere close to the ~5 MB of
    # actual string data it holds
    many_strings = ["y" * 100_000 for _ in range(50)]
    assert sys.getsizeof(many_strings) < 1000            # shallow: barely more than 50 pointers
    assert deep_size(many_strings) > 50 * 100_000        # deep: reflects the real ~5 MB

    # shared references must be counted once, not once per pointer to them.
    # container holds the SAME inner list object twice -- a naive walk with
    # no visited-set would add its size in twice; deep_size must not.
    shared = ["shared payload" * 1000]
    container = [shared, shared]
    correct = deep_size(container)
    expected = sys.getsizeof(container) + deep_size(shared)   # shared counted ONCE
    assert correct == expected

    def naive_deep_size(obj) -> int:   # deliberately no `seen` set -- for comparison only
        size = sys.getsizeof(obj)
        for referent in gc.get_referents(obj):
            size += naive_deep_size(referent)
        return size

    naive = naive_deep_size(container)
    assert naive > correct   # the naive version double-counted `shared`

    # a self-referential (cyclic) structure must not recurse forever
    cyclic: list = [1, 2, 3]
    cyclic.append(cyclic)   # cyclic[3] is cyclic itself
    size_of_cycle = deep_size(cyclic)   # would infinite-loop without the `seen` set
    assert size_of_cycle > 0

    print(f"wrapper: shallow={shallow} bytes, deep={deep} bytes")
    print("OK")
