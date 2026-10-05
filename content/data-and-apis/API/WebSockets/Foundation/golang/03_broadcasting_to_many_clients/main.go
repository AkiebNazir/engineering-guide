/*
FOUNDATION LEVEL 03 - Broadcasting: one message in, many clients out
========================================================================
This is the level that justifies WebSockets existing. Everything so far was
still one client talking to one server, which HTTP can do perfectly well. Now:
one client sends a message, and EVERY connected client receives it - including
ones that were sitting there silent, having asked for nothing.

REST cannot do this at all. A REST server has no way to reach a client; it can
only answer clients who happen to be asking right now. A WebSocket server, by
contrast, holds a live handle to every connected client, so "tell everyone" is
just a loop over a map.

You will learn
  - the registry pattern: a map of live connections, added on connect and -
    critically - removed in a `defer` so it cannot leak
  - that the registry is shared mutable state touched by many goroutines at
    once, so it needs a sync.Mutex; this is the first genuinely concurrent
    level, because Go gives every connection its own goroutine
  - fan-out: one inbound message becomes N outbound messages
  - copying the target list under the lock, then writing OUTSIDE it - a slow
    client must never hold the mutex while everyone else waits
  - where this grows up: a single "hub" goroutine owning the map so no mutex
    is needed at all, in ../../../labs/golang/03_hub_pattern_chat

Run it   go run ./WebSockets/Foundation/golang/03_broadcasting_to_many_clients
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
)

// THIS is the thing REST does not have: a server-side set of clients you can
// speak to whenever you like. Guarded by a mutex because net/http runs each
// connection's handler in its own goroutine.
type registry struct {
	mu      sync.Mutex
	clients map[*websocket.Conn]struct{}
}

func newRegistry() *registry {
	return &registry{clients: make(map[*websocket.Conn]struct{})}
}

func (reg *registry) add(c *websocket.Conn) int {
	reg.mu.Lock()
	defer reg.mu.Unlock()
	reg.clients[c] = struct{}{}
	return len(reg.clients)
}

func (reg *registry) remove(c *websocket.Conn) int {
	reg.mu.Lock()
	defer reg.mu.Unlock()
	delete(reg.clients, c)
	return len(reg.clients)
}

func (reg *registry) size() int {
	reg.mu.Lock()
	defer reg.mu.Unlock()
	return len(reg.clients)
}

// broadcast sends one message to every live client and returns how many were
// reached.
func (reg *registry) broadcast(ctx context.Context, text string) int {
	// Copy the targets under the lock, then release it. Writing while holding
	// the mutex would let one slow client block every other connection on the
	// server - the classic mistake in this pattern.
	reg.mu.Lock()
	targets := make([]*websocket.Conn, 0, len(reg.clients))
	for c := range reg.clients {
		targets = append(targets, c)
	}
	reg.mu.Unlock()

	var wg sync.WaitGroup
	var mu sync.Mutex
	reached := 0
	for _, c := range targets {
		wg.Add(1)
		go func(c *websocket.Conn) {
			defer wg.Done()
			wctx, cancel := context.WithTimeout(ctx, 5*time.Second)
			defer cancel()
			// A client that died a millisecond ago makes this fail. That must
			// not abort the broadcast for everyone else, so the error is
			// counted, not propagated.
			if err := c.Write(wctx, websocket.MessageText, []byte(text)); err == nil {
				mu.Lock()
				reached++
				mu.Unlock()
			}
		}(c)
	}
	wg.Wait()
	return reached
}

func (reg *registry) handler(w http.ResponseWriter, r *http.Request) {
	c, err := websocket.Accept(w, r, nil)
	if err != nil {
		return
	}
	defer c.CloseNow()

	fmt.Printf("  [server] client joined  (now %d connected)\n", reg.add(c))
	// A `defer` is not optional. Without it the map grows forever with dead
	// connections and every broadcast gets slower and noisier.
	defer func() {
		fmt.Printf("  [server] client left    (now %d connected)\n", reg.remove(c))
	}()

	for {
		ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
		_, data, err := c.Read(ctx)
		cancel()
		if err != nil {
			return
		}
		// One inbound message -> len(clients) outbound messages.
		reached := reg.broadcast(r.Context(), "someone said: "+string(data))
		fmt.Printf("  [server] fanned %q out to %d client(s)\n", data, reached)
	}
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func demo(url string, reg *registry) {
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()

	dial := func() *websocket.Conn {
		c, _, err := websocket.Dial(ctx, url, nil)
		must(err == nil, fmt.Sprint(err))
		return c
	}

	fmt.Println("== three clients connect; ONE of them speaks ==")
	alice, bob, carol := dial(), dial(), dial()

	// Wait until the server has registered all three, so the fan-out below is
	// deterministic. (In real code nobody cares; in a teaching assert we do.)
	for i := 0; i < 200 && reg.size() < 3; i++ {
		time.Sleep(5 * time.Millisecond)
	}
	must(reg.size() == 3, "three clients registered")

	must(alice.Write(ctx, websocket.MessageText, []byte("hi everyone")) == nil, "write")

	names := []string{"alice", "bob  ", "carol"}
	for i, c := range []*websocket.Conn{alice, bob, carol} {
		_, data, err := c.Read(ctx)
		must(err == nil, fmt.Sprint(err))
		fmt.Printf("  %s received: %q\n", names[i], data)
		// bob and carol asked for NOTHING. They received it because the
		// server chose to push to them. That is the whole feature.
		must(string(data) == "someone said: hi everyone", "fan-out")
	}

	fmt.Println("\n== a different client speaks: same fan-out, other direction ==")
	must(carol.Write(ctx, websocket.MessageText, []byte("hello back")) == nil, "write")
	for i, c := range []*websocket.Conn{alice, bob, carol} {
		_, data, err := c.Read(ctx)
		must(err == nil, fmt.Sprint(err))
		fmt.Printf("  %s received: %q\n", names[i], data)
		must(string(data) == "someone said: hello back", "fan-out")
	}

	fmt.Println("\n== after everyone disconnects, the registry empties itself ==")
	for _, c := range []*websocket.Conn{alice, bob, carol} {
		must(c.Close(websocket.StatusNormalClosure, "bye") == nil, "close")
	}
	for i := 0; i < 200 && reg.size() > 0; i++ {
		time.Sleep(5 * time.Millisecond)
	}
	fmt.Printf("  clients still registered: %d\n", reg.size())
	must(reg.size() == 0, "registry drained")

	fmt.Println("\n== fan-out shrinks as clients leave ==")
	only := dial()
	defer only.CloseNow()
	must(only.Write(ctx, websocket.MessageText, []byte("just me")) == nil, "write")
	_, data, err := only.Read(ctx)
	must(err == nil, fmt.Sprint(err))
	fmt.Printf("  received: %q\n", data)
	must(only.Close(websocket.StatusNormalClosure, "bye") == nil, "close")

	fmt.Println("\nOK")
}

func main() {
	reg := newRegistry()
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, http.HandlerFunc(reg.handler))
	demo("ws://"+ln.Addr().String(), reg)
}
