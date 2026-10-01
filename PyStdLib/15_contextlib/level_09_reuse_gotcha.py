"""
LEVEL 09 (advanced) - production gotcha: reusing a @contextmanager object
==============================================================================
You will learn
  * calling a @contextmanager-decorated function returns a ONE-SHOT context manager
  * storing that returned object and using it in a SECOND `with` block looks fine
    but fails for real -- __enter__() discards its setup state after first use, so
    reusing the object raises AttributeError, not something more obviously named
  * the fix: call the factory function again for each `with` block, don't cache
    the context-manager object itself

Run: python level_09_reuse_gotcha.py
"""
from contextlib import contextmanager


EVENTS: list[str] = []


@contextmanager
def managed_resource(name: str):
    EVENTS.append(f"open:{name}")
    try:
        yield name
    finally:
        EVENTS.append(f"close:{name}")


if __name__ == "__main__":
    # ---- the trap: cache the CM object, meaning to reuse it -----------------
    EVENTS.clear()
    cm = managed_resource("db")     # looks like a reusable "resource handle"

    with cm as value:
        assert value == "db"
    assert EVENTS == ["open:db", "close:db"]     # first use: works fine

    # ---- using that SAME object a second time fails for real ---------------
    # __enter__() deletes its own internal setup state (self.args/kwds/func) the
    # first time it runs, so it can tell a fresh generator to start on THIS call.
    # A second __enter__() on the same object finds that state already gone.
    raised = None
    try:
        with cm:                     # the generator behind `cm` is already exhausted
            pass
    except AttributeError as e:
        raised = e
    print(f"reusing the same context manager raised: {raised!r}")
    assert raised is not None
    assert isinstance(raised, AttributeError)

    # ---- the fix: call the FACTORY again for every `with` block -------------
    EVENTS.clear()
    with managed_resource("db") as v1:      # fresh generator each time
        assert v1 == "db"
    with managed_resource("db") as v2:      # a brand-new context manager object
        assert v2 == "db"
    assert EVENTS == ["open:db", "close:db", "open:db", "close:db"]   # works every time

    # ---- proof that each call really is a distinct object -------------------
    cm_a = managed_resource("x")
    cm_b = managed_resource("x")
    assert cm_a is not cm_b     # same arguments, but two independent one-shot objects

    print("OK")
