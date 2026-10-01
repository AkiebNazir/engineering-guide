/*
FOUNDATION LEVEL 03 - Idempotency: the same event WILL arrive twice
=======================================================================
This is the defining webhook problem. Not a rare edge case, not bad luck: every
serious sender promises AT-LEAST-ONCE delivery, which is a polite way of saying
"we will sometimes send you the same event more than once, on purpose".

It happens because the sender cannot tell these two situations apart: you never
got the event (must retry), and you got it, processed it, and your 200 was lost
or too slow (must not retry - but it will). Faced with silence, the only safe
thing a sender can do is retry. So the only safe thing YOU can do is make a
repeat delivery harmless.

The fix is one idea: every event carries a stable id that is the SAME across
redeliveries. Remember the ids you have finished, and short-circuit the rest.
"Only process it once" is your job, not the sender's.

You will learn
  - at-least-once delivery, and why exactly-once delivery does not exist
  - dedupe on the EVENT id (stable across retries), never on the delivery id
    (new for every attempt - see level 07)
  - a duplicate must still answer 200: it IS delivered, you already have it
  - the check-and-mark must be ATOMIC - one mutex here, a UNIQUE constraint in
    a real database (see ../../labs/golang/03_delivery_worker_pool)
  - that this is why level 05's fast ACK matters: slow handlers cause the very
    timeouts that produce the duplicates

Run it   go run ./Webhooks/Foundation/golang/03_idempotency_deduplicating_redeliveries
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
	"sync"
)

type Envelope struct {
	Type string `json:"type"`
	ID   string `json:"id"`
	Data struct {
		OrderID string `json:"order_id"`
	} `json:"data"`
}

var (
	mu          sync.Mutex
	seenIDs     = map[string]bool{} // in a real receiver: a table with UNIQUE(event_id)
	sideEffects []string            // the thing that must happen exactly once
)

// claim reports whether THIS call is the first to claim the id. The check and
// the insert happen under one lock, so two concurrent redeliveries of the same
// event cannot both win. A check-then-insert without the lock has a race.
func claim(eventID string) bool {
	mu.Lock()
	defer mu.Unlock()
	if seenIDs[eventID] {
		return false
	}
	seenIDs[eventID] = true
	return true
}

// process pretends to charge a card / ship a box / send an email - something
// you would very much like not to do twice.
func process(e Envelope) {
	mu.Lock()
	defer mu.Unlock()
	sideEffects = append(sideEffects, "emailed receipt for "+e.Data.OrderID)
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

	if !claim(e.ID) {
		fmt.Printf("  [receiver] id=%s seen before -> skipping the work, still answering 200\n", e.ID)
		sendJSON(w, http.StatusOK, map[string]string{"status": "duplicate", "id": e.ID})
		return
	}

	process(e)
	fmt.Printf("  [receiver] id=%s is new -> processed\n", e.ID)
	sendJSON(w, http.StatusOK, map[string]string{"status": "processed", "id": e.ID})
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

	deliver := func(body string) (int, map[string]string) {
		res, err := http.Post(base+"/webhook", "application/json", bytes.NewBufferString(body))
		if err != nil {
			log.Fatal(err)
		}
		defer res.Body.Close()
		var parsed map[string]string
		json.NewDecoder(res.Body).Decode(&parsed)
		return res.StatusCode, parsed
	}

	event := `{"type":"order.paid","id":"evt_7","data":{"order_id":"A-1"}}`

	status, body := deliver(event)
	fmt.Printf("delivery 1 of evt_7 -> %d %v\n", status, body)
	if body["status"] != "processed" {
		panic("FAILED")
	}

	// The sender's retry: byte-for-byte the same event, because from its point
	// of view the first attempt might never have landed.
	status, body = deliver(event)
	fmt.Printf("delivery 2 of evt_7 -> %d %v   (same id: accepted, but NOT processed again)\n", status, body)
	if status != 200 || body["status"] != "duplicate" {
		panic("FAILED")
	}

	status, body = deliver(`{"type":"order.paid","id":"evt_8","data":{"order_id":"A-2"}}`)
	fmt.Printf("delivery 1 of evt_8 -> %d %v\n", status, body)
	if body["status"] != "processed" {
		panic("FAILED")
	}

	// Now the hard case: 12 redeliveries of one event, all at the same instant.
	var wg sync.WaitGroup
	for range 12 {
		wg.Add(1)
		go func() {
			defer wg.Done()
			deliver(`{"type":"order.paid","id":"evt_9","data":{"order_id":"A-3"}}`)
		}()
	}
	wg.Wait()

	mu.Lock()
	defer mu.Unlock()
	fmt.Printf("3 distinct events, 15 deliveries -> side effects: %v\n", sideEffects)
	if len(sideEffects) != 3 {
		panic("FAILED: an event was processed more than once")
	}
	fmt.Println("OK")
}
