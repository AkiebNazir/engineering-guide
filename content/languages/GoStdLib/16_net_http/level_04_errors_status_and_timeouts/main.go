/*
LEVEL 04 (errors) - what counts as an error, and which one you got

You will learn
  - a 404 or 500 is NOT an error from client.Do: err is nil and you get a
    response. Checking err alone and forgetting resp.StatusCode is the most
    common client bug
  - transport failures come back as *url.Error (Op, URL, and the wrapped
    cause), so errors.As / errors.Is see through them:
      connection refused  -> errors.Is(err, syscall.ECONNREFUSED)
      Client.Timeout hit  -> urlErr.Timeout() == true
      context deadline    -> errors.Is(err, context.DeadlineExceeded)
      context cancelled   -> errors.Is(err, context.Canceled)
  - these distinctions decide retry policy: refused and timeouts may be
    retried (idempotent requests only), a 4xx never should be

Run: cd content/languages/GoStdLib && go run ./16_net_http/level_04_errors_status_and_timeouts
*/

package main

import (
	"context"
	"errors"
	"fmt"
	"net"
	"net/http"
	"net/http/httptest"
	"net/url"
	"syscall"
	"time"
)

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /missing", func(w http.ResponseWriter, r *http.Request) {
		http.Error(w, "no such thing", http.StatusNotFound)
	})
	mux.HandleFunc("GET /slow", func(w http.ResponseWriter, r *http.Request) {
		select { // a slow handler that still notices the client going away
		case <-time.After(2 * time.Second):
		case <-r.Context().Done():
		}
	})
	srv := httptest.NewServer(mux)
	defer srv.Close()

	// 1. A 404 is a successful HTTP exchange.
	resp, err := http.Get(srv.URL + "/missing")
	if err != nil {
		panic("a 404 must not be a transport error")
	}
	resp.Body.Close()
	fmt.Printf("1. GET /missing          err=%v status=%d\n", err, resp.StatusCode)
	if resp.StatusCode != http.StatusNotFound {
		panic("expected 404")
	}

	// 2. Connection refused: grab a free port, close it, then dial it.
	ln, _ := net.Listen("tcp", "127.0.0.1:0")
	deadAddr := ln.Addr().String()
	ln.Close()
	_, err = http.Get("http://" + deadAddr + "/")
	var urlErr *url.Error
	if !errors.As(err, &urlErr) || !errors.Is(err, syscall.ECONNREFUSED) {
		panic(fmt.Sprintf("expected *url.Error wrapping ECONNREFUSED, got %T %v", err, err))
	}
	fmt.Printf("2. dial a closed port    op=%s refused=%v\n", urlErr.Op, errors.Is(err, syscall.ECONNREFUSED))

	// 3. http.Client.Timeout covers the whole exchange, body included.
	short := &http.Client{Timeout: 100 * time.Millisecond}
	start := time.Now()
	_, err = short.Get(srv.URL + "/slow")
	if !errors.As(err, &urlErr) || !urlErr.Timeout() {
		panic(fmt.Sprintf("expected a timeout *url.Error, got %v", err))
	}
	fmt.Printf("3. Client.Timeout 100ms  timeout=%v after %v\n", urlErr.Timeout(), time.Since(start).Round(10*time.Millisecond))

	// 4. A context deadline: same effect, but set per request by the caller.
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()
	req, _ := http.NewRequestWithContext(ctx, http.MethodGet, srv.URL+"/slow", nil)
	_, err = http.DefaultClient.Do(req)
	if !errors.Is(err, context.DeadlineExceeded) {
		panic(fmt.Sprintf("expected context.DeadlineExceeded, got %v", err))
	}
	fmt.Printf("4. ctx deadline 100ms    DeadlineExceeded=%v\n", errors.Is(err, context.DeadlineExceeded))

	// 5. Cancelling the context (user hit "stop", parent request ended).
	ctx2, cancel2 := context.WithCancel(context.Background())
	time.AfterFunc(50*time.Millisecond, cancel2)
	req2, _ := http.NewRequestWithContext(ctx2, http.MethodGet, srv.URL+"/slow", nil)
	_, err = http.DefaultClient.Do(req2)
	if !errors.Is(err, context.Canceled) {
		panic(fmt.Sprintf("expected context.Canceled, got %v", err))
	}
	fmt.Printf("5. ctx cancelled         Canceled=%v\n", errors.Is(err, context.Canceled))
	fmt.Println("OK")
}
