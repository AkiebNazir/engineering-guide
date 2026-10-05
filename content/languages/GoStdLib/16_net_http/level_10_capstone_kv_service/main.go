/*
LEVEL 10 (capstone) - a small key/value HTTP service and a well-behaved client

You will learn
  - how the pieces from levels 1-9 fit into one program:
      server: ServeMux method+wildcard routes, JSON bodies with size limits,
              recover + request-counting middleware, all four timeouts,
              graceful Shutdown
      client: one shared *http.Client with a tuned Transport and a Timeout,
              per-call context deadlines, body always drained and closed,
              retries with exponential backoff for 503/connection errors on
              idempotent methods only
  - the server is started on a free loopback port and shut down cleanly at
    the end; everything is checked, then it prints OK

Run: cd content/languages/GoStdLib && go run ./16_net_http/level_10_capstone_kv_service
*/

package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"sync"
	"sync/atomic"
	"time"
)

// ---------------------------------------------------------------- server

type store struct {
	mu   sync.RWMutex
	data map[string]string
}

type valueBody struct {
	Value string `json:"value"`
}

func (s *store) routes() *http.ServeMux {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /kv/{key}", func(w http.ResponseWriter, r *http.Request) {
		s.mu.RLock()
		v, ok := s.data[r.PathValue("key")]
		s.mu.RUnlock()
		if !ok {
			writeJSON(w, http.StatusNotFound, map[string]string{"error": "not found"})
			return
		}
		writeJSON(w, http.StatusOK, valueBody{v})
	})
	mux.HandleFunc("PUT /kv/{key}", func(w http.ResponseWriter, r *http.Request) {
		var in valueBody
		dec := json.NewDecoder(http.MaxBytesReader(w, r.Body, 4<<10))
		dec.DisallowUnknownFields()
		if err := dec.Decode(&in); err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": err.Error()})
			return
		}
		s.mu.Lock()
		s.data[r.PathValue("key")] = in.Value
		s.mu.Unlock()
		w.WriteHeader(http.StatusNoContent)
	})
	mux.HandleFunc("DELETE /kv/{key}", func(w http.ResponseWriter, r *http.Request) {
		s.mu.Lock()
		delete(s.data, r.PathValue("key"))
		s.mu.Unlock()
		w.WriteHeader(http.StatusNoContent)
	})
	// A dependency that is briefly unavailable: 503 twice, then fine.
	var flaky atomic.Int32
	mux.HandleFunc("GET /flaky", func(w http.ResponseWriter, r *http.Request) {
		if flaky.Add(1) <= 2 {
			w.Header().Set("Retry-After", "0")
			writeJSON(w, http.StatusServiceUnavailable, map[string]string{"error": "warming up"})
			return
		}
		writeJSON(w, http.StatusOK, valueBody{"ready"})
	})
	return mux
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}

var served atomic.Int64

func middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		served.Add(1)
		defer func() {
			if v := recover(); v != nil {
				writeJSON(w, http.StatusInternalServerError, map[string]string{"error": "internal"})
			}
		}()
		next.ServeHTTP(w, r)
	})
}

// ---------------------------------------------------------------- client

type kvClient struct {
	base string
	http *http.Client
}

func newKVClient(base string) *kvClient {
	tr := &http.Transport{
		DialContext:           (&net.Dialer{Timeout: 2 * time.Second, KeepAlive: 30 * time.Second}).DialContext,
		MaxIdleConns:          100,
		MaxIdleConnsPerHost:   32, // the default of 2 churns connections under concurrency (level 6)
		IdleConnTimeout:       90 * time.Second,
		ResponseHeaderTimeout: 2 * time.Second,
	}
	return &kvClient{base: base, http: &http.Client{Transport: tr, Timeout: 5 * time.Second}}
}

var errNotFound = errors.New("not found")

