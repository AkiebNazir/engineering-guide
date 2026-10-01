/*
LEVEL 05 (pattern) - middleware: func(http.Handler) http.Handler

You will learn
  - net/http has no middleware framework because it doesn't need one: a
    middleware is a function that takes a Handler and returns a Handler
    that does something before and/or after calling the next one
  - to log the status code you must wrap the ResponseWriter, because the
    handler writes the status and net/http never hands it back to you
  - a recover middleware turns a handler panic into a 500 for that one
    request (net/http would otherwise log it and abort the connection)
  - order matters: the outermost middleware runs first on the way in and
    last on the way out

Run: go run ./GoStdLib/16_net_http/level_05_middleware
*/

package main

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

type ctxKey string

const requestIDKey ctxKey = "request-id"

// statusRecorder remembers the status code the handler wrote.
type statusRecorder struct {
	http.ResponseWriter
	status int
}

func (s *statusRecorder) WriteHeader(code int) {
	s.status = code
	s.ResponseWriter.WriteHeader(code)
}

type logLine struct {
	id, method, path string
	status           int
}

var (
	mu   sync.Mutex
	logs []logLine
	seq  atomic.Int64
)

func requestID(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		id := r.Header.Get("X-Request-ID")
		if id == "" {
			id = "req-" + strconv.FormatInt(seq.Add(1), 10)
		}
		w.Header().Set("X-Request-ID", id)
		next.ServeHTTP(w, r.WithContext(context.WithValue(r.Context(), requestIDKey, id)))
	})
}

func logging(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		rec := &statusRecorder{ResponseWriter: w, status: http.StatusOK}
		next.ServeHTTP(rec, r)
		id, _ := r.Context().Value(requestIDKey).(string)
		mu.Lock()
		logs = append(logs, logLine{id, r.Method, r.URL.Path, rec.status})
		mu.Unlock()
		fmt.Printf("  log: %s %s %s -> %d in %v\n", id, r.Method, r.URL.Path, rec.status, time.Since(start).Round(time.Microsecond))
	})
}

func recoverer(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if v := recover(); v != nil {
				http.Error(w, "internal error", http.StatusInternalServerError)
			}
		}()
		next.ServeHTTP(w, r)
	})
}

// chain applies middlewares so that the first one listed is the outermost.
func chain(h http.Handler, mws ...func(http.Handler) http.Handler) http.Handler {
	for i := len(mws) - 1; i >= 0; i-- {
		h = mws[i](h)
	}
	return h
}

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /ok", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprint(w, "fine")
	})
	mux.HandleFunc("GET /teapot", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusTeapot)
	})
	mux.HandleFunc("GET /boom", func(w http.ResponseWriter, r *http.Request) {
		var m map[string]int
		m["x"] = 1 // nil map write: panics
	})
	srv := httptest.NewServer(chain(mux, requestID, logging, recoverer))
	defer srv.Close()

	get := func(path, id string) (int, string, string) {
		req, _ := http.NewRequest(http.MethodGet, srv.URL+path, nil)
		if id != "" {
			req.Header.Set("X-Request-ID", id)
		}
		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			panic(err)
		}
		defer resp.Body.Close()
		b, _ := io.ReadAll(resp.Body)
		return resp.StatusCode, strings.TrimSpace(string(b)), resp.Header.Get("X-Request-ID")
	}

	s1, b1, id1 := get("/ok", "")
	s2, _, _ := get("/teapot", "")
	s3, b3, id3 := get("/boom", "trace-abc")

	if s1 != 200 || b1 != "fine" || id1 != "req-1" {
		panic(fmt.Sprintf("/ok: %d %q %q", s1, b1, id1))
	}
	if s2 != http.StatusTeapot {
		panic("status recorder / handler mismatch")
	}
	if s3 != 500 || b3 != "internal error" || id3 != "trace-abc" {
		panic(fmt.Sprintf("/boom should be a clean 500 carrying the caller's id: %d %q %q", s3, b3, id3))
	}
	mu.Lock()
	defer mu.Unlock()
	if len(logs) != 3 || logs[1].status != 418 || logs[2].status != 500 || logs[2].id != "trace-abc" {
		panic(fmt.Sprintf("logging middleware saw %+v", logs))
	}
	fmt.Println("panic became a 500, the log line has the real status and the caller's request id")
	fmt.Println("OK")
}
