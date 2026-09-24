/*
Problem 32 — Context & Timeouts Deep Dive (cancellation trees, deadline
budgets, causes, AfterFunc, WithoutCancel, typed keys, leaks)

WHAT WE'RE BUILDING

The context toolkit a production service actually needs, beyond
"pass ctx as the first argument":

 1. Key[T] — generic, collision-proof, type-safe context keys.
 2. WithBudgetFraction / Remaining — split a request's remaining deadline
    between downstream calls, and refuse to start work that can't finish.
 3. Retry — a retry loop that never sleeps past the deadline and always
    reports both the last error and why it stopped.
 4. MergeCancel + Server.Handle — combine a request context with a server
    lifetime context (context has no built-in "merge"), using
    context.AfterFunc and cancellation CAUSES so callers can tell
    "client gave up" from "deadline" from "server shutting down".
 5. Detach — run follow-up work (audit logs, async notifications) that keeps
    the request's values but not its cancellation, via
    context.WithoutCancel.
 6. SendContext / SumUntilDone — blocking operations that can't leak
    goroutines.

WHY THIS MATTERS IN REAL SYSTEMS

Timeouts are the single most important reliability mechanism in a
distributed system, and context is how Go carries them:

  - A request with a 2 s SLA that calls a cache, then a database, then
    another service must divide those 2 s. Giving each hop its own fixed
    2 s timeout means the caller has already given up while you are still
    doing work nobody will read — wasted capacity exactly when the system is
    overloaded, which turns a slowdown into an outage.
  - During a rolling deploy, in-flight requests must learn the server is
    stopping, and logs must say so — "context canceled" on 500 requests
    tells an on-call engineer nothing.
  - A context that is never cancelled, or a goroutine blocked on a channel
    send with no receiver, is a memory leak that grows with traffic.

MENTAL MODEL 1 — THE INTERFACE AND THE TREE

	type Context interface {
	    Deadline() (deadline time.Time, ok bool)
	    Done() <-chan struct{}   // closed on cancel or deadline
	    Err() error              // nil, Canceled, or DeadlineExceeded
	    Value(key any) any
	}

    Background ─┬─ WithValue(RequestIDKey, "req-7") ─── WithTimeout(2s)  ← request ctx
                │                                         │
                │                              ┌──────────┼───────────────┐
                │                              ▼          ▼               ▼
                │                   WithTimeout(400ms) WithTimeout(1.2s) WithoutCancel
                │                     cache lookup      DB query          audit log
                │                                                         (own 5s timeout)
                └─ WithCancelCause ─ server lifetime ── AfterFunc ──▶ cancels request ctx
                                                                       with ErrShutdown

  - Cancellation propagates DOWN only. Cancelling a child never affects
    its parent or siblings.
  - A child's effective deadline is min(own, parent's). WithTimeout(parent,
    10s) under a 50 ms parent still expires at 50 ms — the test proves it.
  - Value lookup walks UP the chain: O(depth). Keep values few.

MENTAL MODEL 2 — HOW CANCELLATION IS WIRED

    parent cancelCtx
    ┌──────────────────────────────────────┐
    │ done chan   children map[canceler]   │───▶ child 1
    │                                      │───▶ child 2
    │                                      │───▶ child 3  ... one entry per
    └──────────────────────────────────────┘                 WithCancel/WithTimeout

    cancel(child)  → close child.done, cancel child's children,
                     REMOVE child from parent.children, stop child's timer

If you never call cancel, the child stays in parent.children until the
parent itself is cancelled. For a request-scoped parent that is soon; for a
long-lived parent (server lifetime, a worker's context, Background-derived
package globals) it is forever. Measured by
TestLesson_ForgettingCancelRetainsChildren on this machine (Apple M4 Pro,
go1.26): 100,000 never-cancelled children of one parent kept 11.0 MB
reachable after a full GC; the same 100,000 children, cancelled, kept 0.0 MB. `go vet` reports the obvious cases as
"lostcancel". Rule: `ctx, cancel := context.With...(...)` is immediately
followed by `defer cancel()` unless you hand cancel to someone else.

MENTAL MODEL 3 — DEADLINE BUDGETS

    request deadline: 1000 ms
    ├─ now = 0 ms     WithBudgetFraction(0.2) → cache gets 200 ms
    │                 cache times out at 200 ms
    ├─ now = 200 ms   800 ms remain → DB gets WithBudgetFraction(0.9) = 720 ms
    │                 DB answers at 500 ms
    └─ now = 500 ms   500 ms remain for rendering and the response write

    and if only 5 ms remain when a 50 ms-minimum call is about to start:
    return ErrBudgetExhausted immediately — fail fast, free the worker.

gRPC propagates the remaining deadline to the server automatically (the
grpc-timeout header); with HTTP you forward it yourself (e.g. a
X-Request-Deadline header) and re-create the deadline on the receiving side.

Retries must respect the same budget:

    attempt 1 ──fail── sleep 20ms ── attempt 2 ──fail── sleep 40ms ──
    attempt 3 ──fail── remaining 15ms < backoff 80ms → STOP, return
    errors.Join(lastErr, ErrBudgetExhausted)

Never `time.Sleep(backoff)` inside a retry loop: the sleep cannot be
interrupted by cancellation. Use a timer in a select with ctx.Done().

MENTAL MODEL 4 — CAUSES: WHY WAS I CANCELLED?

ctx.Err() only ever says Canceled or DeadlineExceeded. Go 1.20/1.21 added
causes:

	ctx, cancel := context.WithCancelCause(parent)
	cancel(ErrShutdown)                    // records the reason
	ctx.Err()            // context.Canceled (unchanged, for compatibility)
	context.Cause(ctx)   // ErrShutdown

	ctx, cancel := context.WithTimeoutCause(parent, 10*time.Millisecond, errSLA)
	// on expiry: Err() == DeadlineExceeded, Cause(ctx) == errSLA

Return context.Cause(ctx) from functions that stop because of cancellation
and log it: "stopped: server shutting down" vs "stopped: client SLA 10ms".
Callers that check errors.Is(err, context.Canceled) should switch to checking
the specific cause they care about.

MENTAL MODEL 5 — MERGING TWO CANCELLATION SOURCES WITH AFTERFUNC

A context has exactly one parent, but a request handler must stop when
EITHER the client goes away OR the server shuts down.

    request ctx ──(parent)──▶ merged ctx ◀──(AfterFunc callback)── server lifetime
                                   │
                        cancelled by whichever ends first,
                        with that source's cause

	ctx, cancel := context.WithCancelCause(primary)
	stop := context.AfterFunc(secondary, func() { cancel(context.Cause(secondary)) })
	return ctx, func() { stop(); cancel(context.Canceled) }

context.AfterFunc (Go 1.21) registers f to run in its own goroutine once
secondary is done — no goroutine sits blocked waiting for it. The returned
stop unregisters f; forgetting to call it on a long-lived secondary leaks
one registration per request (the same shape as MENTAL MODEL 2).

MENTAL MODEL 6 — WORK THAT MUST OUTLIVE THE REQUEST

    handler returns ──▶ request ctx cancelled
                              │
          ┌───────────────────┴──────────────────────────┐
          ▼                                              ▼
    go audit(ctx)                              go audit(Detach(ctx, 5s))
    fails instantly: "context canceled"        keeps request-id / trace values,
                                               ignores the request's cancellation,
    go audit(context.Background())             bounded by its own 5s timeout ✓
    runs, but logs lose request-id/trace

context.WithoutCancel (Go 1.21) returns a context with the parent's values,
no deadline and no Done channel. ALWAYS add a new timeout on top — detached
work with no deadline is how shutdown hangs forever.

MENTAL MODEL 7 — CONTEXT IN NET/HTTP

  - Server: r.Context() is cancelled when the client disconnects, the
    HTTP/2 stream is reset, or ServeHTTP returns. Pass it to every DB and
    RPC call in the handler so abandoned requests stop consuming resources.
    TestLesson_ClientDisconnectCancelsHandlerContext shows a client-side
    50 ms timeout arriving at the server as context.Canceled.
  - Client: http.NewRequestWithContext(ctx, ...) bounds the WHOLE exchange
    including reading the body; http.Client.Timeout is a coarser global
    alternative (Problem 34).
  - http.Server.BaseContext / ConnContext let you derive every request from
    a server lifetime context — the built-in version of MergeCancel's
    secondary.

KEYS: WHY NOT STRINGS

    package auth:     context.WithValue(ctx, "user", "alice")
    package metrics:  context.WithValue(ctx, "user", 42)      ← shadows auth's value
    auth.User(ctx) → ctx.Value("user").(string) → not ok → "anonymous"

Keys compare with ==, so any two packages using the same built-in-typed key
collide. An unexported type, or a pointer to a Key[T] created once, can only
be produced by its own package. Key[T] also types the VALUE, removing the
unchecked type assertion at every call site.

What belongs in context values: request-scoped, cross-cutting data that
passes through APIs untouched — request/trace IDs, auth principal, locale.
What doesn't: optional function parameters, database handles, loggers you
could inject, anything the function's behaviour depends on (make it a real
parameter).

SPEC

	type Key[T any] struct { ... }
	func NewKey[T any](name string) *Key[T]
	func (k *Key[T]) With(ctx context.Context, v T) context.Context
	func (k *Key[T]) Get(ctx context.Context) (T, bool)
	var RequestIDKey = NewKey[string]("request-id")

	var ErrBudgetExhausted error
	func Remaining(ctx context.Context) (time.Duration, bool)
	func WithBudgetFraction(ctx context.Context, fraction float64, minUseful time.Duration) (context.Context, context.CancelFunc, error)
	    fraction must be in (0,1]; no parent deadline → plain WithCancel;
	    remaining < minUseful → error wrapping ErrBudgetExhausted.
	func Retry(ctx context.Context, attempts int, backoff time.Duration, fn func(ctx context.Context) error) error
	    Exponential backoff via timer+select; if remaining < next backoff →
	    errors.Join(lastErr, ErrBudgetExhausted); if ctx done →
	    errors.Join(lastErr, context.Cause(ctx)).

	var ErrShutdown error
	func MergeCancel(primary, secondary context.Context) (context.Context, context.CancelFunc)
	type Server struct { ... }
	func NewServer() *Server
	func (s *Server) Shutdown()                                          // cause ErrShutdown
	func (s *Server) Handle(ctx context.Context, work time.Duration) error   // returns context.Cause on early stop

	func Detach(ctx context.Context, timeout time.Duration) (context.Context, context.CancelFunc)
	func SendContext[T any](ctx context.Context, ch chan<- T, v T) error
	func SumUntilDone(ctx context.Context, in <-chan int) (int, error)

ACCEPTANCE CRITERIA

  - `go test -race -v ./32_context_and_timeouts_deep_dive/solution/...` passes.
  - Shutdown makes every in-flight Handle return an error for which
    errors.Is(err, ErrShutdown) is true.
  - Retry never runs past its context's deadline.
  - Detach keeps RequestIDKey's value after the parent is cancelled.

HOW TO RUN

	go test -race -v ./32_context_and_timeouts_deep_dive/solution/...
	go test -run Example -v ./32_context_and_timeouts_deep_dive/solution/...
	go vet ./...     # includes the lostcancel analyzer

HINTS

  - Key.Get: `v, ok := ctx.Value(k).(T)` handles the missing case too.
  - time.Until(deadline) gives the remaining budget.
  - Handle: `ctx, cancel := MergeCancel(ctx, s.lifetime); defer cancel()`,
    then select on time.After(work) and ctx.Done().
  - Detach: context.WithTimeout(context.WithoutCancel(ctx), timeout).

COMMON PITFALLS

  - Storing a Context in a struct field for later use: its deadline and
    cancellation belong to one call, not an object's lifetime.
  - Passing nil instead of context.TODO() — methods on a nil interface panic.
  - Checking ctx.Err() once at the top of a long loop and never again.
  - Treating DeadlineExceeded as a retryable error without checking the
    parent's remaining budget.
  - Starting goroutines with the request ctx for work that must finish after
    the response (they get cancelled), or with Background (they lose values
    and have no deadline).
  - Wrapping timeouts around timeouts: http.Client.Timeout 30s + ctx 2s +
    DB driver 10s — know which one actually fires.

STRETCH GOALS

  - Write HTTP middleware that reads an X-Request-Deadline header, applies
    it with WithDeadline, and forwards the remaining budget on outgoing
    requests.
  - Add jitter and a retryable-error classifier to Retry.
  - Wire Server into a real http.Server using BaseContext and
    RegisterOnShutdown, and show requests observing ErrShutdown.
*/

