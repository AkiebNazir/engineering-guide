// Package main — reference solution for Problem 03: API client with
// retries, backoff/jitter, and a circuit breaker.
//
// See ../explanation/03_api_client_with_retries_explanation.go for the
// full spec, acceptance criteria, hints, and stretch goals.
package main

import (
	"context"
	"errors"
	"fmt"
	"io"
	"log"
	"math/rand"
	"net/http"
	"net/http/httptest"
	"strconv"
	"sync"
	"time"
)

// ---------------------------------------------------------------------------
// httpDoer — the seam that makes everything in this file testable without
// a real network call. *http.Client satisfies it. A CircuitBreaker (below)
// also satisfies it, which is what lets Client -> CircuitBreaker ->
// *http.Client compose without Client knowing a breaker is involved at
// all.
// ---------------------------------------------------------------------------

type httpDoer interface {
	Do(req *http.Request) (*http.Response, error)
}

// RetryPolicy configures retry attempts and backoff.
type RetryPolicy struct {
	MaxAttempts int
	BaseDelay   time.Duration
	MaxDelay    time.Duration
}

// sleepFunc is a ctx-aware sleep, injectable for tests so backoff logic
// can be exercised without real wall-clock delays.
type sleepFunc func(ctx context.Context, d time.Duration) error

