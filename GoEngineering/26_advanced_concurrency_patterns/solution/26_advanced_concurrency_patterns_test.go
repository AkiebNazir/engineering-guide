package advconc

import (
	"context"
	"errors"
	"fmt"
	"runtime"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

// ----------------------------------------------------------------------------
// FetchAll
// ----------------------------------------------------------------------------

func TestFetchAllPreservesOrderAndRespectsLimit(t *testing.T) {
	const limit = 3
	ids := make([]int, 20)
	for i := range ids {
		ids[i] = i
	}

	var inFlight, highWater atomic.Int32
	fetch := func(ctx context.Context, id int) (string, error) {
		n := inFlight.Add(1)
		defer inFlight.Add(-1)
		for { // lock-free max
			hw := highWater.Load()
			if n <= hw || highWater.CompareAndSwap(hw, n) {
				break
			}
		}
		// Later ids finish first, so order can only be right by index-writes.
		time.Sleep(time.Duration(20-id) * time.Millisecond / 4)
		return fmt.Sprintf("item-%d", id), nil
	}

	got, err := FetchAll(context.Background(), ids, limit, fetch)
	if err != nil {
		t.Fatalf("FetchAll: %v", err)
	}
	for i, v := range got {
		if want := fmt.Sprintf("item-%d", i); v != want {
			t.Fatalf("got[%d] = %q, want %q", i, v, want)
		}
	}
	if hw := highWater.Load(); hw > limit {
		t.Fatalf("high-water concurrency = %d, limit %d", hw, limit)
	}
	t.Logf("high-water concurrency observed: %d (limit %d)", highWater.Load(), limit)
}

func TestFetchAllFailsFastAndCancelsSiblings(t *testing.T) {
	boom := errors.New("boom")
	var cancelled atomic.Int32

	fetch := func(ctx context.Context, id int) (string, error) {
		if id == 2 {
			time.Sleep(10 * time.Millisecond)
			return "", boom
		}
		select {
		case <-ctx.Done(): // well-behaved: honour cancellation
			cancelled.Add(1)
			return "", ctx.Err()
		case <-time.After(2 * time.Second):
			return "slow", nil
		}
	}

	start := time.Now()
	got, err := FetchAll(context.Background(), []int{0, 1, 2, 3}, 0, fetch)
	elapsed := time.Since(start)

	if !errors.Is(err, boom) {
		t.Fatalf("err = %v, want boom", err)
	}
	if got != nil {
		t.Fatalf("results = %v, want nil on error", got)
	}
	if elapsed > 500*time.Millisecond {
		t.Fatalf("took %v; fail-fast should return in ~10ms, not wait for 2s siblings", elapsed)
	}
	if c := cancelled.Load(); c != 3 {
		t.Fatalf("siblings that observed cancellation = %d, want 3", c)
	}
	t.Logf("returned after %v with 3 siblings cancelled", elapsed.Round(time.Millisecond))
}

// ----------------------------------------------------------------------------
// BlockingQueue
// ----------------------------------------------------------------------------

func TestBlockingQueueProducersConsumers(t *testing.T) {
	q := NewBlockingQueue[int](4)
	const producers, perProducer = 4, 250

	var wg sync.WaitGroup
	for p := range producers {
		wg.Go(func() {
			for i := range perProducer {
				if err := q.Put(p*perProducer + i); err != nil {
					t.Errorf("Put: %v", err)
					return
				}
			}
		})
	}

	var sum atomic.Int64
	var consumers sync.WaitGroup
	for range 3 {
		consumers.Go(func() {
			for {
				v, ok := q.Get()
				if !ok {
					return
				}
				sum.Add(int64(v))
			}
		})
	}

	wg.Wait()
	q.Close()
	consumers.Wait()

	n := int64(producers * perProducer)
	if want := n * (n - 1) / 2; sum.Load() != want {
		t.Fatalf("sum = %d, want %d (items lost or duplicated)", sum.Load(), want)
	}
}

func TestBlockingQueuePutBlocksWhenFull(t *testing.T) {
	q := NewBlockingQueue[string](1)
	if err := q.Put("a"); err != nil {
		t.Fatal(err)
	}

	done := make(chan struct{})
	go func() {
		_ = q.Put("b") // must block: capacity 1 is used
		close(done)
	}()

	select {
	case <-done:
		t.Fatal("Put on a full queue returned without blocking")
	case <-time.After(50 * time.Millisecond):
	}

	if v, _ := q.Get(); v != "a" {
		t.Fatalf("Get = %q, want a", v)
	}
	select {
	case <-done: // Get freed a slot → Signal(notFull) → Put proceeds
	case <-time.After(time.Second):
		t.Fatal("Put was not woken after Get freed a slot (lost wakeup)")
	}
	if v, _ := q.Get(); v != "b" {
		t.Fatalf("Get = %q, want b", v)
	}
}

func TestBlockingQueueCloseWakesAllWaitersAndDrains(t *testing.T) {
	q := NewBlockingQueue[int](2)

	const waiters = 5
	var woke sync.WaitGroup
	for range waiters {
		woke.Go(func() {
			if _, ok := q.Get(); ok {
				t.Error("Get on closed empty queue returned ok=true")
			}
		})
	}
	time.Sleep(20 * time.Millisecond) // let them park in cond.Wait
	q.Close()

	finished := make(chan struct{})
	go func() { woke.Wait(); close(finished) }()
	select {
	case <-finished:
	case <-time.After(time.Second):
		t.Fatal("Close did not wake every blocked Get")
	}

	if err := q.Put(1); !errors.Is(err, ErrQueueClosed) {
		t.Fatalf("Put after Close = %v, want ErrQueueClosed", err)
	}
	q.Close() // idempotent
}

// TestLesson_SignalOnCloseStrandsWaiters proves WHY Close must Broadcast.
// signalQueue is a deliberately broken queue that Signals once on close.
func TestLesson_SignalOnCloseStrandsWaiters(t *testing.T) {
	type signalQueue struct {
		mu     sync.Mutex
		cond   *sync.Cond
		closed bool
	}
	q := &signalQueue{}
	q.cond = sync.NewCond(&q.mu)

	var woken atomic.Int32
	for range 3 {
		go func() {
			q.mu.Lock()
			for !q.closed {
				q.cond.Wait()
			}
			q.mu.Unlock()
			woken.Add(1)
		}()
	}
	time.Sleep(20 * time.Millisecond)

	q.mu.Lock()
	q.closed = true
	q.mu.Unlock()
	q.cond.Signal() // BUG: wakes one waiter

	time.Sleep(50 * time.Millisecond)
	if got := woken.Load(); got != 1 {
		t.Fatalf("with Signal, woken = %d; expected exactly 1", got)
	}
	t.Logf("Signal on close woke %d of 3 waiters; the other 2 would hang forever", woken.Load())

	q.cond.Broadcast() // release the stranded goroutines so the test doesn't leak them
	time.Sleep(20 * time.Millisecond)
	if got := woken.Load(); got != 3 {
		t.Fatalf("after Broadcast, woken = %d, want 3", got)
	}
}

// ----------------------------------------------------------------------------
// ConfigStore
// ----------------------------------------------------------------------------

func TestConfigStoreNoLostUpdates(t *testing.T) {
	s := NewConfigStore(&Config{LogLevel: "info", MaxConns: 10, Features: map[string]bool{"a": true}})

	stop := make(chan struct{})
	var readers sync.WaitGroup
	for range 4 { // readers iterate the map while writers publish new ones
		readers.Go(func() {
			for {
				select {
				case <-stop:
					return
				default:
				}
				cfg := s.Load()
				for k, v := range cfg.Features {
					_, _ = k, v
				}
			}
		})
	}

	const writers = 50
	var wg sync.WaitGroup
	for i := range writers {
		wg.Go(func() {
			s.Update(func(next *Config) {
				next.MaxConns++
				next.Features[fmt.Sprintf("flag-%d", i)] = true // safe: private clone
			})
		})
	}
	wg.Wait()
	close(stop)
	readers.Wait()

	cfg := s.Load()
	if cfg.MaxConns != 10+writers {
		t.Fatalf("MaxConns = %d, want %d (lost update)", cfg.MaxConns, 10+writers)
	}
	if len(cfg.Features) != 1+writers {
		t.Fatalf("len(Features) = %d, want %d", len(cfg.Features), 1+writers)
	}
	if v := s.Version(); v != writers {
		t.Fatalf("Version = %d, want %d", v, writers)
	}
}

// TestLesson_StoreWithoutCASLosesUpdates proves why Update uses
// CompareAndSwap: the same workload with Load+Store loses writes.
func TestLesson_StoreWithoutCASLosesUpdates(t *testing.T) {
	var p atomic.Pointer[Config]
	p.Store(&Config{})

	const writers = 200
	var start sync.WaitGroup
	start.Add(1)
	var wg sync.WaitGroup
	for range writers {
		wg.Go(func() {
			start.Wait()
			old := p.Load()
			next := *old
			runtime.Gosched() // widen the window, as real work would
			next.MaxConns++
			p.Store(&next) // BUG: overwrites concurrent writers
		})
	}
	start.Done()
	wg.Wait()

	got := p.Load().MaxConns
	t.Logf("Load+Store with %d concurrent writers kept %d updates (%d lost)", writers, got, writers-got)
	if got == writers {
		t.Skip("no race window hit on this run; the bug is still real")
	}
}

// ----------------------------------------------------------------------------
// FirstSuccess
// ----------------------------------------------------------------------------

func TestFirstSuccessReturnsFastestAndCancelsLosers(t *testing.T) {
	var loserCancelled atomic.Bool
	slow := func(ctx context.Context) (string, error) {
		select {
		case <-ctx.Done():
			loserCancelled.Store(true)
			return "", ctx.Err()
		case <-time.After(2 * time.Second):
			return "slow", nil
		}
	}
	fast := func(ctx context.Context) (string, error) {
		time.Sleep(5 * time.Millisecond)
		return "fast", nil
	}
	failing := func(ctx context.Context) (string, error) { return "", errors.New("replica down") }

	before := runtime.NumGoroutine()
	v, err := FirstSuccess(context.Background(), slow, failing, fast)
	if err != nil || v != "fast" {
		t.Fatalf("got (%q, %v), want (fast, nil)", v, err)
	}

	deadline := time.Now().Add(time.Second)
	for time.Now().Before(deadline) && (!loserCancelled.Load() || runtime.NumGoroutine() > before) {
		time.Sleep(5 * time.Millisecond)
	}
	if !loserCancelled.Load() {
		t.Fatal("slow loser never observed cancellation")
	}
	if after := runtime.NumGoroutine(); after > before {
		t.Fatalf("goroutines before=%d after=%d: leak", before, after)
	}
}

func TestFirstSuccessAllFailJoinsErrors(t *testing.T) {
	e1, e2 := errors.New("e1"), errors.New("e2")
	_, err := FirstSuccess(context.Background(),
		func(context.Context) (int, error) { return 0, e1 },
		func(context.Context) (int, error) { return 0, e2 },
	)
	if !errors.Is(err, e1) || !errors.Is(err, e2) {
		t.Fatalf("err = %v, want both e1 and e2 joined", err)
	}

	if _, err := FirstSuccess[int](context.Background()); err == nil {
		t.Fatal("no candidates should be an error")
	}
}

// ----------------------------------------------------------------------------
// Benchmarks — atomic.Pointer vs RWMutex for a read-mostly config
// ----------------------------------------------------------------------------

// Each reader dereferences a field so the load can't be optimised away, and
// accumulates into a goroutine-local sum (a shared sink would itself be a
// contended write and would distort the measurement).
func BenchmarkConfigReadAtomic(b *testing.B) {
	s := NewConfigStore(&Config{MaxConns: 1})
	b.RunParallel(func(pb *testing.PB) {
		sum := 0
		for pb.Next() {
			sum += s.Load().MaxConns
		}
		_ = sum
	})
}

func BenchmarkConfigReadRWMutex(b *testing.B) {
	var mu sync.RWMutex
	cfg := &Config{MaxConns: 1}
	b.RunParallel(func(pb *testing.PB) {
		sum := 0
		for pb.Next() {
			mu.RLock()
			sum += cfg.MaxConns
			mu.RUnlock()
		}
		_ = sum
	})
}

// ----------------------------------------------------------------------------
// Runnable examples (go test -run Example -v)
// ----------------------------------------------------------------------------

func ExampleFetchAll() {
	lookup := map[int]string{1: "alice", 2: "bob", 3: "carol"}
	names, err := FetchAll(context.Background(), []int{3, 1, 2}, 2,
		func(ctx context.Context, id int) (string, error) { return lookup[id], nil })
	fmt.Println(names, err)
	// Output: [carol alice bob] <nil>
}

func ExampleBlockingQueue() {
	q := NewBlockingQueue[string](2)
	go func() {
		for _, job := range []string{"resize", "encode", "upload"} {
			_ = q.Put(job) // blocks on the third item until the consumer reads
		}
		q.Close()
	}()
	for {
		job, ok := q.Get()
		if !ok {
			break
		}
		fmt.Println("processing", job)
	}
	// Output:
	// processing resize
	// processing encode
	// processing upload
}

func ExampleConfigStore() {
	store := NewConfigStore(&Config{LogLevel: "info", MaxConns: 100})
	before := store.Load() // a reader holding an old snapshot

	store.Update(func(next *Config) {
		next.LogLevel = "debug"
		next.Features["new-checkout"] = true
	})

	after := store.Load()
	fmt.Println(before.LogLevel, len(before.Features)) // old snapshot untouched
	fmt.Println(after.LogLevel, after.Features["new-checkout"], store.Version())
	// Output:
	// info 0
	// debug true 1
}

func ExampleFirstSuccess() {
	replica := func(name string, delay time.Duration, fail bool) func(context.Context) (string, error) {
		return func(ctx context.Context) (string, error) {
			select {
			case <-time.After(delay):
				if fail {
					return "", errors.New(name + " failed")
				}
				return "answer from " + name, nil
			case <-ctx.Done():
				return "", ctx.Err()
			}
		}
	}
	v, err := FirstSuccess(context.Background(),
		replica("us-east", 300*time.Millisecond, false),
		replica("us-west", 1*time.Millisecond, true),
		replica("eu-west", 20*time.Millisecond, false),
	)
	fmt.Println(v, err)
	// Output: answer from eu-west <nil>
}
