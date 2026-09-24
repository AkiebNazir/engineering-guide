# Topic 19 · Intervals — the deep-dive guide

Intervals problems all reduce to a handful of decisions: **how do you represent
an interval, does "touching" count as "overlapping," which key do you sort by,
and do you need a running aggregate (a counter) or a running boundary set (a
heap)?** Get those four decisions right and every problem in this topic falls
out of the same handful of templates. Get the sort key wrong and the code
still "looks right" and still fails silently on specific inputs — this is the
single most common interval bug in interviews.

--------------------------------------------------------------------------------
## 1 · Representation and the touching-vs-overlapping question

An interval is almost always `[start, end]`, a 2-element list/tuple, nearly
always treated as a **closed interval on both ends** unless the problem states
otherwise (LeetCode's interval problems are closed-closed: `end` is inclusive
scheduling-wise, e.g. a meeting `[0, 30]` occupies time 0 through 30).

**The classic trap: do `[1, 2]` and `[2, 3]` overlap?**

The honest answer is: **it depends on the problem, and you must ask.**

- **Merge Intervals (LC 56)**: `[1,2]` and `[2,3]` DO merge into `[1,3]`.
  Two intervals that only touch at a single point are treated as overlapping
  for merge purposes — a meeting ending at 2 and one starting at 2 are
  considered back-to-back and get merged into one block. The merge condition
  is `next.start <= current.end` (non-strict `<=`).
- **Meeting Rooms (LC 252)**: `[1,2]` and `[2,3]` do **NOT** conflict. A
  meeting can end at 2 and the next can start at 2 — same room, no overlap
  in the "can one person attend both" sense. The conflict test after sorting
  by start is `intervals[i][0] < intervals[i-1][1]` (strict `<`).
- **Non-overlapping Intervals (LC 435) / Minimum Arrows (LC 452)**: here
  touching does NOT count as overlapping either — `[1,2]` and `[2,3]` can
  both be kept (arrows: a single arrow at x=2 bursts both, so they're
  "non-overlapping" for the removal count, i.e. `end < next.start`... but
  452 explicitly makes touching balloons poppable by one arrow, so the
  *skip* condition is `intervals[i][0] > current_end`, strict `>`).

There's no universal rule. **In an interview, say the boundary sentence out
loud before you write the comparison**: "I'm treating `[a,b]` and `[b,c]` as
overlapping for merge, but not for room-conflict, because a meeting can end
exactly when the next starts." Then the `<` vs `<=` in your code is a
deliberate choice, not a coin flip you'll get half right.

See each solution's EDGE CASES section for the exact operator used and why.

--------------------------------------------------------------------------------
## 2 · Sort-by-start vs sort-by-end — these are NOT interchangeable

This is the deepest idea in the topic. Two different greedy problems need two
different sort keys, and using the wrong one produces code that passes a
handful of test cases and then fails silently.

```arch
%% caption: Which sort order, and which technique, an interval problem needs.
grid 210x80
node q "Interval problem" at 0,0 shape=pill
node a "Merge, union, or find gaps?" at 0,1 shape=diamond color=amber
node s "Sort by START" at 1,1 color=green w=220 sub="and extend the current end"
node b "Keep the MOST non-overlapping?\n(or remove the fewest)" at 0,2 shape=diamond color=amber
node e "Sort by END" at 1,2 color=green w=220 sub="earliest finish first"
node c "How many at the same time?" at 0,3 shape=diamond color=amber
node h "Sweep line + min-heap" at 1,3 color=green w=220 sub="of end times"
node t "Two sorted lists: two pointers" at 0,4 color=green w=220
q -> a
a -> s : "yes"
a -> b : "no"
b -> e : "yes"
b -> c : "no"
c -> h : "yes"
c -> t : "no"
```


### 2a · Sort by START — for merging / union / "what's covered"

If the question is "combine everything into contiguous blocks" (Merge
Intervals, Insert Interval, Employee Free Time's busy union, Meeting Rooms'
"is there any conflict"), you need to walk intervals **in the order they
begin**, because merging is a left-to-right sweep: you can only decide "does
this interval extend the current block?" if you've already seen every
interval that could have started before it. Sorting by `end` would let a
later-starting-but-earlier-ending interval slip in first, and you'd merge
the wrong pair or miss a merge entirely.

