# `itertools` — Iterator Building Blocks

## What it's for

`itertools` provides fast, memory-efficient building blocks for working with
iterators: chaining them together, slicing them lazily, grouping consecutive
items, computing running totals, and generating combinatorial sequences —
all without building an intermediate list unless you ask for one.

## When to reach for it vs alternatives already in this repo

- **Joining several lists just to loop over them once** → `itertools.chain`,
  not `list1 + list2 + list3` — chaining doesn't allocate a new combined list.
- **Taking a slice of a generator** (which has no `[a:b]` syntax) →
  `itertools.islice`, not `list(gen)[a:b]` which forces the whole generator
  to run first.
- **Grouping consecutive runs** → `itertools.groupby`, but only after sorting
  by the same key — `collections.defaultdict(list)` (see `08_collections`) is
  usually the better choice when the input isn't already sorted and you just
  want *all* items per key, order aside.
- **All pairs/orderings/subsets of a small collection** → `product`,
  `permutations`, `combinations`, `combinations_with_replacement` instead of
  nested `for` loops — same result, and the name documents which one you mean.
- **A running total or running best-so-far** → `itertools.accumulate` instead
  of a manual loop with an accumulator variable.
- **Two sequences of different lengths, paired position-by-position** →
  `itertools.zip_longest`, since the builtin `zip` silently truncates to the
  shorter one.

## Gotchas

| Gotcha | Detail |
|---|---|
| `groupby` needs pre-sorted input | It only groups **consecutive** equal keys; unsorted input silently produces multiple small groups for the same key instead of one, with no error. |
| `cycle()` is infinite | `itertools.cycle(iterable)` never stops on its own — always bound it with `islice` or a counter, or a plain `for` loop over it will hang. |
| Consuming a `tee()` branch consumes shared buffered state | `tee()` gives independent iterators, but if one branch lags far behind the other, the library buffers all the skipped items internally until it catches up. |
| Most itertools return *iterators*, not lists | `chain(...)`, `islice(...)`, `accumulate(...)` etc. are single-use and lazy — printing one directly shows a `<itertools.chain object at ...>`, and once consumed it's empty. |
| `permutations`/`combinations` take an `r` that isn't validated against usefulness | `combinations(items, r)` with `r > len(items)` doesn't error — it just yields nothing. |

## What the 10 levels cover

Level 1 starts with `chain`, the single most common way to treat several
iterables as one. Level 2 covers `islice` for lazy slicing. Level 3 combines
both into a small streaming idiom. Level 4 triggers the real `ValueError` from
an invalid `islice`/`combinations` argument. Level 5 compares `product`,
`permutations`, `combinations`, and `combinations_with_replacement` on the same
input so the differences are concrete. Level 6 is a measured comparison of
`itertools.chain` against repeated list concatenation. Level 7 covers `tee`'s
lifecycle caveat around independent parallel iterators. Level 8 pairs `groupby`
with `operator.itemgetter` for realistic record grouping. Level 9 demonstrates
the classic `groupby`-on-unsorted-input correctness trap and its fix. Level 10
is a capstone report generator combining `chain`, `islice`, `groupby`,
`accumulate`, `zip_longest`, `cycle`, and `starmap`.
