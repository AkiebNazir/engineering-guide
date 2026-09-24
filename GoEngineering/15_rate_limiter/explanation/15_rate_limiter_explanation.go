/*
Problem 15 — Rate Limiter (hand-rolled token bucket, per-key, vs x/time/rate)

# WHAT WE'RE BUILDING

A hand-rolled, per-key token-bucket rate limiter — the algorithm behind
almost every API rate limiter you'll integrate against or build in a real
service (AWS, Stripe, GitHub's API all document token-bucket-shaped
limits) — followed by a second implementation using the stdlib-adjacent
golang.org/x/time/rate package, so you can compare a hand-rolled limiter
against the well-tested, production-grade one and understand exactly what
x/time/rate buys you.

# WHY THIS MATTERS IN REAL SYSTEMS

Rate limiting shows up at every layer of a real backend:
  - Protecting a downstream dependency from being overwhelmed by your own
    service's retry storms.
  - Enforcing a per-customer/per-API-key quota so one noisy tenant can't
    starve every other tenant sharing the same service.
  - Client-side: respecting a third-party API's documented rate limit
    instead of discovering it via 429 responses and exponential backoff.

Two design questions dominate every real rate limiter:

 1. **Per-key vs. global.** A single global limiter protects the whole
    service but lets one bad actor consume the entire budget. A per-key
    limiter (one bucket per API key, per IP, per tenant) is fairer but
    means the limiter's own memory grows with the number of distinct keys
    — which is why a real per-key limiter needs its own eviction strategy
    for buckets belonging to keys that stopped being active (otherwise:
    slow, unbounded memory leak in a long-running service with high key
    churn — direct callback to Problem 14's TTL-eviction lesson).
 2. **Token bucket vs. fixed window vs. sliding window.** Fixed window
    (e.g. "100 requests per minute, reset on the minute boundary") is
    simple but allows 2x the nominal rate in a burst straddling the window
    boundary (100 requests at 0:59, another 100 at 1:00). Token bucket
    avoids this: tokens refill continuously at a steady rate, so the
    burst-at-the-boundary problem doesn't exist, AND it naturally supports
    bursting up to the bucket's capacity — both a feature (absorb a brief
    legitimate spike) and something you must size deliberately (capacity
    is your maximum burst, not just your steady-state rate).

# CONCEPTS COVERED

  - Token bucket algorithm implemented BY HAND: capacity, refill rate,
    lazy refill computed from elapsed wall-clock time (no background
    goroutine ticking every bucket — refill is computed on demand from
    time.Since the bucket's last update, which is both simpler and cheaper
    than a per-bucket ticker goroutine)
  - Per-key limiting: `Limiter` holding one bucket per key, created
    lazily on first use
  - Bucket eviction: idle buckets (a key that stopped being used) are
    reclaimed via TTL, same pattern as Problem 14
  - `Allow() bool` (non-blocking, immediate decision) vs `Wait(ctx) error`
    (blocks until a token is available or ctx is done) — both are real API
    shapes; x/time/rate offers both and the hand-rolled version should too
  - Comparison against golang.org/x/time/rate.Limiter: same algorithm,
    battle-tested implementation — what does it get right that a first
    hand-rolled pass tends to miss?

# SPEC

	type Limiter struct { ... }
	    Per-key token-bucket rate limiter.

	func NewLimiter(rate float64, burst int, idleTTL time.Duration) *Limiter
	    rate is tokens added per second (must be > 0).
	    burst is the bucket capacity / maximum tokens (must be >= 1).
	    idleTTL is how long a key's bucket survives with no Allow/Wait
	    calls before it's eligible for eviction (must be > 0).

	func (l *Limiter) Allow(key string) bool
	    Non-blocking. Consumes one token for key if available; returns
	    whether it did.

	func (l *Limiter) AllowN(key string, n int) bool
	    Non-blocking. Consumes n tokens for key if all n are available
	    (all-or-nothing — never partially consume).

	func (l *Limiter) Wait(ctx context.Context, key string) error
	    Blocks until a token for key is available or ctx is done, then
	    consumes it. Returns ctx.Err() if ctx is done first. Must not
	    busy-spin — compute the wait duration from the bucket's refill
	    rate and sleep (interruptibly, via a timer + ctx.Done()) rather
	    than polling in a tight loop.

	func (l *Limiter) KeyCount() int
	    Number of currently tracked keys (buckets), for
	    tests/observability.

	func (l *Limiter) Close()
	    Stops the limiter's background idle-bucket sweeper. Idempotent.

ACCEPTANCE CRITERIA

  - A fresh key starts with a full bucket (burst tokens available
    immediately) — the first `burst` calls to Allow succeed, the next one
    fails (until refill catches up).
  - Refill is continuous, not steppy: after waiting long enough for
    exactly one token's worth of time to elapse (1/rate seconds), exactly
    one more Allow call succeeds.
  - Two different keys never affect each other's bucket.
  - Wait() actually blocks (verified by measuring elapsed time is close to
    the expected wait) and respects context cancellation without busy-
    spinning (verified by an iteration/wake-up count bound, not just a
    wall-clock check).
  - Concurrent Allow/AllowN/Wait/Close from many goroutines against many
    keys is race-free under `go test -race`.
  - Idle buckets are evicted after idleTTL of inactivity, bounding the
    limiter's memory over a long-running process with high key churn
    (mirrors Problem 14's TTL-eviction acceptance criterion).
*/
package ratelimit

