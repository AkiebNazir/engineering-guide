/*
FOUNDATION LEVEL 05 - Validating a message without destroying the session
=============================================================================
Level 02 decoded the payload and mostly trusted it. Send that server garbage
and wsjson.Read fails, the handler returns, and the connection goes with it. On
a REST server that would cost one request. Here it costs the whole session: the
client's auth, its room membership, its scroll position - all gone because of
one typo in one message.

So WebSocket validation has a different DEFAULT than REST validation. In REST,
isolation is free: every request is separate, so a 400 naturally affects only
that request. In WebSockets, isolation is something you must build on purpose.
The rule: a bad MESSAGE gets an error reply; only a bad CLIENT gets closed.

A Go-specific trap lives here too. wsjson.Read does two things at once - it
reads the message AND unmarshals it - and on a JSON error it CLOSES the
connection (status 1007) before returning. So to keep the session alive you
must read raw bytes with c.Read and unmarshal yourself, which is exactly what
this file does.

You will learn
  - why c.Read + json.Unmarshal beats wsjson.Read when bad input is expected
  - validate in layers: is it text -> is it JSON -> is it an object with a
    known `type` -> is the payload shaped right for that type
  - reply with a structured error message and KEEP READING (the whole point)
  - the exception to the rule: when a peer is clearly not speaking your
    protocol at all, closing with 1003/1008 is correct (level 06)
  - that the library enforces some rules for you - a text frame with invalid
    UTF-8 is a protocol violation it closes with 1007 before you see it

Run it   go run ./WebSockets/Foundation/golang/05_payload_validation_without_dropping
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

type envelope struct {
	Type    string          `json:"type"`
	Payload json.RawMessage `json:"payload"`
}

type reply struct {
	Type    string `json:"type"`
	Payload any    `json:"payload"`
}

// Each entry validates its own payload and, if it is happy, computes a result.
// Returning an error means "this one message was bad", never "hang up".
var schemas = map[string]func(json.RawMessage) (any, error){
	"sum": func(raw json.RawMessage) (any, error) {
		var numbers []float64
		if err := json.Unmarshal(raw, &numbers); err != nil {
			return nil, fmt.Errorf("payload must be a list of numbers")
		}
		if len(numbers) == 0 {
			return nil, fmt.Errorf("payload must be a non-empty list of numbers")
		}
		total := 0.0
		for _, n := range numbers {
			total += n
		}
		return total, nil
	},
	"upper": func(raw json.RawMessage) (any, error) {
		var text string
		if err := json.Unmarshal(raw, &text); err != nil {
			return nil, fmt.Errorf("payload must be a string")
		}
		return strings.ToUpper(text), nil
	},
}

func knownTypes() []string {
	names := make([]string, 0, len(schemas))
	for name := range schemas {
		names = append(names, name)
	}
	sort.Strings(names)
	return names
}

// validate turns raw wire data into a result or a human-readable reason.
func validate(msgType websocket.MessageType, data []byte) (string, any, error) {
	if msgType != websocket.MessageText {
		return "", nil, fmt.Errorf("expected a text message, got binary")
	}
	var msg envelope
	if err := json.Unmarshal(data, &msg); err != nil {
		return "", nil, fmt.Errorf("not valid JSON: %v", err)
	}
	// An empty Type also catches "valid JSON, but not our envelope at all"
	// (a bare array or number decodes into the zero envelope).
	check, ok := schemas[msg.Type]
	if !ok {
		return "", nil, fmt.Errorf("unknown type %q; known: %v", msg.Type, knownTypes())
	}
	if len(msg.Payload) == 0 {
		return "", nil, fmt.Errorf("missing 'payload'")
	}
	result, err := check(msg.Payload)
	if err != nil {
		return "", nil, fmt.Errorf("bad payload for type %q: %v", msg.Type, err)
	}
	return msg.Type, result, nil
}

func validatingHandler(w http.ResponseWriter, r *http.Request) {
	c, err := websocket.Accept(w, r, nil)
	if err != nil {
		return
	}
	defer c.CloseNow()

	for {
		ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
		// c.Read, NOT wsjson.Read: we want the raw bytes so that a decode
		// failure is OUR decision to handle, not the library's decision to
		// close the connection with 1007.
		msgType, data, err := c.Read(ctx)
		cancel()
		if err != nil {
			return
		}

		kind, result, verr := validate(msgType, data)
		out := reply{Type: kind, Payload: result}
		if verr != nil {
			// An error REPLY, not a close. The client is told precisely what
			// was wrong and may immediately try again on the same connection.
			out = reply{Type: "error", Payload: verr.Error()}
		}

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

	sendRaw := func(raw string) reply {
		must(c.Write(ctx, websocket.MessageText, []byte(raw)) == nil, "write")
		var got reply
		must(wsjson.Read(ctx, c, &got) == nil, "read")
		return got
	}

	fmt.Println("== five different kinds of broken message, one surviving connection ==")
	broken := []struct {
		label string
		raw   string
	}{
		{"not JSON at all", "hello there"},
		{"JSON, but not our envelope", "[1, 2, 3]"},
		{"object with no type", `{"payload": 1}`},
		{"unknown type", `{"type": "nope", "payload": 1}`},
		{"right type, wrong payload shape", `{"type": "sum", "payload": "seven"}`},
	}
	for _, b := range broken {
		got := sendRaw(b.raw)
		fmt.Printf("  %-32s -> %s: %v\n", b.label, got.Type, got.Payload)
		must(got.Type == "error", b.label)
	}

	fmt.Println("\n== and a binary message, when this endpoint only speaks text ==")
	must(c.Write(ctx, websocket.MessageBinary, []byte{0x01, 0x02}) == nil, "write")
	var got reply
	must(wsjson.Read(ctx, c, &got) == nil, "read")
	fmt.Printf("  binary frame                     -> %s: %v\n", got.Type, got.Payload)
	must(got.Type == "error", "binary rejected")

	fmt.Println("\n== and the connection is still perfectly usable ==")
	got = sendRaw(`{"type": "sum", "payload": [1, 2, 3]}`)
	fmt.Printf("  valid sum   -> {%s %v}\n", got.Type, got.Payload)
	must(got.Type == "sum" && got.Payload == 6.0, "sum works")

	got = sendRaw(`{"type": "upper", "payload": "still alive"}`)
	fmt.Printf("  valid upper -> {%s %v}\n", got.Type, got.Payload)
	must(got.Type == "upper" && got.Payload == "STILL ALIVE", "upper works")

	// Six protocol violations in a row did not cost this client its session.
	fmt.Println("  connection state: still open after 6 rejected messages")
	must(c.Close(websocket.StatusNormalClosure, "done") == nil, "clean close")

	fmt.Println("\nOK")
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, http.HandlerFunc(validatingHandler))
	demo("ws://" + ln.Addr().String())
}
