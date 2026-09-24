/*
FOUNDATION LEVEL 08 - Middleware for a connection, not for a request
========================================================================
Middleware means the same thing here as in REST
(../../../REST/Foundation/golang/08_middleware_logging_and_recovery): a wrapper
that adds behaviour around your real code without editing it. But the SHAPE is
different, and the difference is not cosmetic - it changes what each wrapper
can do.

	REST middleware wraps ONE request/response: func(http.Handler) http.Handler.
	Scope and lifetime are the same thing. The request arrives, the chain runs,
	a response goes out, everything is discarded. One layer, one concept.

	WebSocket middleware has TWO distinct scopes, and you need both:
	  * CONNECTION-scoped - runs once at connect, once at disconnect. This is
	    where logging, metrics, rate-limit buckets and registry bookkeeping
	    live, because those things belong to the client, not to a message.
	  * MESSAGE-scoped - runs per inbound message. This is where panic
	    recovery must live, because the unit you want to isolate is ONE
	    message. Put recovery at connection scope and a single bad message
	    kills the whole session; put it at message scope and the session
	    shrugs it off.

So the pipeline is built from two different wrapper types:

	withLogging( messageLoop( withRecovery( handleMessage ) ) )
	^connection-scoped             ^message-scoped

WHY RECOVERY MATTERS MORE IN GO THAN IN PYTHON: a panic inside an http.Handler
is recovered by net/http itself, which logs a stack trace and drops that one
connection - bad, but survivable. A panic inside a goroutine YOU started (the
ticker in level 04, the keepalive loop in level 07) is recovered by nobody and
takes down the ENTIRE SERVER PROCESS. Every long-lived connection spawns such
goroutines, so `defer recover()` stops being optional hygiene here.

You will learn
  - the two middleware scopes a persistent connection needs, and why
  - that connection-scoped middleware has a duration - it can time the whole
    session, which a REST middleware can never do
  - panic recovery per message: reply with an error, KEEP the connection
  - that a websocket.Conn handler is still an http.Handler underneath, so your
    existing net/http middleware (request logging, tracing) still composes
  - chaining order still matters, exactly as it did in REST

Run it   go run ./WebSockets/Foundation/golang/08_middleware_logging_and_recovery
*/
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net"
	"net/http"
	"sync/atomic"
	"time"

	"github.com/coder/websocket"
	"github.com/coder/websocket/wsjson"
)

// Two handler shapes, because there are two scopes.
type connHandler func(ctx context.Context, c *websocket.Conn, r *http.Request) error
type messageHandler func(ctx context.Context, c *websocket.Conn, data []byte) error

var (
	connections atomic.Int64
	recovered   atomic.Int64
)

type message struct {
	Type    string `json:"type"`
	Payload any    `json:"payload"`
}

// ---- the "real" application logic: one message in, replies written out ----
func handleMessage(ctx context.Context, c *websocket.Conn, data []byte) error {
	var in message
	if err := json.Unmarshal(data, &in); err != nil {
		return fmt.Errorf("bad JSON: %w", err)
	}
	switch in.Type {
	case "echo":
		return wsjson.Write(ctx, c, message{Type: "echo", Payload: in.Payload})
	case "boom":
		// A genuine panic, not a returned error - the thing recovery exists for.
		panic("simulated bug while handling one message")
	default:
		return fmt.Errorf("unknown type %q", in.Type)
	}
}

// ---- MESSAGE-scoped middleware: isolate one message's failure ----
func withRecovery(next messageHandler) messageHandler {
	return func(ctx context.Context, c *websocket.Conn, data []byte) (err error) {
		// The named return value is what lets a deferred function convert a
		// panic into an ordinary error. This is the Go idiom for recovery.
		defer func() {
			if p := recover(); p != nil {
				recovered.Add(1)
				fmt.Printf("    [recover] panic: %v\n", p)
				fmt.Println("    [recover] -> error reply sent, CONNECTION KEPT OPEN")
				err = wsjson.Write(ctx, c, message{
					Type:    "error",
					Payload: fmt.Sprintf("panic: %v", p),
				})
			}
		}()

		if herr := next(ctx, c, data); herr != nil {
			// An ordinary error is also a per-message failure, so it gets the
			// same treatment: reply, do not disconnect.
			recovered.Add(1)
			fmt.Printf("    [recover] error: %v\n", herr)
			fmt.Println("    [recover] -> error reply sent, CONNECTION KEPT OPEN")
			return wsjson.Write(ctx, c, message{Type: "error", Payload: herr.Error()})
		}
		return nil
	}
}

