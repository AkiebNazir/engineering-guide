/*
Problem 35 — Profiling & Tracing (pprof profile types, flame graphs, the
execution tracer, tasks and regions, flight recorder, scheduler latency,
goroutine leak detection)

WHAT WE'RE BUILDING

An observability toolkit around a small order-processing pipeline:

 1. ProcessOrders — a worker pool instrumented with runtime/trace TASKS
    (one per order), REGIONS (validate → price → persist) and LOGS.
 2. TraceTo / ProfileCPU — capture an execution trace or a CPU profile of
    any function.
 3. ContentionProfile / BlockProfile — enable, capture and restore the
    mutex and block profilers around a workload.
 4. GoroutinesMatching — parse the goroutine profile to count goroutines
    stuck in a function: the basis of a goroutine-leak test (LeakyFanOut
    vs FixedFanOut).
 5. MeasureSchedLatency — read the runtime's /sched/latencies:seconds
    histogram to quantify time goroutines waited for a CPU.
 6. SlowRequestCapture — HTTP middleware that keeps a rolling in-memory
    trace with trace.FlightRecorder (Go 1.25) and snapshots it only when a
    request is slow.

WHY THIS MATTERS IN REAL SYSTEMS

"The service is slow" has very different causes, and each tool sees only
some of them:

  - CPU-bound hot path (JSON encoding, regex, hashing) → CPU profile.
  - Allocation churn driving GC → heap profile (alloc_space) + gctrace
    (Problems 22 and 28).
  - Lock contention → mutex profile.
  - Waiting on channels, I/O, or other goroutines → block profile, trace.
  - Goroutines runnable but not running (CPU starvation, GOMAXPROCS too
    low, CFS throttling) → scheduler latency, execution trace.
  - A leak that grows memory over days → goroutine profile diffs.
  - A 2-second p99.9 spike that happens twice an hour → flight recorder.

A CPU profile of a service whose requests are slow because they WAIT will
show nothing interesting — the classic trap this problem is built around.

MENTAL MODEL 1 — PICK THE TOOL BY THE QUESTION

    | Question                                    | Tool                                   |
    |---------------------------------------------|----------------------------------------|
    | Which code burns CPU?                       | CPU profile (pprof)                    |
    | Who allocates / what's retained?            | heap profile: alloc_space / inuse_space|
    | Where do goroutines wait on locks?          | mutex profile                          |
    | Where do goroutines block (chan, select)?   | block profile                          |
    | How many goroutines, stuck where?           | goroutine profile                      |
    | WHEN did things happen, in what order?      | execution trace                        |
    | Why was THIS request slow?                  | trace tasks/regions, flight recorder   |
    | Are goroutines starved of CPU?              | /sched/latencies histogram, trace      |
    | Is GC the problem?                          | gctrace, runtime/metrics, trace        |

pprof answers "where, in aggregate". The tracer answers "when, and why was
this goroutine not running". Metrics answer "is it happening right now".

MENTAL MODEL 2 — HOW SAMPLING PROFILES WORK

    CPU profile: SIGPROF 100×/second per running thread
                 → record the stack of the goroutine ON CPU at that instant

      time ─────────────────────────────────────────────────────────▶
      G1  ████████ price ████████░░░░ sleep ░░░░████ price ███
      tick  ↑    ↑    ↑    ↑    ↑           (no samples while     ↑    ↑
                                              blocked)
      profile: price 7 samples, sleep 0 samples

    heap profile:   one sampled allocation per ~512 KB allocated
                    (runtime.MemProfileRate), with its stack
    mutex profile:  contention events × SetMutexProfileFraction
    block profile:  blocking events ≥ SetBlockProfileRate nanoseconds
    goroutine:      a snapshot of every goroutine's stack right now

Sampling makes CPU and heap profiling cheap enough for production (the
CPU profiler is commonly run continuously). Mutex and block profiling are
OFF by default; rate 1 records everything and is for diagnostics only.

Measured here: TestLesson_CPUProfileFindsHotFunction profiles the pipeline
for ~500 ms. priceOrder is the hottest APPLICATION function (0.35 s, 31%),
while the 1 ms time.Sleep in the persist region — comparable wall time per
order — does not appear at all. The top row is runtime.pthread_cond_wait
(50%): idle worker threads parking because the pipeline spends much of its
wall time asleep. Seeing idle/scheduler runtime frames at the top is itself a
signal that the workload is not CPU-bound.

MENTAL MODEL 3 — READING PPROF OUTPUT AND FLAME GRAPHS

	go tool pprof -top cpu.pprof      (real output from the test, trimmed)
	Duration: 502.01ms, Total samples = 1.13s (225.09%)
	      flat  flat%   sum%        cum   cum%
	     0.57s 50.44% 50.44%      0.57s 50.44%  runtime.pthread_cond_wait
	     0.35s 30.97% 81.42%      0.36s 31.86%  .../solution.priceOrder
	     0.13s 11.50% 92.92%      0.13s 11.50%  runtime.kevent
	         0     0%   100%      0.36s 31.86%  .../solution.ProcessOrders.func1

  - Total samples 1.13 s over 0.5 s wall = 2.25 CPUs busy on average.
  - flat: samples where the function itself was executing.
  - cum:  samples where the function was anywhere on the stack
    (ProcessOrders.func1 has 0 flat but 0.36 s cum: its time is in priceOrder).
  - High flat → optimise that function. High cum, low flat → look at what
    it calls.

    flame graph (go tool pprof -http=:8080 cpu.pprof → View → Flame Graph)

    ┌──────────────────────────────────────────────────────────────────┐
    │ runtime.goexit                                                   │  root
    ├──────────────────────────────────────────────────────────────────┤
    │ tracing.ProcessOrders.func1                                      │
    ├───────────────────────────────────────────────────────┬──────────┤
    │ tracing.priceOrder                                    │ chan ops │
    └───────────────────────────────────────────────────────┴──────────┘
      WIDTH = share of samples (not time order!)   parent above children

Profiles can be diffed (`go tool pprof -diff_base old.pprof new.pprof`) and
fed back to the compiler: a representative CPU profile saved as default.pgo
in the main package enables profile-guided optimisation (inlining and
devirtualisation of hot calls).

MENTAL MODEL 4 — THE EXECUTION TRACER

The tracer records EVENTS, not samples: every goroutine state transition,
with timestamps.

    goroutine states:
                        ┌───────── preempted / Gosched ─────────┐
                        ▼                                       │
    created ──▶ RUNNABLE ──(scheduler gives it a P)──▶ RUNNING ─┤
                   ▲                                            │
                   │                                            ├─ chan/select/mutex ─▶ BLOCKED ─┐
                   │                                            ├─ syscall ──────────▶ SYSCALL  ─┤
                   │                                            └─ network read ─────▶ NETPOLL  ─┤
                   └────────────────────── unblocked / returns ──────────────────────────────────┘

    time spent RUNNABLE = scheduler latency: ready to run, no CPU available

`go tool trace trace.out` opens a browser UI with:
  - a timeline per P (which goroutine ran where), GC and STW phases, syscalls;
  - goroutine analysis: per-goroutine breakdown of execution / network wait
    / sync block / syscall / scheduler wait time;
  - blocking profiles derived from the trace (network, sync, syscall,
    scheduler latency) in pprof format;
  - user-defined tasks and regions;
  - minimum mutator utilisation — how much CPU the application kept during
    GC.

Overhead: since Go 1.21's frame-pointer-based stack unwinding, tracing costs
roughly 1-2% CPU in typical programs (down from 10-20%). Measured for this
pipeline (Apple M4 Pro, go1.26):

    BenchmarkProcessOrdersTracingOff   2.754 ms/op   944 B/op   17 allocs/op
    BenchmarkProcessOrdersTracingOn    2.798 ms/op   935 B/op   21 allocs/op   (+1.6%)

MENTAL MODEL 5 — TASKS, REGIONS AND LOGS

	ctx, task := trace.NewTask(ctx, "processOrder")   // logical operation; can span goroutines
	defer task.End()
	trace.Logf(ctx, "order", "id=%d", id)             // key/value event attached to the task
	trace.WithRegion(ctx, "price", func() { ... })    // timed span on THIS goroutine

    task processOrder id=17  ├──────────────────────────────── 3.4ms ───────────────┤
      region validate        ├┤
      region price            ├──────── 2.1ms (running) ────────┤
      region persist                                             ├─ 1.1ms (blocked) ─┤

"User-defined tasks" in go tool trace shows a latency histogram of all
processOrder tasks; clicking the slow ones shows their regions and exactly
what each goroutine was doing (running, blocked on what, waiting for a P).
Tasks and regions are cheap when tracing is off — guard only expensive
argument formatting with trace.IsEnabled().

MENTAL MODEL 6 — THE FLIGHT RECORDER

    trace.Start/Stop:    you must be tracing BEFORE the problem happens

    FlightRecorder:      ┌── ring buffer: last ~N seconds / MaxBytes ──┐
                         │ ... events ... events ... events ... events │ ◀── always on
                         └─────────────────────────────────────────────┘
                                             │
      request exceeds 50ms threshold ────────┘ fr.WriteTo(w)
                                             ▼
                         snapshot containing the slow request AND what
                         the rest of the process was doing around it

SlowRequestCapture adds a rate limit (one snapshot per minGap): a latency
incident makes many requests slow at once, and one window contains them all.
Only one flight recorder can be active per process; it can run alongside a
trace.Start consumer.

MENTAL MODEL 7 — GOROUTINE LEAK DETECTION

	func LeakyFanOut(n int) int {
	    ch := make(chan int)            // unbuffered
	    for i := range n {
	        go func() { ch <- i }()     // n-1 of these block forever
	    }
	    return <-ch
	}

    goroutine profile (debug=1):
    19 @ 0x10044f2a8 0x1004173f4 ...
    #  0x1004173f3  runtime.chansend1+0x...
    #  0x1005d2b8f  goengineering/35_profiling_and_tracing/solution.LeakyFanOut.func1+0x...

Snapshot the count of goroutines in a function before and after an
operation (GoroutinesMatching). In production, export
runtime.NumGoroutine() as a metric and pull /debug/pprof/goroutine?debug=1
when it climbs; identical stacks with large counts are the leak. The
go.uber.org/goleak package automates the check in tests.

MENTAL MODEL 8 — SCHEDULER LATENCY AS A METRIC

/sched/latencies:seconds is a histogram of how long goroutines spent
runnable before running. It is cumulative since process start, so read it
before and after a window and subtract bucket counts:

    buckets:  [0,1µs) [1µs,2µs) ... [1ms,2ms) ... [+Inf)
    before:     120     340         ...    2
    after:      180     410         ...   61
    delta:       60      70         ...   59   ← p99 lives here under load

TestLesson_SchedulerLatencyUnderCPUSaturation measures 20 frequently-waking
goroutines on an idle runtime, then again with GOMAXPROCS=1 and 4 CPU-bound
goroutines competing for the single P. Measured here:

    idle   (GOMAXPROCS=12):              p50 ≈ 1.8 µs    p99 ≈ 20 µs
    loaded (GOMAXPROCS=1, 4 CPU hogs):   p50 ≈ 101 ms    p99 ≈ 134 ms

Four orders of magnitude of latency that no CPU profile would show — it
would just say "priceOrder is busy". (Values are histogram bucket upper
bounds, hence the powers-of-two-looking numbers.)

PRODUCTION WIRING

	import _ "net/http/pprof"   // registers /debug/pprof/* on http.DefaultServeMux

	go func() { log.Println(http.ListenAndServe("localhost:6060", nil)) }()

	curl -o cpu.pprof  'localhost:6060/debug/pprof/profile?seconds=30'
	curl -o heap.pprof  localhost:6060/debug/pprof/heap
	curl -o trace.out  'localhost:6060/debug/pprof/trace?seconds=5'
	curl 'localhost:6060/debug/pprof/goroutine?debug=2'

  - NEVER expose these on a public listener: they leak source paths and
    command lines, and a 30-second profile or trace request is a cheap DoS.
    Bind to localhost or an admin port behind auth.
  - Use a private ServeMux in real services and register pprof handlers
    explicitly (pprof.Index, pprof.Profile, pprof.Trace, ...).

SPEC

	type Order struct{ ID, Items int }
	type Result struct{ ID, Total int }
	func ProcessOrders(ctx context.Context, orders []Order, workers int) []Result
	    results[i] corresponds to orders[i]; one task "processOrder" per order,
	    regions "validate", "price", "persist"; persist sleeps 1ms.

	func TraceTo(w io.Writer, fn func()) error
	func ProfileCPU(w io.Writer, fn func()) error
	func ContentionProfile(fn func()) (string, error)   // mutex profile debug=1; restores fraction
	func BlockProfile(fn func()) (string, error)        // block profile debug=1; resets rate to 0
	func GoroutinesMatching(substr string) (int, error) // sum of counts of records whose stack contains substr

	func LeakyFanOut(n int) int        // lesson: leaks n-1 goroutines
	func FixedFanOut(n int) int        // buffered: no leak
	func ContendedWork(goroutines, iterations int) int64

	type SchedLatency struct{ P50, P99 time.Duration; Samples uint64 }
	func MeasureSchedLatency(fn func()) SchedLatency

	func NewSlowRequestCapture(threshold, minGap time.Duration, sink func([]byte)) (*SlowRequestCapture, error)
	func (c *SlowRequestCapture) Middleware(next http.Handler) http.Handler
	func (c *SlowRequestCapture) Stop()

ACCEPTANCE CRITERIA

  - `go test -v ./35_profiling_and_tracing/solution/...` passes:
      - the trace begins with the "go 1." header and names every task and region;
      - `go tool pprof -top` on the captured CPU profile lists priceOrder;
      - the mutex profile names ContendedWork;
      - LeakyFanOut(20) leaves exactly 19 goroutines, FixedFanOut none;
      - p99 scheduler latency rises under CPU saturation;
      - one slow request yields exactly one flight-recorder snapshot.

HOW TO RUN

	go test -v ./35_profiling_and_tracing/solution/...
	go test -run '^$' -bench ProcessOrders -benchmem ./35_profiling_and_tracing/solution/...

	# your own trace and profiles from the benchmark:
	go test -run '^$' -bench TracingOff -trace trace.out -cpuprofile cpu.pprof ./35_profiling_and_tracing/solution/
	go tool trace trace.out
	go tool pprof -http=:8080 cpu.pprof

HINTS

  - trace.Start returns an error if tracing is already on; always
    defer trace.Stop().
  - runtime.SetMutexProfileFraction returns the previous value — restore it.
  - Goroutine profile text: a record header is "N @ 0x...", stack lines start
    with "#".
  - metrics.Float64Histogram has len(Buckets) == len(Counts)+1; bucket i is
    [Buckets[i], Buckets[i+1]).
  - trace.NewFlightRecorder(trace.FlightRecorderConfig{MinAge, MaxBytes}),
    then Start, WriteTo, Stop.

COMMON PITFALLS

  - Profiling a benchmark with too few iterations: a 10 ms CPU profile has
    one sample.
  - Reading only flat% and missing the expensive caller (cum).
  - Looking for latency in a CPU profile when the time is spent blocked.
  - Leaving block/mutex profiling at rate 1 in production.
  - Forgetting trace.Stop → truncated, unreadable trace.
  - Opening giant traces: keep them to a few seconds, or use the flight
    recorder around the interesting moment.
  - Exposing /debug/pprof on the public port.

STRETCH GOALS

  - Add `-memprofile` to the benchmark and find the allocations in
    ProcessOrders with `go tool pprof -sample_index=alloc_objects`.
  - Serve the SlowRequestCapture snapshots on an admin endpoint and open
    one in go tool trace.
  - Collect a CPU profile of the benchmark, save it as default.pgo in a
    main package that calls ProcessOrders, and measure the PGO speedup.
*/

