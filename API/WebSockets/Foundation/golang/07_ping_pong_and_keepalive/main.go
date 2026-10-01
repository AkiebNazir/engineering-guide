/*
FOUNDATION LEVEL 07 - Ping, pong, and spotting a connection that died quietly
=================================================================================
Level 06 ended with a connection that disappeared without saying goodbye. That
is not an edge case, it is the normal failure. Laptops close, phones change
network, NAT tables forget you after a few minutes of silence, load balancers
reap idle connections. In every one of those cases your server still holds an
open socket that will never deliver another byte - a "half-open" connection -
and it will sit there for hours unless you check.

TCP will not tell you. It only notices when you try to write, and even then not
quickly. So WebSockets gives you Ping and Pong: two CONTROL frames whose only
job is to be a heartbeat. Send a ping, and a conforming peer MUST reply with a
pong. No reply in time means the peer is gone, whatever the socket claims.

THE ONE GO-SPECIFIC RULE THAT SURPRISES EVERYONE:
in coder/websocket, control frames are processed by whoever is calling Read.
So a peer that keeps calling Read answers pings automatically and for free -
and a peer that has STOPPED calling Read never answers, even though its
process is alive and its socket is open. That is not a bug, it is the
detection mechanism: "is this peer still reading?" is exactly the question
worth asking.

You will learn
  - c.Ping(ctx) sends a ping and BLOCKS until the pong arrives or ctx expires,
    which makes it both a liveness check and a latency measurement
  - a keepalive goroutine beside the read loop: ping on a ticker, CloseNow on
    failure (a polite Close is pointless - the peer is not listening)
  - that you never write pong-handling code: the library answers pings for you
  - the application-level alternative: your own idle deadline, which requires
    client ACTIVITY rather than mere liveness
  - why sending data is not a substitute: writes into a dead socket succeed
    for a long time before the OS admits the truth

Run it   go run ./WebSockets/Foundation/golang/07_ping_pong_and_keepalive
*/
package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"net/http"
	"sync/atomic"
	"time"

	"github.com/coder/websocket"
)

const (
	pingEvery   = 40 * time.Millisecond  // realistically 15-30s
	pingTimeout = 200 * time.Millisecond // realistically 5-10s
	idleLimit   = 300 * time.Millisecond // realistically 30-120s
)

// Bumped when the keepalive loop decides a peer is not answering.
var deadPeers atomic.Int64

// A plain echo server. Note what is NOT here: any ping handling at all. The
// library answers pings underneath us while we sit in Read, which is the point.
func echoHandler(w http.ResponseWriter, r *http.Request) {
	c, err := websocket.Accept(w, r, nil)
	if err != nil {
		return
	}
	defer c.CloseNow()

	for {
		ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
		msgType, data, err := c.Read(ctx)
		cancel()
		if err != nil {
			return
		}
		if c.Write(r.Context(), msgType, []byte("echo: "+string(data))) != nil {
			return
		}
	}
}

// Pings its peer on a ticker and hangs up on one that stops answering.
func keepaliveHandler(w http.ResponseWriter, r *http.Request) {
	c, err := websocket.Accept(w, r, nil)
	if err != nil {
		return
	}
	defer c.CloseNow()

	ctx, cancel := context.WithCancel(r.Context())
	defer cancel()

	// The keepalive loop runs BESIDE the read loop, in its own goroutine,
	// because Ping blocks and the read loop must not stall while it waits.
	go func() {
		t := time.NewTicker(pingEvery)
		defer t.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-t.C:
				pctx, pcancel := context.WithTimeout(ctx, pingTimeout)
				err := c.Ping(pctx)
				pcancel()
				if err != nil && ctx.Err() == nil {
					fmt.Println("  [server] no pong within the timeout -> this peer is gone")
					deadPeers.Add(1)
					// No point in a polite Close: a peer that will not answer
					// a ping will not answer a close frame either.
					c.CloseNow()
					cancel()
					return
				}
			}
		}
	}()

	for {
		_, _, err := c.Read(ctx)
		if err != nil {
			return
		}
	}
}

