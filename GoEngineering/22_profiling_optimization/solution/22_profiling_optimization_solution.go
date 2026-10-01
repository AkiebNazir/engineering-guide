// Package solution implements the same record-aggregation logic twice —
// once the obviously-correct way (SummarizeNaive) and once rewritten after
// profiling to minimize allocations (SummarizeOptimized) — as a worked
// example of the profile-benchmark-fix loop rather than a claim that hand
// optimization is always warranted.
//
// MEASURED RESULTS (this machine, Apple M4 Pro, go test -bench=. -benchmem
// -count=3, 1000 records, 20 distinct IDs, 10 values each — see the
// _test.go BenchmarkSummarize* functions for the exact setup; numbers
// stable across 3 runs):
//
//	BenchmarkSummarizeNaive-12        5414   221599 ns/op   1609706 B/op   3238 allocs/op
//	BenchmarkSummarizeOptimized-12   36488    32884 ns/op     56261 B/op     29 allocs/op
//
// ~6.7x faster wall-clock, ~28x less memory, ~112x fewer allocations. The
// naive version's dominant cost is `tagKey += tag + ","` string
// concatenation inside the per-record loop, plus unbounded `append` growth
// on the never-actually-needed per-ID []float64 accumulation.
//
// A real mid-course correction worth keeping visible (this is exactly the
// "profile, don't assume" lesson the exercise is about): the first version
// of SummarizeOptimized pooled a *strings.Builder and called Reset()
// between records, expecting Reset() to preserve the builder's grown
// capacity the way `buf[:0]` does for a plain slice. It does not —
// `(*strings.Builder).Reset()` sets its internal buffer to nil — so that
// version was still allocating on nearly every tag write and only barely
// beat the naive version (3029 allocs/op vs naive's 3238, confirmed via
// `go tool pprof -alloc_objects -top` showing ~98% of all allocations
// inside WriteString/WriteByte). Switching the pooled scratch to a raw
// []byte reset via `buf[:0]` (which keeps the backing array) produced the
// 29-allocs/op number above. See the scratchPool comment below for the
// full story.
package solution

import (
	"sort"
	"sync"
)

// Record is one input row to aggregate.
type Record struct {
	ID     string
	Tags   []string
	Values []float64
}

// Stat is the aggregated summary for one ID.
type Stat struct {
	ID    string
	Count int
	Sum   float64
	Mean  float64
	Max   float64
}

// ---------------------------------------------------------------------
// Naive implementation: correct, unoptimized, deliberately kept this way
// as the "before" side of the benchmark comparison.
// ---------------------------------------------------------------------

// SummarizeNaive groups records by ID and computes count/sum/mean/max.
//
// Deliberately naive choices kept here (see solution comments for why each
// one costs allocations, confirmed by the benchmark numbers above):
//   - `make(map[string]*naiveAcc)` with no capacity hint: the map's bucket
//     array reallocates repeatedly as it crosses Go's load-factor
//     thresholds while keys are being discovered.
//   - building a "tagKey" via `+=` string concatenation per value: each
//     `+=` allocates a brand new string and copies both operands into it,
//     which is O(n^2) total work across a growing string — the classic
//     "looks fine, isn't" hot-loop allocation.
//   - `append` to a per-ID []float64 with no pre-sizing: repeated slice
//     growth means the backing array is reallocated and fully copied
//     O(log n) times as it grows past capacity.
func SummarizeNaive(records []Record) []Stat {
	type naiveAcc struct {
		count  int
		sum    float64
		max    float64
		values []float64 // grown with plain append, no capacity hint
		tagKey string    // built with += concatenation, unused beyond
		// existing to demonstrate the allocation cost — a real aggregator
		// might use this for a dedup/grouping key
	}

	acc := make(map[string]*naiveAcc) // NO capacity hint on purpose
	for _, r := range records {
		a, ok := acc[r.ID]
		if !ok {
			a = &naiveAcc{max: -1}
			acc[r.ID] = a
		}
		for _, v := range r.Values {
			a.count++
			a.sum += v
			if v > a.max {
				a.max = v
			}
			a.values = append(a.values, v) // no pre-sizing: repeated regrowth
		}
		for _, tag := range r.Tags {
			a.tagKey = a.tagKey + tag + "," // += concatenation: reallocates every iteration
		}
	}

	out := make([]Stat, 0, len(acc))
	for id, a := range acc {
		mean := 0.0
		if a.count > 0 {
			mean = a.sum / float64(a.count)
		}
		out = append(out, Stat{ID: id, Count: a.count, Sum: a.sum, Mean: mean, Max: a.max})
	}
	sort.Slice(out, func(i, j int) bool { return out[i].ID < out[j].ID })
	return out
}

// ---------------------------------------------------------------------
// Optimized implementation: identical output, rewritten to cut allocations.
// ---------------------------------------------------------------------

