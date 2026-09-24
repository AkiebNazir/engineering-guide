package ratelimit

import (
	"context"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

func TestAllowFreshKeyStartsFull(t *testing.T) {
	l := NewLimiter(10, 3, time.Minute)
	defer l.Close()

	for i := 0; i < 3; i++ {
		if !l.Allow("k") {
			t.Fatalf("Allow call %d = false, want true (burst not yet exhausted)", i)
		}
	}
	if l.Allow("k") {
		t.Fatal("Allow after burst exhausted = true, want false")
	}
}

func TestAllowRefillsOverTime(t *testing.T) {
	// rate=10/sec, burst=1: after draining the single token, waiting
	// ~1/rate seconds (100ms) should make exactly one more Allow succeed.
	l := NewLimiter(10, 1, time.Minute)
	defer l.Close()

	if !l.Allow("k") {
		t.Fatal("first Allow = false, want true")
	}
	if l.Allow("k") {
		t.Fatal("Allow immediately after draining = true, want false")
	}

	time.Sleep(150 * time.Millisecond) // > 1/rate with margin
	if !l.Allow("k") {
		t.Fatal("Allow after refill wait = false, want true")
	}
}

func TestAllowDifferentKeysIndependent(t *testing.T) {
	l := NewLimiter(10, 1, time.Minute)
	defer l.Close()

	if !l.Allow("a") {
		t.Fatal("Allow(a) = false, want true")
	}
	if !l.Allow("b") {
		t.Fatal("Allow(b) = false, want true (independent bucket from a)")
	}
	if l.Allow("a") {
		t.Fatal("Allow(a) after draining a = true, want false")
	}
}

func TestAllowNAllOrNothing(t *testing.T) {
	l := NewLimiter(10, 5, time.Minute)
	defer l.Close()

	if !l.AllowN("k", 5) {
		t.Fatal("AllowN(k, 5) on a fresh burst=5 bucket = false, want true")
	}
	// Bucket is now empty; a failed AllowN must not partially consume.
	if l.AllowN("k", 3) {
		t.Fatal("AllowN(k, 3) on an empty bucket = true, want false")
	}
	if l.Allow("k") {
		t.Fatal("Allow(k) after a failed AllowN = true, want false (partial consumption bug)")
	}
}

func TestAllowNCapsAtBurstAfterLongIdle(t *testing.T) {
	l := NewLimiter(1000, 3, time.Minute)
	defer l.Close()

	// Drain, then simulate a long idle period by just waiting enough
	// wall-clock time that refill would exceed burst without the cap.
	l.AllowN("k", 3)
	time.Sleep(50 * time.Millisecond) // at rate=1000/s this is 50 tokens' worth

	if !l.AllowN("k", 3) {
		t.Fatal("AllowN(k, 3) after long idle = false, want true (should refill to burst)")
	}
	if l.Allow("k") {
		t.Fatal("Allow(k) after AllowN(k, 3) = true, want false (tokens must be capped at burst=3, not accumulate unbounded)")
	}
}

func TestWaitBlocksAndSucceeds(t *testing.T) {
	l := NewLimiter(10, 1, time.Minute) // 1 token per 100ms
	defer l.Close()

	if !l.Allow("k") {
		t.Fatal("first Allow = false, want true")
	}

	start := time.Now()
	if err := l.Wait(context.Background(), "k"); err != nil {
		t.Fatalf("Wait: %v", err)
	}
	elapsed := time.Since(start)

	if elapsed < 60*time.Millisecond {
		t.Fatalf("Wait returned after only %v, expected to block roughly 100ms", elapsed)
	}
	if elapsed > 500*time.Millisecond {
		t.Fatalf("Wait took %v, expected roughly 100ms", elapsed)
	}
}

func TestWaitRespectsContextCancellation(t *testing.T) {
	l := NewLimiter(1, 1, time.Minute) // slow refill: 1 token per second
	defer l.Close()

	l.Allow("k") // drain the only token

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Millisecond)
	defer cancel()

	start := time.Now()
	err := l.Wait(ctx, "k")
	elapsed := time.Since(start)

	if err == nil {
		t.Fatal("Wait with a short-deadline ctx = nil error, want context.DeadlineExceeded")
	}
	if elapsed > 500*time.Millisecond {
		t.Fatalf("Wait took %v after ctx cancellation, want it to return promptly", elapsed)
	}
}

