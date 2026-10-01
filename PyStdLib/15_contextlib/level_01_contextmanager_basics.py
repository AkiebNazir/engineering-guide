"""
LEVEL 01 (basic) - @contextmanager: the single most common use
===================================================================
You will learn
  * @contextmanager turns a plain generator function into a `with`-usable object
  * everything before `yield` is the ENTER phase, everything after is the EXIT phase
  * the value passed to `yield` becomes the `as` target in `with ... as x:`
  * this replaces writing a class with __enter__/__exit__ for simple cases

Run: python level_01_contextmanager_basics.py
"""
from contextlib import contextmanager


EVENTS: list[str] = []


@contextmanager
def managed_greeting(name: str):
    EVENTS.append(f"enter:{name}")     # ---- runs on `with managed_greeting(...):`
    yield f"Hello, {name}!"             # ---- the `as` value; this is the enter/exit boundary
    EVENTS.append(f"exit:{name}")      # ---- runs when the `with` block ends


if __name__ == "__main__":
    EVENTS.clear()

    with managed_greeting("Ada") as message:
        assert message == "Hello, Ada!"
        assert EVENTS == ["enter:Ada"]     # exit hasn't run yet -- we're still inside the block

    assert EVENTS == ["enter:Ada", "exit:Ada"]   # exit ran automatically when the block ended

    # ---- calling it again returns a brand-new context manager -------------
    EVENTS.clear()
    cm = managed_greeting("Grace")
    with cm as message2:
        assert message2 == "Hello, Grace!"
    assert EVENTS == ["enter:Grace", "exit:Grace"]

    # ---- the decorated function itself is not a context manager until called
    assert not hasattr(managed_greeting, "__enter__")   # the function itself, undecorated call
    assert hasattr(cm, "__enter__") and hasattr(cm, "__exit__")   # calling it produces one

    print(f"events recorded: {EVENTS}")
    print("OK")
