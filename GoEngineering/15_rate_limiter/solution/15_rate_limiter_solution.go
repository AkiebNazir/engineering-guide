/*
Problem 15 — Rate Limiter (reference solution)

See explanation/15_rate_limiter_explanation.go for the full spec and
rationale. This file implements the hand-rolled per-key token bucket
limiter, plus a second limiter (WrappedXRateLimiter) built on
golang.org/x/time/rate for direct comparison.

Design summary:
  - Lazy refill: each bucket computes tokens owed from time.Since(its own
    lastRefill) only when touched — no ticker goroutine per key, no global
    ticker walking every bucket.
  - Two-level locking, same shape as Problem 14's Cache: the Limiter-wide
    mutex guards only the `buckets` map (get-or-create); each bucket's own
    mutex guards its token arithmetic. A slow/contended key never blocks
    Allow calls for other keys.
  - Wait() computes an exact sleep duration from the bucket's refill rate
    instead of polling — see waitDuration.
  - Idle-bucket eviction mirrors Problem 14's Cache sweeper exactly:
    sync.Once + stop channel + WaitGroup, so Close() is synchronous.
*/
package ratelimit

import (
	"context"
	"sync"
	"time"

	"golang.org/x/time/rate"
)

// bucket is the per-key token-bucket state.
type bucket struct {
	mu         sync.Mutex
	tokens     float64
	lastRefill time.Time
	lastUsed   time.Time
}

// refillLocked adds tokens owed since lastRefill, capped at burst, and
// advances lastRefill to now. Caller must hold b.mu.
func (b *bucket) refillLocked(now time.Time, rate float64, burst int) {
	elapsed := now.Sub(b.lastRefill).Seconds()
	if elapsed > 0 {
		b.tokens += elapsed * rate
		if b.tokens > float64(burst) {
			b.tokens = float64(burst)
		}
		b.lastRefill = now
	}
}

// Limiter is a per-key token-bucket rate limiter. The zero value is not
// usable; construct with NewLimiter.
type Limiter struct {
	rate    float64
	burst   int
	idleTTL time.Duration

	mu      sync.Mutex
	buckets map[string]*bucket

	stop     chan struct{}
	stopOnce sync.Once
	wg       sync.WaitGroup
}

// NewLimiter constructs a ready-to-use Limiter and starts its idle-bucket
// sweeper. Panics if rate <= 0, burst < 1, or idleTTL <= 0.
func NewLimiter(r float64, burst int, idleTTL time.Duration) *Limiter {
	if r <= 0 {
		panic("ratelimit: rate must be > 0")
	}
	if burst < 1 {
		panic("ratelimit: burst must be >= 1")
	}
	if idleTTL <= 0 {
		panic("ratelimit: idleTTL must be > 0")
	}

	l := &Limiter{
		rate:    r,
		burst:   burst,
		idleTTL: idleTTL,
		buckets: make(map[string]*bucket),
		stop:    make(chan struct{}),
	}

	l.wg.Add(1)
	// Sweep at 1/4 of idleTTL so an idle bucket is reclaimed within a
	// bounded, proportionate delay of becoming idle, regardless of the
	// configured TTL's magnitude.
	go l.sweepLoop(idleTTL / 4)

	return l
}

// getOrCreate returns the bucket for key, creating a full one (burst
// tokens, so a fresh key can burst immediately) if it doesn't exist yet.
func (l *Limiter) getOrCreate(key string, now time.Time) *bucket {
	l.mu.Lock()
	defer l.mu.Unlock()

	if b, ok := l.buckets[key]; ok {
		return b
	}
	b := &bucket{
		tokens:     float64(l.burst),
		lastRefill: now,
		lastUsed:   now,
	}
	l.buckets[key] = b
	return b
}

// Allow reports whether a single token for key is available right now,
// consuming it if so.
func (l *Limiter) Allow(key string) bool {
	return l.AllowN(key, 1)
}

// AllowN reports whether n tokens for key are available right now,
// consuming all n if so (all-or-nothing).
func (l *Limiter) AllowN(key string, n int) bool {
	now := time.Now()
	b := l.getOrCreate(key, now)

	b.mu.Lock()
	defer b.mu.Unlock()

	b.refillLocked(now, l.rate, l.burst)
	b.lastUsed = now

	if b.tokens >= float64(n) {
		b.tokens -= float64(n)
		return true
	}
	return false
}