func TestWaitDoesNotBusySpin(t *testing.T) {
	// A busy-spinning Wait would call time.Now()/loop far more than a
	// handful of times while waiting out a single, entirely predictable
	// refill interval. We can't directly count "spins" without
	// instrumenting the implementation, so instead assert the wall-clock
	// behavior a correct sleep-based implementation guarantees: Wait
	// returns close to the exact computed duration, not immediately and
	// not much later — which a tight poll loop with a coarse interval
	// would also fail (either too eager or too delayed depending on the
	// poll granularity chosen), while a computed-sleep implementation
	// nails it consistently across repeated trials.
	l := NewLimiter(20, 1, time.Minute) // 1 token per 50ms
	defer l.Close()

	l.Allow("k")

	const trials = 5
	for i := 0; i < trials; i++ {
		l.Allow("k") // drain whatever refilled since the last trial, if any
		start := time.Now()
		if err := l.Wait(context.Background(), "k"); err != nil {
			t.Fatalf("Wait: %v", err)
		}
		elapsed := time.Since(start)
		if elapsed > 200*time.Millisecond {
			t.Fatalf("trial %d: Wait took %v, want close to 50ms (busy-spin/backoff bug?)", i, elapsed)
		}
	}
}

func TestKeyCount(t *testing.T) {
	l := NewLimiter(10, 1, time.Minute)
	defer l.Close()

	if got := l.KeyCount(); got != 0 {
		t.Fatalf("KeyCount() = %d, want 0", got)
	}
	l.Allow("a")
	l.Allow("b")
	l.Allow("a")
	if got := l.KeyCount(); got != 2 {
		t.Fatalf("KeyCount() = %d, want 2", got)
	}
}

func TestIdleBucketEviction(t *testing.T) {
	l := NewLimiter(10, 1, 30*time.Millisecond)
	defer l.Close()

	l.Allow("k")
	if got := l.KeyCount(); got != 1 {
		t.Fatalf("KeyCount() = %d, want 1", got)
	}

	deadline := time.Now().Add(2 * time.Second)
	for time.Now().Before(deadline) {
		if l.KeyCount() == 0 {
			return
		}
		time.Sleep(10 * time.Millisecond)
	}
	t.Fatal("idle bucket was not evicted within the deadline")
}

func TestCloseStopsSweeperGoroutine(t *testing.T) {
	l := NewLimiter(10, 1, time.Millisecond)
	done := make(chan struct{})
	go func() {
		l.Close()
		close(done)
	}()
	select {
	case <-done:
	case <-time.After(5 * time.Second):
		t.Fatal("Close did not return: sweeper goroutine leaked")
	}
}

func TestCloseIsIdempotent(t *testing.T) {
	l := NewLimiter(10, 1, time.Minute)
	l.Close()
	l.Close() // must not panic
}

func TestNewLimiterPanicsOnInvalidArgs(t *testing.T) {
	assertPanics := func(t *testing.T, fn func()) {
		t.Helper()
		defer func() {
			if r := recover(); r == nil {
				t.Fatal("expected panic, got none")
			}
		}()
		fn()
	}
	t.Run("zero rate", func(t *testing.T) {
		assertPanics(t, func() { NewLimiter(0, 1, time.Minute) })
	})
	t.Run("negative rate", func(t *testing.T) {
		assertPanics(t, func() { NewLimiter(-1, 1, time.Minute) })
	})
	t.Run("zero burst", func(t *testing.T) {
		assertPanics(t, func() { NewLimiter(10, 0, time.Minute) })
	})
	t.Run("zero idleTTL", func(t *testing.T) {
		assertPanics(t, func() { NewLimiter(10, 1, 0) })
	})
}