import (
	"context"
	"time"
)

// Limiter is a per-key token-bucket rate limiter. The zero value is not
// usable; construct with NewLimiter.
//
// TODO: fields you'll likely need:
//   - rate float64, burst int, idleTTL time.Duration (from NewLimiter's args)
//   - mu sync.Mutex (or sync.RWMutex) guarding buckets
//   - buckets map[string]*bucket
//   - a stop channel + sync.WaitGroup for the idle-bucket sweeper, same
//     pattern as Problem 14's Cache
type Limiter struct {
	// TODO: fields
}

// bucket is the per-key token-bucket state.
// TODO: fields you'll likely need:
//   - mu sync.Mutex — guards tokens/lastRefill for concurrent Allow/Wait
//     calls against the SAME key (the Limiter-wide lock should only guard
//     the buckets map itself, not per-bucket token arithmetic — same
//     lock-granularity lesson as Problem 14's single-flight vs storage
//     locks)
//   - tokens float64 — fractional tokens matter: refilling "0.3 tokens"
//     between two Allow calls 300ms apart at a 1 token/sec rate must not
//     be truncated away, or your effective rate ends up lower than
//     configured
//   - lastRefill time.Time
//   - lastUsed time.Time — separate from lastRefill; touched by idle
//     sweeper eligibility, not by the refill math itself
type bucket struct {
	// TODO: fields
}

// NewLimiter constructs a ready-to-use Limiter. Panics if rate <= 0,
// burst < 1, or idleTTL <= 0.
//
// TODO: implement. Start the idle-bucket sweeper goroutine here (same
// deterministic-shutdown shape as Problem 14's Cache: a stop channel plus
// a WaitGroup that Close() waits on).
func NewLimiter(rate float64, burst int, idleTTL time.Duration) *Limiter {
	panic("TODO: implement NewLimiter")
}

// Allow reports whether a single token for key is available right now,
// consuming it if so. Non-blocking.
//
// TODO: implement in terms of AllowN(key, 1).
func (l *Limiter) Allow(key string) bool {
	panic("TODO: implement Limiter.Allow")
}

// AllowN reports whether n tokens for key are available right now,
// consuming all n if so (all-or-nothing: never consume a partial amount).
// Non-blocking.
//
// TODO: implement:
//  1. Get-or-create the bucket for key (under the Limiter-wide lock,
//     briefly).
//  2. Under the bucket's own lock: compute elapsed time since lastRefill,
//     add elapsed*rate tokens (capped at burst), update lastRefill to now.
//  3. If tokens >= n, subtract n, return true. Else return false (do NOT
//     subtract anything).
//  4. Update lastUsed for the idle sweeper regardless of outcome.
func (l *Limiter) AllowN(key string, n int) bool {
	panic("TODO: implement Limiter.AllowN")
}

