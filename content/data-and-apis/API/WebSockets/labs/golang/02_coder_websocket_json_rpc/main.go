/*
LAB 02 (basic) - A real WebSocket server with coder/websocket: JSON messages and clean closes
=============================================================================================
You will learn
  - the standard-library-friendly API:  websocket.Accept(w, r, opts)  inside a normal http.Handler,
    so your existing middleware and routing keep working
  - a tiny request/response protocol over one socket, matched by an "id" (like JSON-RPC):
    client -> {"id": 7, "op": "add", "args": [2, 3]}     server -> {"id": 7, "result": 5}
    this is how you build RPC-style calls on a WebSocket, including error replies
  - wsjson helpers, and ALWAYS passing a context with a timeout to Read/Write
  - subprotocol negotiation: the client offers versions, the server picks one (protocol versioning)
  - limits: SetReadLimit (default is small on purpose)
  - closing with meaning: StatusNormalClosure 1000, StatusUnsupportedData 1003,
    StatusPolicyViolation 1008, StatusMessageTooBig 1009 - and reading them on the other side
    with websocket.CloseStatus(err)
  - the handler must return to free the connection: defer c.CloseNow()

Run it   go run ./WebSockets/labs/golang/02_coder_websocket_json_rpc
*/
package main

import (
	"context"
	"fmt"
	"net"
	"net/http"
	"time"

	"github.com/coder/websocket"
	"github.com/coder/websocket/wsjson"
)

type request struct {
	ID   int       `json:"id"`
	Op   string    `json:"op"`
	Args []float64 `json:"args"`
}

type response struct {
	ID     int      `json:"id"`
	Result *float64 `json:"result,omitempty"`
	Error  string   `json:"error,omitempty"`
}

func handler(w http.ResponseWriter, r *http.Request) {
	c, err := websocket.Accept(w, r, &websocket.AcceptOptions{
		Subprotocols: []string{"calc.v2", "calc.v1"}, // our preference order
		// OriginPatterns: []string{"app.example.com"},  // <- set this in production (default: same host only)
	})
	if err != nil {
		return // Accept already wrote the HTTP error response
	}
	defer c.CloseNow() // safety net: releases the connection even on early returns

	c.SetReadLimit(4 << 10) // 4 KiB per message; larger => close 1009

	if c.Subprotocol() == "" { // the client offered nothing we speak
		c.Close(websocket.StatusPolicyViolation, "client must offer subprotocol calc.v1 or calc.v2")
		return
	}

	for {
		ctx, cancel := context.WithTimeout(r.Context(), 30*time.Second) // idle limit per message
		var req request
		err := wsjson.Read(ctx, c, &req)
		cancel()
		if err != nil {
			// Peer closed normally (1000/1001), sent invalid JSON (the library closes with 1007),
			// or exceeded the read limit (1009). In every case the close frame is already handled;
			// websocket.CloseStatus(err) tells you which one if you want to log it.
			return
		}

		resp := response{ID: req.ID}
		switch {
		case req.Op == "add" && len(req.Args) == 2:
			v := req.Args[0] + req.Args[1]
			resp.Result = &v
		case req.Op == "div" && len(req.Args) == 2:
			if req.Args[1] == 0 {
				resp.Error = "division by zero"
			} else {
				v := req.Args[0] / req.Args[1]
				resp.Result = &v
			}
		case req.Op == "version" && c.Subprotocol() == "calc.v2":
			v := 2.0
			resp.Result = &v
		default:
			resp.Error = fmt.Sprintf("unknown op %q (protocol %s)", req.Op, c.Subprotocol())
		}
		wctx, wcancel := context.WithTimeout(r.Context(), 5*time.Second)
		err = wsjson.Write(wctx, c, resp) // one JSON message = one WebSocket message
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

func main() {
	ln, _ := net.Listen("tcp", "127.0.0.1:0")
	go http.Serve(ln, http.HandlerFunc(handler))
	url := "ws://" + ln.Addr().String()
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	dial := func(protos ...string) (*websocket.Conn, error) {
		c, _, err := websocket.Dial(ctx, url, &websocket.DialOptions{Subprotocols: protos})
		return c, err
	}
	call := func(c *websocket.Conn, req request) response {
		must(wsjson.Write(ctx, c, req) == nil, "write")
		var resp response
		must(wsjson.Read(ctx, c, &resp) == nil, "read")
		return resp
	}

	fmt.Println("== 1. request/response over one socket, matched by id ==")
	c, err := dial("calc.v1", "calc.v2")
	must(err == nil, fmt.Sprint(err))
	fmt.Println("  negotiated subprotocol:", c.Subprotocol(), "(server preferred v2)")
	must(c.Subprotocol() == "calc.v2", "server preference")
	r1 := call(c, request{ID: 1, Op: "add", Args: []float64{2, 3}})
	fmt.Printf("  add(2,3)   -> id=%d result=%v\n", r1.ID, *r1.Result)
	must(r1.ID == 1 && *r1.Result == 5, "add")
	r2 := call(c, request{ID: 2, Op: "div", Args: []float64{1, 0}})
	fmt.Printf("  div(1,0)   -> id=%d error=%q (an application error, the connection stays open)\n", r2.ID, r2.Error)
	must(r2.Error == "division by zero", "app error")
	r3 := call(c, request{ID: 3, Op: "version"})
	fmt.Printf("  version    -> %v\n", *r3.Result)
	must(*r3.Result == 2, "v2 feature")
	c.Close(websocket.StatusNormalClosure, "done")

	fmt.Println("\n== 2. an older client negotiates v1: same server, different behaviour ==")
	c, _ = dial("calc.v1")
	r := call(c, request{ID: 1, Op: "version"})
	fmt.Printf("  version on v1 -> %q\n", r.Error)
	must(r.Error != "", "v1 lacks version op")
	c.Close(websocket.StatusNormalClosure, "")

	fmt.Println("\n== 3. no acceptable subprotocol ==")
	c, err = dial() // offers none
	must(err == nil, "connection is accepted, then closed")
	var resp response
	err = wsjson.Read(ctx, c, &resp)
	fmt.Printf("  server closed with status %d: %v\n", websocket.CloseStatus(err), err)
	must(websocket.CloseStatus(err) == websocket.StatusPolicyViolation, "policy violation")

	fmt.Println("\n== 4. limits and bad data ==")
	c, _ = dial("calc.v2")
	c.SetReadLimit(1 << 20) // let the CLIENT send big; the SERVER's limit is 4 KiB
	big := make([]byte, 8<<10)
	c.Write(ctx, websocket.MessageText, big)
	_, _, err = c.Read(ctx)
	fmt.Printf("  8 KiB message -> server closed with %d (StatusMessageTooBig = 1009)\n", websocket.CloseStatus(err))
	must(websocket.CloseStatus(err) == websocket.StatusMessageTooBig, "too big")

	c, _ = dial("calc.v2")
	c.Write(ctx, websocket.MessageText, []byte("this is not json"))
	_, _, err = c.Read(ctx)
	fmt.Printf("  malformed JSON -> connection ended with status %d\n", websocket.CloseStatus(err))
	must(websocket.CloseStatus(err) != -1, "closed on bad json")
	fmt.Println("\nOK")
}
