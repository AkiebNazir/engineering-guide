/*
FOUNDATION LEVEL 01 - The event envelope, and routing by type
=================================================================
Level 00 accepted any JSON at one URL. Real senders deliver EVERY kind of event
to that same URL, wrapped in a small, boring, predictable envelope:

	{"type": "order.created", "id": "evt_1", "data": {...}}
	 ^ what happened          ^ which        ^ the payload
	                           delivery it is

So a webhook receiver does not route on the URL path the way a REST API does
(../../REST/Foundation level 01) - one path handles everything. It routes on the
"type" FIELD INSIDE the body. That is webhooks' routing equivalent.

You will learn
  - the envelope/payload split: the outer fields are metadata every event has,
    "data" is the part that differs per type
  - dispatch = a lookup table from event type -> handler function
  - json.RawMessage: decode the envelope now, leave "data" as bytes until the
    handler that knows its shape can decode it into a real struct
  - why an UNKNOWN type must still be answered 200 and ignored: the sender will
    add new event types without asking you, and a non-2xx makes it retry
    forever for an event you were never going to care about

Run it   go run ./Webhooks/Foundation/golang/01_event_envelope_and_routing_by_type
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
)

// Envelope is the part of EVERY event that looks the same. Data stays raw until
// a handler that knows this type's shape decodes it.
type Envelope struct {
	Type string          `json:"type"`
	ID   string          `json:"id"`
	Data json.RawMessage `json:"data"`
}

type orderData struct {
	OrderID string `json:"order_id"`
}

type result struct {
	Handled bool   `json:"handled"`
	Reason  string `json:"reason,omitempty"`
}

// What each handler actually did, so the demo can prove the right one ran.
var effects []string

// ---- one handler per event type. Each one only knows about its own data. ----
func onOrderCreated(e Envelope) {
	var d orderData
	json.Unmarshal(e.Data, &d)
	effects = append(effects, "reserved stock for order "+d.OrderID)
}

func onOrderCancelled(e Envelope) {
	var d orderData
	json.Unmarshal(e.Data, &d)
	effects = append(effects, "released stock for order "+d.OrderID)
}

// The dispatch table IS the router. Adding an event type means adding one line
// here - not a new URL, not a new endpoint.
var handlers = map[string]func(Envelope){
	"order.created":   onOrderCreated,
	"order.cancelled": onOrderCancelled,
}

func dispatch(e Envelope) result {
	handler, known := handlers[e.Type]
	if !known {
		// NOT an error. The sender is allowed to invent new event types at any
		// time; "I don't handle that one" is a successful, final outcome.
		return result{Handled: false, Reason: "unsubscribed event type"}
	}
	handler(e)
	return result{Handled: true}
}

func sendJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(payload)
}

func webhookHandler(w http.ResponseWriter, r *http.Request) {
	raw, _ := io.ReadAll(http.MaxBytesReader(w, r.Body, 1_000_000))
	var e Envelope
	json.Unmarshal(raw, &e)

	res := dispatch(e)
	fmt.Printf("  [receiver] type=%-16s id=%-7s -> handled=%v %s\n", e.Type, e.ID, res.Handled, res.Reason)
	// Both outcomes are 200: "this delivery is finished, never send it again".
	sendJSON(w, http.StatusOK, res)
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

	deliver := func(body string) (int, result) {
		res, err := http.Post(base+"/webhook", "application/json", bytes.NewBufferString(body))
		if err != nil {
			log.Fatal(err)
		}
		defer res.Body.Close()
		var parsed result
		json.NewDecoder(res.Body).Decode(&parsed)
		return res.StatusCode, parsed
	}

	status, body := deliver(`{"type":"order.created","id":"evt_1","data":{"order_id":"A-1"}}`)
	fmt.Printf("order.created      -> %d %+v\n", status, body)
	if status != 200 || !body.Handled {
		panic("FAILED")
	}

	status, body = deliver(`{"type":"order.cancelled","id":"evt_2","data":{"order_id":"A-1"}}`)
	fmt.Printf("order.cancelled    -> %d %+v\n", status, body)
	if status != 200 || !body.Handled {
		panic("FAILED")
	}

	status, body = deliver(`{"type":"order.gift_wrapped","id":"evt_3","data":{}}`)
	fmt.Printf("order.gift_wrapped -> %d %+v   (a type we never subscribed to: ACK it, ignore it)\n", status, body)
	if status != 200 || body.Handled {
		panic("FAILED")
	}

	fmt.Printf("effects in order: %v\n", effects)
	if len(effects) != 2 || effects[0] != "reserved stock for order A-1" || effects[1] != "released stock for order A-1" {
		panic("FAILED")
	}
	fmt.Println("OK")
}
