"""
LEVEL 03 (core) - The defaultdict(list) grouping idiom vs dict.setdefault
=============================================================================
You will learn
  * the manual dict.setdefault(key, []).append(x) boilerplate for grouping
  * how defaultdict(list) removes that boilerplate entirely
  * defaultdict(int) as a counter (Counter is usually still better, but this
    shows WHY defaultdict(int) works: int() with no args returns 0)

Run: python level_03_defaultdict_idiom.py
"""
from collections import defaultdict

WORDS = ["apple", "avocado", "banana", "blueberry", "cherry", "clementine"]

if __name__ == "__main__":
    # ---- the manual way: dict.setdefault everywhere ------------------------
    manual: dict[str, list[str]] = {}
    for word in WORDS:
        key = word[0]
        manual.setdefault(key, []).append(word)   # boilerplate: "insert [] if missing, then append"
    assert manual == {
        "a": ["apple", "avocado"],
        "b": ["banana", "blueberry"],
        "c": ["cherry", "clementine"],
    }

    # ---- the defaultdict way: the default is applied automatically --------
    grouped: defaultdict[str, list[str]] = defaultdict(list)
    for word in WORDS:
        grouped[word[0]].append(word)   # no setdefault call needed -- missing key -> auto []
    assert dict(grouped) == manual   # same result, less code

    # ---- defaultdict(int): missing key -> int() -> 0 -----------------------
    letter_counts: defaultdict[str, int] = defaultdict(int)
    for word in WORDS:
        letter_counts[word[0]] += 1   # works because letter_counts[key] defaults to 0, not KeyError
    assert dict(letter_counts) == {"a": 2, "b": 2, "c": 2}

    # a plain dict would raise KeyError on the first `+= 1` for a new key
    plain: dict[str, int] = {}
    try:
        plain["z"] += 1
        raise AssertionError("expected KeyError on a plain dict")
    except KeyError:
        pass

    print("OK")
