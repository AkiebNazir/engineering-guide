/*
LAB 05 (advanced) - Scaling WebSockets across servers, and authenticating with one-time tickets
================================================================================================
You will learn

  - THE scaling problem: a WebSocket is STATEFUL. Client A is connected to server 1, client B to
    server 2. When A says something, server 1 has no idea B exists.

    A --ws--> [ node 1 ]                [ node 2 ] <--ws-- B
    |  publish("room:go")     ^  deliver to my local clients
    v                         |
    [ BROKER: Redis pub/sub / NATS / Kafka ]

    Every node publishes to the broker, and every node SUBSCRIBES to the rooms its local clients
    joined, then fans messages out to its own sockets. Nodes stay stateless about each other.
    (Here the broker is an in-memory stand-in behind an interface - swap in Redis without touching the rest.)

  - what a load balancer must do: pass Upgrade/Connection headers, use long idle timeouts,
    and NOT balance per-request (a socket is pinned to its node for its lifetime)

  - authentication with ONE-TIME TICKETS:
    1. client calls  POST /ws-ticket  with its normal Bearer token (over ordinary HTTPS)
    2. server returns a random single-use ticket, valid for 30s, bound to that user
    3. client connects to  /ws?ticket=...   - the ticket is burned on first use
    a ticket that leaks into an access log is useless: already spent, or expired

  - Origin allow-list for browser clients

Run it   go run ./WebSockets/labs/golang/05_scaling_pubsub_and_tickets
*/
package main

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/coder/websocket"
)

// ------------------------------------------------------------------ broker ---
// Broker is the seam. The Redis version is ~20 lines: PUBLISH / SUBSCRIBE.
type Broker interface {
	Publish(topic string, msg []byte)
	Subscribe(ctx context.Context, topic string) <-chan []byte
}

type memBroker struct {
	mu   sync.Mutex
	subs map[string][]chan []byte
}

func newMemBroker() *memBroker { return &memBroker{subs: map[string][]chan []byte{}} }

func (b *memBroker) Publish(topic string, msg []byte) {
	b.mu.Lock()
	defer b.mu.Unlock()
	for _, ch := range b.subs[topic] {
		select {
		case ch <- msg:
		default: // a slow node drops; real brokers have their own back-pressure policy
		}
	}
}

func (b *memBroker) Subscribe(ctx context.Context, topic string) <-chan []byte {
	ch := make(chan []byte, 64)
	b.mu.Lock()
	b.subs[topic] = append(b.subs[topic], ch)
	b.mu.Unlock()
	go func() {
		<-ctx.Done()
		b.mu.Lock()
		defer b.mu.Unlock()
		for i, c := range b.subs[topic] {
			if c == ch {
				b.subs[topic] = append(b.subs[topic][:i], b.subs[topic][i+1:]...)
				break
			}
		}
	}()
	return ch
}

// ---------------------------------------------------------- ticket service ---
type ticketStore struct {
	mu      sync.Mutex
	tickets map[string]ticket
	now     func() time.Time
}
type ticket struct {
	user    string
	expires time.Time
}

func (t *ticketStore) issue(user string, ttl time.Duration) string {
	raw := make([]byte, 16)
	rand.Read(raw)
	id := hex.EncodeToString(raw)
	t.mu.Lock()
	t.tickets[id] = ticket{user, t.now().Add(ttl)}
	t.mu.Unlock()
	return id
}

// redeem returns the user and DELETES the ticket: single use, no matter what happens next.
func (t *ticketStore) redeem(id string) (string, bool) {
	t.mu.Lock()
	defer t.mu.Unlock()
	tk, ok := t.tickets[id]
	delete(t.tickets, id)
	if !ok || t.now().After(tk.expires) {
		return "", false
	}
	return tk.user, true
}

// --------------------------------------------------------------------- node --
type chatMsg struct {
	Room string `json:"room"`
	From string `json:"from"`
	Text string `json:"text"`
	Node string `json:"node"` // which node the sender was connected to
}

type localClient struct {
	user string
	room string
	send chan []byte
}

type Node struct {
	id      string
	broker  Broker
	tickets *ticketStore
	tokens  map[string]string // bearer token -> user (stand-in for your real auth)

	mu      sync.Mutex
	clients map[*localClient]struct{}
	joined  map[string]bool // rooms this node is subscribed to
	ctx     context.Context
}

