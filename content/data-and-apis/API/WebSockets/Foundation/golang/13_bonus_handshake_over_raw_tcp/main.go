/*
FOUNDATION BONUS - What does "upgrading a connection" actually mean? (optional, read last)
============================================================================================
Level 00 called websocket.Accept and websocket.Dial and never asked what
happened. This file answers it, with no WebSocket library on EITHER side - just
a bare net.Conn, hand-written bytes, and the rules from RFC 6455. Both the
server and the client here are built from scratch.

It exists to dissolve the word "upgrade". There is no magic: the client sends a
perfectly ordinary HTTP GET with a couple of extra headers, the server replies
`101 Switching Protocols`, and from the next byte onward both sides simply
agree to stop writing HTTP and start writing frames down the same socket. The
socket never changed. Only the convention did.

This is optional. Nothing in levels 00-12 depends on it. Read it when you are
curious what the library is doing for you.

You will learn
  - the exact handshake bytes: GET + Upgrade/Connection/Sec-WebSocket-Key,
    answered with 101 + Sec-WebSocket-Accept
  - what Sec-WebSocket-Accept proves: base64(sha1(key + a fixed GUID)), which a
    confused plain HTTP server could never produce by accident
  - the frame layout by hand: FIN+opcode, MASK+length, an optional 4-byte mask
    key, then the payload
  - the masking rule that trips everyone up: client->server frames MUST be
    masked (XOR with those 4 bytes), server->client frames MUST NOT be
  - that "text" and "binary" are literally just opcode 0x1 vs 0x2

Run it   go run ./WebSockets/Foundation/golang/13_bonus_handshake_over_raw_tcp
*/
package main

import (
	"bufio"
	"crypto/rand"
	"crypto/sha1"
	"encoding/base64"
	"encoding/binary"
	"fmt"
	"log"
	"net"
	"strings"
)

// Fixed by RFC 6455. It is not a secret and not a key - it is a constant chosen
// so that a server's answer can only come from software that meant to answer.
const guid = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

const (
	opcodeText  = 0x1
	opcodeClose = 0x8
)

// acceptKey is the server's half of the handshake proof: sha1(key + GUID), base64'd.
func acceptKey(clientKey string) string {
	sum := sha1.Sum([]byte(clientKey + guid))
	return base64.StdEncoding.EncodeToString(sum[:])
}

// buildFrame assembles one WebSocket frame, byte by byte.
//
//	byte 0 : FIN(1) RSV1-3(3) opcode(4)   -> 0x80 | opcode for a final frame
//	byte 1 : MASK(1) payload-length(7)    -> 0x80 set only when masking
//	then   : 2 or 8 extra length bytes if the length did not fit in 7 bits
//	then   : the 4-byte mask key, if MASK was set
//	then   : the payload (XOR'd with the mask key, if MASK was set)
func buildFrame(payload []byte, opcode byte, maskKey []byte) []byte {
	frame := []byte{0x80 | opcode} // FIN=1, no RSV bits, opcode

	var maskBit byte
	if maskKey != nil {
		maskBit = 0x80
	}

	n := len(payload)
	switch {
	case n < 126:
		frame = append(frame, maskBit|byte(n)) // the length fits in 7 bits
	case n < 65536:
		frame = append(frame, maskBit|126) // 126 => 2 more length bytes
		frame = binary.BigEndian.AppendUint16(frame, uint16(n))
	default:
		frame = append(frame, maskBit|127) // 127 => 8 more length bytes
		frame = binary.BigEndian.AppendUint64(frame, uint64(n))
	}

	if maskKey != nil {
		// Masking is NOT encryption - the key travels in the clear right here.
		// It exists so that a malicious page cannot make a browser emit bytes
		// that a dumb intermediate proxy would mistake for a real HTTP request.
		frame = append(frame, maskKey...)
		masked := make([]byte, n)
		for i, b := range payload {
			masked[i] = b ^ maskKey[i%4]
		}
		return append(frame, masked...)
	}
	return append(frame, payload...)
}

