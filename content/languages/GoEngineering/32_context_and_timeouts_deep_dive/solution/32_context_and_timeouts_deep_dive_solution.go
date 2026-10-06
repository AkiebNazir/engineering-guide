// Package ctxdeep is the reference solution for Problem 32 — Context &
// Timeouts Deep Dive.
package ctxdeep

import (
	"context"
	"errors"
	"fmt"
	"time"
)

// ============================================================================
// 1. Request-scoped values with collision-proof keys
// ============================================================================

// Key is a typed context key. Two keys are equal only if they are the SAME
// *Key pointer, so no other package can read or overwrite your value by
// accident — even one that picks the same name. The name exists only for
// debugging (fmt output of the context).
//
// This improves on the classic `type ctxKey int` pattern by also typing the
// value, so Get can't return the wrong type.
type Key[T any] struct{ name string }

// NewKey creates a new, unique key. Declare keys once, at package level.
func NewKey[T any](name string) *Key[T] { return &Key[T]{name: name} }

func (k *Key[T]) String() string { return "ctxdeep.Key(" + k.name + ")" }

// With returns a child context carrying v under k.
func (k *Key[T]) With(ctx context.Context, v T) context.Context {
	return context.WithValue(ctx, k, v)
}

// Get returns the value stored under k, walking up the context chain.
// Lookup is a linked-list walk — O(depth) — which is one reason to keep
// context values few and small.
func (k *Key[T]) Get(ctx context.Context) (T, bool) {
	v, ok := ctx.Value(k).(T)
	return v, ok
}

// RequestIDKey is an example of a package-level key.
var RequestIDKey = NewKey[string]("request-id")

// ============================================================================
// 2. Deadline budgets
// ============================================================================

// ErrBudgetExhausted means too little time remains to usefully start work.
var ErrBudgetExhausted = errors.New("ctxdeep: deadline budget exhausted")

// Remaining reports how long until ctx's deadline; ok is false if ctx has
// no deadline.
func Remaining(ctx context.Context) (time.Duration, bool) {
	d, ok := ctx.Deadline()
	if !ok {
		return 0, false
	}
	return time.Until(d), true
}

// WithBudgetFraction derives a context whose deadline is `fraction` of the
// time remaining on ctx — for example, give a cache lookup 20% of the
// request's budget so a slow cache still leaves 80% for the database
// fallback. If less than minUseful remains in total, it returns
// ErrBudgetExhausted instead of starting work that is doomed to time out.
//
// Without a parent deadline there is no budget to divide: the child is just
// cancellable. (A service should normally impose its own ceiling at the edge
// rather than let that happen.)
func WithBudgetFraction(ctx context.Context, fraction float64, minUseful time.Duration) (context.Context, context.CancelFunc, error) {
	if fraction <= 0 || fraction > 1 {
		return nil, nil, fmt.Errorf("ctxdeep: fraction %v out of (0,1]", fraction)
	}
	remaining, ok := Remaining(ctx)
	if !ok {
		c, cancel := context.WithCancel(ctx)
		return c, cancel, nil
	}
	if remaining < minUseful {
		return nil, nil, fmt.Errorf("%w: %v left, need %v", ErrBudgetExhausted, remaining.Round(time.Millisecond), minUseful)
	}
	c, cancel := context.WithTimeout(ctx, time.Duration(float64(remaining)*fraction))
	return c, cancel, nil
}

// Retry calls fn up to attempts times with exponential backoff, and is
// deadline-aware in two ways naive retry loops are not:
//   - it stops as soon as ctx is done (select on Done, never a bare Sleep);
//   - it does not start a backoff sleep that would outlive the deadline — it
//     returns immediately with ErrBudgetExhausted joined to the last error.
func Retry(ctx context.Context, attempts int, backoff time.Duration, fn func(ctx context.Context) error) error {
	var lastErr error
	for attempt := range attempts {
		if err := ctx.Err(); err != nil {
			return errors.Join(lastErr, context.Cause(ctx))
		}
		if lastErr = fn(ctx); lastErr == nil {
			return nil
		}
		if attempt == attempts-1 {
			break
		}
		if rem, ok := Remaining(ctx); ok && rem < backoff {
			return errors.Join(lastErr, ErrBudgetExhausted)
		}
		timer := time.NewTimer(backoff)
		select {
		case <-ctx.Done():
			timer.Stop()
			return errors.Join(lastErr, context.Cause(ctx))
		case <-timer.C:
		}
		backoff *= 2
	}
	return lastErr
}

