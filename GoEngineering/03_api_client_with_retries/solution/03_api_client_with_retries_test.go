package main

import (
	"bytes"
	"context"
	"errors"
	"io"
	"net/http"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

// fakeDoer scripts a sequence of responses/errors and counts invocations.
type fakeDoer struct {
	mu     sync.Mutex
	calls  int
	script []fakeResult
	onCall func(n int) // optional hook, invoked before each scripted result
	bodies []string    // records request bodies seen, for replay assertions
}

type fakeResult struct {
	status int
	err    error
}

func (f *fakeDoer) Do(req *http.Request) (*http.Response, error) {
	f.mu.Lock()
	n := f.calls
	f.calls++
	var body []byte
	if req.Body != nil {
		body, _ = io.ReadAll(req.Body)
	}
	f.bodies = append(f.bodies, string(body))
	f.mu.Unlock()

	if f.onCall != nil {
		f.onCall(n)
	}

	if n >= len(f.script) {
		panic("fakeDoer: script exhausted")
	}
	r := f.script[n]
	if r.err != nil {
		return nil, r.err
	}
	return &http.Response{
		StatusCode: r.status,
		Body:       io.NopCloser(bytes.NewReader(nil)),
		Header:     make(http.Header),
	}, nil
}

func (f *fakeDoer) callCount() int {
	f.mu.Lock()
	defer f.mu.Unlock()
	return f.calls
}

func noSleep(ctx context.Context, d time.Duration) error {
	return ctx.Err()
}

func newTestRequest(t *testing.T, ctx context.Context, body string) *http.Request {
	t.Helper()
	var req *http.Request
	var err error
	if body == "" {
		req, err = http.NewRequestWithContext(ctx, http.MethodGet, "http://example.invalid/", nil)
	} else {
		req, err = http.NewRequestWithContext(ctx, http.MethodPost, "http://example.invalid/", bytes.NewReader([]byte(body)))
	}
	if err != nil {
		t.Fatalf("build request: %v", err)
	}
	return req
}

func TestClient_RetriesUntilSuccess(t *testing.T) {
	doer := &fakeDoer{script: []fakeResult{
		{status: http.StatusServiceUnavailable},
		{status: http.StatusServiceUnavailable},
		{status: http.StatusOK},
	}}
	c := NewClient(doer, RetryPolicy{MaxAttempts: 5, BaseDelay: time.Millisecond, MaxDelay: 10 * time.Millisecond})
	c.sleep = noSleep

	resp, err := c.Do(context.Background(), newTestRequest(t, context.Background(), ""))
	if err != nil {
		t.Fatalf("Do returned error: %v", err)
	}
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("status = %d, want 200", resp.StatusCode)
	}
	if got := doer.callCount(); got != 3 {
		t.Fatalf("calls = %d, want 3", got)
	}
}

func TestClient_StopsAtMaxAttempts(t *testing.T) {
	doer := &fakeDoer{script: []fakeResult{
		{status: http.StatusServiceUnavailable},
		{status: http.StatusServiceUnavailable},
		{status: http.StatusServiceUnavailable},
	}}
	c := NewClient(doer, RetryPolicy{MaxAttempts: 3, BaseDelay: time.Millisecond, MaxDelay: 10 * time.Millisecond})
	c.sleep = noSleep

	resp, err := c.Do(context.Background(), newTestRequest(t, context.Background(), ""))
	if err != nil {
		t.Fatalf("Do returned error: %v", err)
	}
	if resp.StatusCode != http.StatusServiceUnavailable {
		t.Fatalf("status = %d, want 503 (last response returned as-is)", resp.StatusCode)
	}
	if got := doer.callCount(); got != 3 {
		t.Fatalf("calls = %d, want exactly MaxAttempts=3", got)
	}
}