package ctxdeep

import (
	"context"
	"errors"
	"time"
)

// ============================================================================
// 1. Keys
// ============================================================================

// Key is a typed, collision-proof context key.
type Key[T any] struct{ name string }

// NewKey creates a new unique key.
func NewKey[T any](name string) *Key[T] { return &Key[T]{name: name} }

// With returns a child context carrying v under k.
func (k *Key[T]) With(ctx context.Context, v T) context.Context {
	// TODO: context.WithValue(ctx, k, v)
	panic("not implemented")
}

// Get returns the value stored under k.
func (k *Key[T]) Get(ctx context.Context) (T, bool) {
	// TODO
	panic("not implemented")
}

// RequestIDKey is an example package-level key.
var RequestIDKey = NewKey[string]("request-id")

// ============================================================================
// 2. Budgets
// ============================================================================

// ErrBudgetExhausted means too little time remains to usefully start work.
var ErrBudgetExhausted = errors.New("ctxdeep: deadline budget exhausted")

// Remaining reports the time until ctx's deadline.
func Remaining(ctx context.Context) (time.Duration, bool) {
	// TODO
	panic("not implemented")
}

// WithBudgetFraction derives a context with fraction of the remaining budget.
func WithBudgetFraction(ctx context.Context, fraction float64, minUseful time.Duration) (context.Context, context.CancelFunc, error) {
	// TODO: validate fraction; no deadline → WithCancel; too little left → ErrBudgetExhausted.
	panic("not implemented")
}

