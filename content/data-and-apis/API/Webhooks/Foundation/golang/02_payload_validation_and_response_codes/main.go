/*
FOUNDATION LEVEL 02 - Validating the payload, and choosing the right status code
===================================================================================
Levels 00-01 trusted the body: json.Unmarshal into a struct and straight on to
e.Type without looking. A webhook URL is PUBLIC - anything on the internet can
POST garbage to it, and even the real sender ships bugs. An unhandled failure
here is not just a 500: it is a 500 the sender will retry, again and again.

The one rule for a receiver: never leave the sender hanging. Answer fast, and be
unambiguous about accepted vs rejected. The status code is the ONLY thing the
sender understands (level 06 shows exactly what it does with each one).

You will learn
  - bound the body first (Content-Length is a claim, not a guarantee) -> 413
  - malformed JSON and a missing envelope field are BAD REQUESTS -> 400, because
    no amount of retrying will ever make those same bytes valid
  - an event you cannot handle YET (your database is down) is the opposite:
    -> 500, please retry me, this is my fault and it is temporary
  - why json.Unmarshal into a struct is not validation: missing fields become
    zero values silently, so you must check them yourself
  - validate the ENVELOPE (type, id) and the per-type data separately

Run it   go run ./Webhooks/Foundation/golang/02_payload_validation_and_response_codes
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
	"strings"
)

const maxBody = 10_000 // deliberately small so the demo can trip it

type Envelope struct {
	Type string          `json:"type"`
	ID   string          `json:"id"`
	Data json.RawMessage `json:"data"`
}

type orderData struct {
	OrderID string `json:"order_id"`
}

// validate is a pure function: no network, no writing - easy to unit test alone.
// It returns the reason a delivery is unusable, or "" when it is fine.
func validate(raw []byte) (Envelope, string) {
	var e Envelope
	if err := json.Unmarshal(raw, &e); err != nil {
		return e, "body is not valid JSON: " + err.Error()
	}
	if e.Type == "" {
		return e, "envelope field 'type' must be a non-empty string"
	}
	if e.ID == "" {
		return e, "envelope field 'id' must be a non-empty string"
	}
	return e, ""
}

func sendJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(payload)
}

func webhookHandler(w http.ResponseWriter, r *http.Request) {
	// MaxBytesReader is the guard: it fails the read once the body exceeds the
	// cap, whatever Content-Length claimed, so nobody can make us allocate 2GB.
	raw, err := io.ReadAll(http.MaxBytesReader(w, r.Body, maxBody))
	if err != nil {
		// 413 tells the sender "permanently too big" - retrying cannot help.
		sendJSON(w, http.StatusRequestEntityTooLarge,
			map[string]string{"error": fmt.Sprintf("payload larger than %d bytes", maxBody)})
		return
	}

	event, reason := validate(raw)
	if reason != "" {
		// 400 = "this delivery is permanently unusable, do not retry it".
		sendJSON(w, http.StatusBadRequest, map[string]string{"error": reason})
		return
	}

	if event.Type == "order.created" {
		var d orderData
		if json.Unmarshal(event.Data, &d) != nil || d.OrderID == "" {
			// Envelope was fine, the per-type payload was not. Still a 400.
			sendJSON(w, http.StatusBadRequest, map[string]string{"error": "order.created requires data.order_id"})
			return
		}
	}

	if event.Type == "order.exploded" {
		// A stand-in for "my database is down right now". This is OUR problem
		// and it is temporary, so we ask to be retried: 500.
		sendJSON(w, http.StatusInternalServerError,
			map[string]string{"error": "temporarily unable to process, please retry"})
		return
	}

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

	deliver := func(body string) (int, string) {
		res, err := http.Post(base+"/webhook", "application/json", bytes.NewBufferString(body))
		if err != nil {
			log.Fatal(err)
		}
		defer res.Body.Close()
		answer, _ := io.ReadAll(res.Body)
		return res.StatusCode, strings.TrimSpace(string(answer))
	}

	meaning := map[int]string{200: "accepted", 400: "never retry", 413: "never retry", 500: "please retry"}
	cases := []struct {
		label string
		body  string
		want  int
	}{
		{"valid event", `{"type":"order.created","id":"evt_1","data":{"order_id":"A-1"}}`, 200},
		{"not JSON at all", `<html>oops</html>`, 400},
		{"JSON, but not an object", `["order.created"]`, 400},
		{"envelope missing id", `{"type":"order.created","data":{}}`, 400},
		{"per-type data missing", `{"type":"order.created","id":"evt_2","data":{}}`, 400},
		{"oversized body", `{"type":"order.created","id":"evt_3","data":{"pad":"` + strings.Repeat("x", maxBody) + `"}}`, 413},
		{"our side is broken", `{"type":"order.exploded","id":"evt_4","data":{}}`, 500},
	}
	for _, c := range cases {
		status, body := deliver(c.body)
		fmt.Printf("%-24s -> %d (%s) %s\n", c.label, status, meaning[status], body)
		if status != c.want {
			panic("FAILED: " + c.label)
		}
	}

	// The crucial property: not one of those answered slowly, hung, or crashed
	// the receiver. The next delivery still works.
	if status, _ := deliver(`{"type":"order.created","id":"evt_9","data":{"order_id":"A-9"}}`); status != 200 {
		panic("FAILED")
	}
	fmt.Println("OK")
}