// ---- the adapter that turns a message handler into a connection handler ----
func messageLoop(handle messageHandler) connHandler {
	return func(ctx context.Context, c *websocket.Conn, r *http.Request) error {
		for {
			rctx, cancel := context.WithTimeout(ctx, 10*time.Second)
			_, data, err := c.Read(rctx)
			cancel()
			if err != nil {
				return err // the peer went away: the normal way out
			}
			if err := handle(ctx, c, data); err != nil {
				return err
			}
		}
	}
}

// ---- CONNECTION-scoped middleware: runs once at each end of the session ----
func withLogging(next connHandler) connHandler {
	return func(ctx context.Context, c *websocket.Conn, r *http.Request) error {
		connections.Add(1)
		started := time.Now()
		// A REST middleware cannot print a line like this, because there is no
		// "connect" event to hang it on.
		fmt.Printf("  [log] CONNECT   path=%s\n", r.URL.Path)

		err := next(ctx, c, r)

		// Runs however the session ended: politely, crashed, or closed by us.
		fmt.Printf("  [log] DISCONNECT status=%d session lasted %dms\n",
			websocket.CloseStatus(err), time.Since(started).Milliseconds())
		return err
	}
}

// Built once, outside in. Logging is outermost so it brackets the entire
// session; recovery is innermost so its blast radius is exactly one message.
var pipeline = withLogging(messageLoop(withRecovery(handleMessage)))

func wsHandler(w http.ResponseWriter, r *http.Request) {
	c, err := websocket.Accept(w, r, nil)
	if err != nil {
		return
	}
	defer c.CloseNow()
	pipeline(r.Context(), c, r)
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func demo(base string) {
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	c, _, err := websocket.Dial(ctx, base+"/chat", nil)
	must(err == nil, fmt.Sprint(err))
	defer c.CloseNow()

	call := func(raw string) message {
		must(c.Write(ctx, websocket.MessageText, []byte(raw)) == nil, "write")
		var got message
		must(wsjson.Read(ctx, c, &got) == nil, "read")
		return got
	}

	fmt.Println("\n  -- a normal message --")
	got := call(`{"type": "echo", "payload": "hi"}`)
	fmt.Printf("  reply: {%s %v}\n", got.Type, got.Payload)
	must(got.Type == "echo" && got.Payload == "hi", "echo")

	fmt.Println("\n  -- a message whose handler PANICS --")
	got = call(`{"type": "boom", "payload": null}`)
	fmt.Printf("  reply: {%s %v}\n", got.Type, got.Payload)
	must(got.Type == "error", "panic recovered into an error reply")

	fmt.Println("\n  -- and another, differently broken --")
	got = call(`{"type": "nope", "payload": null}`)
	fmt.Printf("  reply: {%s %v}\n", got.Type, got.Payload)
	must(got.Type == "error", "error reply")

	fmt.Println("\n  -- the session is untouched by either failure --")
	got = call(`{"type": "echo", "payload": "still connected"}`)
	fmt.Printf("  reply: {%s %v}\n", got.Type, got.Payload)
	must(got.Payload == "still connected", "connection survived")

	must(c.Close(websocket.StatusNormalClosure, "done") == nil, "close")

	// Let the server's logging tail run before we read the counters.
	time.Sleep(100 * time.Millisecond)
	fmt.Printf("\nconnections logged: %d, messages recovered: %d\n",
		connections.Load(), recovered.Load())
	must(connections.Load() == 1, "connection-scoped: once per client")
	must(recovered.Load() == 2, "message-scoped: once per bad message")
	fmt.Println("one CONNECT/DISCONNECT pair, two isolated message failures - " +
		"that is the two scopes working")
	fmt.Println("\nOK")
}

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/chat", wsHandler)

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, mux)
	demo("ws://" + ln.Addr().String())
}