// Wait blocks until a token for key is available or ctx is done, then
// consumes it.
//
// TODO: implement WITHOUT busy-spinning: if Allow fails, compute exactly
// how long until the next token will be available (from the bucket's
// current fractional token count and the refill rate) and sleep for that
// duration via a timer, selecting on ctx.Done() so cancellation wakes you
// immediately instead of waiting out the timer. Loop (another goroutine
// could have consumed the token that became available first) but each
// loop iteration should correspond to an actual state change, not a fixed
// poll interval.
func (l *Limiter) Wait(ctx context.Context, key string) error {
	panic("TODO: implement Limiter.Wait")
}

// KeyCount reports the number of currently tracked keys (buckets).
// TODO: implement.
func (l *Limiter) KeyCount() int {
	panic("TODO: implement Limiter.KeyCount")
}

// Close stops the limiter's background idle-bucket sweeper. Idempotent.
// TODO: implement, same shape as Problem 14's Cache.Close: sync.Once +
// close(stop) + wg.Wait() so Close is synchronous.
func (l *Limiter) Close() {
	panic("TODO: implement Limiter.Close")
}

/*
HINTS

  - Lazy refill (compute tokens owed from elapsed time when a bucket is
    touched) avoids needing a ticker goroutine per key or a global ticker
    that walks every bucket every tick — it only does work when a bucket
    is actually used, which is exactly the workload a per-key limiter with
    potentially thousands of keys needs.
  - Keep tokens as a float64, not an int — see the bucket struct doc
    comment. Truncating fractional tokens on every refill silently lowers
    your effective rate below what was configured; this is a common,
    subtle bug that only shows up in a precise rate-measurement test, not
    a cursory "does Allow work" test.
  - For Wait's sleep duration: if you need `n - tokens` more tokens and
    they refill at `rate` tokens/sec, the wait is
    `(n - tokens) / rate` seconds. Recompute this fresh after waking up
    (don't trust a stale computation) because another goroutine may have
    consumed tokens (or the ctx may have been canceled) while you slept.
  - x/time/rate's Limiter is a single global limiter, not per-key — to get
    a fair comparison in the comparison section of the solution file, wrap
    it the same way your hand-rolled Limiter wraps buckets: a
    map[string]*rate.Limiter, created lazily, one x/time/rate.Limiter per
    key.

COMMON PITFALLS

  - Using time.Sleep in Wait with a fixed poll interval instead of a
    computed duration — wastes CPU on unnecessary wakeups and adds up to
    the poll interval's worth of unnecessary latency on top of the actual
    wait.
  - Holding the Limiter-wide lock while doing a bucket's refill+consume
    arithmetic — serializes every key behind whichever key is currently
    being touched, the same lock-granularity mistake as Problem 14's
    single-flight/storage split.
  - Forgetting the all-or-nothing rule in AllowN: partially consuming
    tokens on a failed AllowN call corrupts the bucket's accounting for
    every subsequent caller.
  - Not bounding tokens at burst on refill — without the cap, a key that's
    idle for a very long time (hours) accumulates an unbounded number of
    tokens and can then burst far beyond the intended maximum the moment
    it's used again.
  - Leaking the idle-sweeper goroutine (same Problem-14-style mistake:
    Close() that signals but doesn't wait for the goroutine to actually
    exit).

STRETCH GOALS

  - Add a Limit(key) (available float64, retryAfter time.Duration) method
    so an HTTP handler can set X-RateLimit-Remaining / Retry-After headers
    from the same bucket state Allow reads, without a second, inconsistent
    computation.
  - Benchmark hand-rolled AllowN against golang.org/x/time/rate.Limiter's
    AllowN under contention (many goroutines, one shared key) and report
    the difference honestly.
  - Add a distributed-limiter discussion (comment-only, no implementation
    required): what changes if buckets must be shared across multiple
    service instances instead of one process (Redis + Lua script for
    atomic check-and-decrement is the standard real-world answer) and why
    the lazy-refill trick still applies there too.
*/
