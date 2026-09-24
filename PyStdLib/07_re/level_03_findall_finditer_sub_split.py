"""
LEVEL 03 (core) - findall vs finditer, sub with a function, split keeping separators
=======================================================================================
You will learn
  * findall() builds a full list up front; finditer() yields Match objects lazily
  * re.sub() can take a FUNCTION as the replacement, not just a string
  * re.split() with a capturing group in the pattern keeps the separators in the result

Run: python level_03_findall_finditer_sub_split.py
"""
import re

TEXT = "apples:3 bananas:5 cherries:12"

if __name__ == "__main__":
    # ---- findall(): eagerly returns a list of matches (or tuples of groups) ----
    counts = re.findall(r"\d+", TEXT)
    assert counts == ["3", "5", "12"]
    assert isinstance(counts, list)

    # ---- finditer(): lazily yields Match objects, one at a time -----------
    it = re.finditer(r"\d+", TEXT)
    assert not isinstance(it, list)         # it's an iterator, not a materialized list
    assert not hasattr(it, "__len__")       # no len(): nothing has been produced yet
    first = next(it)
    assert first.group() == "3"                            # only the first match was computed so far
    remaining = [m.group() for m in it]                     # consuming the rest advances it
    assert remaining == ["5", "12"]

    # ---- sub() with a replacement FUNCTION, not just a literal string -----
    def double_it(match: re.Match) -> str:
        return str(int(match.group()) * 2)

    doubled = re.sub(r"\d+", double_it, TEXT)
    assert doubled == "apples:6 bananas:10 cherries:24"

    # subn() returns (new_string, number_of_substitutions)
    result, n = re.subn(r"\d+", double_it, TEXT)
    assert result == doubled
    assert n == 3

    # ---- split() with a capturing group keeps the separators -------------
    plain = re.split(r"\s+", TEXT)
    assert plain == ["apples:3", "bananas:5", "cherries:12"]   # separators are gone

    kept = re.split(r"(\s+)", TEXT)
    # every other element is the whitespace that was split on
    assert kept == ["apples:3", " ", "bananas:5", " ", "cherries:12"]
    assert "".join(kept) == TEXT   # nothing was lost -> the split is fully reversible

    print("OK")