// ============================================================================
// 3. Cancellation causes and merging two cancellation sources
// ============================================================================

// ErrShutdown is the cause attached when the server stops.
var ErrShutdown = errors.New("ctxdeep: server shutting down")

// MergeCancel returns a context derived from primary (so it keeps primary's
// values and deadline) that is ALSO cancelled when secondary is done, with
// secondary's cause.
//
// The context package has no built-in merge because a context can only have
// one parent. context.AfterFunc (Go 1.21) makes the merge cheap: it registers
// a callback on secondary without dedicating a goroutine to waiting on it.
// The returned CancelFunc also unregisters that callback — without that, a
// long-lived secondary (the server's lifetime context) would accumulate one
// callback per request forever.
func MergeCancel(primary, secondary context.Context) (context.Context, context.CancelFunc) {
	ctx, cancel := context.WithCancelCause(primary)
	stop := context.AfterFunc(secondary, func() {
		cancel(context.Cause(secondary))
	})
	return ctx, func() {
		stop()
		cancel(context.Canceled)
	}
}

// Server shows the pattern: a lifetime context cancelled with a cause on
// shutdown, merged into every request.
type Server struct {
	lifetime context.Context
	stop     context.CancelCauseFunc
}

// NewServer returns a running server.
func NewServer() *Server {
	ctx, cancel := context.WithCancelCause(context.Background())
	return &Server{lifetime: ctx, stop: cancel}
}

// Shutdown cancels every in-flight request with ErrShutdown as the cause.
func (s *Server) Shutdown() { s.stop(ErrShutdown) }

// Handle simulates work that takes `work`, honouring both the caller's
// context and server shutdown. The returned error is the CAUSE, so callers
// can tell "client went away" from "deadline" from "we are shutting down".
func (s *Server) Handle(ctx context.Context, work time.Duration) error {
	ctx, cancel := MergeCancel(ctx, s.lifetime)
	defer cancel()

	select {
	case <-time.After(work):
		return nil
	case <-ctx.Done():
		// ctx.Err() is only ever Canceled or DeadlineExceeded; Cause carries
		// the specific reason when one was supplied.
		return context.Cause(ctx)
	}
}

// ============================================================================
// 4. Work that must outlive the request
// ============================================================================

// Detach returns a context that keeps ctx's VALUES (request ID, trace span,
// auth principal) but not its cancellation or deadline, bounded by its own
// timeout. Use it for audit logs, cache warm-up, or async notifications
// kicked off by a request that is about to return.
//
// Before Go 1.21's context.WithoutCancel people used context.Background(),
// which silently dropped request IDs and tracing from those logs.
func Detach(ctx context.Context, timeout time.Duration) (context.Context, context.CancelFunc) {
	return context.WithTimeout(context.WithoutCancel(ctx), timeout)
}

// ============================================================================
// 5. Honouring cancellation in loops and blocking operations
// ============================================================================

// SendContext sends v on ch unless ctx ends first. A bare `ch <- v` with no
// receiver blocks forever — the most common goroutine leak in Go.
func SendContext[T any](ctx context.Context, ch chan<- T, v T) error {
	select {
	case ch <- v:
		return nil
	case <-ctx.Done():
		return context.Cause(ctx)
	}
}

// SumUntilDone adds values from in until it is closed or ctx is done,
// returning the partial sum and the reason it stopped early (nil if in was
// drained).
func SumUntilDone(ctx context.Context, in <-chan int) (int, error) {
	sum := 0
	for {
		select {
		case v, ok := <-in:
			if !ok {
				return sum, nil
			}
			sum += v
		case <-ctx.Done():
			return sum, context.Cause(ctx)
		}
	}
}
