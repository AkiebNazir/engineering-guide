/*
FOUNDATION LEVEL 08 - Middleware: code that wraps every request
===================================================================
Levels 00-07 put everything a request needed inside one handler function.
Middleware is a WRAPPER: a function that takes an http.Handler and returns a
new http.Handler that runs code before and/or after calling the original -
without touching the original's code at all. This is exactly how logging,
auth (levels 09-10), rate limiting (see ../../labs/golang/04_rate_limit_middleware),
and recovery get added to real servers without editing every single route.

You will learn
  - a Middleware is just "func(http.Handler) http.Handler" - it wraps a
    handler and returns something that is STILL a handler
  - chaining: wrapping a wrapper in a wrapper, in a chosen order
  - ORDER matters: logging placed OUTSIDE recovery sees the final status
    even for a request that panicked; placed INSIDE, it would never run for
    a panicking request at all
  - recover() inside a deferred function is Go's way to catch a panic in ONE
    request without taking down the whole process - other goroutines
    (other in-flight requests) are completely unaffected either way, but
    without this the CONNECTION for the panicking request would just die

Run it   go run ./REST/Foundation/golang/08_middleware_logging_and_recovery
*/
package main

import (
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"time"
)

type Middleware func(http.Handler) http.Handler

// statusRecorder lets middleware see the status code a handler decided on,
// by intercepting the one call that sets it.
type statusRecorder struct {
	http.ResponseWriter
	status int
}

func (r *statusRecorder) WriteHeader(code int) {
	r.status = code
	r.ResponseWriter.WriteHeader(code)
}

func withLogging(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		rec := &statusRecorder{ResponseWriter: w, status: 200} // 200 is net/http's implicit default
		start := time.Now()
		next.ServeHTTP(rec, r)
		fmt.Printf("  [log] %s %s -> %d (%v)\n", r.Method, r.URL.Path, rec.status, time.Since(start).Round(time.Microsecond))
	})
}

func withRecovery(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if err := recover(); err != nil {
				fmt.Printf("  [recovery] caught %v - server stays up, this ONE request becomes a 500\n", err)
				w.WriteHeader(http.StatusInternalServerError)
				w.Write([]byte("internal server error\n"))
			}
		}()
		next.ServeHTTP(w, r)
	})
}

func main() {
	// ---- the "real" application logic, with zero knowledge of logging/recovery ----
	mux := http.NewServeMux()
	mux.HandleFunc("GET /ping", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprint(w, "pong\n")
	})
	mux.HandleFunc("GET /boom", func(w http.ResponseWriter, r *http.Request) {
		panic("simulated bug in a handler") // on purpose, to prove recovery works
	})

	// Built once, outside in: logging sees everything, including failures
	// that recovery converts into a clean 500. Swap the order (recovery
	// outside logging) and a panic would skip the log line entirely - try
	// it, and watch withLogging's print disappear on /boom.
	var pipeline http.Handler = withLogging(withRecovery(mux))

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, pipeline)
	base := "http://" + ln.Addr().String()

	get := func(path string) (int, string) {
		res, err := http.Get(base + path)
		if err != nil {
			log.Fatal(err)
		}
		defer res.Body.Close()
		b, _ := io.ReadAll(res.Body)
		return res.StatusCode, string(b)
	}

	s, b := get("/ping")
	fmt.Printf("GET /ping -> %d %q\n", s, b)
	if s != 200 || b != "pong\n" {
		panic("FAILED")
	}

	s, b = get("/boom")
	fmt.Printf("GET /boom -> %d %q   (the handler panicked - recovery turned it into a clean 500)\n", s, b)
	if s != 500 {
		panic("FAILED")
	}

	// The panic above must NOT have taken the server down for anyone else.
	s, b = get("/ping")
	fmt.Printf("GET /ping -> %d %q   (server is still alive after the previous panic)\n", s, b)
	if s != 200 || b != "pong\n" {
		panic("FAILED")
	}
	fmt.Println("OK")
}