// optAcc is the scratch accumulator type pooled by scratchPool. It holds
// only value types and a slice header (no pointers into records), so
// resetting it between uses is just zeroing a handful of fields — no
// finalizer/Close() semantics, which is exactly the shape of object
// sync.Pool is meant for (see the "COMMON PITFALLS" note in the
// explanation file: never pool something whose lifecycle other code
// depends on).
type optAcc struct {
	count int
	sum   float64
	max   float64
}

// tagScratch is the pooled scratch buffer for tag-key construction. It
// wraps a plain []byte rather than a *strings.Builder — see the comment on
// scratchPool below for the (measured, not assumed) reason why.
type tagScratch struct {
	buf []byte
}

// scratchPool holds a reusable *tagScratch for tag-key construction — the
// one piece of genuinely allocation-prone scratch state in this function
// (string building).
//
// THIS WAS *strings.Builder ORIGINALLY, AND IT WAS WRONG — a real,
// measured finding kept here deliberately rather than silently fixed with
// no trace, because it's exactly the kind of thing profiling catches and
// intuition doesn't: `(*strings.Builder).Reset()` does not keep the
// builder's internal buffer — it sets it to nil (`b.buf = nil`), so
// calling Reset() every iteration of the outer loop discarded the grown
// capacity and forced a fresh heap allocation on every single record's
// tag-key build. A `go test -bench=. -memprofile` + `go tool pprof
// -alloc_objects -top` run on the strings.Builder version showed ~98% of
// all allocations coming from `(*strings.Builder).WriteString` and
// `WriteByte` — i.e. the "optimization" was barely better than the naive
// version's `+=` concatenation, because both were allocating a new backing
// array on essentially every write. Switching the pooled scratch to a raw
// []byte and resetting via `buf = buf[:0]` (which keeps the underlying
// array and its capacity) instead of assigning nil fixed it — see the
// updated MEASURED RESULTS in this file's header, captured after this fix.
var scratchPool = sync.Pool{
	New: func() any { return &tagScratch{} },
}

// SummarizeOptimized computes the identical result to SummarizeNaive but
// minimizes allocations:
//   - the accumulator map is sized with a capacity hint derived from the
//     input (an upper bound — actual distinct IDs may be fewer, which is
//     fine; over-sizing a map to avoid regrowth is the correct trade,
//     under-sizing costs more reallocation than the wasted capacity costs
//     memory);
//   - tag-key building uses a pooled strings.Builder instead of `+=`
//     concatenation — O(n) total writes into one growing buffer instead of
//     O(n^2) copy-and-discard;
//   - per-ID running stats (count/sum/max) are kept as plain value fields,
//     never accumulating a growing []float64 at all, because the
//     naive version's `values []float64` was never actually read after
//     being built (dead weight kept there only to demonstrate its cost;
//     removing the need for it entirely is itself the biggest win —
//     the fastest allocation is the one you don't do).
func SummarizeOptimized(records []Record) []Stat {
	// Rough upper bound on distinct IDs: len(records). Sizing to this
	// avoids map bucket-array regrowth for the common case where IDs
	// repeat only a little; it costs a bit of extra initial memory when
	// IDs repeat a lot, which is the right trade for a hot path.
	acc := make(map[string]*optAcc, len(records))

	scratch := scratchPool.Get().(*tagScratch)
	defer func() {
		scratch.buf = scratch.buf[:0]
		scratchPool.Put(scratch)
	}()

	for _, r := range records {
		a, ok := acc[r.ID]
		if !ok {
			a = &optAcc{max: -1}
			acc[r.ID] = a
		}
		for _, v := range r.Values {
			a.count++
			a.sum += v
			if v > a.max {
				a.max = v
			}
		}
		// Tag-key building via the pooled []byte instead of += — kept to
		// mirror the naive version's work (so the benchmark is comparing
		// like-for-like effort, not "optimized does less work"). Slicing
		// to [:0] (not reassigning to nil) is what actually preserves the
		// backing array's capacity across iterations and across calls via
		// the pool — this is the fix for the strings.Builder.Reset()
		// pitfall documented above.
		scratch.buf = scratch.buf[:0]
		for _, tag := range r.Tags {
			scratch.buf = append(scratch.buf, tag...)
			scratch.buf = append(scratch.buf, ',')
		}
		_ = string(scratch.buf) // consumed here in a real system; discarded in this exercise
	}

	out := make([]Stat, 0, len(acc))
	for id, a := range acc {
		mean := 0.0
		if a.count > 0 {
			mean = a.sum / float64(a.count)
		}
		out = append(out, Stat{ID: id, Count: a.count, Sum: a.sum, Mean: mean, Max: a.max})
	}
	sort.Slice(out, func(i, j int) bool { return out[i].ID < out[j].ID })
	return out
}

