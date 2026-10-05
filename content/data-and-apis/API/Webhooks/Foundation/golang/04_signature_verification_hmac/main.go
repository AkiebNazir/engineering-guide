/*
FOUNDATION LEVEL 04 - Signature verification: proving the delivery is real
=============================================================================
Your webhook URL is public. There is no login page in front of it, no session,
no API key you got to choose - anyone who learns the URL can POST
{"type":"invoice.paid","id":"evt_1"} and claim to be your payment provider.

The fix is a shared secret that never travels on the wire. When the provider
registers your endpoint, both sides store the same random string. For every
delivery the sender computes HMAC-SHA256(secret, raw_body) and puts it in a
header; you recompute the same thing and compare. Only someone holding the
secret can produce a matching value, so a match proves BOTH "this came from
them" and "nobody edited the body in flight".

Three details decide whether the check is actually secure:

 1. sign the RAW BODY BYTES - not a re-encoded struct. Unmarshal followed by
    Marshal changes spacing and key order, and the signature stops matching.
 2. compare with hmac.Equal (constant time), never ==, which leaks how many
    leading bytes were right via how long it took to say no.
 3. verify FIRST, decode and act SECOND. An invalid delivery must cause zero
    work and zero logging of its contents.

You will learn
  - what an HMAC is, in one line: a keyed hash - same body + same key = same
    digest, and you cannot produce it without the key (level 13 builds one by hand)
  - why 401 and not 400: this is an identity failure, not a malformed payload
  - why the raw bytes matter, demonstrated with a re-encoded body that fails
  - that a signature says nothing about WHEN - replay protection needs a
    timestamp too (level 07)

Run it   go run ./Webhooks/Foundation/golang/04_signature_verification_hmac
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
)

// In production this comes from the provider's dashboard and lives in a secret
// store / env var - never in the source tree like this.
var secret = []byte("whsec_shared_with_the_provider")

const signatureHeader = "X-Webhook-Signature"

var processed []string

// sign is the whole scheme: a keyed hash of the exact bytes, as lowercase hex.
func sign(key, rawBody []byte) string {
	mac := hmac.New(sha256.New, key)
	mac.Write(rawBody)
	return hex.EncodeToString(mac.Sum(nil))
}

// verify recomputes and compares in constant time. hmac.Equal takes the same
// amount of time whether the first byte differs or only the last one does.
func verify(key, rawBody []byte, provided string) bool {
	expected, err := hex.DecodeString(sign(key, rawBody))
	if err != nil {
		return false
	}
	got, err := hex.DecodeString(provided)
	if err != nil {
		return false // not even hex: certainly not our signature
	}
	return hmac.Equal(expected, got)
}

func sendJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(payload)
}

func webhookHandler(w http.ResponseWriter, r *http.Request) {
	raw, _ := io.ReadAll(http.MaxBytesReader(w, r.Body, 1_000_000)) // keep the RAW bytes; do not decode yet

	provided := r.Header.Get(signatureHeader)
	if provided == "" {
		sendJSON(w, http.StatusUnauthorized, map[string]string{"error": "missing signature"})
		return
	}
	if !verify(secret, raw, provided) {
		// No decoding, no logging of the body, no work. Just: no.
		fmt.Println("  [receiver] signature mismatch -> 401, nothing was decoded or processed")
		sendJSON(w, http.StatusUnauthorized, map[string]string{"error": "invalid signature"})
		return
	}

	var event struct {
		Type string `json:"type"`
		ID   string `json:"id"`
	}
	json.Unmarshal(raw, &event) // only NOW is it safe to look inside
	processed = append(processed, event.ID)
	sendJSON(w, http.StatusOK, map[string]string{"accepted": event.ID})
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

	deliver := func(raw []byte, signature string) (int, string) {
		req, _ := http.NewRequest("POST", base+"/webhook", bytes.NewReader(raw))
		req.Header.Set("Content-Type", "application/json")
		if signature != "" {
			req.Header.Set(signatureHeader, signature)
		}
		res, err := http.DefaultClient.Do(req)
		if err != nil {
			log.Fatal(err)
		}
		defer res.Body.Close()
		answer, _ := io.ReadAll(res.Body)
		return res.StatusCode, string(bytes.TrimSpace(answer))
	}

	raw := []byte(`{"type":"invoice.paid","id":"evt_1","data":{"amount":500}}`)

	status, body := deliver(raw, sign(secret, raw))
	fmt.Printf("correctly signed         -> %d %s\n", status, body)
	if status != 200 {
		panic("FAILED")
	}

	status, body = deliver(raw, "")
	fmt.Printf("no signature header      -> %d %s\n", status, body)
	if status != 401 {
		panic("FAILED")
	}

	status, body = deliver(raw, sign([]byte("whsec_attacker_guess"), raw))
	fmt.Printf("signed with wrong secret -> %d %s   (an impostor who knows the URL but not the secret)\n", status, body)
	if status != 401 {
		panic("FAILED")
	}

	// Same signature, body edited in flight: the amount is now 50000.
	tampered := bytes.Replace(raw, []byte("500"), []byte("50000"), 1)
	status, body = deliver(tampered, sign(secret, raw))
	fmt.Printf("body tampered in flight  -> %d %s   (the signature covers the bytes)\n", status, body)
	if status != 401 {
		panic("FAILED")
	}

	// The classic self-inflicted bug: re-encoding the JSON before signing.
	// Identical MEANING, different BYTES (Go sorts map keys, drops spacing).
	var asMap map[string]any
	json.Unmarshal(raw, &asMap)
	reencoded, _ := json.Marshal(asMap)
	if bytes.Equal(reencoded, raw) {
		panic("FAILED: expected re-encoding to change the bytes")
	}
	status, body = deliver(reencoded, sign(secret, raw))
	fmt.Printf("body re-encoded          -> %d %s   (same JSON, different bytes: sign/verify RAW)\n", status, body)
	if status != 401 {
		panic("FAILED")
	}

	fmt.Printf("events actually processed: %v\n", processed)
	if len(processed) != 1 || processed[0] != "evt_1" {
		panic("FAILED")
	}
	fmt.Println("OK")
}
