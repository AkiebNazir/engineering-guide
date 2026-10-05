/*
FOUNDATION LEVEL 01 - Messages, not bytes: text frames, binary frames, boundaries
=====================================================================================
Level 00 sent strings and got strings back without ever asking what actually
travelled. This level asks. A WebSocket does NOT give you a byte stream like a
raw TCP socket does - it gives you discrete MESSAGES, each carried in one or
more frames, and the library hands you each message whole or not at all.

That single property is why WebSockets are pleasant to program against: you
never have to invent your own "where does this message end?" rule (length
prefixes, newline delimiters), the way you must with a bare net.Conn.

You will learn
  - a message has a TYPE decided by its frame opcode: websocket.MessageText
    (0x1) or websocket.MessageBinary (0x2), returned to you by c.Read
  - MESSAGE boundaries are preserved: two Writes are two Reads, always, never
    merged and never split (a bare net.Conn guarantees neither)
  - a big message may be split into several FRAMES on the wire, yet still
    arrives as ONE message - frames are transport detail, messages are the API
  - SetReadLimit: the size guard you must think about, because "one message"
    means the library buffers the whole thing (the default is deliberately small)
  - ordering is guaranteed, because underneath it is still one TCP connection

Run it   go run ./WebSockets/Foundation/golang/01_message_framing_text_and_binary
*/
package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"net/http"
	"strings"
	"time"

	"github.com/coder/websocket"
)

// Reports back what KIND of message it received, and how big it was.
func inspectHandler(w http.ResponseWriter, r *http.Request) {
	c, err := websocket.Accept(w, r, nil)
	if err != nil {
		return
	}
	defer c.CloseNow()

	// The default read limit is 32 KiB. Because a message is delivered whole,
	// the library must hold all of it in memory - so the limit is really "how
	// much RAM will I let one peer make me allocate?". We raise it to allow
	// the 200 KB demo below; exceeding it closes the connection with 1009.
	c.SetReadLimit(1 << 20)

	for {
		ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
		msgType, data, err := c.Read(ctx)
		cancel()
		if err != nil {
			return
		}

		var report string
		switch msgType {
		case websocket.MessageText:
			// A text frame's payload is required by RFC 6455 to be valid
			// UTF-8, which is why treating it as a Go string is always safe.
			preview := string(data)
			if len(preview) > 20 {
				preview = preview[:20]
			}
			report = fmt.Sprintf("text:%d:%s", len(data), preview)
		case websocket.MessageBinary:
			// A binary frame is arbitrary bytes - no encoding rules at all.
			report = fmt.Sprintf("binary:%d", len(data))
		}

		wctx, wcancel := context.WithTimeout(r.Context(), 5*time.Second)
		err = c.Write(wctx, websocket.MessageText, []byte(report))
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
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()

	c, _, err := websocket.Dial(ctx, url, nil)
	must(err == nil, fmt.Sprint(err))
	defer c.CloseNow()

	roundTrip := func(msgType websocket.MessageType, payload []byte) string {
		must(c.Write(ctx, msgType, payload) == nil, "write")
		_, data, err := c.Read(ctx)
		must(err == nil, fmt.Sprint(err))
		return string(data)
	}

	fmt.Println("== 1. text vs binary: the frame opcode decides the message type ==")
	got := roundTrip(websocket.MessageText, []byte("hello"))
	fmt.Printf("  MessageText   \"hello\"          -> server saw %s\n", got)
	must(got == "text:5:hello", "text")

	got = roundTrip(websocket.MessageBinary, []byte{0x00, 0x01, 0x02, 0xff})
	fmt.Printf("  MessageBinary  {0,1,2,255}      -> server saw %s\n", got)
	must(got == "binary:4", "binary")

	fmt.Println("\n== 2. boundaries: two Writes are two Reads, never one blurred blob ==")
	must(c.Write(ctx, websocket.MessageText, []byte("aaaa")) == nil, "write")
	must(c.Write(ctx, websocket.MessageText, []byte("bb")) == nil, "write")
	_, first, _ := c.Read(ctx)
	_, second, _ := c.Read(ctx)
	fmt.Printf("  wrote \"aaaa\" then \"bb\"  -> %q then %q\n", first, second)
	// On a bare net.Conn these could have arrived as the 6 bytes "aaaabb" in a
	// single Read, and you would have had no way to tell where the first one
	// ended. WebSockets removes that entire class of bug.
	must(string(first) == "text:4:aaaa" && string(second) == "text:2:bb", "boundaries")

	fmt.Println("\n== 3. one MESSAGE can be many FRAMES, and still arrives whole ==")
	// c.Writer gives you an io.WriteCloser for ONE message. Each Write call on
	// it may become its own frame on the wire (fin=0, fin=0, ... fin=1), but
	// the receiver never sees the seams - it gets one 11-byte message.
	wr, err := c.Writer(ctx, websocket.MessageText)
	must(err == nil, "writer")
	for _, part := range []string{"Hel", "lo ", "world"} {
		_, err = wr.Write([]byte(part))
		must(err == nil, "partial write")
	}
	must(wr.Close() == nil, "close writer") // Close is what sets FIN=1
	_, data, err := c.Read(ctx)
	must(err == nil, fmt.Sprint(err))
	fmt.Printf("  wrote 3 fragments        -> server saw %s   (one message, reassembled)\n", data)
	must(string(data) == "text:11:Hello world", "fragmented message")

	// Same idea at size: 200 KB goes out in whatever frames the library and the
	// OS choose, and comes back as exactly one 200000-byte message.
	got = roundTrip(websocket.MessageBinary, make([]byte, 200_000))
	fmt.Printf("  wrote 200000 binary bytes -> server saw %s\n", got)
	must(got == "binary:200000", "big message")

	fmt.Println("\n== 4. ordering is guaranteed (it is still one TCP connection) ==")
	for i := 0; i < 5; i++ {
		must(c.Write(ctx, websocket.MessageText, []byte(fmt.Sprintf("m%d", i))) == nil, "write")
	}
	var replies []string
	for i := 0; i < 5; i++ {
		_, data, err := c.Read(ctx)
		must(err == nil, fmt.Sprint(err))
		replies = append(replies, string(data))
	}
	fmt.Println("  ", replies)
	must(strings.Join(replies, ",") == "text:2:m0,text:2:m1,text:2:m2,text:2:m3,text:2:m4", "order")

	must(c.Close(websocket.StatusNormalClosure, "done") == nil, "close")
	fmt.Println("\nOK")
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, http.HandlerFunc(inspectHandler))
	demo("ws://" + ln.Addr().String())
}