// parseFrame reads one frame out of raw bytes and returns (opcode, payload,
// total bytes consumed).
func parseFrame(data []byte) (byte, []byte, int) {
	opcode := data[0] & 0x0F
	masked := data[1]&0x80 != 0
	length := int(data[1] & 0x7F)
	offset := 2

	switch length {
	case 126:
		length = int(binary.BigEndian.Uint16(data[offset : offset+2]))
		offset += 2
	case 127:
		length = int(binary.BigEndian.Uint64(data[offset : offset+8]))
		offset += 8
	}

	var maskKey []byte
	if masked {
		maskKey = data[offset : offset+4]
		offset += 4
	}

	payload := make([]byte, length)
	copy(payload, data[offset:offset+length])
	if masked {
		for i := range payload {
			payload[i] ^= maskKey[i%4]
		}
	}
	return opcode, payload, offset + length
}

// rawServer is a WebSocket server written entirely by hand.
func rawServer(conn net.Conn) {
	defer conn.Close()
	reader := bufio.NewReader(conn)

	// ---- phase 1: this is still ordinary HTTP. Read the request head. ----
	var head strings.Builder
	headers := map[string]string{}
	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			return
		}
		head.WriteString(line)
		if line == "\r\n" {
			break
		}
		if name, value, ok := strings.Cut(strings.TrimRight(line, "\r\n"), ": "); ok {
			headers[strings.ToLower(name)] = value
		}
	}
	fmt.Println("---- the upgrade request, exactly as it arrives ----")
	fmt.Print(head.String())

	// A real server would also check the method, the version, and Origin.
	if !strings.EqualFold(headers["upgrade"], "websocket") {
		conn.Write([]byte("HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n"))
		return
	}

	// ---- phase 2: say 101, and the socket's meaning changes ----
	response := "HTTP/1.1 101 Switching Protocols\r\n" +
		"Upgrade: websocket\r\n" +
		"Connection: Upgrade\r\n" +
		"Sec-WebSocket-Accept: " + acceptKey(headers["sec-websocket-key"]) + "\r\n" +
		"\r\n"
	fmt.Println("---- the 101 response we write back ----")
	fmt.Print(response)
	conn.Write([]byte(response))

	// ---- phase 3: no more HTTP. Frames only, on the very same socket. ----
	frameHead := make([]byte, 2)
	if _, err := reader.Read(frameHead); err != nil {
		return
	}
	masked := frameHead[1]&0x80 != 0
	length := int(frameHead[1] & 0x7F)
	rest := make([]byte, length)
	if masked {
		rest = make([]byte, length+4)
	}
	if _, err := reader.Read(rest); err != nil {
		return
	}
	raw := append(append([]byte{}, frameHead...), rest...)
	opcode, payload, _ := parseFrame(raw)

	kind := "other"
	if opcode == opcodeText {
		kind = "text"
	}
	fmt.Println("---- one frame received ----")
	fmt.Printf("  raw     : % x\n", raw)
	fmt.Printf("  opcode  : 0x%x (%s)\n", opcode, kind)
	fmt.Printf("  masked  : %v (required for client -> server)\n", masked)
	fmt.Printf("  payload : %q\n", payload)

	// Our reply carries NO mask - a server that masked would be non-compliant.
	reply := buildFrame([]byte("echo: "+string(payload)), opcodeText, nil)
	fmt.Println("---- our unmasked reply frame ----")
	fmt.Printf("  raw     : % x\n", reply)
	conn.Write(reply)

	// A close frame's payload is a 2-byte big-endian status code (1000 = normal).
	closeCode := binary.BigEndian.AppendUint16(nil, 1000)
	conn.Write(buildFrame(closeCode, opcodeClose, nil))
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

