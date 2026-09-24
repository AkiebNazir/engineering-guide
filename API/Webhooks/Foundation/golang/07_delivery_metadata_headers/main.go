/*
FOUNDATION LEVEL 07 - Delivery metadata: the headers around the event
=========================================================================
The body says WHAT happened. Three headers say things about THIS ATTEMPT to
tell you, and they are not interchangeable:

	X-Webhook-Delivery    a unique id for this ATTEMPT. A retry of the same
	                      event gets a NEW delivery id. Log it, never dedupe on it.
	X-Webhook-Timestamp   when the sender signed the request (unix seconds)
	X-Webhook-Signature   level 04's HMAC - but now over "<timestamp>.<body>"

That last change is the point of this level. A signature over the body alone is
valid FOREVER: anyone who captures one legitimate delivery can replay those
exact bytes at you next year and the signature still verifies. Binding the
timestamp INTO the signed string, and then refusing anything outside a few
minutes, closes that window. The timestamp has to be signed, or an attacker
would simply edit the header.

You will learn
  - event id vs delivery id: one is stable across retries (dedupe key), the
    other is unique per attempt (log/support key)
  - signing "<timestamp>.<raw_body>" instead of the raw body alone
  - a replay window: reject timestamps older (or newer) than the tolerance
  - why the clock check comes AFTER the signature check: until the HMAC passes,
    the timestamp header is just an attacker-supplied string
  - that this is exactly the scheme Stripe and the Standard Webhooks spec use
    (see ../../labs/golang/02_provider_signature_schemes)

Run it   go run ./Webhooks/Foundation/golang/07_delivery_metadata_headers
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
	"math"
	"net"
	"net/http"
	"strconv"
	"time"
)

var secret = []byte("whsec_shared_with_the_provider")

const tolerance = 300 // seconds: five minutes either side, like most providers

var (
	processed   []string
	deliveryLog []string
)

// signedPayload is the exact byte string both sides hash. The separator matters
// as much as the parts: without it, timestamp "1" + body "23..." and "12" +
// "3..." would hash identically.
func signedPayload(timestamp string, rawBody []byte) []byte {
	return append([]byte(timestamp+"."), rawBody...)
}

func sign(key []byte, timestamp string, rawBody []byte) string {
	mac := hmac.New(sha256.New, key)
	mac.Write(signedPayload(timestamp, rawBody))
	return hex.EncodeToString(mac.Sum(nil))
}

func sendJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(payload)
}

func webhookHandler(w http.ResponseWriter, r *http.Request) {
	raw, _ := io.ReadAll(http.MaxBytesReader(w, r.Body, 1_000_000))

	deliveryID := r.Header.Get("X-Webhook-Delivery")
	timestamp := r.Header.Get("X-Webhook-Timestamp")
	signature := r.Header.Get("X-Webhook-Signature")
	if deliveryID == "" || timestamp == "" || signature == "" {
		sendJSON(w, http.StatusBadRequest, map[string]string{"error": "missing delivery metadata headers"})
		return
	}

	// 1. Verify the signature over timestamp + body.
	if !hmac.Equal([]byte(sign(secret, timestamp, raw)), []byte(signature)) {
		sendJSON(w, http.StatusUnauthorized, map[string]string{"error": "invalid signature"})
		return
	}

	// 2. Only now is the timestamp trustworthy - so now we can judge its age.
	signedAt, err := strconv.ParseInt(timestamp, 10, 64)
	if err != nil {
		sendJSON(w, http.StatusBadRequest, map[string]string{"error": "timestamp is not an integer"})
		return
	}
	age := math.Abs(float64(time.Now().Unix() - signedAt))
	if age > tolerance {
		// Correctly signed, but far too old (or from the future - a badly skewed
		// clock). A 400: retrying these same bytes will only get older.
		fmt.Printf("  [receiver] delivery=%s signature valid but %.0fs old -> replay window closed\n", deliveryID, age)
		sendJSON(w, http.StatusBadRequest,
			map[string]string{"error": fmt.Sprintf("timestamp outside the %ds tolerance", tolerance)})
		return
	}

	var event struct {
		Type string `json:"type"`
		ID   string `json:"id"`
	}
	json.Unmarshal(raw, &event)
	// The delivery id is what you quote in a support ticket ("we never got
	// delivery 7f3a"); the EVENT id is what you dedupe on (level 03).
	deliveryLog = append(deliveryLog, deliveryID+" carried event "+event.ID)
	processed = append(processed, event.ID)
	sendJSON(w, http.StatusOK, map[string]string{"accepted": event.ID, "delivery": deliveryID})
}

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("POST /webhook", webhookHandler)

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, mux)
	base := "http://" + ln.Addr().String()

	// deliver plays the sender. An empty overrideSignature means "sign correctly".
	deliver := func(raw []byte, deliveryID string, timestamp int64, overrideSignature string) (int, map[string]string) {
		ts := strconv.FormatInt(timestamp, 10)
		req, _ := http.NewRequest("POST", base+"/webhook", bytes.NewReader(raw))
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("X-Webhook-Delivery", deliveryID)
		req.Header.Set("X-Webhook-Timestamp", ts)
		if overrideSignature != "" {
			req.Header.Set("X-Webhook-Signature", overrideSignature)
		} else {
			req.Header.Set("X-Webhook-Signature", sign(secret, ts, raw))
		}
		res, err := http.DefaultClient.Do(req)
		if err != nil {
			log.Fatal(err)
		}
		defer res.Body.Close()
		var parsed map[string]string
		json.NewDecoder(res.Body).Decode(&parsed)
		return res.StatusCode, parsed
	}

	raw := []byte(`{"type":"invoice.paid","id":"evt_1","data":{"amount":500}}`)
	now := time.Now().Unix()

	status, body := deliver(raw, "dlv_001", now, "")
	fmt.Printf("fresh, signed delivery      -> %d %v\n", status, body)
	if status != 200 {
		panic("FAILED")
	}

	// The retry of the SAME event: new delivery id, new timestamp, same event id.
	status, body = deliver(raw, "dlv_002", now, "")
	fmt.Printf("retry (new delivery id)     -> %d %v   (same event id inside - level 03 dedupes it)\n", status, body)
	if status != 200 || body["delivery"] != "dlv_002" {
		panic("FAILED")
	}

	// A captured delivery replayed an hour later, signature perfectly intact.
	old := now - 3600
	status, body = deliver(raw, "dlv_003", old, "")
	fmt.Printf("replayed one hour later     -> %d %v\n", status, body)
	if status != 400 {
		panic("FAILED")
	}

	// An attacker who rewrites the timestamp header to look fresh: the signature
	// was computed over the OLD timestamp, so it no longer matches.
	status, body = deliver(raw, "dlv_004", now, sign(secret, strconv.FormatInt(old, 10), raw))
	fmt.Printf("timestamp header rewritten  -> %d %v   (the timestamp is inside the signature)\n", status, body)
	if status != 401 {
		panic("FAILED")
	}

	status, body = deliver(raw, "", now, "")
	fmt.Printf("no metadata headers at all  -> %d %v\n", status, body)
	if status != 400 {
		panic("FAILED")
	}

	fmt.Printf("delivery log: %v\n", deliveryLog)
	if len(processed) != 2 || len(deliveryLog) != 2 {
		panic("FAILED")
	}
	fmt.Println("OK")
}
