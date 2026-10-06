"""
LEVEL 09 (advanced) - Production trap: defaultdict inserts on a mere READ
=============================================================================
You will learn
  * d[missing_key] on a defaultdict doesn't just RETURN the default -- it
    STORES it, growing the dict as a side effect of what looks like a read
  * this silently corrupts "just checking" code in loops (unbounded memory growth,
    or a dict that suddenly has keys nobody ever explicitly added)
  * the fix: use .get() (no insert) or `in` for read-only checks

Run: python level_09_defaultdict_insert_on_read_trap.py
"""
from collections import defaultdict

if __name__ == "__main__":
    hits: defaultdict[str, int] = defaultdict(int)
    hits["/home"] = 5

    assert len(hits) == 1   # only one real entry so far

    # This LOOKS like an innocent read-only check...
    pages_to_check = ["/home", "/about", "/contact", "/pricing"]
    suspiciously_popular = [page for page in pages_to_check if hits[page] > 100]

    # ...but every page we merely "checked" is now a real key in the dict,
    # even though we never called .append() or assigned anything to it!
    assert suspiciously_popular == []                 # correct answer: none are popular
    assert len(hits) == 4                              # BUG: grew from 1 entry to 4 just by checking
    assert hits["/about"] == 0                          # /about now exists, with value 0
    assert set(hits.keys()) == {"/home", "/about", "/contact", "/pricing"}

    # In a real service, this pattern in a hot request path (checking many
    # candidate keys that never existed) silently leaks memory: the dict keeps
    # growing forever from "read-only" lookups.

    # ---- the fix: use .get() (never inserts) or `in` for read-only checks ---
    hits2: defaultdict[str, int] = defaultdict(int)
    hits2["/home"] = 5

    safe_check = [page for page in pages_to_check if hits2.get(page, 0) > 100]
    assert safe_check == []
    assert len(hits2) == 1   # unchanged: .get() never inserts the missing key

    # `in` is equally safe and doesn't insert either
    assert "/about" not in hits2
    assert len(hits2) == 1

    print("OK")
