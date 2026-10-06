/*
FOUNDATION LEVEL 11 (capstone) - A real chat-room server
============================================================
Everything from levels 00-10, assembled into one program that does something
you would actually ship: a chat server with rooms, authentication, broadcast,
a moderator action, and clean shutdown.

Nothing new is introduced here. That is the point - if this file reads as
obvious, Foundation has done its job and ../../../labs/ is the next step, not a
jump. Read it as a map of where each earlier level ended up:

	level 00  one handler per connection, living for the whole session
	level 02  every message is {"type": ..., "payload": ...}, routed on `type`
	level 03  a registry of live connections, so we can fan out to a room
	level 04  the server pushes join/leave notices nobody asked for
	level 05  bad messages get an error reply, never a dropped session
	level 06  every ending has a deliberate close code
	level 07  a keepalive ping loop, and a deadline enforced by a timer so the
	          close frame can actually be sent
	level 08  connection-scoped logging, message-scoped recovery
	level 09  a token in the query string, checked before the upgrade
	level 10  `kick` is admin-only, and refusals come back as messages

You will learn
  - how the pieces compose: auth decides WHO, the room registry decides WHERE,
    the type table decides WHAT, and the role table decides WHETHER
  - per-room fan-out rather than per-server: a map of rooms to member sets
  - that state (who is in which room) lives naturally in the server's memory
    because connections are long-lived - the thing REST forbids by design
  - a moderation action that closes SOMEONE ELSE'S connection with a code
  - that one mutex protects the rooms, and writes happen outside it

Run it        go run ./WebSockets/Foundation/golang/11_capstone_chat_room_server
Keep serving  go run ./WebSockets/Foundation/golang/11_capstone_chat_room_server -serve
Then          npx wscat -c "ws://localhost:8080/ws?token=alice-token&room=lobby"
*/
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net"
	"net/http"
	"sort"
	"sync"
	"time"

	"github.com/coder/websocket"
	"github.com/coder/websocket/wsjson"
)

type identity struct {
	User string `json:"user"`
	Role string `json:"role"`
	Room string `json:"room"`
}

var tokens = map[string]identity{
	"alice-token": {User: "alice", Role: "admin"},
	"bob-token":   {User: "bob", Role: "member"},
	"carol-token": {User: "carol", Role: "member"},
}

var permissions = map[string][]string{
	"say":  {"admin", "member"},
	"who":  {"admin", "member"},
	"kick": {"admin"}, // moderation: members must not have this
}

type message struct {
	Type    string          `json:"type"`
	Payload json.RawMessage `json:"payload"`
}

type out struct {
	Type    string `json:"type"`
	Payload any    `json:"payload"`
}

type said struct {
	From string `json:"from"`
	Text string `json:"text"`
}

type errPayload struct {
	Code   string `json:"code"`
	Detail string `json:"detail"`
}

// ---------------------------------------------------------------- member ----
// One connected client. The write mutex matters because the room fan-out, the
// keepalive loop and this member's own reply path can all write at once.
type member struct {
	conn *websocket.Conn
	id   identity
	mu   sync.Mutex
}

func (m *member) send(ctx context.Context, v any) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	wctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	return wsjson.Write(wctx, m.conn, v)
}

// ------------------------------------------------------------------ hub -----
type hub struct {
	mu    sync.Mutex
	rooms map[string]map[*member]struct{}
}

func newHub() *hub {
	return &hub{rooms: make(map[string]map[*member]struct{})}
}

func (h *hub) join(m *member) int {
	h.mu.Lock()
	defer h.mu.Unlock()
	if h.rooms[m.id.Room] == nil {
		h.rooms[m.id.Room] = make(map[*member]struct{})
	}
	h.rooms[m.id.Room][m] = struct{}{}
	return len(h.rooms[m.id.Room])
}

func (h *hub) leave(m *member) int {
	h.mu.Lock()
	defer h.mu.Unlock()
	delete(h.rooms[m.id.Room], m)
	return len(h.rooms[m.id.Room])
}

