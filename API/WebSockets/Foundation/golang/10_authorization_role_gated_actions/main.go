/*
FOUNDATION LEVEL 10 - Authorization: what this connection is allowed to DO
==============================================================================
Level 09 answered "who is this?" once, at the door. Authorization answers a
different question - "may they do THIS?" - and it must be answered again for
every single message, because different messages demand different rights.

That split is more visible here than in REST. A REST server checks permissions
per request, so authentication and authorization tend to run back to back in
the same middleware and blur together. In a WebSocket the two are separated in
TIME: identity is established once, at connect; permission is evaluated over
and over, per message, for the hours that follow. Identity is a property of the
connection; permission is a property of the action.

The other WebSocket-specific rule: a refusal is a MESSAGE, not a disconnect.
REST has a natural place to put "no" - a 403 response, and the request is over.
Here, the client is still sitting on an open connection, so you must answer on
it. Silently ignoring a forbidden message is the worst option of all: the
client cannot tell "denied" from "lost".

You will learn
  - authentication (level 09) vs authorization: recognised vs permitted, and
    why 401's WebSocket analogue happens at connect while 403's happens per message
  - a permission table mapping message type -> allowed roles, kept as DATA
    rather than scattered `if role == ...` checks, so the policy is auditable
  - replying with an error message on the SAME connection, never a silent drop
  - that the connection stays fully usable after a refusal - the client can go
    straight on doing the things it IS allowed to do
  - when a refusal SHOULD escalate to a close: repeated abuse, which is a
    statement about the client rather than about one message (close 1008)

Run it   go run ./WebSockets/Foundation/golang/10_authorization_role_gated_actions
*/
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net"
	"net/http"
	"sort"
	"time"

	"github.com/coder/websocket"
	"github.com/coder/websocket/wsjson"
)

type identity struct {
	User string `json:"user"`
	Role string `json:"role"`
}

var tokens = map[string]identity{
	"alice-token": {User: "alice", Role: "admin"},
	"bob-token":   {User: "bob", Role: "viewer"},
}

// The whole authorization policy, in one readable place.
var permissions = map[string][]string{
	"read":      {"admin", "viewer"},
	"broadcast": {"admin"}, // admin-only: it reaches every other client
	"kick":      {"admin"}, // admin-only: it disconnects someone
}

const strikeLimit = 3 // forbidden attempts tolerated before we stop being polite

type ctxKey string

const userCtxKey ctxKey = "user"

type message struct {
	Type    string `json:"type"`
	Payload any    `json:"payload"`
}

type errorPayload struct {
	Code   string `json:"code"`
	Detail string `json:"detail"`
}

func allowed(kind, role string) ([]string, bool) {
	roles := permissions[kind]
	for _, r := range roles {
		if r == role {
			return roles, true
		}
	}
	sorted := append([]string(nil), roles...)
	sort.Strings(sorted)
	return sorted, false
}

// Level 09's job, done: authenticate before the upgrade.
func withAuthentication(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		id, ok := tokens[r.URL.Query().Get("token")]
		if !ok {
			http.Error(w, "invalid token", http.StatusUnauthorized)
			return
		}
		next.ServeHTTP(w, r.WithContext(context.WithValue(r.Context(), userCtxKey, id)))
	})
}

