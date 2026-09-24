/*
Problem 28 — Scheduler & GC Tuning (GMP model, preemption, stack growth,
GOGC, GOMEMLIMIT, GOMAXPROCS, runtime/metrics)

WHAT WE'RE BUILDING

A small "runtime lab" package that lets you change the Go runtime's knobs
from code, run a workload, and MEASURE what changed — instead of copying
GOGC=200 from a blog post:

 1. MeasureGC(gcPercent, memLimit, fn) — runs fn under a given GOGC and
    GOMEMLIMIT, restores the previous settings, and returns GC cycles,
    total pause time, bytes allocated and final heap goal.
 2. Churn(total, size, live) — a controllable allocation workload: total
    allocations of `size` bytes while keeping only `live` of them
    reachable, so "live heap" is a number you choose.
 3. WithGOMAXPROCS(n, fn) + CountPrimes(limit, workers) — CPU-bound work
    to observe parallel speedup as GOMAXPROCS changes.
 4. ReadSnapshot() — the runtime's current configuration via runtime,
    runtime/debug and runtime/metrics (GOGC, memory limit, heap goal,
    starting goroutine stack size, GOMAXPROCS).
 5. MemoryLimitFor + ParseCgroupMemoryMax — derive a GOMEMLIMIT from a
    container's cgroup memory limit with headroom.
 6. SpinUntil / Recurse — probes used by tests that prove asynchronous
    preemption and goroutine stack growth (and the stack limit) at runtime.

WHY THIS MATTERS IN REAL SYSTEMS

Three production incidents every Go team eventually has:

  - "The pod keeps getting OOMKilled but the Go heap is only 300 MB."
    GOGC=100 lets the heap grow to 2x live before collecting; with a
    350 MB live heap and a 512 MiB container limit, the next GC comes too
    late. GOMEMLIMIT fixes exactly this.
  - "p99 latency is terrible on a 64-core node, but CPU is idle."
    Before Go 1.25, GOMAXPROCS defaulted to the HOST's core count even
    inside a container with a 2-CPU quota: 64 Ps fighting over 2 CPUs of
    CFS quota → throttling → latency spikes. Go 1.25+ reads the cgroup CPU
    limit on Linux; older services used go.uber.org/automaxprocs.
  - "GC is eating 30% of CPU." Usually allocation rate, not the GC: fix
    allocations first (Problem 22), then raise GOGC or set GOGC=off plus
    GOMEMLIMIT if memory is plentiful.

MENTAL MODEL 1 — THE GMP SCHEDULER

  G = goroutine (a stack + an instruction pointer + status)
  M = machine: an OS thread
  P = processor: the right to run Go code. Exactly GOMAXPROCS of them.
      Each P owns a local run queue (256 slots) and an mcache for
      lock-free small allocations.

    global run queue [G G]              netpoller (kqueue / epoll)
            │                                 │ goroutines whose sockets
            │ checked every 61 ticks          │ became ready
    ┌───────┴──────────────┬──────────────────┴─────────────┐
    ▼                      ▼                                ▼
  ┌────┐ runq [G G G G]  ┌────┐ runq [G]                 ┌────┐ runq [ ]
  │ P0 │                 │ P1 │                          │ P2 │──steal half of P0's runq
  └─┬──┘                 └─┬──┘                          └─┬──┘
    │                      │                               │
  ┌─▼──┐                 ┌─▼──┐   blocking syscall        ┌─▼──┐
  │ M0 │ running G       │ M1 │── P1 handed off to ──▶    │ M2 │
  └────┘                 └────┘   an idle/new M           └────┘

  sysmon: a dedicated M with no P. Every 20µs–10ms it retakes Ps stuck in
  syscalls, preempts goroutines that ran > 10ms, and polls the network.

Key consequences:
  - A goroutine blocked on a channel, mutex or network read costs no
    thread: it is parked and its P runs something else.
  - A goroutine blocked in a SYSCALL or cgo call holds its M; the P moves
    to another M. That is why thousands of blocking file reads create
    thousands of threads, but thousands of socket reads do not.
  - runtime.GOMAXPROCS(n) stops the world. Call it at startup, not per
    request.

MENTAL MODEL 2 — PREEMPTION

    Go ≤ 1.13: cooperative only. Preemption checks lived in function
    prologues (the stack-growth check). A loop with no function calls
    could never be preempted:

        go func() { for { i++ } }()   // with GOMAXPROCS=1 this starved
                                      // every other goroutine forever

    Go ≥ 1.14: asynchronous preemption. sysmon notices a G running > 10ms
    and sends its thread a signal (SIGURG); the signal handler parks the
    goroutine at a safe point.

    time ──────────────────────────────────────────────────────▶
    P0:  [ spinner G ██████████▌ ]──SIGURG──▶[ main G ]─▶[ spinner ]
                                ▲
                  sysmon: "running > 10ms, preempt"

The test file re-runs a tight loop in a child process with GOMAXPROCS=1.
Measured here: with defaults the child finishes in ~43 ms (the spinner
did ~172 million iterations before being preempted); with
GODEBUG=asyncpreemptoff=1 it was still hung after 2 s and was killed.

And GOMAXPROCS matters only for parallel CPU work: CountPrimes(3,000,000)
split across 12 goroutines took 166 ms with GOMAXPROCS=1 and 25 ms with
GOMAXPROCS=12 (6.6x) — same goroutines, different number of Ps.

MENTAL MODEL 3 — GOROUTINE STACKS GROW BY COPYING

    new goroutine: small stack (the runtime tracks the average stack
    size and starts new goroutines near it; /gc/stack/starting-size:bytes
    reports it, typically 2 KB on a fresh process)

    ┌──────┐   function prologue: "is there room for my frame?"
    │ 2 KB │── no ──▶ allocate 4 KB, COPY the whole stack, fix up
    └──────┘          every pointer into it, free the old one
                      ┌──────────┐
                      │   4 KB   │── ... 8 KB ... up to the max
                      └──────────┘

  - Max stack is 1 GB on 64-bit (debug.SetMaxStack changes it).
    Exceeding it is "fatal error: stack overflow" — NOT a panic, recover()
    cannot catch it, the process dies.
  - Because stacks move, you cannot keep a uintptr to a stack variable,
    and pointers to stack memory can't be passed to C (Problem 27).
  - Deep recursion is fine in Go in a way it isn't in Python or C with
    8 MB thread stacks — but every growth is a copy, so a hot path that
    repeatedly grows and shrinks a stack pays for it.

MENTAL MODEL 4 — THE GC CYCLE AND THE PACER

Go's GC is a concurrent, non-moving, tri-colour mark-sweep collector.

    ┌─────────────┐  ┌──────────────────────────────┐  ┌────────────┐  ┌──────────────┐
    │ sweep term. │─▶│ MARK (concurrent)            │─▶│ mark term. │─▶│ SWEEP        │
    │ STW ~10-50µs│  │ write barrier ON             │  │ STW 10-50µs│  │ (concurrent, │
    └─────────────┘  │ 25% of GOMAXPROCS dedicated  │  └────────────┘  │  lazy)       │
                     │ + mutator "assists" when a G │                  └──────────────┘
                     │   allocates faster than GC   │
                     └──────────────────────────────┘

When does a cycle start? When the heap reaches the HEAP GOAL:

    heap goal = live heap + (live heap + GC roots) × GOGC / 100
                (GC roots = goroutine stacks + globals, since Go 1.18)
    with a floor of 4 MB × GOGC/100

    GOGC=100, 200 MB live:  goal ≈ 400 MB  ─ collect when heap doubles
    GOGC=50,  200 MB live:  goal ≈ 300 MB  ─ more cycles, less memory
    GOGC=400, 200 MB live:  goal ≈ 1 GB    ─ fewer cycles, more memory
    GOGC=off:               no goal        ─ never collects (unless GOMEMLIMIT)

The trade-off is purely CPU vs memory. Total GC CPU is roughly
proportional to (number of cycles) × (live heap to mark), so halving the
number of cycles roughly halves GC CPU at the cost of peak memory.

Measured by TestLowerGOGCRunsMoreCycles on this machine (Apple M4 Pro,
12 P, go1.26) — the same Churn workload, 125 MB allocated, ~4 MB live:

    GOGC=25    72 cycles   3.39 ms total STW pause
    GOGC=100   23 cycles   1.07 ms
    GOGC=400    6 cycles   0.29 ms

And TestMemoryLimitRescuesGOGCOff (64 MB allocated, ~1 MB live):

    GOGC=off                     0 cycles  (heap simply grows)
    GOGC=off + GOMEMLIMIT=24MiB  5 cycles  (limit-driven collections only)

MENTAL MODEL 5 — GOMEMLIMIT: A SOFT CEILING

    memory
      ▲                                     GOMEMLIMIT ─ ─ ─ ─ ─ ─ ─ ─
      │           GOGC goal ╱╲      ╱╲           ╱╲╱╲╱╲╱╲╱╲  ← GC runs more often
      │                   ╱    ╲  ╱    ╲       ╱            as the limit nears
      │        ╱╲       ╱        ╲╱      ╲   ╱
      │      ╱    ╲   ╱                    ╲╱
      │    ╱        ╲╱
      └──────────────────────────────────────────────────────────▶ time

  - The limit counts ALL runtime-managed memory (heap, stacks, runtime
    metadata), not RSS from cgo/mmap.
  - Soft: if live data truly exceeds the limit the runtime keeps running
    rather than thrash — GC CPU is capped (about 50% of CPU) to avoid a
    death spiral. You still get OOM-killed; you just don't lock up first.
  - Pattern for a container with a known budget:
    GOMEMLIMIT ≈ 90% of the container limit, GOGC left at 100 (or GOGC=off
    when the live heap is small relative to the limit and you want the
    fewest possible cycles).

READING GODEBUG=gctrace=1 (REAL OUTPUT FROM THIS MACHINE)

	gc 5 @0.013s 5%: 0.38+0.78+0.017 ms clock, 4.6+0.75/1.7/0.13+0.21 ms cpu, 3->4->2 MB, 4 MB goal, 0 MB stacks, 0 MB globals, 12 P

    gc 5                 fifth cycle since start
    @0.013s              13ms after process start
    5%                   share of CPU spent in GC since start
    0.38+0.78+0.017 ms   wall clock: STW sweep-term + concurrent mark + STW mark-term
    4.6+0.75/1.7/0.13+0.21 ms cpu
                         CPU: STW + (assist / background / idle mark) + STW
    3->4->2 MB           heap at GC start -> heap at mark end -> LIVE heap
    4 MB goal            heap goal for this cycle (here the 4 MB floor)
    12 P                 GOMAXPROCS

And GODEBUG=schedtrace=1000 prints scheduler state every second:

	SCHED 5ms: gomaxprocs=12 idleprocs=11 threads=14 spinningthreads=0 needspinning=0 idlethreads=12 runqueue=0 [0 0 0 0 0 0 0 0 0 0 0 0]

runqueue is the global queue; the bracketed list is each P's local queue.
Large, persistent per-P queues mean goroutines are waiting for CPU.

TUNING DECISION TABLE

    | Symptom                                   | First knob                          |
    |-------------------------------------------|-------------------------------------|
    | OOMKilled, heap << container limit        | GOMEMLIMIT = ~90% of limit          |
    | High GC CPU, memory to spare              | raise GOGC (200-400) or GOGC=off +  |
    |                                           | GOMEMLIMIT                          |
    | Memory tight, CPU to spare                | lower GOGC (50)                     |
    | CPU throttling in containers, Go < 1.25   | automaxprocs / set GOMAXPROCS       |
    | Latency spikes, low CPU                   | trace (Problem 35), not GC knobs    |
    | GC CPU high because allocation rate high  | reduce allocations (Problem 22)     |

SPEC

	type GCStats struct {
	    Cycles     uint32        // GC cycles completed during fn
	    PauseTotal time.Duration // total stop-the-world pause during fn
	    Allocated  uint64        // bytes allocated during fn
	    HeapGoal   uint64        // heap goal after fn (runtime/metrics)
	    Elapsed    time.Duration
	}
	func MeasureGC(gcPercent int, memLimit int64, fn func()) GCStats
	    Forces a GC first (clean baseline), applies gcPercent (-1 = off) and
	    memLimit (<= 0 = no limit), runs fn, restores BOTH previous settings.

	func Churn(total, size, live int)  // live >= 1
	func WithGOMAXPROCS(n int, fn func())  // restores previous value
	func CountPrimes(limit, workers int) int  // primes < limit, trial division, split across workers

	type Snapshot struct {
	    GOMAXPROCS, NumCPU, NumGoroutine int
	    GCPercent            int64   // from /gc/gogc:percent
	    MemoryLimit          uint64  // from /gc/gomemlimit:bytes
	    HeapGoal             uint64  // from /gc/heap/goal:bytes
	    StartingStackSize    uint64  // from /gc/stack/starting-size:bytes
	}
	func ReadSnapshot() Snapshot

	func ParseCgroupMemoryMax(content string) (int64, bool)  // "max" → false
	func MemoryLimitFor(containerBytes int64, headroomPercent int) int64

	func SpinUntil(stop *atomic.Bool) uint64  // tight loop, no function calls; returns iterations
	func Recurse(depth int) int               // recursion with a non-trivial frame; returns depth

ACCEPTANCE CRITERIA

  - `go test -v ./28_scheduler_and_gc_tuning/solution/...` passes and logs:
      - GOGC=25 runs several times more GC cycles than GOGC=400 on the
        same workload;
      - GOGC=off runs 0 cycles, and GOGC=off + a small GOMEMLIMIT runs > 0;
      - a tight loop with GOMAXPROCS=1 lets another goroutine run
        (async preemption) and hangs with asyncpreemptoff=1;
      - 100k-deep recursion succeeds on a goroutine, and a lowered
        debug.SetMaxStack produces a fatal stack overflow in a child process.
  - Every test restores GOGC, GOMEMLIMIT and GOMAXPROCS.

HOW TO RUN

	go test -v ./28_scheduler_and_gc_tuning/solution/...
	go test -run Example -v ./28_scheduler_and_gc_tuning/solution/...
	GODEBUG=gctrace=1 go test -run TestLowerGOGC ./28_scheduler_and_gc_tuning/solution/ 2>&1 | head
	GOGC=off GOMEMLIMIT=64MiB go run yourprog.go

HINTS

  - debug.SetGCPercent and debug.SetMemoryLimit both RETURN the previous
    value — capture it and defer the restore. SetMemoryLimit(math.MaxInt64)
    means "no limit"; a negative input only reads the current value.
  - runtime.ReadMemStats gives NumGC, PauseTotalNs, TotalAlloc. It briefly
    stops the world, so don't call it per request; runtime/metrics is the
    cheap, modern API.
  - Churn: a ring buffer `keep := make([][]byte, live)` and
    `keep[i%live] = make([]byte, size)` keeps exactly `live` buffers alive.
  - SpinUntil must not call any function inside the loop; stop.Load() is a
    compiler intrinsic, so it doesn't count.

COMMON PITFALLS

  - Setting GOGC very high "for performance" in a container with no
    GOMEMLIMIT: the next spike doubles your heap and the kernel kills you.
  - GOMEMLIMIT set to 100% of the container limit: non-heap memory (cgo,
    thread stacks, page cache in some accounting) pushes you over anyway.
  - Setting GOMAXPROCS higher than available CPU quota: more Ps just means
    more context switching and CFS throttling.
  - Treating runtime.GC() as a fix. It is a synchronous, full, blocking
    collection; calling it in request paths destroys latency.
  - Reading MemStats.HeapAlloc once and calling it "memory usage"; RSS also
    includes stacks, fragmentation and memory not yet returned to the OS.

STRETCH GOALS

  - Record /sched/latencies:seconds (a histogram of time goroutines spent
    runnable before running) under GOMAXPROCS=1 vs NumCPU with 1000 busy
    goroutines.
  - Build a tiny HTTP server, load it, and compare p99 latency with
    GOGC=50, 100, 400 and GOGC=off+GOMEMLIMIT.
  - Plot heap size over time from runtime/metrics sampled every 10ms with
    and without a memory limit.
*/

