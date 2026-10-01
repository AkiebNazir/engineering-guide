/*
Problem 13 — Pipeline
======================

WHAT WE'RE BUILDING

A generic multi-stage concurrent pipeline: a producer emits items onto a
channel, one or more fan-out stages transform them concurrently, and a
fan-in stage merges everything back into a single stream a caller can
drain. This is the shape behind almost every batch/stream processing job
you'll write in Go — read rows, transform each with bounded concurrency,
collect results — and it is also where Go's channel-ownership discipline
either pays off or turns into a goroutine leak.

WHY THIS MATTERS IN REAL SYSTEMS

  - Every stage of a pipeline is a goroutine (or a pool of them) connected
    by channels. The rule that keeps this leak-free is simple to state and
    easy to violate: only the goroutine that CREATES a channel is allowed
    to close it, and it must close it on every exit path (success, error,
    or ctx cancellation) — otherwise a downstream `range` over that channel
    blocks forever and its goroutine never exits.
  - Fan-out (one input channel, many worker goroutines reading it) is how
    you parallelize a slow per-item transform (a network call, a hash, a
    resize) without parallelizing the whole pipeline by hand.
  - Fan-in (many channels, one merged output) is the mirror problem: N
    workers each producing on their own channel need to be joined into one
    stream without the joiner closing the merged channel too early (while
    a worker might still send) or too late (leaking the reader).
  - Cancellation must propagate UPSTREAM, not just stop the downstream
    reader. If a caller stops reading mid-pipeline without canceling a
    shared context, every upstream stage blocks forever trying to send on
    a channel nobody drains — the single most common pipeline goroutine
    leak in real codebases.

CONCEPTS COVERED

  - Channel ownership: exactly one goroutine creates + closes each channel;
    every other goroutine only sends or only receives.
  - Fan-out with bounded worker count, fan-in via a `sync.WaitGroup` closer
    goroutine (the same "wait for every producer, then close" shape as
    12_worker_pool's Results channel, applied to N-to-1 instead of pool
    results).
  - Context-cancellation-propagates-upstream: canceling ctx must unblock
    every stage, not just the final reader.
  - Generics (Go 1.18+) so the pipeline works over any element type without
    per-type duplication.

# THE SPEC

Package `pipeline`.

	func Generate[T any](ctx context.Context, items []T) <-chan T
	    - Emits each item from items onto the returned channel, in order.
	    - Owns and closes the returned channel: closes it after emitting the
	      last item, OR immediately if ctx is canceled before finishing (no
	      goroutine leak either way).
	    - A send that would block past ctx cancellation must abort instead of
	      blocking forever — select on both the send and ctx.Done().

	type Result[T any] struct {
	    Value T
	    Err   error
	}

	func FanOut[In, Out any](ctx context.Context, in <-chan In, workers int, fn func(context.Context, In) (Out, error)) <-chan Result[Out]
	    - Spawns `workers` goroutines (minimum 1), each ranging over `in` and
	      calling fn on every item, sending a Result[Out] to the returned
	      channel.
	    - Does NOT own `in` — never closes it (the caller/Generate owns it).
	    - DOES own the returned channel: closes it only after every worker
	      goroutine has exited (a WaitGroup + one closer goroutine, exactly
	      like NewPool's results-closer in 12_worker_pool).
	    - ctx cancellation stops workers from picking up new items from `in`
	      and stops them from blocking on a send to the output channel.

	func FanIn[T any](ctx context.Context, cs ...<-chan T) <-chan T
	    - Merges zero or more input channels into one output channel, in
	      whatever order items arrive (interleaved, not round-robin).
	    - Owns and closes the returned channel: closes it once every input
	      channel has been drained AND closed, or immediately on ctx
	      cancellation.
	    - Zero input channels returns an already-closed empty channel, not a
	      channel that blocks forever.

	func Collect[T any](ctx context.Context, in <-chan Result[T]) ([]T, error)
	    - Drains `in` into a slice of values, in arrival order.
	    - On the FIRST Result with a non-nil Err, stops draining, returns
	      (nil, that error) — the caller is expected to have derived ctx from
	      a cancel func and call it so upstream stages stop promptly (see
	      HINTS); Collect itself only reads, it does not cancel.
	    - If ctx is canceled while draining (and no error has been seen yet),
	      returns (nil, ctx.Err()).
	    - Fully draining `in` to completion with no errors returns
	      (all values in arrival order, nil).

ACCEPTANCE CRITERIA

  - A full pipeline (Generate -> FanOut -> FanIn -> Collect) run to
    completion returns every input item's transformed value exactly once,
    with no duplicates and no drops.
  - Canceling ctx at any point unblocks every stage within a short bound —
    no goroutine outlives the pipeline call (verified via
    runtime.NumGoroutine() before/after with a short settle loop).
  - FanOut never has more than `workers` calls to fn executing at once.
  - FanIn never closes its output channel while an input channel might
    still send on it, and never leaks a goroutine waiting on an input
    channel that will never close.
  - Everything passes `go test -race` (or, absent a test file for this
    topic, `go vet ./...` finds nothing and the demo in a scratch `main`
    shows correct, leak-free behavior under -race manually).

HINTS

  - Generate: `select { case out <- item: case <-ctx.Done(): close(out); return }`
    inside the loop, `close(out)` again after the loop for the normal-exit
    path (closing twice is fine as long as it's the same goroutine and you
    guard with a labeled break / return, not two independent close calls on
    both paths — return immediately after the ctx.Done() close).
  - FanOut's closer goroutine: `go func() { wg.Wait(); close(out) }()` —
    same shape as 12_worker_pool's `go func() { eg.Wait(); close(p.results) }()`.
  - FanIn: one goroutine per input channel, each doing
    `for v := range c { select { case out <- v: case <-ctx.Done(): return } }`,
    all coordinated by one shared WaitGroup whose Wait() gates the single
    `close(out)` call — never let more than one goroutine call close(out).
  - Collect: a plain `for { select { case r, ok := <-in: ...; case <-ctx.Done(): ... } }`
    loop; remember `ok == false` means `in` is closed and draining is done,
    not an error.

COMMON PITFALLS

  - Closing a channel from more than one goroutine, or closing it more than
    once — both panic. Every channel in this package has exactly one
    designated closer.
  - FanOut or FanIn closing `in` — they never own an input channel, only
    the caller/upstream stage that created it does.
  - Downstream stopping early (e.g. Collect returning on first error)
    without the caller canceling ctx — upstream FanOut workers then block
    forever trying to send results nobody reads. Collect returning an error
    is a signal to the CALLER to cancel, not something Collect does for you.
  - FanIn's closer goroutine calling close(out) before every input channel
    has actually finished draining — a `sync.WaitGroup` sized to len(cs),
    with each per-input goroutine calling Done() on its own exit, is the
    only reliable way to know "every input is drained."

STRETCH GOALS

  - Add a `Tee[T any]` stage that duplicates one input channel onto two
    output channels (both must be read from, or both must respect ctx, to
    avoid one slow reader stalling the other).
  - Add per-item timeouts inside FanOut via `context.WithTimeout` layered
    on the shared ctx, independent per item.
  - Make FanIn preserve a deterministic order (round-robin across inputs)
    as an alternate function, and explain in comments why that is strictly
    slower (it must wait for the "next" input in rotation even if a later
    one is ready sooner) than the interleaved default.
  - Wire Generate -> FanOut -> FanIn -> Collect together behind a single
    `Run[In, Out any](ctx, items []In, workers int, fn func(context.Context, In) (Out, error)) ([]Out, error)`
    convenience function that also calls cancel() internally on the first
    error, demonstrating the "downstream error cancels upstream" pattern
    end-to-end in one call.
*/
package pipeline

