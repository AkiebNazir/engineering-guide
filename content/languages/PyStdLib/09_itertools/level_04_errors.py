"""
LEVEL 04 (core) - Real itertools exceptions: bad islice/combinations arguments
==================================================================================
You will learn
  * islice() raises ValueError for a negative start/stop/step -- it can't
    slice an iterator backwards, since iterators can't be rewound
  * combinations()/permutations() raise ValueError for a negative r
  * both are triggered for real here, not just described

Run: python level_04_errors.py
"""
from itertools import combinations, islice, permutations

if __name__ == "__main__":
    # ---- islice: negative indices make no sense on a forward-only iterator ----
    try:
        list(islice(range(10), -1))
        raise AssertionError("expected ValueError for a negative islice stop")
    except ValueError as exc:
        assert "must be" in str(exc) or "negative" in str(exc)

    try:
        list(islice(range(10), 0, 5, -1))   # negative step
        raise AssertionError("expected ValueError for a negative islice step")
    except ValueError:
        pass

    # ---- combinations/permutations: negative r is invalid, not just empty ----
    try:
        list(combinations([1, 2, 3], -1))
        raise AssertionError("expected ValueError for a negative r in combinations")
    except ValueError as exc:
        assert "must be" in str(exc) or "non-negative" in str(exc)

    try:
        list(permutations([1, 2, 3], -1))
        raise AssertionError("expected ValueError for a negative r in permutations")
    except ValueError:
        pass

    # by contrast, r LARGER than the input length is perfectly legal -- it's
    # just an empty result, not an error (the real gotcha, see the GUIDE table)
    assert list(combinations([1, 2, 3], 5)) == []
    assert list(permutations([1, 2, 3], 5)) == []

    print("OK")
