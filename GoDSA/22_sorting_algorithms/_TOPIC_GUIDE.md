# Topic 22 · Sorting Algorithms — Go Deep Dive

> Topic 01 told you to reach for `sort.Slice` and `slices.Sort` and move on. This
> document is about what happens when the interviewer says "don't use the
> standard library" — and about understanding what `sort.Slice` is actually
> doing under the hood, because "it's pdqsort" is a one-line answer that hides
> a genuinely interesting three-algorithm hybrid.

---

## Part 1 · What `sort.Slice` Actually Does

### 1.1 pdqsort is not "just quicksort"

Since Go 1.19, `sort.Sort`, `sort.Slice`, and (via a similar core) `slices.Sort`
are backed by **pdqsort** — pattern-defeating quicksort. It is an **introsort**:
a hybrid that switches strategy based on partition size and recursion depth,
specifically so that no single pathological input can force it into quadratic
behavior.

```
   pdqsort_func(data, a, b, limit)          limit = bits.Len(n) — a budget of "bad pivots"
        │
        ├─ length <= 12 ──────────────► insertion sort, done
        │
        ├─ limit == 0 ────────────────► heapsort this range, done   (the O(n log n) guarantee)
        │
        ├─ last partition was unbalanced? ► breakPatterns (swap a few elements), limit--
        │
        ├─ choose a pivot:  length < 8  → the middle element
        │                   8 .. 49     → median of three
        │                   >= 50       → Tukey "ninther" (median of three medians)
        │   the samples also say "looks increasing / decreasing": a decreasing range is reversed first
        │
        ├─ looks sorted and the last partition was balanced?
        │      └─► partialInsertionSort: give up after 5 out-of-place elements (only tried on ranges >= 50)
        │
        ├─ pivot equals the element just left of this range?  (many duplicates)
        │      └─► partitionEqual: peel off everything equal to the pivot, continue on the greater side
        │
        └─ partition; recurse into the SMALLER side, loop on the larger (O(log n) stack)
               "balanced" means the smaller side holds at least length/8 elements
```

- **Small ranges (up to and including 12 elements):** insertion sort. Quicksort's overhead isn't worth it at this size,
  and insertion sort is O(n) on nearly-sorted data.
- **Too many bad pivots:** the range gets `bits.Len(n)` (about `log₂ n + 1`) "bad pivot" credits. A pivot is *bad* when the
  smaller side ends up under `length/8`; each bad one costs a credit, and at zero the range is **heapsorted**, which is
  O(n log n) whatever the data. That is the real worst-case guarantee — plain quicksort has none. (It is a budget of bad
  *pivots*, not a recursion-depth check.)
- **Pattern defeaters:** the pivot rule (median of three, ninther for big ranges), `breakPatterns` after a bad partition,
  `partialInsertionSort` and the reverse-a-decreasing-range step make sorted and reverse-sorted inputs cost O(n) — measured
  below — and `partitionEqual` handles duplicate-heavy data (the thing plain Lomuto quicksort cannot, see Part 9.1).

> ⚡ This is why you can no longer construct a simple "kill Go's sort with a
> sorted array" adversarial input the way you once could against naive
> quicksort — pdqsort detects the degenerate recursion pattern and bails to
> heapsort before it goes quadratic.

### 1.2 `sort.Interface` vs the generic `slices` package

Pre-generics Go (before 1.18) could only sort through an interface:

```go
type Interface interface {
    Len() int
    Less(i, j int) bool
    Swap(i, j int)
}

type byAge []Person
func (a byAge) Len() int           { return len(a) }
func (a byAge) Less(i, j int) bool { return a[i].Age < a[j].Age }
func (a byAge) Swap(i, j int)      { a[i], a[j] = a[j], a[i] }

sort.Sort(byAge(people))
```

`sort.Slice(xs, less)` is a shortcut that spares you the three methods: it takes your `less(i, j)` closure over *indices* and
uses `reflectlite.Swapper` — reflection — to swap elements, so every comparison and every swap is an indirect call
(pass it something that is not a slice and it panics with `reflect: call of Swapper on int Value`).

Go 1.21's generic `slices` package sorts without that indirection:

```go
slices.Sort(nums)                                          // Ordered constraint
slices.SortFunc(people, func(a, b Person) int { return cmp.Compare(a.Age, b.Age) }) // never a.Age - b.Age: it can overflow
slices.SortStableFunc(people, cmp)
```

> ⚡ `slices.Sort`/`slices.SortFunc` are instantiated generically per type at
> compile time — no interface vtable call per comparison, no boxing. For large
> slices this is measurably faster than `sort.Slice`. Default to the `slices`
> package on Go 1.21+; reach for `sort.Slice` only in older codebases or when
> you need `sort.Interface` for something else (e.g. `container/heap`, which
> still requires the old-style interface — see Topic 12).

### 1.3 Stability, revisited with teeth

`sort.Slice` / `slices.Sort` / `slices.SortFunc` are **not stable** — pdqsort
freely reorders equal elements. `sort.Stable` / `slices.SortStableFunc` are
stable, but slower: they sort blocks of 20 with insertion sort and then merge in place with **SymMerge**, which needs no
buffer but moves elements a lot. The documentation's own bound is **O(n log n) calls to `Less` and O(n log² n) calls to
`Swap`**, with O(log n) recursion and no auxiliary array.

```go
type Task struct {
    Priority int
    Name     string
}
tasks := []Task{{1, "a"}, {2, "x"}, {1, "b"}, {2, "y"}, {1, "c"}}

sort.SliceStable(tasks, func(i, j int) bool { return tasks[i].Priority < tasks[j].Priority })
// priority-1 tasks come out in original order: a, b, c — then x, y.

sort.Slice(tasks, func(i, j int) bool { return tasks[i].Priority < tasks[j].Priority })
// order of equal priorities is NOT guaranteed.
```