import (
	"context"
)

// Result pairs a fan-out stage's output with any error it returned.
type Result[T any] struct {
	Value T
	Err   error
}

// Generate emits each item from items onto the returned channel, in order,
// then closes it. See the header comment for the full contract.
func Generate[T any](ctx context.Context, items []T) <-chan T {
	panic("TODO: implement Generate")
}

// FanOut spawns `workers` goroutines (minimum 1) consuming from in and
// applying fn to each item, sending a Result[Out] on the returned channel.
// It does not own (and never closes) in; it does own and close the
// returned channel, only after every worker has exited.
func FanOut[In, Out any](ctx context.Context, in <-chan In, workers int, fn func(context.Context, In) (Out, error)) <-chan Result[Out] {
	panic("TODO: implement FanOut")
}

// FanIn merges zero or more input channels into one output channel. It owns
// and closes the returned channel, only once every input channel has been
// fully drained and closed (or ctx is canceled).
func FanIn[T any](ctx context.Context, cs ...<-chan T) <-chan T {
	panic("TODO: implement FanIn")
}

// Collect drains in into a slice of values in arrival order, stopping and
// returning an error on the first Result with a non-nil Err, or on ctx
// cancellation. It does not cancel ctx itself — see the header comment.
func Collect[T any](ctx context.Context, in <-chan Result[T]) ([]T, error) {
	panic("TODO: implement Collect")
}