```arch
%% caption: Merge intervals: after sorting by start, an interval either extends the last merged one or starts a new one.
grid 140x80
node a "sort by start" at 1,0 shape=pill
node b "merged = [first interval]" at 1,1 w=210
node c "next interval (s, e)" at 1,2 w=210
node d "s ≤\nmerged[-1].end ?" at 1,3 shape=diamond color=amber
node e "Extend the last one" at 0,4 color=amber w=230 sub="end = max(merged[-1].end, e)"
node f "Start a new one" at 2,4 w=200 sub="append (s, e) as a new interval"
a -> b -> c -> d
d:L -> e:T : "yes: overlap"
d:R -> f:T : "no"
e:L -> c:L
f:R -> c:R
```


```
merged = [sorted[0]]
for iv in sorted[1:]:
    if iv.start <= merged[-1].end:   # overlaps (or touches) the last block
        merged[-1].end = max(merged[-1].end, iv.end)
    else:
        merged.append(iv)
```

### 2b · Sort by END — for "max intervals you can keep" / greedy selection

If the question is "select the maximum number of intervals such that none
conflict" (equivalently: "remove the minimum number to make the rest
non-overlapping" — LC 435, or "minimum arrows to burst all balloons" — LC
452), you sort by **end**, not start. This is the *activity selection*
problem, and the greedy proof is the reason the sort key flips:

**Why end, not start:** greedily keep the interval that frees up the
timeline soonest. Among all intervals that don't conflict with what you've
already kept, the one that ends earliest leaves the most room for everything
after it — provably at least as much room as keeping any other candidate,
by an exchange argument (swapping in the earliest-ending interval for any
other choice can never make the remaining schedule worse). Sorting by
*start* and greedily keeping the first non-conflicting interval you meet
does NOT give this guarantee — a long early-starting interval can block out
several short ones that would have fit.

Concrete counter-example proving start-sort is wrong for this variant:
`[[1, 10], [2, 3], [4, 5]]`. Sorted by start, the first kept interval is
`[1,10]` — it conflicts with both others, so you can only keep 1 interval.
Sorted by end: `[2,3], [4,5], [1,10]` — keep `[2,3]`, keep `[4,5]` (no
conflict), reject `[1,10]` (conflicts with both) — you keep 2. The correct
answer is 2. Start-sort silently under-counts.

```
sorted by end
kept_end = -inf
count = 0
for iv in sorted:
    if iv.start >= kept_end:      # no conflict with the last KEPT interval
        count += 1
        kept_end = iv.end
```

**Rule of thumb:** *merging/union* → sort by start. *Max non-conflicting
subset / min removals* → sort by end. If you catch yourself sorting by start
for a "how many can I keep" problem, stop and re-derive — it's the most
common interval mistake there is.

--------------------------------------------------------------------------------
## 3 · Sweep-line + min-heap — "how many resources are needed concurrently"

Meeting Rooms II (LC 253) and Car Pooling (LC 1094) ask a different question
than §2: not "can everything fit in ONE resource" but "what's the PEAK
number of resources needed at any instant?" This needs to track, at every
point in time, how many intervals are currently "open."

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


**Pattern**: sort intervals by start. Walk them in that order, and maintain a
min-heap of the END times of every interval currently "in progress" (a room
occupied, a car occupied). For each new interval:

1. Pop every end time from the heap that is `<=` the new interval's start
   (those rooms/seats have freed up by the time this one begins — reuse
   them).
2. Push the new interval's end time onto the heap.
3. The heap size *right now* is the number of resources concurrently in use;
   track the running max across the whole sweep — that's the answer.

The heap replaces a plain counter because "free up a room" isn't a simple
decrement in time order — you need to know *which* end time is next to
expire, and a min-heap gives you the earliest-expiring room in O(log n)
without re-scanning.

