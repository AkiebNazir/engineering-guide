package ctxdeep

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"runtime"
	"sync/atomic"
	"testing"
	"time"
)

// ----------------------------------------------------------------------------
// The tree: deadlines only shrink
// ----------------------------------------------------------------------------

func TestChildCannotExtendParentDeadline(t *testing.T) {
	parent, cancelP := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancelP()
	child, cancelC := context.WithTimeout(parent, 10*time.Second)
	defer cancelC()

	pd, _ := parent.Deadline()
	cd, _ := child.Deadline()
	if !cd.Equal(pd) {
		t.Fatalf("child deadline %v should equal parent's %v", cd, pd)
	}

	start := time.Now()
	<-child.Done()
	if took := time.Since(start); took > time.Second {
		t.Fatalf("child waited %v; parent's 50ms should win", took)
	}
	if !errors.Is(child.Err(), context.DeadlineExceeded) {
		t.Fatalf("child.Err() = %v", child.Err())
	}

	// And cancellation never flows UP.
	p2, cancel2 := context.WithCancel(context.Background())
	defer cancel2()
	c2, cancelChild := context.WithCancel(p2)
	cancelChild()
	if c2.Err() == nil || p2.Err() != nil {
		t.Fatal("cancelling a child must not cancel its parent")
	}
}

// ----------------------------------------------------------------------------
// Keys
// ----------------------------------------------------------------------------

func TestLesson_StringKeysCollideTypedKeysDont(t *testing.T) {
	ctx := context.Background()

	// Two unrelated packages both decide to store a "user" under a string key.
	ctx = context.WithValue(ctx, "user", "alice@auth-pkg") //nolint:staticcheck // SA1029: the point of the lesson
	ctx = context.WithValue(ctx, "user", 42)               //nolint:staticcheck // metrics pkg's "user" = numeric ID
	if _, ok := ctx.Value("user").(string); ok {
		t.Fatal("expected the auth package's value to be shadowed")
	}
	t.Logf(`string key "user" now holds %v (%T) — the auth package lost its value`, ctx.Value("user"), ctx.Value("user"))

	authUser := NewKey[string]("user")
	metricsUser := NewKey[int]("user") // same name, different key
	ctx = authUser.With(ctx, "alice@auth-pkg")
	ctx = metricsUser.With(ctx, 42)
	a, okA := authUser.Get(ctx)
	m, okM := metricsUser.Get(ctx)
	if !okA || a != "alice@auth-pkg" || !okM || m != 42 {
		t.Fatalf("typed keys collided: %q %v / %d %v", a, okA, m, okM)
	}

	if _, ok := RequestIDKey.Get(context.Background()); ok {
		t.Fatal("missing value must report ok=false")
	}
}

// ----------------------------------------------------------------------------
// Budgets and retry
// ----------------------------------------------------------------------------

func TestWithBudgetFraction(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()

	sub, subCancel, err := WithBudgetFraction(ctx, 0.2, 10*time.Millisecond)
	if err != nil {
		t.Fatal(err)
	}
	defer subCancel()
	rem, _ := Remaining(sub)
	if rem > 210*time.Millisecond || rem < 150*time.Millisecond {
		t.Fatalf("20%% of ~1s budget should be ~200ms, got %v", rem)
	}

	tight, cancelTight := context.WithTimeout(context.Background(), 5*time.Millisecond)
	defer cancelTight()
	if _, _, err := WithBudgetFraction(tight, 0.5, 50*time.Millisecond); !errors.Is(err, ErrBudgetExhausted) {
		t.Fatalf("err = %v, want ErrBudgetExhausted", err)
	}

	noDeadline, c, err := WithBudgetFraction(context.Background(), 0.5, time.Second)
	if err != nil {
		t.Fatal(err)
	}
	c()
	if _, ok := noDeadline.Deadline(); ok || noDeadline.Err() == nil {
		t.Fatal("without a parent deadline the child should be cancellable and deadline-free")
	}

	if _, _, err := WithBudgetFraction(ctx, 1.5, 0); err == nil {
		t.Fatal("fraction > 1 should be rejected")
	}
}

