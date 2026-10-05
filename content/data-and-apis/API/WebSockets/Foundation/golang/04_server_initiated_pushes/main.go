/*
FOUNDATION LEVEL 04 - The server speaks first: unsolicited pushes
=====================================================================
Level 03's broadcast was still triggered by a client message. This level
removes even that. Here the server sends messages that NO client asked for,
on a timer, driven entirely by something happening on the server side.

This is the capability REST fundamentally lacks. With HTTP, a server can only
ever answer; if it has news, it must wait to be asked (polling) or hold a
request open (long polling). With a WebSocket, the connection is already open
in both directions, so the server just... writes.

You will learn
  - a connection handler can run a background goroutine that WRITES while the
    main loop READS - full duplex means genuinely simultaneous, not taking turns
  - a goroutine + a cancelled context: the standard way to own a
    per-connection background job without leaking it when the client leaves
  - that the client must be built to accept messages at any time (a Read loop),
    not to expect one reply per write
  - why this replaces polling entirely: the client stops asking "anything
    new?" and the server stops answering "no" thousands of times
  - an important footgun: two goroutines writing to one connection need a
    mutex, because a Write must not be interleaved with another Write

Run it   go run ./WebSockets/Foundation/golang/04_server_initiated_pushes
*/
package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"net/http"
	"sync"
	"time"

	"github.com/coder/websocket"
	"github.com/coder/websocket/wsjson"
)

const tickInterval = 50 * time.Millisecond // tiny for a fast demo; real: 1-30s

type message struct {
	Type    string `json:"type"`
	Payload any    `json:"payload"`
}

// safeConn serialises writes. Two goroutines (the ticker and the reply path)
// both write to one connection here, and coder/websocket only permits one
// Write at a time - without this mutex you would corrupt the message stream.
type safeConn struct {
	mu sync.Mutex
	c  *websocket.Conn
}

func (s *safeConn) send(ctx context.Context, m message) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	wctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	return wsjson.Write(wctx, s.c, m)
}

// ticker pushes a message every tickInterval forever. Nothing here reads from
// the client. It is purely the server having news and delivering it - a
// metrics update, a price change, a job finishing.
func ticker(ctx context.Context, conn *safeConn) {
	n := 0
	for {
		select {
		case <-ctx.Done():
			return // the client left; stop writing into a dead connection
		case <-time.After(tickInterval):
			n++
			if err := conn.send(ctx, message{Type: "tick", Payload: n}); err != nil {
				return
			}
		}
	}
}

func pushHandler(w http.ResponseWriter, r *http.Request) {
	c, err := websocket.Accept(w, r, nil)
	if err != nil {
		return
	}
	defer c.CloseNow()

	conn := &safeConn{c: c}

	// Cancelling this context is what stops the ticker. `defer cancel()` is
	// the whole leak-prevention story.
	ctx, cancel := context.WithCancel(r.Context())
	defer cancel()

	// Start pushing IMMEDIATELY, before the client has said a single word.
	go ticker(ctx, conn)

	for {
		// Meanwhile the same handler still reads. Reading and writing happen
		// at the same time on the same connection: that is "full duplex".
		rctx, rcancel := context.WithTimeout(ctx, 10*time.Second)
		var in message
		err := wsjson.Read(rctx, c, &in)
		rcancel()
		if err != nil {
			return
		}
		// Pretend answering takes real work (a database call, say). The ticker
		// keeps pushing throughout - which is exactly the situation the client
		// below must be written to survive.
		time.Sleep(tickInterval * 5 / 2)
		if err := conn.send(ctx, message{Type: "pong", Payload: in.Payload}); err != nil {
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

	c, _, err := websocket.Dial(ctx, url, nil)
	must(err == nil, fmt.Sprint(err))
	defer c.CloseNow()

	fmt.Println("== the client connects and then says NOTHING ==")
	for want := 1; want <= 3; want++ {
		var m message
		must(wsjson.Read(ctx, c, &m) == nil, "read")
		fmt.Printf("  <- pushed by the server, unrequested: {%s %v}\n", m.Type, m.Payload)
		// We wrote zero messages and received three. REST cannot produce this.
		must(m.Type == "tick" && m.Payload == float64(want), "tick")
	}

	fmt.Println("\n== pushes keep arriving WHILE the client does its own asking ==")
	must(wsjson.Write(ctx, c, message{Type: "ping", Payload: "are you there"}) == nil, "write")

	// The crucial client-side lesson: the next message off the pipe might be
	// our answer, or it might be another tick. A WebSocket client must be
	// written as an event loop ("handle whatever arrives"), never as "write,
	// then assume the next message is my reply".
	sawPong := false
	moreTicks := 0
	for i := 0; i < 8; i++ {
		var m message
		must(wsjson.Read(ctx, c, &m) == nil, "read")
		if m.Type == "pong" {
			fmt.Printf("  <- our own answer arrived: {%s %v}\n", m.Type, m.Payload)
			sawPong = true
			break
		}
		moreTicks++
		fmt.Printf("  <- another unrequested tick while we waited: {%s %v}\n", m.Type, m.Payload)
	}
	must(sawPong, "the reply to our ping should have arrived")
	fmt.Printf("  (ticks that interleaved before our reply: %d)\n", moreTicks)
	// If this were REST, nothing could possibly have arrived between our
	// request and its response. Here, things did.
	must(moreTicks >= 1, "a tick should have arrived before the pong")

	must(c.Close(websocket.StatusNormalClosure, "done") == nil, "close")
	fmt.Println("\nOK")
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, http.HandlerFunc(pushHandler))
	demo("ws://" + ln.Addr().String())
}