An equivalent, often faster in practice, formulation: build two sorted
arrays, `starts` and `ends`. Two-pointer walk: an interval starting before
the earliest still-open interval ends means "need one more room" (increment
a counter, advance the start pointer); otherwise a room frees up (decrement,
advance the end pointer). This avoids the heap entirely because you only
ever care about the *single* earliest end time, which sorting already gives
you directly — no need to re-extract-min from a heap when a sorted array
serves the same purpose. See 005's solution file for both, measured.

**Car Pooling (extra 009)** generalizes the "peak concurrent count" sweep
to a *weighted* version — each interval doesn't count as 1, it counts as
`numPassengers`. The min-heap-of-end-times approach still works, but a
**difference array over pickup/dropoff events** (`diff[start] += passengers;
diff[end] -= passengers`, then a prefix sum) is simpler and faster when the
coordinate range is small and bounded, trading O(n log n) heap operations
for an O(n + V) counting sort-like sweep. Knowing when the diff-array trick
applies (bounded, small integer coordinates) versus when a heap is required
(coordinates arbitrary/large, or you need to know *which* resource is free,
not just the count) is itself an interviewer follow-up.

--------------------------------------------------------------------------------
## 4 · Two-pointer merge across two independent sorted interval lists

Interval List Intersections (LC 986) and the busy-union half of Employee
Free Time (LC 759) both start from **two (or more) already-sorted-by-start,
internally-non-overlapping** interval lists and need to combine them — not
by concatenating and re-sorting (that throws away the O(n) structure you
already have), but by a linear two-pointer walk, exactly like the merge step
of merge sort:

```
i = j = 0
while i < len(A) and j < len(B):
    lo = max(A[i].start, B[j].start)
    hi = min(A[i].end,   B[j].end)
    if lo <= hi:                       # they overlap — emit the intersection
        result.append([lo, hi])
    # advance whichever interval ends first — it cannot intersect anything
    # further along in the OTHER list, since both lists are sorted by start
    if A[i].end < B[j].end:
        i += 1
    else:
        j += 1
```

The key invariant that makes the "advance the earlier-ending pointer" rule
safe: since both lists are individually sorted and non-overlapping, once
`A[i]` ends before `B[j]` does, `A[i]` cannot possibly intersect `B[j+1]`,
`B[j+2]`, ... either (they all start even later than `B[j]`). So it's safe
to retire `A[i]` and never look at it again — this is exactly why the merge
step of merge sort is O(n) and not O(n²).

**Employee Free Time** extends this to *k* lists (one per employee):
flatten all employees' intervals, sort by start (§2a's merge machinery),
merge into the union of all busy time, then the free time is simply the
**gaps between consecutive merged intervals** — `merged[i].end` to
`merged[i+1].start` wherever that gap is positive. This is the "complement
of a union" pattern: solve the union first with the standard sort-by-start
merge, then read the answer off the *gaps*, not the merged blocks
themselves.

--------------------------------------------------------------------------------
## 5 · Decision table

| Question shape | Sort key | Data structure | Problems here |
|---|---|---|---|
| "Does anything conflict at all?" | start | none (single pass) | 001 Meeting Rooms |
| "Combine everything into contiguous blocks" | start | none (single pass, extend last block) | 002 Merge, 003 Insert |
| "Max keepable / min removals to de-conflict" | **end** | none (track last kept end) | 004 Non-overlapping, 007 Min Arrows |
| "Peak concurrent resources needed" | start (+ separately sorted ends) | min-heap of end times, or two sorted arrays | 005 Meeting Rooms II, 009 Car Pooling |
| "Overlap between two independent lists" | both pre-sorted by start | two-pointer merge walk | 006 Interval List Intersections |
| "Union across k lists, then find gaps" | start (after flattening) | merge, then read complement | 008 Employee Free Time |

--------------------------------------------------------------------------------
## 6 · General edge cases across the whole topic

- **Empty input** — `[]` intervals: most answers degenerate to 0 rooms / 0
  merges / no intersections. Always the first test.
- **Single interval** — trivially no conflicts, nothing to merge, nothing to
  remove.
