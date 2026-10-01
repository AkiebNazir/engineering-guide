/*
Problem 13 — Pipeline (solution)
==================================

Reference implementation for the generic Generate -> FanOut -> FanIn ->
Collect pipeline specified in explanation/13_pipeline_explanation.go. See
that file for the full spec, rationale, and channel-ownership rules. The
short version, followed exactly below: exactly one goroutine creates and
closes each channel; cancellation propagates by every blocking channel
operation also selecting on ctx.Done().
*/
package pipeline

import (
	"context"
	"sync"
)

// Result pairs a fan-out stage's output with any error it returned.
type Result[T any] struct {
	Value T
	Err   error
}

// Generate emits each item from items onto the returned channel, in order,
// then closes it. It owns the returned channel exclusively: the deferred
// close fires whether the loop finishes naturally or ctx is canceled
// partway through, so there is exactly one close on every exit path.
func Generate[T any](ctx context.Context, items []T) <-chan T {
	out := make(chan T)
	go func() {
		defer close(out)
		for _, item := range items {
			select {
			case out <- item:
			case <-ctx.Done():
				return
			}
		}
	}()
	return out
}

// FanOut spawns `workers` goroutines (minimum 1) consuming from in and
// applying fn to each item. It never closes in — that channel belongs to
// whoever created it (typically Generate). It does own the returned
// channel and closes it only after every worker has exited, via the same
// "WaitGroup + one closer goroutine" shape as 12_worker_pool's results
// channel: no worker races another to close, because none of them close it
// at all.
func FanOut[In, Out any](ctx context.Context, in <-chan In, workers int, fn func(context.Context, In) (Out, error)) <-chan Result[Out] {
	if workers <= 0 {
		workers = 1
	}

	out := make(chan Result[Out])
	var wg sync.WaitGroup
	wg.Add(workers)
	for i := 0; i < workers; i++ {
		go func() {
			defer wg.Done()
			for {
				select {
				case item, ok := <-in:
					if !ok {
						// in is closed and drained — this worker's job is done.
						return
					}
					val, err := fn(ctx, item)
					select {
					case out <- Result[Out]{Value: val, Err: err}:
					case <-ctx.Done():
						// A result nobody will read — don't block forever
						// trying to deliver it.
						return
					}
				case <-ctx.Done():
					return
				}
			}
		}()
	}

	go func() {
		wg.Wait()
		close(out)
	}()
	return out
}

// FanIn merges cs into one output channel. It never closes any input
// channel — those belong to whichever stage produced them. It owns the
// returned channel and closes it only once every input channel has been
// fully drained and closed, tracked with a WaitGroup sized to len(cs) so
// the single close(out) call happens exactly once, after the last
// per-input goroutine exits.
func FanIn[T any](ctx context.Context, cs ...<-chan T) <-chan T {
	out := make(chan T)
	if len(cs) == 0 {
		close(out)
		return out
	}

	var wg sync.WaitGroup
	wg.Add(len(cs))
	for _, c := range cs {
		c := c // pre-Go-1.22 capture idiom; harmless and explicit even on 1.22+
		go func() {
			defer wg.Done()
			for v := range c {
				select {
				case out <- v:
				case <-ctx.Done():
					return
				}
			}
		}()
	}

	go func() {
		wg.Wait()
		close(out)
	}()
	return out
}

// Collect drains in into a slice of values in arrival order. On the first
// Result carrying a non-nil Err it stops immediately and returns that
// error — it is the CALLER's job to cancel ctx in response (typically by
// deriving ctx from context.WithCancel and calling cancel() here), which is
// what actually unblocks any upstream FanOut workers still trying to send.
// Collect itself only ever reads; it has no channel to own or close.
func Collect[T any](ctx context.Context, in <-chan Result[T]) ([]T, error) {
	var values []T
	for {
		select {
		case r, ok := <-in:
			if !ok {
				return values, nil
			}
			if r.Err != nil {
				return nil, r.Err
			}
			values = append(values, r.Value)
		case <-ctx.Done():
			return nil, ctx.Err()
		}
	}
}

/*
Best practices demonstrated here:

  - Exactly one designated closer per channel, always via `defer close(...)`
    or a dedicated "wait for every producer, then close" goroutine — never a
    close call reachable from more than one goroutine. This is the entire
    difference between a pipeline that shuts down cleanly and one that
    panics with "close of closed channel" or "send on closed channel" the
    first time cancellation races a send.
  - Every blocking channel operation (a send in Generate/FanOut/FanIn, the
    receive in Collect) is paired with a `case <-ctx.Done()`, so cancellation
    unblocks every stage, not just the one closest to the caller. This is
    what makes shutdown "leak-free" rather than merely "the reader stops
    reading."
  - FanOut and FanIn both refuse to close channels they don't own (`in` in
    FanOut, each `c` in FanIn) — ownership is a property of WHO CREATED the
    channel, not who happens to be reading it last.
  - sync.WaitGroup + a single closer goroutine generalizes cleanly from "N
    workers, 1 results channel" (FanOut, and 12_worker_pool's Pool) to "N
    input channels, 1 merged channel" (FanIn) — same shape, different
    direction.

Alternative approaches:

  - FanOut's output could be two separate channels (values and errors)
    instead of one Result[Out] channel — functionally equivalent, but
    forces the reader to select on two channels to reconstruct which error
    belongs to which item; one channel of pairs keeps that association
    explicit and is the more common idiom in real pipelines.
  - FanIn could use a `select` over a dynamically-sized slice of cases via
    reflection (`reflect.Select`) to merge without one goroutine per input —
    faster to write for a large, dynamic number of channels, but it gives up
    compile-time type safety and is meaningfully slower per-select than N
    goroutines each blocked on a plain channel receive; not worth it at the
    channel counts real pipelines fan in (single digits to low hundreds).
  - Collect canceling ctx itself on error (instead of leaving that to the
    caller) was deliberately rejected: Collect doesn't own ctx (it didn't
    create it), and a function silently canceling a context it was only
    handed is a common source of "why did my sibling goroutine stop" bugs
    elsewhere in the same call tree.

Testing / failure-mode notes (exercise these manually with `go run` +
`-race`, since this topic ships without a *_test.go file):

  - A full Generate -> FanOut -> FanIn -> Collect run over a known input
    slice should return every transformed value exactly once; feed it
    through a `map[int]bool` of seen inputs to check for drops or dupes.
  - Cancel ctx mid-run (via context.WithCancel + calling cancel() from a
    timer) and confirm runtime.NumGoroutine() settles back to its pre-run
    baseline within a short polling loop — a stage that forgot a
    ctx.Done() case shows up here as a permanently elevated goroutine
    count, not as a test failure anywhere else.
  - Run an fn that returns an error for one input among many; confirm
    Collect returns that error promptly and that canceling ctx in response
    (as the caller) brings FanOut's workers and Generate's producer down
    without a manual timeout — if it hangs instead, a send somewhere is
    missing its ctx.Done() case.
  - Run with `-race` and workers > 1: the only shared mutable state here is
    the channels themselves, which are race-safe by construction, so a race
    detector hit means a channel ownership rule was broken (e.g. two
    goroutines both closing the same channel).
*/