// waitDuration computes how long until b will have n tokens available,
// given l's refill rate. Must be called with b.mu held.
func (l *Limiter) waitDuration(b *bucket, n int) time.Duration {
	need := float64(n) - b.tokens
	if need <= 0 {
		return 0
	}
	secs := need / l.rate
	return time.Duration(secs * float64(time.Second))
}

// Wait blocks until a token for key is available or ctx is done, then
// consumes it. Does not busy-spin: each loop iteration sleeps for exactly
// the computed remaining wait (via a timer, interruptible by ctx.Done()),
// not a fixed poll interval.
func (l *Limiter) Wait(ctx context.Context, key string) error {
	for {
		now := time.Now()
		b := l.getOrCreate(key, now)

		b.mu.Lock()
		b.refillLocked(now, l.rate, l.burst)
		b.lastUsed = now
		if b.tokens >= 1 {
			b.tokens--
			b.mu.Unlock()
			return nil
		}
		d := l.waitDuration(b, 1)
		b.mu.Unlock()

		t := time.NewTimer(d)
		select {
		case <-ctx.Done():
			t.Stop()
			return ctx.Err()
		case <-t.C:
			// Recompute from scratch on the next loop iteration: another
			// goroutine may have consumed the token(s) that became
			// available while we slept, so don't assume our wait was the
			// only claim on them.
		}
	}
}

// KeyCount reports the number of currently tracked keys (buckets).
func (l *Limiter) KeyCount() int {
	l.mu.Lock()
	defer l.mu.Unlock()
	return len(l.buckets)
}

// sweepLoop periodically evicts buckets idle for longer than idleTTL,
// bounding the limiter's memory over a long-running process with high key
// churn. Holds the Limiter-wide lock only for the O(keys) scan itself.
func (l *Limiter) sweepLoop(interval time.Duration) {
	defer l.wg.Done()
	if interval <= 0 {
		interval = time.Second
	}
	t := time.NewTicker(interval)
	defer t.Stop()
	for {
		select {
		case <-l.stop:
			return
		case now := <-t.C:
			l.evictIdle(now)
		}
	}
}

func (l *Limiter) evictIdle(now time.Time) {
	l.mu.Lock()
	defer l.mu.Unlock()
	for key, b := range l.buckets {
		b.mu.Lock()
		idle := now.Sub(b.lastUsed) > l.idleTTL
		b.mu.Unlock()
		if idle {
			delete(l.buckets, key)
		}
	}
}

// Close stops the limiter's background idle-bucket sweeper and waits for
// it to actually exit before returning. Idempotent.
func (l *Limiter) Close() {
	l.stopOnce.Do(func() {
		close(l.stop)
	})
	l.wg.Wait()
}

// ============================================================================
// COMPARISON: golang.org/x/time/rate — a per-key wrapper around the
// stdlib-adjacent, production-grade token-bucket implementation, built the
// same way the hand-rolled Limiter is (map[string]*rate.Limiter, lazily
// created, guarded by a mutex) so the two are a fair, apples-to-apples
// comparison rather than "hand-rolled per-key vs. a single global limiter."
// ============================================================================

// WrappedXRateLimiter is a per-key rate limiter built on
// golang.org/x/time/rate.Limiter. Same external shape as Limiter (minus
// idle eviction, to keep the comparison focused on the token-bucket
// mechanics themselves — see the BEST PRACTICES section below for what
// x/time/rate gets right that this file's Limiter also had to get right by
// hand).
type WrappedXRateLimiter struct {
	rate  rate.Limit
	burst int

	mu       sync.Mutex
	limiters map[string]*rate.Limiter
}

// NewWrappedXRateLimiter constructs a per-key limiter backed by
// x/time/rate.Limiter instances, one per key, created lazily.
func NewWrappedXRateLimiter(r float64, burst int) *WrappedXRateLimiter {
	if r <= 0 {
		panic("ratelimit: rate must be > 0")
	}
	if burst < 1 {
		panic("ratelimit: burst must be >= 1")
	}
	return &WrappedXRateLimiter{
		rate:     rate.Limit(r),
		burst:    burst,
		limiters: make(map[string]*rate.Limiter),
	}
}