package tracing

import (
	"context"
	"io"
	"net/http"
	"time"
)

// ============================================================================
// 1. Instrumented pipeline
// ============================================================================

// Order is an input to the pipeline.
type Order struct {
	ID    int
	Items int
}

// Result is the priced order.
type Result struct {
	ID    int
	Total int
}

// ProcessOrders prices orders with a worker pool, instrumented with trace
// tasks and regions.
func ProcessOrders(ctx context.Context, orders []Order, workers int) []Result {
	// TODO: jobs channel of indices; workers read indices; per order:
	// trace.NewTask(ctx, "processOrder"); trace.Logf when trace.IsEnabled();
	// trace.WithRegion for "validate", "price" (priceOrder), "persist" (1ms sleep);
	// results[i] = ...; task.End().
	panic("not implemented")
}

// priceOrder burns CPU proportional to Items.
//
//go:noinline
func priceOrder(o Order) int {
	total := 0
	for i := range o.Items * 20_000 {
		total += (i*31 + o.ID) % 97
	}
	return total
}

// ============================================================================
// 2. Traces and profiles
// ============================================================================

// TraceTo records an execution trace of fn into w.
func TraceTo(w io.Writer, fn func()) error {
	// TODO: trace.Start(w); defer trace.Stop(); fn()
	panic("not implemented")
}

