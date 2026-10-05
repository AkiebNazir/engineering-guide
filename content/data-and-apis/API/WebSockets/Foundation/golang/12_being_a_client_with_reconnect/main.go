/*
FOUNDATION LEVEL 12 - Being the client: reconnecting is not optional
========================================================================
Levels 00-11 were all SERVER code. Flip the lens: you are the client now, and
you have a problem REST clients do not have.

A REST client's retry logic is per call. One request fails, you retry that one
request, and nothing else in your program knows or cares - each call stands
alone (see ../../../REST/Foundation/golang/12_being_a_client).

A WebSocket client's connection IS its state. When it drops - and it WILL drop:
wifi, sleep, a deploy, a load balancer's idle timeout - you do not lose one
call, you lose the session: your authentication, your room membership, your
subscriptions, and any messages sent while you were away. So a real WebSocket
client is not "dial and read". It is a LOOP that reconnects forever, with
backoff, and re-establishes its session state every time it gets back in.

You will learn
  - the reconnect loop: dial -> use -> on failure, wait, then dial again
  - exponential backoff with a cap, so a server that is down does not get
    hammered by every client at once the moment it starts recovering
  - JITTER: without a random offset, ten thousand clients dropped by the same
    deploy all reconnect in the same millisecond (the "thundering herd")
  - resubscribing: on reconnect you must redo the setup handshake (auth, room
    join) - the server remembers nothing about the connection that died
  - the gap problem: messages sent while you were disconnected are simply gone
    unless the protocol has sequence numbers
    (../../../labs/golang/05_scaling_pubsub_and_tickets covers resume)

Run it   go run ./WebSockets/Foundation/golang/12_being_a_client_with_reconnect
*/
package main

import (
	"context"
	"fmt"
	"log"
	"math/rand/v2"
	"net"
	"net/http"
	"sync/atomic"
	"time"

	"github.com/coder/websocket"
	"github.com/coder/websocket/wsjson"
)

const (
	baseDelay         = 20 * time.Millisecond  // realistically 500ms-1s
	maxDelay          = 200 * time.Millisecond // realistically 30-60s
	dropsBeforeStable = 2
	messagesToCollect = 3
)

// Server-side bookkeeping so the demo can prove what happened.
var serverConnections atomic.Int64

type message struct {
	Type    string `json:"type"`
	Payload any    `json:"payload"`
}

// flakyHandler drops the first dropsBeforeStable connections abruptly, then
// behaves. This imitates a server being rolled out, or a proxy reaping
// connections - not a broken server. Note it drops them with NO close frame,
// which is the realistic case.
func flakyHandler(w http.ResponseWriter, r *http.Request) {
	c, err := websocket.Accept(w, r, nil)
	if err != nil {
		return
	}
	defer c.CloseNow()

	n := serverConnections.Add(1)

	// Every connection must re-subscribe: the server kept nothing.
	var hello message
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	err = wsjson.Read(ctx, c, &hello)
	cancel()
	if err != nil {
		return
	}
	if hello.Type != "subscribe" {
		c.Close(websocket.StatusPolicyViolation, "expected subscribe first")
		return
	}
	if wsjson.Write(r.Context(), c, message{Type: "subscribed", Payload: hello.Payload}) != nil {
		return
	}

	if n <= dropsBeforeStable {
		fmt.Printf("  [server] connection #%d: dropping it abruptly (no close frame)\n", n)
		c.CloseNow()
		return
	}

	fmt.Printf("  [server] connection #%d: this one will stay up\n", n)
	for {
		rctx, rcancel := context.WithTimeout(r.Context(), 10*time.Second)
		var in message
		err := wsjson.Read(rctx, c, &in)
		rcancel()
		if err != nil {
			return
		}
		if wsjson.Write(r.Context(), c, message{Type: "echo", Payload: in.Payload}) != nil {
			return
		}
	}
}