func TestClient_DoesNotRetryClientErrors(t *testing.T) {
	doer := &fakeDoer{script: []fakeResult{
		{status: http.StatusBadRequest},
	}}
	c := NewClient(doer, RetryPolicy{MaxAttempts: 5, BaseDelay: time.Millisecond, MaxDelay: 10 * time.Millisecond})
	c.sleep = noSleep

	resp, err := c.Do(context.Background(), newTestRequest(t, context.Background(), ""))
	if err != nil {
		t.Fatalf("Do returned error: %v", err)
	}
	if resp.StatusCode != http.StatusBadRequest {
		t.Fatalf("status = %d, want 400", resp.StatusCode)
	}
	if got := doer.callCount(); got != 1 {
		t.Fatalf("calls = %d, want 1 (no retry on 400)", got)
	}
}

func TestClient_RetriesNetworkErrors(t *testing.T) {
	doer := &fakeDoer{script: []fakeResult{
		{err: errors.New("connection reset")},
		{status: http.StatusOK},
	}}
	c := NewClient(doer, RetryPolicy{MaxAttempts: 3, BaseDelay: time.Millisecond, MaxDelay: 10 * time.Millisecond})
	c.sleep = noSleep

	resp, err := c.Do(context.Background(), newTestRequest(t, context.Background(), ""))
	if err != nil {
		t.Fatalf("Do returned error: %v", err)
	}
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("status = %d, want 200", resp.StatusCode)
	}
	if got := doer.callCount(); got != 2 {
		t.Fatalf("calls = %d, want 2", got)
	}
}

func TestClient_StopsImmediatelyOnCancellation(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	doer := &fakeDoer{script: []fakeResult{
		{err: errors.New("network error")},
		{status: http.StatusOK}, // should never be reached
	}}
	doer.onCall = func(n int) {
		if n == 0 {
			cancel() // cancel right after the first (failing) attempt
		}
	}
	c := NewClient(doer, RetryPolicy{MaxAttempts: 5, BaseDelay: time.Millisecond, MaxDelay: 10 * time.Millisecond})
	c.sleep = noSleep

	_, err := c.Do(ctx, newTestRequest(t, ctx, ""))
	if err == nil {
		t.Fatal("expected error after cancellation, got nil")
	}
	if !errors.Is(err, context.Canceled) {
		t.Fatalf("error = %v, want wrapped context.Canceled", err)
	}
	if got := doer.callCount(); got != 1 {
		t.Fatalf("calls = %d, want exactly 1 (no retry past cancellation)", got)
	}
}

func TestClient_ReplaysRequestBody(t *testing.T) {
	doer := &fakeDoer{script: []fakeResult{
		{status: http.StatusServiceUnavailable},
		{status: http.StatusOK},
	}}
	c := NewClient(doer, RetryPolicy{MaxAttempts: 3, BaseDelay: time.Millisecond, MaxDelay: 10 * time.Millisecond})
	c.sleep = noSleep

	req := newTestRequest(t, context.Background(), "payload")
	_, err := c.Do(context.Background(), req)
	if err != nil {
		t.Fatalf("Do returned error: %v", err)
	}
	if len(doer.bodies) != 2 || doer.bodies[0] != "payload" || doer.bodies[1] != "payload" {
		t.Fatalf("bodies = %v, want [\"payload\", \"payload\"] (body must be replayed each attempt)", doer.bodies)
	}
}

func TestBackoffDelay_ExponentialAndCapped(t *testing.T) {
	policy := RetryPolicy{BaseDelay: 100 * time.Millisecond, MaxDelay: 2 * time.Second}
	fullJitter := func() float64 { return 1.0 } // deterministic: always take the max of the range

	tests := []struct {
		attemptsMade int
		want         time.Duration
	}{
		{0, 100 * time.Millisecond},
		{1, 200 * time.Millisecond},
		{2, 400 * time.Millisecond},
		{3, 800 * time.Millisecond},
		{4, 1600 * time.Millisecond},
		{5, 2 * time.Second}, // would be 3.2s uncapped; capped at MaxDelay
		{10, 2 * time.Second},
	}
	for _, tt := range tests {
		got := backoffDelay(policy, tt.attemptsMade, fullJitter)
		if got != tt.want {
			t.Errorf("backoffDelay(attemptsMade=%d) = %v, want %v", tt.attemptsMade, got, tt.want)
		}
	}
}

