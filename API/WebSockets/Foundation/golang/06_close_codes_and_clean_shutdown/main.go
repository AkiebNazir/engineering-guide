/*
FOUNDATION LEVEL 06 - Close codes: the vocabulary for ENDING a conversation
===============================================================================
REST has status codes to describe one answer. WebSockets has close codes to
describe one ending. They are not the same tool: a status code says "here is
what happened to your request", a close code says "here is why this whole
relationship is over". A long-lived connection needs that second vocabulary,
because "goodbye" can mean a dozen different things.

A clean close is a HANDSHAKE, not a hang-up: one side sends a Close frame with
a code and a reason, the other echoes a Close frame back, and only then does
the TCP connection drop. That is why the client below can read the code the
server chose - the close was a message, and messages carry data.

	c.Close(code, reason)  sends a close frame and WAITS for the peer's reply
	c.CloseNow()           drops the TCP connection immediately, no frame

You will learn
  - the codes that matter in practice: StatusNormalClosure 1000, StatusGoingAway
    1001, StatusUnsupportedData 1003, StatusPolicyViolation 1008,
    StatusMessageTooBig 1009, StatusInternalError 1011
  - websocket.CloseStatus(err) is how you read the peer's code; it returns -1
    when the error was not a close at all
  - that 1005 and 1006 are NEVER sent on the wire - they are local placeholders
    meaning "no code given" and "the connection died without a close frame",
    and that coder/websocket refuses to invent them: it returns -1 instead
  - the difference between Close (polite, mutual) and CloseNow (an abort)
  - the 4000-4999 range, which is yours: application-specific close codes

Run it   go run ./WebSockets/Foundation/golang/06_close_codes_and_clean_shutdown
*/
package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"net/http"
	"time"

	"github.com/coder/websocket"
)

// The reason string is capped at 123 bytes by the protocol - it is a hint for
// a human reading logs, never a place to put structured data.
type closer struct {
	trigger string
	code    websocket.StatusCode
	reason  string
}

var closers = []closer{
	{"bye", websocket.StatusNormalClosure, "normal closure - we are done, nothing is wrong"},
	{"shutdown", websocket.StatusGoingAway, "going away - server is restarting"},
	{"binary", websocket.StatusUnsupportedData, "unsupported data - this endpoint only accepts text"},
	{"rude", websocket.StatusPolicyViolation, "policy violation - you broke a rule of this service"},
	{"huge", websocket.StatusMessageTooBig, "message too big"},
	{"crash", websocket.StatusInternalError, "internal error - our bug, not yours"},
	{"custom", websocket.StatusCode(4001), "app-specific: your subscription expired"},
}

func closingHandler(w http.ResponseWriter, r *http.Request) {
	c, err := websocket.Accept(w, r, nil)
	if err != nil {
		return
	}
	defer c.CloseNow()

	for {
		ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
		_, data, err := c.Read(ctx)
		cancel()
		if err != nil {
			return
		}
		text := string(data)

		if text == "abort" {
			// The opposite of clean: rip the TCP connection away with no Close
			// frame at all. The peer cannot learn a code, so it reports 1006.
			// Real causes: a crashed process, dropped wifi, a killed pod.
			c.CloseNow()
			return
		}

		matched := false
		for _, cl := range closers {
			if cl.trigger == text {
				// Close sends a close frame and WAITS for the peer's close
				// frame back. That round trip is what makes it "clean".
				c.Close(cl.code, cl.reason)
				matched = true
				break
			}
		}
		if matched {
			return
		}

		wctx, wcancel := context.WithTimeout(r.Context(), 5*time.Second)
		err = c.Write(wctx, websocket.MessageText, []byte("echo: "+text))
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

func demo(url string) {
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()

	dial := func() *websocket.Conn {
		c, _, err := websocket.Dial(ctx, url, nil)
		must(err == nil, fmt.Sprint(err))
		return c
	}

	fmt.Println("== every close code is a deliberate statement about why we are done ==")
	for _, cl := range closers {
		c := dial()
		must(c.Write(ctx, websocket.MessageText, []byte(cl.trigger)) == nil, "write")

		// The close arrives as an ERROR from Read. That is not a failure of
		// your code - it is how a stream-shaped API reports "the stream ended".
		_, _, err := c.Read(ctx)
		must(err != nil, "expected the server to close")

		got := websocket.CloseStatus(err)
		fmt.Printf("  %-9s -> %d  %q\n", cl.trigger, got, cl.reason)
		must(got == cl.code, fmt.Sprintf("%s: got %d want %d", cl.trigger, got, cl.code))
		c.CloseNow()
	}

	fmt.Println("\n== a clean close is mutual: both sides agree on the code ==")
	c := dial()
	must(c.Write(ctx, websocket.MessageText, []byte("ping")) == nil, "write")
	_, data, err := c.Read(ctx)
	must(err == nil && string(data) == "echo: ping", "echo")
	// This time the CLIENT initiates. The server's Read returns an error, its
	// handler returns, and the close handshake completes.
	must(c.Close(websocket.StatusNormalClosure, "client is done") == nil, "close")
	fmt.Println("  client-initiated Close returned with no error -> the peer replied")

	fmt.Println("\n== no close frame at all: the connection just vanished ==")
	c = dial()
	must(c.Write(ctx, websocket.MessageText, []byte("abort")) == nil, "write")
	_, _, err = c.Read(ctx)
	must(err != nil, "expected a failure")
	got := websocket.CloseStatus(err)
	fmt.Printf("  aborted connection -> CloseStatus(err) = %d, err = %v\n", got, err)
	// A real library difference worth knowing. Some stacks (Python's
	// `websockets`, browsers) invent the placeholder code 1006
	// "abnormal closure" here. coder/websocket does not pretend: there was no
	// close frame, so there is no code, and CloseStatus returns -1 - the same
	// value it returns for any error that was not a close. So in Go you must
	// treat "-1" as "the peer vanished or something else broke", and read the
	// underlying error if you need to tell those apart.
	must(got == -1, "expected -1: no close frame was ever sent")
	fmt.Println("  -1 means \"no close frame\": Go declines to invent the 1006")
	fmt.Println("  placeholder that browsers and some libraries report here.")
	fmt.Println("  Either way the meaning is the same, and it is the case")
	fmt.Println("  level 07's keepalive exists to detect.")
	c.CloseNow()

	fmt.Println("\nOK")
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, http.HandlerFunc(closingHandler))
	demo("ws://" + ln.Addr().String())
}
