/*
FOUNDATION LEVEL 11 - Putting it all together: one complete webhook receiver
================================================================================
Nothing new here. Every idea from levels 00-10 - the envelope, routing by type,
validation, idempotency, signature verification, the replay window, the fast
ACK, retry-aware status codes, logging, recovery, and source-scoped
authorization - combined into one receiver, in the order a real one uses:

	log -> recover -> authenticate (signature + timestamp)
	    -> validate -> authorize (source scope) -> dedupe -> enqueue -> 202
	                                                            |
	                                       background worker does the slow part

That order is not arbitrary. Cheap and security-critical checks go first, so a
hostile or broken delivery is rejected before it costs you anything; the slow,
failable work goes last, off the request path entirely.

This is deliberately the same shape as ../../labs/golang/01_receiver_net_http
and ../../labs/golang/03_delivery_worker_pool: once this feels easy, those labs
(bounded worker pools with back-pressure, provider signature schemes, replay
and rotation, SSRF-safe senders) are the very next step, not a jump.

You will learn
  - how ten small lessons compose into one real, secured, reliable receiver
  - that "a webhook receiver" is not one big new idea - it is these small ideas,
    layered in a deliberate order
  - which failures are the sender's to retry (5xx) and which are final (4xx)

Run it        go run ./Webhooks/Foundation/golang/11_complete_webhook_receiver
Keep serving  go run ./Webhooks/Foundation/golang/11_complete_webhook_receiver -serve
*/
package main

import (
	"bytes"
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"math"
	"net"
	"net/http"
	"slices"
	"strconv"
	"sync"
	"time"
)

const (
	maxBody   = 100_000
	tolerance = 300 // seconds
)

// ---- level 10: one registration record per source ----
type registration struct {
	secret       []byte
	allowedTypes []string
}

var sources = map[string]registration{
	"billing": {
		secret:       []byte("whsec_billing_only"),
		allowedTypes: []string{"invoice.paid", "invoice.disputed", "refund.created"},
	},
	"support": {
		secret:       []byte("whsec_support_only"),
		allowedTypes: []string{"ticket.created"},
	},
}

type Envelope struct {
	Type string          `json:"type"`
	ID   string          `json:"id"`
	Data json.RawMessage `json:"data"`
}

type queued struct {
	source string
	event  Envelope
}

type ctxKey string

const (
	sourceCtxKey ctxKey = "source"
	eventCtxKey  ctxKey = "event"
)

// ---- level 03: the dedupe store, and level 05: the work queue ----
var (
	mu        sync.Mutex
	seenIDs   = map[string]bool{}
	completed []string // what the worker actually finished
	logLines  []string

	work      = make(chan queued, 100)
	workGroup sync.WaitGroup
)

func sign(key []byte, timestamp string, rawBody []byte) string {
	mac := hmac.New(sha256.New, key)
	mac.Write(append([]byte(timestamp+"."), rawBody...))
	return hex.EncodeToString(mac.Sum(nil))
}

func sendJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(payload)
}

// worker is level 05: the slow, failable half of the job, off the request path.
func worker() {
	for item := range work {
		time.Sleep(50 * time.Millisecond) // pretend: charge, email, ship
		mu.Lock()
		completed = append(completed, item.source+":"+item.event.Type+":"+item.event.ID)
		mu.Unlock()
		workGroup.Done()
	}
}

// ---- level 08: logging, outermost so it sees every outcome ----
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
		started := time.Now()
		rec := &statusRecorder{ResponseWriter: w, status: 200}
		next.ServeHTTP(rec, r)
		line := fmt.Sprintf("delivery=%s status=%d (%s)",
			r.Header.Get("X-Webhook-Delivery"), rec.status, time.Since(started).Round(time.Millisecond))
		mu.Lock()
		logLines = append(logLines, line)
		mu.Unlock()
		fmt.Println("  [log] " + line)
	})
}

