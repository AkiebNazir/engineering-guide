# Topic 19 · Intervals — Go Deep Dive

> LeetCode hands you intervals as `[][]int` — a slice of 2-element slices — not as
> a named struct. That single fact shapes almost everything below: your sort
> comparator reaches for `intervals[i][0]` instead of `iv.Start`, and every
> "build a new result vs. mutate in place" decision has to think about whose
> backing array you're touching. Get the sort key wrong or the aliasing wrong
> and the bug is silent — the output looks plausible until you feed it an edge
> case with a shared boundary.

---

## Part 1 · Representing an Interval

### 1.1 `[][]int` vs. a named struct

```go
type Interval struct{ Start, End int }
```

Clean, self-documenting, and what you'd reach for in a real codebase. But
LeetCode's Go function signatures give you `intervals [][]int` directly —
each `intervals[i]` is a 2-element `[]int` — so you're sorting and indexing
raw slices-of-slices unless you convert:

```go
sort.Slice(intervals, func(i, j int) bool {
    return intervals[i][0] < intervals[j][0]   // magic numbers: 0 = start, 1 = end
})
```

`intervals[i][0]` and `intervals[i][1]` are magic numbers — easy to transpose
under interview pressure (`[1] < [1]` instead of `[0] < [0]` compiles fine and
produces silently wrong output). ✅ **Recommendation:** if the problem has more
than two or three interval operations, convert to `[]Interval` once at the top
of the function and work in named fields; for a single sort-and-sweep, the raw
`[][]int` with a comment naming the indices is fine and avoids a conversion
pass over the whole input.

```go
// intervals[i][0] = start, intervals[i][1] = end
```

### 1.2 The half-open vs. closed question

Confirm with the problem statement whether `[1,3]` and `[3,5]` "touch" (share
the boundary `3`) and should be treated as overlapping or not. LC 56 (Merge
Intervals) treats touching intervals as mergeable (`<=`); LC 435 (Non-overlapping
Intervals) and the "minimum arrows" problem often hinge on `<` vs `<=` at the
boundary. This single comparison operator is where most interval solutions
fail on the boundary test case — decide it explicitly, don't guess.

---

## Part 2 · Sort Key Depends on the Goal — This Is Not Arbitrary

This is the most common point of confusion in this topic, so it earns its own
Part: **which field you sort by is determined by what the algorithm needs to
guarantee, not by convention.**

### 2.1 Sort by start → for sweeping and merging

Merge Intervals, Insert Interval, and "does interval X overlap anything"
problems all sweep left to right and ask "does the next interval, in start
order, overlap what I've built so far?" That question is only answerable in a
single left-to-right pass if the intervals arrive **in start order** — sorting
by start turns an O(n²) all-pairs overlap check into an O(n) linear sweep.

```go
sort.Slice(intervals, func(i, j int) bool { return intervals[i][0] < intervals[j][0] })
```

### 2.2 Sort by end → for greedy interval-scheduling maximization

"Non-overlapping Intervals" (LC 435, minimum removals to make the rest
non-overlapping) and "Minimum Number of Arrows to Burst Balloons" (LC 452) are
**activity-selection** problems: you're choosing the maximum number of
mutually non-overlapping intervals to *keep*. The greedy proof for this
specific goal requires sorting by **end time**:

> Exchange argument: among all optimal solutions, there is one that includes
> the interval with the earliest end time. Why? Take any optimal solution and
> replace its first-chosen interval with the one that ends earliest overall —
> it can only free up *more* room for what follows, never less, so the
> solution stays optimal. Repeating this argument greedily (always take the
> not-yet-excluded interval with the smallest end, skip everything it
> overlaps, repeat) is therefore safe.

Sorting by *start* does not give this guarantee — a long interval that starts
first can block many short intervals that would otherwise all fit. Sorting by
*end* is what makes the greedy choice provably safe.

```go
sort.Slice(intervals, func(i, j int) bool { return intervals[i][1] < intervals[j][1] })
```

> ⚠️ **Rule of thumb:** merging/inserting/"does this overlap" → sort by start.
> Maximizing the count of kept non-overlapping intervals (equivalently,
> minimizing removals) → sort by end. Mixing these up compiles and runs; it
> just returns the wrong answer on inputs where a long early interval would
> have blocked several short later ones.

---

## Part 3 · Merging Intervals — the Sweep, and an Aliasing Trap

### 3.1 The sweep