func (h *hub) membersOf(room string) []*member {
	h.mu.Lock()
	defer h.mu.Unlock()
	list := make([]*member, 0, len(h.rooms[room]))
	for m := range h.rooms[room] {
		list = append(list, m)
	}
	return list
}

func (h *hub) occupancy() int {
	h.mu.Lock()
	defer h.mu.Unlock()
	total := 0
	for _, members := range h.rooms {
		total += len(members)
	}
	return total
}

// sendToRoom fans out to one room, writing OUTSIDE the hub lock so a slow
// client cannot stall the whole server (level 03).
func (h *hub) sendToRoom(ctx context.Context, room string, v any, exclude *member) {
	var wg sync.WaitGroup
	for _, m := range h.membersOf(room) {
		if m == exclude {
			continue
		}
		wg.Add(1)
		go func(m *member) {
			defer wg.Done()
			m.send(ctx, v) // a client that just died simply misses this
		}(m)
	}
	wg.Wait()
}

// --------------------------------------------------------------- routing ----
func permitted(kind, role string) bool {
	for _, r := range permissions[kind] {
		if r == role {
			return true
		}
	}
	return false
}

func knownTypes() []string {
	names := make([]string, 0, len(permissions))
	for name := range permissions {
		names = append(names, name)
	}
	sort.Strings(names)
	return names
}

// handleMessage processes ONE message. Returning an error means "this message
// was bad"; the caller turns that into an error reply and keeps the session.
func (h *hub) handleMessage(ctx context.Context, me *member, data []byte) error {
	var in message
	if err := json.Unmarshal(data, &in); err != nil {
		return fmt.Errorf("not valid JSON: %v", err)
	}
	if _, known := permissions[in.Type]; !known {
		return fmt.Errorf("unknown type %q; known: %v", in.Type, knownTypes())
	}
	if !permitted(in.Type, me.id.Role) { // level 10
		return me.send(ctx, out{Type: "error", Payload: errPayload{
			Code:   "forbidden",
			Detail: fmt.Sprintf("role %q may not %q", me.id.Role, in.Type),
		}})
	}

	switch in.Type {
	case "say":
		var text string
		if err := json.Unmarshal(in.Payload, &text); err != nil || text == "" {
			return fmt.Errorf("payload must be a non-empty string")
		}
		h.sendToRoom(ctx, me.id.Room,
			out{Type: "said", Payload: said{From: me.id.User, Text: text}}, nil)

	case "who":
		names := []string{}
		for _, m := range h.membersOf(me.id.Room) {
			names = append(names, m.id.User)
		}
		sort.Strings(names)
		return me.send(ctx, out{Type: "who", Payload: names})

	case "kick":
		var target string
		json.Unmarshal(in.Payload, &target)
		var victim *member
		for _, m := range h.membersOf(me.id.Room) {
			if m.id.User == target {
				victim = m
			}
		}
		if victim == nil {
			return fmt.Errorf("nobody called %q is in %q", target, me.id.Room)
		}
		// Closing someone ELSE's connection, with a code that explains itself.
		victim.conn.Close(websocket.StatusCode(4003), "kicked by "+me.id.User)
		h.sendToRoom(ctx, me.id.Room, out{
			Type:    "kicked",
			Payload: map[string]string{"user": target, "by": me.id.User},
		}, nil)
	}
	return nil
}

// Level 09: authenticate and pick a room BEFORE the upgrade completes.
type ctxKey string

const userCtxKey ctxKey = "user"

func withAuthentication(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		id, ok := tokens[r.URL.Query().Get("token")]
		if !ok {
			http.Error(w, "invalid token", http.StatusUnauthorized)
			return
		}
		id.Room = r.URL.Query().Get("room")
		if id.Room == "" {
			id.Room = "lobby"
		}
		next.ServeHTTP(w, r.WithContext(context.WithValue(r.Context(), userCtxKey, id)))
	})
}

