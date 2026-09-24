package main

import (
	"context"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

func discardLogger() *slog.Logger {
	return slog.New(slog.NewTextHandler(io.Discard, nil))
}

// ---------------------------------------------------------------------
// Health check handlers.
// ---------------------------------------------------------------------

func TestHealthzHandler_AlwaysOK(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/healthz", nil)
	rec := httptest.NewRecorder()

	healthzHandler(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want %d", rec.Code, http.StatusOK)
	}
}

func TestReadyzHandler_NotReadyReturns503(t *testing.T) {
	h := &Health{}
	h.setReady(false, errors.New("db unreachable"))

	req := httptest.NewRequest(http.MethodGet, "/readyz", nil)
	rec := httptest.NewRecorder()
	readyzHandler(h)(rec, req)

	if rec.Code != http.StatusServiceUnavailable {
		t.Fatalf("status = %d, want %d", rec.Code, http.StatusServiceUnavailable)
	}
	if !strings.Contains(rec.Body.String(), "db unreachable") {
		t.Fatalf("body = %q, want it to mention the underlying error", rec.Body.String())
	}
}

func TestReadyzHandler_ReadyReturns200(t *testing.T) {
	h := &Health{}
	h.setReady(true, nil)

	req := httptest.NewRequest(http.MethodGet, "/readyz", nil)
	rec := httptest.NewRecorder()
	readyzHandler(h)(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want %d", rec.Code, http.StatusOK)
	}
}

func TestReadyzHandler_ZeroValueHealthIsNotReady(t *testing.T) {
	// A freshly constructed Health (before any check has run) must report
	// not-ready, not silently succeed as the Go zero value for bool would
	// suggest if callers weren't careful.
	h := &Health{}
	req := httptest.NewRequest(http.MethodGet, "/readyz", nil)
	rec := httptest.NewRecorder()
	readyzHandler(h)(rec, req)

	if rec.Code != http.StatusServiceUnavailable {
		t.Fatalf("status = %d, want %d for a never-checked Health", rec.Code, http.StatusServiceUnavailable)
	}
}

// ---------------------------------------------------------------------
// Metrics.
// ---------------------------------------------------------------------

func TestMetricsRender_ContainsHelpTypeAndExpectedSample(t *testing.T) {
	m := newMetrics()

	handler := m.middleware("/healthz", http.HandlerFunc(healthzHandler))
	req := httptest.NewRequest(http.MethodGet, "/healthz", nil)
	for i := 0; i < 3; i++ {
		handler.ServeHTTP(httptest.NewRecorder(), req)
	}

	out := m.render()

	wantLines := []string{
		"# HELP http_requests_total",
		"# TYPE http_requests_total counter",
		`http_requests_total{method="GET",path="/healthz",code="200"} 3`,
		"# HELP http_requests_in_flight",
		"# TYPE http_requests_in_flight gauge",
		"http_requests_in_flight 0",
		"# HELP process_uptime_seconds",
		"# TYPE process_uptime_seconds gauge",
	}
	for _, want := range wantLines {
		if !strings.Contains(out, want) {
			t.Errorf("render() missing %q\nfull output:\n%s", want, out)
		}
	}
}

func TestMetricsMiddleware_TracksInFlightDuringRequest(t *testing.T) {
	m := newMetrics()

	started := make(chan struct{})
	release := make(chan struct{})
	slowHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		close(started)
		<-release
		w.WriteHeader(http.StatusOK)
	})
	handler := m.middleware("/slow", slowHandler)

	done := make(chan struct{})
	go func() {
		handler.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest(http.MethodGet, "/slow", nil))
		close(done)
	}()

	<-started
	if got := m.inFlight.Load(); got != 1 {
		t.Fatalf("in-flight during request = %d, want 1", got)
	}

	close(release)
	<-done

	if got := m.inFlight.Load(); got != 0 {
		t.Fatalf("in-flight after request = %d, want 0", got)
	}
}

func TestMetricsMiddleware_LabelsByRoutePatternNotRawPath(t *testing.T) {
	// Simulates a route like "/items/{id}": the pattern passed to
	// middleware stays fixed regardless of which concrete path the request
	// carried, which is exactly what keeps label cardinality bounded.
	m := newMetrics()
	handler := m.middleware("/items/{id}", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))

	for _, path := range []string{"/items/1", "/items/2", "/items/3"} {
		handler.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest(http.MethodGet, path, nil))
	}

	snap := m.snapshot()
	if len(snap) != 1 {
		t.Fatalf("distinct metric series = %d, want 1 (one per route pattern, not per concrete path)", len(snap))
	}
	if got := snap[metricKey(http.MethodGet, "/items/{id}", http.StatusOK)]; got != 3 {
		t.Fatalf("count for /items/{id} = %d, want 3", got)
	}
}

