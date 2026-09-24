/*
FOUNDATION LEVEL 02 - A tiny message protocol: routing by "type", not by URL
================================================================================
Here is a problem REST simply does not have. In REST, every request carries its
own address: `GET /books/7` says what to do and what to do it to. A WebSocket
message carries NO url and NO verb - the URL was used up once, during the
handshake. So how does one connection support twenty different operations?

You invent a protocol. Overwhelmingly the convention is a JSON envelope:

	{"type": "<what to do>", "payload": <the data for it>}

and the server switches on `type`. That `type` field is this level's whole
point: it is the WebSocket equivalent of REST's method+path routing, except
YOU define the vocabulary instead of inheriting HTTP's.

You will learn
  - why a WebSocket needs an application-level envelope at all
  - the {"type": ..., "payload": ...} convention, and routing on `type`
  - wsjson.Read / wsjson.Write: one JSON value = exactly one WebSocket message
  - json.RawMessage for the payload, so you can decode it per type - the
    envelope is decoded once, the body only when you know what it should be
  - an unknown `type` is an application-level error message, NOT a closed
    connection: the session survives, unlike REST where a 404 ends the request
  - where this goes next: matching replies to requests by id is JSON-RPC,
    which ../../../labs/golang/02_coder_websocket_json_rpc builds properly

Run it   go run ./WebSockets/Foundation/golang/02_message_protocol_typed_routing
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
	"strings"
	"time"

	"github.com/coder/websocket"
	"github.com/coder/websocket/wsjson"
)

// The envelope. Only `type` is decoded eagerly; the payload stays as raw bytes
// until a route that knows its shape decodes it.
type envelope struct {
	Type    string          `json:"type"`
	Payload json.RawMessage `json:"payload"`
}

type reply struct {
	Type    string `json:"type"`
	Payload any    `json:"payload"`
}

// Each route decodes its own payload shape and returns what to reply with.
// This is a dispatch TABLE, exactly like a REST router's path -> handler map,
// except the key is a made-up string instead of a URL.
var routes = map[string]func(json.RawMessage) (any, error){
	"upper": func(raw json.RawMessage) (any, error) {
		var p struct{ Text string }
		if err := json.Unmarshal(raw, &p); err != nil {
			return nil, err
		}
		return strings.ToUpper(p.Text), nil
	},
	"sum": func(raw json.RawMessage) (any, error) {
		var p struct{ Numbers []float64 }
		if err := json.Unmarshal(raw, &p); err != nil {
			return nil, err
		}
		total := 0.0
		for _, n := range p.Numbers {
			total += n
		}
		return total, nil
	},
	"reverse": func(raw json.RawMessage) (any, error) {
		var p struct{ Text string }
		if err := json.Unmarshal(raw, &p); err != nil {
			return nil, err
		}
		runes := []rune(p.Text)
		for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
			runes[i], runes[j] = runes[j], runes[i]
		}
		return string(runes), nil
	},
}

func knownTypes() []string {
	names := make([]string, 0, len(routes))
	for name := range routes {
		names = append(names, name)
	}
	sort.Strings(names)
	return names
}

func protocolHandler(w http.ResponseWriter, r *http.Request) {
	c, err := websocket.Accept(w, r, nil)
	if err != nil {
		return
	}
	defer c.CloseNow()

	for {
		ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
		var msg envelope
		err := wsjson.Read(ctx, c, &msg) // one JSON message off the pipe
		cancel()
		if err != nil {
			return
		}

		route, ok := routes[msg.Type]
		if !ok {
			// The client asked for an operation we do not have. In REST this
			// would be a 404 and the request would be over. Here the
			// connection is long-lived and valuable, so we answer and keep
			// listening.
			wctx, wcancel := context.WithTimeout(r.Context(), 5*time.Second)
			wsjson.Write(wctx, c, reply{
				Type:    "error",
				Payload: fmt.Sprintf("unknown type %q; known: %v", msg.Type, knownTypes()),
			})
			wcancel()
			continue
		}

		result, err := route(msg.Payload)
		out := reply{Type: msg.Type, Payload: result}
		if err != nil {
			out = reply{Type: "error", Payload: err.Error()}
		}
		// Echoing the type back is what lets the client correlate a reply with
		// what it asked for - there is no HTTP request/response pairing here.
		wctx, wcancel := context.WithTimeout(r.Context(), 5*time.Second)
		err = wsjson.Write(wctx, c, out)
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
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	c, _, err := websocket.Dial(ctx, url, nil)
	must(err == nil, fmt.Sprint(err))
	defer c.CloseNow()

	call := func(kind string, payload any) reply {
		must(wsjson.Write(ctx, c, map[string]any{"type": kind, "payload": payload}) == nil, "write")
		var got reply
		must(wsjson.Read(ctx, c, &got) == nil, "read")
		return got
	}

	fmt.Println("== three different operations, one connection, one handshake ==")
	r1 := call("upper", map[string]any{"text": "websockets"})
	fmt.Printf("  -> {type: upper}     <- {type: %s, payload: %v}\n", r1.Type, r1.Payload)
	must(r1.Type == "upper" && r1.Payload == "WEBSOCKETS", "upper")

	r2 := call("sum", map[string]any{"numbers": []int{1, 2, 3, 4}})
	fmt.Printf("  -> {type: sum}       <- {type: %s, payload: %v}\n", r2.Type, r2.Payload)
	must(r2.Type == "sum" && r2.Payload == 10.0, "sum")

	r3 := call("reverse", map[string]any{"text": "stressed"})
	fmt.Printf("  -> {type: reverse}   <- {type: %s, payload: %v}\n", r3.Type, r3.Payload)
	must(r3.Type == "reverse" && r3.Payload == "desserts", "reverse")

	fmt.Println("\n== an unknown type is an ERROR MESSAGE, not a dead connection ==")
	r4 := call("launch_missiles", map[string]any{})
	fmt.Printf("  <- {type: %s, payload: %v}\n", r4.Type, r4.Payload)
	must(r4.Type == "error", "error reply")

	// Still alive, still in the same session - that is the difference between
	// "this message was bad" and "this client is bad".
	r5 := call("upper", map[string]any{"text": "still here"})
	fmt.Printf("  <- {type: %s, payload: %v}   (same connection, unharmed)\n", r5.Type, r5.Payload)
	must(r5.Payload == "STILL HERE", "connection survived")

	must(c.Close(websocket.StatusNormalClosure, "done") == nil, "close")
	fmt.Println("\nOK")
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, http.HandlerFunc(protocolHandler))
	demo("ws://" + ln.Addr().String())
}