// rawClient is a WebSocket client written entirely by hand.
func rawClient(addr string) {
	conn, err := net.Dial("tcp", addr)
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()

	// The key is 16 random bytes, base64'd. It is a handshake nonce, not a
	// credential - it proves the peer speaks WebSocket, nothing about identity.
	nonce := make([]byte, 16)
	rand.Read(nonce)
	key := base64.StdEncoding.EncodeToString(nonce)

	request := "GET /ws HTTP/1.1\r\n" +
		"Host: " + addr + "\r\n" +
		"Upgrade: websocket\r\n" +
		"Connection: Upgrade\r\n" +
		"Sec-WebSocket-Key: " + key + "\r\n" +
		"Sec-WebSocket-Version: 13\r\n" +
		"\r\n"
	conn.Write([]byte(request))

	reader := bufio.NewReader(conn)
	var head strings.Builder
	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			log.Fatal(err)
		}
		head.WriteString(line)
		if line == "\r\n" {
			break
		}
	}
	must(strings.HasPrefix(head.String(), "HTTP/1.1 101 "), "expected 101")

	// Verify the server's proof OURSELVES, the way every real client does.
	expected := acceptKey(key)
	must(strings.Contains(head.String(), "Sec-WebSocket-Accept: "+expected), "accept mismatch")
	fmt.Println("---- the client verifies the proof ----")
	fmt.Printf("  we computed  : %s\n", expected)
	fmt.Println("  it matches the server's Sec-WebSocket-Accept, so this really is a")
	fmt.Println("  WebSocket server and not some HTTP server echoing our headers back")

	// Frames from a client MUST be masked. The mask key is fresh per frame.
	maskKey := make([]byte, 4)
	rand.Read(maskKey)
	conn.Write(buildFrame([]byte("hello"), opcodeText, maskKey))

	buf := make([]byte, 4096)
	n, err := reader.Read(buf)
	must(err == nil, fmt.Sprint(err))
	data := buf[:n]

	opcode, payload, consumed := parseFrame(data)
	fmt.Println("---- what came back ----")
	fmt.Printf("  raw     : % x\n", data)
	fmt.Printf("  decoded : opcode 0x%x, payload %q\n", opcode, payload)
	must(opcode == opcodeText, "expected a text frame")
	must(string(payload) == "echo: hello", "payload mismatch")
	// The second byte's top bit is the MASK bit; on a server frame it is clear.
	must(data[1]&0x80 == 0, "server frames must not be masked")

	// The close frame the server appended, right after the text frame.
	closeOpcode, closePayload, _ := parseFrame(data[consumed:])
	code := binary.BigEndian.Uint16(closePayload)
	fmt.Printf("  then    : opcode 0x%x (close), status code %d\n", closeOpcode, code)
	must(closeOpcode == opcodeClose && code == 1000, "expected close 1000")
}

func main() {
	// A known-answer test straight out of RFC 6455 section 1.3: if our accept
	// computation is right, this exact key must produce this exact value.
	must(acceptKey("dGhlIHNhbXBsZSBub25jZQ==") == "s3pPLMBiTxaQ9kYGzzhZRbK+xOo=", "RFC accept example")
	fmt.Println("RFC 6455's own example handshake verifies against our acceptKey()")

	// And the RFC's example frame: a masked text frame carrying "Hello".
	rfcFrame := buildFrame([]byte("Hello"), opcodeText, []byte{0x37, 0xfa, 0x21, 0x3d})
	must(fmt.Sprintf("% x", rfcFrame) == "81 85 37 fa 21 3d 7f 9f 4d 51 58", "RFC frame example")
	fmt.Printf("RFC 6455's own example frame verifies too: % x\n", rfcFrame)
	fmt.Println("  81 = FIN+text, 85 = MASKED + length 5, then 4 mask bytes, " +
		"then 5 masked bytes")
	fmt.Println()

	listener, err := net.Listen("tcp", "127.0.0.1:0") // port 0 = "OS, pick any free port"
	if err != nil {
		log.Fatal(err)
	}
	defer listener.Close()

	go func() {
		conn, err := listener.Accept()
		if err != nil {
			return
		}
		rawServer(conn)
	}()

	rawClient(listener.Addr().String())

	fmt.Println("\nOK")
}
