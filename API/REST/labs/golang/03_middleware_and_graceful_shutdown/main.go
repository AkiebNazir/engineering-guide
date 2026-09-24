/*
LAB 03 (advanced) - Middleware chain, request IDs, panic recovery, timeouts, graceful shutdown
================================================================================================
You will learn
  - middleware = a function  func(http.Handler) http.Handler  that wraps the next handler
  - composing a chain:  RequestID -> Logging -> Recover -> Timeout -> your handler
  - context.WithValue for request-scoped data (with an unexported key type, so nothing collides)
  - wrapping http.ResponseWriter to CAPTURE the status code for logs (and why it needs Unwrap
    so http.ResponseController / Flusher keep working)
  - turning a panic in one handler into a 500 instead of a dead connection
  - http.TimeoutHandler and the four server timeouts that stop slow-client attacks
  - graceful shutdown: stop accepting NEW requests but let in-flight ones finish

Request flow (outermost first):

	client -> [RequestID] -> [Logging] -> [Recover] -> [Timeout] -> handler
	          sets ctx ID    times it     panic->500    503 if slow

Run it   go run ./REST/labs/golang/03_middleware_and_graceful_shutdown
*/
package main

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"
)

// ------------------------------------------------------------- middleware ---
type Middleware func(http.Handler) http.Handler

// Chain(a, b, c)(h) == a(b(c(h))): the first middleware listed runs first.
func Chain(mws ...Middleware) Middleware {
	return func(h http.Handler) http.Handler {
		for i := len(mws) - 1; i >= 0; i-- {
			h = mws[i](h)
		}
		return h
	}
}

type ctxKey struct{} // unexported type => no other package can collide with our key

func RequestID(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		id := r.Header.Get("X-Request-Id") // honour an upstream id, else make one
		if id == "" {
			b := make([]byte, 8)
			rand.Read(b)
			id = hex.EncodeToString(b)
		}
		w.Header().Set("X-Request-Id", id)
		next.ServeHTTP(w, r.WithContext(context.WithValue(r.Context(), ctxKey{}, id)))
	})
}

func idFrom(ctx context.Context) string { s, _ := ctx.Value(ctxKey{}).(string); return s }

// statusWriter remembers the status code the handler wrote.
type statusWriter struct {
	http.ResponseWriter
	status int
}

func (s *statusWriter) WriteHeader(code int) { s.status = code; s.ResponseWriter.WriteHeader(code) }

// Unwrap lets http.ResponseController reach the real writer (Flush, SetWriteDeadline, ...).
func (s *statusWriter) Unwrap() http.ResponseWriter { return s.ResponseWriter }

func Logging(logf func(string, ...any)) Middleware {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()
			sw := &statusWriter{ResponseWriter: w, status: http.StatusOK}
			next.ServeHTTP(sw, r)
			// For METRICS label by route pattern ("GET /users/{id}"), not raw path (unbounded cardinality).
			logf("req=%s %s -> %d in %s", idFrom(r.Context()), r.Method+" "+r.URL.Path, sw.status, time.Since(start).Round(time.Millisecond))
		})
	}
}

func Recover(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if rec := recover(); rec != nil {
				log.Printf("PANIC req=%s: %v", idFrom(r.Context()), rec) // stack trace goes to logs, never to the client
				http.Error(w, "internal server error", http.StatusInternalServerError)
			}
		}()
		next.ServeHTTP(w, r)
	})
}

func Timeout(d time.Duration) Middleware {
	return func(next http.Handler) http.Handler {
		return http.TimeoutHandler(next, d, `{"error":"request timed out"}`) // 503 + cancels r.Context()
	}
}

// --------------------------------------------------------------- handlers ---
func routes() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /hello", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "hello from request %s\n", idFrom(r.Context()))
	})
	mux.HandleFunc("GET /boom", func(w http.ResponseWriter, r *http.Request) {
		var m map[string]int
		m["x"] = 1 // panic: assignment to entry in nil map
	})
	mux.HandleFunc("GET /slow", func(w http.ResponseWriter, r *http.Request) {
		select {
		case <-time.After(2 * time.Second): // pretend to do a slow query...
			fmt.Fprintln(w, "finally")
		case <-r.Context().Done(): // ...but STOP when the deadline passes or the client leaves
		}
	})
	return Chain(RequestID, Logging(log.Printf), Recover, Timeout(500*time.Millisecond))(mux)
}

func main() {
	log.SetFlags(0)
	log.SetOutput(os.Stdout)

	srv := &http.Server{
		Handler: routes(),
		// The four timeouts. Without them one slow client can hold a connection forever.
		ReadHeaderTimeout: 2 * time.Second,  // slowloris protection
		ReadTimeout:       5 * time.Second,  // whole request incl. body
		WriteTimeout:      10 * time.Second, // must exceed the handler timeout
		IdleTimeout:       60 * time.Second, // keep-alive connections
	}
	ln, _ := net.Listen("tcp", "127.0.0.1:0")
	done := make(chan error, 1)
	go func() { done <- srv.Serve(ln) }()
	base := "http://" + ln.Addr().String()

	get := func(path string) (int, string, http.Header) {
		res, err := http.Get(base + path)
		if err != nil {
			panic(err)
		}
		defer res.Body.Close()
		b, _ := io.ReadAll(res.Body)
		return res.StatusCode, strings.TrimSpace(string(b)), res.Header
	}

	st, body, h := get("/hello")
	fmt.Println("hello  ->", st, body, "| header X-Request-Id:", h.Get("X-Request-Id"))
	must(st == 200 && strings.Contains(body, h.Get("X-Request-Id")), "request id flows through context")

	st, body, _ = get("/boom")
	fmt.Println("boom   ->", st, body, "(server still alive)")
	must(st == 500, "panic recovered")
	st, _, _ = get("/hello")
	must(st == 200, "server survived the panic")

	st, body, _ = get("/slow")
	fmt.Println("slow   ->", st, body)
	must(st == 503, "timeout")

	// Graceful shutdown, on a second server without the timeout middleware: a request that is already
	// in flight (600ms of work) is allowed to finish; only NEW requests are refused.
	inflight := make(chan string, 1)
	var started sync.WaitGroup
	started.Add(1)
	mux2 := http.NewServeMux()
	mux2.HandleFunc("GET /work", func(w http.ResponseWriter, r *http.Request) {
		started.Done()
		time.Sleep(600 * time.Millisecond)
		fmt.Fprint(w, "work finished")
	})
	srv2 := &http.Server{Handler: mux2}
	ln2, _ := net.Listen("tcp", "127.0.0.1:0")
	go srv2.Serve(ln2)
	go func() {
		res, err := http.Get("http://" + ln2.Addr().String() + "/work")
		if err != nil {
			inflight <- "ERROR " + err.Error()
			return
		}
		b, _ := io.ReadAll(res.Body)
		inflight <- string(b)
	}()
	started.Wait() // the request is now in flight

	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	t0 := time.Now()
	err := srv2.Shutdown(ctx) // 1) closes listeners 2) waits for active requests 3) closes idle conns
	fmt.Printf("shutdown-> err=%v after %s; in-flight request said: %q\n", err, time.Since(t0).Round(100*time.Millisecond), <-inflight)

	_, err = http.Get("http://" + ln2.Addr().String() + "/work")
	fmt.Println("after shutdown, new request fails:", err != nil)
	must(err != nil, "no new requests after shutdown")

	srv.Shutdown(context.Background())
	<-done
	fmt.Println("OK")
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}
