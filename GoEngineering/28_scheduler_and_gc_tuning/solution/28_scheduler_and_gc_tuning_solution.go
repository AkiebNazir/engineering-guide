// Package rtune is the reference solution for Problem 28 — Scheduler & GC
// Tuning. Every function that changes a global runtime setting restores it,
// because these knobs are process-wide: a test (or a library!) that forgets
// to restore GOGC silently changes the behaviour of everything else.
package rtune

import (
	"math"
	"runtime"
	"runtime/debug"
	"runtime/metrics"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

// ============================================================================
// 1. Measuring the GC under different settings
// ============================================================================

// GCStats summarises garbage-collector activity during a measured function.
type GCStats struct {
	Cycles     uint32
	PauseTotal time.Duration
	Allocated  uint64
	HeapGoal   uint64
	Elapsed    time.Duration
}

// MeasureGC runs fn with GOGC=gcPercent (negative = off) and a soft memory
// limit of memLimit bytes (<= 0 = no limit), then restores both settings.
func MeasureGC(gcPercent int, memLimit int64, fn func()) GCStats {
	// Start from a clean slate: garbage left by earlier code would otherwise
	// trigger (or delay) the first cycle inside fn and skew the count.
	runtime.GC()

	if memLimit <= 0 {
		memLimit = math.MaxInt64 // the runtime's own "no limit" value
	}
	prevPct := debug.SetGCPercent(gcPercent)
	prevLimit := debug.SetMemoryLimit(memLimit)
	defer func() {
		debug.SetMemoryLimit(prevLimit)
		debug.SetGCPercent(prevPct)
	}()

	var before, after runtime.MemStats
	runtime.ReadMemStats(&before) // stops the world briefly: fine for a lab, not per request
	start := time.Now()
	fn()
	elapsed := time.Since(start)
	runtime.ReadMemStats(&after)

	return GCStats{
		Cycles:     after.NumGC - before.NumGC,
		PauseTotal: time.Duration(after.PauseTotalNs - before.PauseTotalNs),
		Allocated:  after.TotalAlloc - before.TotalAlloc,
		HeapGoal:   readUint64("/gc/heap/goal:bytes"),
		Elapsed:    elapsed,
	}
}

// Churn performs total allocations of size bytes while keeping only the most
// recent live of them reachable, so the live heap stays ≈ live×size while the
// allocation volume is total×size.
func Churn(total, size, live int) {
	if live < 1 {
		live = 1
	}
	keep := make([][]byte, live)
	for i := range total {
		b := make([]byte, size) // size is not a constant → heap allocation
		b[0] = byte(i)          // touch it so the OS actually backs the page
		keep[i%live] = b        // overwrites (and so frees) the oldest buffer
	}
	runtime.KeepAlive(keep)
}

// ============================================================================
// 2. GOMAXPROCS and parallel CPU work
// ============================================================================

// WithGOMAXPROCS runs fn with GOMAXPROCS set to n, then restores it.
// GOMAXPROCS changes stop the world — configure at startup, not per request.
func WithGOMAXPROCS(n int, fn func()) {
	prev := runtime.GOMAXPROCS(n)
	defer runtime.GOMAXPROCS(prev)
	fn()
}

// CountPrimes counts primes in [2, limit) by trial division, splitting the
// range across workers goroutines. Goroutines are cheap to create, but they
// only run in parallel up to GOMAXPROCS — spawning 64 workers with
// GOMAXPROCS=1 gives concurrency, not parallelism.
func CountPrimes(limit, workers int) int {
	if limit <= 2 {
		return 0
	}
	if workers < 1 {
		workers = 1
	}
	var total atomic.Int64
	var wg sync.WaitGroup
	chunk := (limit - 2 + workers - 1) / workers
	for lo := 2; lo < limit; lo += chunk {
		hi := min(lo+chunk, limit)
		wg.Go(func() {
			n := 0
			for v := lo; v < hi; v++ {
				if isPrime(v) {
					n++
				}
			}
			total.Add(int64(n))
		})
	}
	wg.Wait()
	return int(total.Load())
}

func isPrime(v int) bool {
	if v < 2 {
		return false
	}
	for d := 2; d*d <= v; d++ {
		if v%d == 0 {
			return false
		}
	}
	return true
}

// ============================================================================
// 3. Observing the runtime
// ============================================================================

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

// ReadSnapshot reads the current runtime configuration. runtime/metrics is
// the stable, cheap interface (no stop-the-world, unlike ReadMemStats), and
// unlike debug.SetGCPercent it lets you READ GOGC without writing it.
func ReadSnapshot() Snapshot {
	samples := []metrics.Sample{
		{Name: "/gc/gogc:percent"},
		{Name: "/gc/gomemlimit:bytes"},
		{Name: "/gc/heap/goal:bytes"},
		{Name: "/gc/stack/starting-size:bytes"},
	}
	metrics.Read(samples)
	u := func(i int) uint64 {
		// A metric missing from this Go version reads as KindBad; calling
		// Uint64 on it would panic.
		if samples[i].Value.Kind() != metrics.KindUint64 {
			return 0
		}
		return samples[i].Value.Uint64()
	}
	return Snapshot{
		GOMAXPROCS:        runtime.GOMAXPROCS(0), // 0 = query without changing
		NumCPU:            runtime.NumCPU(),
		NumGoroutine:      runtime.NumGoroutine(),
		GCPercent:         int64(u(0)), // GOGC=off reports as 0 here
		MemoryLimit:       u(1),
		HeapGoal:          u(2),
		StartingStackSize: u(3),
	}
}

func readUint64(name string) uint64 {
	s := []metrics.Sample{{Name: name}}
	metrics.Read(s)
	if s[0].Value.Kind() != metrics.KindUint64 {
		return 0
	}
	return s[0].Value.Uint64()
}

// ============================================================================
// 4. Container memory budgets
// ============================================================================

// ParseCgroupMemoryMax parses the content of a cgroup v2 memory.max file
// (/sys/fs/cgroup/memory.max). "max" means unlimited.
func ParseCgroupMemoryMax(content string) (int64, bool) {
	s := strings.TrimSpace(content)
	if s == "" || s == "max" {
		return 0, false
	}
	n, err := strconv.ParseInt(s, 10, 64)
	if err != nil || n <= 0 {
		return 0, false
	}
	return n, true
}

// MemoryLimitFor returns a GOMEMLIMIT that leaves headroomPercent of the
// container's memory for things the Go runtime doesn't count: cgo/C
// allocations, memory-mapped files, and the gap between runtime accounting
// and the kernel's RSS accounting.
func MemoryLimitFor(containerBytes int64, headroomPercent int) int64 {
	headroomPercent = min(max(headroomPercent, 0), 100)
	return containerBytes - containerBytes*int64(headroomPercent)/100
}

// ============================================================================
// 5. Probes for preemption and stack growth
// ============================================================================

// SpinUntil loops until stop is set. The loop body contains no function
// calls (atomic.Bool.Load is a compiler intrinsic), so it has no cooperative
// preemption point: only asynchronous, signal-based preemption can take the
// CPU away from it.
func SpinUntil(stop *atomic.Bool) uint64 {
	var n uint64
	for !stop.Load() {
		n++
	}
	return n
}

// Recurse recurses depth times with a ~128-byte frame, forcing the goroutine
// stack to grow (by allocating a bigger stack and copying) many times.
//
//go:noinline
func Recurse(depth int) int {
	var pad [128]byte
	pad[depth%len(pad)] = 1 // use pad so the frame is really there
	if depth == 0 {
		return 0
	}
	return 1 + Recurse(depth-1) + int(pad[0]&0)
}
