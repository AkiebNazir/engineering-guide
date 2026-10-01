/*
LAB 01 (basic) - A WebSocket server written from scratch with net/http (no library)
===================================================================================
You will learn

  - the upgrade: validate the request headers, compute Sec-WebSocket-Accept, answer 101, and then
    TAKE OVER the TCP connection with http.Hijacker (net/http gives up control of it)

  - Sec-WebSocket-Accept = base64( sha1( Sec-WebSocket-Key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11" ) )

  - the frame format, byte by byte:

    byte 0:  FIN(1) RSV(3) opcode(4)          0x1 text  0x2 binary  0x8 close  0x9 ping  0xA pong
    byte 1:  MASK(1) payload length(7)        126 => next 2 bytes are the length, 127 => next 8
    [mask key: 4 bytes]                       client -> server frames MUST be masked
    payload                                    XOR-ed with the mask key when masked

  - why clients mask: to stop a malicious page from crafting bytes that look like HTTP to a
    caching proxy (cache poisoning). Servers must REJECT unmasked client frames.

  - control frames: ping -> reply pong with the same payload; close -> echo the close code and close

  - proof it is right: the RFC 6455 test vectors AND an interop test - the professional
    library coder/websocket connects to OUR server and chats with it

Run it   go run ./WebSockets/labs/golang/01_handshake_and_frames_by_hand
*/
package main

import (
	"bufio"
	"context"
	"crypto/sha1"
	"encoding/base64"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"strings"
	"time"

	"github.com/coder/websocket"
)

const guid = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

func acceptKey(key string) string {
	h := sha1.Sum([]byte(key + guid))
	return base64.StdEncoding.EncodeToString(h[:])
}

// ------------------------------------------------------------------ frames --
const (
	opText, opBinary, opClose, opPing, opPong = 0x1, 0x2, 0x8, 0x9, 0xA
)

type frame struct {
	fin     bool
	opcode  byte
	payload []byte
}

// readFrame parses ONE frame. `wantMasked` = true on the server side.
func readFrame(r *bufio.Reader, wantMasked bool, maxPayload int64) (frame, error) {
	var hdr [2]byte
	if _, err := io.ReadFull(r, hdr[:]); err != nil {
		return frame{}, err
	}
	f := frame{fin: hdr[0]&0x80 != 0, opcode: hdr[0] & 0x0F}
	if hdr[0]&0x70 != 0 {
		return f, errors.New("RSV bits set but no extension negotiated") // protocol error
	}
	masked := hdr[1]&0x80 != 0
	if masked != wantMasked {
		return f, fmt.Errorf("frame masked=%v but expected %v (client frames MUST be masked, server frames must NOT)", masked, wantMasked)
	}
	n := int64(hdr[1] & 0x7F)
	switch n {
	case 126:
		var b [2]byte
		if _, err := io.ReadFull(r, b[:]); err != nil {
			return f, err
		}
		n = int64(binary.BigEndian.Uint16(b[:]))
	case 127:
		var b [8]byte
		if _, err := io.ReadFull(r, b[:]); err != nil {
			return f, err
		}
		n = int64(binary.BigEndian.Uint64(b[:]))
	}
	if n > maxPayload { // ALWAYS bound this: the length is attacker-controlled
		return f, fmt.Errorf("frame of %d bytes exceeds limit %d", n, maxPayload)
	}
	var mask [4]byte
	if masked {
		if _, err := io.ReadFull(r, mask[:]); err != nil {
			return f, err
		}
	}
	f.payload = make([]byte, n)
	if _, err := io.ReadFull(r, f.payload); err != nil {
		return f, err
	}
	if masked {
		for i := range f.payload {
			f.payload[i] ^= mask[i%4]
		}
	}
	return f, nil
}

// writeFrame builds one frame. A non-nil mask makes it a CLIENT frame.
func writeFrame(w io.Writer, opcode byte, payload []byte, mask *[4]byte) error {
	buf := []byte{0x80 | opcode} // FIN=1 (no fragmentation in this lab)
	m := byte(0)
	if mask != nil {
		m = 0x80
	}
	switch n := len(payload); {
	case n < 126:
		buf = append(buf, m|byte(n))
	case n < 65536:
		buf = append(buf, m|126, byte(n>>8), byte(n))
	default:
		buf = append(buf, m|127)
		buf = binary.BigEndian.AppendUint64(buf, uint64(n))
	}
	if mask != nil {
		buf = append(buf, mask[:]...)
		masked := make([]byte, len(payload))
		for i, b := range payload {
			masked[i] = b ^ mask[i%4]
		}
		payload = masked
	}
	_, err := w.Write(append(buf, payload...))
	return err
}