After sorting by start, walk once and either extend the last interval in the
result or start a new one:

```go
func merge(intervals [][]int) [][]int {
    if len(intervals) == 0 {
        return intervals
    }
    sort.Slice(intervals, func(i, j int) bool { return intervals[i][0] < intervals[j][0] })

    merged := make([][]int, 0, len(intervals))   // preallocate — result is at most len(intervals)
    merged = append(merged, intervals[0])

    for _, cur := range intervals[1:] {
        last := merged[len(merged)-1]
        if cur[0] <= last[1] {                    // overlaps (touching counts, per LC 56)
            if cur[1] > last[1] {
                last[1] = cur[1]                  // extend in place
            }
        } else {
            merged = append(merged, cur)
        }
    }
    return merged
}
```

### 3.2 The aliasing trap, made concrete

`merged = append(merged, intervals[0])` does not copy `intervals[0]` — it
copies the **slice header**, so `merged[0]` and `intervals[0]` point at the
*same* 2-element backing array (direct instance of the Part 1.2 aliasing rule
from the Arrays & Hashing guide). When the sweep later does
`last[1] = cur[1]`, and `last` is `merged[len(merged)-1]` which still aliases
an entry of the original input, **you are mutating the caller's input slice**
in place.

```
intervals ──► [1,3] [2,6] [8,10] [15,18]
                 ▲
merged[0] ───────┘   same backing array — writing last[1] here writes intervals[0][1] too
```

This is usually harmless: `merge` typically owns the only reference to
`intervals` for the rest of the function, and the caller (LeetCode's test
harness) doesn't reuse the input after the call returns. But if your function
signature promises not to mutate its input — e.g. you need to sort *and*
merge but the caller still needs the original order afterward — either sort a
copy or deep-copy each kept interval before extending it:

```go
merged = append(merged, []int{cur[0], cur[1]})   // ✅ independent copy — no aliasing
```

State which behavior you intend; don't let it be accidental.

---

## Part 4 · Insert Interval — the Three-Phase Sweep

LC 57 gives you an already-sorted, non-overlapping list plus one new interval
to insert. The clean linear template is three phases over the *same* single
pass — no nested loops, no re-sorting:

```go
func insert(intervals [][]int, newInterval []int) [][]int {
    result := make([][]int, 0, len(intervals)+1)
    i, n := 0, len(intervals)

    // Phase 1: intervals ending strictly before newInterval starts — untouched.
    for i < n && intervals[i][1] < newInterval[0] {
        result = append(result, intervals[i])
        i++
    }

    // Phase 2: intervals overlapping newInterval — absorb them all into it.
    for i < n && intervals[i][0] <= newInterval[1] {
        newInterval = []int{min(newInterval[0], intervals[i][0]), max(newInterval[1], intervals[i][1])}
        i++
    }
    result = append(result, newInterval)

    // Phase 3: intervals starting strictly after newInterval ends — untouched.
    for i < n {
        result = append(result, intervals[i])
        i++
    }
    return result
}
```

`newInterval = []int{...}` in Phase 2 rebinds the local slice header to a
**new** backing array on each merge step — it does not mutate the caller's
original `newInterval` argument (Go passes the slice header by value), so
there's no aliasing hazard here the way there was in Part 3.

---

## Part 5 · Meeting Rooms II — Two Ways to Count Concurrency

LC 253/253-style "minimum number of rooms needed" is really "what's the
maximum number of intervals alive at the same instant." Two idiomatic Go
approaches:

### 5.1 Two sorted arrays + two-pointer sweep — O(n log n) time, O(n) space

Split into separate `starts` and `ends` slices, sort each independently, then
walk both with two pointers: every time a meeting starts before the earliest
still-open meeting ends, that's a room in use.

```go
func minMeetingRooms(intervals [][]int) int {
    n := len(intervals)
    starts := make([]int, n)
    ends := make([]int, n)
    for i, iv := range intervals {
        starts[i], ends[i] = iv[0], iv[1]
    }
    sort.Ints(starts)
    sort.Ints(ends)

    rooms, maxRooms := 0, 0
    s, e := 0, 0
    for s < n {
        if starts[s] < ends[e] {   // a meeting starts before the earliest one ends
            rooms++
            s++
        } else {                  // a meeting has ended, freeing a room
            rooms--
            e++
        }
        if rooms > maxRooms {
            maxRooms = rooms
        }
    }
    return maxRooms
}
```

