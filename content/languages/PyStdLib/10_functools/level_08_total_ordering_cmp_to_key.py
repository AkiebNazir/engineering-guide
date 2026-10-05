"""
LEVEL 08 (advanced) - total_ordering + cmp_to_key working together
======================================================================
You will learn
  * @total_ordering fills in <=, >, >= from just __eq__ and __lt__
  * cmp_to_key adapts a legacy two-argument comparator (cmp(a, b) -> -1/0/1)
    into a `key=` function usable by sorted()/list.sort()
  * these interoperate: a legacy comparator can be built out of the rich
    comparisons total_ordering derived, then handed to cmp_to_key for
    sorted() -- bridging "old style" comparator code with modern objects
  * total_ordering does NOT give you __hash__: defining __eq__ yourself
    disables the default __hash__ unless you define one explicitly

Run: python level_08_total_ordering_cmp_to_key.py
"""
from functools import cmp_to_key, total_ordering


@total_ordering
class Version:
    """A dotted version number, e.g. Version(1, 4, 0)."""

    def __init__(self, major: int, minor: int, patch: int):
        self.major, self.minor, self.patch = major, minor, patch

    def _tuple(self):
        return (self.major, self.minor, self.patch)

    def __eq__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return self._tuple() == other._tuple()

    def __lt__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return self._tuple() < other._tuple()

    def __repr__(self):
        return f"{self.major}.{self.minor}.{self.patch}"


def legacy_version_cmp(a: Version, b: Version) -> int:
    """An old-style two-argument comparator, the kind pre-`key=` code wrote."""
    if a == b:
        return 0
    return -1 if a < b else 1


def main() -> None:
    v1 = Version(1, 4, 0)
    v2 = Version(1, 4, 0)
    v3 = Version(2, 0, 0)
    v4 = Version(1, 9, 9)

    # --- total_ordering derived the other three comparisons for us --------
    assert v1 == v2
    assert v1 < v3
    assert v3 > v1          # derived from __lt__ + __eq__
    assert v1 <= v2         # derived: equal counts as <=
    assert v3 >= v4         # derived
    assert not (v1 >= v3)

    # --- cmp_to_key bridges the legacy comparator into sorted() -----------
    versions = [v3, v1, v4, v2]
    ordered = sorted(versions, key=cmp_to_key(legacy_version_cmp))
    assert [str(v) for v in ordered] == ["1.4.0", "1.4.0", "1.9.9", "2.0.0"]

    # cmp_to_key also works directly as a comparison key for min()/max().
    assert max(versions, key=cmp_to_key(legacy_version_cmp)) is v3

    # --- the gotcha: total_ordering does not restore __hash__ --------------
    # Defining __eq__ ourselves set Version.__hash__ to None (Python's normal
    # rule), and @total_ordering does not touch __hash__ at all.
    assert Version.__hash__ is None
    try:
        hash(v1)
        raised = False
    except TypeError:
        raised = True
    assert raised, "a class with __eq__ but no __hash__ must be unhashable"

    # --- the fix: define __hash__ explicitly if you need hashability -------
    class HashableVersion(Version):
        def __hash__(self):
            return hash(self._tuple())

    hv = HashableVersion(1, 0, 0)
    assert hash(hv) == hash((1, 0, 0))
    assert {hv, HashableVersion(1, 0, 0)} == {hv}  # dedupes via __eq__+__hash__

    print("OK")


if __name__ == "__main__":
    main()
