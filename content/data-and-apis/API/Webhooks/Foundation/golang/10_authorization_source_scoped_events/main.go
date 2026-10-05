/*
FOUNDATION LEVEL 10 - Authorization: each source may only send its own events
================================================================================
Authentication (level 09) proved a delivery was signed by SOMEONE we share a
secret with. Authorization is a different question: is THIS sender allowed to
trigger THIS event type?

It matters as soon as you integrate more than one system - and everyone does.
Your receiver ends up with a billing provider, a support desk, a CI system, all
POSTing to you. Give them one shared secret and you have built a privilege
escalation: the support desk's secret (or a leaked support integration) can now
fabricate refund.created and move money. Two rules fix it:

	every source gets its OWN secret          -> a leak is contained to one source
	every source gets its OWN allowed types   -> a valid signature is not a blank cheque

So "billing" may send refund.created; "support", correctly signed with its own
real secret, may not - and that is a 403, not a 401. The difference is the whole
level: 401 means "I do not know you", 403 means "I know exactly who you are and
the answer is still no".

You will learn
  - per-source secrets, selected by the source in the URL, checked with that
    source's key only (never "try every secret until one matches")
  - an allow-list of event types per source - authorization data, not code
  - 403 Forbidden vs 401 Unauthorized, on the same endpoint, same day
  - the order that this forces: identify -> authenticate -> authorize -> dispatch
  - why a 403 is a permanent answer: the sender must NOT retry it (level 06)

Run it   go run ./Webhooks/Foundation/golang/10_authorization_source_scoped_events
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
	"slices"
)

// registration is one record per source: its own secret, its own scope. In a
// real receiver this is a database table you can edit without deploying code.
type registration struct {
	secret       []byte
	allowedTypes []string
}

var sources = map[string]registration{
	"billing": {secret: []byte("whsec_billing_only"), allowedTypes: []string{"invoice.paid", "refund.created"}},
	"support": {secret: []byte("whsec_support_only"), allowedTypes: []string{"ticket.created", "ticket.closed"}},
}

var processed []string

func sign(key, rawBody []byte) string {
	mac := hmac.New(sha256.New, key)
	mac.Write(rawBody)
	return hex.EncodeToString(mac.Sum(nil))
}

func sendJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(payload)
}

func webhookHandler(w http.ResponseWriter, r *http.Request) {
	// ---- 1. IDENTIFY: which registration is this delivery claiming to be? ----
	// Each source gets its own endpoint URL, exactly as real providers are given.
	sourceName := r.PathValue("source")
	source, registered := sources[sourceName]

	raw, _ := io.ReadAll(http.MaxBytesReader(w, r.Body, 1_000_000))

	if !registered {
		// An unregistered source is an identity failure, not a scope failure.
		sendJSON(w, http.StatusUnauthorized, map[string]string{"error": "unknown webhook source"})
		return
	}

	// ---- 2. AUTHENTICATE: with THIS source's secret, and only that one ----
	provided := r.Header.Get("X-Webhook-Signature")
	if provided == "" || !hmac.Equal([]byte(sign(source.secret, raw)), []byte(provided)) {
		sendJSON(w, http.StatusUnauthorized,
			map[string]string{"error": "invalid signature for source " + sourceName})
		return
	}

	var event struct {
		Type string `json:"type"`
		ID   string `json:"id"`
	}
	json.Unmarshal(raw, &event)

	// ---- 3. AUTHORIZE: is this type inside the source's registered scope? ----
	if !slices.Contains(source.allowedTypes, event.Type) {
		fmt.Printf("  [receiver] %s is genuine but not scoped for %s -> 403\n", sourceName, event.Type)
		sendJSON(w, http.StatusForbidden, map[string]any{
			"error":   fmt.Sprintf("source %q may not send %q", sourceName, event.Type),
			"allowed": source.allowedTypes,
		})
		return
	}

	// ---- 4. DISPATCH: everything above passed ----
	processed = append(processed, sourceName+":"+event.Type)
	sendJSON(w, http.StatusOK, map[string]string{"accepted": event.ID, "source": sourceName})
}

func main() {
	mux := http.NewServeMux()
	// A wildcard segment, so one handler serves every registered source's URL.
	mux.HandleFunc("POST /webhook/{source}", webhookHandler)

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, mux)
	base := "http://" + ln.Addr().String()

	deliver := func(source, body string, signWith []byte) (int, string) {
		raw := []byte(body)
		req, _ := http.NewRequest("POST", base+"/webhook/"+source, bytes.NewReader(raw))
		req.Header.Set("Content-Type", "application/json")
		if signWith != nil {
			req.Header.Set("X-Webhook-Signature", sign(signWith, raw))
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
	refund := `{"type":"refund.created","id":"evt_1","data":{"amount":500}}`
	ticket := `{"type":"ticket.created","id":"evt_2","data":{"subject":"help"}}`

	status, body := deliver("billing", refund, billing)
	fmt.Printf("billing -> refund.created (own secret)  -> %d %s\n", status, body)
	if status != 200 {
		panic("FAILED")
	}

	status, body = deliver("support", ticket, support)
	fmt.Printf("support -> ticket.created (own secret)  -> %d %s\n", status, body)
	if status != 200 {
		panic("FAILED")
	}

	// The point of the level: a perfectly valid, correctly signed delivery from
	// a source that has no business creating refunds.
	status, body = deliver("support", refund, support)
	fmt.Printf("support -> refund.created (own secret)  -> %d %s\n", status, body)
	if status != 403 {
		panic("FAILED")
	}

	// Signed with the WRONG source's secret: never gets as far as scope.
	status, body = deliver("billing", refund, support)
	fmt.Printf("billing -> refund.created (support key) -> %d %s   (secrets do not interchange)\n", status, body)
	if status != 401 {
		panic("FAILED")
	}

	status, body = deliver("ci-system", ticket, support)
	fmt.Printf("ci-system (never registered)            -> %d %s\n", status, body)
	if status != 401 {
		panic("FAILED")
	}

	fmt.Printf("processed: %v\n", processed)
	if len(processed) != 2 || processed[0] != "billing:refund.created" || processed[1] != "support:ticket.created" {
		panic("FAILED")
	}
	fmt.Println("OK")
}
