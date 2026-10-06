/*
Problem 12 — Worker Pool
========================

WHAT WE'RE BUILDING

Two complementary shapes of the same idea — running work with bounded
concurrency — because real services need both:

 1. RunBatch: you already have a fixed, known slice of jobs (e.g. "fetch
    these 500 user records") and want them run with at most N in flight,
    first error aborts the rest, results come back in input order.
 2. Pool: work arrives over time from unrelated callers (e.g. an HTTP
    handler enqueuing background jobs) and you want a long-lived pool of
    goroutines consuming from a shared queue, with graceful shutdown.

Both are "worker pools" in the colloquial sense, but conflating them causes
real bugs: a batch API that blocks forever waiting for a fixed number of
results doesn't compose with dynamic submission, and a dynamic pool sized
for a one-shot batch wastes goroutines idling on an empty channel. Building
both here, side by side, makes the distinction concrete.

WHY THIS MATTERS IN REAL SYSTEMS

  - Unbounded goroutine-per-item ("go func() {...}()" in a loop over 100k
    items) exhausts memory, file descriptors, or a downstream service's
    connection limit. Bounding concurrency is the single most common
    concurrency fix applied to real incident postmortems.
  - `errgroup.Group` gives you the two things you'd otherwise hand-roll
    error-prone: (a) a shared context that's canceled the moment ANY
    goroutine returns a non-nil error, so siblings can stop early, and
    (b) `Wait()` that blocks for all goroutines and returns the first error.
  - A pool that doesn't drain/close its channels on shutdown leaks
    goroutines forever — one of the most common resource leaks in
    long-running Go services, invisible until a pprof goroutine dump.
  - Result collection must preserve caller-meaningful order (batch) or be
    explicitly unordered-and-labeled (streaming) — never silently reorder
    without saying so.

CONCEPTS COVERED

  - Bounded concurrency via a semaphore pattern and via `errgroup.SetLimit`.
  - `context.Context` cancellation: caller cancels -> in-flight work stops
    accepting new items and returns promptly; one job's error cancels its
    siblings in RunBatch.
  - Goroutine lifecycle: every goroutine this package starts has a clear
    owner and a clear termination signal — no goroutine outlives the call
    that started it (verified by the tests via goroutine-count comparisons).
  - Result collection patterns: indexed slice (order-preserving, batch) vs.
    a results channel (arrival order, streaming).

# THE SPEC

Package `workerpool`.

	type Result[T any] struct {
	    Value T
	    Err   error
	}

	func RunBatch[T any](ctx context.Context, concurrency int, jobs []func(context.Context) (T, error)) ([]T, error)
	    - Runs all jobs with at most `concurrency` running at once (concurrency
	      <= 0 means "run all jobs' worth of goroutines simultaneously", i.e.
	      len(jobs), but never 0 workers for a non-empty jobs slice).
	    - Results returned in the SAME order as `jobs`, regardless of
	      completion order.
	    - On the first job error, remaining not-yet-started jobs are skipped
	      (their context is already canceled), already-running jobs finish or
	      observe cancellation via ctx, and RunBatch returns that first error
	      wrapped with context (nil []T is fine on error — caller should not
	      trust partial results on error, mirroring errgroup.Wait semantics).
	    - nil jobs / empty jobs returns (empty, non-nil, slice, nil error).

	type Pool[T any] struct { ... } // unexported fields

	func NewPool[T any](ctx context.Context, workers int) *Pool[T]
	    - workers <= 0 is a caller programming error; NewPool should treat it
	      as 1 (never start a pool with zero workers, which would deadlock
	      every Submit).
	    - Spawns `workers` goroutines (via an internal *errgroup.Group)
	      immediately; each pulls tasks off an internal channel and pushes a
	      Result[T] onto an internal results channel.
	    - ctx cancellation stops all workers: in-flight tasks may finish
	      naturally (they receive ctx too and should check it), but no new
	      task is pulled off the queue.

	func (p *Pool[T]) Submit(task func(context.Context) (T, error)) error
	    - Enqueues a task. Returns ctx.Err() (without blocking forever) if the
	      pool's context is already canceled. Safe to call from multiple
	      goroutines concurrently.

	func (p *Pool[T]) Results() <-chan Result[T]
	    - Returns the channel results are delivered on, in COMPLETION order
	      (not submission order — that's the streaming/batch distinction).
	      Closed automatically once CloseAndWait has drained all workers.

	func (p *Pool[T]) CloseAndWait() error
	    - Signals no more tasks will be submitted, waits for all in-flight and
	      already-queued tasks to finish, closes the Results() channel, and
	      returns the first error encountered starting a worker goroutine
	      itself (not task errors — those arrive via Results()). Safe to call
	      exactly once; calling Submit after CloseAndWait must return an error
	      rather than panic.

ACCEPTANCE CRITERIA

  - RunBatch with concurrency=1 behaves like running jobs sequentially
    (results still in order, but so is execution — useful for testing).
  - RunBatch never has more than `concurrency` job functions actually
    executing at once (verified with an atomic in-flight counter in tests).
  - RunBatch's first error cancels the shared context so jobs that check
    ctx.Err() stop promptly instead of running to completion needlessly.
  - Pool.Submit after CloseAndWait returns an error, never panics or blocks
    forever.
  - Goroutine count returns to its pre-test baseline after every test
    (checked via runtime.NumGoroutine() with a short settle loop, since
    goroutine teardown isn't instantaneous).
  - Everything passes `go test -race`.

HINTS

  - The semaphore pattern: `sem := make(chan struct{}, concurrency)`;
    acquire with `sem <- struct{}{}`, release with `<-sem` in a defer.
    `errgroup.Group.SetLimit(n)` does exactly this internally — prefer it
    over hand-rolling when you're already using errgroup for error
    aggregation, which RunBatch is.
  - `errgroup.WithContext(ctx)` gives you back a derived context that is
    canceled the moment any goroutine in the group returns a non-nil error
    — pass THAT derived context into each job, not the original ctx.
  - For Pool, closing the *task* channel is how workers know to stop pulling
    (range over it exits when closed+drained); closing the *results* channel
    must happen only after every worker has exited, which is exactly what
    `errgroup.Wait()` returning tells you — spawn one more goroutine whose
    only job is `eg.Wait(); close(results)`.
  - `sync.Once` guards CloseAndWait against being called twice (closing an
    already-closed channel panics).

COMMON PITFALLS

  - Closing the results channel while workers might still send on it — the
    classic "send on closed channel" panic. Order matters: stop accepting
    new tasks -> close task channel -> wait for workers -> THEN close
    results.
  - Using the original (non-errgroup-derived) ctx inside job functions in
    RunBatch — then one job's error never cancels its siblings.
  - Forgetting that `concurrency <= 0` for RunBatch must not mean "0
    workers" (permanent deadlock) — it should mean "unbounded" for that call.
  - Leaking the internal goroutine that waits on eg.Wait() to close results
    — it exits on its own once workers finish, but only if workers
    themselves are guaranteed to terminate (which requires the task channel
    to actually get closed by CloseAndWait).

STRETCH GOALS

  - Add per-task timeouts via `context.WithTimeout` layered on top of the
    pool's ctx, independent per submitted task.
  - Add a `TrySubmit` that returns immediately (non-blocking) if the task
    queue is full instead of blocking the caller.
  - Add metrics: tasks submitted/completed/failed counters, exposed via an
    accessor method, useful for a `/debug/vars`-style endpoint.
  - Generalize RunBatch to support a `FailFast bool` option: when false,
    collect ALL job errors (e.g. via a joined error) instead of stopping at
    the first.
*/
package workerpool