> ⚠️ **Do not trust a small test to reveal this.** Ranges of up to 12 elements are sorted with insertion sort, which *is*
> stable, so a five-element example like the one above always happens to come out in input order. Measured: with random
> 3-valued keys, `slices.SortFunc` left ties in input order for every one of 200 inputs of 12 elements — and broke the order
> in **all 200** inputs of 13 elements (and of 20, 100 and 1000). For `sort.Slice` with two key values the smallest
> failing size I found was 13. The bug appears the day the data outgrows the test.

> ⚠️ If a later step in your algorithm depends on "elements with equal keys
> keep their input order" — e.g. you sorted by priority and now rely on
> insertion order as a tiebreak for FIFO processing — using `sort.Slice`
> instead of `sort.SliceStable` is a real, silent correctness bug. Python's
> `list.sort()`/`sorted()` (Timsort) is *always* stable, so this class of bug
> does not exist when porting from Python — it is introduced by moving to Go.

---

## Part 2 · Hand-Rolled Comparison Sorts

Interviews that ask you to "implement sort" want to see you reproduce this
reasoning in code, not call `slices.Sort`.

### 2.1 Quicksort (Lomuto partition, randomized pivot)

```go
func quickSort(nums []int) {
    quickSortRange(nums, 0, len(nums)-1)
}

func quickSortRange(nums []int, lo, hi int) {
    if lo >= hi {
        return
    }
    // Randomize the pivot choice. A fixed "always pick nums[hi]" pivot is
    // O(n^2) on already-sorted or reverse-sorted input — an adversary (or an
    // interview test case!) that knows your pivot rule can trivially trigger
    // the worst case. A random pivot makes that attack impossible in
    // expectation, at the cost of one rand.Intn call per partition.
    r := lo + rand.Intn(hi-lo+1)
    nums[r], nums[hi] = nums[hi], nums[r]

    p := lomutoPartition(nums, lo, hi)
    quickSortRange(nums, lo, p-1)
    quickSortRange(nums, p+1, hi)
}

// lomutoPartition places nums[hi] (the pivot) into its final sorted position
// and returns that position. Everything left of it is <= pivot, everything
// right is > pivot.
func lomutoPartition(nums []int, lo, hi int) int {
    pivot := nums[hi]
    i := lo // boundary: nums[lo:i] are all <= pivot
    for j := lo; j < hi; j++ {
        if nums[j] <= pivot {
            nums[i], nums[j] = nums[j], nums[i]
            i++
        }
    }
    nums[i], nums[hi] = nums[hi], nums[i]
    return i
}
```

- **Average:** O(n log n). **Worst case:** O(n²) — every pivot the min or max of its partition. A random pivot makes that
  vanishingly unlikely for *distinct* keys — but **not for duplicates**: `nums[j] <= pivot` sends every equal element to the
  same side, so an all-equal slice peels off one element per pass. Measured for `n = 20,000`: **199,990,000** comparisons on
  all-equal input against 343,232 on random input. The fix is a 3-way partition (Part 9.1).
- **Space:** O(log n) expected recursion depth (O(n) worst case, unmitigated —
  mention this honestly if asked; pdqsort avoids it via the heapsort fallback,
  a plain hand-rolled quicksort does not unless you also add that fallback).
- **Not stable:** Lomuto's swaps freely reorder equal elements.

### 2.2 Merge sort (guaranteed O(n log n), stable by construction)

```go
func mergeSort(nums []int) []int {
    if len(nums) <= 1 {
        return nums
    }
    mid := len(nums) / 2
    left := mergeSort(append([]int(nil), nums[:mid]...))  // copy — see note
    right := mergeSort(append([]int(nil), nums[mid:]...))
    return merge(left, right)
}

func merge(left, right []int) []int {
    result := make([]int, 0, len(left)+len(right)) // preallocate — Part 1.3, Topic 01
    i, j := 0, 0
    for i < len(left) && j < len(right) {
        // <= (not <) keeps a left-side element ahead of an equal right-side
        // element, which is exactly what "stable" means: equal keys keep
        // their relative input order.
        if left[i] <= right[j] {
            result = append(result, left[i])
            i++
        } else {
            result = append(result, right[j])
            j++
        }
    }
    result = append(result, left[i:]...)
    result = append(result, right[j:]...)
    return result
}
```

> ⚠️ `nums[:mid]` and `nums[mid:]` alias the original backing array (Topic 01,
> Part 1.2). Recursing directly on those sub-slices would work for splitting,
> but the moment you build `result` by merging into a *new* slice at every
> level, the original array is never mutated — so the `append([]int(nil), …)`
> copy above is defensive, not strictly required by this particular
> implementation. If you instead try to merge back **in place** into the
> original array (an in-place merge sort, a genuinely harder variant), the
> aliasing between the two halves and the destination becomes the whole
> problem — that's why almost every from-scratch merge sort you'll write uses
> a fresh output slice per merge instead.

- **Time:** O(n log n) **guaranteed** — no worst case, unlike quicksort.
- **Space:** O(n) auxiliary (the `result` slices at every merge level) — this
  is merge sort's real cost relative to heapsort's O(1).
- **Stable:** yes, by construction of the `<=` comparison above. This is
  merge sort's other headline property, and the reason to reach for it by
  hand when you need a stable sort and can afford an O(n) buffer: measured on a million random ints, a one-buffer merge sort
  took 58 ms against 153 ms for `slices.SortStableFunc` and 252 ms for `sort.Stable` (Part 8.1, Part 9.2).

### 2.3 Heap sort (O(1) space, not stable)

