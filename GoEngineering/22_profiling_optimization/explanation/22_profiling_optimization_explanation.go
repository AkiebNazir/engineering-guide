/*
Problem 22 — Profiling & Optimization (pprof, escape analysis, allocations,
sync.Pool, honest benchmarks)

WHAT WE'RE BUILDING

A small "record aggregator": given a batch of Record{ID string, Tags []string,
Values []float64} it produces per-ID summary stats (count, sum, mean, max).
This is a stand-in for the shape of real hot-path code: lots of small
allocations (string building, slice growth, intermediate maps) done once per
request/record, which is exactly where allocation-driven GC pressure comes
from in production Go services.

We implement it TWICE on purpose:

 1. SummarizeNaive — the obviously-correct first draft. String
    concatenation with +, no capacity hints, a fresh map lookup path, a
    freshly allocated []Stat every call.
 2. SummarizeOptimized — the same output, rewritten after profiling to
    avoid unnecessary allocations: pre-sized maps/slices, strings.Builder
    with computed key building, and a sync.Pool for a reusable scratch
    buffer type.

The point of the exercise is not "optimized is fancier" — it's the
*methodology*: profile first, benchmark before/after, only keep a change
that measurably wins, understand exactly which allocation moved from heap
to stack (or was eliminated) and why.

# WHY THIS MATTERS IN REAL SYSTEMS

Every senior Go engineer eventually debugs a service where GC pauses or CPU
spend way exceeds what the algorithm should cost. The tools for this ship
in the stdlib: `runtime/pprof` for CPU/heap/goroutine profiles, `go tool
pprof` to analyze them, `go build -gcflags="-m"` to see the compiler's
escape analysis decisions, and `testing.B` with `-benchmem` for honest,
repeatable allocation counts. Guessing at performance without measuring is
how "optimizations" that do nothing (or make things worse) end up in
production.

CONCEPTS COVERED

  - `runtime/pprof.StartCPUProfile` / `WriteHeapProfile` for programmatic
    profiling (and `net/http/pprof` for a live server's `/debug/pprof/`)
  - Escape analysis: `go build -gcflags="-m"` output, what makes a value
    "escape to heap" (returned by pointer, stored in an interface, closed
    over by an escaping closure, sized unknown at compile time)
  - `sync.Pool` for reusing scratch allocations across calls, and the
    contract it requires (never assume anything survives between Get/Put,
    always reset before reuse, never Pool something with per-item identity
    that matters)
  - `testing.B` correctly: `b.ReportAllocs()`, `b.ResetTimer()` /
    `b.StartTimer()`/`b.StopTimer()` around setup, `b.N`, and a
    package-level sink variable so the compiler can't dead-code-eliminate
    the very thing you're benchmarking
  - Reading `-benchmem` output: ns/op, B/op, allocs/op

# SPEC

	type Record struct {
	    ID     string
	    Tags   []string
	    Values []float64
	}

	type Stat struct {
	    ID    string
	    Count int
	    Sum   float64
	    Mean  float64
	    Max   float64
	}

SummarizeNaive(records []Record) []Stat
SummarizeOptimized(records []Record) []Stat
  - Both group records by ID (a record's Values are added to that ID's
    running count/sum/max) and return one Stat per distinct ID.
  - Order of the returned []Stat does not need to match input order, but
    MUST be deterministic across calls with the same input (sort by ID) —
    otherwise the benchmark/test can't compare outputs meaningfully.
  - Both must produce IDENTICAL output for identical input — this is
    checked by a test that fuzzes/table-tests both against each other, not
    just against a hand-computed expected value.

ACCEPTANCE CRITERIA

  - `go test ./22_profiling_optimization/solution/...` passes, including a
    test that asserts SummarizeNaive and SummarizeOptimized agree on
    randomized input.
  - `go test -bench=. -benchmem ./22_profiling_optimization/solution/...`
    runs both benchmarks and SummarizeOptimized shows measurably fewer
    allocs/op than SummarizeNaive (documented with real numbers in the
    solution file, not asserted from memory).
  - `go build -gcflags="-m" ./22_profiling_optimization/solution/... 2>&1 | grep escape`
    output is discussed in the solution file's comments for at least one
    concrete case in each implementation.

HINTS

  - String concatenation with `+` in a loop reallocates on every
    concatenation; `strings.Builder` (or knowing the final size and using
    `make([]byte, 0, n)`) avoids that.
  - A map without a capacity hint (`make(map[K]V)`) grows by reallocating
    its bucket array repeatedly as it crosses load-factor thresholds — if
    you know (or can estimate) the number of keys up front,
    `make(map[K]V, n)` measurably reduces allocations.
  - `sync.Pool` is for *reducing GC pressure on short-lived scratch
    objects*, not for object lifecycle/cleanup semantics — never put
    something in a Pool that has a Close()/finalizer contract others rely
    on, and always zero/reset it before returning to the pool or after
    getting it out (whichever direction your invariant needs).
  - `go build -gcflags="-m"` prints one line per compiler escape decision;
    grep for the type/variable name you care about, output is verbose.
  - Benchmark pitfall: forgetting `b.ReportAllocs()` hides the exact metric
    you're trying to optimize; forgetting to assign the loop's result to a
    package-level sink lets the compiler prove the result is unused and
    optimize the whole loop body away, benchmarking nothing.

COMMON PITFALLS

  - "Optimizing" based on intuition/StackOverflow folklore instead of an
    actual profile — the bottleneck is often not where you'd guess.
  - Micro-benchmarking something the compiler can constant-fold or
    dead-code-eliminate, producing a benchmark result that says nothing
    about real workloads.
  - Using `sync.Pool` for objects with meaningfully different sizes without
    capping what goes back in — a single huge item put back can pin a large
    backing array in the pool indefinitely (the pool is not size-aware).
  - Trusting a benchmark run once — GC pauses, other processes, and thermal
    throttling all add noise; run with `-count=N` and `benchstat` for real
    comparisons in a serious investigation (not required for this exercise,
    but worth knowing).

STRETCH GOALS

  - Wire an `net/http/pprof` endpoint into a tiny throwaway `main()` and
    capture a real CPU profile of SummarizeNaive under load with
    `go tool pprof`.
  - Add a benchmark variant with `GOMAXPROCS`-scaled parallelism
    (`b.RunParallel`) and see whether the allocation-heavy naive version
    degrades disproportionately under contention (shared allocator/GC
    pressure) compared to the optimized version.
  - Try replacing the `sync.Pool`-backed scratch buffer with a fixed-size
    stack array where possible, and use `-gcflags="-m"` to confirm it
    genuinely stays on the stack (no `moved to heap` line for it).
*/
package explanation

// Record is one input row: an ID key plus tag labels and numeric values to
// aggregate.
//
// TODO: add the Values []float64 and Tags []string fields per the spec.
type Record struct {
	ID string
}

// Stat is the aggregated summary for one ID.
//
// TODO: add Count int, Sum float64, Mean float64, Max float64 per the spec.
type Stat struct {
	ID string
}

// SummarizeNaive is the obviously-correct, unoptimized first draft.
//
// TODO: group records by ID using string concatenation for any derived
// keys, a map without a capacity hint, and return a freshly built []Stat
// sorted by ID.
func SummarizeNaive(records []Record) []Stat {
	panic("TODO: implement SummarizeNaive")
}

// SummarizeOptimized computes the identical result to SummarizeNaive but
// is written to minimize allocations: pre-sized map, strings.Builder where
// string building is unavoidable, and a sync.Pool for scratch state.
//
// TODO: implement with allocation-reduction techniques from the header
// comment; output must be identical (same []Stat, same order) to
// SummarizeNaive for the same input.
func SummarizeOptimized(records []Record) []Stat {
	panic("TODO: implement SummarizeOptimized")
}
