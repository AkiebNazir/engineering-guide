// Package main — reference solution for Problem 02: middleware chain.
//
// See ../explanation/02_middleware_chain_explanation.go for the full spec,
// acceptance criteria, hints, and stretch goals.
package main

import (
	"context"
	"crypto/subtle"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"runtime/debug"
	"strconv"
	"sync/atomic"
	"syscall"
	"time"
)

// ---------------------------------------------------------------------------
// Middleware type and composition
//
// A Middleware is just a function from one http.Handler to another — the
// simplest possible "decorator" shape Go offers, requiring no interface,
// no struct, no framework. Chain lets us declare a readable pipeline
// (RequestID, Recoverer, Logger, Timeout) instead of manually nesting
// RequestID(Recoverer(Logger(Timeout(d)(handler))))), which becomes
// unreadable past 2-3 middlewares and error-prone to reorder.
// ---------------------------------------------------------------------------

// Middleware wraps an http.Handler with additional behavior.
type Middleware func(http.Handler) http.Handler

// Chain composes middlewares so mws[0] is outermost (runs first on the way
// in, last on the way out) and mws[len-1] is innermost.
//
// We build inside-out: start from the final handler and wrap with mws in
// REVERSE order, so the LAST middleware wrapped is mws[0] — making it the
// outermost layer a request hits first. Folding the other direction would
// silently invert the documented contract, which is the single easiest
// bug to introduce in a hand-rolled Chain.
func Chain(mws ...Middleware) Middleware {
	return func(final http.Handler) http.Handler {
		h := final
		for i := len(mws) - 1; i >= 0; i-- {
			h = mws[i](h)
		}
		return h
	}
}

// ---------------------------------------------------------------------------
// Request ID
//
// The context key is an unexported type (not a bare string) specifically
// so no other package can accidentally collide with it — two independent
// packages both choosing context.WithValue(ctx, "requestID", ...) would
// silently clobber each other with a string key; an unexported type
// defined here can only be produced by this package.
// ---------------------------------------------------------------------------

type ctxKey int

const requestIDKey ctxKey = iota

// RequestIDHeader is the header carrying the request ID, both incoming
// (if the client/a preceding proxy already set one — useful for tracing a
// request across service boundaries) and outgoing.
const RequestIDHeader = "X-Request-ID"

// requestIDCounter generates process-unique, monotonically increasing
// IDs. A real distributed system would prefer a UUID or a
// trace-ID-compatible format (e.g. W3C traceparent) so IDs stay unique
// across many processes; a counter is sufficient — and cheaper — for a
// single-process demo, and atomic.Uint64 needs no mutex at all.
var requestIDCounter atomic.Uint64

func newRequestID() string {
	return "req-" + strconv.FormatUint(requestIDCounter.Add(1), 10)
}

// RequestID ensures every request has an ID: it forwards an existing
// X-Request-ID header (so a request ID assigned by an upstream load
// balancer or gateway survives end-to-end) or mints a new one, stores it
// in the request context, and echoes it on the response so the caller can
// correlate their request with server-side logs.
func RequestID(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		id := r.Header.Get(RequestIDHeader)
		if id == "" {
			id = newRequestID()
		}
		w.Header().Set(RequestIDHeader, id)
		ctx := context.WithValue(r.Context(), requestIDKey, id)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// RequestIDFromContext extracts the request ID stored by RequestID, or ""
// if none is present.
func RequestIDFromContext(ctx context.Context) string {
	id, _ := ctx.Value(requestIDKey).(string)
	return id
}

// ---------------------------------------------------------------------------
// Response-status-capturing ResponseWriter
//
// The stdlib http.ResponseWriter interface is deliberately write-only: it
// has no GetStatus()/BytesWritten(). Any middleware that needs to know
// "what did the handler actually respond with" (Logger, but also metrics
// middleware in a real service) has to wrap it. Embedding
// http.ResponseWriter means statusRecorder satisfies the interface for
// free and we only need to override the two methods we care about.
// ---------------------------------------------------------------------------

type statusRecorder struct {
	http.ResponseWriter
	status      int
	bytes       int
	wroteHeader bool
}

func newStatusRecorder(w http.ResponseWriter) *statusRecorder {
	// Default to 200: if the handler never calls WriteHeader explicitly
	// and only calls Write, net/http itself defaults to 200 on the first
	// Write — we mirror that so an un-instrumented handler still reports
	// the status it actually sent.
	return &statusRecorder{ResponseWriter: w, status: http.StatusOK}
}

func (r *statusRecorder) WriteHeader(code int) {
	if r.wroteHeader {
		// A second WriteHeader call is a caller bug (net/http itself
		// logs "superfluous WriteHeader call" and ignores it) — we
		// match that behavior: record only the first status.
		return
	}
	r.wroteHeader = true
	r.status = code
	r.ResponseWriter.WriteHeader(code)
}

func (r *statusRecorder) Write(b []byte) (int, error) {
	if !r.wroteHeader {
		r.WriteHeader(http.StatusOK)
	}
	n, err := r.ResponseWriter.Write(b)
	r.bytes += n
	return n, err
}

// ---------------------------------------------------------------------------
// Logger
//
// Logging AFTER next.ServeHTTP returns (rather than before) is what lets
// us report the real status code and total duration — the two numbers
// that actually matter for debugging a slow or failing request. Using
// log/slog with structured key-value attributes (rather than
// fmt.Sprintf-ing a single string) means log lines are machine-parseable
// by whatever aggregator ingests them (Loki, CloudWatch Insights,
// Datadog) without a custom regex per format change.
// ---------------------------------------------------------------------------

// Logger logs one structured line per request via log/slog: method, path,
// status, duration, request ID, and remote address.
func Logger(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		rec := newStatusRecorder(w)

		next.ServeHTTP(rec, r)

		slog.Info("http request",
			"method", r.Method,
			"path", r.URL.Path,
			"status", rec.status,
			"bytes", rec.bytes,
			"duration_ms", time.Since(start).Milliseconds(),
			"request_id", RequestIDFromContext(r.Context()),
			"remote_addr", r.RemoteAddr,
		)
	})
}

