# slices — generic slice operations (Go 1.21+)

`slices` gives you generic, type-safe operations that used to require either
the `sort` package's `Interface`/`sort.Slice` boilerplate or a hand-written
loop: sorting, searching, comparing, reversing, deduping, inserting, and
deleting, all as free functions over `[]T`.

## When to reach for it vs alternatives already in this repo

- Sorting a slice of a built-in ordered type → `slices.Sort`, not
  `sort.Ints`/`sort.Strings`/`sort.Slice` (those still work, but `slices` is
  the one generic API for every element type).
- Sorting by a custom comparison → `slices.SortFunc` with a `func(a, b T)
  int`, not `sort.Slice`'s `func(i, j int) bool` plus manual indexing.
  `slices.SortFunc` is the direct upgrade path from `sort.Slice` - see
  level 8.
- Checking membership or finding a position → `slices.Contains` /
  `slices.Index`, not a hand-rolled `for` loop (level 2 shows the line-count
  difference).
- Looking something up in a slice you search often, and it's sorted →
  `slices.BinarySearch`, not `slices.Contains` - O(log n) instead of O(n)
  (level 6 measures the real gap at scale).
- Removing duplicates → `slices.Compact`, but ONLY on an already-sorted
  slice - it removes ADJACENT duplicates only, the exact same caveat as
  Python's `itertools.groupby` (level 9 shows what happens when you forget).
- Making an independent copy before mutating → `slices.Clone`, never a bare
  reslice, or you mutate the original's backing array by accident (level 7).

## Gotchas

| Gotcha | Detail |
|---|---|
| `Compact` only removes ADJACENT duplicates | It assumes the input is already sorted. `Compact` on an unsorted slice silently leaves non-adjacent duplicates in place - no error, just wrong output. |
| A reslice is not a copy | `cp := s[:len(s)]` (or just `cp := s`) shares the same backing array as `s`. Mutating an element of `cp` mutates `s` too. Use `slices.Clone(s)` for a real independent copy. |
| `BinarySearch` requires a sorted slice | Like any binary search, it assumes sorted input and gives meaningless results (silently) if that assumption is violated - it does not check for you. |
| `Insert`/`Delete` can reallocate | `Insert` may grow the backing array (invalidating old slices aliasing it); `Delete` shifts elements down in place and does NOT shrink capacity - the freed slots still reference old elements until overwritten (relevant if they held pointers, for GC). |
| `SortFunc`'s comparator returns an `int`, not a `bool` | Negative means a < b, zero means equal, positive means a > b - the same contract as `cmp.Compare`, different from `sort.Slice`'s less-than bool. |
| Generic functions still need a comparable/ordered constraint | `slices.Sort` needs `cmp.Ordered` elements; for a struct slice you need `SortFunc` (or `SortStableFunc`) with your own comparator - there's no free generic `<` for structs. |

## What the 10 levels cover

Levels 1-2 cover the everyday surface: `Sort`, `Contains`, `Index`, then
`SortFunc`, `Reverse`, and `Equal`, each contrasted with the pre-1.21
hand-written loop it replaces. Level 3 combines `Sort` + `Compact` into the
standard dedupe idiom. Level 4 covers `BinarySearch`'s not-found result and
handles it for real. Level 5 covers `Insert`/`Delete` for maintaining an
ordered slice. Level 6 is a measured comparison of linear `Contains` vs.
`BinarySearch` on a large sorted slice. Level 7 is the `Clone` aliasing bug -
mutating a "copy" that's actually the same backing array - demonstrated
failing, then fixed. Level 8 is `slices` + `sort` interop: `SortFunc` next
to the equivalent hand-written `sort.Slice`, for a second line-count
contrast. Level 9 is the `Compact`-on-unsorted-input trap. Level 10 is a
capstone record pipeline exercising most of the above together.
