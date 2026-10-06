// Command 25_production_service_capstone_solution is the operational shell
// every production HTTP service needs: liveness/readiness health checks, a
// hand-rolled stdlib-only Prometheus text-exposition /metrics endpoint,
// log/slog JSON structured logging, and graceful shutdown. See the
// Dockerfile and ci.yml alongside this file, and the PROJECT LAYOUT NOTE in
// the explanation package for how this would be split across cmd/+internal/
// in a standalone repository.
package main

import (
	"context"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"sort"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"syscall"
	"time"
)

// ---------------------------------------------------------------------
// Health: readiness state, updated by a background poller, read fast and
// non-blocking by the /readyz handler.
// ---------------------------------------------------------------------

// Health holds the current cached readiness state. Reads (from HTTP
// handlers, potentially concurrent and frequent — a readiness probe can
// fire every second or two per instance) must never block on a dependency
// check; only the background poller in runReadinessLoop performs the
// actual check, on its own schedule.
type Health struct {
	mu    sync.RWMutex
	ready bool
	err   error
}

// Ready returns the last-known readiness state and, if not ready, the
// error from the most recent failed check.
func (h *Health) Ready() (ready bool, err error) {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return h.ready, h.err
}

func (h *Health) setReady(ready bool, err error) {
	h.mu.Lock()
	defer h.mu.Unlock()
	h.ready = ready
	h.err = err
}

// Pinger abstracts whatever dependency readiness actually depends on. A
// real service would implement this against *sql.DB.PingContext (problem
// 09's repository layer) or a downstream health-check RPC; here it's
// deliberately just an interface so the polling logic can be tested
// without a real dependency.
type Pinger interface {
	Ping(ctx context.Context) error
}

// alwaysHealthyPinger is the demo Pinger main() wires up by default: no
// real dependency, always succeeds. Stands in for "the database is up."
type alwaysHealthyPinger struct{}

func (alwaysHealthyPinger) Ping(context.Context) error { return nil }

// runReadinessLoop polls p on a fixed interval and updates h accordingly,
// until ctx is done. It runs one check IMMEDIATELY before entering the
// ticker loop — without this, a freshly started process would report "not
// ready" for up to a full `interval` after startup even if the dependency
// was reachable the entire time, which is exactly backwards for a
// readiness probe deciding whether to route traffic to a newly started pod.
//
// Each check gets its own bounded sub-context (checkTimeout), independent
// of `interval` and independent of ctx's own deadline (if any) beyond
// ctx's cancellation — so a hung dependency can't block the readiness loop
// from ever running its next check.
func runReadinessLoop(ctx context.Context, p Pinger, h *Health, interval time.Duration, logger *slog.Logger) {
	const checkTimeout = 2 * time.Second

	check := func() {
		checkCtx, cancel := context.WithTimeout(ctx, checkTimeout)
		defer cancel()
		err := p.Ping(checkCtx)
		wasReady, _ := h.Ready()
		h.setReady(err == nil, err)
		if err != nil {
			logger.Warn("readiness check failed", "error", err)
		} else if !wasReady {
			logger.Info("readiness check recovered")
		}
	}

	check()

	ticker := time.NewTicker(interval)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			check()
		}
	}
}

// ---------------------------------------------------------------------
// Metrics: hand-rolled, stdlib-only Prometheus text exposition format.
// No third-party client library — go.mod deliberately has none, and this
// file doesn't add one.
// ---------------------------------------------------------------------

// metricKeySep separates the (method, route pattern, status code) label
// tuple inside a single map key. 0x1F (ASCII Unit Separator) is used
// specifically because it cannot appear in an HTTP method, a route
// pattern, or a decimal status code, so splitting is unambiguous without
// needing to escape the parts going in.
const metricKeySep = "\x1f"

// Metrics tracks everything this endpoint exposes: a request counter
// labeled by method/route/status, an in-flight gauge, and process start
// time (uptime is derived from it, not stored separately).
type Metrics struct {
	mu           sync.Mutex
	requestCount map[string]uint64 // key: method+sep+pattern+sep+code -> count

	inFlight  atomic.Int64
	startedAt time.Time
}