// ---------------------------------------------------------------------------
// Recoverer
//
// net/http's Server already recovers panics per-connection so one bad
// handler can't take down the whole process — but its default recovery
// just logs to stderr and abruptly closes the connection with NO response
// body, which looks like a network failure to the client rather than a
// clean 500. Recoverer intercepts the panic ourselves, so we control the
// response shape and can log with the same structured logger and request
// ID as everything else.
//
// Recoverer is placed INSIDE Logger in the chain (Logger wraps Recoverer)
// so that: (a) Logger's deferred-via-return status read still executes
// for a panicked request, because Recoverer catches the panic and returns
// normally rather than letting it propagate past Logger, and (b)
// Recoverer's own 500 write goes through the same statusRecorder Logger
// is watching, so the log line correctly shows status=500 instead of the
// zero-value/never-set status a raw panic would otherwise leave behind.
// This resolves the "Recoverer vs Logger order" question the explanation
// file poses: nest Recoverer inside Logger, not outside it.
// ---------------------------------------------------------------------------

func Recoverer(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if rec := recover(); rec != nil {
				slog.Error("panic recovered",
					"error", fmt.Sprint(rec),
					"request_id", RequestIDFromContext(r.Context()),
					"stack", string(debug.Stack()),
				)
				writeError(w, http.StatusInternalServerError, "internal_error", "internal server error")
			}
		}()
		next.ServeHTTP(w, r)
	})
}

// ---------------------------------------------------------------------------
// Timeout
//
// We hand-roll this instead of using http.TimeoutHandler for two reasons
// documented as a trade-off at the bottom of this file: (1) we want our
// own error envelope, not TimeoutHandler's plain-text body, and (2) we
// want the SAME statusRecorder-observable status semantics as the rest of
// this chain. Either approach shares an unavoidable limitation: canceling
// the context tells a WELL-BEHAVED handler to stop, but cannot forcibly
// kill a handler goroutine that ignores ctx.Done() — Go has no safe way
// to preempt an arbitrary goroutine. We only get "stop waiting for it,"
// not "guarantee it stopped."
// ---------------------------------------------------------------------------

// Timeout returns middleware that bounds request handling to d. If the
// handler doesn't finish in time, the client receives a 503 with the
// standard error envelope and the handler's context is canceled so a
// well-behaved handler (one that selects on ctx.Done() during long work)
// can stop promptly.
//
// Because the handler runs in its own goroutine (so this middleware can
// race it against the deadline), a panic inside the handler does NOT
// unwind through this goroutine's stack — it unwinds the spawned
// goroutine's stack instead, which Recoverer (running in the ORIGINAL
// goroutine, outside/around Timeout in the chain) would never see, and an
// unrecovered panic in any goroutine crashes the whole process regardless
// of what recover() calls exist elsewhere. We recover it locally and
// re-panic on the calling goroutine once we know the handler finished
// (not timed out), so it re-enters the normal panic path where Recoverer
// (further out in the chain) can catch it exactly as if no goroutine hop
// had happened. This is the standard pattern for forwarding a panic
// across a goroutine boundary — Go never propagates panics between
// goroutines automatically.
func Timeout(d time.Duration) Middleware {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ctx, cancel := context.WithTimeout(r.Context(), d)
			defer cancel()

			done := make(chan struct{})
			panicked := make(chan any, 1)
			go func() {
				defer close(done)
				defer func() {
					if p := recover(); p != nil {
						panicked <- p
					}
				}()
				next.ServeHTTP(w, r.WithContext(ctx))
			}()

			select {
			case <-done:
				// Handler finished before the deadline, successfully or
				// not. If it panicked, re-panic here (the original,
				// Recoverer-wrapped goroutine) so recovery/logging work
				// exactly as if Timeout weren't in the chain at all.
				select {
				case p := <-panicked:
					panic(p)
				default:
				}
			case <-ctx.Done():
				// Deadline hit first. We respond now; the handler
				// goroutine keeps running in the background until it
				// notices ctx.Done() (if it ever checks) or finishes —
				// this goroutine is not forcibly terminated, matching
				// the fundamental limitation documented above. If the
				// handler later tries to write to w, that write is a
				// race with this one; a hardened version would swap in
				// a "write-once" ResponseWriter guard here (see
				// ALTERNATIVE APPROACHES below). If it panics after the
				// deadline, that panic is recovered by the deferred func
				// above (preventing a process crash) and then silently
				// dropped, since the client has already gotten its 503
				// and there is no one left listening on `panicked`.
				writeError(w, http.StatusServiceUnavailable, "timeout", "request timed out")
			}
		})
	}
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

