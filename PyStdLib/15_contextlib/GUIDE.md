# `contextlib` — utilities for `with`-statement contexts

## What it's for

`contextlib` provides tools for writing and combining context managers without hand-rolling
a class with `__enter__`/`__exit__` every time: turning a generator function into one
(`@contextmanager`), managing a variable number of resources (`ExitStack`), replacing a
`try/except/pass` (`suppress`), wrapping a `.close()`-only object (`closing`), and
temporarily redirecting `stdout`/`stderr`.

## When to reach for it vs alternatives already in this repo

| Situation | Use |
|---|---|
| A resource with real setup/teardown, used once | write a plain generator + `@contextmanager`, or a class with `__enter__`/`__exit__` if the state is complex |
| An unknown/variable number of resources (e.g. N files chosen at runtime) | `ExitStack` |
| Ignoring one specific, expected exception type | `contextlib.suppress(SomeError)`, not bare `try/except: pass` |
| An object that only has `.close()` (e.g. some `urllib` handles), not `__enter__`/`__exit__` | `contextlib.closing(obj)` |
| Capturing what a function prints, for a test assertion | `redirect_stdout`/`redirect_stderr` into an `io.StringIO` |
| Managing a database connection/transaction across a whole request | still `contextlib`-shaped, but see `PyEngineering/09_database_repository` for the fuller pattern |

## Gotchas

| Gotcha | Detail |
|---|---|
| A `@contextmanager` generator is single-use | Calling the decorated function returns a *new* context manager each time; reusing the *same* returned object in two `with` blocks raises `RuntimeError` on the second use. |
| Forgetting `try/finally` around the `yield` | Without it, an exception in the `with` block skips the generator's cleanup code entirely — the cleanup after `yield` only runs unconditionally if wrapped in `finally`. |
| A generator that yields more than once | `@contextmanager` requires exactly one `yield`; a second one raises `RuntimeError: generator didn't stop`. |
| `suppress()` swallows only the types you name | `suppress(FileNotFoundError)` still lets a `PermissionError` through — it is not a blanket `except:`. |
| `ExitStack` closes in reverse order | Like nested `with` statements, the *last* resource entered is the *first* one closed — matters when resources depend on each other. |
| `closing()` only calls `.close()` | It does not suppress exceptions or call anything else; it is exactly `try/finally: obj.close()`, no more. |

## What the 10 levels cover

Levels 1–3 build the mental model: `@contextmanager` for the single most common case, the
`yield` as the enter/exit boundary with `try/finally` proving cleanup runs even when the
body raises, then a small realistic idiom (temporarily changing state and restoring it).
Level 4 uses `suppress()` against a real, triggered exception and shows it does not
over-suppress. Level 5 covers `closing()` for a `.close()`-only object. Level 6 is a
measured, timed comparison of a generator-based context manager against a hand-written
`__enter__`/`__exit__` class doing the same job. Level 7 covers `ExitStack` for a dynamic
number of resources closed in reverse order. Level 8 uses `redirect_stdout` to capture
output, the way a test would. Level 9 demonstrates the single-use generator gotcha
failing for real, then fixes it. Level 10 is a small capstone tying several of the above
together in one resource-managing function.