func newMetrics() *Metrics {
	return &Metrics{
		requestCount: make(map[string]uint64),
		startedAt:    time.Now(),
	}
}

func metricKey(method, pattern string, code int) string {
	return method + metricKeySep + pattern + metricKeySep + strconv.Itoa(code)
}

func splitMetricKey(key string) (method, pattern, code string) {
	parts := strings.Split(key, metricKeySep)
	if len(parts) != 3 {
		return "", "", "" // defensive: should be unreachable given metricKey's construction
	}
	return parts[0], parts[1], parts[2]
}

// statusRecorder wraps an http.ResponseWriter to capture the status code
// it was given — net/http provides no other way to observe it after the
// fact. Defaults to 200 if Write happens without an explicit WriteHeader
// call first, matching net/http's own implicit behavior.
type statusRecorder struct {
	http.ResponseWriter
	status      int
	wroteHeader bool
}

func (r *statusRecorder) WriteHeader(code int) {
	if r.wroteHeader {
		return // net/http itself only honors the first WriteHeader call
	}
	r.status = code
	r.wroteHeader = true
	r.ResponseWriter.WriteHeader(code)
}

func (r *statusRecorder) Write(b []byte) (int, error) {
	if !r.wroteHeader {
		r.WriteHeader(http.StatusOK)
	}
	return r.ResponseWriter.Write(b)
}

// middleware wraps next to record it in this Metrics instance: increments
// the in-flight gauge for the request's duration, and on completion
// records one request-count observation labeled by method, the REGISTERED
// ROUTE PATTERN (not the raw request path), and the resulting status code.
//
// Using the route pattern rather than r.URL.Path matters: a raw path label
// on a route like "/items/{id}" would create one distinct metric series
// PER ITEM ID ever requested — unbounded label cardinality is one of the
// most common ways to make a metrics backend fall over in production. The
// pattern is passed in at registration time specifically to avoid this.
func (m *Metrics) middleware(pattern string, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		m.inFlight.Add(1)
		defer m.inFlight.Add(-1)

		rec := &statusRecorder{ResponseWriter: w, status: http.StatusOK}
		next.ServeHTTP(rec, r)

		key := metricKey(r.Method, pattern, rec.status)
		m.mu.Lock()
		m.requestCount[key]++
		m.mu.Unlock()
	})
}

// snapshot returns a point-in-time copy of the request counters, safe to
// iterate without holding m.mu (and without racing further increments).
func (m *Metrics) snapshot() map[string]uint64 {
	m.mu.Lock()
	defer m.mu.Unlock()
	out := make(map[string]uint64, len(m.requestCount))
	for k, v := range m.requestCount {
		out[k] = v
	}
	return out
}

// escapeLabelValue escapes a Prometheus label value per the text exposition
// format's grammar: backslash and double-quote must be escaped, and a
// literal newline must become the two-character sequence \n. Every label
// value this service actually emits (HTTP method, a registered route
// pattern, a decimal status code) is already safe by construction — this
// exists so the output is correct BY CONTRACT, not just correct for the
// specific inputs this program happens to produce today.
func escapeLabelValue(v string) string {
	v = strings.ReplaceAll(v, `\`, `\\`)
	v = strings.ReplaceAll(v, `"`, `\"`)
	v = strings.ReplaceAll(v, "\n", `\n`)
	return v
}

// render produces the full /metrics response body in Prometheus text
// exposition format (version 0.0.4): a "# HELP" line and a "# TYPE" line
// per metric family, then one sample line per label combination. Label-set
// keys are sorted before being written so the output is deterministic —
// Prometheus itself doesn't require ordering, but deterministic output is
// what makes this endpoint testable with an exact string comparison
// instead of an order-independent parser.
func (m *Metrics) render() string {
	var b strings.Builder

	b.WriteString("# HELP http_requests_total Total number of HTTP requests processed, labeled by method, route pattern, and status code.\n")
	b.WriteString("# TYPE http_requests_total counter\n")
	snap := m.snapshot()
	keys := make([]string, 0, len(snap))
	for k := range snap {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		method, pattern, code := splitMetricKey(k)
		fmt.Fprintf(&b, "http_requests_total{method=%q,path=%q,code=%q} %d\n",
			escapeLabelValue(method), escapeLabelValue(pattern), escapeLabelValue(code), snap[k])
	}

	b.WriteString("# HELP http_requests_in_flight Number of HTTP requests currently being served.\n")
	b.WriteString("# TYPE http_requests_in_flight gauge\n")
	fmt.Fprintf(&b, "http_requests_in_flight %d\n", m.inFlight.Load())

	b.WriteString("# HELP process_uptime_seconds Time in seconds since the process started.\n")
	b.WriteString("# TYPE process_uptime_seconds gauge\n")
	fmt.Fprintf(&b, "process_uptime_seconds %.2f\n", time.Since(m.startedAt).Seconds())

	return b.String()
}

// handler serves the rendered metrics with the exposition format's
// standard content type.
func (m *Metrics) handler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
		w.WriteHeader(http.StatusOK)
		io.WriteString(w, m.render())
	}
}

