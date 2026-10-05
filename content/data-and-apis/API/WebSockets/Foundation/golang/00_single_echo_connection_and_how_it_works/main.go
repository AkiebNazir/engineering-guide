/*
FOUNDATION LEVEL 00 (start here) - A basic WebSocket endpoint, explained end to end
=====================================================================================
If someone says "build me a basic WebSocket endpoint", THIS is what they mean: one
server, one URL, and a connection that stays open and echoes whatever you say into
it. Nothing about protocols, rooms, or auth yet - just enough to watch one
connection be born, carry messages both ways, and die.

THE MENTAL MODEL (read this before the code)

	A WebSocket starts life as an ordinary HTTP GET with an "Upgrade: websocket"
	header. The server answers "101 Switching Protocols" and from that instant the
	same TCP connection stops being HTTP and becomes a two-way message pipe.

	THE CONTRAST WITH REST (../../../REST/Foundation) IS THE WHOLE POINT:
	  REST      : request -> response -> done. Ask again, and it is a brand new,
	              unrelated conversation. Nothing is remembered ("stateless").
	  WebSocket : handshake ONCE, then N messages in EITHER direction over that
	              one pipe. No URL, no verb, no headers, no status code per
	              message - all of that was negotiated a single time, up front.
	This file proves that literally: the server counts how many times Accept
	succeeds, we send three messages, and the count is still 1.

Notice that websocket.Accept takes an http.ResponseWriter and an *http.Request.
That is not an accident - a WebSocket endpoint IS a normal net/http handler, so
your existing mux and middleware keep working (level 08).

You will learn
  - what the upgrade handshake is, and that it happens exactly once per connection
  - that after the upgrade there are no more requests - only messages, both ways
  - the Go shape: one goroutine per CONNECTION (net/http gives you that for
    free), usually looping on c.Read until the peer goes away
  - that every Read and Write takes a context, because a blocked read on a
    persistent connection would otherwise wait forever
  - defer c.CloseNow() as the safety net that frees the connection on any path

Run it        go run ./WebSockets/Foundation/golang/00_single_echo_connection_and_how_it_works
Keep serving  go run ./WebSockets/Foundation/golang/00_single_echo_connection_and_how_it_works -serve
Then          npx wscat -c ws://localhost:8080/ws   (and type something)
*/
package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"net"
	"net/http"
	"sync/atomic"
	"time"

	"github.com/coder/websocket"
)

// Incremented once per ACCEPTED CONNECTION, not once per message. The demo
// asserts this stays at 1 while three messages fly back and forth - that
// single number is the difference between WebSockets and REST.
var handshakes atomic.Int64

func echoHandler(w http.ResponseWriter, r *http.Request) {
	// Accept performs the server half of the handshake: it validates the
	// upgrade headers and writes the 101 response. Everything before this line
	// is plain HTTP; everything after it is WebSocket.
	c, err := websocket.Accept(w, r, nil)
	if err != nil {
		return // Accept already wrote an HTTP error response for us
	}
	// CloseNow is the safety net: it releases the connection on every return
	// path, including panics. A clean close is a separate, deliberate act.
	defer c.CloseNow()

	handshakes.Add(1)
	fmt.Printf("  [server] connection opened (handler entered, path=%s)\n", r.URL.Path)

	for {
		// Every Read needs a context. Without one, a connection whose peer
		// went silent would pin this goroutine forever - a leak that does not
		// exist in REST, where a request always ends.
		ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
		msgType, data, err := c.Read(ctx)
		cancel()
		if err != nil {
			// The normal way out: the peer closed, or the context expired.
			// CloseStatus(err) tells you the code, or -1 if there was none.
			fmt.Printf("  [server] connection closed (status %d), handler returns\n",
				websocket.CloseStatus(err))
			return
		}

		// Each loop turn is NOT a new request - nothing is re-parsed,
		// re-routed or re-authenticated. That work happened once, in Accept.
		fmt.Printf("  [server] received %q -> sending it straight back\n", data)
		wctx, wcancel := context.WithTimeout(r.Context(), 5*time.Second)
		err = c.Write(wctx, msgType, []byte("echo: "+string(data)))
		wcancel()
		if err != nil {
			return
		}
	}
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func demo(base string) {
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	url := base + "/ws"

	// Dial performs the HTTP GET + Upgrade, waits for 101, and hands back an
	// open pipe. This one call is the entire "handshake" cost, paid once.
	c, resp, err := websocket.Dial(ctx, url, nil)
	must(err == nil, fmt.Sprint(err))
	defer c.CloseNow()
	fmt.Printf("client   : connected to %s (HTTP %s)\n", url, resp.Status)
	must(resp.StatusCode == http.StatusSwitchingProtocols, "expected 101")

	send := func(text string) string {
		must(c.Write(ctx, websocket.MessageText, []byte(text)) == nil, "write")
		_, data, err := c.Read(ctx)
		must(err == nil, fmt.Sprint(err))
		return string(data)
	}

	reply := send("hello")
	fmt.Printf("client   : sent %q  -> got %q\n", "hello", reply)
	must(reply == "echo: hello", "echo")

	// Two more round trips on the SAME connection. No new handshake, no new
	// URL, no new headers. This is what "persistent" buys you.
	for _, text := range []string{"again", "and again"} {
		got := send(text)
		fmt.Printf("client   : sent %q -> got %q\n", text, got)
		must(got == "echo: "+text, "echo")
	}

	// Closing is explicit and carries a code. 1000 = normal closure.
	// Close (unlike CloseNow) sends a close frame and waits for the peer's.
	must(c.Close(websocket.StatusNormalClosure, "done") == nil, "close")
	fmt.Println("client   : closed cleanly with 1000")

	// THE PROOF: three messages, one handshake.
	fmt.Printf("handshakes on the server for 3 messages: %d"+
		"   (REST would have needed 3 separate requests)\n", handshakes.Load())
	must(handshakes.Load() == 1, "exactly one handshake")

	// A path this server never registered. In Go the mux answers FIRST, with
	// an ordinary HTTP 404, so the upgrade never happens at all and Dial
	// itself fails - there is no WebSocket to close.
	_, resp, err = websocket.Dial(ctx, base+"/nope", nil)
	must(err != nil, "expected the dial to fail")
	must(resp != nil && resp.StatusCode == http.StatusNotFound, "expected a 404")
	fmt.Printf("client   : /nope -> HTTP %d, no upgrade, no WebSocket "+
		"(a handled outcome, not a crash)\n", resp.StatusCode)

	fmt.Println("OK")
}

func main() {
	serve := flag.Bool("serve", false, "listen on :8080 instead of running the demo")
	flag.Parse()

	mux := http.NewServeMux()
	mux.HandleFunc("/ws", echoHandler) // a WebSocket route is just an http route

	if *serve {
		fmt.Println("listening on ws://localhost:8080/ws  (try: npx wscat -c ws://localhost:8080/ws)")
		log.Fatal(http.ListenAndServe("127.0.0.1:8080", mux))
	}

	// port 0 = "OS, hand me any free port", so this demo never collides with
	// something already listening on your machine.
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, mux)
	demo("http://" + ln.Addr().String())
}