// Auth returns middleware requiring an exact "Authorization: Bearer
// <token>" match. subtle.ConstantTimeCompare avoids leaking information
// about how many leading bytes of a guessed token were correct via
// response-timing differences — a real (if narrow) side channel for a
// naive == comparison on secret material.
func Auth(token string) Middleware {
	want := []byte(token)
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			const prefix = "Bearer "
			auth := r.Header.Get("Authorization")
			if len(auth) <= len(prefix) || auth[:len(prefix)] != prefix {
				writeError(w, http.StatusUnauthorized, "unauthorized", "missing or malformed Authorization header")
				return
			}
			got := []byte(auth[len(prefix):])
			if len(got) != len(want) || subtle.ConstantTimeCompare(got, want) != 1 {
				writeError(w, http.StatusUnauthorized, "unauthorized", "invalid token")
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}

// ---------------------------------------------------------------------------
// Shared error envelope (same shape as problem 01, deliberately — a
// consistent error contract is a cross-cutting API concern, and every
// middleware/handler in a real service should import one shared package
// for this rather than redefine it per problem; we redefine it locally
// here only because each problem directory in this curriculum is an
// independent, self-contained package).
// ---------------------------------------------------------------------------

type apiErrorBody struct {
	Code    string `json:"code"`
	Message string `json:"message"`
}

type apiError struct {
	Error apiErrorBody `json:"error"`
}

func writeError(w http.ResponseWriter, status int, code, message string) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(apiError{Error: apiErrorBody{Code: code, Message: message}})
}

// ---------------------------------------------------------------------------
// Demo server
// ---------------------------------------------------------------------------

func demoMux() http.Handler {
	mux := http.NewServeMux()

	mux.HandleFunc("GET /ping", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		_ = json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
	})

	// /slow demonstrates Timeout: it selects on ctx.Done() so it behaves
	// like a well-written handler that actually stops promptly rather
	// than continuing to burn resources after the client got a 503.
	mux.HandleFunc("GET /slow", func(w http.ResponseWriter, r *http.Request) {
		select {
		case <-time.After(5 * time.Second):
			w.Write([]byte("finished (should not happen under the 2s timeout)"))
		case <-r.Context().Done():
			// The Timeout middleware already wrote the 503; we just
			// stop working. Nothing left to write here.
			return
		}
	})

	// /boom demonstrates Recoverer.
	mux.HandleFunc("GET /boom", func(w http.ResponseWriter, r *http.Request) {
		panic("simulated handler panic")
	})

	// /secret demonstrates Auth, applied to this single route only —
	// most real services don't gate every route behind the same auth, so
	// per-route composition (rather than putting Auth in the global
	// Chain) mirrors how you'd actually wire a mixed public/private API.
	mux.Handle("GET /secret", Auth("supersecret")(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		_ = json.NewEncoder(w).Encode(map[string]string{"secret": "42"})
	})))

	return mux
}

// newServer wires the shared chain (RequestID -> Recoverer -> Logger ->
// Timeout) around the demo mux. RequestID is outermost so an ID exists
// before anything else runs (including Recoverer's and Logger's log
// lines, which both include it). Recoverer sits inside Logger so a panic
// still produces exactly one log line with status=500 (see the Recoverer
// doc comment above for the full reasoning). Timeout is innermost among
// the shared middlewares so it wraps only the actual handler dispatch,
// not the logging/recovery bookkeeping around it.
func newServer(addr string) *http.Server {
	chain := Chain(RequestID, Recoverer, Logger, Timeout(2*time.Second))
	return &http.Server{
		Addr:              addr,
		Handler:           chain(demoMux()),
		ReadHeaderTimeout: 5 * time.Second,
		WriteTimeout:      15 * time.Second, // > Timeout's 2s so it never fires first
		IdleTimeout:       60 * time.Second,
	}
}

