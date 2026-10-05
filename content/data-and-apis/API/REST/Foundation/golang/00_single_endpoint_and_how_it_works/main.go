/*
FOUNDATION LEVEL 00 (start here) - A basic REST API endpoint, explained end to end
=====================================================================================
If someone says "build me a basic REST API endpoint", THIS is what they mean: one
server, one URL, a canned response. Nothing about JSON, routing, or databases yet -
just enough to see the whole request/response loop happen once, so every later
level is "add one more piece" instead of "understand everything at once".

THE MENTAL MODEL (read this before the code)

	A REST API is two separate programs talking over a network:
	  - the SERVER starts, then does nothing but wait for connections on one port
	  - the CLIENT (a browser, curl, another program) opens a connection, sends a
	    short request, and waits for a reply
	Nothing is remembered between requests - each one is a fresh, unrelated
	conversation. That is what "stateless" means (see ../../Theory.md).

You will learn
  - what "listening on a port" actually means: one program, one door, on this machine
  - what an "endpoint" is: a specific URL path this server has agreed to answer
  - the exact request/response loop: verb + path in -> status code + body out
  - why the SAME client code works whether it is curl, a browser, or another
    program calling this - the server does not know or care who is asking
  - that "no such endpoint" is a normal, handled outcome (404), not a crash

Run it         go run ./REST/Foundation/golang/00_single_endpoint_and_how_it_works
Keep serving   go run ./REST/Foundation/golang/00_single_endpoint_and_how_it_works -serve   (curl -i localhost:8080/ping)
*/
package main

import (
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
)

// pingHandler runs exactly once per incoming request that reaches it. By the
// time this function starts, net/http has already read the request off the
// network socket and parsed it into method / path / headers for you - that
// parsing step is what the bonus level (13) shows happening by hand, with
// nothing but raw bytes, once this feels easy.
func pingHandler(w http.ResponseWriter, r *http.Request) {
	// r.URL.Path is the exact URL path the client asked for, e.g. "/ping".
	// This handler is only ever registered for "/ping" (see main below), so
	// by the time we're here that check has already been made for us.
	w.Header().Set("Content-Type", "text/plain") // step 1: headers, before the status line is sent
	fmt.Fprint(w, "pong\n")                      // step 2: the body (net/http sends "200 OK" automatically
	//         the first time you write, unless you called WriteHeader yourself)
}

func main() {
	serve := flag.Bool("serve", false, "keep serving on :8080 instead of running the demo")
	flag.Parse()

	mux := http.NewServeMux()
	mux.HandleFunc("GET /ping", pingHandler) // this server agrees to answer exactly ONE path

	if *serve {
		log.Println("listening on http://localhost:8080  (try: curl -i localhost:8080/ping)")
		log.Fatal(http.ListenAndServe("127.0.0.1:8080", mux))
	}

	// port 0 = "operating system, hand me any free port" - so this demo never
	// collides with something else already listening on 8080 on your machine.
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, mux)
	base := "http://" + ln.Addr().String()

	// This IS "the client". curl, a browser's address bar, and this code all
	// do the exact same three things: open a connection, send a request, read
	// back a response. There is nothing special about any of them - they all
	// speak the same plain-text protocol.
	res, err := http.Get(base + "/ping")
	if err != nil {
		log.Fatal(err)
	}
	body, _ := io.ReadAll(res.Body)
	res.Body.Close()

	fmt.Printf("request  : GET %s/ping\n", base)
	fmt.Printf("response : %d %q\n", res.StatusCode, string(body))
	// 200 means "the server understood the request AND was able to fulfil it".
	if res.StatusCode != 200 || string(body) != "pong\n" {
		panic("FAILED")
	}

	// Now ask for a path this server never agreed to answer.
	res2, err := http.Get(base + "/does-not-exist")
	if err != nil {
		log.Fatal(err)
	}
	res2.Body.Close()
	fmt.Printf("request  : GET %s/does-not-exist\n", base)
	fmt.Printf("response : %d   (an endpoint this server never agreed to answer - not a crash)\n", res2.StatusCode)
	if res2.StatusCode != 404 {
		panic("FAILED")
	}
	fmt.Println("OK")
}