// ------------------------------------------------------------------ server --
func echoHandler(w http.ResponseWriter, r *http.Request) {
	// 1. validate the upgrade request
	if !strings.EqualFold(r.Header.Get("Upgrade"), "websocket") ||
		!strings.Contains(strings.ToLower(r.Header.Get("Connection")), "upgrade") {
		http.Error(w, "expected a WebSocket upgrade", http.StatusUpgradeRequired)
		return
	}
	if r.Header.Get("Sec-WebSocket-Version") != "13" {
		w.Header().Set("Sec-WebSocket-Version", "13")
		http.Error(w, "unsupported version", http.StatusBadRequest)
		return
	}
	key := r.Header.Get("Sec-WebSocket-Key")
	if raw, err := base64.StdEncoding.DecodeString(key); err != nil || len(raw) != 16 {
		http.Error(w, "bad Sec-WebSocket-Key", http.StatusBadRequest)
		return
	}
	// (a real server also checks r.Header.Get("Origin") here - see the Python track, lab 3)

	// 2. take over the raw TCP connection
	hj, ok := w.(http.Hijacker)
	if !ok {
		http.Error(w, "hijacking not supported (HTTP/2?)", http.StatusInternalServerError)
		return
	}
	conn, rw, err := hj.Hijack()
	if err != nil {
		return
	}
	defer conn.Close()

	// 3. the 101 response. From now on: frames, not HTTP.
	fmt.Fprintf(rw, "HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: %s\r\n\r\n", acceptKey(key))
	rw.Flush()

	// 4. the frame loop
	for {
		conn.SetReadDeadline(time.Now().Add(5 * time.Second))
		f, err := readFrame(rw.Reader, true, 1<<20)
		if err != nil {
			code := uint16(1002) // protocol error
			if strings.Contains(err.Error(), "exceeds limit") {
				code = 1009 // message too big
			}
			if !errors.Is(err, io.EOF) {
				writeFrame(conn, opClose, binary.BigEndian.AppendUint16(nil, code), nil)
			}
			return
		}
		switch f.opcode {
		case opText, opBinary:
			writeFrame(conn, f.opcode, append([]byte("echo: "), f.payload...), nil)
		case opPing:
			writeFrame(conn, opPong, f.payload, nil) // pong must carry the ping's payload
		case opClose:
			writeFrame(conn, opClose, f.payload, nil) // echo the status code, then close
			return
		}
	}
}

// ------------------------------------------------------- hand-made client ---
type rawClient struct {
	conn net.Conn
	r    *bufio.Reader
}

