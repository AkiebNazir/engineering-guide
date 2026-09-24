"""
LEVEL 04 (core) - Real exceptions: namedtuple immutability, empty deque pops
================================================================================
You will learn
  * assigning to a namedtuple field raises AttributeError -- it's truly immutable
  * popping from an empty deque raises IndexError, same as an empty list
  * how a defaultdict sidesteps the KeyError a plain dict would raise

Run: python level_04_errors.py
"""
from collections import deque, namedtuple

Point = namedtuple("Point", ["x", "y"])

if __name__ == "__main__":
    # ---- namedtuple: truly immutable, not just "conventionally" -----------
    p = Point(1, 2)
    try:
        p.x = 99
        raise AssertionError("expected AttributeError: namedtuple fields cannot be reassigned")
    except AttributeError as exc:
        assert "can't set attribute" in str(exc) or "no attribute" in str(exc) or "object has no setter" in str(exc)
    assert p.x == 1   # unchanged -- the assignment never took effect

    # ---- deque: popping from empty raises IndexError -----------------------
    empty = deque()
    try:
        empty.pop()
        raise AssertionError("expected IndexError from popping an empty deque")
    except IndexError as exc:
        assert "empty" in str(exc).lower()

    try:
        empty.popleft()
        raise AssertionError("expected IndexError from popleft on an empty deque")
    except IndexError:
        pass

    # ---- plain dict: a missing key raises KeyError (contrast with defaultdict) ----
    plain = {"a": 1}
    try:
        _ = plain["missing"]
        raise AssertionError("expected KeyError")
    except KeyError as exc:
        assert exc.args == ("missing",)   # KeyError's argument is the missing key itself

    print("OK")