// ProfileCPU records a CPU profile of fn into w.
func ProfileCPU(w io.Writer, fn func()) error {
	// TODO: pprof.StartCPUProfile / StopCPUProfile
	panic("not implemented")
}

// ContentionProfile returns the mutex profile (debug=1) captured around fn.
func ContentionProfile(fn func()) (string, error) {
	// TODO: prev := runtime.SetMutexProfileFraction(1); defer restore; pprof.Lookup("mutex").WriteTo
	panic("not implemented")
}

// BlockProfile returns the block profile (debug=1) captured around fn.
func BlockProfile(fn func()) (string, error) {
	// TODO: runtime.SetBlockProfileRate(1); defer reset to 0.
	panic("not implemented")
}

// GoroutinesMatching counts goroutines whose stack contains substr.
func GoroutinesMatching(substr string) (int, error) {
	// TODO: parse pprof.Lookup("goroutine").WriteTo(&sb, 1).
	panic("not implemented")
}

// ============================================================================
// 3. Leaks and contention
// ============================================================================

// LeakyFanOut leaks n-1 goroutines. Lesson only — keep as is.
func LeakyFanOut(n int) int {
	ch := make(chan int)
	for i := range n {
		go func() { ch <- i }()
	}
	return <-ch
}

// FixedFanOut must not leak.
func FixedFanOut(n int) int {
	// TODO
	panic("not implemented")
}