// ctxSleep is the real, production sleepFunc: it blocks for d or until
// ctx is canceled, whichever comes first — a plain time.Sleep cannot be
// interrupted, which would make a canceled caller wait out the full
// backoff for no reason.
func ctxSleep(ctx context.Context, d time.Duration) error {
	if d <= 0 {
		return ctx.Err()
	}
	t := time.NewTimer(d)
	defer t.Stop()
	select {
	case <-t.C:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

// Client wraps an httpDoer with retry/backoff logic.
type Client struct {
	doer   httpDoer
	policy RetryPolicy
	sleep  sleepFunc
	rng    func() float64 // uniform [0,1); injectable for deterministic jitter tests
}

// NewClient returns a Client wrapping doer with the given retry policy,
// using real ctx-aware sleeping and math/rand for jitter.
func NewClient(doer httpDoer, policy RetryPolicy) *Client {
	if policy.MaxAttempts < 1 {
		policy.MaxAttempts = 1
	}
	return &Client{
		doer:   doer,
		policy: policy,
		sleep:  ctxSleep,
		rng:    rand.Float64,
	}
}

// isRetryableStatus reports whether a response status should trigger a
// retry: 429 (rate limited) or any 5xx (server-side failure). Other 4xx
// codes mean the request itself is wrong and retrying identically will
// fail identically forever — not retryable. 2xx/3xx are success, also
// not retryable.
func isRetryableStatus(status int) bool {
	if status == http.StatusTooManyRequests {
		return true
	}
	return status >= 500 && status <= 599
}

// backoffDelay computes the full-jitter exponential backoff delay before
// the attempt AFTER `attemptsMade` attempts have already been made, per
// the well-known AWS "full jitter" formula:
//
//	sleep = random(0, min(cap, base * 2^attemptsMade))
//
// Full jitter (uniform over the whole range, vs "equal jitter" which
// only randomizes half the range) is deliberately used because it
// spreads retries more evenly across time — a large population of
// clients all backing off from the same outage produces far less
// synchronized "thundering herd" re-contact than any jitter strategy
// that keeps a large deterministic floor.
func backoffDelay(policy RetryPolicy, attemptsMade int, rng func() float64) time.Duration {
	if attemptsMade < 0 {
		attemptsMade = 0
	}
	// Avoid overflow for large attempt counts: cap the shift.
	shift := attemptsMade
	if shift > 30 {
		shift = 30
	}
	backoff := policy.BaseDelay * time.Duration(uint64(1)<<uint(shift))
	if backoff <= 0 || backoff > policy.MaxDelay { // overflow or over cap
		backoff = policy.MaxDelay
	}
	if backoff <= 0 {
		return 0
	}
	return time.Duration(rng() * float64(backoff))
}

// parseRetryAfter parses a Retry-After header in delta-seconds form
// ("120") and returns the resulting duration. The HTTP-date form
// ("Wed, 21 Oct ... GMT") is intentionally not supported here — a real
// client should also try http.ParseTime — documented as a known,
// acceptable gap for this problem's scope (see STRETCH GOALS).
func parseRetryAfter(header string) (time.Duration, bool) {
	if header == "" {
		return 0, false
	}
	secs, err := strconv.Atoi(header)
	if err != nil || secs < 0 {
		return 0, false
	}
	return time.Duration(secs) * time.Second, true
}

// maxRetryAfter caps how long we'll honor a server-supplied Retry-After,
// so a broken or hostile upstream can't stall a caller indefinitely by
// claiming a huge delay.
const maxRetryAfter = 30 * time.Second

// Do performs req, retrying transient failures per c.policy.
//
// Design notes on the loop structure:
//   - ctx is the budget for the WHOLE operation, not each attempt: we
//     check ctx.Err() before every attempt and treat cancellation as
//     immediately terminal (no point retrying past a deadline the caller
//     already gave up on).
//   - Each attempt gets a fresh *http.Request via req.Clone, with the
//     body re-armed from GetBody — an http.Request's Body is a single-use
//     io.ReadCloser; reusing the original request object across attempts
//     would send an empty body on every retry after the first.
//   - A response we're about to discard (because we're going to retry)
//     MUST have its body drained and closed first, or the underlying
//     transport can't reuse the TCP connection — a classic, easy-to-miss
//     performance bug that silently turns every retried request into a
//     fresh connection.
func (c *Client) Do(ctx context.Context, req *http.Request) (*http.Response, error) {
	if req.Body != nil && req.GetBody == nil {
		return nil, errors.New("api client: request body must support GetBody for retries (use NewRequestWithContext with a body that implements GetBody, e.g. via bytes.NewReader)")
	}

	var lastResp *http.Response
	var lastErr error

	for attempt := 1; attempt <= c.policy.MaxAttempts; attempt++ {
		if err := ctx.Err(); err != nil {
			if lastResp != nil {
				lastResp.Body.Close()
			}
			return nil, fmt.Errorf("api client: context done before attempt %d: %w", attempt, err)
		}

		attemptReq := req.Clone(ctx)
		if req.GetBody != nil {
			body, err := req.GetBody()
			if err != nil {
				return nil, fmt.Errorf("api client: GetBody for attempt %d: %w", attempt, err)
			}
			attemptReq.Body = body
		}

		resp, err := c.doer.Do(attemptReq)
		lastResp, lastErr = resp, err

		if err != nil {
			if ctxErr := ctx.Err(); ctxErr != nil {
				// The error is (or is caused by) cancellation — stop
				// immediately rather than retrying a context that's
				// already dead. Wrap ctx.Err() itself (not the raw doer
				// error) so callers can errors.Is(err, context.Canceled)
				// / context.DeadlineExceeded reliably regardless of how
				// the underlying transport happened to phrase its own
				// error for a canceled request.
				return nil, fmt.Errorf("api client: after %d attempt(s): %w", attempt, ctxErr)
			}
			if attempt == c.policy.MaxAttempts {
				return nil, fmt.Errorf("api client: after %d attempt(s): %w", attempt, err)
			}
			if sleepErr := c.sleep(ctx, backoffDelay(c.policy, attempt-1, c.rng)); sleepErr != nil {
				return nil, fmt.Errorf("api client: context done during backoff after attempt %d: %w", attempt, sleepErr)
			}
			continue
		}

		if !isRetryableStatus(resp.StatusCode) {
			return resp, nil
		}
		if attempt == c.policy.MaxAttempts {
			return resp, nil // caller gets the last (failing) response, not an error
		}

		delay := backoffDelay(c.policy, attempt-1, c.rng)
		if ra, ok := parseRetryAfter(resp.Header.Get("Retry-After")); ok {
			if ra > maxRetryAfter {
				ra = maxRetryAfter
			}
			delay = ra
		}

		// Must drain+close before retrying so the connection can be
		// reused by the transport's pool.
		io.Copy(io.Discard, resp.Body)
		resp.Body.Close()

		if sleepErr := c.sleep(ctx, delay); sleepErr != nil {
			return nil, fmt.Errorf("api client: context done during backoff after attempt %d: %w", attempt, sleepErr)
		}
	}

	// Unreachable given MaxAttempts >= 1, but keeps the compiler happy
	// and guards against a future refactor changing the loop bounds.
	return lastResp, lastErr
}

// ---------------------------------------------------------------------------
// Circuit breaker
//
// A retry loop alone is dangerous against a FULLY down dependency: every
// caller independently retries MaxAttempts times, multiplying load on an
// already-struggling service. The circuit breaker adds a shared,
// cross-request memory of "this dependency is currently failing" so
// callers stop even trying once that's established, freeing up
// connections/goroutines/latency budget, and automatically probes for
// recovery instead of requiring an operator to intervene.
// ---------------------------------------------------------------------------

// CircuitState identifies which of the three circuit-breaker states a
// CircuitBreaker is in.
type CircuitState int

const (
	StateClosed CircuitState = iota
	StateOpen
	StateHalfOpen
)

func (s CircuitState) String() string {
	switch s {
	case StateClosed:
		return "closed"
	case StateOpen:
		return "open"
	case StateHalfOpen:
		return "half-open"
	default:
		return "unknown"
	}
}

// ErrCircuitOpen is returned by CircuitBreaker.Do when the circuit is
// open and no call was attempted.
var ErrCircuitOpen = errors.New("circuit breaker: circuit is open")

// CircuitBreaker wraps an httpDoer, tripping open after consecutive
// failures and probing recovery after a cooldown.
//
// All state is protected by a single mutex. Breakers see concurrent
// traffic from every goroutine calling through them by design — this is
// the one component in the whole file where lock contention is
// unavoidable and acceptable: the critical section is tiny (a few field
// reads/writes), and correctness (never letting two callers both think
// they own the single half-open trial slot) matters far more than
// shaving nanoseconds here.
type CircuitBreaker struct {
	mu sync.Mutex

	doer             httpDoer
	failureThreshold int
	cooldown         time.Duration

	state            CircuitState
	consecutiveFail  int
	openedAt         time.Time
	halfOpenInFlight bool
}

// NewCircuitBreaker returns a CircuitBreaker wrapping doer, tripping open
// after failureThreshold consecutive failures and attempting recovery
// after cooldown.
func NewCircuitBreaker(doer httpDoer, failureThreshold int, cooldown time.Duration) *CircuitBreaker {
	if failureThreshold < 1 {
		failureThreshold = 1
	}
	return &CircuitBreaker{
		doer:             doer,
		failureThreshold: failureThreshold,
		cooldown:         cooldown,
		state:            StateClosed,
	}
}

// State returns the breaker's current state, resolving an elapsed
// cooldown into Half-Open as a side effect of observation — this mirrors
// how the state machine is actually driven (see Do below): there's no
// background timer goroutine, just "check on access."
func (b *CircuitBreaker) State() CircuitState {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.maybeTransitionToHalfOpenLocked()
	return b.state
}

func (b *CircuitBreaker) maybeTransitionToHalfOpenLocked() {
	if b.state == StateOpen && time.Since(b.openedAt) >= b.cooldown {
		b.state = StateHalfOpen
		b.halfOpenInFlight = false
	}
}

// Do executes req through the breaker.
//
// Design decision: only network errors and 5xx responses count as
// "failures" that move the breaker toward Open. A 4xx (other than what
// isRetryableStatus already excludes for Client's own retries) means the
// CALLER sent a bad request — that's not evidence the dependency is
// unhealthy, and tripping the breaker on client-caused 4xx would
// incorrectly deny service to callers making perfectly valid, unrelated
// requests once enough bad ones came in.
func (b *CircuitBreaker) Do(req *http.Request) (*http.Response, error) {
	b.mu.Lock()
	b.maybeTransitionToHalfOpenLocked()

	switch b.state {
	case StateOpen:
		b.mu.Unlock()
		return nil, ErrCircuitOpen
	case StateHalfOpen:
		if b.halfOpenInFlight {
			// Another goroutine's trial call is already in flight; don't
			// let a second one through concurrently, or a struggling-but-
			// not-dead dependency gets hit by every waiting caller at
			// once the instant the cooldown elapses.
			b.mu.Unlock()
			return nil, ErrCircuitOpen
		}
		b.halfOpenInFlight = true
	}
	b.mu.Unlock()

	resp, err := b.doer.Do(req)

	failed := err != nil || (resp != nil && resp.StatusCode >= 500 && resp.StatusCode <= 599)

	b.mu.Lock()
	defer b.mu.Unlock()

	switch b.state {
	case StateHalfOpen:
		b.halfOpenInFlight = false
		if failed {
			b.state = StateOpen
			b.openedAt = time.Now()
			b.consecutiveFail = b.failureThreshold // stay armed to reopen immediately after next cooldown
		} else {
			b.state = StateClosed
			b.consecutiveFail = 0
		}
	case StateClosed:
		if failed {
			b.consecutiveFail++
			if b.consecutiveFail >= b.failureThreshold {
				b.state = StateOpen
				b.openedAt = time.Now()
			}
		} else {
			b.consecutiveFail = 0
		}
	}

	return resp, err
}

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------

func main() {
	// A local httptest.Server stands in for "some real upstream" so this
	// demo is runnable offline and deterministically: it fails the first
	// two requests with 503, then succeeds.
	var calls int
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		calls++
		if calls <= 2 {
			w.WriteHeader(http.StatusServiceUnavailable)
			return
		}
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("ok"))
	}))
	defer ts.Close()

	breaker := NewCircuitBreaker(http.DefaultClient, 5, 10*time.Second)
	client := NewClient(breaker, RetryPolicy{
		MaxAttempts: 4,
		BaseDelay:   50 * time.Millisecond,
		MaxDelay:    2 * time.Second,
	})

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, ts.URL, nil)
	if err != nil {
		log.Fatalf("build request: %v", err)
	}

	resp, err := client.Do(ctx, req)
	if err != nil {
		log.Fatalf("request failed: %v", err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	log.Printf("final status=%d body=%q after %d server hits, breaker state=%s", resp.StatusCode, body, calls, breaker.State())
}

/*
BEST PRACTICES

  - Make retry logic depend on a minimal interface (httpDoer), not a
    concrete *http.Client, so every layer (Client, CircuitBreaker) can be
    tested with a fake and composed in any order.
  - Treat context as an end-to-end budget: check it before every attempt
    and during every sleep, never just once at the top.
  - Always drain and close a response body you're not returning to the
    caller, to keep connection reuse working.
  - Keep "is this worth retrying" (status/error classification) as pure,
    independently testable functions (isRetryableStatus, backoffDelay,
    parseRetryAfter) separate from the stateful loop that calls them.
  - Inject time (sleep function) and randomness (rng) as fields so tests
    never need a real wall-clock sleep.

ALTERNATIVE APPROACHES / TRADE-OFFS

  - http.RoundTripper middleware instead of a wrapping Client: attaching
    retry logic as a RoundTripper (set as *http.Client's Transport) makes
    it transparent to callers using the client normally, at the cost of
    RoundTripper's contract being stricter about body-consumption and
    header-mutation rules, and losing the ability to easily pass
    additional non-http.Request retry configuration per call. A wrapping
    Client (this file's approach) is more explicit and easier to reason
    about for a teaching example; a RoundTripper is more idiomatic for a
    library meant to be a drop-in replacement for *http.Client.Transport.
  - Full jitter vs equal jitter vs no jitter: equal jitter
    (`base/2 + random(0, base/2)`) guarantees a minimum backoff (useful if
    you specifically want to avoid a near-zero retry immediately
    hammering the server again) at the cost of less spread than full
    jitter. This solution uses full jitter per AWS's documented guidance
    for the general case.
  - One global CircuitBreaker vs one per upstream host/endpoint: a single
    breaker (used here) is simplest but conflates the health of unrelated
    endpoints if a client calls many hosts through the same Client/
    breaker pair — the STRETCH GOALS section calls out a per-host map as
    the production-grade evolution.
  - Time-based half-open transition (checked lazily on access, as here)
    vs a background goroutine ticking the state machine: the lazy
    approach needs no goroutine lifecycle management (nothing to leak or
    shut down) at the cost of a breaker that's technically still "Open"
    internally between the cooldown elapsing and the next call arriving —
    harmless here since nothing observes state except through Do/State.

TESTING NOTES

  - Test retry counts with a fake httpDoer whose Do counts invocations and
    returns a scripted sequence of responses/errors.
  - Test backoff purely: call backoffDelay directly with a fixed rng
    (e.g. `func() float64 { return 1.0 }`) to get exact, non-flaky
    expected durations instead of range assertions.
  - Test ctx cancellation by canceling a context mid-retry (e.g. via a
    fake sleep func that cancels the context the first time it's called)
    and asserting no further attempts occur.
  - Test the breaker's concurrency safety with `go test -race` and many
    goroutines calling Do simultaneously while it's transitioning states.

FAILURE MODES TO CONSIDER

  - A dependency that returns 200 with a malformed/error-shaped body: this
    client only inspects status codes, not body content — a real system
    layering an "application-level error" convention on top of HTTP 200
    needs its own retry classification above this layer.
  - Retry-After claiming an enormous delay: capped at maxRetryAfter here;
    without a cap, a single misbehaving/hostile response could stall a
    caller indefinitely.
  - Clock skew or a paused process (e.g. laptop sleep) between when a
    breaker opens and when State()/Do() is next called: time.Since-based
    cooldown checking means a very long pause is indistinguishable from
    "cooldown definitely elapsed," which is the correct, safe direction
    to be wrong in (it just tries again a bit eagerly, rather than
    getting stuck open forever).
*/