func TestRetryIsDeadlineAware(t *testing.T) {
	boom := errors.New("upstream 503")
	var calls atomic.Int32
	fail := func(context.Context) error { calls.Add(1); return boom }

	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()
	start := time.Now()
	err := Retry(ctx, 10, 20*time.Millisecond, fail)
	took := time.Since(start)

	if !errors.Is(err, boom) {
		t.Fatalf("last error should be preserved, got %v", err)
	}
	if !errors.Is(err, ErrBudgetExhausted) && !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("should report why it stopped, got %v", err)
	}
	if took > 100*time.Millisecond {
		t.Fatalf("Retry ran past the deadline: %v", took)
	}
	t.Logf("10 attempts requested, %d made in %v: %v", calls.Load(), took.Round(time.Millisecond), err)

	calls.Store(0)
	flaky := func(context.Context) error {
		if calls.Add(1) < 3 {
			return boom
		}
		return nil
	}
	if err := Retry(context.Background(), 5, time.Millisecond, flaky); err != nil || calls.Load() != 3 {
		t.Fatalf("flaky: err=%v calls=%d", err, calls.Load())
	}
}

// ----------------------------------------------------------------------------
// Causes and merging
// ----------------------------------------------------------------------------

func TestServerHandleReportsTheRealCause(t *testing.T) {
	s := NewServer()

	// 1. Work finishes.
	if err := s.Handle(context.Background(), time.Millisecond); err != nil {
		t.Fatalf("fast work: %v", err)
	}

	// 2. Caller's deadline.
	ctx, cancel := context.WithTimeoutCause(context.Background(), 10*time.Millisecond, errors.New("client SLA 10ms"))
	defer cancel()
	if err := s.Handle(ctx, time.Second); err == nil || err.Error() != "client SLA 10ms" {
		t.Fatalf("deadline cause: %v", err)
	}

	// 3. Shutdown while requests are in flight.
	errs := make(chan error, 3)
	for range 3 {
		go func() { errs <- s.Handle(context.Background(), 5*time.Second) }()
	}
	time.Sleep(20 * time.Millisecond)
	s.Shutdown()
	for range 3 {
		if err := <-errs; !errors.Is(err, ErrShutdown) {
			t.Fatalf("in-flight request got %v, want ErrShutdown", err)
		}
	}
}

func TestMergeCancelUnregistersCallback(t *testing.T) {
	lifetime, stopServer := context.WithCancelCause(context.Background())
	defer stopServer(nil)

	reqCtx := RequestIDKey.With(context.Background(), "req-7")
	merged, cancel := MergeCancel(reqCtx, lifetime)
	if id, _ := RequestIDKey.Get(merged); id != "req-7" {
		t.Fatal("merged context must keep the primary's values")
	}
	cancel()
	if !errors.Is(context.Cause(merged), context.Canceled) {
		t.Fatalf("cause after own cancel = %v", context.Cause(merged))
	}

	// After cancel(), cancelling the server must not re-cancel with a new
	// cause (the AfterFunc was stopped).
	stopServer(ErrShutdown)
	time.Sleep(5 * time.Millisecond)
	if errors.Is(context.Cause(merged), ErrShutdown) {
		t.Fatal("AfterFunc still registered after cancel")
	}
}

// ----------------------------------------------------------------------------
// Detach
// ----------------------------------------------------------------------------

func TestDetachKeepsValuesDropsCancellation(t *testing.T) {
	req, cancelReq := context.WithTimeout(RequestIDKey.With(context.Background(), "req-42"), time.Hour)
	cancelReq() // the handler has returned

	audit, cancel := Detach(req, 50*time.Millisecond)
	defer cancel()

	if audit.Err() != nil {
		t.Fatal("detached context was cancelled with its parent")
	}
	if id, _ := RequestIDKey.Get(audit); id != "req-42" {
		t.Fatalf("request ID lost: %q", id)
	}
	rem, ok := Remaining(audit)
	if !ok || rem > 50*time.Millisecond {
		t.Fatalf("detached context should have ITS OWN 50ms timeout, got %v %v", rem, ok)
	}
}

// ----------------------------------------------------------------------------
// Leaks
// ----------------------------------------------------------------------------