func (n *Node) mux() http.Handler {
	mux := http.NewServeMux()

	// Step 1: ordinary authenticated HTTP call that mints a ticket.
	mux.HandleFunc("POST /ws-ticket", func(w http.ResponseWriter, r *http.Request) {
		user, ok := n.tokens[strings.TrimPrefix(r.Header.Get("Authorization"), "Bearer ")]
		if !ok {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		json.NewEncoder(w).Encode(map[string]any{"ticket": n.tickets.issue(user, 30*time.Second), "expires_in": 30})
	})

	// Step 2: the WebSocket, authenticated by burning the ticket.
	mux.HandleFunc("GET /ws", func(w http.ResponseWriter, r *http.Request) {
		user, ok := n.tickets.redeem(r.URL.Query().Get("ticket"))
		if !ok {
			http.Error(w, "invalid, used or expired ticket", http.StatusUnauthorized) // refuse BEFORE upgrading
			return
		}
		c, err := websocket.Accept(w, r, &websocket.AcceptOptions{OriginPatterns: []string{"app.example.com"}})
		if err != nil {
			return
		}
		defer c.CloseNow()
		lc := &localClient{user: user, room: r.URL.Query().Get("room"), send: make(chan []byte, 32)}
		n.join(lc)
		defer n.leave(lc)

		ctx, cancel := context.WithCancel(r.Context())
		defer cancel()
		go func() { // writer
			for {
				select {
				case m := <-lc.send:
					if c.Write(ctx, websocket.MessageText, m) != nil {
						cancel()
						return
					}
				case <-ctx.Done():
					return
				}
			}
		}()
		for { // reader: every message goes to the BROKER, never straight to local sockets
			_, data, err := c.Read(ctx)
			if err != nil {
				return
			}
			msg, _ := json.Marshal(chatMsg{Room: lc.room, From: user, Text: string(data), Node: n.id})
			n.broker.Publish("room:"+lc.room, msg)
		}
	})
	return mux
}

func (n *Node) join(c *localClient) {
	n.mu.Lock()
	n.clients[c] = struct{}{}
	first := !n.joined[c.room]
	n.joined[c.room] = true
	n.mu.Unlock()
	if first { // subscribe to the room ONCE per node, however many local clients are in it
		ch := n.broker.Subscribe(n.ctx, "room:"+c.room)
		go func() {
			for m := range ch {
				n.fanOut(c.room, m)
			}
		}()
	}
}

func (n *Node) leave(c *localClient) {
	n.mu.Lock()
	delete(n.clients, c)
	n.mu.Unlock()
}

func (n *Node) fanOut(room string, msg []byte) {
	n.mu.Lock()
	defer n.mu.Unlock()
	for c := range n.clients {
		if c.room == room {
			select {
			case c.send <- msg:
			default: // slow local client: evict/drop policy as in lab 03
			}
		}
	}
}

func (n *Node) localCount() int {
	n.mu.Lock()
	defer n.mu.Unlock()
	return len(n.clients)
}

// -------------------------------------------------------------------- demo ---
func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	broker := newMemBroker()
	fakeNow := time.Now()
	tickets := &ticketStore{tickets: map[string]ticket{}, now: func() time.Time { return fakeNow }}
	tokens := map[string]string{"tok-ana": "ana", "tok-ben": "ben", "tok-cy": "cy"}

	start := func(id string) (*Node, string) {
		n := &Node{id: id, broker: broker, tickets: tickets, tokens: tokens,
			clients: map[*localClient]struct{}{}, joined: map[string]bool{}, ctx: ctx}
		ln, _ := net.Listen("tcp", "127.0.0.1:0")
		go http.Serve(ln, n.mux())
		return n, ln.Addr().String()
	}
	node1, addr1 := start("node-1")
	node2, addr2 := start("node-2")

	getTicket := func(addr, token string) (string, int) {
		req, _ := http.NewRequest("POST", "http://"+addr+"/ws-ticket", nil)
		req.Header.Set("Authorization", "Bearer "+token)
		res, err := http.DefaultClient.Do(req)
		must(err == nil, "ticket request")
		defer res.Body.Close()
		var body struct{ Ticket string }
		json.NewDecoder(res.Body).Decode(&body)
		return body.Ticket, res.StatusCode
	}
	connect := func(addr, ticketID, room string) (*websocket.Conn, *http.Response, error) {
		return websocket.Dial(ctx, "ws://"+addr+"/ws?room="+room+"&ticket="+ticketID,
			&websocket.DialOptions{HTTPHeader: http.Header{"Origin": {"https://app.example.com"}}})
	}

	fmt.Println("== 1. one-time tickets ==")
	_, code := getTicket(addr1, "tok-bad")
	fmt.Println("  bad bearer token         -> ticket request status", code)
	must(code == 401, "no ticket without auth")
	tk, code := getTicket(addr1, "tok-ana")
	fmt.Printf("  good bearer token        -> %d, ticket %s...\n", code, tk[:8])
	c, _, err := connect(addr1, tk, "go")
	must(err == nil, "first use works")
	fmt.Println("  first use of the ticket  -> connected")
	_, resp, err := connect(addr1, tk, "go")
	fmt.Printf("  SAME ticket again        -> refused in handshake (HTTP %d): replay is useless\n", resp.StatusCode)
	must(err != nil && resp.StatusCode == 401, "replay refused")
	old, _ := getTicket(addr1, "tok-ben")
	fakeNow = fakeNow.Add(31 * time.Second) // time passes...
	_, resp, err = connect(addr1, old, "go")
	fmt.Printf("  ticket used after 31s    -> refused (HTTP %d): expired\n", resp.StatusCode)
	must(err != nil && resp.StatusCode == 401, "expired refused")

	fmt.Println("\n== 2. Origin allow-list ==")
	tk, _ = getTicket(addr1, "tok-cy")
	_, resp, err = websocket.Dial(ctx, "ws://"+addr1+"/ws?room=go&ticket="+tk,
		&websocket.DialOptions{HTTPHeader: http.Header{"Origin": {"https://evil.example.net"}}})
	fmt.Printf("  Origin: evil.example.net -> HTTP %d\n", resp.StatusCode)
	must(err != nil && resp.StatusCode == 403, "bad origin refused")

	fmt.Println("\n== 3. two nodes, one room: a message crosses servers through the broker ==")
	tkB, _ := getTicket(addr2, "tok-ben")
	ben, _, err := connect(addr2, tkB, "go") // Ben is on NODE 2, Ana (c) is on NODE 1
	must(err == nil, "ben connects")
	tkC, _ := getTicket(addr2, "tok-cy")
	cy, _, err := connect(addr2, tkC, "py") // Cy is on node 2 but in ANOTHER room
	must(err == nil, "cy connects")
	time.Sleep(150 * time.Millisecond)
	fmt.Printf("  local connections: node-1 = %d, node-2 = %d\n", node1.localCount(), node2.localCount())

	c.Write(ctx, websocket.MessageText, []byte("hello from node-1")) // Ana on node-1
	rctx, rcancel := context.WithTimeout(ctx, 2*time.Second)
	_, data, err := ben.Read(rctx)
	rcancel()
	must(err == nil, fmt.Sprint(err))
	var m chatMsg
	json.Unmarshal(data, &m)
	fmt.Printf("  Ben (node-2) received: %+v\n", m)
	must(m.From == "ana" && m.Node == "node-1" && m.Text == "hello from node-1", "cross-node delivery")

	rctx, rcancel = context.WithTimeout(ctx, 300*time.Millisecond)
	_, _, err = cy.Read(rctx)
	rcancel()
	must(err != nil, "Cy (other room) must not receive it")
	fmt.Println("  Cy (node-2, other room) received nothing - rooms are isolated across nodes too")

	fmt.Println("\n== 4. the sender also hears the fan-out (chat clients usually dedupe by sender) ==")
	rctx, rcancel = context.WithTimeout(ctx, time.Second)
	_, data, err = c.Read(rctx)
	rcancel()
	must(err == nil, "Ana hears her own message via the broker")
	fmt.Println("  Ana received her own message through the broker:", string(data)[:40]+"...")
	fmt.Println("  (this is the price of a single path: ALL delivery goes through the broker. Filter by `from` on the client)")

	fmt.Println("\nLoad-balancer checklist for WebSockets")
	for _, l := range []string{
		"forward the Upgrade and Connection headers (nginx: proxy_set_header Upgrade $http_upgrade; Connection \"upgrade\")",
		"raise idle/read timeouts far above the default 60s, and heartbeat more often than the timeout",
		"terminate TLS (wss://) at the balancer or the node; never serve ws:// on the public internet",
		"do NOT rely on sticky sessions for correctness - a dropped socket may reconnect to any node (that is what the broker is for)",
		"drain nodes on deploy: stop accepting, send 1001 to clients (lab 04), let them reconnect with jitter",
	} {
		fmt.Println("  -", l)
	}
	fmt.Println("\nOK")
}
