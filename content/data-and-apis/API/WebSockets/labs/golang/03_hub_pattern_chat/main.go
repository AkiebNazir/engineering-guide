/*
LAB 03 (advanced) - The hub pattern: a concurrent chat server with rooms and slow-client eviction
================================================================================================
You will learn

  - the canonical Go WebSocket architecture (used by gorilla's chat example, Slack-like servers, ...):

    client A ---readPump---\                       /--writePump--- client A
    client B ---readPump----> [ HUB goroutine ] --<---writePump--- client B
    client C ---readPump---/    owns the rooms      \--writePump--- client C  (slow!)
    map: NO MUTEX

  - ONE goroutine (the hub) owns all shared state, so there is no locking and no data race

  - each connection has TWO goroutines: readPump (socket -> hub) and writePump (channel -> socket)
    because a websocket allows one concurrent reader and one concurrent writer

  - each client has a BUFFERED send channel; the hub NEVER blocks on a client:
    select { case c.send <- msg: default: evict(c) }
    a slow client is evicted instead of stalling the whole room

  - cleanup discipline: every exit path unregisters, closes the channel exactly once, and ends both pumps

  - SHUTDOWN SAFETY (the leak check below caught this bug in the first draft): once the hub stops,
    a handler that tries to `unregister <- c` would block forever. So Register/Unregister/Broadcast
    all `select` on hub.done, and the writePump also ends on ctx.Done(), not just on its channel closing

  - proving it: 30 clients, 200 messages, one deliberately slow client - verified with a goroutine
    leak check (run with -race to also prove there are no data races)

Run it   go run ./WebSockets/labs/golang/03_hub_pattern_chat
Race     go run -race ./WebSockets/labs/golang/03_hub_pattern_chat
*/
package main

import (
	"context"
	"fmt"
	"net"
	"net/http"
	"runtime"
	"sync"
	"sync/atomic"
	"time"

	"github.com/coder/websocket"
)

// ------------------------------------------------------------------ client --
type Client struct {
	conn *websocket.Conn
	room string
	name string
	send chan []byte   // hub -> writePump. BOUNDED.
	link time.Duration // TEST ONLY: models a slow network path (loopback has no real bandwidth limit)
	done chan struct{} // closed when writePump has finished
}

func (c *Client) writePump(ctx context.Context) {
	defer close(c.done)
	for {
		select {
		case msg, ok := <-c.send:
			if !ok { // the hub closed our channel: it evicted us because we could not keep up
				c.conn.Close(websocket.StatusTryAgainLater, "too slow, reconnect")
				return
			}
			time.Sleep(c.link)
			wctx, cancel := context.WithTimeout(ctx, 5*time.Second)
			err := c.conn.Write(wctx, websocket.MessageText, msg)
			cancel()
			if err != nil {
				c.conn.CloseNow()
				return
			}
		case <-ctx.Done(): // the read side ended (client left, or the server is shutting down)
			c.conn.CloseNow()
			return
		}
	}
}

func (c *Client) readPump(ctx context.Context, h *Hub) {
	defer h.Unregister(c) // EVERY exit path unregisters
	c.conn.SetReadLimit(4 << 10)
	for {
		_, data, err := c.conn.Read(ctx)
		if err != nil {
			return
		}
		h.Broadcast(envelope{from: c, data: data})
	}
}

// --------------------------------------------------------------------- hub ---
type envelope struct {
	from *Client
	data []byte
}

type Hub struct {
	done       chan struct{} // closed when Run returns; senders must never block on a dead hub
	register   chan *Client
	unregister chan *Client
	broadcast  chan envelope
	rooms      map[string]map[*Client]struct{} // touched ONLY by Run()
	evicted    atomic.Int64
	delivered  atomic.Int64
}

func NewHub() *Hub {
	return &Hub{done: make(chan struct{}), register: make(chan *Client), unregister: make(chan *Client),
		broadcast: make(chan envelope, 256), rooms: map[string]map[*Client]struct{}{}}
}

func (h *Hub) drop(c *Client) {
	if members, ok := h.rooms[c.room]; ok {
		if _, in := members[c]; in { // idempotent: unregister may follow an eviction
			delete(members, c)
			close(c.send) // closed exactly once, because we only get here when c was still a member
			if len(members) == 0 {
				delete(h.rooms, c.room)
			}
		}
	}
}

// Register / Unregister / Broadcast are how the outside world talks to the hub. Each one gives up
// if the hub has stopped - otherwise a handler finishing during shutdown would block forever.
func (h *Hub) Register(c *Client) bool {
	select {
	case h.register <- c:
		return true
	case <-h.done:
		return false
	}
}

func (h *Hub) Unregister(c *Client) {
	select {
	case h.unregister <- c:
	case <-h.done:
	}
}

func (h *Hub) Broadcast(e envelope) {
	select {
	case h.broadcast <- e:
	case <-h.done:
	}
}

func (h *Hub) Run(ctx context.Context) {
	defer close(h.done)
	for {
		select {
		case c := <-h.register:
			if h.rooms[c.room] == nil {
				h.rooms[c.room] = map[*Client]struct{}{}
			}
			h.rooms[c.room][c] = struct{}{}
		case c := <-h.unregister:
			h.drop(c)
		case e := <-h.broadcast:
			msg := []byte(e.from.name + ": " + string(e.data))
			for c := range h.rooms[e.from.room] {
				if c == e.from {
					continue
				}
				select {
				case c.send <- msg: // fast path
					h.delivered.Add(1)
				default: // buffer full => this client cannot keep up. EVICT it; do not wait.
					h.evicted.Add(1)
					h.drop(c)
				}
			}
		case <-ctx.Done():
			return
		}
	}
}