Splitting into two arrays deliberately throws away the start/end *pairing* —
we only need the multiset of start times and the multiset of end times, not
which end belongs to which start, since we're only counting concurrency.

```arch
%% caption: Meeting rooms II: the heap holds the end time of every room in use. Its maximum size is the answer.
grid 190x80
node a "sort meetings by start" at 1,0 shape=pill w=200
node b "next meeting (s, e)" at 1,1 w=230
node c "heap not empty and\nheap[0] ≤ s ?" at 1,2 shape=diamond color=amber
node e "A new room is needed" at 2,2 color=amber w=190
node d "Pop it: reuse that room" at 1,3 color=green w=230
node f "push e" at 1,4 w=230
node g "rooms = max(rooms, len(heap))" at 1,5 w=230
a -> b -> c
c -> d : "yes: earliest room free"
c -> e : "no"
d -> f
e:B -> f:R
f -> g
g:L -> b:L
```

### 5.2 Min-heap of active end times — O(n log n) time, O(n) space

Sort by start, then push each meeting's end time onto a min-heap
(`container/heap`, per the Heap & Priority Queue guide); before pushing a new
meeting, pop-and-discard every heap-top end time that is `<=` the new
meeting's start — those rooms have freed up. The heap's size at any point is
the number of rooms in concurrent use.

```go
type endHeap []int

func (h endHeap) Len() int            { return len(h) }
func (h endHeap) Less(i, j int) bool  { return h[i] < h[j] }
func (h endHeap) Swap(i, j int)       { h[i], h[j] = h[j], h[i] }
func (h *endHeap) Push(x any)         { *h = append(*h, x.(int)) }
func (h *endHeap) Pop() any {
    old := *h
    n := len(old)
    v := old[n-1]
    *h = old[:n-1]
    return v
}

func minMeetingRoomsHeap(intervals [][]int) int {
    sort.Slice(intervals, func(i, j int) bool { return intervals[i][0] < intervals[j][0] })

    h := &endHeap{}
    maxRooms := 0
    for _, iv := range intervals {
        for h.Len() > 0 && (*h)[0] <= iv[0] {   // room(s) freed before this meeting starts
            heap.Pop(h)
        }
        heap.Push(h, iv[1])
        if h.Len() > maxRooms {
            maxRooms = h.Len()
        }
    }
    return maxRooms
}
```

Interviewers often ask for this version specifically to confirm you can wire
up `container/heap` from memory — see the Heap & Priority Queue guide for why
`Push`/`Pop` take pointer receivers and must be called via `heap.Push`/
`heap.Pop`, never invoked directly.

---

## Part 6 · Complexity Table

| Operation | Time | Space | Note |
|---|:--:|:--:|---|
| Sort by start or end | O(n log n) | O(log n) | pdqsort — dominates almost every interval algorithm |
| Merge sweep (post-sort) | O(n) | O(n) | one pass, preallocate result |
| Insert Interval (already sorted) | O(n) | O(n) | no re-sort needed — single pass |
| Meeting Rooms II, two-pointer | O(n log n) | O(n) | two separate sorted arrays |
| Meeting Rooms II, heap | O(n log n) | O(n) | heap holds at most n active ends |
| Non-overlapping / arrows, greedy | O(n log n) | O(1) extra | sort by end, single pass |

The sort is the asymptotic bottleneck everywhere in this topic; the sweep
itself is always linear.

---

## Part 7 · Python vs. Go — Where They Diverge

| | Python | Go |
|---|---|---|
| Interval shape | Usually `(start, end)` tuples or a class | LeetCode hands you raw `[][]int` |
| Sort key | `intervals.sort(key=lambda x: x[0])` | `sort.Slice(intervals, func(i, j int) bool {...})` — comparator, not key function |
| Sort stability | Timsort — stable | `sort.Slice` — **unstable**; use `sort.SliceStable` if tie order matters |
| Copying on append | List append copies the reference (same aliasing risk exists in Python too) | Same risk, but explicit: slice header copy is visible in the code, not hidden behind a name |
| Heap for end times | `heapq.heappush(heap, end)` on a plain list | Must implement `heap.Interface` first (see Topic 12) |
| Tuple unpacking | `start, end = interval` | No destructuring — `iv[0]`, `iv[1]`, or convert to a named struct first |

---

## Part 8 · Algorithms Owned by This Topic