- **Fully nested intervals** — `[1, 10]` and `[2, 3]`: the merge must extend
  by `max(end, iv.end)`, NOT just overwrite with `iv.end` — a naive
  `merged[-1].end = iv.end` silently *shrinks* the block when the nested
  interval ends before the outer one, corrupting the merge.
- **Touching endpoints** — see §1. Get the operator (`<` vs `<=`) right on
  purpose for each problem's semantics.
- **Already-sorted input assumed but not guaranteed** — Interval List
  Intersections and Employee Free Time both require pre-sorted, mutually
  non-overlapping lists per the problem's constraints; if that guarantee
  didn't hold, the two-pointer / merge logic would silently produce wrong
  results without erroring.
- **Unsorted input in general** — always sort explicitly rather than assume;
  LeetCode intervals problems frequently give intervals in arbitrary order
  and this is the #1 cause of a "works on the example, fails on the hidden
  test" submission.

--------------------------------------------------------------------------------
## 7 · Related non-interval patterns this topic borrows from

- The min-heap sweep in §3 is the same "lazy deletion via heap-of-expirations"
  idea as Topic 12's task-scheduling problems.
- The two-pointer merge in §4 is literally the merge step of merge sort
  (Topic 22, when written).
- The greedy exchange-argument proof in §2b is the same proof style used for
  Topic 18's greedy problems (e.g. Jump Game II, Gas Station) — sort/greedy
  correctness always rests on "swapping in my choice can't make things
  worse," and it's worth being able to say that sentence out loud in an
  interview, not just cite "greedy works here."

---

## 8 · Added Problems (010–011) · My Calendar I & II — Online Interval Booking

Added 16 Sep 2026 from the Google prep plan. The rest of this topic is BATCH (all intervals known up
front, sort once). These are ONLINE: intervals arrive one at a time and each must be answered.

**The overlap test to memorize (half-open `[s, e)`):** `s1 < e2 and s2 < e1`. It covers every
arrangement and correctly lets `[10,20)` and `[20,30)` coexist. The closed version (`<=`) rejects them.

- **010 My Calendar I (no double booking).** Booked intervals are disjoint, so keep them sorted and
  check only the two neighbors of the insertion point (`bisect_right` on starts). Measured at 20,000
  random bookings: linear scan ~2,000 ms, sorted list + bisect ~29 ms. A plain BST was faster still on
  random input (~12 ms) but degrades to depth 1,000 on 1,000 sorted bookings.
- **011 My Calendar II (no triple booking).** Keep `bookings` and `overlaps` (the double-booked
  regions). Reject if the new event touches an overlap; otherwise record its INTERSECTIONS with
  bookings. Storing the union instead of the intersection rejects valid events. The sweep-line over a
  difference map generalizes to "at most K" (and to My Calendar III).

- [ ] I can write the half-open overlap test and the two-neighbor check from memory.
- [ ] I can explain overlaps-list vs sweep-line for "at most K bookings".

<!-- block:19_py_1_beyond -->
## 9 · Sweep-Line Events, Interval Covering and Online Interval Structures

