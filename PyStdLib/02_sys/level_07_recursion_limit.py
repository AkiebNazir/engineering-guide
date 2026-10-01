"""
LEVEL 07 (advanced) - Lifecycle concern: the recursion limit, hit for real
=============================================================================
You will learn
  * sys.getrecursionlimit()/sys.setrecursionlimit() control Python's guard
    against a runaway call stack (it protects the C stack, not your data)
  * lowering the limit and triggering a REAL RecursionError on purpose
  * why you must restore the original limit afterwards (try/finally) --
    it's process-global state, not scoped to your function
  * catching RecursionError like any other exception once it happens

Run: python level_07_recursion_limit.py
"""
import sys


def recurse(n: int) -> int:
    return 1 + recurse(n + 1)   # never terminates on its own -- only the limit stops it


if __name__ == "__main__":
    original_limit = sys.getrecursionlimit()
    assert original_limit > 0

    try:
        # deliberately small so the error fires almost immediately and safely,
        # well before we'd ever risk the real C stack itself overflowing
        sys.setrecursionlimit(80)
        assert sys.getrecursionlimit() == 80

        raised = False
        try:
            recurse(0)
        except RecursionError as e:
            raised = True
            assert "maximum recursion depth exceeded" in str(e)
        assert raised, "expected a real RecursionError to fire"

        # the limit is unaffected by the error itself -- still what we set it to
        assert sys.getrecursionlimit() == 80

        # raising the limit lets deeper (but still finite) recursion succeed
        sys.setrecursionlimit(2000)

        def countdown(n: int) -> int:
            return 0 if n == 0 else 1 + countdown(n - 1)

        assert countdown(500) == 500   # comfortably under 2000, no error this time
    finally:
        # ALWAYS restore it: this is process-global, not undone automatically
        # when your function returns -- leaving it low would break unrelated
        # code (e.g. a normal-depth library call) that runs afterwards.
        sys.setrecursionlimit(original_limit)

    assert sys.getrecursionlimit() == original_limit

    print("OK")
