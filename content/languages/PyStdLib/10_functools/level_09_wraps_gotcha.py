"""
LEVEL 09 (advanced) - the decorator-without-@wraps trap
==========================================================
You will learn
  * a decorator that returns a plain `def wrapper(*a, **kw)` silently
    corrupts the decorated function's __name__, __doc__ and signature
  * this looks fine at the call site (the function still runs correctly)
    but breaks introspection: help(), debuggers, and anything reading
    __name__/__doc__/__wrapped__ sees the wrong thing
  * @functools.wraps fixes it by copying the original's metadata onto the
    wrapper, and also sets __wrapped__ to the original function

Run: python level_09_wraps_gotcha.py
"""
from functools import wraps


# --- the broken version: no @wraps --------------------------------------
def logged_broken(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


@logged_broken
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


# --- the fixed version: @wraps preserves identity -----------------------
def logged_fixed(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


@logged_fixed
def multiply(a: int, b: int) -> int:
    """Multiply two numbers together."""
    return a * b


def main() -> None:
    # --- the function still WORKS correctly either way ---------------------
    assert add(2, 3) == 5
    assert multiply(2, 3) == 6

    # --- but the broken decorator corrupted its metadata --------------------
    assert add.__name__ == "wrapper"          # should be "add" -- it's wrong
    assert add.__doc__ is None                # the real docstring was lost
    assert not hasattr(add, "__wrapped__")    # no trace of the original

    # --- @wraps fixes all of it ---------------------------------------------
    assert multiply.__name__ == "multiply"                       # correct
    assert multiply.__doc__ == "Multiply two numbers together."  # preserved
    assert multiply.__wrapped__ is multiply.__wrapped__           # exists
    assert multiply.__wrapped__.__name__ == "multiply"

    # __wrapped__ even lets you reach the ORIGINAL, undecorated function --
    # unwrapped call bypasses whatever the wrapper does (here, nothing extra,
    # but in real logging/timing decorators this matters for introspection).
    original = multiply.__wrapped__
    assert original(4, 5) == 20

    # --- why this matters in practice: help()/documentation tools read
    # __name__ and __doc__ directly. A stack of broken decorators makes
    # every wrapped function in a traceback or `help()` call show up as
    # generic "wrapper" -- a real debugging tax.
    import inspect
    # wraps() also copies __wrapped__, which inspect.signature() follows by
    # default -- so the wrapper reports the ORIGINAL's real parameter names,
    # not "*args, **kwargs".
    assert list(inspect.signature(multiply).parameters) == ["a", "b"]
    assert list(inspect.signature(add).parameters) == ["args", "kwargs"]

    print("OK")


if __name__ == "__main__":
    main()
