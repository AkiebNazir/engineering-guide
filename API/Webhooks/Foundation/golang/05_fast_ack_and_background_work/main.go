/*
FOUNDATION LEVEL 05 - The fast ACK: answer now, work later
==============================================================
Senders give you a few seconds - Stripe and GitHub give about 10, some give 5 -
and then they hang up and call the delivery failed. They do not know your
handler was still busy resizing a video; silence looks exactly like being down.

So a receiver that does its real work INSIDE the handler is not merely slow, it
is incorrect: the sender times out, retries, and now the same event is being
processed twice at once. That is the duplicate storm level 03 was defending
against - and the cheapest way to stop causing it is to stop being slow.

The pattern, in two lines of responsibility:

	handler:  validate -> store/enqueue (cheap, durable) -> 202, done
	worker:   pick it up in the background -> do the slow, failable part

Your 2xx means "I have accepted responsibility for this event", NOT "the work
is finished". Those are different promises, and only the first one is fast.

You will learn
  - how a sender-side timeout actually looks (and that it causes a retry, so
    the slow handler gets you duplicate WORK, not just a scary log line)
  - the enqueue-then-ACK split, with a buffered channel and a worker goroutine
  - 202 Accepted as the honest status code for "queued, not finished"
  - that the handler goroutine keeps running after the sender gives up: the work
    is not cancelled, its result is simply thrown away
  - the durability catch: an in-memory channel loses events if the process dies,
    which is why real receivers enqueue into a database or broker first
    (see ../../labs/golang/03_delivery_worker_pool)

Run it   go run ./Webhooks/Foundation/golang/05_fast_ack_and_background_work
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
	"time"
)

const (
	senderTimeout = 250 * time.Millisecond // our pretend sender gives up after 250ms
	slowWork      = 600 * time.Millisecond // the real work takes longer than that
)

type Envelope struct {
	Type string `json:"type"`
	ID   string `json:"id"`
}

var (
	queue = make(chan Envelope, 100) // the hand-off: bounded on purpose

	mu              sync.Mutex
	slowHandlerRuns []string // every time the SLOW endpoint did the work inline
	backgroundRuns  []string // every time the BACKGROUND worker did it
	queueWork       sync.WaitGroup
	inlineWork      sync.WaitGroup
)

func doTheSlowWork(id string, into *[]string) {
	time.Sleep(slowWork)
	mu.Lock()
	*into = append(*into, id)
	mu.Unlock()
}

func worker() {
	for event := range queue {
		doTheSlowWork(event.ID, &backgroundRuns)
		queueWork.Done()
	}
}

func sendJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(payload)
}

// slowHandler is THE ANTI-PATTERN. The work happens before the response, so the
// response cannot possibly arrive before the work is finished.
func slowHandler(w http.ResponseWriter, r *http.Request) {
	raw, _ := io.ReadAll(r.Body)
	var event Envelope
	json.Unmarshal(raw, &event)

	inlineWork.Add(1)
	defer inlineWork.Done()
	doTheSlowWork(event.ID, &slowHandlerRuns)

	// By now the sender has usually hung up. This write goes nowhere, which is
	// exactly what a delivery timeout feels like from inside the receiver.
	sendJSON(w, http.StatusOK, map[string]string{"status": "finished the work inline"})
}

// fastAckHandler does only the cheap, durable thing: hand it off, then answer.
func fastAckHandler(w http.ResponseWriter, r *http.Request) {
	raw, _ := io.ReadAll(r.Body)
	var event Envelope
	json.Unmarshal(raw, &event)

	queueWork.Add(1)
	queue <- event
	sendJSON(w, http.StatusAccepted, map[string]string{"status": "queued", "id": event.ID})
}

func main() {
	go worker()

	mux := http.NewServeMux()
	mux.HandleFunc("POST /slow", slowHandler)
	mux.HandleFunc("POST /fast-ack", fastAckHandler)

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, mux)
	base := "http://" + ln.Addr().String()

	// A sender with a real timeout, like every provider has.
	client := &http.Client{Timeout: senderTimeout}
	deliver := func(path string) (int, time.Duration) {
		started := time.Now()
		res, err := client.Post(base+path, "application/json",
			bytes.NewBufferString(`{"type":"video.uploaded","id":"evt_1"}`))
		if err != nil {
			return 0, time.Since(started) // 0 = no answer in time
		}
		defer res.Body.Close()
		io.ReadAll(res.Body)
		return res.StatusCode, time.Since(started)
	}

	// --- the anti-pattern: the sender gives up, then retries ---
	status, elapsed := deliver("/slow")
	fmt.Printf("POST /slow     -> timed out after %v (no status at all: %d)\n", elapsed.Round(time.Millisecond), status)
	if status != 0 {
		panic("FAILED: expected a client timeout")
	}
	status, _ = deliver("/slow") // the retry any sender would make
	fmt.Println("POST /slow     -> timed out again; the work has now run TWICE for one event")
	if status != 0 {
		panic("FAILED")
	}

	// --- the pattern: ACK first, work in the background ---
	status, elapsed = deliver("/fast-ack")
	fmt.Printf("POST /fast-ack -> %d in %v   (202 = accepted, not finished)\n", status, elapsed.Round(time.Millisecond))
	if status != http.StatusAccepted || elapsed >= senderTimeout {
		panic("FAILED: the ACK must be far faster than the sender's timeout")
	}

	queueWork.Wait()  // let the background worker finish, purely so we can assert
	inlineWork.Wait() // and let the two abandoned /slow handlers finish too

	mu.Lock()
	defer mu.Unlock()
	fmt.Printf("slow-handler runs: %d   (one event, processed twice - duplicate work)\n", len(slowHandlerRuns))
	fmt.Printf("background worker runs: %d   (one event, processed once)\n", len(backgroundRuns))
	if len(slowHandlerRuns) != 2 || len(backgroundRuns) != 1 {
		panic("FAILED")
	}
	fmt.Println("OK")
}