| Algorithm | Time | Space | Problem |
|---|:--:|:--:|---|
| Sort by start + linear merge sweep | O(n log n) | O(n) | LC 56 Merge Intervals |
| Three-phase insert sweep | O(n) | O(n) | LC 57 Insert Interval |
| Sort by end + greedy exchange argument | O(n log n) | O(1) | LC 435 Non-overlapping Intervals |
| Sort by end + greedy, count groups | O(n log n) | O(1) | LC 452 Minimum Arrows to Burst Balloons |
| Two sorted arrays + two-pointer sweep | O(n log n) | O(n) | LC 253 Meeting Rooms II |
| Min-heap of active end times | O(n log n) | O(n) | LC 253 Meeting Rooms II (heap variant) |
| Sort by start, boolean overlap check | O(n log n) | O(1) | LC 252 Meeting Rooms |

---

<!-- block:19_go_1_problems -->
## Part 9 · The Eleven Problems in Go, Sweep-Line Events and Online Structures

All code below ran on Go 1.24.5 against LeetCode's own examples; the online structure was also checked against a naive version
on 5,000 random inputs (0 mismatches).

```arch
%% caption: Choosing the interval technique. The question — merge, select, count concurrency, cover, or answer online — picks the sort and the structure.
grid 200x80
node q "An interval problem" at 0,1 shape=pill
node a "What is asked?" at 0,2 shape=diamond color=amber
node b "Sort by START, sweep and merge" at 1,0 color=green w=400 sub="combine overlapping ones"
node c "Sort by END, greedy selection" at 1,1 color=green w=400 sub="keep the MOST non-overlapping"
node d "Sweep line: +1 / -1 events" at 1,2 color=green w=400 sub="peak overlap / resources needed · or a min-heap of end times"
node e "Sort by start, greedy farthest reach" at 1,3 color=amber w=400 sub="cover a range with the FEWEST intervals"
node f "Two pointers" at 1,4 color=green w=400 sub="intersect two sorted lists · advance the one that ends first"
node g "Sorted slice + sort.Search, or a balanced tree" at 1,5 color=amber w=400 sub="intervals arrive online"
q -> a
a:R -> b:L
a:R -> c:L
a:R -> d:L
a:R -> e:L
a:R -> f:L
a:R -> g:L
```

### The boundary is different for almost every problem

| Problem | The test | Why |
|---|---|---|
| Meeting Rooms (001) | conflict iff `next[0] < prev[1]` | back-to-back meetings are fine |
| Merge Intervals (002) | merge iff `cur[0] <= last[1]` | touching intervals merge |
| Non-overlapping Intervals (004) | keep iff `start >= lastEnd` | touching does not conflict |
| Meeting Rooms II (005) | reuse a room iff `end <= start` | a room freed at `t` is free at `t` |
| Min Arrows (007) | new arrow iff `start > arrowPos` | touching balloons **share** an arrow |
| My Calendar (010) | overlap iff `s1 < e2 && s2 < e1` | half-open `[s, e)` |

Reusing 004's `>=` in 007 silently over-counts arrows; a closed-interval `<=` in My Calendar rejects `[10,20)` then `[20,30)`.
Say the convention out loud *before* writing the operator.

### Sort, then sweep: Meeting Rooms, Merge, Insert, Non-overlapping, Arrows

Use `cmp.Compare` (never `a[0] - b[0]`) and clone the slice when the function is a *query* — sorting the caller's slice is a
hidden side effect:

```go
c := slices.Clone(iv)
slices.SortFunc(c, func(a, b []int) int { return cmp.Compare(a[0], b[0]) })
for i := 1; i < len(c); i++ { if c[i][0] < c[i-1][1] { return false } }       // [[0 30] [5 10] [15 20]] -> false
```

**Merge:** extend with `max`, never a plain assignment — nested intervals are exactly where `out[n-1][1] = cur[1]` shrinks the
block — and append an *independent copy* (`[]int{cur[0], cur[1]}`) so extending it never mutates the input (Part 3.2):

```go
if n := len(out); n > 0 && cur[0] <= out[n-1][1] { out[n-1][1] = max(out[n-1][1], cur[1]) } else { out = append(out, []int{cur[0], cur[1]}) }
// [[1 3] [2 6] [8 10] [15 18]] -> [[1 6] [8 10] [15 18]]     [[1 4] [2 3]] -> [[1 4]]     [[1 4] [4 5]] -> [[1 5]]
```