func (h *hub) handler(w http.ResponseWriter, r *http.Request) {
	id := r.Context().Value(userCtxKey).(identity)

	c, err := websocket.Accept(w, r, nil)
	if err != nil {
		return
	}
	defer c.CloseNow()

	me := &member{conn: c, id: id}
	ctx, cancel := context.WithCancel(r.Context())
	defer cancel()

	// Level 08: connection-scoped bookkeeping, outside the message loop.
	fmt.Printf("  [log] JOIN  %s (%s) -> room %q (now %d)\n",
		id.User, id.Role, id.Room, h.join(me))
	defer func() {
		remaining := h.leave(me)
		fmt.Printf("  [log] LEAVE %s (room %q now %d)\n", id.User, id.Room, remaining)
		h.sendToRoom(context.Background(), id.Room, out{Type: "left", Payload: id.User}, me)
	}()

	// Level 04: an unsolicited push to everyone already here.
	h.sendToRoom(ctx, id.Room, out{Type: "joined", Payload: id.User}, me)

	// Level 07: keepalive beside the read loop.
	go func() {
		t := time.NewTicker(20 * time.Second)
		defer t.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-t.C:
				pctx, pcancel := context.WithTimeout(ctx, 10*time.Second)
				err := c.Ping(pctx)
				pcancel()
				if err != nil && ctx.Err() == nil {
					c.CloseNow()
					cancel()
					return
				}
			}
		}
	}()

	for {
		_, data, err := c.Read(ctx)
		if err != nil {
			return
		}
		// Level 05 + 08: one bad message must not cost this user the session.
		if err := h.handleMessage(ctx, me, data); err != nil {
			if me.send(ctx, out{Type: "error", Payload: errPayload{
				Code: "bad_message", Detail: err.Error(),
			}}) != nil {
				return
			}
		}
	}
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

type reply struct {
	Type    string          `json:"type"`
	Payload json.RawMessage `json:"payload"`
}

func (r reply) str() string {
	var s string
	json.Unmarshal(r.Payload, &s)
	return s
}

func (r reply) errp() errPayload {
	var e errPayload
	json.Unmarshal(r.Payload, &e)
	return e
}

func (r reply) names() []string {
	var n []string
	json.Unmarshal(r.Payload, &n)
	return n
}