The guide covers the three sorts (start, end, sweep-with-heap) and two-list merging. These are the variations that use the
same ideas with a different data structure. Every snippet was run against LeetCode's own examples; the online structure was
also checked against a brute-force version on 5,000 random inputs (0 mismatches).

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
node g "Sorted list + bisect, or a balanced tree" at 1,5 color=amber w=400 sub="intervals arrive online"
q -> a
a:R -> b:L
a:R -> c:L
a:R -> d:L
a:R -> e:L
a:R -> f:L
a:R -> g:L
```

### 9.1 Sweep line with events: concurrency without a heap

Turn every interval into two **events**, `+1` at its start and `−1` at its end, sort them, and keep a running total. The
peak of the running total is the maximum overlap — Meeting Rooms II, Car Pooling and My Calendar III are all this:

```python
ev = sorted([(s, 1) for s, e in intervals] + [(e, -1) for s, e in intervals])
cur = best = 0
for _, d in ev: cur += d; best = max(best, cur)
# [[0,30],[5,10],[15,20]] -> 2     [[7,10],[2,4]] -> 1     [[1,5],[5,10]] -> 1
```

The tie-break is the whole edge case: with half-open intervals `[s, e)`, an interval that *ends* at `t` and one that *starts*
at `t` do **not** overlap, so the `−1` must be processed **before** the `+1` at the same timestamp. Tuples sort `-1` before
`+1`, which does it for free; write `(t, delta)` and it works. For **Car Pooling** the delta is the passenger count
(`+n` at pickup, `−n` at drop-off, applied *at* `to`, not `to − 1`), and you fail the moment the running total exceeds the
capacity. `[[2,1,5],[3,3,7]]` → capacity 4 fails, capacity 5 passes. When the coordinates are small integers a **difference
array** replaces the sort (topic 04).

### 9.2 Covering a range with the fewest intervals (greedy)

Different from selection: here you must *cover* `[0, T]`. Sort by start; among all clips that begin within the part already
covered, pick the one that reaches **farthest**; repeat. This is Jump Game II's frontier in interval clothing (Video Stitching,
Minimum Number of Taps to Water a Garden):

```python
clips.sort(); res = cur_end = far = i = 0
while cur_end < T:
    while i < len(clips) and clips[i][0] <= cur_end:           # every clip that starts inside the covered prefix
        far = max(far, clips[i][1]); i += 1
    if far <= cur_end: return -1                                # a gap nothing can bridge
    res += 1; cur_end = far
return res      # ... , T=10 -> 3      [[0,1],[1,2]], T=5 -> -1
```

The `far <= cur_end` check is the failure detector; forgetting it loops forever on an uncoverable range.

### 9.3 Which intervals are covered? Sort by start, then by end **descending**

To drop intervals contained in another (Remove Covered Intervals), sort by start ascending and — for equal starts — by
**end descending**, so the longer interval is seen first and the shorter one is recognised as covered:

```python
intervals.sort(key=lambda x: (x[0], -x[1]))
kept, far = 0, 0
for s, e in intervals:
    if e > far: kept += 1; far = e          # an interval that ends beyond everything so far is not covered
```

`[[1,4],[3,6],[2,8]]` → 2, `[[1,4],[2,3]]` → 1, `[[1,2],[1,4],[3,4]]` → 2. Sorting equal starts *ascending* by end mis-classifies `[1,2]` and `[1,4]`.

### 9.4 Online: intervals that keep arriving

When intervals arrive one at a time (My Calendar, Data Stream as Disjoint Intervals), keep a **sorted list** and use `bisect`
to find the neighbours — an insertion can only interact with the one or two intervals next to it. **Data Stream as Disjoint
Intervals** merges a new number `v` into a left neighbour ending at `v − 1`, a right neighbour starting at `v + 1`, both, or
neither:

```python
i = bisect_left(self.iv, [v, v])
if i > 0 and self.iv[i-1][1] >= v - 1:  ...extend the left neighbour to cover v, then fuse with the right one if they now touch
elif i < len(self.iv) and self.iv[i][0] <= v + 1: ...extend the right neighbour leftwards
else: self.iv.insert(i, [v, v])
```

Adding `1, 3, 7, 2, 6` yields `[[1,3],[6,7]]`. The search is O(log n) but a Python `list.insert` is O(n); a balanced tree or
`sortedcontainers.SortedList` gives O(log n) throughout (topic 11). **My Calendar III** (how many bookings overlap at most?)
needs no structure at all: a dictionary of `+1`/`−1` events and a sorted sweep gives `[1, 1, 2, 3, 3, 3]` on the LeetCode
sequence (O(n log n) per query; a segment tree makes it O(log n), topic 26).

### 9.5 The Skyline problem: sweep line + a max-heap with lazy deletion

Events are building edges: at a left edge push `(−height, right)`; at a right edge nothing is pushed but expired buildings
must leave. At each event x, first **lazily pop** buildings whose right edge is `<= x`, then read the current maximum
height, and emit `[x, height]` **only when the height changes**:

```python
events = sorted([(l, -h, r) for l, r, h in buildings] + [(r, 0, 0) for _, r, _ in buildings])
heap = [(0, inf)]                                              # the ground never expires
for x, negh, r in events:
    while heap[0][1] <= x: heappop(heap)                        # LAZY deletion of ended buildings
    if negh: heappush(heap, (negh, r))
    h = -heap[0][0]
    if not res or res[-1][1] != h: res.append([x, h])