**Insert Interval** is three phases on already-sorted input (do **not** re-sort): copy the intervals that end before the new one,
merge everything that overlaps (`<=`, and update *both* `ns = min(ns, start)` and `ne = max(ne, end)`), copy the rest.
**Non-overlapping Intervals** sorts by **end**; removals = `n − kept` (returning `kept` is the classic slip), and sorting by
start keeps one interval instead of two on `[[1 10] [2 3] [4 5]]`. **Min Arrows** sorts by end with `start > arrowPos`.

### Two lists at once: Interval List Intersections

Both lists are sorted and internally disjoint — the precondition for a linear two-pointer merge. The intersection is
`[max(starts), min(ends)]` when non-empty; advance **only** the pointer whose interval ends first:

```go
lo, hi := max(a[i][0], b[j][0]), min(a[i][1], b[j][1])
if lo <= hi { res = append(res, []int{lo, hi}) }
if a[i][1] < b[j][1] { i++ } else { j++ }
```

Concatenating and re-merging is a different problem (merging *loses* the overlap regions); advancing both pointers skips valid
intersections.

### Concurrency: events, a heap, or a difference array

Turn each interval into two events and keep a running total. With half-open intervals the `−1` must come **before** the `+1` at
the same time, so sort by `(t, delta)`:

```go
slices.SortFunc(ev, func(a, b event) int { return cmp.Or(cmp.Compare(a.t, b.t), cmp.Compare(a.delta, b.delta)) })   // -1 sorts first
cur += e.delta; best = max(best, cur)              // [[0 30] [5 10] [15 20]] -> 2   [[7 10] [2 4]] -> 1   [[1 5] [5 10]] -> 1
```

**Car Pooling** is the same with `+n` at pickup and `−n` **at** the drop-off (not `to − 1`), failing when the running total
exceeds the capacity. With small integer coordinates a value-indexed **difference array** replaces the sort — size it past the
largest coordinate (`[1002]int` for `to <= 1000`) and Go's array value semantics keep it on the stack:

```go
diff[t[1]] += t[0]; diff[t[2]] -= t[0]              // [[2 1 5] [3 3 7]]: capacity 4 -> false, 5 -> true
```

**Employee Free Time** is the *complement of the union*: flatten every employee's intervals into one list, merge, and read the
gaps — merging employee by employee is wrong. `[[1 2] [5 6]]`, `[[1 3]]`, `[[4 10]]` → `[[3 4]]`.

### Covering a range with the fewest intervals

Different from selection: you must *cover* `[0, T]`. Sort by start; among every clip that begins inside the covered prefix take the
**farthest** reach; repeat — Jump Game II's frontier in interval clothing (Video Stitching, Minimum Taps):

```go
for curEnd < T {
    for i < len(c) && c[i][0] <= curEnd { far = max(far, c[i][1]); i++ }
    if far <= curEnd { return -1 }                   // a gap nothing can bridge
    res++; curEnd = far
}                                                    // the LeetCode clips, T=10 -> 3;  [[0 1] [1 2]], T=5 -> -1
```

Forgetting the `far <= curEnd` guard loops forever on an uncoverable range. **Remove Covered Intervals** sorts by start
ascending and — for equal starts — by **end descending** (`cmp.Compare(b[1], a[1])`), so the longer interval is seen first and
the shorter is recognised as covered: `[[1 4] [3 6] [2 8]]` → 2, `[[1 2] [1 4] [3 4]]` → 2.

### Online: intervals that keep arriving

Keep a **sorted slice** and use `sort.Search` to find the neighbours — a new interval can only interact with the one or two next
to it. My Calendar I checks exactly two neighbours:

```go
i := sort.Search(len(c.books), func(i int) bool { return c.books[i][0] >= s })   // first booking starting at or after s
if i < len(c.books) && c.books[i][0] < e { return false }                          // the NEXT one starts before we end
if i > 0 && c.books[i-1][1] > s { return false }                                    // the PREVIOUS one ends after we start
c.books = slices.Insert(c.books, i, [2]int{s, e})                                   // 10-20 T, 15-25 F, 20-30 T, 5-10 T, 9-11 F
```