// ---- level 08: recovery, so one poisonous delivery cannot kill the next ----
func withRecovery(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if problem := recover(); problem != nil {
				fmt.Printf("  [recovery] caught %v\n", problem)
				sendJSON(w, http.StatusInternalServerError,
					map[string]string{"error": "internal error, please retry"})
			}
		}()
		next.ServeHTTP(w, r)
	})
}

// ---- levels 04 + 07 + 09: authentication with this source's secret, then the
// replay window - in that order, because an unverified timestamp means nothing.
func withAuthentication(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		sourceName := r.PathValue("source")
		source, registered := sources[sourceName]

		raw, err := io.ReadAll(http.MaxBytesReader(w, r.Body, maxBody))
		if err != nil {
			sendJSON(w, http.StatusRequestEntityTooLarge, map[string]string{"error": "payload too large"})
			return
		}
		r.Body = io.NopCloser(bytes.NewReader(raw)) // hand the SAME bytes downstream

		if !registered {
			sendJSON(w, http.StatusUnauthorized, map[string]string{"error": "unknown webhook source"})
			return
		}

		timestamp := r.Header.Get("X-Webhook-Timestamp")
		signature := r.Header.Get("X-Webhook-Signature")
		if timestamp == "" || signature == "" {
			sendJSON(w, http.StatusUnauthorized, map[string]string{"error": "missing signature or timestamp"})
			return
		}
		if !hmac.Equal([]byte(sign(source.secret, timestamp, raw)), []byte(signature)) {
			sendJSON(w, http.StatusUnauthorized, map[string]string{"error": "invalid signature"})
			return
		}

		signedAt, convErr := strconv.ParseInt(timestamp, 10, 64)
		if convErr != nil || math.Abs(float64(time.Now().Unix()-signedAt)) > tolerance {
			sendJSON(w, http.StatusBadRequest,
				map[string]string{"error": fmt.Sprintf("timestamp outside the %ds tolerance", tolerance)})
			return
		}

		next.ServeHTTP(w, r.WithContext(context.WithValue(r.Context(), sourceCtxKey, sourceName)))
	})
}

// ---- level 02: validation. Bad bytes are permanently bad -> 400 ----
func withValidation(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		raw, _ := io.ReadAll(r.Body)
		var event Envelope
		if json.Unmarshal(raw, &event) != nil {
			sendJSON(w, http.StatusBadRequest, map[string]string{"error": "body is not valid JSON"})
			return
		}
		if event.Type == "" || event.ID == "" {
			sendJSON(w, http.StatusBadRequest, map[string]string{"error": "envelope needs 'type' and 'id'"})
			return
		}
		next.ServeHTTP(w, r.WithContext(context.WithValue(r.Context(), eventCtxKey, event)))
	})
}

// ---- level 10: authorization. Genuine, but out of scope -> 403 ----
func withAuthorization(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		sourceName := r.Context().Value(sourceCtxKey).(string)
		event := r.Context().Value(eventCtxKey).(Envelope)
		if !slices.Contains(sources[sourceName].allowedTypes, event.Type) {
			sendJSON(w, http.StatusForbidden,
				map[string]string{"error": fmt.Sprintf("source %q may not send %q", sourceName, event.Type)})
			return
		}
		next.ServeHTTP(w, r)
	})
}

// ---- levels 01 + 03 + 05 + 06: route, dedupe, enqueue, ACK ----
func dispatch(w http.ResponseWriter, r *http.Request) {
	sourceName := r.Context().Value(sourceCtxKey).(string)
	event := r.Context().Value(eventCtxKey).(Envelope)

	if event.Type == "invoice.disputed" {
		// Stand-in for "my database is down": mine, temporary -> ask for a retry.
		sendJSON(w, http.StatusInternalServerError,
			map[string]string{"error": "storage unavailable, please retry"})
		return
	}

	mu.Lock()
	firstTime := !seenIDs[event.ID]
	seenIDs[event.ID] = true
	mu.Unlock()
	if !firstTime {
		sendJSON(w, http.StatusAccepted, map[string]string{"status": "duplicate", "id": event.ID})
		return
	}

	workGroup.Add(1)
	work <- queued{source: sourceName, event: event}
	sendJSON(w, http.StatusAccepted, map[string]string{"status": "queued", "id": event.ID})
}