// do sends one request, retrying 503s and transport errors for idempotent
// methods with exponential backoff. It always drains and closes the body.
func (c *kvClient) do(ctx context.Context, method, path string, body any, out any) (attempts int, err error) {
	var payload []byte
	if body != nil {
		if payload, err = json.Marshal(body); err != nil {
			return 0, err
		}
	}
	idempotent := method == http.MethodGet || method == http.MethodPut || method == http.MethodDelete
	backoff := 20 * time.Millisecond
	for attempts = 1; ; attempts++ {
		req, err := http.NewRequestWithContext(ctx, method, c.base+path, bytes.NewReader(payload))
		if err != nil {
			return attempts, err
		}
		if body != nil {
			req.Header.Set("Content-Type", "application/json")
		}
		resp, err := c.http.Do(req)
		retry := false
		switch {
		case err != nil:
			retry = idempotent && ctx.Err() == nil
		case resp.StatusCode == http.StatusServiceUnavailable:
			retry = idempotent
			err = fmt.Errorf("%s %s: %s", method, path, resp.Status)
		case resp.StatusCode == http.StatusNotFound:
			err = errNotFound
		case resp.StatusCode >= 400:
			b, _ := io.ReadAll(io.LimitReader(resp.Body, 512))
			err = fmt.Errorf("%s %s: %s: %s", method, path, resp.Status, bytes.TrimSpace(b))
		case out != nil:
			err = json.NewDecoder(resp.Body).Decode(out)
		}
		if resp != nil {
			io.Copy(io.Discard, resp.Body) // drain so the connection is reused
			resp.Body.Close()
		}
		if !retry || attempts == 4 {
			return attempts, err
		}
		select {
		case <-time.After(backoff):
			backoff *= 2
		case <-ctx.Done():
			return attempts, ctx.Err()
		}
	}
}

// ---------------------------------------------------------------- main

func main() {
	st := &store{data: map[string]string{}}
	srv := &http.Server{
		Handler:           middleware(st.routes()),
		ReadHeaderTimeout: 2 * time.Second,
		ReadTimeout:       5 * time.Second,
		WriteTimeout:      5 * time.Second,
		IdleTimeout:       60 * time.Second,
	}
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		panic(err)
	}
	serveErr := make(chan error, 1)
	go func() { serveErr <- srv.Serve(ln) }()

	c := newKVClient("http://" + ln.Addr().String())
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	must := func(_ int, err error) {
		if err != nil {
			panic(err)
		}
	}
	must(c.do(ctx, http.MethodPut, "/kv/color", valueBody{"teal"}, nil))
	var got valueBody
	must(c.do(ctx, http.MethodGet, "/kv/color", nil, &got))
	fmt.Println("PUT then GET /kv/color ->", got.Value)
	if got.Value != "teal" {
		panic("round trip failed")
	}

	must(c.do(ctx, http.MethodDelete, "/kv/color", nil, nil))
	if _, err := c.do(ctx, http.MethodGet, "/kv/color", nil, &got); !errors.Is(err, errNotFound) {
		panic(fmt.Sprintf("want errNotFound after DELETE, got %v", err))
	}
	fmt.Println("after DELETE          -> errNotFound")

	_, err = c.do(ctx, http.MethodPut, "/kv/x", map[string]string{"valu": "typo"}, nil)
	fmt.Println("PUT with a typo'd field ->", err)
	if err == nil {
		panic("unknown field should be a 400")
	}

	var ready valueBody
	attempts, err := c.do(ctx, http.MethodGet, "/flaky", nil, &ready)
	fmt.Printf("GET /flaky            -> %q after %d attempts (two 503s retried with backoff)\n", ready.Value, attempts)
	if err != nil || attempts != 3 || ready.Value != "ready" {
		panic(fmt.Sprintf("retry logic: attempts=%d err=%v value=%q", attempts, err, ready.Value))
	}

	// 50 concurrent GETs share the pooled connections.
	must(c.do(ctx, http.MethodPut, "/kv/hot", valueBody{"v"}, nil))
	var wg sync.WaitGroup
	var failures atomic.Int32
	for i := 0; i < 50; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			var v valueBody
			if _, err := c.do(ctx, http.MethodGet, "/kv/hot", nil, &v); err != nil || v.Value != "v" {
				failures.Add(1)
			}
		}()
	}
	wg.Wait()
	if failures.Load() != 0 {
		panic(fmt.Sprintf("%d concurrent reads failed", failures.Load()))
	}
	fmt.Println("50 concurrent GETs     -> all succeeded")

	// Under concurrency the Transport may dial a spare connection it never
	// sends a request on. The server sees it as StateNew, and Shutdown treats
	// a new connection as active for up to 5 seconds. Closing the client's
	// idle connections first lets Shutdown finish immediately.
	c.http.CloseIdleConnections()
	shutdownCtx, cancelShutdown := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancelShutdown()
	if err := srv.Shutdown(shutdownCtx); err != nil {
		panic(err)
	}
	if err := <-serveErr; !errors.Is(err, http.ErrServerClosed) {
		panic(err)
	}
	fmt.Printf("graceful shutdown done; server handled %d requests\n", served.Load())
	fmt.Println("OK")
}