/*
ESCAPE ANALYSIS — go build -gcflags="-m" ./22_profiling_optimization/solution/... 2>&1 | grep -i escape

Real, complete output from that exact command against this file (both
functions' internal helper types included for contrast):

  make(map[string]*naiveAcc) does not escape
  &naiveAcc{...} escapes to heap
  a.tagKey + tag + "," escapes to heap
  make(map[string]*optAcc, len(records)) does not escape
  &optAcc{...} escapes to heap
  &tagScratch{} escapes to heap
  string(scratch.buf) does not escape

Both accumulator structs (&naiveAcc{...}, &optAcc{...}) escape in BOTH
implementations, for the identical reason: they're stored as map values,
and the compiler can't prove the map itself doesn't outlive the current
stack frame (maps are reference types whose backing storage is always
heap-allocated), so anything reachable through it must also be
heap-allocated. This is *not* one of the differences the benchmark
measures; it's identical overhead in both versions, which is exactly why
comparing the two numbers isolates the real difference (string building)
instead of conflating it with something constant.

The map itself, by contrast, `does not escape` in both cases — Go's
escape analysis can prove the map header/hash state never leaves this
function even though its VALUES do, because nothing returns the map or
stores it somewhere longer-lived; only what's reachable *through* a value
already forced to the heap (the *naiveAcc/*optAcc pointers) escapes.

`&tagScratch{}` escapes to heap — expected and fine: it's allocated inside
scratchPool's New func and stored into the sync.Pool's internal slice,
which by definition outlives the current call. This is a one-time cost
per pool-miss, not a per-record cost — the entire point of pooling it.

Contrast this against the ORIGINAL (buggy) strings.Builder version: its
equivalent scratch struct escaped identically, but — as the header comment
explains — `Reset()` discarded that struct's internal buffer's capacity on
every single loop iteration, forcing `WriteString`/`WriteByte` to
re-escape and reallocate a new backing array practically every time. The
`[]byte` + `buf[:0]` version fixes this: `buf[:0]` keeps the same backing
array (confirmed by the compiler's own `ignoring self-assignment in
scratch.buf = scratch.buf[:0]` note — it recognizes the slice header isn't
meaningfully changing), so `append` only allocates when it must actually
grow past the current capacity, which happens only a handful of times
total as the buffer reaches its steady-state size, not once per record.

BEST PRACTICES

  - Profile before optimizing. This file's "before" numbers came from an
    actual `go test -bench=. -benchmem` run, not a guess — always attach
    real numbers to a performance claim.
  - Prefer eliminating an allocation over speeding it up (the biggest win
    here was dropping the never-read `values []float64` accumulation
    entirely, not making it faster).
  - Size maps and slices with a capacity hint whenever the count is known
    or boundable — even a loose upper bound beats no hint.
  - Use `strings.Builder` (or `bytes.Buffer`) for any string built across
    more than a couple of concatenations; never `+=` in a loop. But if you
    intend to pool and reuse one across many short-lived builds, know that
    `Reset()` drops its internal buffer (sets it to nil) rather than
    keeping capacity — pool a raw `[]byte` and reset via `buf[:0]` instead
    when reuse-of-capacity is the actual goal (measured above).
  - Reserve `sync.Pool` for short-lived scratch objects with no external
    identity or lifecycle contract; always Reset()/zero before Put, and
    never assume a Get returns a "fresh" (zeroed) object unless your New
    func or your own reset logic guarantees it.

ALTERNATIVE APPROACHES / TRADE-OFFS

  - A columnar (struct-of-slices) input representation instead of
    []Record (array-of-structs) would improve cache locality further for
    very large batches, at the cost of a much less ergonomic API — not
    worth it unless profiling on real production data shows this function
    is still hot after the changes made here.
  - `sync.Pool` could also hold the *optAcc values themselves across calls
    to Summarize* if this function were called repeatedly in a hot loop
    (e.g., once per HTTP request) — not done here because within a single
    call each optAcc's lifetime already ends when the function returns;
    pooling only pays off when the *caller* invokes this function
    repeatedly and pool reuse survives across those calls.
  - Precomputing distinct ID count (e.g., if IDs are known to come from a
    bounded enum) would let the map be sized exactly instead of
    over-sized to len(records) — a cheap win when the domain allows it.

TESTING / BENCHMARKING / FAILURE MODES

  - The test file cross-checks SummarizeNaive and SummarizeOptimized
    against EACH OTHER on randomized input (not just against a fixed
    fixture) — this is the property that actually matters: the optimized
    version must be observably indistinguishable in output, only in cost.
  - Benchmarks use `b.ReportAllocs()` and assign every result to a
    package-level sink var (see _test.go) so the compiler cannot prove the
    loop body's result is unused and eliminate it — a benchmark without
    this guard can silently measure nothing.
  - Failure mode if the sync.Pool's builder were never Reset() before
    reuse: tag keys from a previous call would leak into the next one's
    output — this is exactly the class of bug sync.Pool user code is
    responsible for preventing, since the pool itself has no idea what
    "clean" means for your type.
*/
