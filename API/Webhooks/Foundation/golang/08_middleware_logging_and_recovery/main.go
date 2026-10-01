/*
FOUNDATION LEVEL 08 - Middleware: code that wraps every delivery
====================================================================
Levels 00-07 put everything a delivery needed inside one handler. Middleware is
a WRAPPER: a function that takes an http.Handler and returns a new http.Handler
that runs code before and/or after calling the original - without touching the
original at all. Signature checks (09), source scoping (10), logging and
recovery all become one line each, applied to every event type at once.

For a receiver, recovery is not a nicety. A handler that panics has TWO bad
outcomes to avoid: the obvious one (net/http closes the connection, so the
sender sees a broken pipe, times out and retries blind) and the sneaky one (a
framework that answers 200 by default on an error, after which the event is
lost forever). Recovery makes the failure explicit and correct: log it, answer
500, and let the sender retry on purpose (level 06).

You will learn
  - a Middleware is just "func(http.Handler) http.Handler" - it wraps a handler
    and returns something that is STILL a handler
  - chaining: wrapping a wrapper in a wrapper, in a chosen order
  - ORDER matters: logging placed OUTSIDE recovery still logs the crashed
    delivery and the 500 it became; placed INSIDE, it would never run at all
  - a webhook log line is worth designing: event type, event id, delivery id,
    outcome, duration - that is what you will search at 3am
  - recover() inside a deferred function is Go's way to catch a panic in ONE
    delivery without taking down the process for the next one

Run it   go run ./Webhooks/Foundation/golang/08_middleware_logging_and_recovery
*/
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"time"
)

type Middleware func(http.Handler) http.Handler

// statusRecorder lets middleware see the status a handler decided on, by
// intercepting the one call that sets it. It also remembers whether anything
// was written at all, which is how recovery knows a panic happened mid-response.
type statusRecorder struct {
	http.ResponseWriter
	status int
}

func (r *statusRecorder) WriteHeader(code int) {
	r.status = code
	r.ResponseWriter.WriteHeader(code)
}

var (
	logLines []string
	refunds  []string
)

func sendJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(payload)
}

// ---- the "real" application logic, with zero knowledge of logging/recovery ----
func dispatch(w http.ResponseWriter, r *http.Request) {
	raw, _ := io.ReadAll(http.MaxBytesReader(w, r.Body, 1_000_000))
	var event struct {
		Type string         `json:"type"`
		ID   string         `json:"id"`
		Data map[string]any `json:"data"`
	}
	json.Unmarshal(raw, &event)
	// The event type and id travel to the middleware via headers we set on the
	// request, so the log line can name them without parsing the body twice.
	r.Header.Set("X-Parsed-Type", event.Type)
	r.Header.Set("X-Parsed-Event", event.ID)

	switch event.Type {
	case "refund.created":
		refunds = append(refunds, event.ID)
		sendJSON(w, http.StatusOK, map[string]bool{"handled": true})
	case "order.exploded":
		// A real bug: the handler assumes a field the payload does not have.
		panic("nil dereference on data.customer.email")
	default:
		sendJSON(w, http.StatusOK, map[string]any{"handled": false, "reason": "unsubscribed event type"})
	}
}

// ---- middleware #1: the log line you will actually page through ----
func withLogging(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		started := time.Now()
		rec := &statusRecorder{ResponseWriter: w, status: 200}
		next.ServeHTTP(rec, r)
		line := fmt.Sprintf("delivery=%s type=%s event=%s status=%d (%s)",
			r.Header.Get("X-Webhook-Delivery"), r.Header.Get("X-Parsed-Type"),
			r.Header.Get("X-Parsed-Event"), rec.status, time.Since(started).Round(time.Microsecond))
		logLines = append(logLines, line)
		fmt.Println("  [log] " + line)
	})
}

// ---- middleware #2: catches ANY panic from everything it wraps ----
func withRecovery(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if problem := recover(); problem != nil {
				fmt.Printf("  [recovery] caught %v - answering 500 so the sender retries, staying up\n", problem)
				sendJSON(w, http.StatusInternalServerError,
					map[string]string{"error": "internal error, please retry"})
			}
		}()
		next.ServeHTTP(w, r)
	})
}

func main() {
	// Built once, outside in: logging sees everything, including failures that
	// recovery converts into a deliberate 500. Swap the order and the crashed
	// delivery vanishes from your logs - the one line you most needed.
	handler := withLogging(withRecovery(http.HandlerFunc(dispatch)))

	mux := http.NewServeMux()
	mux.Handle("POST /webhook", handler)

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, mux)
	base := "http://" + ln.Addr().String()

	deliver := func(deliveryID, body string) (int, string) {
		req, _ := http.NewRequest("POST", base+"/webhook", bytes.NewBufferString(body))
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("X-Webhook-Delivery", deliveryID)
		res, err := http.DefaultClient.Do(req)
		if err != nil {
			log.Fatal(err)
		}
		defer res.Body.Close()
		answer, _ := io.ReadAll(res.Body)
		return res.StatusCode, string(bytes.TrimSpace(answer))
	}

	status, body := deliver("dlv_1", `{"type":"refund.created","id":"evt_1","data":{}}`)
	fmt.Printf("refund.created  -> %d %s\n", status, body)
	if status != 200 {
		panic("FAILED")
	}

	status, body = deliver("dlv_2", `{"type":"order.exploded","id":"evt_2","data":{}}`)
	fmt.Printf("order.exploded  -> %d %s   (the handler panicked - recovery made it a deliberate 500)\n", status, body)
	if status != 500 {
		panic("FAILED")
	}

	// The panic above must not have taken the receiver down for the next sender.
	status, body = deliver("dlv_3", `{"type":"refund.created","id":"evt_3","data":{}}`)
	fmt.Printf("refund.created  -> %d %s   (receiver still alive after the panic)\n", status, body)
	if status != 200 {
		panic("FAILED")
	}

	if len(refunds) != 2 || len(logLines) != 3 {
		panic("FAILED: every delivery must be logged, INCLUDING the one that crashed")
	}
	if !bytes.Contains([]byte(logLines[1]), []byte("status=500")) {
		panic("FAILED: the crashed delivery's log line must show the 500")
	}
	fmt.Println("OK")
}
