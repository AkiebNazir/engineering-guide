/*
Problem 12 — Worker Pool (solution)
====================================

Reference implementation for both shapes specified in
explanation/12_worker_pool_explanation.go: RunBatch (fixed batch, ordered
results, first-error-cancels) and Pool (long-lived, dynamic submission,
completion-order results). See that file for the full spec and rationale.
*/
package workerpool

import (
	"context"
	"fmt"
	"sync"

	"golang.org/x/sync/errgroup"
)

// Result pairs a job's output with any error it returned.
type Result[T any] struct {
	Value T
	Err   error
}

// RunBatch runs jobs with at most `concurrency` executing concurrently. The
// returned slice mirrors the input order regardless of completion order,
// which is why each job writes directly into its own pre-allocated index
// rather than being collected off a channel.
func RunBatch[T any](ctx context.Context, concurrency int, jobs []func(context.Context) (T, error)) ([]T, error) {
	results := make([]T, len(jobs))
	if len(jobs) == 0 {
		return results, nil
	}

	if concurrency <= 0 {
		concurrency = len(jobs)
	}

	// errgroup.WithContext gives us a derived context that is canceled the
	// instant any goroutine in the group returns a non-nil error. Every job
	// gets THIS context, not the caller's original one, so one job's
	// failure promptly propagates as cancellation to every other job that
	// checks ctx.Err() — that's the entire "first error cancels siblings"
	// mechanism, no manual cancel() bookkeeping required.
	eg, egCtx := errgroup.WithContext(ctx)
	eg.SetLimit(concurrency)

	for i, job := range jobs {
		i, job := i, job // pre-Go-1.22 capture idiom; harmless and explicit even on 1.22+
		eg.Go(func() error {
			// SetLimit already caps how many of these goroutines run their
			// body concurrently; a canceled egCtx (from a sibling's error)
			// means further scheduling is pointless, but we still let
			// errgroup decide whether to even start us — checking egCtx
			// here additionally means an already-failed batch fails fast
			// for jobs that haven't been scheduled yet.
			if err := egCtx.Err(); err != nil {
				return err
			}
			val, err := job(egCtx)
			if err != nil {
				return fmt.Errorf("workerpool: job %d: %w", i, err)
			}
			results[i] = val
			return nil
		})
	}

	if err := eg.Wait(); err != nil {
		return nil, err
	}
	return results, nil
}

// Pool is a long-lived, bounded-concurrency worker pool. Workers are spawned
// once at construction and run until ctx is canceled or CloseAndWait is
// called; tasks are submitted over time via Submit.
type Pool[T any] struct {
	ctx       context.Context
	cancel    context.CancelFunc
	tasks     chan func(context.Context) (T, error)
	results   chan Result[T]
	eg        *errgroup.Group
	closeOnce sync.Once
	closed    chan struct{} // closed once CloseAndWait has run, guards Submit
}

// NewPool starts `workers` goroutines (minimum 1, to guarantee Submit never
// deadlocks against a zero-worker pool) consuming tasks until ctx is
// canceled or CloseAndWait is called.
func NewPool[T any](ctx context.Context, workers int) *Pool[T] {
	if workers <= 0 {
		workers = 1
	}

	poolCtx, cancel := context.WithCancel(ctx)
	eg, egCtx := errgroup.WithContext(poolCtx)

	p := &Pool[T]{
		ctx:     poolCtx,
		cancel:  cancel,
		tasks:   make(chan func(context.Context) (T, error)),
		results: make(chan Result[T]),
		eg:      eg,
		closed:  make(chan struct{}),
	}

	// Each worker ranges over tasks until the channel is closed (by
	// CloseAndWait) — that's the sole termination signal for the "no more
	// work is coming" case. egCtx cancellation is the other: a canceled
	// context makes the worker stop pulling new tasks even if more are
	// queued, matching "caller cancels -> stop accepting new items".
	for i := 0; i < workers; i++ {
		eg.Go(func() error {
			for {
				select {
				case <-egCtx.Done():
					return nil
				case task, ok := <-p.tasks:
					if !ok {
						return nil
					}
					val, err := task(egCtx)
					select {
					case p.results <- Result[T]{Value: val, Err: err}:
					case <-egCtx.Done():
						// Caller stopped caring about results (or the pool
						// is shutting down) — don't block forever trying to
						// deliver a result nobody will read.
						return nil
					}
				}
			}
		})
	}

	// The only goroutine allowed to close `results` is this one, and only
	// after every worker above has actually returned — closing a channel
	// while a worker might still send on it is a send-on-closed-channel
	// panic waiting to happen.
	go func() {
		_ = eg.Wait()
		close(p.results)
	}()

	return p
}