// Requires the client to SAY SOMETHING every idleLimit.
//
// This is stricter than ping/pong: a client can answer pings perfectly while
// being a stuck, useless process. Demanding real messages ("activity", not
// "liveness") is an application decision - e.g. a game that requires input.
func strictHandler(w http.ResponseWriter, r *http.Request) {
	c, err := websocket.Accept(w, r, nil)
	if err != nil {
		return
	}
	defer c.CloseNow()

	ctx, cancel := context.WithCancel(r.Context())
	defer cancel()

	// A GO GOTCHA WORTH THE WHOLE LEVEL: you might expect to write the idle
	// deadline as context.WithTimeout around each Read. Do not. When a read
	// context expires, coder/websocket tears the connection down immediately -
	// so a c.Close(1001, ...) afterwards has no connection left to send on,
	// and the peer learns nothing (it sees "no close frame", level 06's -1).
	//
	// Instead: let Read block on a long-lived context, and run the deadline as
	// a timer beside it. Then the close frame goes out on a live connection.
	activity := make(chan struct{}, 1)
	go func() {
		t := time.NewTimer(idleLimit)
		defer t.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-activity: // a message arrived: start the clock over
				if !t.Stop() {
					select {
					case <-t.C:
					default:
					}
				}
				t.Reset(idleLimit)
			case <-t.C:
				fmt.Printf("  [server] no message for %v -> assuming this client is gone\n", idleLimit)
				// 1001 "going away" is the polite code for "I am ending this,
				// and it is not exactly your fault" - see level 06.
				c.Close(websocket.StatusGoingAway, "idle timeout, no heartbeat")
				cancel()
				return
			}
		}
	}()

	for {
		_, data, err := c.Read(ctx)
		if err != nil {
			return
		}
		select {
		case activity <- struct{}{}:
		default:
		}
		if c.Write(ctx, websocket.MessageText, []byte("ack: "+string(data))) != nil {
			return
		}
	}
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func demo(echoURL, keepaliveURL, strictURL string) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	fmt.Println("== 1a. the Go rule, demonstrated: no Read in flight means no pong ==")
	lonely, _, err := websocket.Dial(ctx, echoURL, nil)
	must(err == nil, fmt.Sprint(err))
	// Nobody is calling Read on this connection, so when the server's pong
	// arrives there is no one to process it, and Ping waits forever.
	pctx, pcancel := context.WithTimeout(ctx, 250*time.Millisecond)
	err = lonely.Ping(pctx)
	pcancel()
	fmt.Printf("  Ping with no reader goroutine -> %v\n", err)
	must(err != nil, "a ping with nobody reading must not succeed")
	fmt.Println("  the pong DID arrive on the socket; nothing was there to pick it up")
	lonely.CloseNow()

	fmt.Println("\n== 1b. with a reader running, a ping is a free latency measurement ==")
	c, _, err := websocket.Dial(ctx, echoURL, nil)
	must(err == nil, fmt.Sprint(err))

	// One goroutine owns Read for this connection. It processes control frames
	// (pongs) as a side effect, and hands application messages to a channel.
	// This is the standard shape for any client that also needs to ping.
	replies := make(chan string, 4)
	go func() {
		defer close(replies)
		for {
			_, data, err := c.Read(ctx)
			if err != nil {
				return
			}
			replies <- string(data)
		}
	}()

	start := time.Now()
	// Ping blocks until the matching pong comes back, so the elapsed time is
	// real network round-trip time.
	must(c.Ping(ctx) == nil, "ping")
	fmt.Printf("  ping -> pong round trip: %.2f ms\n", float64(time.Since(start).Microseconds())/1000)
	fmt.Println("  the echo handler has no ping code in it at all -")
	fmt.Println("  the library answered on its behalf, from inside ITS Read call")

	// Proof that the ping did not disturb the message stream.
	must(c.Write(ctx, websocket.MessageText, []byte("hello")) == nil, "write")
	data := <-replies
	fmt.Printf("  a normal message still behaves normally: %q\n", data)
	must(data == "echo: hello", "echo")
	must(c.Close(websocket.StatusNormalClosure, "done") == nil, "close")

	fmt.Println("\n== 2. a client that stops READING is detected, even though it is 'up' ==")
	dead, _, err := websocket.Dial(ctx, keepaliveURL, nil)
	must(err == nil, fmt.Sprint(err))
	// Deliberately never call Read on `dead`. Its process is healthy, its
	// socket is open, and it will still never send a pong - which is exactly
	// what a frozen app or a vanished network looks like from the server.
	fmt.Println("  client connected, then stopped calling Read (simulating a frozen app)")

	deadline := time.Now().Add(5 * time.Second)
	for deadPeers.Load() == 0 && time.Now().Before(deadline) {
		time.Sleep(10 * time.Millisecond)
	}
	fmt.Printf("  peers the server gave up on: %d\n", deadPeers.Load())
	must(deadPeers.Load() == 1, "the server should have detected one dead peer")
	dead.CloseNow()

	fmt.Println("\n== 3. an application-level idle deadline (requiring ACTIVITY) ==")
	s, _, err := websocket.Dial(ctx, strictURL, nil)
	must(err == nil, fmt.Sprint(err))

	for i := 0; i < 3; i++ {
		must(s.Write(ctx, websocket.MessageText, []byte(fmt.Sprintf("heartbeat %d", i))) == nil, "write")
		_, data, err := s.Read(ctx)
		must(err == nil, fmt.Sprint(err))
		fmt.Printf("   %s\n", data)
		time.Sleep(idleLimit / 3) // comfortably inside the deadline
	}

	fmt.Printf("  now going silent for longer than the %v deadline...\n", idleLimit)
	_, _, err = s.Read(ctx)
	must(err != nil, "expected the server to hang up on us")
	fmt.Printf("  server closed us: %d\n", websocket.CloseStatus(err))
	must(websocket.CloseStatus(err) == websocket.StatusGoingAway, "expected 1001")
	s.CloseNow()

	fmt.Println("\n  note: this client was perfectly healthy and answering pings.")
	fmt.Println("  It was closed for being IDLE, which is a different rule on purpose.")
	fmt.Println("\nOK")
}

func main() {
	listen := func(h http.HandlerFunc) string {
		ln, err := net.Listen("tcp", "127.0.0.1:0")
		if err != nil {
			log.Fatal(err)
		}
		go http.Serve(ln, h)
		return "ws://" + ln.Addr().String()
	}
	demo(listen(echoHandler), listen(keepaliveHandler), listen(strictHandler))
}