func main() {
	serve := flag.Bool("serve", false, "keep serving on :8080 instead of running the demo")
	flag.Parse()

	go worker()

	// The chain, outside in. Read it top to bottom: that is the order a
	// delivery is examined in.
	receiver := withLogging(withRecovery(withAuthentication(withValidation(
		withAuthorization(http.HandlerFunc(dispatch))))))
	mux := http.NewServeMux()
	mux.Handle("POST /webhook/{source}", receiver)

	if *serve {
		log.Println("listening on http://localhost:8080/webhook/billing  (secret: whsec_billing_only)")
		log.Println("a delivery needs X-Webhook-Timestamp and X-Webhook-Signature - see level 12 for a sender")
		log.Fatal(http.ListenAndServe("127.0.0.1:8080", mux))
	}

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, mux)
	base := "http://" + ln.Addr().String()

	// The demo below plays the SENDER (level 12 does that properly).
	deliver := func(source, body string, secret []byte, timestamp int64, deliveryID string) (int, string) {
		raw := []byte(body)
		req, _ := http.NewRequest("POST", base+"/webhook/"+source, bytes.NewReader(raw))
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("X-Webhook-Delivery", deliveryID)
		if secret != nil {
			ts := strconv.FormatInt(timestamp, 10)
			req.Header.Set("X-Webhook-Timestamp", ts)
			req.Header.Set("X-Webhook-Signature", sign(secret, ts, raw))
		}
		res, err := http.DefaultClient.Do(req)
		if err != nil {
			log.Fatal(err)
		}
		defer res.Body.Close()
		answer, _ := io.ReadAll(res.Body)
		return res.StatusCode, string(bytes.TrimSpace(answer))
	}

	billing, support := sources["billing"].secret, sources["support"].secret
	paid := `{"type":"invoice.paid","id":"evt_1","data":{"amount":500}}`
	now := time.Now().Unix()

	checks := []struct {
		label      string
		source     string
		body       string
		secret     []byte
		timestamp  int64
		deliveryID string
		want       int
	}{
		{"unsigned delivery", "billing", paid, nil, now, "dlv_1", 401},
		{"signed with the wrong source's secret", "billing", paid, support, now, "dlv_2", 401},
		{"stale timestamp (replayed later)", "billing", paid, billing, now - 3600, "dlv_3", 400},
		{"malformed JSON", "billing", `{not json`, billing, now, "dlv_4", 400},
		{"out-of-scope event type", "support", paid, support, now, "dlv_5", 403},
		{"receiver temporarily broken", "billing",
			`{"type":"invoice.disputed","id":"evt_2"}`, billing, now, "dlv_6", 500},
		{"valid delivery", "billing", paid, billing, now, "dlv_7", 202},
		{"the sender retries the SAME event", "billing", paid, billing, now, "dlv_8", 202},
		{"a different event", "support",
			`{"type":"ticket.created","id":"evt_3"}`, support, now, "dlv_9", 202},
	}
	for _, c := range checks {
		status, body := deliver(c.source, c.body, c.secret, c.timestamp, c.deliveryID)
		fmt.Printf("%-38s -> %d %s\n", c.label, status, body)
		if status != c.want {
			panic("FAILED: " + c.label)
		}
	}

	workGroup.Wait()
	mu.Lock()
	defer mu.Unlock()
	fmt.Printf("work actually completed: %v\n", completed)
	if len(completed) != 2 || completed[0] != "billing:invoice.paid:evt_1" {
		panic("FAILED: exactly the two new events should have been processed, once each")
	}
	if len(logLines) != len(checks) {
		panic("FAILED: every delivery gets exactly one log line")
	}
	fmt.Println("OK")
}
