# functools

`functools` is the stdlib's toolbox for working with *functions themselves* — folding
sequences, pre-binding arguments, caching return values, preserving metadata through
decorators, dispatching on argument type, and deriving comparison methods. None of it
is about I/O or data structures; it is about composing and adapting callables.

## When to reach for it

- Folding a sequence into a single value → `functools.reduce` (though a plain `for`
  loop or `sum`/`math.prod` is often clearer for the common cases — `reduce` earns its
  keep for genuinely custom combining logic).
- Pre-binding some arguments of a function to build a specialized callable →
  `functools.partial`, instead of a `lambda` wrapper.
- Memoizing a pure function's results → `functools.lru_cache` / `functools.cache`.
  For caching *shared across processes* (not just one Python process's memory), see a
  real cache/store instead — this repo's `PyEngineering/14_concurrent_cache` covers the
  concurrency-safe, TTL-aware version.
- Writing a decorator → always apply `functools.wraps` inside it, or you silently break
  introspection (`__name__`, `__doc__`, `help()`) for every function it wraps.
- One function needs different implementations per argument *type* (not per value) →
  `functools.singledispatch`, instead of a chain of `isinstance` checks.
- Sorting with a legacy two-argument comparator (`cmp(a, b) -> -1/0/1`) instead of a
  `key=` function → `functools.cmp_to_key`.
- A class needs `<`, `<=`, `>`, `>=` and you don't want to hand-write all four →
  `@functools.total_ordering`, given `__eq__` and just one of the others.

`functools` is not a concurrency or IPC tool — for worker pools, multiprocessing, or
cross-process communication, see `PyEngineering/33_concurrency_models_ipc`. It is also
not a general data-caching layer — `lru_cache` lives in one process's memory only.

## Gotchas

| Gotcha | Detail |
|---|---|
| `lru_cache` needs hashable arguments | Passing a `list` or `dict` raises `TypeError: unhashable type`. |
| Decorators without `@wraps` corrupt introspection | `wrapper.__name__` becomes `"wrapper"`, `help(fn)` shows the wrong docstring, and tools relying on `__wrapped__`/`__name__` (debuggers, some frameworks) misbehave. |
| `lru_cache` on instance methods leaks memory | The cache key includes `self`, so cached instances are never garbage-collected while the cache holds a reference — a real production trap. |
| `reduce` with no `initial` on an empty sequence raises `TypeError` | Always pass an explicit `initial` unless you have proven the sequence is non-empty. |
| `total_ordering` does not give you `__hash__` | Defining `__eq__` yourself sets `__hash__` to `None` unless you define it too — instances become unhashable. |
| `partial` binds *positionally first* | Extra positional args at call time are appended after the bound ones — reordering can silently pass the wrong value into the wrong parameter. |

## What the 10 levels cover

Levels 1-3 build the core toolbox (`reduce`, `partial`, `lru_cache` combined into a
memoized pipeline). Level 4 triggers the real `TypeError` from caching an unhashable
argument. Level 5 shows `partial` composed with `singledispatch` for a small dispatch
table. Level 6 *measures* cached vs uncached recursive Fibonacci with `cache_info()` and
wall-clock timing — real numbers from that run, not claimed ones. Level 7 covers the
instance-method cache-leak lifecycle concern and how to avoid it. Level 8 combines
`cmp_to_key` with `total_ordering` for legacy-comparator sorting of rich objects. Level 9
is the `wraps`-less decorator trap, shown breaking and then fixed. Level 10 is a small
capstone: a memoized, type-dispatching text-report pipeline built from every earlier
piece.
