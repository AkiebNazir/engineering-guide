package workerpool

import (
	"context"
	"errors"
	"fmt"
	"runtime"
	"sync/atomic"
	"testing"
	"time"
)

// waitForGoroutineBaseline polls runtime.NumGoroutine() until it returns to
// (at most) `baseline`, or fails the test after a timeout. Goroutine
// teardown after a channel close/cancel isn't synchronous with the call
// that triggered it, so a single immediate comparison is inherently flaky.
func waitForGoroutineBaseline(t *testing.T, baseline int) {
	t.Helper()
	deadline := time.Now().Add(2 * time.Second)
	for time.Now().Before(deadline) {
		if runtime.NumGoroutine() <= baseline {
			return
		}
		time.Sleep(10 * time.Millisecond)
	}
	t.Errorf("goroutine count did not return to baseline %d, got %d", baseline, runtime.NumGoroutine())
}

func TestRunBatch_OrderPreserved(t *testing.T) {
	t.Parallel()
	jobs := make([]func(context.Context) (int, error), 10)
	for i := range jobs {
		i := i
		jobs[i] = func(ctx context.Context) (int, error) {
			// Deliberately vary completion order: later-indexed jobs finish
			// sooner, so a bug that returns arrival order instead of input
			// order would be caught.
			time.Sleep(time.Duration(10-i) * time.Millisecond)
			return i * i, nil
		}
	}

	results, err := RunBatch(context.Background(), 4, jobs)
	if err != nil {
		t.Fatalf("RunBatch: %v", err)
	}
	for i, r := range results {
		if want := i * i; r != want {
			t.Errorf("results[%d] = %d, want %d", i, r, want)
		}
	}
}

func TestRunBatch_EmptyJobs(t *testing.T) {
	t.Parallel()
	results, err := RunBatch[int](context.Background(), 4, nil)
	if err != nil {
		t.Fatalf("RunBatch(nil): %v", err)
	}
	if results == nil {
		t.Fatal("RunBatch(nil) returned nil slice, want empty non-nil slice")
	}
	if len(results) != 0 {
		t.Fatalf("RunBatch(nil) = %v, want empty", results)
	}
}

func TestRunBatch_RespectsConcurrencyLimit(t *testing.T) {
	t.Parallel()
	const concurrency = 3
	var inFlight, maxSeen int64

	jobs := make([]func(context.Context) (struct{}, error), 30)
	for i := range jobs {
		jobs[i] = func(ctx context.Context) (struct{}, error) {
			cur := atomic.AddInt64(&inFlight, 1)
			defer atomic.AddInt64(&inFlight, -1)
			for {
				max := atomic.LoadInt64(&maxSeen)
				if cur <= max || atomic.CompareAndSwapInt64(&maxSeen, max, cur) {
					break
				}
			}
			time.Sleep(5 * time.Millisecond)
			return struct{}{}, nil
		}
	}

	if _, err := RunBatch(context.Background(), concurrency, jobs); err != nil {
		t.Fatalf("RunBatch: %v", err)
	}
	if got := atomic.LoadInt64(&maxSeen); got > concurrency {
		t.Errorf("max concurrent jobs = %d, want <= %d", got, concurrency)
	}
}

func TestRunBatch_FirstErrorCancelsSiblings(t *testing.T) {
	t.Parallel()
	sentinel := errors.New("boom")
	var ranAfterFailure int64

	jobs := []func(context.Context) (int, error){
		func(ctx context.Context) (int, error) {
			return 0, sentinel
		},
		func(ctx context.Context) (int, error) {
			// This job should observe cancellation promptly rather than
			// sleeping its full duration.
			select {
			case <-ctx.Done():
				return 0, ctx.Err()
			case <-time.After(2 * time.Second):
				atomic.AddInt64(&ranAfterFailure, 1)
				return 0, nil
			}
		},
	}

	start := time.Now()
	_, err := RunBatch(context.Background(), 2, jobs)
	elapsed := time.Since(start)

	if err == nil {
		t.Fatal("expected RunBatch to return an error")
	}
	if !errors.Is(err, sentinel) {
		t.Errorf("RunBatch err = %v, want wrapping %v", err, sentinel)
	}
	if elapsed > time.Second {
		t.Errorf("RunBatch took %v, want cancellation to short-circuit well under 2s", elapsed)
	}
}