func TestMetricsMiddleware_ConcurrentRequestsCountCorrectly(t *testing.T) {
	m := newMetrics()
	handler := m.middleware("/ping", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))

	const n = 200
	var wg sync.WaitGroup
	wg.Add(n)
	for i := 0; i < n; i++ {
		go func() {
			defer wg.Done()
			handler.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest(http.MethodGet, "/ping", nil))
		}()
	}
	wg.Wait()

	snap := m.snapshot()
	if got := snap[metricKey(http.MethodGet, "/ping", http.StatusOK)]; got != n {
		t.Fatalf("count = %d, want %d (race in the counter under concurrent load)", got, n)
	}
}

// ---------------------------------------------------------------------
// Readiness polling.
// ---------------------------------------------------------------------

type fakePinger struct {
	fail atomic.Bool
}

func (p *fakePinger) Ping(context.Context) error {
	if p.fail.Load() {
		return errors.New("simulated dependency failure")
	}
	return nil
}

func TestRunReadinessLoop_ReadyImmediatelyOnStartup(t *testing.T) {
	// Must not wait a full interval before the first check — use a long
	// interval so if the immediate check didn't happen, the test would
	// time out waiting, proving the "check() before the ticker loop"
	// behavior rather than just happening to be fast enough.
	p := &fakePinger{}
	h := &Health{}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go runReadinessLoop(ctx, p, h, time.Hour, discardLogger())

	deadline := time.After(2 * time.Second)
	for {
		if ready, _ := h.Ready(); ready {
			return
		}
		select {
		case <-deadline:
			t.Fatal("Health never became ready — initial check did not run immediately")
		case <-time.After(5 * time.Millisecond):
		}
	}
}

func TestRunReadinessLoop_ReflectsFailureAndRecovery(t *testing.T) {
	p := &fakePinger{}
	h := &Health{}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	const interval = 20 * time.Millisecond
	go runReadinessLoop(ctx, p, h, interval, discardLogger())

	waitFor := func(want bool) {
		t.Helper()
		deadline := time.After(2 * time.Second)
		for {
			if ready, _ := h.Ready(); ready == want {
				return
			}
			select {
			case <-deadline:
				t.Fatalf("Health.Ready() never became %v", want)
			case <-time.After(5 * time.Millisecond):
			}
		}
	}

	waitFor(true) // initial check succeeds

	p.fail.Store(true)
	waitFor(false) // next tick observes the failure

	p.fail.Store(false)
	waitFor(true) // recovers on a later tick
}

// ---------------------------------------------------------------------
// Graceful shutdown, end-to-end against a real server.
// ---------------------------------------------------------------------

func TestGracefulShutdown_WaitsForInFlightRequest(t *testing.T) {
	started := make(chan struct{})
	release := make(chan struct{})
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		close(started)
		<-release
		w.WriteHeader(http.StatusOK)
		io.WriteString(w, "done\n")
	})

	lis, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("net.Listen: %v", err)
	}
	srv := newServer(lis.Addr().String(), handler)
	go func() { _ = srv.Serve(lis) }()

	clientErr := make(chan error, 1)
	go func() {
		resp, err := http.Get("http://" + lis.Addr().String() + "/")
		if err != nil {
			clientErr <- err
			return
		}
		defer resp.Body.Close()
		if resp.StatusCode != http.StatusOK {
			clientErr <- fmt.Errorf("unexpected status code: %s", http.StatusText(resp.StatusCode))
			return
		}
		clientErr <- nil
	}()

	<-started // the request is now in flight, blocked on `release`

	shutdownDone := make(chan error, 1)
	go func() {
		shutdownDone <- srv.Shutdown(context.Background())
	}()

	// Shutdown must NOT complete while the handler is still blocked —
	// give it a brief window during which it would be a bug for either
	// signal to have fired.
	select {
	case <-shutdownDone:
		t.Fatal("Shutdown returned before the in-flight request completed")
	case <-clientErr:
		t.Fatal("client request completed before it was unblocked")
	case <-time.After(100 * time.Millisecond):
		// expected: neither has fired yet.
	}

	close(release) // let the handler finish

	select {
	case err := <-shutdownDone:
		if err != nil {
			t.Fatalf("Shutdown returned an error: %v", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("Shutdown did not return after the in-flight request completed")
	}

	select {
	case err := <-clientErr:
		if err != nil {
			t.Fatalf("in-flight client request failed: %v", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("client never received a response")
	}

	// After Shutdown has completed, the listener is closed: a new
	// connection attempt must fail rather than succeed.
	if _, err := http.Get("http://" + lis.Addr().String() + "/"); err == nil {
		t.Fatal("request after Shutdown succeeded, want connection failure")
	}
}
