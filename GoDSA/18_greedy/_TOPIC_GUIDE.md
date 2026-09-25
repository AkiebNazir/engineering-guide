# Topic 18 · Greedy — Go Deep Dive

> Greedy algorithms are 10% proof and 90% "sort correctly, then make one pass."
> The proof (why the local choice is globally optimal) is language-agnostic —
> but the implementation lives or dies on how you sort, how you break ties, and
> whether your single pass is actually one pass or an accidental O(n²). Go's
> sort primitives and value-vs-pointer semantics are where these problems are
> won or lost.

---

## Part 1 · Why "Sort, Then Scan" Dominates This Topic

Almost every greedy problem reduces to: impose an order that exposes the
locally-optimal choice, then walk it once making that choice. In Go that means
`sort.Slice` / `sort.SliceStable` / `slices.SortFunc` (Topic 1, Part 1.6) is
the single most-used primitive in this entire topic — more than any loop
construct.

```go
type interval struct{ start, end int }

sort.Slice(iv, func(i, j int) bool { return iv[i].start < iv[j].start })
```

### 1.1 Instability is not just a Topic-1 footnote here — it can leak into your proof

`sort.Slice` is **not stable**. For most greedy problems this is harmless
because the greedy argument only depends on the *sorted order of the primary
key*, and any permutation of equal-key elements is an equally valid optimal
choice. But there is a real failure mode: a greedy proof that implicitly
assumes a specific tie-break (e.g. "among meetings starting at the same time,
process the one that ends earliest first") will silently produce a *different
but still-optimal* answer on one run and a *wrong* answer if your
tie-break assumption doesn't actually hold under an unstable reordering.

```go
// ⚠️ If two intervals have the same start, does the algorithm require a
// specific tie-break, or does any order work? Answer this BEFORE coding,
// not after your test fails on one specific input ordering.
sort.Slice(iv, func(i, j int) bool {
    if iv[i].start != iv[j].start {
        return iv[i].start < iv[j].start
    }
    return iv[i].end < iv[j].end     // explicit secondary key — don't rely on stability
})
```

> ✅ **The fix is never "use `sort.SliceStable`."** If your algorithm's
> correctness depends on tie order, encode that order as an explicit secondary
> sort key. Relying on stability to encode a tie-break is fragile — the next
> person who swaps in `slices.SortFunc` (which has no stability guarantee
> either) breaks your program silently. Reach for `sort.SliceStable` only when
> preserving *original input order* among equal keys is a stated requirement
> (e.g. "return results in the order jobs were submitted"), never as a
> substitute for a real secondary key.

### 1.2 The multi-key comparator shape

This exact shape recurs across nearly every interval/scheduling greedy problem
in Go — memorize it once:

```go
sort.Slice(items, func(i, j int) bool {
    if items[i].end != items[j].end {
        return items[i].end < items[j].end   // primary key
    }
    return items[i].start < items[j].start   // tie-break
})
```

`slices.SortFunc` (Go 1.21+) is the generic, `strcmp`-style modern equivalent
— returns an `int`, not a `bool`, and composes multi-key comparisons via
`cmp.Compare` and `cmp.Or` (Go 1.22+):

```go
slices.SortFunc(items, func(a, b item) int {
    return cmp.Or(
        cmp.Compare(a.end, b.end),
        cmp.Compare(a.start, b.start),
    )
})
```

`cmp.Or` short-circuits on the first non-zero comparison — it's the idiomatic
Go answer to Python's `sorted(items, key=lambda x: (x.end, x.start))` tuple-key
trick, without allocating a tuple per element.

---

## Part 2 · Why Greedy Works, Briefly

Two properties must hold for a greedy algorithm to be provably correct:

1. **Greedy-choice property** — a locally optimal choice at each step leads to
   a globally optimal solution; you never need to reconsider it later.
2. **Optimal substructure** — an optimal solution to the whole problem contains
   optimal solutions to its subproblems (the same property <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> relies on —
   greedy is the special case where you don't need to explore all subproblems
   because the correct one is knowable in advance).

The standard interview-defensible proof technique is the **exchange argument**:
assume an optimal solution that *doesn't* make the greedy choice at some step,
then show you can swap in the greedy choice without making the solution worse
— contradiction, or at worst a tie. You are not expected to write this proof
formally in an interview, but you should be able to state it in one sentence
per problem ("if we picked a later end time here, we'd only reduce room for
future intervals, never gain any") before writing code. This part of the
skillset is language-agnostic — the rest of this guide is about the Go-specific
mechanics of implementing the choice once you've justified it.

---

```arch
%% caption: The exchange argument: show that swapping the greedy choice into any optimal solution never makes it worse.
grid 190x80
node a "Greedy picks choice g first" at 0,0 w=200
node b "Take ANY optimal solution O" at 0,1 w=200
node c "Does O already contain g?" at 0,2 shape=diamond color=amber
node e "Some optimal solution contains g" at 1,2 color=green w=200
node g "Repeat on the remaining subproblem" at 2,2 w=180
node d "Swap g in" at 0,3 w=200 sub="for the element it displaces in O"
node f "Still feasible and no worse?" at 0,4 shape=diamond color=amber
node x "Greedy choice is WRONG" at 0,5 color=red w=200 sub="look at DP"
a -> b -> c
c -> e : "yes"
c -> d : "no"
d -> f
f:R -> e:B : "yes"
f -> x : "no"
e -> g
```

## Part 3 · Canonical Patterns

### 3.1 Farthest-reach tracking — Jump Game family

Track the farthest index reachable so far in a single forward pass; no
backtracking, no recursion:

```go
farthest, jumps, currentEnd := 0, 0, 0
for i := 0; i < len(nums)-1; i++ {
    if i > farthest {
        return -1  // unreachable
    }
    if i+nums[i] > farthest {
        farthest = i + nums[i]
    }
    if i == currentEnd {          // exhausted the current jump's range
        jumps++
        currentEnd = farthest
    }
}
```

The invariant maintained every iteration: `farthest` is always the best
possible outcome of *any* jump taken from indices seen so far — the greedy
choice is implicit in never discarding a better reach once found.

### 3.2 Single-pass feasibility — Gas Station

The classic "if the total is non-negative, a valid start exists, and it's the
point right after the deepest deficit" argument:

```go
total, tank, start := 0, 0, 0
for i := range gas {
    diff := gas[i] - cost[i]
    total += diff
    tank += diff
    if tank < 0 {
        start = i + 1   // no earlier start could have survived past i either
        tank = 0
    }
}
if total < 0 {
    return -1
}
return start
```

One pass, O(1) space — the greedy insight is that any station index that
causes `tank` to go negative can be eliminated as a candidate *and every index
between the previous start and here can be eliminated too*, which is why a
single running `tank` (not a re-check from every candidate start) suffices.

### 3.3 Two-pass, one-array — Candy / Trapping-style greedy

Some greedy problems need information from both directions. Rather than two
separate result arrays, allocate one `[]int` and run left-to-right, then
right-to-left, with the second pass reading (and improving) what the first
pass wrote:

```go
n := len(ratings)
candies := make([]int, n)
for i := range candies {
    candies[i] = 1                 // baseline — preallocate, don't append
}
for i := 1; i < n; i++ {           // left-to-right: compare to left neighbor
    if ratings[i] > ratings[i-1] {
        candies[i] = candies[i-1] + 1
    }
}
for i := n - 2; i >= 0; i-- {      // right-to-left: compare to right neighbor
    if ratings[i] > ratings[i+1] {
        candies[i] = max(candies[i], candies[i+1]+1)
    }
}
```

> ⚡ This is O(n) time O(n) space, reusing one slice across two passes instead
> of allocating two full arrays and merging them — the second loop's
> `max(candies[i], ...)` is what makes reusing the same array correct: it
> never *discards* information the first pass established, only strengthens it.

### 3.4 Interval scheduling — sort by end time

Maximizing the count of non-overlapping intervals: sort by **end time**, greedily
keep any interval whose start is ≥ the last kept interval's end (cross-reference
Topic 19 · Intervals, which owns interval-merging/overlap problems in depth —
this is the greedy-selection variant of the same underlying data shape):

```go
sort.Slice(iv, func(i, j int) bool { return iv[i].end < iv[j].end })
count, lastEnd := 0, math.MinInt
for _, x := range iv {
    if x.start >= lastEnd {
        count++
        lastEnd = x.end
    }
}
```

### 3.5 Kruskal's <abbr title="Minimum Spanning Tree. A subset of the edges of a connected, edge-weighted undirected graph that connects all vertices with the minimum possible total edge weight.">MST</abbr> — greedy wearing a graph-algorithm costume

Kruskal's is not really "a graph algorithm" so much as "sort edges by weight,
then greedily accept any edge that doesn't create a cycle" — the graph
machinery (Union-Find, Topic 14) is just the cycle-detection oracle the greedy
loop consults:

```go
sort.Slice(edges, func(i, j int) bool { return edges[i].weight < edges[j].weight })
uf := NewUnionFind(n)
totalWeight := 0
for _, e := range edges {
    if uf.Find(e.u) != uf.Find(e.v) {   // would NOT create a cycle
        uf.Union(e.u, e.v)
        totalWeight += e.weight
    }
}
```

Seeing Kruskal's this way — sort + greedy-accept-if-safe — is what lets you
recognize the *pattern*, not just the named algorithm, in unfamiliar problems.

---

## Part 4 · Overflow and Accumulation Gotchas

Greedy accumulation loops (running totals of gas/cost, min/max trackers) are
exactly the shape where Topic 1's overflow warning bites hardest, because the
loop runs unattended over the whole input with no per-step bounds check:

```go
// ⚠️ total += diff, accumulated over a large or adversarial input, can wrap
// silently — Go ints wrap at 64 bits, they do not raise OverflowError like
// Python's arbitrary-precision ints. `int` is 64-bit on the platforms you run on, so
// this only bites on huge sums — but for int32-typed data (or a 32-bit build) accumulate into int64 explicitly.
```

Also watch initial-sentinel choices: `lastEnd := math.MinInt` (Part 3.4) is
correct and idiomatic; `lastEnd := 0` is a subtle bug the moment an interval's
`start` can legitimately be negative.

---

## Part 5 · Complexity Table

| Pattern | Time | Space | Note |
|---|:--:|:--:|---|
| Sort-then-single-pass (most of this topic) | **O(n log n)** | O(1)–O(n) | Dominated entirely by the initial sort |
| Farthest-reach tracking (Jump Game) | O(n) | O(1) | No sort needed — already in index order |
| Gas Station single pass | O(n) | O(1) | |
| Two-pass one-array (Candy) | O(n) | O(n) | The output array itself is the only allocation |
| Kruskal's <abbr title="Minimum Spanning Tree. A subset of the edges of a connected, edge-weighted undirected graph that connects all vertices with the minimum possible total edge weight.">MST</abbr> | O(E log E) | O(V) | Sort dominates; Union-Find is ~O(1) amortized per op |
| Interval scheduling (max non-overlap) | O(n log n) | O(1) | Sort by end time |

---

## Part 6 · Python vs. Go — Where They Diverge

| | Python | Go |
|---|---|---|
| Multi-key sort | `sorted(x, key=lambda v: (v.end, v.start))` — tuple key | `cmp.Or(cmp.Compare(...), ...)` or manual `if/return` chain in `sort.Slice` |
| Sort stability | **Stable** (Timsort) — safe to lean on for tie-break order | **Unstable** (`sort.Slice`/`slices.SortFunc`) — never lean on it for correctness |
| "Infinity" sentinel | `float('inf')` / no overflow ever | `math.MaxInt` / `math.MinInt` — arithmetic on these **can overflow and wrap** |
| Min/max of two values | `min(a, b)` (builtin, any type) | `min(a, b)` / `max(a, b)` builtins since **Go 1.21** — before that, hand-rolled |
| Tuple return for two greedy trackers | Native tuple `return count, last_end` | Multiple return values — same ergonomics, no tuple allocation |

---

## Part 7 · Building Gas Station (LC 134) From Scratch

```go
package main

func canCompleteCircuit(gas []int, cost []int) int {
	total, tank, start := 0, 0, 0

	for i := 0; i < len(gas); i++ {
		diff := gas[i] - cost[i]
		total += diff
		tank += diff

		// Greedy invariant: if the tank goes negative anywhere between the
		// current `start` and `i`, NONE of those indices can be a valid
		// start either — a later start only ever has a smaller or equal
		// cumulative deficit up to this point, never a larger surplus.
		if tank < 0 {
			start = i + 1
			tank = 0
		}
	}

	// A valid circuit exists iff total gas >= total cost across the whole
	// loop. If it does, `start` (the index right after the deepest deficit)
	// is guaranteed to be the unique valid starting point.
	if total < 0 {
		return -1
	}
	return start
}
```

**Talk track while writing:** one pass, O(1) space; `total` answers "does a
solution exist at all," `tank` + the reset-on-negative answers "where does it
start"; the exchange-argument justification is that any station index between
the last reset and the current deficit point can never be a valid start,
because starting later only removes surplus you'd otherwise be carrying
forward, never adds any.

---

<!-- block:18_go_1_problems -->
## Part 8 · The Ten Problems in Go, and the Classics Beyond Them

Part 3 gave the patterns; this Part is the folder's problems in Go, plus the interval-scheduling classic and a way to *test*
a greedy. Every snippet ran on Go 1.24.5 against LeetCode's own examples.

```arch
%% caption: A greedy is only as good as its proof. Try to break it on tiny inputs first, then name the argument.
grid 200x80
node q "A greedy idea" at 0,0 shape=pill
node a "Small counter-example?\n(brute-force tiny inputs)" at 0,1 shape=diamond color=amber
node d "Not greedy: use DP or search" at 1,1 color=red w=230 sub="coins 1,3,4 for 6"
node b "Which argument fits?" at 0,2 shape=diamond color=amber
node e "Exchange argument" at 1,2 color=green w=380 sub="swap an optimal choice for the greedy one, no worse"
node s "Greedy stays ahead" at 1,3 color=green w=380 sub="after every step greedy is at least as far ahead"
node m "Matroid / structural argument" at 1,4 color=green w=380 sub="every partial choice extends to an optimum"
q -> a
a -> d : "yes"
a -> b : "no"
b:R -> e:L
b:R -> s:L
b:R -> m:L
```

### Sort, then scan: K Negations, Hand of Straights, Merge Triplets

**K Negations:** sort, negate the *most negative* first while `k` lasts (each flip adds `2·|x|`); if `k` is still odd, negate
the smallest value **of the already-negated slice** — computing `slices.Min` before the flips uses the wrong array:

```go
slices.Sort(nums)
for i := 0; i < len(nums) && k > 0 && nums[i] < 0; i++ { nums[i] = -nums[i]; k-- }
if k%2 == 1 { sum -= 2 * slices.Min(nums) }              // [4 2 3],1 -> 5    [3 -1 0 2],3 -> 6    [2 -3 -1 5 -4],2 -> 13
```

"Negate the current maximum" is the tempting wrong rule. **Hand of Straights** must always start the next run at the
**smallest remaining card** — and a Go map has no order, so iterate a **sorted key slice**:

```go
keys := slices.Sorted(maps.Keys(count))                  // Go 1.23; or build and sort by hand
for _, start := range keys {
    n := count[start]; if n == 0 { continue }
    for c := start; c < start+groupSize; c++ { if count[c] < n { return false }; count[c] -= n }   // n runs at once
}
```

Return early if `len(hand) % groupSize != 0`. `[1 2 3 6 2 3 4 7 8]`, 3 → true; `[1 2 3 4 5]`, 4 → false. **Merge Triplets**: merging is a
coordinate-wise **max**, so discard any triplet with *any* coordinate above the target (`>`, not `>=`), then check each
coordinate is hit exactly by a survivor. Merging without the filter lets one over-target coordinate poison the max.

### Running best and running frontier: Kadane, Jump Game I/II, Stock II

```go
curr = max(x, curr+x); best = max(best, curr)            // Kadane: extend or restart. Seed best with nums[0], NOT 0
farthest = max(farthest, i+x); if i > farthest { return false }     // Jump Game: fail when you can never arrive
if i == levelEnd { jumps++; levelEnd = farthest }         // Jump Game II: loop i < n-1, or you jump FROM the destination
profit += max(0, prices[i]-prices[i-1])                    // Stock II: sum every rise (no fee, no cooldown, unlimited)
```

Seeding Kadane's `best` with `0` allows the empty subarray and is wrong on `[-3 -2 -5]` (answer −2). Jump Game needs
*no per-step jump choices* — "always take the biggest jump" walks into a `0`. Stock II's trick stops working the moment a
cooldown, fee or transaction limit appears (that is <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr>, topic 17).

### Running total and precomputation: Gas Station, Partition Labels, Valid Parenthesis String

Gas Station (Part 7) resets the start after a failed stretch and needs the global `sum(gas) >= sum(cost)` check. **Partition
Labels** precomputes each letter's *last* index in a `[26]int`, then cuts when `i == end` — the map must be built *first*, or
you cannot know a letter will not reappear:

```go
for i := 0; i < len(s); i++ { end = max(end, last[s[i]-'a']); if i == end { out = append(out, end-start+1); start = i + 1 } }
// "ababcbacadefegdehijhklij" -> [9 7 8]
```

**Valid Parenthesis String** tracks the *range* `[lo, hi]` of possible unmatched `(`, because a `*` has three meanings — a
single counter or a fixed "`*` is `(` first" rule cannot backtrack:

```go
case '(': lo++; hi++
case ')': lo--; hi--
default:  lo--; hi++                                       // '*': '(' , ')' or empty
if hi < 0 { return false }; lo = max(lo, 0)                 // hi < 0: too many ')' ; clamp lo at 0
return lo == 0                                              // "(*)" true   "(*))" true   ")(" false
```

### Interval scheduling: the sort key *is* the algorithm

Maximise the number of non-overlapping intervals. Sort by **end time** (ties by start), keep any interval that starts at or
after the last kept end — seed `lastEnd` with `math.MinInt`, not `0`, so a negative start is not silently rejected:

```go
slices.SortFunc(c, func(a, b iv) int { return cmp.Or(cmp.Compare(a.e, b.e), cmp.Compare(a.s, b.s)) })
```

The tempting alternatives fail: earliest-**start** on `[[1 10] [2 3] [4 5]]` picks only `[1 10]` (1, not 2), and shortest-first
fails when a short interval in the middle blocks two others. **Test it.** A brute force over every subset is 12 lines, and
over 2,000 random instances (up to 6 intervals, coordinates 0–13) the earliest-end greedy disagreed **0** times, earliest-start
**82**, shortest-first **560** (Go's `rand` with seed 3; Python's run of the same experiment gave 0 / 100 / 576 — the ordering, not
the exact counts, is the point). A counter-example found in seconds beats a proof attempted in minutes.

The same skeleton answers **Minimum Arrows to Burst Balloons** (sort by end; a new arrow whenever `p[0] > end`) and
**Non-overlapping Intervals** (`n − chosen`).

### More classics

```go
// Candy: two passes over ONE slice; the second takes max so it never discards the first pass's work.
c[i] = max(c[i], c[i+1]+1)                                  // [1 0 2] -> 5   [1 2 2] -> 4

// Queue Reconstruction: tallest first (ties: fewer-in-front first), then insert at index k.
out = slices.Insert(out, p[1], p)                           // a shorter person never changes a taller one's count

// Two City Scheduling: sort by cost_A - cost_B; first half to A, second half to B.  -> 110
```

Fractional knapsack (sort by value/weight, take greedily, `float64`) is optimal — capacity 50 on `(60,10) (100,20) (120,30)`
gives **240** — but 0/1 knapsack on the same items is **220**; greedy fails as soon as an item cannot be split.

### Go traps in this topic

| Trap | What happens | The fix |
|---|---|---|
| A comparator written as `a[1] - b[1]` | For `int32` data it overflows and can flip the sign (`MaxInt32 − MinInt32 < 0` measured `true`). | `cmp.Compare(a[1], b[1])`. |
| Relying on `sort.Slice` stability for ties | Unspecified order of equal keys. | An explicit secondary key via `cmp.Or`. |
| Iterating a `map` for "the smallest key" | Random order. | Sort the keys first. |
| `lastEnd := 0` | Rejects intervals with negative starts. | `math.MinInt`. |
| Kadane seeded with `0` | Allows the empty subarray. | Seed with `nums[0]`. |
| Sorting the caller's slice in place | Reorders their data. | `slices.Clone` first (as the scheduler above does). |
| `cmp.Or` on Go < 1.22 | Compile error. | Use an explicit `if` chain, or upgrade. |

### Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Prove it." | The exchange argument or the "stays ahead" quantity, in one sentence. |
| "Why not DP?" | Greedy is O(n log n) or O(n); DP only if a small counter-example exists — show you looked. |
| "Does the sort key matter?" | It *is* the algorithm; give the counter-example for the wrong key. |
| "Weighted intervals?" | Greedy fails — DP over end-sorted intervals with a binary search for the last compatible one. |
| "Streaming?" | Kadane and farthest-reach work online; the sorted greedies need the whole input. |

---
<!-- /block:18_go_1_problems -->

<!-- problem-map:start -->
## Part 9 · Every Problem in This Topic, by Pattern

Ten problems, four moves (sort then scan · running best-so-far · running frontier · range tracking) — the Python guide's map in Go. Every **Trap** is a "looks-greedy-but-wrong" mistake documented in that problem's solution file, plus the Go-specific hazards. Topic 18's solutions are Python-first; the Go column is the plan you would write.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Maximize Sum Of Array After K Negations](GoDSA/18_greedy/001_maximize_sum_of_array_after_k_negations/solution.go) <br>LC 1005 · Easy | Sort, then scan | `slices.Sort`; negate the most negative while `k` lasts; leftover odd `k` subtracts `2 * slices.Min(nums)` of the *negated* slice. **Trap:** "negate the current maximum"; the pre-flip minimum. |
| [002 · Maximum Subarray](GoDSA/18_greedy/002_maximum_subarray/solution.go) <br>LC 53 · Medium | Running best-so-far (Kadane) | `curr = max(x, curr+x)`; seed `best` with `nums[0]`. **Trap:** `best := 0` (empty subarray); `curr = max(0, curr) + x`. |
| [003 · Jump Game](GoDSA/18_greedy/003_jump_game/solution.go) <br>LC 55 · Medium | Running frontier | `farthest = max(farthest, i+x)`; `i > farthest` → false. **Trap:** "always take the biggest jump"; comparing with `n` instead of `n-1`. |
| [004 · Jump Game II](GoDSA/18_greedy/004_jump_game_ii/solution.go) <br>LC 45 · Medium | Running frontier by levels | `levelEnd`/`farthest`/`jumps`, looping `i < len(nums)-1`. **Trap:** "always jump exactly `nums[i]`"; looping to `n` (an extra jump). |
| [005 · Gas Station](GoDSA/18_greedy/005_gas_station/solution.go) <br>LC 134 · Medium | Running total + reset point | One pass with `total` and `tank`; `total < 0 → -1`. **Trap:** the local test `gas[i] >= cost[i]`; no global check. |
| [006 · Best Time to Buy and Sell Stock II](GoDSA/18_greedy/006_best_time_to_buy_and_sell_stock_ii/solution.go) <br>LC 122 · Medium | Sum every rise | `profit += max(0, p[i]-p[i-1])`. **Trap:** one best (buy, sell) pair; reusing it with a fee or cooldown. |
| [007 · Hand of Straights](GoDSA/18_greedy/007_hand_of_straights/solution.go) <br>LC 846 · Medium | Sort, then start from the minimum | `count` map plus a **sorted key slice**; consume `n` runs at a time. **Trap:** an arbitrary start card; iterating the map (random order); no `len % groupSize` guard. |
| [008 · Merge Triplets to Form Target Triplet](GoDSA/18_greedy/008_merge_triplets_to_form_target_triplet/solution.go) <br>LC 1899 · Medium | Filter, then scan | Skip a triplet with any coordinate `> target`; track which coordinates are hit. **Trap:** no filter; filtering on fewer than three coordinates; `>=`. |
| [009 · Partition Labels](GoDSA/18_greedy/009_partition_labels/solution.go) <br>LC 763 · Medium | Precompute last index, then scan | `var last [26]int` first; cut at `i == end`. **Trap:** cutting when a letter "looks stable"; one-pass map building. |
| [010 · Valid Parenthesis String](GoDSA/18_greedy/010_valid_parenthesis_string/solution.go) <br>LC 678 · Medium | Range tracking | `lo`/`hi` with `lo = max(lo, 0)`, `hi < 0 → false`, `lo == 0` at the end. **Trap:** "`*` is `(` first"; forgetting the clamp. |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] State the exchange-argument justification for the greedy choice in one sentence before coding
- [ ] Identify whether the algorithm's correctness depends on a tie-break — if so, encode it as an explicit secondary sort key, never rely on `sort.SliceStable`
- [ ] Know the multi-key `sort.Slice` / `cmp.Or` comparator shape cold
- [ ] Recognize Kruskal's as "sort edges, greedily accept if no cycle" rather than memorizing it as a standalone algorithm
- [ ] Use an explicit int64 or bounds-aware accumulation when summing over large/adversarial inputs
- [ ] Pick correct sentinel initial values (`math.MinInt`/`math.MaxInt`, not `0`) when the domain includes negative numbers
- [ ] Recognize the two-pass-one-array pattern instead of allocating two separate result slices
- [ ] Test a greedy against a brute force on tiny random inputs, and report what it found <!--ca-->
- [ ] Write interval scheduling with `cmp.Or` (end, then start) and `math.MinInt` for `lastEnd` <!--ca-->
- [ ] Never write a comparator as `a - b` on int32-sized data — use `cmp.Compare` <!--ca-->
- [ ] Iterate a sorted key slice, never a map, when a greedy needs "the smallest remaining" <!--ca-->
- [ ] Give the counter-examples: greedy coin change, 0/1 knapsack, earliest-start scheduling <!--ca-->
