/*
FOUNDATION LEVEL 00 (start here) - A basic webhook receiver, explained end to end
====================================================================================
If someone says "build me a basic webhook receiver", THIS is what they mean: one
server, one URL that accepts POST, and a 200 answer. Nothing about signatures,
retries, or queues yet - just enough to see one delivery arrive and be accepted,
so every later level is "add one more piece" instead of "understand everything
at once".

THE MENTAL MODEL (read this before the code)
A webhook is just you running a small REST server that someone else's system
calls into, unprompted. You never initiate the connection - you have no idea
when it will happen - you only have to be READY when it arrives:

  - you publish a URL once ("here is where to reach me")
  - their system POSTs a JSON event to it whenever something happens
  - you answer 200 as fast as you can, meaning "got it, it's mine now"

That is the whole reversal: in a normal API (../../REST/Foundation) you are the
client and they are the server. Here they are the client and YOU are the server.
Everything difficult about webhooks follows from that one flip.

You will learn
  - that a webhook receiver is an ordinary HTTP endpoint - no new protocol
  - why it is POST (a delivery carries a body and changes your state)
  - the exact loop: raw body in -> 200 out, immediately
  - that answering 200 is a PROMISE ("I have it"), not just politeness - the
    sender deletes its copy or stops retrying based on that number
  - that a path nobody registered is a normal, handled 404, not a crash

Run it        go run ./Webhooks/Foundation/golang/00_single_receiver_endpoint_and_how_it_works
Keep serving  go run ./Webhooks/Foundation/golang/00_single_receiver_endpoint_and_how_it_works -serve
*/
package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
)

const maxBody = 1_000_000 // never read an unbounded body off the network

func sendJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status) // the status line: the one number the sender acts on
	json.NewEncoder(w).Encode(payload)
}

// webhookHandler runs once per incoming delivery. net/http has already read the
// request line and headers off the socket for you - the one thing a webhook
// receiver must not let a library hide is the raw body bytes (levels 04, 13).
func webhookHandler(w http.ResponseWriter, r *http.Request) {
	// MaxBytesReader caps what we are willing to read, no matter what
	// Content-Length claimed.
	raw, err := io.ReadAll(http.MaxBytesReader(w, r.Body, maxBody))
	if err != nil {
		sendJSON(w, http.StatusBadRequest, map[string]string{"error": "could not read body"})
		return
	}

	// A real sender POSTs JSON. Later levels validate this properly (02) and
	// verify it really came from who it claims (04) - not yet.
	var event map[string]any
	json.Unmarshal(raw, &event)
	fmt.Printf("  [receiver] a delivery arrived, unprompted: %v\n", event)

	// 200 is the entire point of the exercise. To the sender it means
	// "delivered, stop worrying about this event".
	sendJSON(w, http.StatusOK, map[string]bool{"received": true})
}

func main() {
	serve := flag.Bool("serve", false, "keep serving on :8080 instead of running the demo")
	flag.Parse()

	mux := http.NewServeMux()
	// Go 1.22+ patterns: the method is part of the route, so a GET to this same
	// path is a 405 without any code of ours running.
	mux.HandleFunc("POST /webhook", webhookHandler)

	if *serve {
		log.Println("listening on http://localhost:8080/webhook")
		log.Println(`try: curl -i -X POST localhost:8080/webhook -d '{"type":"ping"}'`)
		log.Fatal(http.ListenAndServe("127.0.0.1:8080", mux))
	}

	// Port 0 = "operating system, hand me any free port" - so this demo never
	// collides with something already listening on 8080 on your machine.
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, mux)
	base := "http://" + ln.Addr().String()

	// This closure IS "their system". There is nothing special about a webhook
	// sender - it is any program that can make an HTTP POST.
	post := func(path, body string) (int, string) {
		res, err := http.Post(base+path, "application/json", bytes.NewBufferString(body))
		if err != nil {
			log.Fatal(err)
		}
		defer res.Body.Close()
		answer, _ := io.ReadAll(res.Body)
		return res.StatusCode, string(bytes.TrimSpace(answer))
	}

	status, body := post("/webhook", `{"type":"order.created","id":"evt_1"}`)
	fmt.Printf("POST /webhook -> %d %s\n", status, body)
	if status != 200 {
		panic("FAILED")
	}

	status, body = post("/not-registered", `{"type":"order.created"}`)
	fmt.Printf("POST /not-registered -> %d %q   (a path nobody registered - not a crash)\n", status, body)
	if status != 404 {
		panic("FAILED")
	}

	fmt.Println("OK")
}
