"""
LEVEL 04 (basic) - the real exceptions functools raises
==========================================================
You will learn
  * reduce() on an empty sequence with no initial value raises TypeError
    -- for real, triggered and caught here, not just described
  * lru_cache requires hashable arguments; passing a list/dict raises
    TypeError: unhashable type
  * why an explicit `initial=` for reduce and hashable-only inputs for
    lru_cache are the two disciplines that avoid these at call time

Run: python level_04_errors.py
"""
from functools import lru_cache, reduce


def main() -> None:
    # --- reduce() on an empty sequence, no initial ------------------------
    try:
        reduce(lambda acc, n: acc + n, [])
        raised = False
    except TypeError as exc:
        raised = True
        message = str(exc)
    assert raised, "reduce() on an empty sequence with no initial must raise TypeError"
    assert "empty" in message and "initial" in message

    # The fix: always pass an explicit initial when the sequence could be empty.
    safe_total = reduce(lambda acc, n: acc + n, [], 0)
    assert safe_total == 0

    # --- reduce() on a single-element sequence, no initial: does NOT raise
    # (it just returns that element untouched) -- worth confirming the
    # boundary explicitly rather than assuming it also errors.
    assert reduce(lambda acc, n: acc + n, [7]) == 7

    # --- lru_cache with an unhashable argument -----------------------------
    @lru_cache(maxsize=None)
    def total_of(numbers) -> int:
        return sum(numbers)

    assert total_of((1, 2, 3)) == 6  # tuples are hashable: this works fine

    try:
        total_of([1, 2, 3])  # a list is NOT hashable
        raised = False
    except TypeError as exc:
        raised = True
        message = str(exc)
    assert raised, "lru_cache must reject unhashable arguments"
    assert "unhashable" in message

    # The fix: convert to a hashable shape (tuple) before calling the
    # cached function, which is exactly why total_of((1, 2, 3)) above works.
    assert total_of(tuple([4, 5, 6])) == 15

    # --- cache_info confirms the unhashable call never touched the cache --
    info = total_of.cache_info()
    assert info.hits == 0
    assert info.misses == 2  # only the two tuple calls counted

    print("OK")


if __name__ == "__main__":
    main()
