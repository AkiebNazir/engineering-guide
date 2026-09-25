# sort — ordering slices and searching sorted data

`sort` orders slices in place and binary-searches over already-sorted data.
Reach for it any time you need "these in order" or "where would X go in this
already-ordered list" - the convenience wrappers cover primitives, closures
cover custom orderings, and `sort.Interface` covers the type-safe/reusable
case.

## When to reach for it vs alternatives already in this repo

- A one-off ordering of a slice you already have → `sort.Slice`/`SliceStable`
  with a closure - no new type needed.
- The same ordering reused across a codebase, or you want the compiler to
  check `Less`/`Swap` line up with `Len` → implement `sort.Interface` on a
  named type (level 5), the same shape `sort.IntSlice`/`StringSlice`/
  `Float64Slice` already use internally (level 7).
- Keeping a slice sorted as you insert one item at a time → `sort.Search` to
  find the insertion point, then a manual slice insert - `sort` itself has
  no "insert and keep sorted" helper.
- Generic (type-parameterized) sorting without `interface{}`/reflection → out
  of scope for this module; `slices.Sort`/`slices.SortFunc` in the newer
  `slices` package take that approach, `sort` predates generics.

## Gotchas

| Gotcha | Detail |
|---|---|
| `sort.Slice`/`sort.Sort` are NOT stable | Equal elements (by your `Less`) may be reordered relative to their input order. Use `SliceStable`/`Stable` when a secondary, unobserved field must survive sorting (level 9). |
| `sort.Search`'s "not found" is `len(slice)`, not `-1` | If the predicate is never true, `Search` returns one index past the end. Indexing with it unchecked panics for real (level 4). |
| `sort.Slice` uses reflection under the hood | It takes `interface{}` and reflects to swap elements; a hand-written `sort.Interface` avoids that entirely - measurable, not just theoretical (level 6). |
| `time.Time` (and other non-primitive values) can't use `<`/`>` | A `Less` closure over such values must call the type's own comparison method, e.g. `t1.Before(t2)` (level 8). |
| `sort.Reverse` doesn't sort descending itself | It wraps a `sort.Interface` and swaps what `Less` means; you still call `sort.Sort` (or `Stable`) on the wrapped result. |
| The named slice types have `Sort()`, not `IsSorted()` | `sort.IntSlice`/`StringSlice`/`Float64Slice` each add a `Sort()` (and `Search()`) method, but "is it sorted" is still the free function `sort.IsSorted`/`SliceIsSorted` (level 7). |

## What the 10 levels cover

Levels 1-2 build the everyday <abbr title="Application Programming Interface">API</abbr>: the primitive convenience wrappers
(`sort.Ints`/`Strings`/`Float64s`), then `sort.Slice`/`SliceStable`/`Sort`/
`Reverse`/`IsSorted` together. Level 3 is the multi-key comparator idiom
(primary key, then a secondary tiebreak). Level 4 triggers sort's one real
failure mode - `sort.Search`'s not-found sentinel indexed without a bounds
check - as a real panic, then fixes it. Level 5 implements `sort.Interface`
by hand on a named type. Level 6 is a measured, honestly-reported comparison
of `sort.Slice`'s reflection-based approach against a typed `sort.Interface`.
Level 7 covers the built-in `IntSlice`/`StringSlice`/`Float64Slice` types and
composing them with `sort.Reverse`. Level 8 sorts `[]time.Time`-backed values
using `Before()` inside the closure. Level 9 is the production trap: an
observed (not assumed) demonstration that `sort.Slice` scrambles equal-key
order while `SliceStable` does not. Level 10 is a capstone leaderboard
combining a stable multi-key sort with a `sort.Search`-based rank lookup.