func TestBackoffDelay_ZeroJitterIsZero(t *testing.T) {
	policy := RetryPolicy{BaseDelay: 100 * time.Millisecond, MaxDelay: 2 * time.Second}
	zero := func() float64 { return 0.0 }
	got := backoffDelay(policy, 3, zero)
	if got != 0 {
		t.Fatalf("backoffDelay with rng=0 = %v, want 0", got)
	}
}

func TestIsRetryableStatus(t *testing.T) {
	tests := []struct {
		status int
		want   bool
	}{
		{200, false},
		{201, false},
		{301, false},
		{400, false},
		{404, false},
		{429, true},
		{500, true},
		{502, true},
		{503, true},
		{599, true},
	}
	for _, tt := range tests {
		if got := isRetryableStatus(tt.status); got != tt.want {
			t.Errorf("isRetryableStatus(%d) = %v, want %v", tt.status, got, tt.want)
		}
	}
}

func TestParseRetryAfter(t *testing.T) {
	tests := []struct {
		header string
		wantD  time.Duration
		wantOK bool
	}{
		{"", 0, false},
		{"120", 120 * time.Second, true},
		{"0", 0, true},
		{"-5", 0, false},
		{"not-a-number", 0, false},
	}
	for _, tt := range tests {
		gotD, gotOK := parseRetryAfter(tt.header)
		if gotOK != tt.wantOK || (gotOK && gotD != tt.wantD) {
			t.Errorf("parseRetryAfter(%q) = (%v, %v), want (%v, %v)", tt.header, gotD, gotOK, tt.wantD, tt.wantOK)
		}
	}
}

// --- Circuit breaker tests ---

type countingDoer struct {
	calls  atomic.Int64
	result fakeResult
}

func (d *countingDoer) Do(req *http.Request) (*http.Response, error) {
	d.calls.Add(1)
	if d.result.err != nil {
		return nil, d.result.err
	}
	return &http.Response{StatusCode: d.result.status, Body: io.NopCloser(bytes.NewReader(nil))}, nil
}

func TestCircuitBreaker_TripsAfterThreshold(t *testing.T) {
	doer := &countingDoer{result: fakeResult{status: http.StatusInternalServerError}}
	cb := NewCircuitBreaker(doer, 3, time.Hour)

	req := newTestRequest(t, context.Background(), "")
	for i := 0; i < 3; i++ {
		cb.Do(req)
	}
	if cb.State() != StateOpen {
		t.Fatalf("state = %v, want Open after 3 consecutive failures", cb.State())
	}

	// Further calls must fail fast without touching the doer.
	before := doer.calls.Load()
	_, err := cb.Do(req)
	if !errors.Is(err, ErrCircuitOpen) {
		t.Fatalf("err = %v, want ErrCircuitOpen", err)
	}
	if doer.calls.Load() != before {
		t.Fatalf("doer was called while circuit open: before=%d after=%d", before, doer.calls.Load())
	}
}

