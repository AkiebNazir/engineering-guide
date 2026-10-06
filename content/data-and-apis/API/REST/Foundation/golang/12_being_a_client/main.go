/*
FOUNDATION LEVEL 12 - Every API you will ever use is also just a client
============================================================================
Levels 00-09 were all SERVER code. But you spend at least as much real-world
time writing CLIENTS: code that calls someone else's API. This level flips
the lens: a small server plays "someone else's API", and the interesting
code is the client calling it - handling timeouts, non-2xx responses, and
retrying a transient failure. This is deliberately where Foundation stops
and ../../labs/ (auth, rate limiting, retries, idempotency, pagination)
picks up.

You will learn
  - a client must treat "connection refused / timeout" and "got a 500" as two
    DIFFERENT failure kinds - one means "maybe try again", the other might
    too, but for a different reason (the server told you something, it did
    not just vanish)
  - exponential backoff: wait longer after each failed attempt, so a
    struggling server is not hammered harder while it is already struggling
  - why you must NEVER blindly retry every failed request (retrying a
    non-idempotent POST can create the same order twice - covered properly in
    ../../labs/golang/04_rate_limit_middleware and 05_api_key_auth_and_ownership)

Run it   go run ./REST/Foundation/golang/12_being_a_client
*/
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"time"
)

var attempts = 0

// flakyHandler fails the first 2 calls to /flaky with 503, then succeeds.
// Simulates a real service warming up or briefly overloaded - not actually broken.
func flakyHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/flaky" {
		w.WriteHeader(http.StatusNotFound)
		return
	}
	attempts++
	w.Header().Set("Content-Type", "application/json")
	if attempts <= 2 {
		w.Header().Set("Retry-After", "0")
		w.WriteHeader(http.StatusServiceUnavailable)
		json.NewEncoder(w).Encode(map[string]string{"error": "temporarily unavailable"})
		return
	}
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "ready"})
}

// getWithRetries: a GET is safe to retry - calling it twice never changes server state.
func getWithRetries(url string, maxAttempts int) (int, map[string]string, error) {
	client := &http.Client{Timeout: 2 * time.Second}
	var lastErr error

	for attempt := 1; attempt <= maxAttempts; attempt++ {
		res, err := client.Get(url)
		if err != nil {
			// The server did not even answer - back off and retry, same idea as below.
			lastErr = err
			if attempt == maxAttempts {
				return 0, nil, lastErr
			}
			time.Sleep(50 * time.Millisecond * (1 << (attempt - 1)))
			continue
		}
		body, _ := io.ReadAll(res.Body)
		res.Body.Close()
		var parsed map[string]string
		json.Unmarshal(body, &parsed)

		// The server DID respond - only 5xx is worth retrying, 4xx never is
		// (a 400 will still be a 400 next time; the request itself is bad).
		if res.StatusCode < 500 || attempt == maxAttempts {
			return res.StatusCode, parsed, nil
		}
		wait := 50 * time.Millisecond * (1 << (attempt - 1)) // 50ms, 100ms, 200ms, ...
		fmt.Printf("  attempt %d got %d, backing off %v before retrying\n", attempt, res.StatusCode, wait)
		time.Sleep(wait)
	}
	return 0, nil, lastErr
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, http.HandlerFunc(flakyHandler))
	base := "http://" + ln.Addr().String()

	status, body, err := getWithRetries(base+"/flaky", 5)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("final result -> %d %v\n", status, body)
	if status != 200 || body["status"] != "ready" {
		panic("FAILED")
	}
	if attempts != 3 {
		panic("FAILED: expected exactly 2 failures then 1 success")
	}
	fmt.Println("OK")
}
