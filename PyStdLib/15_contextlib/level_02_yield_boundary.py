"""
LEVEL 02 (core) - the yield boundary: try/finally guarantees cleanup
=========================================================================
You will learn
  * without try/finally, an exception in the `with` block skips your cleanup code
  * wrapping the yield in try/finally makes cleanup run on BOTH normal exit and
    exception exit -- this is the core API contract of @contextmanager
  * an uncaught exception in the body still propagates out of the `with` block
    even though cleanup ran first
  * this is the number one thing @contextmanager exists to make easy to get right

Run: python level_02_yield_boundary.py
"""
from contextlib import contextmanager


EVENTS: list[str] = []


# ---- the WRONG way: no try/finally, cleanup is skipped on exception --------
@contextmanager
def broken_resource(name: str):
    EVENTS.append(f"open:{name}")
    yield name
    EVENTS.append(f"close:{name}")   # never reached if the body raises!


# ---- the RIGHT way: try/finally guarantees cleanup either way --------------
@contextmanager
def safe_resource(name: str):
    EVENTS.append(f"open:{name}")
    try:
        yield name
    finally:
        EVENTS.append(f"close:{name}")   # ALWAYS runs, exception or not


if __name__ == "__main__":
    # ---- broken_resource: cleanup is silently skipped on exception --------
    EVENTS.clear()
    try:
        with broken_resource("db"):
            raise ValueError("something went wrong inside the block")
    except ValueError:
        pass
    print(f"broken_resource events: {EVENTS}")
    assert EVENTS == ["open:db"]                 # "close:db" never happened -- a real leak

    # ---- safe_resource: cleanup runs even though the body raised ----------
    EVENTS.clear()
    raised = None
    try:
        with safe_resource("db"):
            raise ValueError("something went wrong inside the block")
    except ValueError as e:
        raised = e
    print(f"safe_resource events: {EVENTS}")
    assert EVENTS == ["open:db", "close:db"]     # cleanup ran BEFORE the exception propagated
    assert raised is not None                     # and the exception still escaped the `with`

    # ---- safe_resource on the normal (non-exception) path ------------------
    EVENTS.clear()
    with safe_resource("cache") as name:
        assert name == "cache"
    assert EVENTS == ["open:cache", "close:cache"]

    print("OK")
