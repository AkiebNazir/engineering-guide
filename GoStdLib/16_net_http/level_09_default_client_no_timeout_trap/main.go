/*
LEVEL 09 (trap) - http.DefaultClient has no timeout

You will learn
  - http.Get, http.Post and http.DefaultClient use a Client whose Timeout
    is 0, which means "wait forever". The default Transport does bound the
    TCP dial (30s) and the TLS handshake (10s), but once connected, a server
    that accepts the request and then never answers holds your goroutine
    (and whatever request of yours is waiting on it) indefinitely
  - in production this shows up as goroutine counts that only ever go up
    and requests that hang until the load balancer gives up
  - the fix is one line: your own *http.Client with a Timeout (a ceiling
    for the whole exchange), plus a per-request context deadline where the
    caller has a tighter budget

Run: go run ./GoStdLib/16_net_http/level_09_default_client_no_timeout_trap
*/

package main

import (
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"net/url"
	"runtime"
	"time"
)

func main() {
	release := make(chan struct{})
	// A dependency that accepted the request and then got stuck
	// (a deadlock, a lost lock, a GC pause that never ends...).
	stuck := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		select {
		case <-release:
		case <-r.Context().Done():
		}
	}))
	defer stuck.Close()

	// --- The trap: 20 calls through the default client. ---
	before := runtime.NumGoroutine()
	finished := make(chan error, 20)
	for i := 0; i < 20; i++ {
		go func() {
			resp, err := http.Get(stuck.URL) // DefaultClient, Timeout 0
			if err == nil {
				resp.Body.Close()
			}
			finished <- err
		}()
	}
	time.Sleep(1 * time.Second)
	fmt.Printf("DefaultClient: after 1s, %d of 20 calls have returned; goroutines %d -> %d\n",
		len(finished), before, runtime.NumGoroutine())
	if len(finished) != 0 {
		panic("with no timeout, none of the calls should have returned yet")
	}

	// --- The fix: a client with a timeout. ---
	client := &http.Client{Timeout: 200 * time.Millisecond}
	start := time.Now()
	_, err := client.Get(stuck.URL)
	var urlErr *url.Error
	if !errors.As(err, &urlErr) || !urlErr.Timeout() {
		panic(fmt.Sprintf("expected a timeout error, got %v", err))
	}
	fmt.Printf("Client{Timeout: 200ms}: gave up after %v with %q\n",
		time.Since(start).Round(10*time.Millisecond), "Client.Timeout exceeded")

	// The 20 default-client calls return only when the server lets go.
	if len(finished) != 0 {
		panic("the default-client calls should still be blocked")
	}
	close(release)
	for i := 0; i < 20; i++ {
		select {
		case <-finished:
		case <-time.After(2 * time.Second):
			panic("released calls should finish promptly")
		}
	}
	fmt.Println("the 20 default-client calls returned only after the server released them")
	fmt.Println("OK")
}