// Retry retries fn with exponential backoff without outliving ctx.
func Retry(ctx context.Context, attempts int, backoff time.Duration, fn func(ctx context.Context) error) error {
	// TODO: see SPEC. Use time.NewTimer + select, never time.Sleep.
	panic("not implemented")
}

// ============================================================================
// 3. Causes and merging
// ============================================================================

// ErrShutdown is the cause attached when the server stops.
var ErrShutdown = errors.New("ctxdeep: server shutting down")

// MergeCancel returns a child of primary that is also cancelled when secondary ends.
func MergeCancel(primary, secondary context.Context) (context.Context, context.CancelFunc) {
	// TODO: WithCancelCause(primary) + context.AfterFunc(secondary, ...); the
	// returned cancel must call stop() and cancel(context.Canceled).
	panic("not implemented")
}

// Server has a lifetime context cancelled on Shutdown.
type Server struct {
	lifetime context.Context
	stop     context.CancelCauseFunc
}

// NewServer returns a running server.
func NewServer() *Server {
	// TODO
	panic("not implemented")
}

// Shutdown cancels in-flight requests with ErrShutdown.
func (s *Server) Shutdown() {
	// TODO
	panic("not implemented")
}

// Handle simulates work honouring ctx and server shutdown.
func (s *Server) Handle(ctx context.Context, work time.Duration) error {
	// TODO
	panic("not implemented")
}

// ============================================================================
// 4. Detached work
// ============================================================================

// Detach keeps ctx's values but not its cancellation, with a new timeout.
func Detach(ctx context.Context, timeout time.Duration) (context.Context, context.CancelFunc) {
	// TODO
	panic("not implemented")
}

// ============================================================================
// 5. Blocking operations
// ============================================================================

// SendContext sends v on ch unless ctx ends first.
func SendContext[T any](ctx context.Context, ch chan<- T, v T) error {
	// TODO
	panic("not implemented")
}

// SumUntilDone sums values from in until it closes or ctx ends.
func SumUntilDone(ctx context.Context, in <-chan int) (int, error) {
	// TODO
	panic("not implemented")
}