// ---------------------------------------------------------------------
// Health check handlers.
// ---------------------------------------------------------------------

// healthzHandler is LIVENESS ONLY: it must succeed as long as this process
// can execute a handler at all. It deliberately does not consult Health —
// a downstream dependency being down is a readiness concern, not a
// liveness one. Conflating them means an orchestrator restarts every pod
// in the deployment in response to a problem restarting them cannot fix.
func healthzHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	io.WriteString(w, "ok\n")
}

// readyzHandler reports the cached readiness state from Health, doing NO
// dependency check of its own — that's runReadinessLoop's job, on its own
// schedule, so a hung dependency can't make the probe endpoint itself slow.
func readyzHandler(h *Health) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ready, err := h.Ready()
		if !ready {
			w.WriteHeader(http.StatusServiceUnavailable)
			fmt.Fprintf(w, "not ready: %v\n", err)
			return
		}
		w.WriteHeader(http.StatusOK)
		io.WriteString(w, "ready\n")
	}
}

// ---------------------------------------------------------------------
// Logging middleware + server wiring.
// ---------------------------------------------------------------------

// loggingMiddleware emits one structured slog record per request: method,
// registered route pattern (same cardinality reasoning as Metrics.middleware),
// resulting status code, duration, and remote address.
func loggingMiddleware(logger *slog.Logger, pattern string, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		rec := &statusRecorder{ResponseWriter: w, status: http.StatusOK}
		next.ServeHTTP(rec, r)
		logger.Info("http request",
			"method", r.Method,
			"path", pattern,
			"code", rec.status,
			"duration_ms", time.Since(start).Milliseconds(),
			"remote_addr", r.RemoteAddr,
		)
	})
}

// instrument composes logging + metrics around a handler for one route,
// registered under its route pattern for consistent, bounded-cardinality
// labeling in both.
func instrument(logger *slog.Logger, metrics *Metrics, pattern string, h http.HandlerFunc) http.Handler {
	return loggingMiddleware(logger, pattern, metrics.middleware(pattern, h))
}

func newMux(logger *slog.Logger, metrics *Metrics, health *Health) *http.ServeMux {
	mux := http.NewServeMux()
	mux.Handle("GET /healthz", instrument(logger, metrics, "/healthz", healthzHandler))
	mux.Handle("GET /readyz", instrument(logger, metrics, "/readyz", readyzHandler(health)))
	mux.Handle("GET /metrics", instrument(logger, metrics, "/metrics", metrics.handler()))
	return mux
}

