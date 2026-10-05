package cache

import (
	"context"
	"errors"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

func stores() []Store {
	return []Store{StoreMutex, StoreSyncMap}
}

func TestGetMissLoadsAndCaches(t *testing.T) {
	for _, st := range stores() {
		t.Run(string(st), func(t *testing.T) {
			c := New[string, int](Options{TTL: time.Minute, SweepInterval: time.Hour, Store: st})
			defer c.Close()

			var calls int32
			load := func(ctx context.Context, key string) (int, error) {
				atomic.AddInt32(&calls, 1)
				return 42, nil
			}

			v, err := c.Get(context.Background(), "k", load)
			if err != nil {
				t.Fatalf("Get: %v", err)
			}
			if v != 42 {
				t.Fatalf("v = %d, want 42", v)
			}

			// Second Get for the same key must hit the cache, not the loader.
			v2, err := c.Get(context.Background(), "k", load)
			if err != nil {
				t.Fatalf("Get (cached): %v", err)
			}
			if v2 != 42 {
				t.Fatalf("v2 = %d, want 42", v2)
			}
			if got := atomic.LoadInt32(&calls); got != 1 {
				t.Fatalf("loader called %d times, want 1", got)
			}
		})
	}
}

func TestGetLoaderErrorNotCached(t *testing.T) {
	for _, st := range stores() {
		t.Run(string(st), func(t *testing.T) {
			c := New[string, int](Options{TTL: time.Minute, SweepInterval: time.Hour, Store: st})
			defer c.Close()

			boom := errors.New("boom")
			var calls int32
			load := func(ctx context.Context, key string) (int, error) {
				n := atomic.AddInt32(&calls, 1)
				if n == 1 {
					return 0, boom
				}
				return 7, nil
			}

			_, err := c.Get(context.Background(), "k", load)
			if !errors.Is(err, boom) {
				t.Fatalf("Get err = %v, want boom", err)
			}

			// Retry must call the loader again — errors are never cached.
			v, err := c.Get(context.Background(), "k", load)
			if err != nil {
				t.Fatalf("Get retry: %v", err)
			}
			if v != 7 {
				t.Fatalf("v = %d, want 7", v)
			}
			if got := atomic.LoadInt32(&calls); got != 2 {
				t.Fatalf("loader called %d times, want 2", got)
			}
		})
	}
}

func TestGetExpiredEntryReloads(t *testing.T) {
	for _, st := range stores() {
		t.Run(string(st), func(t *testing.T) {
			// Sweeper interval much larger than TTL so the lazy
			// expiry-on-read check, not the sweeper, is what's exercised.
			c := New[string, int](Options{TTL: 20 * time.Millisecond, SweepInterval: time.Hour, Store: st})
			defer c.Close()

			var calls int32
			load := func(ctx context.Context, key string) (int, error) {
				n := atomic.AddInt32(&calls, 1)
				return int(n), nil
			}

			v, err := c.Get(context.Background(), "k", load)
			if err != nil || v != 1 {
				t.Fatalf("Get = (%d, %v), want (1, nil)", v, err)
			}

			time.Sleep(50 * time.Millisecond)

			v2, err := c.Get(context.Background(), "k", load)
			if err != nil {
				t.Fatalf("Get after expiry: %v", err)
			}
			if v2 != 2 {
				t.Fatalf("v2 = %d, want 2 (expired entry must reload)", v2)
			}
		})
	}
}

func TestSingleFlightCollapsesConcurrentMisses(t *testing.T) {
	for _, st := range stores() {
		t.Run(string(st), func(t *testing.T) {
			c := New[string, int](Options{TTL: time.Minute, SweepInterval: time.Hour, Store: st})
			defer c.Close()

			var calls int32
			release := make(chan struct{})
			load := func(ctx context.Context, key string) (int, error) {
				atomic.AddInt32(&calls, 1)
				<-release // hold every concurrent caller here until we let go
				return 99, nil
			}

			const n = 50
			var wg sync.WaitGroup
			results := make([]int, n)
			errs := make([]error, n)
			for i := 0; i < n; i++ {
				wg.Add(1)
				go func(i int) {
					defer wg.Done()
					v, err := c.Get(context.Background(), "k", load)
					results[i] = v
					errs[i] = err
				}(i)
			}

			// Give every goroutine a chance to reach the loader/wait point.
			time.Sleep(50 * time.Millisecond)
			close(release)
			wg.Wait()

			if got := atomic.LoadInt32(&calls); got != 1 {
				t.Fatalf("loader called %d times, want exactly 1 (single-flight failed)", got)
			}
			for i := 0; i < n; i++ {
				if errs[i] != nil {
					t.Fatalf("goroutine %d: err = %v, want nil", i, errs[i])
				}
				if results[i] != 99 {
					t.Fatalf("goroutine %d: v = %d, want 99", i, results[i])
				}
			}
		})
	}
}

// TestGetContextCancelDoesNotCancelOtherWaiters exercises the "joiner"
// path specifically: the goroutine that actually calls load (the "owner")
// is not, and cannot be, unblocked by a caller-side context cancellation —
// only a goroutine WAITING on someone else's in-flight call (wait()) is
// selecting on ctx.Done(). So this test deliberately makes the owner use
// an uncancelable context and only cancels a joiner's context.
func TestGetContextCancelDoesNotCancelOtherWaiters(t *testing.T) {
	c := New[string, int](Options{TTL: time.Minute, SweepInterval: time.Hour})
	defer c.Close()

	release := make(chan struct{})
	ownerStarted := make(chan struct{})
	var ownerStartedOnce sync.Once
	load := func(ctx context.Context, key string) (int, error) {
		ownerStartedOnce.Do(func() { close(ownerStarted) })
		<-release
		return 5, nil
	}

	// Owner: uncancelable context, becomes the single-flight owner because
	// it calls Get first.
	var ownerWG sync.WaitGroup
	ownerWG.Add(1)
	var ownerVal int
	var ownerErr error
	go func() {
		defer ownerWG.Done()
		ownerVal, ownerErr = c.Get(context.Background(), "k", load)
	}()
	<-ownerStarted // owner is now blocked inside load, holding the in-flight call

	// Joiner: cancelable context, joins the existing in-flight call via
	// wait() since the owner already registered it.
	joinerCtx, cancelJoiner := context.WithCancel(context.Background())
	var joinerWG sync.WaitGroup
	joinerWG.Add(1)
	var joinerErr error
	go func() {
		defer joinerWG.Done()
		_, joinerErr = c.Get(joinerCtx, "k", load)
	}()

	time.Sleep(20 * time.Millisecond) // let the joiner reach wait()
	cancelJoiner()
	joinerWG.Wait()

	if !errors.Is(joinerErr, context.Canceled) {
		t.Fatalf("joiner err = %v, want context.Canceled", joinerErr)
	}

	// The owner's load must be unaffected by the joiner's cancellation.
	close(release)
	ownerWG.Wait()
	if ownerErr != nil {
		t.Fatalf("owner err = %v, want nil", ownerErr)
	}
	if ownerVal != 5 {
		t.Fatalf("owner v = %d, want 5", ownerVal)
	}
}

func TestSetAndDelete(t *testing.T) {
	for _, st := range stores() {
		t.Run(string(st), func(t *testing.T) {
			c := New[string, int](Options{TTL: time.Minute, SweepInterval: time.Hour, Store: st})
			defer c.Close()

			c.Set("k", 10)
			v, err := c.Get(context.Background(), "k", func(ctx context.Context, key string) (int, error) {
				t.Fatal("loader should not be called: Set already populated the entry")
				return 0, nil
			})
			if err != nil || v != 10 {
				t.Fatalf("Get after Set = (%d, %v), want (10, nil)", v, err)
			}

			c.Delete("k")
			var loaded bool
			_, err = c.Get(context.Background(), "k", func(ctx context.Context, key string) (int, error) {
				loaded = true
				return 20, nil
			})
			if err != nil {
				t.Fatalf("Get after Delete: %v", err)
			}
			if !loaded {
				t.Fatal("Get after Delete should have missed and called the loader")
			}
		})
	}
}

func TestLen(t *testing.T) {
	for _, st := range stores() {
		t.Run(string(st), func(t *testing.T) {
			c := New[string, int](Options{TTL: time.Minute, SweepInterval: time.Hour, Store: st})
			defer c.Close()

			if got := c.Len(); got != 0 {
				t.Fatalf("Len() = %d, want 0", got)
			}
			c.Set("a", 1)
			c.Set("b", 2)
			if got := c.Len(); got != 2 {
				t.Fatalf("Len() = %d, want 2", got)
			}
			c.Delete("a")
			if got := c.Len(); got != 1 {
				t.Fatalf("Len() = %d, want 1", got)
			}
		})
	}
}

func TestSweeperRemovesExpiredEntries(t *testing.T) {
	for _, st := range stores() {
		t.Run(string(st), func(t *testing.T) {
			c := New[string, int](Options{TTL: 10 * time.Millisecond, SweepInterval: 10 * time.Millisecond, Store: st})
			defer c.Close()

			c.Set("a", 1)
			if got := c.Len(); got != 1 {
				t.Fatalf("Len() = %d, want 1", got)
			}

			deadline := time.Now().Add(2 * time.Second)
			for time.Now().Before(deadline) {
				if c.Len() == 0 {
					return
				}
				time.Sleep(10 * time.Millisecond)
			}
			t.Fatal("sweeper did not remove the expired entry within the deadline")
		})
	}
}

func TestCloseStopsSweeperGoroutine(t *testing.T) {
	c := New[string, int](Options{TTL: time.Minute, SweepInterval: time.Millisecond})
	// wg.Wait() inside Close blocking forever would hang the test/suite
	// (caught by `go test`'s default timeout), which is exactly the
	// deterministic signal we want instead of a sleep-then-check.
	done := make(chan struct{})
	go func() {
		c.Close()
		close(done)
	}()
	select {
	case <-done:
	case <-time.After(5 * time.Second):
		t.Fatal("Close did not return: sweeper goroutine leaked")
	}
}

func TestCloseIsIdempotent(t *testing.T) {
	c := New[string, int](Options{TTL: time.Minute, SweepInterval: time.Hour})
	c.Close()
	c.Close() // must not panic
}

func TestGetSetDeleteAfterClose(t *testing.T) {
	c := New[string, int](Options{TTL: time.Minute, SweepInterval: time.Hour})
	c.Close()

	c.Set("k", 1) // must not panic
	v, err := c.Get(context.Background(), "k", func(ctx context.Context, key string) (int, error) {
		return 2, nil
	})
	if err != nil || v != 1 {
		t.Fatalf("Get after Close = (%d, %v), want (1, nil)", v, err)
	}
	c.Delete("k") // must not panic
}

func TestNewPanicsOnInvalidOptions(t *testing.T) {
	assertPanics := func(t *testing.T, fn func()) {
		t.Helper()
		defer func() {
			if r := recover(); r == nil {
				t.Fatal("expected panic, got none")
			}
		}()
		fn()
	}
	t.Run("zero TTL", func(t *testing.T) {
		assertPanics(t, func() { New[string, int](Options{TTL: 0, SweepInterval: time.Second}) })
	})
	t.Run("zero SweepInterval", func(t *testing.T) {
		assertPanics(t, func() { New[string, int](Options{TTL: time.Second, SweepInterval: 0}) })
	})
}

// TestConcurrencyStress hammers a single cache with many goroutines doing
// overlapping Get/Set/Delete/Len for a small key space, for both storage
// backends, designed to run clean under `go test -race`.
func TestConcurrencyStress(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping stress test in -short mode")
	}
	for _, st := range stores() {
		t.Run(string(st), func(t *testing.T) {
			c := New[int, int](Options{TTL: 15 * time.Millisecond, SweepInterval: 5 * time.Millisecond, Store: st})
			defer c.Close()

			const goroutines = 32
			const opsPerGoroutine = 200
			var wg sync.WaitGroup
			var loaderCalls int32

			load := func(ctx context.Context, key int) (int, error) {
				atomic.AddInt32(&loaderCalls, 1)
				return key * 2, nil
			}

			for g := 0; g < goroutines; g++ {
				wg.Add(1)
				go func(g int) {
					defer wg.Done()
					for i := 0; i < opsPerGoroutine; i++ {
						key := (g + i) % 8
						switch i % 4 {
						case 0:
							_, _ = c.Get(context.Background(), key, load)
						case 1:
							c.Set(key, key*3)
						case 2:
							c.Delete(key)
						case 3:
							_ = c.Len()
						}
					}
				}(g)
			}
			wg.Wait()

			if atomic.LoadInt32(&loaderCalls) == 0 {
				t.Fatal("loader was never called during the stress test")
			}
		})
	}
}