func dialRaw(addr, key string) (*rawClient, string, error) {
	conn, err := net.Dial("tcp", addr)
	if err != nil {
		return nil, "", err
	}
	fmt.Fprintf(conn, "GET /chat HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n", addr, key)
	r := bufio.NewReader(conn)
	var head []string
	for {
		line, err := r.ReadString('\n')
		if err != nil {
			return nil, "", err
		}
		if line = strings.TrimRight(line, "\r\n"); line == "" {
			break
		}
		head = append(head, line)
	}
	return &rawClient{conn, r}, strings.Join(head, "\n"), nil
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	fmt.Println("== 1. RFC 6455 test vectors ==")
	must(acceptKey("dGhlIHNhbXBsZSBub25jZQ==") == "s3pPLMBiTxaQ9kYGzzhZRbK+xOo=", "accept key")
	fmt.Println("  Sec-WebSocket-Accept for the RFC's sample key: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=  OK")
	var sb strings.Builder
	mask := [4]byte{0x37, 0xfa, 0x21, 0x3d}
	writeFrame(&sb, opText, []byte("Hello"), &mask)
	fmt.Printf("  masked \"Hello\" frame: % x  (RFC: 81 85 37 fa 21 3d 7f 9f 4d 51 58)\n", sb.String())
	must(fmt.Sprintf("% x", sb.String()) == "81 85 37 fa 21 3d 7f 9f 4d 51 58", "masked frame")

	ln, _ := net.Listen("tcp", "127.0.0.1:0")
	go http.Serve(ln, http.HandlerFunc(echoHandler))
	addr := ln.Addr().String()

	fmt.Println("\n== 2. our own client speaks to our own server ==")
	key := base64.StdEncoding.EncodeToString([]byte("sixteen-byte-key"))
	c, head, err := dialRaw(addr, key)
	must(err == nil, fmt.Sprint(err))
	fmt.Println(indent(head))
	must(strings.Contains(head, "Sec-WebSocket-Accept: "+acceptKey(key)), "accept matches")

	writeFrame(c.conn, opText, []byte("hello"), &mask)
	f, _ := readFrame(c.r, false, 1<<20)
	fmt.Printf("  text  -> %q (opcode %#x)\n", f.payload, f.opcode)
	must(string(f.payload) == "echo: hello", "echo")

	writeFrame(c.conn, opPing, []byte("are-you-there"), &mask)
	f, _ = readFrame(c.r, false, 1<<20)
	fmt.Printf("  ping  -> pong with payload %q (opcode %#x)\n", f.payload, f.opcode)
	must(f.opcode == opPong && string(f.payload) == "are-you-there", "pong")

	big := strings.Repeat("x", 70000) // > 65535 => uses the 8-byte length form
	writeFrame(c.conn, opBinary, []byte(big), &mask)
	f, _ = readFrame(c.r, false, 1<<20)
	fmt.Printf("  70000-byte message -> %d bytes echoed (extended 64-bit length form)\n", len(f.payload))
	must(len(f.payload) == 70000+6, "large frame")

	writeFrame(c.conn, opClose, binary.BigEndian.AppendUint16(nil, 1000), &mask)
	f, _ = readFrame(c.r, false, 1<<20)
	fmt.Printf("  close -> server echoes close code %d and hangs up\n", binary.BigEndian.Uint16(f.payload))
	must(f.opcode == opClose && binary.BigEndian.Uint16(f.payload) == 1000, "close echo")
	c.conn.Close()

	fmt.Println("\n== 3. protocol violations are rejected ==")
	c, _, _ = dialRaw(addr, key)
	writeFrame(c.conn, opText, []byte("unmasked!"), nil) // a client MUST mask
	f, _ = readFrame(c.r, false, 1<<20)
	fmt.Printf("  unmasked client frame -> server closes with code %d (protocol error)\n", binary.BigEndian.Uint16(f.payload))
	must(f.opcode == opClose && binary.BigEndian.Uint16(f.payload) == 1002, "unmasked rejected")
	c.conn.Close()

	c, _, _ = dialRaw(addr, key)
	writeFrame(c.conn, opBinary, []byte(strings.Repeat("y", 2<<20)), &mask) // 2 MiB > limit
	f, _ = readFrame(c.r, false, 1<<20)
	fmt.Printf("  2 MiB frame           -> server closes with code %d (message too big)\n", binary.BigEndian.Uint16(f.payload))
	must(binary.BigEndian.Uint16(f.payload) == 1009, "size limit")
	c.conn.Close()

	resp, _ := http.Get("http://" + addr + "/plain")
	fmt.Printf("  plain HTTP GET        -> %d %s\n", resp.StatusCode, http.StatusText(resp.StatusCode))
	must(resp.StatusCode == http.StatusUpgradeRequired, "plain http refused")

	fmt.Println("\n== 4. INTEROP: the professional coder/websocket client talks to our hand-made server ==")
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	ws, _, err := websocket.Dial(ctx, "ws://"+addr+"/chat", nil)
	must(err == nil, fmt.Sprint(err))
	must(ws.Write(ctx, websocket.MessageText, []byte("from a real library")) == nil, "write")
	typ, data, err := ws.Read(ctx)
	must(err == nil, fmt.Sprint(err))
	fmt.Printf("  library got: %q (type %v)\n", data, typ)
	must(string(data) == "echo: from a real library", "interop echo")
	ws.Close(websocket.StatusNormalClosure, "bye")
	fmt.Println("\nOK")
}

func indent(s string) string {
	var out []string
	for _, l := range strings.Split(s, "\n") {
		out = append(out, "  <- "+l)
	}
	return strings.Join(out, "\n")
}