func demo(base string, h *hub) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	url := func(token, room string) string {
		return fmt.Sprintf("%s/ws?token=%s&room=%s", base, token, room)
	}
	read := func(c *websocket.Conn) reply {
		var got reply
		must(wsjson.Read(ctx, c, &got) == nil, "read")
		return got
	}
	call := func(c *websocket.Conn, kind string, payload any) reply {
		must(wsjson.Write(ctx, c, out{Type: kind, Payload: payload}) == nil, "write")
		return read(c)
	}

	fmt.Println("== an unauthenticated client never gets in (level 09) ==")
	_, resp, err := websocket.Dial(ctx, url("forged", "lobby"), nil)
	must(err != nil && resp != nil && resp.StatusCode == http.StatusUnauthorized, "401")
	fmt.Printf("  forged token -> HTTP %d, upgrade refused\n", resp.StatusCode)

	fmt.Println("\n== three authenticated clients join the lobby ==")
	dial := func(token string) *websocket.Conn {
		c, _, err := websocket.Dial(ctx, url(token, "lobby"), nil)
		must(err == nil, fmt.Sprint(err))
		return c
	}
	alice := dial("alice-token")
	defer alice.CloseNow()
	bob := dial("bob-token")
	defer bob.CloseNow()
	carol := dial("carol-token")
	defer carol.CloseNow()

	// alice and bob each get a "joined" push for the people after them.
	must(read(alice).str() == "bob", "alice saw bob join")
	must(read(alice).str() == "carol", "alice saw carol join")
	must(read(bob).str() == "carol", "bob saw carol join")

	got := call(alice, "who", nil)
	fmt.Println("  who -> ", got.names())
	must(len(got.names()) == 3, "three members")

	fmt.Println("\n== bob says something; everyone in the room hears it (level 03) ==")
	must(wsjson.Write(ctx, bob, out{Type: "say", Payload: "hello lobby"}) == nil, "write")
	for i, c := range []*websocket.Conn{alice, bob, carol} {
		name := []string{"alice", "bob  ", "carol"}[i]
		m := read(c)
		var s said
		json.Unmarshal(m.Payload, &s)
		fmt.Printf("  %s <- %s: {from:%s text:%s}\n", name, m.Type, s.From, s.Text)
		must(m.Type == "said" && s.From == "bob" && s.Text == "hello lobby", "broadcast")
	}

	fmt.Println("\n== a bad message costs one message, not the session (level 05) ==")
	got = call(bob, "say", "")
	fmt.Println("  empty say  ->", got.errp().Detail)
	must(got.errp().Code == "bad_message", "bad payload")
	got = call(bob, "teleport", nil)
	fmt.Println("  bad type   ->", got.errp().Detail)
	must(got.errp().Code == "bad_message", "unknown type")

	fmt.Println("\n== moderation is admin-only (level 10) ==")
	got = call(bob, "kick", "carol")
	fmt.Println("  bob kicking carol   ->", got.errp().Detail)
	must(got.errp().Code == "forbidden", "forbidden")

	// carol is untouched: a refused kick has no victim.
	got = call(carol, "who", nil)
	fmt.Println("  carol is still here:", got.names())
	must(len(got.names()) == 3, "carol survived")

	fmt.Println("\n== alice CAN kick, and carol learns why (level 06) ==")
	must(wsjson.Write(ctx, alice, out{Type: "kick", Payload: "carol"}) == nil, "write")
	_, _, err = carol.Read(ctx)
	must(err != nil, "expected carol to be closed")
	fmt.Printf("  carol closed with %d\n", websocket.CloseStatus(err))
	must(websocket.CloseStatus(err) == websocket.StatusCode(4003), "expected 4003")

	// The room gets TWO pushes now: the "kicked" announcement, and the "left"
	// notice from carol's own deferred cleanup. Their relative order is not
	// guaranteed - two independent goroutines are writing - so a correct
	// client handles events as a SET, never as a script.
	for i, c := range []*websocket.Conn{alice, bob} {
		name := []string{"alice", "bob  "}[i]
		seen := map[string]bool{}
		for j := 0; j < 2; j++ {
			seen[read(c).Type] = true
		}
		kinds := []string{}
		for k := range seen {
			kinds = append(kinds, k)
		}
		sort.Strings(kinds)
		fmt.Printf("  %s saw: %v\n", name, kinds)
		must(seen["kicked"] && seen["left"], "both notices")
	}

	got = call(alice, "who", nil)
	fmt.Println("  who -> ", got.names())
	must(len(got.names()) == 2, "two left")

	must(alice.Close(websocket.StatusNormalClosure, "done") == nil, "close")
	must(bob.Close(websocket.StatusNormalClosure, "done") == nil, "close")

	fmt.Println("\n== rooms are empty again once everyone leaves ==")
	deadline := time.Now().Add(5 * time.Second)
	for h.occupancy() > 0 && time.Now().Before(deadline) {
		time.Sleep(10 * time.Millisecond)
	}
	fmt.Printf("  occupants left across all rooms: %d\n", h.occupancy())
	must(h.occupancy() == 0, "rooms drained")

	fmt.Println("\nOK")
}

func main() {
	serveFlag := flag.Bool("serve", false, "listen on :8080 instead of running the demo")
	flag.Parse()

	h := newHub()
	mux := http.NewServeMux()
	mux.Handle("/ws", withAuthentication(http.HandlerFunc(h.handler)))

	if *serveFlag {
		fmt.Println("listening on ws://localhost:8080/ws")
		fmt.Println(`  try: npx wscat -c "ws://localhost:8080/ws?token=alice-token&room=lobby"`)
		fmt.Println(`  then: {"type":"say","payload":"hi"}   /   {"type":"who"}`)
		log.Fatal(http.ListenAndServe("127.0.0.1:8080", mux))
	}

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, mux)
	demo("ws://"+ln.Addr().String(), h)
}