func (w *WrappedXRateLimiter) getOrCreate(key string) *rate.Limiter {
	w.mu.Lock()
	defer w.mu.Unlock()
	if lim, ok := w.limiters[key]; ok {
		return lim
	}
	lim := rate.NewLimiter(w.rate, w.burst)
	w.limiters[key] = lim
	return lim
}

// Allow reports whether a single token for key is available right now,
// consuming it if so.
func (w *WrappedXRateLimiter) Allow(key string) bool {
	return w.getOrCreate(key).Allow()
}

// AllowN reports whether n tokens for key are available right now,
// consuming all n if so.
func (w *WrappedXRateLimiter) AllowN(key string, n int) bool {
	return w.getOrCreate(key).AllowN(time.Now(), n)
}

// Wait blocks until a token for key is available or ctx is done.
// x/time/rate.Limiter.Wait already implements exactly the
// "compute-the-wait, sleep interruptibly" mechanism this file's Limiter.Wait
// implements by hand — including reserving the token up front (so a
// canceled Wait doesn't leave the reservation dangling for someone else to
// unexpectedly consume) which the hand-rolled version does not do.
func (w *WrappedXRateLimiter) Wait(ctx context.Context, key string) error {
	return w.getOrCreate(key).Wait(ctx)
}

// KeyCount reports the number of currently tracked keys.
func (w *WrappedXRateLimiter) KeyCount() int {
	w.mu.Lock()
	defer w.mu.Unlock()
	return len(w.limiters)
}

/*
BEST PRACTICES DEMONSTRATED

  - Lazy, on-touch refill instead of a ticker per bucket: a bucket that's
    never used costs nothing but a map entry until it's evicted; a bucket
    that's used does O(1) work per call regardless of how long it sat idle.
  - Fractional (float64) token accounting: truncating to an int on every
    refill would silently lower the effective rate below what was
    configured — see the explanation file's pitfalls section; this
    solution keeps tokens as float64 throughout and only compares/consumes
    against the requested integer n.
  - Two-level locking (Limiter-wide for map membership, per-bucket for
    token math) — identical lock-granularity discipline to Problem 14's
    single-flight/storage split, for the identical reason: one contended
    key must never serialize every other key.
  - Wait() computes an exact sleep duration and re-derives it after every
    wakeup instead of trusting a stale computation or polling on a fixed
    interval — no busy-spinning, no unnecessary CPU wakeups.
  - Idle-bucket eviction reuses the exact sync.Once + stop-channel +
    WaitGroup shutdown shape from Problem 14's Cache — the same pattern
    recurring across two different problems is a signal it's a real,
    reusable idiom for "background goroutine a caller must be able to
    deterministically stop," not a one-off.

ALTERNATIVE APPROACHES

  - x/time/rate.Limiter.Wait additionally RESERVES the token synchronously
    (via Reserve/ReserveN under the hood) before sleeping, so if the
    caller's context is canceled during the sleep, the reservation can be
    explicitly cancelled (Reservation.Cancel) to return the token to the
    bucket instead of losing it. This file's hand-rolled Wait does NOT
    reserve — it re-checks from scratch every wakeup — which is simpler
    but means a canceled Wait doesn't get anything "back" (nothing was
    taken from the bucket in the first place, so there's nothing to
    return); the trade-off is that x/time/rate's version can express
    "tell me the token is mine, even before I've waited for it," useful
    for building a queueing/backpressure system on top, which this
    exercise's simpler contract doesn't need.
  - A fixed-window or sliding-window-log limiter would be simpler to
    reason about but reintroduces the boundary-burst problem described in
    the explanation file — token bucket is preferred here specifically
    because it doesn't have that failure mode.
  - For a distributed (multi-instance) limiter, the lazy-refill trick
    still applies, but the bucket state has to live somewhere shared (e.g.
    Redis) with an atomic check-and-decrement (a Lua script, since a
    naive GET-then-SET from two instances races exactly like the
    check-then-act bugs called out in Problems 14 and 16) — out of scope
    here but a direct escalation of everything demonstrated in-process.
*/