# [[2,9,10],[3,7,15],[5,12,12],[15,20,10],[19,24,8]] -> [[2,10],[3,15],[7,12],[12,0],[15,10],[20,8],[24,0]]
```

Sorting `-h` puts a taller building first among same-x starts (so a shorter one never emits a spurious point), and the `(r, 0,
0)` end events carry `negh = 0` so they push nothing. This is the canonical *hard* interval problem: every idea above,
plus a heap.

### 9.6 Binary search over intervals (Find Right Interval)

"For each interval, the one that starts at or after my end, as early as possible": sort the *starts*, then `bisect_left` on each
end — O(n log n). `[[3,4],[2,3],[1,2]]` → `[-1, 0, 1]`. Recognising that "smallest start `>=` x" is a lower bound is the entire
problem.

### 9.7 Boundary checklist (where nearly every interval bug lives)

| Question | Decide up front |
|---|---|
| Closed `[s, e]` or half-open `[s, e)`? | Touching intervals overlap iff closed. State the convention before writing a comparison. |
| `<` or `<=`? | Meeting Rooms `<`; Non-overlapping keep `>=`; Arrows new-arrow `>` — each problem has its own answer (the solution files show all three). |
| Zero-length intervals (`s == e`)? | Under half-open they are empty and overlap nothing; check the constraints. |
| Sorted input? | Insert Interval and List Intersections *guarantee* it — do not throw it away by re-sorting. |
| Mutating the caller's list? | `sorted(...)` versus `.sort()` in a query function. |
| `merged[-1][1] = end` versus `max(...)`? | Nested intervals: only `max` is correct. |

### 9.8 Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Intervals arrive online." | A sorted structure with neighbour lookup (`bisect`, or a balanced tree for O(log n) inserts). |
| "Peak overlap, but online / very many queries?" | A segment tree with lazy range-add (topic 26), or an interval tree. |
| "Weighted intervals — maximise total weight." | Greedy fails; DP over end-sorted intervals with a binary search for the last compatible one. |
| "Merge with a tolerance (gap `≤ k`)?" | Merge when `next.start <= last.end + k`. |
| "Multi-dimensional (rectangles)?" | Sweep one axis with a structure over the other (Rectangle Area II, Skyline generalisations). |
| "Huge inputs, streaming?" | Sorted-by-start streams merge in one pass with O(1) state; unsorted ones need an external sort. |

---
<!-- /block:19_py_1_beyond -->

<!-- problem-map:start -->
## 10 · Every Problem in This Topic, by Pattern

Eleven problems, five moves (sort by start and merge · sort by end and select · sweep line with a heap or events · two-pointer merge · online booking). Each **Trap** is a mistake documented in that problem's solution file — the boundary (`<` vs `<=`) is different for almost every problem.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Meeting Rooms](PyDSA/19_intervals/001_meeting_rooms_solution.py) <br>LC 252 · Easy | Sort by start, check neighbours | After sorting, a conflict can only appear between *adjacent* meetings: `next.start < prev.end`. **Trap:** `<=` (rejects back-to-back meetings); `.sort()` mutating the caller's list in a query function. |
| [002 · Merge Intervals](PyDSA/19_intervals/002_merge_intervals_solution.py) <br>LC 56 · Medium | Sort by start, merge | Extend the last block when the next interval starts at or before its end: `merged[-1][1] = max(merged[-1][1], end)`. **Trap:** assigning `end` instead of `max` (breaks only on nested inputs); sorting by end; strict `<` (touching intervals stay apart). |
| [003 · Insert Interval](PyDSA/19_intervals/003_insert_interval_solution.py) <br>LC 57 · Medium | Three-phase sweep on sorted input | Copy the intervals ending before the new one, merge everything that overlaps (`<=`), copy the rest — the input is already sorted, so do not re-sort. **Trap:** strict `<` in phase 2; updating only `ne` and forgetting `ns = min(ns, start)`. |
| [004 · Non-overlapping Intervals](PyDSA/19_intervals/004_non_overlapping_intervals_solution.py) <br>LC 435 · Medium | Sort by **end**, keep greedily | Removals = `n − kept`; keep an interval when `start >= last_end` (touching does not conflict). **Trap:** sorting by start (keeps 1 on `[[1,10],[2,3],[4,5]]`, not 2); `>` instead of `>=`; returning `kept` instead of `n − kept`. |
| [005 · Meeting Rooms II](PyDSA/19_intervals/005_meeting_rooms_ii_solution.py) <br>LC 253 · Medium | Peak concurrency | The peak number of simultaneous meetings *is* the number of rooms: sort by start, keep a min-heap of end times, reuse a room when `heap[0] <= start`. **Trap:** sorting by end; `<` instead of `<=`; popping unconditionally. |
| [006 · Interval List Intersections](PyDSA/19_intervals/006_interval_list_intersections_solution.py) <br>LC 986 · Medium | Two pointers over two sorted lists | The intersection is `[max(starts), min(ends)]` when non-empty; advance only the pointer whose interval ends first. **Trap:** concatenating and re-merging (a different problem — merging loses the overlap regions); advancing both pointers. |
| [007 · Minimum Number of Arrows to Burst Balloons](PyDSA/19_intervals/007_minimum_number_of_arrows_to_burst_balloons_solution.py) <br>LC 452 · Medium | Sort by end, with the boundary flipped | One arrow per group of mutually overlapping balloons: a new arrow when `start > arrow_pos` (touching balloons *share* an arrow). **Trap:** reusing 004's `>=`, which over-counts arrows on touching balloons. |
| [008 · Employee Free Time](PyDSA/19_intervals/008_employee_free_time_solution.py) <br>LC 759 · Hard | The complement of the union | Free time is the gaps in the *union* of everyone's busy time: flatten across employees, sort, merge, read the gaps. **Trap:** merging employee by employee instead of one flat start-sorted list; `merged[-1][1] = end` without `max`. |
| [009 · Car Pooling](PyDSA/19_intervals/009_car_pooling_solution.py) <br>LC 1094 · Medium | Weighted concurrency | Room-count's sweep, but each trip occupies `passengers` seats: `+n` at pickup, `−n` **at** drop-off (not `to − 1`); fail when the running total exceeds the capacity. **Trap:** decrementing at `end − 1`; a difference array sized below the maximum `to`. |
| [010 · My Calendar I](PyDSA/19_intervals/010_my_calendar_i_solution.py) <br>LC 729 · Medium | Online: check the two neighbours | Half-open intervals overlap iff `s1 < e2 and s2 < e1`; keep bookings sorted so a new event can only collide with its neighbours. **Trap:** closed intervals (rejects `[10,20)` then `[20,30)`); enumerating overlap cases by hand and missing one. |
| [011 · My Calendar II](PyDSA/19_intervals/011_my_calendar_ii_solution.py) <br>LC 731 · Medium | Online: track the double-booked regions | Keep `bookings` and the `overlaps` (already double-booked regions); a new event triple-books iff it intersects an overlap. **Trap:** storing the whole booking in `overlaps` instead of the *intersection*; adding overlaps before checking the new event against them. |

---
<!-- problem-map:end -->


## Checklist Before Leaving This Topic <!--ca-->

- [ ] Count concurrency with `+1`/`−1` events and say why ends must sort before starts at a tie <!--ca-->
- [ ] Cover a range with the fewest intervals using a farthest-reach frontier, and detect an uncoverable gap <!--ca-->
- [ ] Sort by start ascending, end **descending** to remove covered intervals <!--ca-->
- [ ] Keep an online interval set in a sorted list with `bisect`, and name the O(n) insert cost <!--ca-->
- [ ] State the closed/half-open convention and the `<` vs `<=` choice *before* writing the comparison <!--ca-->