// newServer builds an *http.Server with production-sane, EXPLICIT timeouts.
// An http.Server with only Addr/Handler set has no ReadHeaderTimeout,
// leaving it open to a slow-client resource-exhaustion attack (a client
// that opens a connection and trickles header bytes in one at a time,
// tying up a goroutine and file descriptor indefinitely — the "Slowloris"
// class of vulnerability).
func newServer(addr string, handler http.Handler) *http.Server {
	return &http.Server{
		Addr:              addr,
		Handler:           handler,
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       10 * time.Second,
		WriteTimeout:      30 * time.Second,
		IdleTimeout:       120 * time.Second,
	}
}

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))

	metrics := newMetrics()
	health := &Health{}
	var pinger Pinger = alwaysHealthyPinger{} // real service: wrap *sql.DB.PingContext (problem 09)

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	go runReadinessLoop(ctx, pinger, health, 5*time.Second, logger)

	srv := newServer(":8080", newMux(logger, metrics, health))

	serveErr := make(chan error, 1)
	go func() {
		logger.Info("http server listening", "addr", srv.Addr)
		serveErr <- srv.ListenAndServe()
	}()

	select {
	case err := <-serveErr:
		if err != nil && !errors.Is(err, http.ErrServerClosed) {
			logger.Error("server failed", "error", err)
			os.Exit(1)
		}
		return
	case <-ctx.Done():
		logger.Info("shutdown signal received, draining in-flight requests")
	}

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := srv.Shutdown(shutdownCtx); err != nil {
		// Shutdown returns the shutdownCtx's error if the deadline fires
		// before every connection drains — a real failure to act on
		// (page, alert, or at minimum log loudly), not something to
		// silently ignore.
		logger.Error("graceful shutdown did not complete cleanly", "error", err)
		os.Exit(1)
	}
	logger.Info("server stopped cleanly")
}

/*
BEST PRACTICES

  - Keep liveness dependency-free. It answers "can this process run code,"
    nothing more. Readiness is the only place a downstream dependency
    check belongs.
  - Poll readiness in the background on a fixed interval; never perform the
    dependency check synchronously inside the /readyz handler itself — a
    probe endpoint that can hang is worse than useless, it actively
    destabilizes the orchestrator's view of the fleet.
  - Label metrics by the REGISTERED ROUTE PATTERN, never the raw request
    path, whenever the path can contain a variable segment (an ID, a slug)
    — unbounded label cardinality is a leading cause of metrics-backend
    outages in real deployments.
  - Set every http.Server timeout field explicitly. The zero value (no
    timeout) is never the right production default for any of them.
  - Always give srv.Shutdown a bounded context, and treat its returned
    error (deadline exceeded before drain completed) as an operational
    signal, not noise to swallow.

ALTERNATIVE APPROACHES / TRADE-OFFS

  - A histogram for request latency (with proper bucket boundaries and the
    _bucket/_sum/_count lines the exposition format requires for
    histograms) would be far more useful in practice than exposing only
    counts — omitted here to keep the hand-rolled exposition format
    approachable; the counter+gauge shown is exactly the part that's
    tractable to hand-roll correctly, and the stretch goals call out the
    histogram explicitly as the natural next step.
  - Using a third-party client library (prometheus/client_golang) would
    eliminate essentially all of the Metrics type's code and handle label
    escaping, histogram bucketing, and concurrent-safe collection for
    free — not used here specifically because go.mod deliberately has no
    metrics dependency and the point of this exercise is understanding the
    wire format well enough to have built it by hand at least once.
  - A single combined logging+metrics middleware (rather than composing two
    separate ones via `instrument`) would allocate one fewer
    statusRecorder per request — a real micro-optimization at very high
    request rates, traded here for keeping each middleware's single
    responsibility clearly separated and independently testable.

TESTING / FAILURE MODES

  - Handler-level tests (healthzHandler, readyzHandler) use
    httptest.NewRecorder directly — no real server needed to verify status
    codes and body content.
  - Metrics.render is tested for exact substrings (HELP/TYPE lines, a
    specific label-set line) after driving the middleware through a real
    http.Handler chain — proving the whole path (middleware -> counter ->
    render) produces the documented format, not just that render's string
    formatting is correct in isolation.
  - runReadinessLoop is tested against a fake Pinger whose Ping toggles
    between success and failure, asserting Health.Ready() reflects both
    the initial state (available immediately, not after a full interval)
    and the transition on failure/recovery.
  - Graceful shutdown is tested end-to-end against a REAL *http.Server on a
    real (ephemeral, localhost) listener: a handler blocks on a channel to
    simulate in-flight work, Shutdown is triggered concurrently, and the
    test asserts Shutdown does not return — and the in-flight client
    request does not fail — until the handler is unblocked and completes,
    proving Shutdown drains rather than aborts.
*/