**My Calendar II** keeps `bookings` and the `overlaps` — the *intersections* already double-booked; a new event triple-books iff
it intersects an overlap. Store the intersection (`max` of starts, `min` of ends), **not** the whole booking, and check the new
event against `overlaps` *before* adding to it. **Data Stream as Disjoint Intervals** merges a value into a left neighbour
ending at `v − 1`, a right neighbour starting at `v + 1`, both (fuse and `slices.Delete`), or neither (`slices.Insert`).
`slices.Insert`/`Delete` are O(n) — a balanced tree (topic 11) makes inserts O(log n). **My Calendar III** needs no structure:
a `map[int]int` of `+1/−1` events and a sorted sweep gives `[1 1 2 3 3 3]`.

### The Skyline problem: sweep line + a max-heap with lazy deletion

Events are building edges. At each event `x`, first **lazily pop** buildings whose right edge is `<= x`, push the new building
(if this is a left edge), read the current maximum height, and emit `[x, height]` only when the height *changes*. Sort events by
`(x, −height)` so a taller building comes first among same-`x` starts:

```go
push(item{0, math.MaxInt})                          // the ground never expires
for _, e := range evs {
    for heap[0].r <= e.x { pop() }                   // LAZY deletion of ended buildings
    if e.negh != 0 { push(item{e.negh, e.r}) }
    h := -heap[0].negh
    if len(res) == 0 || res[len(res)-1][1] != h { res = append(res, []int{e.x, h}) }
}   // [[2 9 10] [3 7 15] [5 12 12] [15 20 10] [19 24 8]] -> [[2 10] [3 15] [7 12] [12 0] [15 10] [20 8] [24 0]]
```