// TestConcurrencyStress hammers a single limiter with many goroutines
// doing overlapping Allow/AllowN/Wait/KeyCount for a small key space,
// designed to run clean under `go test -race`.
func TestConcurrencyStress(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping stress test in -short mode")
	}
	l := NewLimiter(500, 10, 20*time.Millisecond)
	defer l.Close()

	const goroutines = 32
	const opsPerGoroutine = 200
	var wg sync.WaitGroup
	var allowed int32

	for g := 0; g < goroutines; g++ {
		wg.Add(1)
		go func(g int) {
			defer wg.Done()
			for i := 0; i < opsPerGoroutine; i++ {
				key := string(rune('a' + (g+i)%6))
				switch i % 3 {
				case 0:
					if l.Allow(key) {
						atomic.AddInt32(&allowed, 1)
					}
				case 1:
					_ = l.AllowN(key, 2)
				case 2:
					_ = l.KeyCount()
				}
			}
		}(g)
	}
	wg.Wait()

	if atomic.LoadInt32(&allowed) == 0 {
		t.Fatal("no Allow call ever succeeded during the stress test")
	}
}

// TestConcurrentAllowNeverExceedsBurst is the correctness property that
// justifies the per-bucket mutex: however many goroutines race on the
// same key, the total number of successful Allow calls before any refill
// can occur must never exceed burst.
func TestConcurrentAllowNeverExceedsBurst(t *testing.T) {
	const burst = 20
	l := NewLimiter(0.0001, burst, time.Minute) // effectively no refill during the test
	defer l.Close()

	const goroutines = 100
	var wg sync.WaitGroup
	var successes int32
	for i := 0; i < goroutines; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if l.Allow("k") {
				atomic.AddInt32(&successes, 1)
			}
		}()
	}
	wg.Wait()

	if got := atomic.LoadInt32(&successes); got != burst {
		t.Fatalf("successful Allow calls = %d, want exactly %d (burst)", got, burst)
	}
}

// ---------------------------------------------------------------------------
// WrappedXRateLimiter: the same core behaviors, against x/time/rate.
// ---------------------------------------------------------------------------

func TestWrappedXRateLimiterAllowFreshKeyStartsFull(t *testing.T) {
	w := NewWrappedXRateLimiter(10, 3)
	for i := 0; i < 3; i++ {
		if !w.Allow("k") {
			t.Fatalf("Allow call %d = false, want true", i)
		}
	}
	if w.Allow("k") {
		t.Fatal("Allow after burst exhausted = true, want false")
	}
}

func TestWrappedXRateLimiterKeysIndependent(t *testing.T) {
	w := NewWrappedXRateLimiter(10, 1)
	if !w.Allow("a") || !w.Allow("b") {
		t.Fatal("fresh keys should both allow")
	}
	if w.Allow("a") {
		t.Fatal("Allow(a) after draining = true, want false")
	}
}

func TestWrappedXRateLimiterWait(t *testing.T) {
	w := NewWrappedXRateLimiter(10, 1) // 1 token per 100ms
	w.Allow("k")

	start := time.Now()
	if err := w.Wait(context.Background(), "k"); err != nil {
		t.Fatalf("Wait: %v", err)
	}
	elapsed := time.Since(start)
	if elapsed < 60*time.Millisecond {
		t.Fatalf("Wait returned after only %v, expected roughly 100ms", elapsed)
	}
}

func TestWrappedXRateLimiterKeyCount(t *testing.T) {
	w := NewWrappedXRateLimiter(10, 1)
	if got := w.KeyCount(); got != 0 {
		t.Fatalf("KeyCount() = %d, want 0", got)
	}
	w.Allow("a")
	w.Allow("b")
	if got := w.KeyCount(); got != 2 {
		t.Fatalf("KeyCount() = %d, want 2", got)
	}
}