// TestLesson_ForgettingCancelRetainsChildren measures what `go vet`'s
// lostcancel check warns about: a child context you never cancel stays
// registered in its (long-lived) parent until the parent itself ends.
func TestLesson_ForgettingCancelRetainsChildren(t *testing.T) {
	const n = 100_000
	measure := func(callCancel bool) (uint64, context.CancelFunc) {
		parent, cancelParent := context.WithCancel(context.Background())
		runtime.GC()
		var before runtime.MemStats
		runtime.ReadMemStats(&before)
		// Keep the cancel funcs in a slice we then drop, rather than discarding
		// them outright: discarding is exactly what go vet's lostcancel check
		// reports, and this package must stay vet-clean.
		cancels := make([]context.CancelFunc, 0, n)
		for range n {
			_, cancel := context.WithCancel(parent)
			if callCancel {
				cancel()
			} else {
				cancels = append(cancels, cancel)
			}
		}
		cancels = nil // the funcs are unreachable now, yet the children remain registered in parent
		runtime.GC()
		var after runtime.MemStats
		runtime.ReadMemStats(&after)
		runtime.KeepAlive(parent)
		if after.HeapAlloc < before.HeapAlloc {
			return 0, cancelParent
		}
		return after.HeapAlloc - before.HeapAlloc, cancelParent
	}

	leaked, stop1 := measure(false)
	proper, stop2 := measure(true)
	stop1()
	stop2()

	t.Logf("%d children never cancelled: %.1f MB still reachable from the parent", n, float64(leaked)/(1<<20))
	t.Logf("%d children cancelled:       %.1f MB", n, float64(proper)/(1<<20))
	if leaked < 5*(1<<20) || leaked < 10*proper {
		t.Fatalf("expected uncancelled children to retain far more memory: leaked=%d proper=%d", leaked, proper)
	}
}

func TestSendContextDoesNotLeak(t *testing.T) {
	ch := make(chan int) // nobody will ever receive
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Millisecond)
	defer cancel()
	if err := SendContext(ctx, ch, 1); !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("err = %v", err)
	}
}

func TestSumUntilDone(t *testing.T) {
	in := make(chan int)
	ctx, cancel := context.WithCancelCause(context.Background())
	go func() {
		for i := 1; i <= 5; i++ {
			in <- i
		}
		cancel(errors.New("operator hit ctrl-c"))
	}()
	sum, err := SumUntilDone(ctx, in)
	if sum != 15 || err == nil || err.Error() != "operator hit ctrl-c" {
		t.Fatalf("sum=%d err=%v", sum, err)
	}

	closed := make(chan int, 2)
	closed <- 4
	closed <- 5
	close(closed)
	if sum, err := SumUntilDone(context.Background(), closed); sum != 9 || err != nil {
		t.Fatalf("drained: sum=%d err=%v", sum, err)
	}
}

// ----------------------------------------------------------------------------
// net/http: a client giving up cancels the server handler's context
// ----------------------------------------------------------------------------

func TestLesson_ClientDisconnectCancelsHandlerContext(t *testing.T) {
	observed := make(chan error, 1)
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		select {
		case <-r.Context().Done():
			observed <- r.Context().Err() // stop the expensive work: nobody is listening
		case <-time.After(5 * time.Second):
			observed <- nil
		}
	}))
	defer srv.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancel()
	req, _ := http.NewRequestWithContext(ctx, http.MethodGet, srv.URL, nil)
	start := time.Now()
	_, err := http.DefaultClient.Do(req)
	if !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("client err = %v", err)
	}

	select {
	case got := <-observed:
		if !errors.Is(got, context.Canceled) {
			t.Fatalf("handler saw %v, want context.Canceled", got)
		}
		t.Logf("client timed out at 50ms; server handler's r.Context() was cancelled %v after the request started",
			time.Since(start).Round(time.Millisecond))
	case <-time.After(2 * time.Second):
		t.Fatal("handler never noticed the client went away")
	}
}

// ----------------------------------------------------------------------------
// Runnable examples
// ----------------------------------------------------------------------------

func ExampleKey() {
	tenant := NewKey[string]("tenant")
	ctx := tenant.With(context.Background(), "acme")
	ctx = RequestIDKey.With(ctx, "req-1")

	t, _ := tenant.Get(ctx)
	id, _ := RequestIDKey.Get(ctx)
	_, missing := NewKey[string]("tenant").Get(ctx) // same name, different key
	fmt.Println(t, id, missing)
	// Output: acme req-1 false
}

func ExampleServer_Handle() {
	s := NewServer()
	done := make(chan error)
	go func() { done <- s.Handle(context.Background(), time.Minute) }()
	time.Sleep(10 * time.Millisecond)
	s.Shutdown()
	err := <-done
	fmt.Println(err, errors.Is(err, context.Canceled))
	// Output: ctxdeep: server shutting down false
}

func ExampleWithBudgetFraction() {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Millisecond)
	defer cancel()
	_, _, err := WithBudgetFraction(ctx, 0.5, 100*time.Millisecond)
	fmt.Println(errors.Is(err, ErrBudgetExhausted))
	// Output: true
}
