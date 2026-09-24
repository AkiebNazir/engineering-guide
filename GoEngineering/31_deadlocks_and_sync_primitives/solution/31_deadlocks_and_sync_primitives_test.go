package syncprim

import (
	"context"
	"errors"
	"fmt"
	"math/rand/v2"
	"os"
	"os/exec"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

// ----------------------------------------------------------------------------
// Child-process scenarios (fatal errors can't be caught in-process)
// ----------------------------------------------------------------------------

const helperEnv = "SYNCPRIM_HELPER"

func TestMain(m *testing.M) {
	switch os.Getenv(helperEnv) {
	case "all-asleep":
		// Every goroutine, including main, ends up blocked.
		var mu sync.Mutex
		mu.Lock()
		ch := make(chan int)
		go func() { mu.Lock(); ch <- 1 }()
		<-ch
		os.Exit(0)
	case "one-awake":
		// Identical deadlock, plus one unrelated goroutine that sleeps in a
		// loop (think: a metrics ticker, an HTTP server). Now the runtime
		// cannot prove a deadlock and the process just hangs.
		go func() {
			for {
				time.Sleep(10 * time.Millisecond)
			}
		}()
		var mu sync.Mutex
		mu.Lock()
		ch := make(chan int)
		go func() { mu.Lock(); ch <- 1 }()
		<-ch
		os.Exit(0)
	}
	os.Exit(m.Run())
}

func runChild(t *testing.T, args []string, env []string, timeout time.Duration) (string, bool, error) {
	t.Helper()
	if testing.Short() {
		t.Skip("spawns child processes")
	}
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()
	cmd := exec.CommandContext(ctx, args[0], args[1:]...)
	cmd.Env = append(os.Environ(), env...)
	out, err := cmd.CombinedOutput()
	return string(out), ctx.Err() != nil, err
}

func TestLesson_RuntimeDetectorOnlyFiresWhenEverythingIsAsleep(t *testing.T) {
	out, timedOut, err := runChild(t, []string{os.Args[0], "-test.run=^$"},
		[]string{helperEnv + "=all-asleep"}, 10*time.Second)
	if timedOut || err == nil || !strings.Contains(out, "all goroutines are asleep - deadlock!") {
		t.Fatalf("expected the runtime's deadlock fatal error; timedOut=%v err=%v\n%s", timedOut, err, out)
	}
	t.Logf("all goroutines blocked → %q", strings.SplitN(out, "\n", 2)[0])

	_, timedOut, _ = runChild(t, []string{os.Args[0], "-test.run=^$"},
		[]string{helperEnv + "=one-awake"}, 1500*time.Millisecond)
	if !timedOut {
		t.Fatal("with one live goroutine the deadlock should go undetected and hang")
	}
	t.Log("same deadlock + one sleeping goroutine → no detection, hung until killed after 1.5s")
}

// ----------------------------------------------------------------------------
// Lock ordering
// ----------------------------------------------------------------------------

func TestTransferConcurrentNoDeadlockConservesMoney(t *testing.T) {
	const n, initial = 8, 1_000
	accounts := make([]*Account, n)
	for i := range accounts {
		accounts[i] = NewAccount(i, initial)
	}

	finished := Completes(10*time.Second, func() {
		var wg sync.WaitGroup
		for g := range 16 {
			wg.Go(func() {
				r := rand.New(rand.NewPCG(uint64(g), 99))
				for range 5_000 {
					a, b := accounts[r.IntN(n)], accounts[r.IntN(n)]
					// Opposite-direction transfers happen constantly here.
					_ = Transfer(a, b, int64(r.IntN(50)))
				}
			})
		}
		wg.Wait()
	})
	if !finished {
		t.Fatal("ordered-lock transfers did not finish: deadlock")
	}

	var total int64
	for _, a := range accounts {
		b := a.Balance()
		if b < 0 {
			t.Fatalf("account %d went negative: %d", a.ID, b)
		}
		total += b
	}
	if total != n*initial {
		t.Fatalf("money not conserved: %d != %d", total, n*initial)
	}
}

func TestTransferErrors(t *testing.T) {
	a, b := NewAccount(1, 10), NewAccount(2, 0)
	if err := Transfer(a, a, 1); !errors.Is(err, ErrSameAccount) {
		t.Fatalf("self transfer: %v", err)
	}
	if err := Transfer(a, b, 11); !errors.Is(err, ErrInsufficientFunds) {
		t.Fatalf("overdraft: %v", err)
	}
	if a.Balance() != 10 || b.Balance() != 0 {
		t.Fatal("failed transfer must not change balances")
	}
}

// TestLesson_NaiveTransferDeadlocks forces the deadly embrace: both
// goroutines take their first lock, then both reach for the other's.
func TestLesson_NaiveTransferDeadlocks(t *testing.T) {
	a, b := NewAccount(1, 100), NewAccount(2, 100)

	var bothHoldFirstLock sync.WaitGroup
	bothHoldFirstLock.Add(2)
	barrier := func() { bothHoldFirstLock.Done(); bothHoldFirstLock.Wait() }

	finished := Completes(300*time.Millisecond, func() {
		var wg sync.WaitGroup
		wg.Go(func() { _ = TransferNaive(a, b, 10, barrier) }) // holds a, wants b
		wg.Go(func() { _ = TransferNaive(b, a, 10, barrier) }) // holds b, wants a
		wg.Wait()
	})
	if finished {
		t.Fatal("expected TransferNaive to deadlock under the forced interleaving")
	}
	t.Log("TransferNaive(a→b) + TransferNaive(b→a) with both first locks held: deadlocked (2 goroutines leaked by design)")

	// Same forced interleaving is impossible with ordered locks: whoever gets
	// account 1 first also gets account 2 first.
	c, d := NewAccount(3, 100), NewAccount(4, 100)
	if !Completes(time.Second, func() {
		var wg sync.WaitGroup
		wg.Go(func() { _ = Transfer(c, d, 10) })
		wg.Go(func() { _ = Transfer(d, c, 10) })
		wg.Wait()
	}) {
		t.Fatal("ordered Transfer deadlocked")
	}
}

func TestTransferTryBacksOffInsteadOfDeadlocking(t *testing.T) {
	a, b := NewAccount(1, 100), NewAccount(2, 100)

	// Hold b's lock for the whole attempt window: TransferTry must give up
	// with ErrContended rather than block forever.
	b.mu.Lock()
	start := time.Now()
	err := TransferTry(a, b, 10, 5, nil)
	b.mu.Unlock()
	if !errors.Is(err, ErrContended) {
		t.Fatalf("err = %v, want ErrContended", err)
	}
	t.Logf("gave up after 5 attempts in %v while b was held", time.Since(start).Round(time.Microsecond))

	// The forced opposite-direction interleaving that wedged TransferNaive:
	// one side's TryLock fails, it releases its first lock, and both finish.
	// On each goroutine's FIRST attempt only, wait until both hold their
	// first lock — so both TryLocks are guaranteed to fail once.
	var bothHold sync.WaitGroup
	bothHold.Add(2)
	var firstAttempt [2]sync.Once
	barrier := func(i int) func() {
		return func() { firstAttempt[i].Do(func() { bothHold.Done(); bothHold.Wait() }) }
	}
	var errs [2]error
	if !Completes(2*time.Second, func() {
		var wg sync.WaitGroup
		wg.Go(func() { errs[0] = TransferTry(a, b, 10, 1000, barrier(0)) })
		wg.Go(func() { errs[1] = TransferTry(b, a, 5, 1000, barrier(1)) })
		wg.Wait()
	}) {
		t.Fatal("TransferTry deadlocked")
	}
	if errs[0] != nil || errs[1] != nil {
		t.Fatalf("errors: %v", errs)
	}
	if a.Balance() != 95 || b.Balance() != 105 {
		t.Fatalf("balances a=%d b=%d, want 95/105", a.Balance(), b.Balance())
	}
}

// ----------------------------------------------------------------------------
// RWMutex recursive read lock
// ----------------------------------------------------------------------------

func TestLesson_RecursiveRLockDeadlocksWithWaitingWriter(t *testing.T) {
	scenario := func(r *Registry, get func(between func()) string) bool {
		outerHeld := make(chan struct{})
		writerQueued := make(chan struct{})
		between := func() {
			close(outerHeld)
			<-writerQueued // resume only once a writer is waiting on Lock
		}
		return Completes(300*time.Millisecond, func() {
			var wg sync.WaitGroup
			wg.Go(func() { _ = get(between) })
			wg.Go(func() {
				<-outerHeld
				go func() {
					time.Sleep(30 * time.Millisecond) // let Set block inside Lock
					close(writerQueued)
				}()
				r.Set("k", "v") // blocks: a reader holds the lock
			})
			wg.Wait()
		})
	}

	bad := NewRegistry()
	if scenario(bad, func(b func()) string { return bad.GetOrDefaultBad("k", "def", b) }) {
		t.Fatal("expected recursive RLock + waiting writer to deadlock")
	}
	t.Log("GetOrDefaultBad: outer RLock held → writer queued → inner RLock blocks behind writer → deadlock")

	good := NewRegistry()
	if !scenario(good, func(b func()) string { return good.GetOrDefault("k", "def", b) }) {
		t.Fatal("GetOrDefault (single RLock) should complete")
	}
	if v, _ := good.Get("k"); v != "v" {
		t.Fatalf("writer's value missing: %q", v)
	}
}

// ----------------------------------------------------------------------------
// Once semantics
// ----------------------------------------------------------------------------

func TestLesson_OnceValuesCachesErrorsForever(t *testing.T) {
	calls := 0
	flaky := func() (string, error) {
		calls++
		if calls == 1 {
			return "", errors.New("dns timeout")
		}
		return "db-conn", nil
	}

	stdOnce := sync.OnceValues(flaky)
	_, err1 := stdOnce()
	_, err2 := stdOnce()
	if err1 == nil || err2 == nil || calls != 1 {
		t.Fatalf("sync.OnceValues should cache the first error: calls=%d err2=%v", calls, err2)
	}
	t.Logf("sync.OnceValues: first call failed, second call returned the SAME cached error (%v)", err2)

	calls = 0
	retry := NewOnceRetry(flaky)
	if _, err := retry.Get(); err == nil {
		t.Fatal("first Get should fail")
	}
	v, err := retry.Get()
	if err != nil || v != "db-conn" {
		t.Fatalf("second Get = %q, %v", v, err)
	}
	if v, _ := retry.Get(); v != "db-conn" || calls != 2 {
		t.Fatalf("value should be cached after success; calls=%d", calls)
	}
}

func TestOnceRetryConcurrentCallersLoadOnce(t *testing.T) {
	var loads atomic.Int32
	o := NewOnceRetry(func() (int, error) {
		loads.Add(1)
		time.Sleep(20 * time.Millisecond)
		return 42, nil
	})
	var wg sync.WaitGroup
	for range 50 {
		wg.Go(func() {
			if v, err := o.Get(); v != 42 || err != nil {
				t.Errorf("Get = %d, %v", v, err)
			}
		})
	}
	wg.Wait()
	if loads.Load() != 1 {
		t.Fatalf("loads = %d, want 1 (no stampede)", loads.Load())
	}
}

// ----------------------------------------------------------------------------
// Race detector (child `go test -race`)
// ----------------------------------------------------------------------------

func TestRaceHelper(t *testing.T) {
	if os.Getenv(helperEnv) != "race" {
		t.Skip("helper for TestLesson_RaceDetector")
	}
	counter := 0
	var wg sync.WaitGroup
	for range 2 {
		wg.Go(func() { counter++ }) // unsynchronised write from two goroutines
	}
	wg.Wait()
	_ = counter
}

func TestLesson_RaceDetector(t *testing.T) {
	gobin, err := exec.LookPath("go")
	if err != nil {
		t.Skip("go not on PATH")
	}
	out, timedOut, err := runChild(t,
		[]string{gobin, "test", "-race", "-count=1", "-run", "^TestRaceHelper$", "."},
		[]string{helperEnv + "=race"}, 120*time.Second)
	if timedOut {
		t.Skip("race build took too long on this machine")
	}
	if err == nil || !strings.Contains(out, "WARNING: DATA RACE") {
		t.Fatalf("expected -race to report the counter race; err=%v\n%.800s", err, out)
	}
	t.Log("go test -race flagged `counter++` from two goroutines: WARNING: DATA RACE")
}

// ----------------------------------------------------------------------------
// Contention benchmarks
// ----------------------------------------------------------------------------

type globalCounter struct {
	mu sync.Mutex
	m  map[string]int64
}

func (c *globalCounter) Inc(k string) {
	c.mu.Lock()
	c.m[k]++
	c.mu.Unlock()
}

var benchKeys = func() []string {
	keys := make([]string, 1024)
	for i := range keys {
		keys[i] = fmt.Sprintf("route-%d", i)
	}
	return keys
}()

func BenchmarkCounterGlobalMutex(b *testing.B) {
	c := &globalCounter{m: map[string]int64{}}
	var seq atomic.Uint64
	b.RunParallel(func(pb *testing.PB) {
		i := seq.Add(1) * 7919
		for pb.Next() {
			c.Inc(benchKeys[i%uint64(len(benchKeys))])
			i++
		}
	})
}

func BenchmarkCounterSharded(b *testing.B) {
	c := NewShardedCounter()
	var seq atomic.Uint64
	b.RunParallel(func(pb *testing.PB) {
		i := seq.Add(1) * 7919
		for pb.Next() {
			c.Inc(benchKeys[i%uint64(len(benchKeys))])
			i++
		}
	})
}

func TestShardedCounter(t *testing.T) {
	c := NewShardedCounter()
	var wg sync.WaitGroup
	for range 8 {
		wg.Go(func() {
			for i := range 1000 {
				c.Inc(benchKeys[i%10])
			}
		})
	}
	wg.Wait()
	for i := range 10 {
		if got := c.Get(benchKeys[i]); got != 800 {
			t.Fatalf("%s = %d, want 800", benchKeys[i], got)
		}
	}
}

// ----------------------------------------------------------------------------
// Runnable examples
// ----------------------------------------------------------------------------

func ExampleTransfer() {
	alice, bob := NewAccount(1, 100), NewAccount(2, 50)
	var wg sync.WaitGroup
	wg.Go(func() { _ = Transfer(alice, bob, 30) }) // locks 1 then 2
	wg.Go(func() { _ = Transfer(bob, alice, 20) }) // ALSO locks 1 then 2
	wg.Wait()
	fmt.Println(alice.Balance(), bob.Balance())
	fmt.Println(Transfer(alice, bob, 1_000))
	// Output:
	// 90 60
	// syncprim: insufficient funds
}

func ExampleOnceRetry() {
	attempt := 0
	conn := NewOnceRetry(func() (string, error) {
		attempt++
		if attempt < 3 {
			return "", fmt.Errorf("attempt %d: connection refused", attempt)
		}
		return "connected", nil
	})
	for range 4 {
		v, err := conn.Get()
		fmt.Printf("%q %v\n", v, err)
	}
	// Output:
	// "" attempt 1: connection refused
	// "" attempt 2: connection refused
	// "connected" <nil>
	// "connected" <nil>
}
