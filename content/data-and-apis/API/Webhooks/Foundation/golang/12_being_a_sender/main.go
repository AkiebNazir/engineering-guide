/*
FOUNDATION LEVEL 12 - Being the sender: signing and delivering a webhook
============================================================================
Levels 00-11 were all RECEIVER code. Now switch chairs. Every provider whose
webhooks you consume runs the code in this file, and you will write it too the
first time your own service needs to notify customers.

This is the mirror of every other API type's "being a client" level, but with a
twist that is unique to webhooks: nobody asked you for this request. There is no
user waiting, no response to render. You are calling into someone else's server,
unprompted, and you are entirely responsible for making sure the event
eventually lands - which means the retry loop is not optional, it IS the feature.

The sender's contract, in the order this file does it:

 1. marshal the event ONCE and keep those exact bytes
 2. sign timestamp + bytes, put delivery id / timestamp / signature in headers
 3. POST with a short timeout - a slow receiver must not block your queue
 4. read the status code and decide: done / retry later / give up (level 06)
 5. back off exponentially between attempts, honouring Retry-After
 6. keep the EVENT id stable across attempts so the receiver can dedupe, and
    give each ATTEMPT a fresh delivery id so logs stay untangled

You will learn
  - marshal once, sign the same bytes you send (re-encoding breaks the HMAC)
  - exponential backoff, and why a fixed 1s retry is how you flatten a
    recovering receiver with your whole queue at once
  - giving up: a 4xx goes to a dead-letter queue, not back on the retry loop
  - that "at-least-once" is a SENDER-side decision, and duplicates are its
    unavoidable price (level 03 is the receiver paying it)

Run it   go run ./Webhooks/Foundation/golang/12_being_a_sender
*/
package main

import (
	"bytes"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"strconv"
	"sync"
	"time"
)

var secret = []byte("whsec_shared_with_the_receiver")

const (
	timeout     = 500 * time.Millisecond // never let one slow receiver hold a sender goroutine hostage
	maxAttempts = 4
	baseBackoff = 50 * time.Millisecond // tiny so the demo is quick; real senders use seconds -> hours
)

type Envelope struct {
	Type string         `json:"type"`
	ID   string         `json:"id"`
	Data map[string]any `json:"data"`
}

type failed struct {
	event  Envelope
	status int
}

var (
	deadLetter   []failed
	attemptsMu   sync.Mutex
	attemptsSeen = map[string]int{}
)

func sign(key []byte, timestamp string, rawBody []byte) string {
	mac := hmac.New(sha256.New, key)
	mac.Write(append([]byte(timestamp+"."), rawBody...))
	return hex.EncodeToString(mac.Sum(nil))
}

// ---------------------------------------------------------------------------
// THE SENDER
// ---------------------------------------------------------------------------
var client = &http.Client{Timeout: timeout}

// attemptDelivery makes one HTTP attempt. A status of 0 means the receiver never
// answered, which is NOT the same as answering "no".
func attemptDelivery(url string, raw []byte, eventID string, attempt int) (int, string) {
	timestamp := strconv.FormatInt(time.Now().Unix(), 10)
	req, _ := http.NewRequest("POST", url, bytes.NewReader(raw))
	req.Header.Set("Content-Type", "application/json")
	// New per ATTEMPT - so the receiver's logs can tell attempts apart...
	req.Header.Set("X-Webhook-Delivery", fmt.Sprintf("dlv_%s_%d", eventID, attempt))
	req.Header.Set("X-Webhook-Timestamp", timestamp)
	// ...re-signed per attempt, because the timestamp is inside the signature.
	req.Header.Set("X-Webhook-Signature", sign(secret, timestamp, raw))

	res, err := client.Do(req)
	if err != nil {
		return 0, ""
	}
	defer res.Body.Close()
	io.ReadAll(res.Body)
	return res.StatusCode, res.Header.Get("Retry-After")
}

