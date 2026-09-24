/*
Problem 03 — API Client With Retries (backoff, jitter, circuit breaker, deadlines)

WHAT WE'RE BUILDING

An HTTP client wrapper (`Client`) that calls a flaky upstream service
resiliently: retries transient failures with exponential backoff and
jitter, respects context deadlines/cancellation at every step, refuses to
retry non-idempotent-unsafe or client-error (4xx) responses, and trips a
circuit breaker after sustained failures so a downed dependency doesn't
get hammered by every caller's individual retry loop.

# WHY THIS MATTERS IN REAL SYSTEMS

Every service that calls another service over the network needs this
exact logic, and getting it wrong is one of the most common causes of
cascading outages: naive retries without backoff turn a brief blip into a
"retry storm" that keeps the downstream dead; retries without jitter
synchronize every client's retry attempts into thundering-herd waves;
retries without a circuit breaker mean a fully-down dependency still gets
hit by 100% of traffic, wasting connections/threads/latency budget on
calls that are certain to fail; and retries that ignore context deadlines
keep working past the point where the caller has already given up and
walked away.

CONCEPTS COVERED

  - Exponential backoff with jitter (full jitter, per Marc Brooker's
    well-known formula: `sleep = random(0, min(cap, base*2^attempt))`)
  - Retry classification: which errors/status codes are worth retrying
    (network errors, 429, 5xx) vs not (4xx other than 429, context
    cancellation)
  - `context.Context` deadline propagation through retries — a deadline
    is a budget for the WHOLE operation including retries, not a
    per-attempt timeout
  - A circuit breaker state machine: Closed -> Open -> Half-Open -> Closed
  - `Retry-After` header handling (a well-behaved server tells you exactly
    how long to back off)
  - Idempotency: why only GET/PUT/DELETE (and POST specifically marked
    idempotent by the caller) should ever be retried automatically
  - Interfaces for testability: an `httpDoer` interface
    (`Do(*http.Request) (*http.Response, error)`) so tests can inject a
    fake transport without a real network call or `httptest.Server` for
    every test case

# SPEC

Build a `Client` wrapping an `*http.Client` (or any `httpDoer`) with:

	type RetryPolicy struct {
	    MaxAttempts int           // total attempts including the first, >= 1
	    BaseDelay   time.Duration // e.g. 100ms
	    MaxDelay    time.Duration // cap on any single backoff sleep
	}

	func NewClient(doer httpDoer, policy RetryPolicy) *Client

	func (c *Client) Do(ctx context.Context, req *http.Request) (*http.Response, error)

Retry rules:
  - Retry on: network-level errors (anything `doer.Do` returns as `err !=
    nil`, e.g. connection refused/reset, DNS failure — NOT context
    cancellation, which must propagate immediately without further
    attempts), HTTP 429, and HTTP 5xx (500-599).
  - Do NOT retry on: any other 4xx status (400-499 except 429), or any
    2xx/3xx (obviously — that's success).
  - Respect `Retry-After` on a 429/503 response if present (either
    delta-seconds or an HTTP-date; delta-seconds is enough for this
    problem — document the HTTP-date gap as a known limitation if you
    skip it) — use it INSTEAD OF the computed backoff delay for that
    attempt, but still cap it to a sane maximum so a malicious/broken
    server can't make you sleep for a day.
  - Stop retrying after MaxAttempts total attempts (so MaxAttempts=3 means
    at most 2 retries) OR when ctx is done, whichever comes first.
  - Between attempts, sleep for `min(MaxDelay, BaseDelay * 2^(attempt-1))`
    with full jitter applied (uniform random in [0, that value]), UNLESS
    Retry-After overrides it. The sleep must itself respect ctx
    cancellation (a `time.Sleep` cannot be interrupted — you need a
    `select` on a timer and `ctx.Done()`).
  - On exhausting all attempts, return the last response/error, wrapped
    with context (e.g. `fmt.Errorf("after %d attempts: %w", n, err)`), NOT
    a generic "retries exhausted" with no trace of the underlying cause.

Circuit breaker (`CircuitBreaker`, wrapping a `Client` or standalone,
your call — recommended: standalone, composed via a wrapping RoundTripper
or a decorator around `httpDoer`):
  - States: Closed (normal), Open (fail fast, no calls attempted), Half-
    Open (one trial call allowed through to test recovery).
  - Trips to Open after N consecutive failures (configurable).
  - After a configurable cooldown, transitions Open -> Half-Open
    automatically (time-based, no external trigger needed).
  - A successful Half-Open trial call closes the circuit (reset failure
    count); a failed one reopens it (reset cooldown timer).
  - Must be safe for concurrent use (many goroutines calling through the
    same breaker).
  - When Open, calls fail immediately with a sentinel `ErrCircuitOpen`
    without attempting any network I/O or consuming a retry budget.

ACCEPTANCE CRITERIA

  - A fake `httpDoer` that fails N times then succeeds proves the client
    retries exactly enough times and no more.
  - A fake that always returns 400 proves the client does NOT retry
    client errors.
  - A fake honoring `context.Canceled` context proves retries stop
    immediately rather than continuing to sleep/retry.
  - A backoff-only test (no real sleeping — inject a clock/sleep function)
    proves delays grow exponentially and are capped.
  - A circuit breaker test proves: N consecutive failures trips it,
    subsequent calls fail fast with ErrCircuitOpen without touching the
    fake doer, and after the cooldown a single trial call is let through.
  - All tests run in well under a second — no real `time.Sleep` of
    meaningful duration in tests (inject a clock or use tiny durations
    with a fake clock, not real wall time, for backoff-heavy tests).
*/
package main