// ------------------------------------------------------------ http handler --
func serveWS(h *Hub, slowNames map[string]time.Duration) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		conn, err := websocket.Accept(w, r, nil)
		if err != nil {
			return
		}
		name := r.URL.Query().Get("name")
		c := &Client{conn: conn, room: r.URL.Query().Get("room"), name: name,
			send: make(chan []byte, 32), link: slowNames[name], done: make(chan struct{})}
		ctx, cancel := context.WithCancel(r.Context()) // ends BOTH pumps, whichever finishes first
		defer cancel()
		if !h.Register(c) {
			conn.Close(websocket.StatusServiceRestart, "shutting down")
			return
		}
		go c.writePump(ctx)
		c.readPump(ctx, h) // blocks until the client leaves
		cancel()           // tell the writer to stop even if the hub never closes c.send
		<-c.done           // wait for the writer so nothing outlives the handler
	}
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	before := runtime.NumGoroutine()
	hubCtx, stopHub := context.WithCancel(context.Background())
	hub := NewHub()
	go hub.Run(hubCtx)

	slow := map[string]time.Duration{"slowpoke": 50 * time.Millisecond} // 20 msg/s; the room sends far faster
	ln, _ := net.Listen("tcp", "127.0.0.1:0")
	srv := &http.Server{Handler: serveWS(hub, slow)}
	go srv.Serve(ln)
	base := "ws://" + ln.Addr().String() + "/ws"

	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()

	const nFast, nMessages = 30, 200
	type stats struct {
		got   atomic.Int64
		close int
	}
	var wg sync.WaitGroup
	counters := make([]*stats, nFast)
	dial := func(room, name string) *websocket.Conn {
		c, _, err := websocket.Dial(ctx, base+"?room="+room+"&name="+name, nil)
		must(err == nil, fmt.Sprint(err))
		return c
	}

	fmt.Printf("== %d fast readers, 1 slow reader (room \"go\"), 1 reader in another room ==\n", nFast)
	for i := 0; i < nFast; i++ {
		conn := dial("go", fmt.Sprintf("fast-%02d", i))
		st := &stats{}
		counters[i] = st
		wg.Add(1)
		go func() {
			defer wg.Done()
			for {
				if _, _, err := conn.Read(ctx); err != nil {
					return
				}
				st.got.Add(1)
			}
		}()
	}
	slowConn := dial("go", "slowpoke")
	var slowGot atomic.Int64
	var slowClose atomic.Int64
	slowClose.Store(-2)
	wg.Add(1)
	go func() {
		defer wg.Done()
		for {
			if _, _, err := slowConn.Read(ctx); err != nil {
				slowClose.Store(int64(websocket.CloseStatus(err)))
				return
			}
			slowGot.Add(1)
		}
	}()
	otherRoom := dial("py", "other")
	var otherGot atomic.Int64
	wg.Add(1)
	go func() {
		defer wg.Done()
		for {
			if _, _, err := otherRoom.Read(ctx); err != nil {
				return
			}
			otherGot.Add(1)
		}
	}()
	time.Sleep(200 * time.Millisecond) // let every registration land

	fmt.Printf("== a publisher sends %d messages as fast as it can ==\n", nMessages)
	pub := dial("go", "publisher")
	start := time.Now()
	for i := 0; i < nMessages; i++ {
		must(pub.Write(ctx, websocket.MessageText, []byte(fmt.Sprintf("message %d", i))) == nil, "publish")
		time.Sleep(time.Millisecond) // ~1000 msg/s: a fast but not instantaneous publisher
	}
	took := time.Since(start)
	fmt.Printf("  publisher finished in %s (≈%.0f msg/s; it never waited on the slow reader)\n", took.Round(time.Millisecond), nMessages/took.Seconds())
	time.Sleep(1500 * time.Millisecond) // let deliveries settle

	minGot := int64(nMessages)
	for _, st := range counters {
		if g := st.got.Load(); g < minGot {
			minGot = g
		}
	}
	fmt.Printf("  every fast reader received at least %d/%d messages\n", minGot, nMessages)
	fmt.Printf("  slow reader received %d, was evicted: %v, close status seen by the slow client: %d (1013 = try again later)\n",
		slowGot.Load(), hub.evicted.Load() > 0, slowClose.Load())
	fmt.Printf("  reader in room \"py\" received %d (rooms are isolated)\n", otherGot.Load())
	must(minGot == nMessages, "no fast reader lost a message")
	must(hub.evicted.Load() == 1 && slowGot.Load() < nMessages, "exactly the slow reader was evicted")
	must(slowClose.Load() == int64(websocket.StatusTryAgainLater), "slow reader told to retry later")
	must(otherGot.Load() == 0, "room isolation")

	fmt.Println("\n== shutdown and leak check ==")
	pub.Close(websocket.StatusNormalClosure, "")
	otherRoom.Close(websocket.StatusNormalClosure, "")
	shutdownCtx, c2 := context.WithTimeout(context.Background(), 5*time.Second)
	defer c2()
	srv.Shutdown(shutdownCtx)
	cancel() // stops the client read loops
	wg.Wait()
	stopHub()
	time.Sleep(300 * time.Millisecond)
	after := runtime.NumGoroutine()
	fmt.Printf("  goroutines before: %d, after: %d\n", before, after)
	must(after <= before+3, "no goroutine leak (server side pumps all exited)")
	fmt.Println("\nOK")
}