// sendEvent delivers one event, with retries. Returns (delivered, attemptsUsed).
func sendEvent(url string, event Envelope) (bool, int) {
	raw, _ := json.Marshal(event) // marshal ONCE; these are the signed bytes

	for attempt := 1; attempt <= maxAttempts; attempt++ {
		status, retryAfter := attemptDelivery(url, raw, event.ID, attempt)

		if status >= 200 && status < 300 {
			fmt.Printf("  [sender] attempt %d: %d - delivered, stopping\n", attempt, status)
			return true, attempt
		}

		permanent := status >= 400 && status < 500 && status != 408 && status != 429
		if permanent {
			// The receiver told us this payload will never work. Retrying it is
			// pure waste; a human needs to look at it.
			fmt.Printf("  [sender] attempt %d: %d - permanent rejection, dead-lettering\n", attempt, status)
			deadLetter = append(deadLetter, failed{event, status})
			return false, attempt
		}

		if attempt == maxAttempts {
			fmt.Printf("  [sender] attempt %d: %d - out of attempts, dead-lettering for now\n", attempt, status)
			deadLetter = append(deadLetter, failed{event, status})
			return false, attempt
		}

		// Exponential backoff: 1x, 2x, 4x... so a struggling receiver gets more
		// room each time, not the same hammering. Retry-After overrides us.
		wait := baseBackoff * (1 << (attempt - 1))
		reason := "backoff"
		if retryAfter != "" {
			if seconds, err := strconv.Atoi(retryAfter); err == nil {
				wait, reason = time.Duration(seconds)*time.Second, "Retry-After"
			}
		}
		fmt.Printf("  [sender] attempt %d: %d - retrying in %v (%s)\n", attempt, status, wait, reason)
		time.Sleep(wait)
	}
	return false, maxAttempts
}

// ---------------------------------------------------------------------------
// A RECEIVER to deliver to, so the sender has something to fight with.
// ---------------------------------------------------------------------------
func sendJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(payload)
}

func receiver(w http.ResponseWriter, r *http.Request) {
	raw, _ := io.ReadAll(http.MaxBytesReader(w, r.Body, 1_000_000))

	attemptsMu.Lock()
	attemptsSeen[r.URL.Path]++
	n := attemptsSeen[r.URL.Path]
	attemptsMu.Unlock()

	timestamp := r.Header.Get("X-Webhook-Timestamp")
	if !hmac.Equal([]byte(sign(secret, timestamp, raw)), []byte(r.Header.Get("X-Webhook-Signature"))) {
		sendJSON(w, http.StatusUnauthorized, map[string]string{"error": "invalid signature"})
		return
	}

	switch r.URL.Path {
	case "/good":
		sendJSON(w, http.StatusAccepted, map[string]string{"status": "queued"})
	case "/flaky":
		// Down for the first two attempts, then recovers - the single most
		// common real situation, and exactly what backoff exists for.
		if n <= 2 {
			sendJSON(w, http.StatusServiceUnavailable, map[string]string{"error": "still starting up"})
		} else {
			sendJSON(w, http.StatusAccepted, map[string]string{"status": "queued"})
		}
	case "/bad-payload":
		sendJSON(w, http.StatusBadRequest, map[string]string{"error": "data.amount must be an integer"})
	default:
		sendJSON(w, http.StatusNotFound, map[string]string{"error": "no endpoint registered"})
	}
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, http.HandlerFunc(receiver))
	base := "http://" + ln.Addr().String()

	event := Envelope{Type: "invoice.paid", ID: "evt_1", Data: map[string]any{"amount": 500}}

	fmt.Println("delivering to a healthy receiver:")
	delivered, used := sendEvent(base+"/good", event)
	if !delivered || used != 1 {
		panic("FAILED")
	}

	fmt.Println("delivering to a receiver that is down, then recovers:")
	delivered, used = sendEvent(base+"/flaky", event)
	fmt.Printf("  -> delivered=%v after %d attempts, receiver saw %d\n", delivered, used, attemptsSeen["/flaky"])
	if !delivered || used != 3 || attemptsSeen["/flaky"] != 3 {
		panic("FAILED")
	}

	fmt.Println("delivering a payload the receiver permanently rejects:")
	delivered, used = sendEvent(base+"/bad-payload", event)
	fmt.Printf("  -> delivered=%v after %d attempt (no retries: 400 is final)\n", delivered, used)
	if delivered || used != 1 || attemptsSeen["/bad-payload"] != 1 {
		panic("FAILED")
	}

	fmt.Println("delivering to an endpoint that does not exist:")
	delivered, used = sendEvent(base+"/gone", event)
	if delivered || used != 1 { // 404 is a 4xx: permanent
		panic("FAILED")
	}

	fmt.Printf("dead letter queue holds %d event(s): ", len(deadLetter))
	for _, d := range deadLetter {
		fmt.Printf("(%s, %d) ", d.event.ID, d.status)
	}
	fmt.Println()
	if len(deadLetter) != 2 {
		panic("FAILED")
	}
	fmt.Println("OK")
}