func main() {
	srv := newServer(":8080")

	serveErr := make(chan error, 1)
	go func() {
		log.Printf("listening on %s", srv.Addr)
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			serveErr <- err
			return
		}
		serveErr <- nil
	}()

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	select {
	case err := <-serveErr:
		if err != nil {
			log.Fatalf("server failed to start: %v", err)
		}
	case <-ctx.Done():
		stop()
		log.Print("shutdown signal received, draining in-flight requests")
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		if err := srv.Shutdown(shutdownCtx); err != nil {
			log.Fatalf("graceful shutdown failed: %v", err)
		}
		<-serveErr
		log.Print("shutdown complete")
	}
}

/*
BEST PRACTICES

  - Middleware order is part of your API's contract, not an implementation
    detail — document it explicitly (as this file does) rather than
    leaving the next maintainer to reverse-engineer why Recoverer is
    nested where it is.
  - Use an unexported context-key type, never a bare string/int literal
    type, to avoid cross-package collisions on context.WithValue.
  - Wrap http.ResponseWriter rather than trying to introspect it — the
    interface is intentionally minimal; anything you need beyond
    Header/Write/WriteHeader has to be tracked yourself.
  - Prefer log/slog's structured attributes over fmt.Sprintf'd strings for
    anything that will be ingested by a log aggregator.
  - Apply narrow middlewares (like Auth) per-route, and only put genuinely
    universal concerns (request ID, recovery, logging) in the global
    chain.

ALTERNATIVE APPROACHES / TRADE-OFFS

  - http.TimeoutHandler vs hand-rolled Timeout: TimeoutHandler is
    battle-tested and handles the write-after-timeout race for you (it
    provides its own buffering ResponseWriter that discards writes after
    the timeout fires) at the cost of an internal buffer allocation per
    request and a fixed plain-text-ish response body shape unless you
    parse/replace it. Our hand-rolled version gives us the exact error
    envelope for free but has the write-race caveat noted inline above —
    a production-grade version should wrap w in a "first write wins, then
    silently discard" ResponseWriter (essentially reimplementing what
    TimeoutHandler already does internally) to fully close that gap.
  - A single "Observability" middleware doing both recovery and logging in
    one function vs two composable ones: fusing them avoids the ordering
    question entirely and shares the statusRecorder naturally, at the
    cost of a less composable, less independently testable unit. This
    solution keeps them separate because independent testability is worth
    more in a teaching context (and in most real codebases).
  - context.WithValue for request ID vs a dedicated struct-based "request
    scope" object: WithValue is idiomatic for exactly this narrow use
    (cross-cutting, read-only, request-scoped metadata) but doesn't scale
    to many fields without turning into stringly-typed soup — beyond 2-3
    values, prefer a single struct value under one context key.

TESTING NOTES

  - Test Chain's ordering with middlewares that append to a shared []string
    and assert the exact sequence — this catches an inside-out/outside-in
    fold bug immediately.
  - Test Recoverer by wrapping a handler that panics and asserting: no
    process crash, exact 500 JSON envelope, and (via httptest.ResponseRecorder)
    that no earlier partial body was written.
  - Test Timeout with a handler that blocks on a channel you control,
    asserting a 503 arrives at the configured deadline and that the
    handler's ctx.Done() actually fires (assert via a second channel the
    handler closes after observing cancellation) — this is the only way
    to prove no goroutine leak rather than assume it.
  - Test Auth with table cases: no header, wrong scheme, wrong token,
    correct token.

FAILURE MODES TO CONSIDER

  - A handler that ignores context cancellation entirely: Timeout still
    returns a 503 to the client, but the handler goroutine leaks until it
    eventually finishes on its own (or never does, e.g. blocked on an I/O
    call with no deadline itself) — the fix is always at the leaf
    (propagate ctx into every blocking call), never at the middleware.
  - A handler that panics AFTER writing a partial response and status
    code: Recoverer's attempt to WriteHeader(500) is a no-op superfluous
    call (see statusRecorder.WriteHeader) — the client receives a
    truncated/malformed body with no way to fix it after the fact. This is
    why handlers should fully build a response before writing any of it
    when possible.
  - Two middlewares both wrapping w in their own statusRecorder: only the
    outermost wrapper's recorded status reflects reality if an inner one
    is bypassed; keep exactly one recorder in the chain (Logger's) and
    have everything else that needs status (there is nothing else here)
    read through RequestIDFromContext-style accessors instead of
    re-wrapping.
*/