import (
	"context"
)

// Result pairs a job's output with any error it returned.
type Result[T any] struct {
	Value T
	Err   error
}

// RunBatch runs jobs with at most `concurrency` executing concurrently,
// returning results in the same order as jobs. See the header comment for
// the full contract.
func RunBatch[T any](ctx context.Context, concurrency int, jobs []func(context.Context) (T, error)) ([]T, error) {
	panic("TODO: implement RunBatch")
}

// Pool is a long-lived, bounded-concurrency worker pool that accepts tasks
// submitted over time and delivers results as they complete.
type Pool[T any] struct {
	// TODO: unexported fields — tasks chan, results chan, *errgroup.Group,
	// context/cancel, sync.Once for shutdown.
}

// NewPool starts `workers` goroutines (minimum 1) consuming tasks until ctx
// is canceled or CloseAndWait is called.
func NewPool[T any](ctx context.Context, workers int) *Pool[T] {
	panic("TODO: implement NewPool")
}

// Submit enqueues task for execution. Returns an error instead of blocking
// forever if the pool's context is canceled or the pool has been closed.
func (p *Pool[T]) Submit(task func(context.Context) (T, error)) error {
	panic("TODO: implement Submit")
}

// Results returns the channel on which completed Results are delivered, in
// completion order. It is closed once CloseAndWait has drained all workers.
func (p *Pool[T]) Results() <-chan Result[T] {
	panic("TODO: implement Results")
}

// CloseAndWait stops accepting new tasks, waits for all queued and
// in-flight tasks to finish, and closes the Results channel. Safe to call
// exactly once.
func (p *Pool[T]) CloseAndWait() error {
	panic("TODO: implement CloseAndWait")
}
