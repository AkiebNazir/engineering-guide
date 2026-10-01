/*
FOUNDATION LEVEL 09 - Authentication: checked once, at the door
===================================================================
Authentication answers exactly ONE question: "do we recognise this peer at
all?" It says nothing about what they may do - that is level 10, authorization,
and it is deliberately a separate idea.

What is different from REST is WHEN. A REST client proves who it is on every
single request, so there is nowhere else to put the check. A WebSocket client
proves who it is ONCE, and that identity then covers every message for the
entire life of the connection - possibly hours. Authenticate at the door and
you never pay for it again; get it wrong and an imposter has a long, warm seat.

TWO PLACES TO DO IT, and both are shown below:

	A) DURING the handshake, before websocket.Accept is ever called. The best
	   option, and in Go it is beautifully simple: the handler is an ordinary
	   http.Handler, so you check the request and http.Error out of it. An
	   unauthenticated peer never gets a WebSocket at all, just an HTTP 401.
	   Downside: browsers cannot set headers on `new WebSocket(...)`, so the
	   token has to ride in the query string (and therefore in access logs) or
	   in a cookie, or be a short-lived single-use "ticket".
	B) As the FIRST MESSAGE after connecting. The connection exists but is not
	   usable until it arrives; a deadline stops an anonymous peer squatting.
	   This is what browsers usually end up doing.

You will learn
  - that a WebSocket endpoint being an http.Handler means REST's entire auth
    toolkit (middleware, headers, cookies) applies unchanged before the upgrade
  - that a client sees a failed upgrade as a Dial error plus an *http.Response,
    not a closed WebSocket - because there never was a WebSocket
  - the first-message variant, and closing with 1008 when the token is bad
  - why an auth deadline is mandatory in variant B (else you have a free
    resource for anyone who can open a socket)
  - attaching the identity to the request context, so every later message and
    level 10's role check can use it without re-verifying anything

Run it   go run ./WebSockets/Foundation/golang/09_authentication_at_connect_time
*/
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net"
	"net/http"
	"time"

	"github.com/coder/websocket"
	"github.com/coder/websocket/wsjson"
)

type identity struct {
	User string `json:"user"`
	Role string `json:"role"`
}

// A stand-in for "who is allowed in". A real system verifies a signed JWT or
// looks the token up in a store - see
// ../../../labs/golang/05_scaling_pubsub_and_tickets for the ticket pattern.
var tokens = map[string]identity{
	"alice-token": {User: "alice", Role: "admin"},
	"bob-token":   {User: "bob", Role: "viewer"},
}

type ctxKey string

const userCtxKey ctxKey = "user"

const authDeadline = 300 * time.Millisecond // time to send the auth message (variant B)

// =========================== variant A: at the door ===========================
//
// Ordinary net/http middleware. Note it runs BEFORE any websocket code exists:
// if the token is bad, the request is answered with a plain HTTP 401 and the
// upgrade never happens.
func withAuthentication(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		token := r.URL.Query().Get("token")
		id, ok := tokens[token]
		if !ok {
			fmt.Printf("  [server] refusing upgrade: token=%q\n", token)
			http.Error(w, "invalid or missing token", http.StatusUnauthorized)
			return
		}
		// Now every message for the rest of this connection's life is
		// attributable, with no further token checks.
		fmt.Printf("  [server] upgrade allowed for %s (%s)\n", id.User, id.Role)
		next.ServeHTTP(w, r.WithContext(context.WithValue(r.Context(), userCtxKey, id)))
	})
}

func gatedHandler(w http.ResponseWriter, r *http.Request) {
	// If this line runs, the peer is authenticated. There is no auth code here.
	id := r.Context().Value(userCtxKey).(identity)

	c, err := websocket.Accept(w, r, nil)
	if err != nil {
		return
	}
	defer c.CloseNow()

	for {
		ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
		_, _, err := c.Read(ctx)
		cancel()
		if err != nil {
			return
		}
		if wsjson.Write(r.Context(), c, id) != nil {
			return
		}
	}
}

// ====================== variant B: first message after connect ======================
type authMessage struct {
	Type    string `json:"type"`
	Payload string `json:"payload"`
}

type reply struct {
	Type    string `json:"type"`
	Payload any    `json:"payload"`
}