Build a max-heap over the slice **in place**, then repeatedly swap the root
(the max) to the end of the live region and shrink it by one, sifting the new
root down to restore the heap property. Cross-reference Topic 12 for the
sift-down mechanics and the array-as-tree index math (`2i+1`, `2i+2`).

```go
func heapSort(nums []int) {
    n := len(nums)
    for i := n/2 - 1; i >= 0; i-- { // build max-heap: O(n), not O(n log n) —
        siftDown(nums, i, n)       // see Topic 12's heapify amortized argument
    }
    for end := n - 1; end > 0; end-- {
        nums[0], nums[end] = nums[end], nums[0] // move current max to its slot
        siftDown(nums, 0, end)                  // restore heap over the shrunk region
    }
}

func siftDown(nums []int, i, n int) {
    for {
        largest, l, r := i, 2*i+1, 2*i+2
        if l < n && nums[l] > nums[largest] {
            largest = l
        }
        if r < n && nums[r] > nums[largest] {
            largest = r
        }
        if largest == i {
            return
        }
        nums[i], nums[largest] = nums[largest], nums[i]
        i = largest
    }
}
```

- **Time:** O(n log n) worst case, guaranteed — same guarantee pdqsort borrows
  its fallback from.
- **Space:** O(1) — sorts in place with no auxiliary buffer, unlike merge
  sort's O(n). This is heap sort's headline advantage.
- **Not stable:** swapping the root to the end freely reorders equal keys.

---

## Part 3 · Non-Comparison Sorts

Comparison sorts have an information-theoretic floor of O(n log n) — you
cannot beat it by comparing elements pairwise. Non-comparison sorts sidestep
this by exploiting structure in the *values* themselves (small integer range),
not just their relative order.

### 3.1 Counting sort — O(n + k)

Direct application of Topic 01's frequency-array idiom: if keys are integers
in a known small range `[0, k)`, count occurrences, then reconstruct. (Negative keys need an offset — the version in
Part 9.3 subtracts the minimum.)

```go
func countingSort(nums []int, k int) []int {
    counts := make([]int, k)
    for _, v := range nums {
        counts[v]++
    }
    result := make([]int, 0, len(nums))
    for v, c := range counts {
        for ; c > 0; c-- {
            result = append(result, v)
        }
    }
    return result
}
```

This version is not stable as written (it discards original positions
entirely and rebuilds by value). A **stable** counting sort instead computes a
prefix sum over `counts` to get each value's starting output index, then
places original elements (not just their value) into `result` by walking the
input **left to right** and incrementing that starting index — this is the
form used as a subroutine inside radix sort.

- **Time:** O(n + k). **Space:** O(n + k). Beats O(n log n) whenever `k =
  O(n)` — e.g., LC 347 Top K Frequent Elements can bucket by frequency (which
  ranges only `0..n`) instead of sorting by frequency, for O(n) total instead
  of O(n log n).

### 3.2 Bucket sort — O(n + k) expected

Partition values into `k` buckets by range, sort each bucket (with any
algorithm — often insertion sort, since buckets are small), concatenate.
Good when input is roughly uniformly distributed over a known range; degrades
toward O(n²) if all elements land in one bucket.

---

## Part 4 · Complexity Table

| Algorithm | Best | Average | Worst | Space | Stable? |
|---|:--:|:--:|:--:|:--:|:--:|
| pdqsort (`sort.Slice`, `slices.Sort`) | O(n) | O(n log n) | **O(n log n)** | O(log n) | ❌ |
| `sort.Stable` / `slices.SortStableFunc` | — | O(n log n) compares, O(n log² n) swaps | same | O(log n) (in place) | ✅ |
| Quicksort (naive, fixed pivot) | O(n log n) | O(n log n) | O(n²) | O(log n) | ❌ |
| Quicksort (randomized pivot) | O(n log n) | O(n log n) | O(n²)* | O(log n) | ❌ |
| Merge sort | O(n log n) | O(n log n) | **O(n log n)** | O(n) | ✅ |
| Heap sort | O(n log n) | O(n log n) | **O(n log n)** | **O(1)** | ❌ |
| Insertion sort | **O(n)** | O(n²) | O(n²) | O(1) | ✅ |
| Counting sort | O(n+k) | O(n+k) | O(n+k) | O(n+k) | ✅ (proper form) |
| Bucket sort | O(n+k) | O(n+k) | O(n²) | O(n+k) | depends |

\* vanishingly unlikely, not eliminated, for randomized quicksort — pdqsort's
heapsort fallback is what actually eliminates it.

---

## Part 5 · Python vs. Go — Where They Diverge