// backoffDelay is exponential backoff, capped, with jitter.
//
// attempt 0 -> ~baseDelay, 1 -> ~2x, 2 -> ~4x, ... never above maxDelay.
// The jitter is the part people forget, and the part that saves the server: it
// spreads a herd of reconnecting clients over a window instead of letting them
// all arrive in one synchronised spike.
func backoffDelay(attempt int) time.Duration {
	capped := baseDelay << attempt
	if capped > maxDelay || capped <= 0 {
		capped = maxDelay
	}
	// 50-100% of the capped delay.
	return time.Duration(float64(capped) * (0.5 + rand.Float64()/2))
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

// resilientClient stays connected until `want` echo replies have been
// collected. This function is the deliverable of this level: the shape every
// production WebSocket client has.
func resilientClient(ctx context.Context, url, room string, want int) ([]float64, []time.Duration) {
	var received []float64
	var delays []time.Duration
	attempt := 0

	for len(received) < want {
		if attempt > 0 {
			delay := backoffDelay(attempt - 1)
			delays = append(delays, delay)
			fmt.Printf("  [client] reconnecting in %dms (attempt %d)\n",
				delay.Milliseconds(), attempt+1)
			time.Sleep(delay)
		}
		attempt++

		func() {
			c, _, err := websocket.Dial(ctx, url, nil)
			if err != nil {
				fmt.Printf("  [client] dial failed: %v - will retry\n", err)
				return
			}
			defer c.CloseNow()

			// RE-ESTABLISH THE SESSION. The server that just accepted us has
			// never heard of us before, even if we were talking to the same
			// process 20ms ago. Authentication, subscriptions, room
			// membership: all of it must be redone, every single time.
			if wsjson.Write(ctx, c, message{Type: "subscribe", Payload: room}) != nil {
				return
			}
			var ack message
			if wsjson.Read(ctx, c, &ack) != nil || ack.Type != "subscribed" {
				return
			}
			fmt.Printf("  [client] connected and re-subscribed to %v\n", ack.Payload)

			// A successful connection resets the backoff, so the next
			// unrelated failure starts from a short delay again.
			attempt = 0

			for len(received) < want {
				if wsjson.Write(ctx, c, message{Type: "work", Payload: len(received)}) != nil {
					attempt = 1
					return
				}
				var reply message
				if err := wsjson.Read(ctx, c, &reply); err != nil {
					// This is the ONLY correct reaction to a dropped
					// WebSocket: note it, back off, and go round the loop.
					// Exiting here would mean your app dies every time
					// someone walks into a lift.
					fmt.Printf("  [client] connection lost: CloseStatus %d - will retry\n",
						websocket.CloseStatus(err))
					attempt = 1
					return
				}
				received = append(received, reply.Payload.(float64))
				fmt.Printf("  [client] got reply %v\n", reply.Payload)
			}
		}()
	}
	return received, delays
}

func demo(url string) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	fmt.Printf("== the server will abruptly drop the first %d connections; "+
		"the client must not care ==\n", dropsBeforeStable)
	received, delays := resilientClient(ctx, url, "prices", messagesToCollect)

	fmt.Printf("\nserver accepted %d connections to deliver %d replies\n",
		serverConnections.Load(), len(received))
	must(len(received) == messagesToCollect, "all replies collected")
	for i, v := range received {
		must(v == float64(i), "replies in order")
	}
	// One connection per drop, plus the one that finally stuck.
	must(serverConnections.Load() == int64(dropsBeforeStable+1), "connection count")

	fmt.Print("backoff delays used: ")
	for _, d := range delays {
		fmt.Printf("%dms ", d.Milliseconds())
	}
	fmt.Println()
	must(len(delays) == dropsBeforeStable, "one delay per drop")
	fmt.Println("  both are short, because each drop came AFTER a successful connect -")
	fmt.Println("  and success resets the backoff. Delays only grow while failures")
	fmt.Println("  are consecutive, which is exactly the behaviour you want.")

	fmt.Println("\n== so, for a server that stays down: the delays grow and the cap holds ==")
	// Shown without jitter so the doubling is obvious; the real delays above
	// are each a random 50-100% of these.
	for attempt := 0; attempt < 8; attempt++ {
		capped := baseDelay << attempt
		note := ""
		if capped > maxDelay || capped <= 0 {
			capped = maxDelay
			note = "   <- capped"
		}
		fmt.Printf("  attempt %d: up to %6dms%s\n", attempt+1, capped.Milliseconds(), note)
		must(capped <= maxDelay, "cap holds")
	}

	fmt.Println("\n== jitter spreads a herd out instead of synchronising it ==")
	var herd []time.Duration
	for i := 0; i < 5; i++ {
		herd = append(herd, backoffDelay(3))
	}
	fmt.Print("  5 clients, same attempt number, different waits: ")
	allSame := true
	for _, d := range herd {
		fmt.Printf("%dms ", d.Milliseconds())
		if d != herd[0] {
			allSame = false
		}
	}
	fmt.Println()
	must(!allSame, "jitter should not produce identical delays")

	fmt.Println("\nOK")
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, http.HandlerFunc(flakyHandler))
	demo("ws://" + ln.Addr().String())
}
