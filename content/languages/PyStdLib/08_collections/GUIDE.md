# `collections` — Specialized Container Datatypes

## What it's for

`collections` provides container types that solve a specific access pattern
better than the built-in `dict`/`list`/`tuple` do: counting things (`Counter`),
a double-ended queue (`deque`), dict-with-a-default (`defaultdict`), a
lightweight immutable record (`namedtuple`), and layering multiple mappings
into one view (`ChainMap`).

## When to reach for it vs alternatives already in this repo

- **Counting occurrences** → `Counter`, not a hand-rolled `dict` + `if key in d`
  loop. `Counter` is also a `dict` subclass, so everything you know about dicts
  still applies.
- **Adding/removing from BOTH ends of a sequence** → `deque`, not `list`. A
  `list` is backed by a contiguous array, so `list.pop(0)`/`list.insert(0, x)`
  are O(n); `deque` is a doubly-linked block structure, so both ends are O(1).
  Use a plain `list` when you only ever touch the end (`append`/`pop()`).
  This mirrors the same array-vs-linked-list trade-off covered in `PyDSA`.
  Use a plain `list` when you only ever touch the end (`append`/`pop()`); a
  `deque` doesn't support O(1) random-access indexing into the middle.
- **Grouping items into a dict of lists** → `defaultdict(list)`, not
  `dict.setdefault(key, []).append(x)` repeated everywhere.
- **A tiny immutable record** (2-6 fields, no methods needed) → `namedtuple`
  (or `typing.NamedTuple` for type hints) instead of a full class or a bare
  tuple where `row[2]` says nothing about what index 2 means.
- **Layered configuration** (CLI args > env vars > file > defaults) →
  `ChainMap`, not copying and merging dicts by hand.
- **Ordered iteration** → a plain `dict` already preserves insertion order as
  of Python 3.7+; only reach for `OrderedDict` when you specifically need
  `move_to_end()` or equality that's order-sensitive.

## Gotchas

| Gotcha | Detail |
|---|---|
| `defaultdict` inserts on read | `d[missing_key]` doesn't just return the default — it **stores** it in the dict as a side effect of merely looking it up. |
| `Counter` subtraction drops non-positive counts | `a - b` keeps only *strictly positive* results; a key that would go to zero or negative simply disappears, it doesn't become `0` or negative. |
| `namedtuple` is immutable | `.field = x` raises `AttributeError`; use `._replace(field=x)` to get a new instance instead. |
| Plain `dict` preserves insertion order (3.7+), but isn't `OrderedDict` | A plain `dict` doesn't have `.move_to_end()`, and two dicts compare equal regardless of key order — `OrderedDict` equality IS order-sensitive. |
| `deque` has no O(1) random-access middle insert | `deque` is fast at both *ends*; indexing/inserting into the *middle* is still O(n), same as a list. |
| `ChainMap` writes go to the FIRST mapping only | `cm[key] = value` always mutates `cm.maps[0]`, even if `key` already exists deeper in the chain — reads see the deep value, writes never touch it. |

## What the 10 levels cover

Level 1 starts with `Counter` for the single most common job: counting things.
Level 2 covers `deque`'s core API (`append`/`appendleft`/`pop`/`popleft`/`rotate`/
`maxlen`). Level 3 builds the `defaultdict(list)` grouping idiom next to the
manual `dict.setdefault` it replaces. Level 4 triggers real exceptions —
`namedtuple` immutability and `deque` popping from empty. Level 5 goes deeper on
`namedtuple` (`_asdict()`, `_replace()`, positional/keyword access). Level 6 is a
measured `deque.popleft()` vs `list.pop(0)` timing. Level 7 covers `OrderedDict`
vs a plain dict's insertion-order guarantee, plus `move_to_end()`/`popitem()`.
Level 8 pairs `ChainMap` with `os.environ` for layered configuration. Level 9
demonstrates the `defaultdict` insert-on-read trap silently growing a dict, then
fixes it. Level 10 is a capstone event-processing pipeline using most of the
above together.