| | Python | Go |
|---|---|---|
| Default sort algorithm | Timsort (merge-sort family) | pdqsort (quicksort family) |
| Default stability | **Always stable** | **Not stable** (`sort.Slice`) |
| Stable option | (already the default) | `sort.Stable` / `slices.SortStableFunc` — in place, but O(n log² n) swaps |
| Sort dispatch mechanism | Duck-typed `__lt__` / `key=` | `sort.Interface` (pre-generics) or generic `slices.SortFunc` |
| Worst-case guarantee | O(n log n) (Timsort) | O(n log n) (pdqsort's heapsort fallback) |
| Built-in stable-merge sort access | `sorted()` itself | Must hand-roll (one-buffer merge sort), or accept `sort.Stable`'s extra log n factor in swaps |
| Counting/bucket sort in stdlib | None (hand-roll both) | None (hand-roll both) |

Python's Timsort is *already* what Go needs `sort.Stable` for — a genuinely
adaptive, stable merge sort — so "just use the default sort" is unconditionally
safe in Python and conditionally unsafe in Go. This is the one fact from this
guide worth remembering above all others.

---

## Part 6 · Algorithms Owned by This Topic

| Algorithm | Time | Space | Problem |
|---|:--:|:--:|---|
| pdqsort via `slices.Sort`/`sort.Slice` | O(n log n) | O(log n) | Any "sort first" solution |
| Hand-rolled quicksort | O(n log n) avg | O(log n) | Kth Largest Element (LC 215), quickselect variant |
| Hand-rolled merge sort | O(n log n) | O(n) | Sort List (LC 148, linked-list merge sort), Count of Smaller Numbers After Self (LC 315) |
| Heap sort | O(n log n) | O(1) | In-place top-K without extra structures |
| Counting sort | O(n+k) | O(n+k) | Sort Colors (LC 75, k=3 case), Top K Frequent Elements (LC 347) via bucket-by-frequency |
| Bucket sort | O(n+k) expected | O(n+k) | Maximum Gap (LC 164) |

---

## Part 7 · Building Merge Sort and Quicksort From Scratch

Both are given in full in Parts 2.1–2.2 above. As a single runnable-shaped
reference, here is the entry point you'd actually write in an interview,
combining both with a correctness check:

```go
package main

import (
    "fmt"
    "math/rand"
)

func main() {
    a := []int{5, 2, 9, 1, 5, 6, 3, 8, 2, 0}
    b := append([]int(nil), a...) // independent copy — Topic 01, Part 1.2

    quickSort(a)
    sorted := mergeSort(b)

    fmt.Println(a)      // sorted in place
    fmt.Println(sorted) // new slice, b left untouched
}
```

**Talk track while writing:** name the pivot strategy and why it's randomized
before you write the partition loop; state merge sort's O(n) space cost
before an interviewer has to ask; and if asked for O(1) extra space, pivot
immediately to heap sort rather than trying to force merge sort in place.

---

<!-- block:22_go_1_stdlib -->
## Part 8 · The Standard Library, Measured — Cost, Comparators, Stability in Practice

Part 1 says what pdqsort *is*. This Part is what you can *say about it with numbers* — and the three ways it goes wrong in
real code. Everything ran on Go 1.24 (darwin/arm64); each time is the best of five runs sorting a fresh copy of a
million-element `[]int`.

### 8.1 What each call costs, on five input shapes

| Input (n = 10⁶) | `slices.Sort` | `sort.Slice` | `slices.SortFunc` | `slices.SortStableFunc` | `sort.Stable` |
|---|--:|--:|--:|--:|--:|
| random | **51.8 ms** | 84.1 ms | 72.6 ms | 153.5 ms | 252.1 ms |
| already sorted | 0.5 ms | 1.3 ms | 1.3 ms | 2.1 ms | 2.3 ms |
| reversed | 0.7 ms | 1.9 ms | 1.5 ms | 18.0 ms | 41.4 ms |
| all equal | 0.5 ms | 1.3 ms | 1.5 ms | 2.1 ms | 2.0 ms |
| 4 distinct values | 4.8 ms | 9.3 ms | 10.3 ms | 31.8 ms | 56.6 ms |

(`SortFunc` used `cmp.Compare[int]`; `sort.Stable` used `sort.IntSlice`.) Four things to read off it:

1. **Sorted, reversed and all-equal inputs cost O(n)** — half a millisecond for a million elements. That is
   `partialInsertionSort`, the reverse-a-decreasing-range step and `partitionEqual` from Part 1.1 doing their job; you cannot
   feed pdqsort a "sorted array" and hurt it.
2. **The typed call wins:** `slices.Sort` (51.8 ms) beat `sort.Slice` (84.1 ms) by about 1.6× on random data because it has no
   reflection-based swap and no indirect `less` call. `sort.Ints` measured 51.2 ms — since Go 1.22 it simply calls
   `slices.Sort`. `slices.SortFunc` sits in between (72.6 ms): still a function-value call per comparison.
3. **Stability is not free:** on random data `slices.SortStableFunc` took about 3× `slices.Sort`, and the old `sort.Stable` about
   5×. On *reversed* input the stable sorts fall off the O(n) fast path (18 ms and 41 ms).
4. **`slices.SortStableFunc` beats `sort.Stable`** (153.5 against 252.1 ms) — same algorithm, no interface dispatch.

### 8.2 Comparators: `cmp.Compare`, `cmp.Or`, and the subtraction bug

`slices.SortFunc` wants a three-way `int` (negative, zero, positive); `sort.Slice` wants a `bool` over *indices*. Both need a
**strict weak ordering** — a comparator that says "less" for equal elements (`<=`) breaks the contract, and the result is
unspecified. (Go did not panic when I sorted 1,000 values in `[0, 3]` with `<=`, and the output happened to be sorted — do
not read that as permission.)

```go
// descending, then a multi-key sort with cmp.Or (Go 1.22): age descending, name ascending
slices.SortFunc(xs, func(a, b int) int { return cmp.Compare(b, a) })
slices.SortFunc(ps, func(a, b P) int { return cmp.Or(cmp.Compare(b.age, a.age), cmp.Compare(a.name, b.name)) })
// [{bo 30} {al 30} {cy 25}] -> [{al 30} {bo 30} {cy 25}]
```

**Never write `a - b` as the comparator.** It overflows, silently. Measured: `slices.SortFunc(xs, func(a, b int) int { return a - b })`
on `[MaxInt64, -5, MinInt64+1, 3]` returned `[9223372036854775807 -9223372036854775807 -5 3]` — not sorted — while
`cmp.Compare[int]` sorted it. The same bug shows up with `int32` keys: `int(a - b)` on `[2000000000, -2000000000, 0, 5]`
computes the subtraction in `int32`, wraps, and leaves the slice unsorted. Other API facts: `sort.Sort(sort.Reverse(sort.IntSlice(xs)))`
also sorts descending; `slices.Sort` orders **NaN before every other float** (`[3 NaN 1 NaN 2]` → `[NaN NaN 1 2 3]`); `slices.Sort`
works directly on `[]rune` and `[]byte` (`"hello"` → `"ehllo"`), and `sort.Slice(5, …)` panics because it needs a slice.

A `sort.Slice` closure indexes *its own* slice. Point it at another slice and nothing errors — it just does not sort
(`less` over an all-zero `other` left `[3 1 2]` untouched).

### 8.3 Stability, when you cannot trust the default

Part 1.3 showed that `sort.Slice` and `slices.SortFunc` are not stable — and that the instability **only appears above 12
elements**. You have two remedies, both measured stable over 200 random inputs of 1,000 elements:

```go
slices.SortStableFunc(xs, func(a, b rec) int { return cmp.Compare(a.key, b.key) }) // 0 of 200 inputs out of order

// or: keep the original index and make it the final tiebreak — a TOTAL order, so any sort is deterministic
slices.SortFunc(xs, func(a, b rec) int {
    return cmp.Or(cmp.Compare(a.key, b.key), cmp.Compare(a.id, b.id))               // 0 of 200 inputs out of order
})
```

The second form keeps pdqsort's speed and also removes run-to-run ambiguity, at the price of storing the index. If the
stability requirement is the *point* of the problem (Problem 008's merge, or a stable partition), write the merge sort in
Part 9.2 — it beat `slices.SortStableFunc` by about 2.6× on the random million (58 ms against 153 ms).

### 8.4 Searching sorted data

`slices.BinarySearch(xs, target)` returns `(index, found)` where `index` is the insertion point when `found` is false:
on `[1 3 3 5 9]`, `3` gives `(1, true)` and `4` gives `(3, false)`; `sort.SearchInts(xs, 4)` is `3` and
`sort.SearchInts(xs, 10)` is `5` (`len(xs)`). `slices.IsSorted` checks the precondition. With duplicates the index is the
*leftmost* match — the lower bound (topic 05).

---
<!-- /block:22_go_1_stdlib -->

<!-- block:22_go_2_algorithms -->
## Part 9 · The Algorithms the Guide Above Leaves Out — Duplicates, One Buffer, Radix, and the Eight Problems in Go

Parts 2–3 give the textbook versions; three of them have real weaknesses in Go (a quicksort that is quadratic on duplicates, a
merge sort that allocates at every level, a counting sort that panics on negatives). Every snippet below was compiled with
`go vet` and checked against `slices.Sort` on random input (500 cases per sort, lengths 0–59, values in `[-10, 9]`).

```arch
%% caption: Choosing a sort in Go. The standard library covers most cases; hand-rolled sorts are for stability, bounded keys or the interview itself.
grid 240x80
node q "Sort a slice in Go" at 0,0 shape=pill
node a "Keys are small\nintegers?" at 0,1 shape=diamond color=amber
node b "Counting sort" at 1,1 color=green w=260 sub="or LSD radix for 32-bit keys"
node c "Equal keys must\nkeep input order?" at 0,2 shape=diamond color=amber w=250
node d "slices.SortStableFunc" at 1,2 color=amber w=260 sub="or an index tiebreak, or a one-buffer merge sort"
node e "slices.Sort / slices.SortFunc" at 0,3 color=green w=230 sub="pdqsort"
node f "Comparator subtracts?" at 0,4 shape=diamond color=amber
node g "Use cmp.Compare" at 1,4 color=red w=260 sub="subtraction overflows"
q -> a
a -> b : "yes"
a -> c : "no"
c -> d : "yes"
c -> e : "no"
e -> f
f -> g : "yes"
```

### 9.1 Quicksort with a 3-way partition — and why the Lomuto version is quadratic on duplicates

A random pivot defeats *sorted* input, not *duplicates*. With `nums[j] <= pivot`, every element equal to the pivot lands on
one side, so an all-equal slice loses a single element per pass. Counting comparisons for `n = 20,000`:

| Input | Lomuto (Part 2.1) | 3-way |
|---|--:|--:|
| random | 343,232 | 347,810 |
| all equal | **199,990,000** | **20,000** |
| 4 distinct values | 50,046,069 | 39,860 |

```go
func quick3(a []int, lo, hi int) { // random pivot + Dutch-flag partition; recurse on the smaller side
    for lo < hi {
        pivot := a[lo+rand.Intn(hi-lo+1)]
        lt, i, gt := lo, lo, hi // a[lo:lt] < pivot   a[lt:i] == pivot   a[gt+1:hi+1] > pivot
        for i <= gt {
            switch {
            case a[i] < pivot:
                a[lt], a[i] = a[i], a[lt]
                lt++
                i++
            case a[i] > pivot:
                a[i], a[gt] = a[gt], a[i]
                gt--
            default:
                i++
            }
        }
        if lt-lo < hi-gt {
            quick3(a, lo, lt-1)
            lo = gt + 1
        } else {
            quick3(a, gt+1, hi)
            hi = lt - 1
        }
    }
}
```

The inner loop is Problem 003's Dutch national flag with the pivot chosen at random instead of fixed to `1`. Looping on the
larger side and recursing on the smaller keeps the stack at O(log n) even when the partitions are lopsided.

```arch
%% caption: Dutch national flag: one pass, three regions. The 2 case does not advance mid because the swapped-in value is still unexamined.
grid 180x80
node a "lo = 0, mid = 0, hi = n - 1" at 1,0 shape=pill w=240
node b "mid ≤ hi ?" at 1,1 shape=diamond color=amber
node z "sorted" at 0,1 color=green
node c "nums[mid]" at 1,2 shape=diamond color=amber
node d "swap(lo, mid)" at 2,2 w=190 sub="lo += 1, mid += 1"
node e "mid += 1" at 2,3 w=190
node f "swap(mid, hi), hi -= 1" at 2,4 color=amber w=190 sub="do NOT advance mid"
a -> b
b -> z : "no"
b -> c : "yes"
c:R -> d:L : "0"
c:R -> e:L : "1"
c:R -> f:L : "2"
d:R -> b:R
e:R -> b:R
f:R -> b:R
```

### 9.2 Merge sort with one buffer, and bottom-up

The Part 2.2 version allocates a fresh slice at every level. Sorting **in place over one shared buffer** allocates once, and
skipping the merge when the halves are already ordered makes sorted input cost O(n):

```go
func mergeSort(a []int) {
    buf := make([]int, len(a))
    var rec func(lo, hi int)
    rec = func(lo, hi int) {
        if hi-lo <= 1 { return }
        mid := lo + (hi-lo)/2
        rec(lo, mid)
        rec(mid, hi)
        if a[mid-1] <= a[mid] { return } // already in order: skip the merge
        copy(buf[lo:hi], a[lo:hi])
        i, j := lo, mid
        for k := lo; k < hi; k++ {
            if j >= hi || (i < mid && buf[i] <= buf[j]) { // <= : the left element wins ties => stable
                a[k] = buf[i]; i++
            } else {
                a[k] = buf[j]; j++
            }
        }
    }
    rec(0, len(a))
}
```

The **bottom-up** form needs no recursion: merge runs of width 1, 2, 4, … from `src` into `dst`, swapping the two slices after
each pass, and copy back at the end if an odd number of passes left the answer in the buffer (test `&src[0] != &a[0]`, and
return early for `len(a) < 2` — `&src[0]` on an empty slice panics).

Measured, `n = 10⁶` random ints: **58.4 ms** for the recursive one-buffer version and **52.8 ms** bottom-up, against 51.8 ms for
`slices.Sort` and 153.5 ms for `slices.SortStableFunc`. On already-sorted input the skip test made the recursive version take
3.3 ms; the bottom-up version has no such shortcut (9.0 ms).

### 9.3 Counting sort and LSD radix sort — in compiled Go, O(n) really wins

```go
// stable counting sort; subtracting the minimum makes negative keys work
func countingSort(a []int) []int {
    if len(a) == 0 { return nil }
    lo, hi := slices.Min(a), slices.Max(a)
    count := make([]int, hi-lo+2)
    for _, v := range a { count[v-lo+1]++ }
    for i := 1; i < len(count); i++ { count[i] += count[i-1] } // count[k] = first output index of key k
    out := make([]int, len(a))
    for _, v := range a { // left to right => stable
        out[count[v-lo]] = v
        count[v-lo]++
    }
    return out
}

// LSD radix sort for int32: four stable passes of 8 bits; flipping the sign bit makes negatives sort first
func radixSort(a []int32) {
    buf := make([]int32, len(a))
    for shift := 0; shift < 32; shift += 8 {
        var count [257]int
        for _, v := range a { count[int((uint32(v)^0x80000000)>>shift)&0xFF+1]++ }
        for i := 1; i < 257; i++ { count[i] += count[i-1] }
        for _, v := range a {
            d := int((uint32(v)^0x80000000)>>shift) & 0xFF
            buf[count[d]] = v
            count[d]++
        }
        a, buf = buf, a
    }
    // four passes = an even number of swaps, so the result is back in the caller's slice
}
```

Unlike CPython (where the built-in beats every pure-Python O(n) sort — see the Python guide), compiled Go lets the linear-time
algorithms win. Measured: a million `int32` values sorted by `radixSort` in **3.3 ms** against **50.9 ms** for `slices.Sort`
(and the output matched `slices.Sort` exactly); a million values in `[0, 1000)` took **0.5 ms** with a plain counting loop
against **23.6 ms** for `slices.Sort`. The flip of the sign bit (`^ 0x80000000`) maps `MinInt32 … MaxInt32` monotonically onto
`0 … 2³²−1` — without it, negative numbers (top bit set) would sort *after* the positives.

### 9.4 The eight problems, as you would write them in Go

The Go solution files for this topic are still placeholders, so here are the plans, each run against a brute-force or
`slices.Sort` reference (2,000 random cases for 006–008, 300 permutation checks for 005).

```go
// 001 Merge Sorted Array — from the back
func merge(nums1 []int, m int, nums2 []int, n int) {
    i, j, k := m-1, n-1, m+n-1
    for j >= 0 { // once nums2 is exhausted, the rest of nums1 is already in place
        if i >= 0 && nums1[i] > nums2[j] { nums1[k] = nums1[i]; i-- } else { nums1[k] = nums2[j]; j-- }
        k--
    }
}

// 003 Sort Colors — Dutch national flag
func sortColors(nums []int) {
    lo, mid, hi := 0, 0, len(nums)-1
    for mid <= hi {
        switch nums[mid] {
        case 0: nums[lo], nums[mid] = nums[mid], nums[lo]; lo++; mid++
        case 1: mid++
        default: nums[mid], nums[hi] = nums[hi], nums[mid]; hi-- // do NOT advance mid
        }
    }
}

// 005 Largest Number — the comparator is the problem
func largestNumber(nums []int) string {
    s := make([]string, len(nums))
    for i, v := range nums { s[i] = strconv.Itoa(v) }
    slices.SortFunc(s, func(a, b string) int { return cmp.Compare(b+a, a+b) }) // a first if a+b > b+a
    if s[0] == "0" { return "0" }
    return strings.Join(s, "")
}
```

`largestNumber([]int{3, 30, 34, 5, 9})` is `"9534330"`, `[10, 2]` is `"210"`, and `[0, 0]` is `"0"`. Sorting the numbers
descending instead gives `[34 30 9 5 3]` — the wrong answer. The comparator was checked against every permutation of 1–5
random numbers below 120 (300 trials, 0 mismatches).

```go
// 006 H-Index — count by min(citation, n), sweep down; O(n)
func hIndex(c []int) int {
    n := len(c)
    cnt := make([]int, n+1)
    for _, v := range c { cnt[min(v, n)]++ }
    total := 0
    for h := n; h >= 0; h-- {
        total += cnt[h]
        if total >= h { return h }
    }
    return 0
}

// 007 Maximum Gap — pigeonhole buckets, O(n)
func maximumGap(nums []int) int {
    n := len(nums)
    if n < 2 { return 0 }
    lo, hi := slices.Min(nums), slices.Max(nums)
    if lo == hi { return 0 }
    size := max(1, (hi-lo)/(n-1)) // bucket width; the max(1, …) prevents a zero width
    nb := (hi-lo)/size + 1
    bmin, bmax := make([]int, nb), make([]int, nb)
    for i := range bmin { bmin[i], bmax[i] = math.MaxInt, math.MinInt }
    for _, v := range nums {
        b := (v - lo) / size
        bmin[b], bmax[b] = min(bmin[b], v), max(bmax[b], v)
    }
    best, prev := 0, lo
    for b := 0; b < nb; b++ {
        if bmin[b] == math.MaxInt { continue } // empty bucket
        best = max(best, bmin[b]-prev)
        prev = bmax[b]
    }
    return best
}
```

`hIndex` gives `3` for `[3,0,6,1,5]`, `1` for `[1,3,1]`, `0` for `[0]` and `1` for `[100]`; `maximumGap` gives `3` for `[3,6,9,1]`,
`0` for `[10]` and for `[1,1,1]`, and `9999999` for `[1, 10000000]`.

```go
// 008 Count of Smaller Numbers After Self — merge sort over INDICES
func countSmaller(nums []int) []int {
    n := len(nums)
    idx, buf, ans := make([]int, n), make([]int, n), make([]int, n)
    for i := range idx { idx[i] = i }
    var rec func(lo, hi int)
    rec = func(lo, hi int) {
        if hi-lo <= 1 { return }
        mid := lo + (hi-lo)/2
        rec(lo, mid)
        rec(mid, hi)
        i, j, k, moved := lo, mid, lo, 0 // moved = right-half elements already placed
        for i < mid || j < hi {
            if j == hi || (i < mid && nums[idx[i]] <= nums[idx[j]]) { // <= : ties do not count as smaller
                ans[idx[i]] += moved
                buf[k] = idx[i]; i++
            } else {
                moved++
                buf[k] = idx[j]; j++
            }
            k++
        }
        copy(idx[lo:hi], buf[lo:hi])
    }
    rec(0, n)
    return ans
}
// countSmaller([5,2,6,1]) = [2 1 1 0]   ([-1,-1]) = [0 0]   ([2,0,1]) = [2 0 0]
```

And Problem 004 — sorting a linked list — is merge sort on pointers. Starting `fast` one step ahead of `slow` leaves `slow` on
the *last node of the first half*, so cutting at `slow.Next` needs no trailing `prev`:

```go
func sortList(head *ListNode) *ListNode {
    if head == nil || head.Next == nil { return head }
    slow, fast := head, head.Next
    for fast != nil && fast.Next != nil { slow, fast = slow.Next, fast.Next.Next }
    right := slow.Next
    slow.Next = nil // CUT: without it both halves share the tail
    return mergeTwo(sortList(head), sortList(right))
}
```

with `mergeTwo` the topic-08 splice (`<=` so the left node wins ties). It matched `slices.Sort` on 1,000 random lists and sorted a
million-node list; recursion depth is only `log₂ n`.

### 9.5 Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Why is `slices.Sort` faster than `sort.Slice`?" | Generic instantiation: no reflection-based swap, no indirect `less` (51.8 vs 84.1 ms on a million ints). |
| "Sort by name, then keep insertion order for ties." | `slices.SortStableFunc`, or an index tiebreak with `cmp.Or`. |
| "Is `sort.Slice` stable on my 5-element test?" | Yes — by accident (insertion sort up to 12 elements); it breaks from 13. |
| "Sort a million 32-bit ints faster than pdqsort." | LSD radix, four passes (3.3 vs 50.9 ms measured). |
| "Sort a huge file." | Sort memory-sized chunks, then a `k`-way merge with a heap (`container/heap`, topic 12). |
| "Find the `k`-th largest." | Quickselect — expected O(n) — or a size-`k` heap (topic 27, topic 12). |
| "Why did my comparator return the wrong order at the extremes?" | `a - b` overflowed — use `cmp.Compare`. |

---
<!-- /block:22_go_2_algorithms -->

<!-- problem-map:start -->
## Part 10 · Every Problem in This Topic, by Pattern

Eight problems, six moves (merge into padding from the back · a guaranteed-O(n log n) engine · partition around a known domain · merge on pointers · the comparator as the whole problem · bucketing instead of comparing · augmenting the merge step) — the Python guide's map in Go. Each **Trap** is a mistake documented in that problem's solution file, plus Go-specific hazards. Topic 22's Go solutions are still placeholders; the Go column is the plan you would write.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Merge Sorted Array](GoDSA/22_sorting_algorithms/001_merge_sorted_array/solution.go) <br>LC 88 · Easy | Merge from the back | `i, j, k := m-1, n-1, m+n-1`; `for j >= 0`, taking `nums1[i]` only when `i >= 0 && nums1[i] > nums2[j]`. **Trap:** merging from the front (overwrites unread data); `for i >= 0 && j >= 0` (strands `nums2` values); dropping the `i >= 0` guard (an index-out-of-range panic in Go, where Python silently wraps). |
| [002 · Sort an Array](GoDSA/22_sorting_algorithms/002_sort_an_array/solution.go) <br>LC 912 · Medium | Merge sort as the guaranteed answer | One shared buffer, `<=` on ties (stable), skip the merge when `a[mid-1] <= a[mid]`. **Trap:** a fixed pivot; the Lomuto partition on duplicates (199,990,000 comparisons on 20,000 equal values — use 3-way); allocating a slice per level; forgetting the `- min` offset in counting sort; `slices.Min` on an empty slice (it panics). |
| [003 · Sort Colors](GoDSA/22_sorting_algorithms/003_sort_colors/solution.go) <br>LC 75 · Medium | Dutch national flag | `lo`/`mid`/`hi` with a `switch`: `0` swaps with `lo` and advances both, `1` advances `mid`, `2` swaps with `hi` and shrinks `hi` without advancing `mid`. **Trap:** advancing `mid` after the 2-swap; `for mid < hi`; presenting the two-pass count as the final answer. |
| [004 · Sort List](GoDSA/22_sorting_algorithms/004_sort_list/solution.go) <br>LC 148 · Medium | Merge sort on a linked list | `slow, fast := head, head.Next` leaves `slow` on the first half's last node; `right := slow.Next; slow.Next = nil`; merge with `<=`. **Trap:** not cutting the list; starting `fast` at `head` while cutting at `slow.Next` (a two-node list is never split, so the recursion never ends); forgetting to attach the leftover list. |
| [005 · Largest Number](GoDSA/22_sorting_algorithms/005_largest_number/solution.go) <br>LC 179 · Medium | The comparator is the problem | `slices.SortFunc(s, func(a, b string) int { return cmp.Compare(b+a, a+b) })`, join, collapse to `"0"`. **Trap:** numeric or lexicographic order (`[3,30,34,5,9]`, `[10,2]`); the comparator's sign flipped (gives the smallest number); `[0,0,0]` → `"000"`; a subtraction comparator. |
| [006 · H-Index](GoDSA/22_sorting_algorithms/006_h_index/solution.go) <br>LC 274 · Medium | Bucket by `min(c, n)` | `cnt[min(v, n)]++`, then sweep `h` from `n` down, accumulating, returning the first `h` with `total >= h`. **Trap:** an uncapped bucket array (index out of range); an ascending sort with `c[i] >= n - i` backwards; aggregate conditions (sum, average). |
| [007 · Maximum Gap](GoDSA/22_sorting_algorithms/007_maximum_gap/solution.go) <br>LC 164 · Hard | Pigeonhole buckets | Width `max(1, (hi-lo)/(n-1))`, `(hi-lo)/size + 1` buckets, only a min and a max per bucket, skip empty buckets when sweeping. **Trap:** no `max(1, …)` (integer divide by zero panics); sorting inside buckets; not skipping empty buckets (the `math.MaxInt` sentinel becomes a giant fake gap); one bucket too few. |
| [008 · Count of Smaller Numbers After Self](GoDSA/22_sorting_algorithms/008_count_of_smaller_numbers_after_self/solution.go) <br>LC 315 · Hard | Augment the merge step | Merge-sort a slice of *indices*; when a left index is placed, add the count of right indices already placed. Or a Fenwick tree over compressed ranks. **Trap:** `<` instead of `<=` on ties; sorting values instead of indices; skipping the leftover-left elements; no compression in the Fenwick version. |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] Explain pdqsort's three-way hybrid: insertion sort (small), quicksort
      (normal), heapsort (recursion-too-deep fallback)
- [ ] State why `sort.Slice`/`slices.Sort` are not stable, and what `sort.Stable`
      costs extra for stability
- [ ] Explain why `slices.SortFunc` is faster than `sort.Slice` (no interface
      dispatch)
- [ ] Implement quicksort with a randomized pivot and explain why a fixed
      pivot is an adversarial-input risk
- [ ] Implement merge sort and explain why it is stable by construction
- [ ] Implement heap sort and state its O(1)-space advantage over merge sort
- [ ] Know when counting sort beats O(n log n) comparison sorts, and why
- [ ] Say, unprompted, that Python's default sort is already stable and Go's
      is not
- [ ] State pdqsort's real thresholds: insertion sort up to 12 elements, a `bits.Len(n)` bad-pivot budget before heapsort, median-of-three below 50 and the ninther from 50, `partitionEqual` for duplicates <!--ca-->
- [ ] Quote the measured gaps: `slices.Sort` ≈ 52 ms, `sort.Slice` ≈ 84 ms, `slices.SortStableFunc` ≈ 153 ms, `sort.Stable` ≈ 252 ms per million random ints <!--ca-->
- [ ] Explain why sorted, reversed and all-equal inputs are O(n) for pdqsort but the stable sorts are not <!--ca-->
- [ ] Never write a `a - b` comparator; use `cmp.Compare`, and `cmp.Or` for multi-key <!--ca-->
- [ ] Know that `sort.Slice` looks stable up to 12 elements and stops being stable at 13 <!--ca-->
- [ ] Write 3-way quicksort and reproduce the 2-way O(n²) failure on all-equal input <!--ca-->
- [ ] Write merge sort over one shared buffer (skip the merge when already ordered) and a bottom-up version <!--ca-->
- [ ] Write stable counting sort with a `- min` offset and an LSD radix sort with the sign-bit flip <!--ca-->