func authorizingHandler(w http.ResponseWriter, r *http.Request) {
	me := r.Context().Value(userCtxKey).(identity)

	c, err := websocket.Accept(w, r, nil)
	if err != nil {
		return
	}
	defer c.CloseNow()

	strikes := 0
	for {
		rctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
		_, data, err := c.Read(rctx)
		cancel()
		if err != nil {
			return
		}

		var in message
		json.Unmarshal(data, &in)

		roles, ok := allowed(in.Type, me.Role)
		if !ok {
			strikes++
			fmt.Printf("  [server] DENIED %s (%s) -> %q  [strike %d/%d]\n",
				me.User, me.Role, in.Type, strikes, strikeLimit)
			detail := fmt.Sprintf("role %q may not %q; allowed: %v", me.Role, in.Type, roles)
			if len(roles) == 0 {
				detail = fmt.Sprintf("role %q may not %q; allowed: nobody", me.Role, in.Type)
			}
			// The refusal travels back down the same pipe the request came up.
			if wsjson.Write(r.Context(), c, message{
				Type:    "error",
				Payload: errorPayload{Code: "forbidden", Detail: detail},
			}) != nil {
				return
			}
			if strikes >= strikeLimit {
				// Now we are judging the CLIENT, not the message - so a close
				// is the right response, where a single denial was not.
				c.Close(websocket.StatusPolicyViolation, "too many forbidden attempts")
				return
			}
			continue
		}

		fmt.Printf("  [server] ALLOWED %s (%s) -> %q\n", me.User, me.Role, in.Type)
		if wsjson.Write(r.Context(), c, message{
			Type:    in.Type,
			Payload: fmt.Sprintf("%s performed by %s", in.Type, me.User),
		}) != nil {
			return
		}
	}
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

// decoded is `message` with the payload left raw, so an error payload and a
// string payload can both be read out of one reply shape.
type decoded struct {
	Type    string          `json:"type"`
	Payload json.RawMessage `json:"payload"`
}

func (d decoded) text() string {
	var s string
	json.Unmarshal(d.Payload, &s)
	return s
}

func (d decoded) err() errorPayload {
	var e errorPayload
	json.Unmarshal(d.Payload, &e)
	return e
}

func demo(base string) {
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()

	dial := func(token string) *websocket.Conn {
		c, _, err := websocket.Dial(ctx, base+"?token="+token, nil)
		must(err == nil, fmt.Sprint(err))
		return c
	}
	call := func(c *websocket.Conn, kind string) decoded {
		must(wsjson.Write(ctx, c, message{Type: kind}) == nil, "write")
		var got decoded
		must(wsjson.Read(ctx, c, &got) == nil, "read")
		return got
	}

	fmt.Println("== the admin may do everything ==")
	alice := dial("alice-token")
	for _, kind := range []string{"read", "broadcast", "kick"} {
		got := call(alice, kind)
		fmt.Printf("  alice %-10s -> %s: %s\n", kind, got.Type, got.text())
		must(got.Type == kind, kind)
	}
	must(alice.Close(websocket.StatusNormalClosure, "done") == nil, "close")

	fmt.Println("\n== the viewer is authenticated, but not permitted ==")
	bob := dial("bob-token")
	// Identity is not in question - bob got through level 09's door.
	got := call(bob, "read")
	fmt.Printf("  bob   read       -> %s: %s\n", got.Type, got.text())
	must(got.Type == "read", "read allowed")

	got = call(bob, "broadcast")
	fmt.Printf("  bob   broadcast  -> %s: %s\n", got.Type, got.err().Detail)
	must(got.Type == "error" && got.err().Code == "forbidden", "forbidden")

	// THE POINT: the refusal did not end the session. bob is still here, still
	// authenticated, and can carry on with what he may do.
	got = call(bob, "read")
	fmt.Printf("  bob   read       -> %s: %s   (still connected after being refused)\n",
		got.Type, got.text())
	must(got.Type == "read", "connection survived the refusal")
	must(bob.Close(websocket.StatusNormalClosure, "done") == nil, "close")

	fmt.Println("\n== repeated abuse IS about the client, so it earns a close ==")
	bob = dial("bob-token")
	for attempt := 1; attempt <= strikeLimit; attempt++ {
		got = call(bob, "kick")
		fmt.Printf("  attempt %d -> %s\n", attempt, got.err().Code)
		must(got.Type == "error", "forbidden")
	}
	_, _, err := bob.Read(ctx)
	must(err != nil, "expected a close after the strike limit")
	fmt.Printf("  after %d strikes -> closed %d\n", strikeLimit, websocket.CloseStatus(err))
	must(websocket.CloseStatus(err) == websocket.StatusPolicyViolation, "expected 1008")
	bob.CloseNow()

	fmt.Println("\nOK")
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, withAuthentication(http.HandlerFunc(authorizingHandler)))
	demo("ws://" + ln.Addr().String())
}