func TestRunBatch_ZeroConcurrencyMeansUnbounded(t *testing.T) {
	t.Parallel()
	jobs := make([]func(context.Context) (int, error), 5)
	for i := range jobs {
		i := i
		jobs[i] = func(ctx context.Context) (int, error) { return i, nil }
	}
	results, err := RunBatch(context.Background(), 0, jobs)
	if err != nil {
		t.Fatalf("RunBatch: %v", err)
	}
	for i, r := range results {
		if r != i {
			t.Errorf("results[%d] = %d, want %d", i, r, i)
		}
	}
}

func TestPool_BasicSubmitAndCollect(t *testing.T) {
	baseline := runtime.NumGoroutine()

	p := NewPool[int](context.Background(), 3)
	const n = 20
	for i := 0; i < n; i++ {
		i := i
		if err := p.Submit(func(ctx context.Context) (int, error) {
			return i * 2, nil
		}); err != nil {
			t.Fatalf("Submit: %v", err)
		}
	}

	go func() {
		if err := p.CloseAndWait(); err != nil {
			t.Errorf("CloseAndWait: %v", err)
		}
	}()

	seen := make(map[int]bool)
	for r := range p.Results() {
		if r.Err != nil {
			t.Errorf("unexpected task error: %v", r.Err)
		}
		seen[r.Value] = true
	}
	if len(seen) != n {
		t.Fatalf("collected %d results, want %d", len(seen), n)
	}
	for i := 0; i < n; i++ {
		if !seen[i*2] {
			t.Errorf("missing result %d", i*2)
		}
	}

	waitForGoroutineBaseline(t, baseline+2) // allow small scheduling slack
}

func TestPool_SubmitAfterCloseReturnsError(t *testing.T) {
	t.Parallel()
	p := NewPool[int](context.Background(), 2)
	if err := p.Submit(func(ctx context.Context) (int, error) { return 1, nil }); err != nil {
		t.Fatalf("Submit before close: %v", err)
	}

	go func() {
		for range p.Results() {
		}
	}()

	if err := p.CloseAndWait(); err != nil {
		t.Fatalf("CloseAndWait: %v", err)
	}

	if err := p.Submit(func(ctx context.Context) (int, error) { return 2, nil }); err == nil {
		t.Fatal("expected Submit after CloseAndWait to return an error")
	}

	// Calling CloseAndWait a second time must not panic.
	if err := p.CloseAndWait(); err != nil {
		t.Fatalf("second CloseAndWait: %v", err)
	}
}

func TestPool_ContextCancellationStopsWorkers(t *testing.T) {
	baseline := runtime.NumGoroutine()
	ctx, cancel := context.WithCancel(context.Background())
	p := NewPool[int](ctx, 2)

	if err := p.Submit(func(ctx context.Context) (int, error) {
		<-ctx.Done()
		return 0, ctx.Err()
	}); err != nil {
		t.Fatalf("Submit: %v", err)
	}

	cancel()

	// Drain results (may be empty/closed once workers exit).
	drained := make(chan struct{})
	go func() {
		for range p.Results() {
		}
		close(drained)
	}()

	select {
	case <-drained:
	case <-time.After(2 * time.Second):
		t.Fatal("results channel never closed after context cancellation")
	}

	if err := p.CloseAndWait(); err != nil && !errors.Is(err, context.Canceled) {
		t.Fatalf("CloseAndWait after cancel: %v", err)
	}

	waitForGoroutineBaseline(t, baseline+2)
}

func TestPool_TaskErrorsSurfaceInResults(t *testing.T) {
	t.Parallel()
	p := NewPool[int](context.Background(), 2)
	sentinel := fmt.Errorf("task failed")

	if err := p.Submit(func(ctx context.Context) (int, error) {
		return 0, sentinel
	}); err != nil {
		t.Fatalf("Submit: %v", err)
	}

	go func() { _ = p.CloseAndWait() }()

	r, ok := <-p.Results()
	if !ok {
		t.Fatal("expected one result before channel close")
	}
	if r.Err == nil || r.Err.Error() != sentinel.Error() {
		t.Errorf("result.Err = %v, want %v", r.Err, sentinel)
	}
}