// ContendedWork runs goroutines competing for one mutex.
func ContendedWork(goroutines, iterations int) int64 {
	// TODO: shared mutex held while looping 2,000 times per iteration.
	panic("not implemented")
}

// ============================================================================
// 4. Scheduler latency
// ============================================================================

// SchedLatency summarises runnable-wait time.
type SchedLatency struct {
	P50, P99 time.Duration
	Samples  uint64
}

// MeasureSchedLatency diffs the /sched/latencies:seconds histogram around fn.
func MeasureSchedLatency(fn func()) SchedLatency {
	// TODO
	panic("not implemented")
}

// ============================================================================
// 5. Flight recorder
// ============================================================================

// SlowRequestCapture snapshots a rolling trace when requests are slow.
type SlowRequestCapture struct {
	// TODO: fr *trace.FlightRecorder; threshold, minGap time.Duration;
	// sink func([]byte); last atomic.Int64; snapMu sync.Mutex
}

// NewSlowRequestCapture starts a flight recorder.
func NewSlowRequestCapture(threshold, minGap time.Duration, sink func(snapshot []byte)) (*SlowRequestCapture, error) {
	// TODO
	panic("not implemented")
}

// Middleware snapshots the recorder for requests slower than the threshold.
func (c *SlowRequestCapture) Middleware(next http.Handler) http.Handler {
	// TODO
	panic("not implemented")
}

// Stop stops the flight recorder.
func (c *SlowRequestCapture) Stop() {
	// TODO
	panic("not implemented")
}