import (
	"context"
	"net/http"
	"sync"
	"time"
)

// httpDoer is the minimal interface Client depends on — satisfied by
// *http.Client, and trivially fakeable in tests without a real network
// call or httptest.Server.
type httpDoer interface {
	Do(req *http.Request) (*http.Response, error)
}

// RetryPolicy configures retry attempts and backoff.
type RetryPolicy struct {
	MaxAttempts int
	BaseDelay   time.Duration
	MaxDelay    time.Duration
}

// Client wraps an httpDoer with retry/backoff logic.
//
// TODO: add whatever fields you need: the doer, the policy, and an
// injectable sleep function `func(context.Context, time.Duration) error`
// so tests can avoid real wall-clock sleeps while still exercising the
// cancellation-aware sleeping logic.
type Client struct {
	doer   httpDoer
	policy RetryPolicy
	// TODO: fields (e.g. a sleep func for testability)
}

// NewClient returns a Client wrapping doer with the given retry policy.
// TODO: implement, defaulting the sleep func to a real ctx-aware sleep.
func NewClient(doer httpDoer, policy RetryPolicy) *Client {
	panic("TODO: implement NewClient")
}

// isRetryableStatus reports whether an HTTP status code should trigger a
// retry per the spec (429 or 5xx; not other 4xx, not 2xx/3xx).
// TODO: implement.
func isRetryableStatus(status int) bool {
	panic("TODO: implement isRetryableStatus")
}

// backoffDelay computes the full-jitter exponential backoff delay for the
// given (1-indexed) attempt number, per the spec formula:
// random(0, min(MaxDelay, BaseDelay*2^(attempt-1))).
// TODO: implement. attempt=1 is the delay before the SECOND attempt (i.e.
// call this with attempt-1 already representing "how many attempts have
// been made so far" — get the indexing right and document it).
func backoffDelay(policy RetryPolicy, attempt int, rng func() float64) time.Duration {
	panic("TODO: implement backoffDelay")
}

// parseRetryAfter parses a Retry-After header value as delta-seconds and
// returns the resulting duration, or ok=false if absent/unparseable.
// TODO: implement the delta-seconds form; document HTTP-date as
// unsupported (a known, acceptable gap for this problem).
func parseRetryAfter(header string) (time.Duration, bool) {
	panic("TODO: implement parseRetryAfter")
}

// Do performs req, retrying per c.policy, and returns the first non-retryable
// response/error (or the last one after exhausting attempts).
//
// TODO: implement the full retry loop:
//  1. Loop attempt 1..MaxAttempts.
//  2. Clone req for each attempt (http.Request bodies can only be read
//     once — you need req.Body to be replayable via GetBody, or require
//     the caller supply a body that supports it; document this
//     requirement).
//  3. Call c.doer.Do. If err != nil and ctx.Err() != nil, return
//     immediately (don't retry past cancellation). If err != nil
//     otherwise, this attempt failed; retry if attempts remain.
//  4. If err == nil, check resp.StatusCode: return immediately if not
//     retryable; otherwise drain+close resp.Body (required before
//     retrying to allow connection reuse) and retry if attempts remain.
//  5. Before each retry, sleep per backoffDelay (or Retry-After if
//     present), respecting ctx cancellation during the sleep itself.
//  6. After exhausting attempts, return the last response/error wrapped
//     with attempt count context.
func (c *Client) Do(ctx context.Context, req *http.Request) (*http.Response, error) {
	panic("TODO: implement Client.Do")
}

// ---------------------------------------------------------------------------
// Circuit breaker
// ---------------------------------------------------------------------------

// CircuitState identifies which of the three circuit-breaker states a
// CircuitBreaker is in.
type CircuitState int

const (
	StateClosed CircuitState = iota
	StateOpen
	StateHalfOpen
)

// ErrCircuitOpen is returned by CircuitBreaker.Do when the circuit is
// open and no call was attempted.
var ErrCircuitOpen error