// Submit enqueues task for execution. It returns an error instead of
// blocking forever if the pool's context is canceled or CloseAndWait has
// already been called.
func (p *Pool[T]) Submit(task func(context.Context) (T, error)) error {
	select {
	case <-p.closed:
		return fmt.Errorf("workerpool: pool is closed")
	default:
	}

	select {
	case p.tasks <- task:
		return nil
	case <-p.ctx.Done():
		return p.ctx.Err()
	case <-p.closed:
		return fmt.Errorf("workerpool: pool is closed")
	}
}

// Results returns the channel completed Results are delivered on, in
// completion order. It is closed once every worker has exited following
// CloseAndWait (or ctx cancellation).
func (p *Pool[T]) Results() <-chan Result[T] {
	return p.results
}

// CloseAndWait stops accepting new tasks, waits for all queued and
// in-flight tasks to finish, and (transitively, via the goroutine started in
// NewPool) closes the Results channel. Safe to call exactly once; a second
// call is a harmless no-op that returns the same error.
func (p *Pool[T]) CloseAndWait() (err error) {
	p.closeOnce.Do(func() {
		close(p.closed) // Submit now refuses new work
		close(p.tasks)  // workers drain remaining queued tasks, then exit
		err = p.eg.Wait()
		p.cancel() // release the derived context's resources
	})
	return err
}

/*
Best practices demonstrated here:

  - errgroup.WithContext for BOTH shapes: RunBatch gets automatic
    first-error-cancels-siblings propagation, and Pool gets a single
    goroutine-joining primitive (eg.Wait()) instead of a hand-rolled
    sync.WaitGroup plus a separate error-collection channel.
  - Channel-closing order in Pool is deliberate and one-directional: stop
    accepting (closed) -> stop enqueuing (tasks) -> wait for workers ->
    close results. Reversing any step risks a panic or a stuck goroutine.
  - sync.Once around CloseAndWait's body — calling it twice must not double
    -close p.tasks (which would panic).
  - Every blocking channel operation in Submit and the worker loop is
    paired with a ctx.Done()/closed case, so nothing blocks forever if the
    caller cancels — a top requirement for goroutine-leak-free code.
  - RunBatch returns a plain (not partially valid) nil results slice on
    error, mirroring errgroup.Wait()'s own "don't trust partial state on
    error" convention, so callers can't accidentally read zero-valued
    entries for jobs that never got to run.

Alternative approaches:

  - RunBatch could hand-roll a semaphore (`make(chan struct{}, concurrency)`)
    instead of `errgroup.SetLimit` — functionally equivalent, but SetLimit
    is one line and already composes with the group's error/context
    machinery, so there's no reason to hand-roll it once errgroup is already
    in use for error aggregation.
  - Pool's results channel is completion-ordered by design; if a caller
    needs Submit-order results from a Pool, they must tag their own tasks
    with an index and re-sort — offering both would smuggle RunBatch's
    ordering guarantee into an API that's fundamentally about interleaved,
    async work, which is misleading.
  - A more advanced pool would resize workers dynamically or expose
    queue-depth metrics; deliberately out of scope here (see stretch goals).

Testing / failure-mode notes:

  - Concurrency-bound tests use an atomic in-flight counter incremented at
    job entry and decremented at exit, asserting the observed max never
    exceeds the configured limit — this is the only reliable way to test
    "at most N concurrent," since timing-based assertions are flaky.
  - Goroutine-leak tests snapshot runtime.NumGoroutine() before and after,
    with a short polling loop after the pool/batch call returns (goroutine
    teardown after a channel close is not synchronous with the close
    itself).
  - All tests run under `go test -race`; the Pool's shared `results` and
    `tasks` channels plus the `closed` channel are the only shared mutable
    state, and channels are race-safe by construction — no separate mutex
    was needed here.
*/
