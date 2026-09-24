"""
LEVEL 07 (advanced) - ExitStack: a dynamic number of resources, closed in reverse
======================================================================================
You will learn
  * ExitStack lets you enter a NUMBER of context managers decided at runtime
  * enter_context() registers a context manager; it is exited automatically later
  * exits happen in REVERSE order of entry, exactly like nested `with` statements
  * callback() registers a plain cleanup function, not just a context manager
  * if one resource's setup fails partway through, everything entered so far
    still gets cleaned up

Run: python level_07_exitstack.py
"""
from contextlib import ExitStack, contextmanager


EVENTS: list[str] = []


@contextmanager
def resource(name: str):
    EVENTS.append(f"open:{name}")
    try:
        yield name
    finally:
        EVENTS.append(f"close:{name}")


if __name__ == "__main__":
    # ---- a variable number of resources, decided at runtime ----------------
    names = ["db", "cache", "queue"]     # imagine this list came from config

    EVENTS.clear()
    with ExitStack() as stack:
        opened = [stack.enter_context(resource(n)) for n in names]
        assert opened == names
        assert EVENTS == ["open:db", "open:cache", "open:queue"]   # entered in order

    # ---- exits happen in REVERSE order of entry ----------------------------
    print(f"events: {EVENTS}")
    assert EVENTS == [
        "open:db", "open:cache", "open:queue",
        "close:queue", "close:cache", "close:db",   # LIFO, like nested `with`
    ]

    # ---- callback(): a plain function registered for cleanup, no CM needed -
    EVENTS.clear()
    with ExitStack() as stack:
        stack.enter_context(resource("db"))
        stack.callback(EVENTS.append, "custom-cleanup-ran")
        stack.enter_context(resource("cache"))
    assert EVENTS == ["open:db", "open:cache", "close:cache", "custom-cleanup-ran", "close:db"]

    # ---- partial failure: resources entered so far are still cleaned up ----
    EVENTS.clear()
    raised = None
    try:
        with ExitStack() as stack:
            stack.enter_context(resource("db"))
            stack.enter_context(resource("cache"))
            raise RuntimeError("queue connection failed")   # never got to enter "queue"
    except RuntimeError as e:
        raised = e
    print(f"events after partial failure: {EVENTS}")
    assert raised is not None
    assert EVENTS == ["open:db", "open:cache", "close:cache", "close:db"]  # both cleaned up

    # ---- pop_all(): hand off ownership without closing (e.g. return it) ----
    EVENTS.clear()
    with ExitStack() as stack:
        stack.enter_context(resource("kept-open"))
        transferred = stack.pop_all()   # stack itself no longer owns "kept-open"
    assert EVENTS == ["open:kept-open"]   # NOT closed by the `with` block above
    with transferred:
        pass
    assert EVENTS == ["open:kept-open", "close:kept-open"]   # closed once transferred exits

    print("OK")