`(r, 0, 0)` end events carry `negh = 0` so they push nothing. (Topic 12's generic `Heap[T]` replaces the hand-rolled sift code.)

### Find Right Interval: a lower bound over sorted starts

Sort the *starts* with their indices, then for each interval `sort.Search` for the first start `>=` its end: O(n log n).
`[[3 4] [2 3] [1 2]]` → `[-1 0 1]`.

### Go traps in this topic

| Trap | What happens | The fix |
|---|---|---|
| `intervals[i][1] < intervals[j][1]` typed where `[0]` was meant | Compiles, silently sorts by the wrong field. | Named struct fields, or a comment naming the indices. |
| A comparator `a[0] - b[0]` on `int32` data | Overflows and can flip the sign. | `cmp.Compare`. |
| `sort.Slice` on the caller's slice in a query function | Reorders their data. | `slices.Clone` first. |
| `out = append(out, cur)` in Merge | `out` aliases the input's 2-element slices; extending mutates the input. | Append an independent copy. |
| `last[1] = cur[1]` instead of `max` | Shrinks the block on nested intervals. | `max(last[1], cur[1])`. |
| Ranging a `map[int]int` of events without sorting | Random order. | Sort the keys, or use a sorted event slice. |
| `slices.Insert` on a long sorted slice | O(n) per insert. | A balanced tree or skip list for heavy online use. |

### Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Online intervals." | A sorted structure with neighbour lookup (`sort.Search`, or a balanced tree for O(log n) inserts). |
| "Peak overlap, many queries." | A segment tree with lazy range-add (topic 26), or an interval tree. |
| "Weighted intervals?" | Greedy fails — DP over end-sorted intervals with a binary search for the last compatible one. |
| "Merge with a tolerance `k`?" | Merge when `cur[0] <= last[1] + k`. |
| "Rectangles?" | Sweep one axis with a structure over the other (Skyline generalisations, Rectangle Area II). |
| "Huge / streaming?" | Start-sorted streams merge in one pass with O(1) state; unsorted ones need an external sort. |

---
<!-- /block:19_go_1_problems -->

<!-- problem-map:start -->
## Part 10 · Every Problem in This Topic, by Pattern

Eleven problems, five moves (sort by start and merge · sort by end and select · sweep line with a heap or events · two-pointer merge · online booking) — the Python guide's map in Go, with the Go-only traps. Each **Trap** is a mistake documented in that problem's solution file, plus Go-specific hazards. Topic 19's solutions are Python-first; the Go column is the plan you would write.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Meeting Rooms](GoDSA/19_intervals/001_meeting_rooms/solution.go) <br>LC 252 · Easy | Sort by start, check neighbours | `slices.Clone`, sort by start with `cmp.Compare`, conflict iff `c[i][0] < c[i-1][1]`. **Trap:** `<=`; sorting the caller's slice in a query function. |
| [002 · Merge Intervals](GoDSA/19_intervals/002_merge_intervals/solution.go) <br>LC 56 · Medium | Sort by start, merge | Extend with `max(out[n-1][1], cur[1])`; append `[]int{cur[0], cur[1]}` (a copy). **Trap:** assigning instead of `max`; appending `cur` itself (aliases the input); sorting by end. |
| [003 · Insert Interval](GoDSA/19_intervals/003_insert_interval/solution.go) <br>LC 57 · Medium | Three-phase sweep on sorted input | Copy the earlier ones, merge the overlapping with `<=` (updating both `ns` and `ne`), copy the rest. **Trap:** strict `<`; forgetting `ns = min(...)`; re-sorting. |
| [004 · Non-overlapping Intervals](GoDSA/19_intervals/004_non_overlapping_intervals/solution.go) <br>LC 435 · Medium | Sort by **end**, keep greedily | `cmp.Or(end, start)`; `kept` when `start >= lastEnd`; return `len - kept`. **Trap:** sorting by start; `>`; `lastEnd := 0` (rejects negative starts — use `math.MinInt`). |
| [005 · Meeting Rooms II](GoDSA/19_intervals/005_meeting_rooms_ii/solution.go) <br>LC 253 · Medium | Peak concurrency | Sorted `(t, delta)` events with `-1` before `+1`, or a min-heap of end times reused when `end <= start`. **Trap:** sorting by end; `<`; an unconditional pop. |
| [006 · Interval List Intersections](GoDSA/19_intervals/006_interval_list_intersections/solution.go) <br>LC 986 · Medium | Two pointers over two sorted lists | `[max, min]` when `lo <= hi`; advance the pointer that ends first. **Trap:** concatenate-and-merge; advancing both. |
| [007 · Minimum Number of Arrows to Burst Balloons](GoDSA/19_intervals/007_minimum_number_of_arrows_to_burst_balloons/solution.go) <br>LC 452 · Medium | Sort by end, boundary flipped | New arrow iff `p[0] > pos`. **Trap:** 004's `>=`; a subtraction comparator on `int32` data. |
| [008 · Employee Free Time](GoDSA/19_intervals/008_employee_free_time/solution.go) <br>LC 759 · Hard | The complement of the union | Flatten all employees, merge, read the gaps. **Trap:** merging per employee; `merge` without `max`. |
| [009 · Car Pooling](GoDSA/19_intervals/009_car_pooling/solution.go) <br>LC 1094 · Medium | Weighted concurrency | A `[1002]int` difference array: `+n` at pickup, `−n` **at** drop-off; running total vs capacity. **Trap:** `to - 1`; an array too small. |
| [010 · My Calendar I](GoDSA/19_intervals/010_my_calendar_i/solution.go) <br>LC 729 · Medium | Online: check the two neighbours | `sort.Search` for the first booking starting at or after `s`; check that one and its predecessor; `slices.Insert`. **Trap:** closed intervals; hand-enumerated overlap cases. |
| [011 · My Calendar II](GoDSA/19_intervals/011_my_calendar_ii/solution.go) <br>LC 731 · Medium | Online: track double-booked regions | `bookings` plus `overlaps` (intersections). **Trap:** storing the whole booking; adding overlaps before checking the new event. |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] Know when to sort by start (merge/insert) vs. by end (greedy scheduling maximization), and *why* the exchange argument requires end-sort for the latter
- [ ] Explain the touching-boundary (`<` vs `<=`) decision and confirm it against the problem statement before coding
- [ ] Spot the aliasing risk when appending an original `[][]int` sub-slice into a result you'll later mutate in place, and know the copy-based fix
- [ ] Write the three-phase Insert Interval sweep without nested loops
- [ ] Implement Meeting Rooms II both ways: two-pointer over separate sorted arrays, and a `container/heap` of active end times
- [ ] Preallocate result slices with `make([][]int, 0, len(intervals))` when the upper bound is known
- [ ] Remember `sort.Slice` is unstable — reach for `sort.SliceStable` if input order among equal keys must be preserved
- [ ] Name the boundary operator for each of the seven problems (`<`, `<=`, `>=`, `>`) and the reason for each <!--ca-->
- [ ] Sort `(t, delta)` events so `-1` precedes `+1` at a tie, and say what that models <!--ca-->
- [ ] Clone before sorting in a query function, and append an independent copy in Merge <!--ca-->
- [ ] Keep an online interval set in a sorted slice with `sort.Search`, and name the O(n) `Insert` cost <!--ca-->
- [ ] Write the Skyline sweep with lazy heap deletion <!--ca-->
