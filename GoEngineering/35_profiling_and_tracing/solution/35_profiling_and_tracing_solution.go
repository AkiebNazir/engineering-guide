// Package tracing is the reference solution for Problem 35 — Profiling &
// Tracing. It instruments a small order-processing pipeline and wraps the
// runtime's observability tools behind functions you can call from tests,
// admin endpoints, or incident tooling.
package tracing

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"io"
	"math"
	"net/http"
	"runtime"
	"runtime/metrics"
	"runtime/pprof"
	"runtime/trace"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

// ============================================================================
// 1. An instrumented pipeline (tasks, regions, logs)
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

// ProcessOrders prices orders with a pool of workers. Each order is a trace
// TASK (a logical operation that can hop goroutines), split into REGIONS
// (validate → price → persist) on the goroutine doing the work. In
// `go tool trace`, "User-defined tasks" then shows per-order latency
// broken down by region, and which regions spent their time running vs
// blocked vs waiting for a CPU.
//
// All of this costs almost nothing when tracing is off: NewTask/WithRegion
// check trace.IsEnabled() internally, and we guard trace.Logf ourselves so
// the fmt formatting doesn't run either.
func ProcessOrders(ctx context.Context, orders []Order, workers int) []Result {
	workers = max(workers, 1)
	results := make([]Result, len(orders))
	jobs := make(chan int)

	var wg sync.WaitGroup
	for range workers {
		wg.Go(func() {
			for i := range jobs {
				o := orders[i]
				tctx, task := trace.NewTask(ctx, "processOrder")
				if trace.IsEnabled() {
					trace.Logf(tctx, "order", "id=%d items=%d", o.ID, o.Items)
				}

				trace.WithRegion(tctx, "validate", func() {
					if o.Items <= 0 {
						o.Items = 1
					}
				})
				var total int
				trace.WithRegion(tctx, "price", func() { total = priceOrder(o) })          // CPU-bound
				trace.WithRegion(tctx, "persist", func() { time.Sleep(time.Millisecond) }) // blocking I/O stand-in

				results[i] = Result{ID: o.ID, Total: total}
				task.End()
			}
		})
	}
	for i := range orders {
		jobs <- i
	}
	close(jobs)
	wg.Wait()
	return results
}

// priceOrder burns CPU proportional to Items so it shows up in CPU profiles.
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
// 2. Capturing traces and profiles
// ============================================================================

// TraceTo records an execution trace of fn into w. Only one trace.Start can
// be active per process; a second returns an error (as would a concurrent
// /debug/pprof/trace request).
func TraceTo(w io.Writer, fn func()) error {
	if err := trace.Start(w); err != nil {
		return fmt.Errorf("tracing: start trace: %w", err)
	}
	defer trace.Stop() // flushes buffered events; forgetting it truncates the file
	fn()
	return nil
}

// ProfileCPU records a CPU profile of fn into w (pprof protobuf format).
// The profiler samples the running goroutines' stacks 100 times per second
// via SIGPROF, so fn must run for a while (hundreds of ms) to collect
// enough samples, and time spent BLOCKED never appears — that's what the
// block profile and the execution tracer are for.
func ProfileCPU(w io.Writer, fn func()) error {
	if err := pprof.StartCPUProfile(w); err != nil {
		return fmt.Errorf("tracing: start cpu profile: %w", err)
	}
	defer pprof.StopCPUProfile()
	fn()
	return nil
}

// ContentionProfile enables mutex-contention sampling for every event, runs
// fn, and returns the "mutex" profile in text form (debug=1). The profile
// attributes delay to the stack that UNLOCKED the mutex — the holder that
// made others wait — which is usually where to fix it.
func ContentionProfile(fn func()) (string, error) {
	prev := runtime.SetMutexProfileFraction(1) // 1 = record every contention event
	defer runtime.SetMutexProfileFraction(prev)
	fn()
	var sb strings.Builder
	if err := pprof.Lookup("mutex").WriteTo(&sb, 1); err != nil {
		return "", err
	}
	return sb.String(), nil
}

// BlockProfile enables blocking-event sampling, runs fn, and returns the
// "block" profile text: where goroutines waited on channels, select,
// sync primitives and timers.
func BlockProfile(fn func()) (string, error) {
	runtime.SetBlockProfileRate(1) // record every blocking event (costly: diagnostics only)
	defer runtime.SetBlockProfileRate(0)
	fn()
	var sb strings.Builder
	if err := pprof.Lookup("block").WriteTo(&sb, 1); err != nil {
		return "", err
	}
	return sb.String(), nil
}

// GoroutinesMatching counts live goroutines whose stack contains substr, by
// parsing the goroutine profile. This is the core of a goroutine-leak check:
// snapshot before and after an operation, compare.
//
// debug=1 format:
//
//	goroutine profile: total 7
//	3 @ 0x1004f1a8 0x100500c4 ...
//	#	0x1004f1a7	runtime.gopark+0x107	/usr/local/go/src/runtime/proc.go:435
//	#	0x100a2b1f	example.com/pkg.leaky.func1+0x2f	/src/pkg/x.go:42
func GoroutinesMatching(substr string) (int, error) {
	var sb strings.Builder
	if err := pprof.Lookup("goroutine").WriteTo(&sb, 1); err != nil {
		return 0, err
	}
	total, count, matched := 0, 0, false
	flush := func() {
		if matched {
			total += count
		}
		count, matched = 0, false
	}
	sc := bufio.NewScanner(strings.NewReader(sb.String()))
	for sc.Scan() {
		line := sc.Text()
		if n, _, ok := strings.Cut(line, " @ "); ok {
			flush()
			count, _ = strconv.Atoi(n)
			continue
		}
		if strings.HasPrefix(line, "#") && strings.Contains(line, substr) {
			matched = true
		}
	}
	flush()
	return total, sc.Err()
}