func TestCircuitBreaker_HalfOpenRecovery(t *testing.T) {
	doer := &countingDoer{result: fakeResult{status: http.StatusInternalServerError}}
	cb := NewCircuitBreaker(doer, 2, 20*time.Millisecond)
	req := newTestRequest(t, context.Background(), "")

	cb.Do(req)
	cb.Do(req)
	if cb.State() != StateOpen {
		t.Fatalf("state = %v, want Open", cb.State())
	}

	time.Sleep(30 * time.Millisecond) // let cooldown elapse
	if cb.State() != StateHalfOpen {
		t.Fatalf("state = %v, want HalfOpen after cooldown", cb.State())
	}

	// Trial call succeeds -> should close the circuit.
	doer.result = fakeResult{status: http.StatusOK}
	resp, err := cb.Do(req)
	if err != nil {
		t.Fatalf("half-open trial call returned error: %v", err)
	}
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("status = %d, want 200", resp.StatusCode)
	}
	if cb.State() != StateClosed {
		t.Fatalf("state = %v, want Closed after successful trial", cb.State())
	}
}

func TestCircuitBreaker_HalfOpenFailureReopens(t *testing.T) {
	doer := &countingDoer{result: fakeResult{status: http.StatusInternalServerError}}
	cb := NewCircuitBreaker(doer, 1, 20*time.Millisecond)
	req := newTestRequest(t, context.Background(), "")

	cb.Do(req) // trips open (threshold=1)
	if cb.State() != StateOpen {
		t.Fatalf("state = %v, want Open", cb.State())
	}

	time.Sleep(30 * time.Millisecond)
	if cb.State() != StateHalfOpen {
		t.Fatalf("state = %v, want HalfOpen", cb.State())
	}

	cb.Do(req) // trial call fails (doer still returns 500)
	if cb.State() != StateOpen {
		t.Fatalf("state = %v, want Open again after failed trial", cb.State())
	}
}

func TestCircuitBreaker_SuccessResetsFailureCount(t *testing.T) {
	doer := &countingDoer{result: fakeResult{status: http.StatusInternalServerError}}
	cb := NewCircuitBreaker(doer, 3, time.Hour)
	req := newTestRequest(t, context.Background(), "")

	cb.Do(req)
	cb.Do(req)
	doer.result = fakeResult{status: http.StatusOK}
	cb.Do(req) // success resets consecutive failure count
	doer.result = fakeResult{status: http.StatusInternalServerError}
	cb.Do(req)
	cb.Do(req)

	if cb.State() != StateClosed {
		t.Fatalf("state = %v, want Closed (failure streak was reset by the intervening success)", cb.State())
	}
}

func TestCircuitBreaker_ClientErrorsDoNotTripBreaker(t *testing.T) {
	doer := &countingDoer{result: fakeResult{status: http.StatusBadRequest}}
	cb := NewCircuitBreaker(doer, 2, time.Hour)
	req := newTestRequest(t, context.Background(), "")

	cb.Do(req)
	cb.Do(req)
	cb.Do(req)

	if cb.State() != StateClosed {
		t.Fatalf("state = %v, want Closed (4xx should not count as breaker failures)", cb.State())
	}
}

func TestCircuitBreaker_ConcurrentAccess(t *testing.T) {
	doer := &countingDoer{result: fakeResult{status: http.StatusOK}}
	cb := NewCircuitBreaker(doer, 5, 10*time.Millisecond)
	req := newTestRequest(t, context.Background(), "")

	var wg sync.WaitGroup
	for i := 0; i < 50; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			cb.Do(req)
		}()
	}
	wg.Wait()
	// No assertion beyond "the race detector didn't fire and nothing panicked."
}

func TestClient_RequiresReplayableBodyForRetries(t *testing.T) {
	doer := &fakeDoer{script: []fakeResult{{status: http.StatusOK}}}
	c := NewClient(doer, RetryPolicy{MaxAttempts: 3, BaseDelay: time.Millisecond, MaxDelay: time.Millisecond})
	c.sleep = noSleep

	req, _ := http.NewRequestWithContext(context.Background(), http.MethodPost, "http://example.invalid/", bytes.NewReader([]byte("x")))
	req.GetBody = nil // simulate a body that can't be replayed

	_, err := c.Do(context.Background(), req)
	if err == nil {
		t.Fatal("expected error for non-replayable body, got nil")
	}
}