// CircuitBreaker wraps an httpDoer, tripping open after consecutive
// failures and probing recovery after a cooldown.
//
// TODO: add fields: mutex, current state, consecutive failure count,
// failure threshold, cooldown duration, time the circuit opened (to know
// when the cooldown elapses), and the wrapped doer.
type CircuitBreaker struct {
	mu sync.Mutex
	// TODO: fields
}

// NewCircuitBreaker returns a CircuitBreaker wrapping doer, tripping open
// after failureThreshold consecutive failures and attempting recovery
// after cooldown.
func NewCircuitBreaker(doer httpDoer, failureThreshold int, cooldown time.Duration) *CircuitBreaker {
	panic("TODO: implement NewCircuitBreaker")
}

// Do executes req through the breaker: fails fast with ErrCircuitOpen if
// open (and the cooldown hasn't elapsed), allows exactly one trial call
// through if half-open, and otherwise passes through to the wrapped
// doer, updating breaker state based on the outcome.
//
// TODO: implement the state machine described in the spec. Treat any
// non-nil err OR a 5xx status as a "failure" for breaker purposes (this
// is a design decision worth documenting: should 4xx count as a
// breaker failure? Spec answer: no — a 400 means the CALLER is wrong,
// not the dependency, so it shouldn't move the breaker toward Open).
func (b *CircuitBreaker) Do(req *http.Request) (*http.Response, error) {
	panic("TODO: implement CircuitBreaker.Do")
}

// State returns the breaker's current state (useful for tests/metrics).
func (b *CircuitBreaker) State() CircuitState {
	panic("TODO: implement CircuitBreaker.State")
}

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------

func main() {
	// TODO: wire a Client around http.DefaultClient with a sane
	// RetryPolicy, optionally wrap a CircuitBreaker around
	// http.DefaultClient first and pass the breaker as the Client's
	// doer (CircuitBreaker itself implements httpDoer), then issue a
	// demo request against a well-known reliable endpoint (or a local
	// httptest.Server you spin up inline) and print the outcome —
	// demonstrating that Client -> CircuitBreaker -> *http.Client
	// composes cleanly because everything speaks httpDoer.
	panic("TODO: implement main")
}

/*
HINTS

  - Full jitter (`rand(0, cap)`) spreads retries far better than
    "equal jitter" or no jitter at all — it's the AWS Architecture Blog's
    documented recommendation and worth citing as the reasoning, not just
    the formula.
  - `req.Clone(ctx)` gives you a fresh *http.Request per attempt sharing
    the same GetBody — but you still need to call `req.GetBody()` to get
    a fresh io.ReadCloser body for each attempt if the original request
    had a body (Clone does NOT re-arm Body itself).
  - Always `io.Copy(io.Discard, resp.Body)` then `resp.Body.Close()`
    before retrying a request whose response you're discarding — failing
    to drain the body prevents the underlying connection from being
    reused by the transport's connection pool, silently degrading every
    subsequent request to a fresh TCP+TLS handshake.
  - Inject both the sleep function AND (if you want fully deterministic
    tests) the RNG function used for jitter — a test that can force
    jitter's random draw makes backoff assertions exact instead of
    range-checks.

COMMON PITFALLS

  - Retrying a POST that isn't idempotent (e.g. "charge the customer $10")
    — a network error on the response leg (the charge succeeded, but the
    ack was lost) followed by a retry double-charges. This problem's
    Client retries based on status/error only, not method — document
    that a real system additionally needs an idempotency key or must only
    auto-retry verbs the caller has confirmed are safe.
  - Treating `context.DeadlineExceeded` as a retryable network error — if
    ctx is already past its deadline, retrying just burns more time
    failing the same way; check `ctx.Err()` first.
  - `time.Sleep(d)` inside the retry loop instead of a ctx-aware sleep —
    ignores cancellation entirely, so a caller who gave up still waits
    out the full backoff.
  - A circuit breaker with no mutex — every field it tracks (state,
    failure count, last-opened time) is written from every caller's
    goroutine; without a lock this is a data race, not just a
    theoretical one (go test -race will catch it immediately).
  - Not resetting the consecutive-failure counter on ANY success — a
    breaker that only resets on reaching some other state can trip
    permanently after a transient blip even though the dependency has
    long since recovered.

STRETCH GOALS

  - Parse the HTTP-date form of Retry-After too.
  - Add per-endpoint circuit breakers (a map keyed by host) instead of one
    global breaker.
  - Emit metrics (attempt count, breaker state transitions) via a
    injectable callback/interface instead of just returning them.
  - Add a token-bucket rate limit on top using golang.org/x/time/rate
    (already vendored) to cap outbound request rate independent of
    retries.
*/