package rtune

import (
	"sync/atomic"
	"time"
)

// GCStats summarises garbage-collector activity during a measured function.
type GCStats struct {
	Cycles     uint32
	PauseTotal time.Duration
	Allocated  uint64
	HeapGoal   uint64
	Elapsed    time.Duration
}

// MeasureGC runs fn under the given GOGC percentage and memory limit.
func MeasureGC(gcPercent int, memLimit int64, fn func()) GCStats {
	// TODO: runtime.GC(); prevPct := debug.SetGCPercent(gcPercent)
	// TODO: prevLimit := debug.SetMemoryLimit(memLimit or math.MaxInt64); defer restore both
	// TODO: ReadMemStats before/after; read /gc/heap/goal:bytes after.
	panic("not implemented")
}

// Churn performs total allocations of size bytes, keeping live of them reachable.
func Churn(total, size, live int) {
	// TODO: ring buffer of `live` slices.
	panic("not implemented")
}

// WithGOMAXPROCS runs fn with GOMAXPROCS set to n, then restores it.
func WithGOMAXPROCS(n int, fn func()) {
	// TODO
	panic("not implemented")
}

// CountPrimes counts primes below limit using trial division across workers goroutines.
func CountPrimes(limit, workers int) int {
	// TODO: split [2, limit) into `workers` ranges; sum counts.
	panic("not implemented")
}

