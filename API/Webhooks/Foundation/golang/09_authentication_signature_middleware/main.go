/*
FOUNDATION LEVEL 09 - Authentication: the signature check, as middleware
============================================================================
This IS level 04's check. Same secret, same HMAC-SHA256 over the raw body, same
hmac.Equal. Nothing about the cryptography changes here. What changes is WHERE
it lives: level 04 wrote the check inline at the top of the handler, and this
level lifts it out into middleware (level 08's mechanism) that runs before
dispatch ever happens.

That move is the whole lesson, and it is not cosmetic. The check cannot be
forgotten on a new event type, because there is one door. Handlers stop
containing security code, so they get simple and testable. And a rejection
short-circuits - dispatch is never called, so an unauthenticated delivery costs
you one hash and nothing else.

Authentication answers exactly ONE question: "is this delivery really from the
sender we share a secret with?" It says nothing about what that sender is
allowed to trigger - that is level 10, authorization, and it is deliberately a
separate concept. For webhooks the identity is the SENDER, not a user: there is
no login, no session, no bearer token you chose. The signature is the identity.

You will learn
  - how to turn an inline check into middleware, and why one door beats ten
  - 401 Unauthorized means "we do not recognize you" - never confuse it with
    403 (level 10), which means "we know you and the answer is still no"
  - middleware needs the RAW body, so read it ONCE at the edge and put those
    exact bytes back with io.NopCloser for the handler downstream
  - context.WithValue is how Go attaches the verified sender onto the request,
    so nothing downstream re-checks the signature

Run it   go run ./Webhooks/Foundation/golang/09_authentication_signature_middleware
*/
package main

import (
	"bytes"
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
)

var secret = []byte("whsec_shared_with_the_provider")

type ctxKey string

const senderCtxKey ctxKey = "sender"

var dispatchCalls []string

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

// withAuthentication is level 04's four lines, now guarding every event type.
func withAuthentication(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		provided := r.Header.Get("X-Webhook-Signature")
		if provided == "" {
			sendJSON(w, http.StatusUnauthorized, map[string]string{"error": "missing signature header"})
			return
		}

		// Read the body ONCE here, then put the same bytes back so the handler
		// can read them too. Re-reading a consumed body yields nothing, and
		// re-encoding it would change the bytes the signature was computed over.
		raw, err := io.ReadAll(http.MaxBytesReader(w, r.Body, 1_000_000))
		if err != nil {
			sendJSON(w, http.StatusRequestEntityTooLarge, map[string]string{"error": "payload too large"})
			return
		}
		r.Body = io.NopCloser(bytes.NewReader(raw))

		if !hmac.Equal([]byte(sign(secret, raw)), []byte(provided)) {
			sendJSON(w, http.StatusUnauthorized, map[string]string{"error": "invalid signature"})
			return
		}

		// Now every handler downstream knows who this is, via the context.
		ctx := context.WithValue(r.Context(), senderCtxKey, "payments-provider")
		next.ServeHTTP(w, r.WithContext(ctx)) // only reached by verified deliveries
	})
}

// dispatch has no security code in it at all - and there is no way to reach this
// line without having passed the middleware above.
func dispatch(w http.ResponseWriter, r *http.Request) {
	raw, _ := io.ReadAll(r.Body)
	var event struct {
		Type string `json:"type"`
		ID   string `json:"id"`
	}
	json.Unmarshal(raw, &event)
	dispatchCalls = append(dispatchCalls, event.ID)
	sender, _ := r.Context().Value(senderCtxKey).(string) // set by withAuthentication
	sendJSON(w, http.StatusOK, map[string]string{"accepted": event.ID, "from": sender})
}

func main() {
	mux := http.NewServeMux()
	mux.Handle("POST /webhook", withAuthentication(http.HandlerFunc(dispatch)))

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, mux)
	base := "http://" + ln.Addr().String()

	deliver := func(raw []byte, signature string) (int, map[string]string) {
		req, _ := http.NewRequest("POST", base+"/webhook", bytes.NewReader(raw))
		req.Header.Set("Content-Type", "application/json")
		if signature != "" {
			req.Header.Set("X-Webhook-Signature", signature)
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

	status, body := deliver(raw, "")
	fmt.Printf("no signature        -> %d %v\n", status, body)
	if status != 401 {
		panic("FAILED")
	}

	status, body = deliver(raw, sign([]byte("whsec_wrong"), raw))
	fmt.Printf("wrong secret        -> %d %v\n", status, body)
	if status != 401 {
		panic("FAILED")
	}

	status, body = deliver(raw, "not-even-hex")
	fmt.Printf("garbage signature   -> %d %v\n", status, body)
	if status != 401 {
		panic("FAILED")
	}

	status, body = deliver(raw, sign(secret, raw))
	fmt.Printf("correctly signed    -> %d %v   (and only now is the sender known)\n", status, body)
	if status != 200 || body["from"] != "payments-provider" {
		panic("FAILED")
	}

	// The short-circuit, proved: three rejected deliveries never reached dispatch.
	fmt.Printf("dispatch was called for: %v\n", dispatchCalls)
	if len(dispatchCalls) != 1 || dispatchCalls[0] != "evt_1" {
		panic("FAILED")
	}
	fmt.Println("OK")
}