// ============================================================================
// 3. Goroutine leaks (for the profile-based leak test)
// ============================================================================

// LeakyFanOut asks n replicas and takes the first answer. The result channel
// is unbuffered and nobody reads after the first value, so n-1 goroutines
// block on their send forever. DO NOT USE — it exists to be caught.
func LeakyFanOut(n int) int {
	ch := make(chan int)
	for i := range n {
		go func() { ch <- i }()
	}
	return <-ch
}

// FixedFanOut is the same with a buffer of n: every sender completes.
func FixedFanOut(n int) int {
	ch := make(chan int, n)
	for i := range n {
		go func() { ch <- i }()
	}
	return <-ch
}

// ContendedWork runs goroutines that fight over one mutex, holding it while
// doing work — a textbook source of mutex-profile samples.
func ContendedWork(goroutines, iterations int) int64 {
	var mu sync.Mutex
	var total int64
	var wg sync.WaitGroup
	for range goroutines {
		wg.Go(func() {
			for range iterations {
				mu.Lock()
				for i := range 2_000 { // work under the lock: the actual bug
					total += int64(i & 1)
				}
				mu.Unlock()
			}
		})
	}
	wg.Wait()
	return total
}

// ============================================================================
// 4. Scheduler latency from runtime/metrics
// ============================================================================

// SchedLatency summarises how long goroutines sat RUNNABLE (ready, waiting
// for a P) before running — latency that neither CPU profiles nor
// "CPU usage" graphs show.
type SchedLatency struct {
	P50, P99 time.Duration
	Samples  uint64
}

// MeasureSchedLatency reads the /sched/latencies:seconds histogram before
// and after fn and summarises only the events that happened during fn.
func MeasureSchedLatency(fn func()) SchedLatency {
	const name = "/sched/latencies:seconds"
	read := func() *metrics.Float64Histogram {
		s := []metrics.Sample{{Name: name}}
		metrics.Read(s)
		return s[0].Value.Float64Histogram()
	}
	before := read()
	fn()
	after := read()

	// The histogram is cumulative since process start; subtract.
	delta := make([]uint64, len(after.Counts))
	var total uint64
	for i := range after.Counts {
		delta[i] = after.Counts[i] - before.Counts[i]
		total += delta[i]
	}
	quantile := func(q float64) time.Duration {
		if total == 0 {
			return 0
		}
		target := uint64(math.Ceil(q * float64(total)))
		var cum uint64
		for i, c := range delta {
			cum += c
			if cum >= target {
				// Buckets[i] and Buckets[i+1] bound bucket i; report the
				// upper bound (conservative), falling back to the lower one
				// for the final +Inf bucket.
				upper := after.Buckets[i+1]
				if math.IsInf(upper, 1) {
					upper = after.Buckets[i]
				}
				return time.Duration(upper * float64(time.Second))
			}
		}
		return 0
	}
	return SchedLatency{P50: quantile(0.50), P99: quantile(0.99), Samples: total}
}

// ============================================================================
// 5. Flight recorder: capture the trace of a slow request after the fact
// ============================================================================

// SlowRequestCapture keeps a rolling in-memory execution trace (Go 1.25's
// trace.FlightRecorder) and snapshots it whenever a request exceeds a
// threshold. Unlike trace.Start, which you must start BEFORE the problem, a
// flight recorder lets you ask "what just happened?" once you notice a slow
// request — the only practical way to trace rare production latency spikes.
type SlowRequestCapture struct {
	fr        *trace.FlightRecorder
	threshold time.Duration
	sink      func(snapshot []byte)
	minGap    time.Duration
	last      atomic.Int64 // unix nanos of the last snapshot
	snapMu    sync.Mutex   // WriteTo must not run concurrently
}

// ErrRecorderBusy is returned when another flight recorder is already active.
var ErrRecorderBusy = errors.New("tracing: flight recorder already active")

// NewSlowRequestCapture starts a flight recorder keeping roughly the last
// few seconds of execution. sink receives each snapshot (write it to a file
// or object storage). At most one snapshot is taken per minGap.
func NewSlowRequestCapture(threshold, minGap time.Duration, sink func(snapshot []byte)) (*SlowRequestCapture, error) {
	fr := trace.NewFlightRecorder(trace.FlightRecorderConfig{
		MinAge:   5 * time.Second,
		MaxBytes: 16 << 20,
	})
	if err := fr.Start(); err != nil {
		return nil, fmt.Errorf("%w: %v", ErrRecorderBusy, err)
	}
	return &SlowRequestCapture{fr: fr, threshold: threshold, sink: sink, minGap: minGap}, nil
}

// Middleware times each request and snapshots the recorder when one is slow.
func (c *SlowRequestCapture) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		if time.Since(start) >= c.threshold {
			c.snapshot()
		}
	})
}

func (c *SlowRequestCapture) snapshot() {
	now := time.Now().UnixNano()
	last := c.last.Load()
	// Rate limit: a latency incident makes MANY requests slow at once, and
	// one snapshot of the window already contains all of them.
	if last != 0 && time.Duration(now-last) < c.minGap {
		return
	}
	if !c.last.CompareAndSwap(last, now) {
		return // another request is taking this snapshot
	}
	c.snapMu.Lock()
	defer c.snapMu.Unlock()
	var sb strings.Builder
	if _, err := c.fr.WriteTo(&sb); err == nil {
		c.sink([]byte(sb.String()))
	}
}

// Stop stops the flight recorder.
func (c *SlowRequestCapture) Stop() { c.fr.Stop() }