func firstMessageAuthHandler(w http.ResponseWriter, r *http.Request) {
	c, err := websocket.Accept(w, r, nil)
	if err != nil {
		return
	}
	defer c.CloseNow()

	// Without this deadline, anyone could hold connections open for free.
	actx, acancel := context.WithTimeout(r.Context(), authDeadline)
	_, data, err := c.Read(actx)
	timedOut := actx.Err() == context.DeadlineExceeded
	acancel()
	if err != nil {
		if timedOut {
			fmt.Println("  [server] no auth message in time -> closing 1008")
			// The read context expiring has already torn the connection down
			// (see level 07), so the peer will see "no close frame". To send a
			// real code, read with a long context and enforce the deadline
			// with a timer - which is what the capstone (level 11) does.
			c.Close(websocket.StatusPolicyViolation, "authentication timeout")
		}
		return
	}

	var msg authMessage
	json.Unmarshal(data, &msg)
	id, ok := tokens[msg.Payload]
	if msg.Type != "auth" || !ok {
		// 1008 policy violation is the conventional close code for "you failed
		// a rule of this service", authentication very much included.
		c.Close(websocket.StatusPolicyViolation, "authentication failed")
		return
	}

	if wsjson.Write(r.Context(), c, reply{Type: "welcome", Payload: id}) != nil {
		return
	}
	for {
		ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
		_, _, err := c.Read(ctx)
		cancel()
		if err != nil {
			return
		}
		if wsjson.Write(r.Context(), c, reply{Type: "whoami", Payload: id}) != nil {
			return
		}
	}
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func demo(gated, firstMsg string) {
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()

	fmt.Println("== A. authenticated during the handshake: rejected peers get HTTP, not WS ==")
	for _, tc := range []struct{ label, query string }{
		{"no token", ""},
		{"bad token", "?token=forged"},
	} {
		_, resp, err := websocket.Dial(ctx, gated+tc.query, nil)
		must(err != nil, "expected the upgrade to be refused")
		must(resp != nil && resp.StatusCode == http.StatusUnauthorized, "expected 401")
		fmt.Printf("  %-10s -> HTTP %d %s (no WebSocket was ever created)\n",
			tc.label, resp.StatusCode, http.StatusText(resp.StatusCode))
	}

	for _, tc := range []struct{ token, role string }{
		{"alice-token", "admin"},
		{"bob-token", "viewer"},
	} {
		c, _, err := websocket.Dial(ctx, gated+"?token="+tc.token, nil)
		must(err == nil, fmt.Sprint(err))
		must(c.Write(ctx, websocket.MessageText, []byte("who am I?")) == nil, "write")
		var id identity
		must(wsjson.Read(ctx, c, &id) == nil, "read")
		fmt.Printf("  %-12s -> upgraded; server knows us as %+v\n", tc.token, id)
		must(id.Role == tc.role, "role")
		must(c.Close(websocket.StatusNormalClosure, "done") == nil, "close")
	}

	fmt.Println("\n  the identity was checked ONCE and covered the whole session:")
	c, _, err := websocket.Dial(ctx, gated+"?token=alice-token", nil)
	must(err == nil, fmt.Sprint(err))
	for i := 0; i < 3; i++ {
		must(c.Write(ctx, websocket.MessageText, []byte("ping")) == nil, "write")
		var id identity
		must(wsjson.Read(ctx, c, &id) == nil, "read")
		must(id.User == "alice", "still alice")
	}
	fmt.Println("  3 messages, still alice, zero further token checks")
	must(c.Close(websocket.StatusNormalClosure, "done") == nil, "close")

	fmt.Println("\n== B. authenticated by the first message, with a deadline ==")
	c, _, err = websocket.Dial(ctx, firstMsg, nil)
	must(err == nil, fmt.Sprint(err))
	must(wsjson.Write(ctx, c, authMessage{Type: "auth", Payload: "bob-token"}) == nil, "write")
	var welcome reply
	must(wsjson.Read(ctx, c, &welcome) == nil, "read")
	fmt.Printf("  good token  -> {%s %v}\n", welcome.Type, welcome.Payload)
	must(welcome.Type == "welcome", "welcome")
	must(c.Write(ctx, websocket.MessageText, []byte("and now?")) == nil, "write")
	var later reply
	must(wsjson.Read(ctx, c, &later) == nil, "read")
	fmt.Printf("  later message still knows us: {%s %v}\n", later.Type, later.Payload)
	must(c.Close(websocket.StatusNormalClosure, "done") == nil, "close")

	c, _, err = websocket.Dial(ctx, firstMsg, nil)
	must(err == nil, fmt.Sprint(err))
	must(wsjson.Write(ctx, c, authMessage{Type: "auth", Payload: "forged"}) == nil, "write")
	_, _, err = c.Read(ctx)
	must(err != nil, "expected a close")
	fmt.Printf("  bad token   -> closed %d\n", websocket.CloseStatus(err))
	must(websocket.CloseStatus(err) == websocket.StatusPolicyViolation, "expected 1008")
	c.CloseNow()

	c, _, err = websocket.Dial(ctx, firstMsg, nil)
	must(err == nil, fmt.Sprint(err))
	fmt.Printf("  saying nothing for %v...\n", authDeadline)
	_, _, err = c.Read(ctx)
	must(err != nil, "expected the connection to end")
	fmt.Printf("  no auth at all -> connection ended (CloseStatus %d)\n",
		websocket.CloseStatus(err))
	c.CloseNow()

	fmt.Println("\nOK")
}

func main() {
	listen := func(h http.Handler) string {
		ln, err := net.Listen("tcp", "127.0.0.1:0")
		if err != nil {
			log.Fatal(err)
		}
		go http.Serve(ln, h)
		return "ws://" + ln.Addr().String()
	}
	demo(
		listen(withAuthentication(http.HandlerFunc(gatedHandler))),
		listen(http.HandlerFunc(firstMessageAuthHandler)),
	)
}