// Snapshot is the runtime's current configuration and state.
type Snapshot struct {
	GOMAXPROCS        int
	NumCPU            int
	NumGoroutine      int
	GCPercent         int64
	MemoryLimit       uint64
	HeapGoal          uint64
	StartingStackSize uint64
}

// ReadSnapshot reads the current runtime configuration.
func ReadSnapshot() Snapshot {
	// TODO: runtime.GOMAXPROCS(0), runtime.NumCPU(), runtime.NumGoroutine(),
	// metrics.Read for the four metric names in the SPEC.
	panic("not implemented")
}

// ParseCgroupMemoryMax parses the content of cgroup v2 memory.max.
func ParseCgroupMemoryMax(content string) (int64, bool) {
	// TODO: trim; "max" → 0,false; otherwise strconv.ParseInt.
	panic("not implemented")
}

// MemoryLimitFor returns a GOMEMLIMIT leaving headroomPercent of containerBytes free.
func MemoryLimitFor(containerBytes int64, headroomPercent int) int64 {
	// TODO
	panic("not implemented")
}

// SpinUntil loops without function calls until stop is set.
func SpinUntil(stop *atomic.Bool) uint64 {
	// TODO: var n uint64; for !stop.Load() { n++ }; return n
	panic("not implemented")
}

// Recurse recurses depth times with a non-trivial stack frame.
func Recurse(depth int) int {
	// TODO: var pad [128]byte; if depth == 0 { return int(pad[0]) }; return 1 + Recurse(depth-1)
	panic("not implemented")
}
