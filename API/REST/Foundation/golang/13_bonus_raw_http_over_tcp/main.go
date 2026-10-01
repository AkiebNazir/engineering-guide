/*
FOUNDATION BONUS - What is an HTTP request, really? (optional, read after level 00)
=======================================================================================
Level 00 built a working endpoint using net/http and never asked what that
library does for you underneath. This file answers that: an HTTP server is a
program that reads bytes off a TCP socket, and those bytes happen to follow a
text format everyone agreed on. This proves it by building both the request
AND the response BY HAND - no net/http, nothing but the raw "net" package's
TCP listener.

This is optional. Nothing in levels 01+ depends on it. It exists to answer
"but what is a framework actually doing for me?" once you're curious.

You will learn
  - a "web request" is plain ASCII text sent over a plain TCP connection
  - the exact wire format: request line, headers, a blank line, then an optional body
  - a response has the same shape: status line, headers, blank line, body
  - why every response needs Content-Length: it is the only way the client
    knows where the body ends (the connection itself does not signal that)

Run it   go run ./REST/Foundation/golang/13_bonus_raw_http_over_tcp
*/
package main

import (
	"bufio"
	"fmt"
	"log"
	"net"
	"strings"
)

var responseBody = []byte("hello from a hand-written HTTP response\n")

func handleOneConnection(conn net.Conn) {
	defer conn.Close()

	// Read whatever the client sent, line by line, until the blank line that
	// ends the headers. We do not even need to understand it for level 00.
	// (level 00 used net/http, which does exactly this parsing for you.)
	reader := bufio.NewReader(conn)
	var rawRequest strings.Builder
	for {
		line, err := reader.ReadString('\n')
		rawRequest.WriteString(line)
		if err != nil || line == "\r\n" {
			break
		}
	}
	fmt.Println("---- raw request bytes received by the server ----")
	fmt.Print(rawRequest.String())

	// We write every line of the response ourselves: status line, headers
	// (one per line, each ending \r\n), a BLANK line, then the body.
	response := fmt.Sprintf(
		"HTTP/1.1 200 OK\r\n"+
			"Content-Type: text/plain\r\n"+
			"Content-Length: %d\r\n"+
			"Connection: close\r\n"+
			"\r\n", len(responseBody))
	conn.Write([]byte(response))
	conn.Write(responseBody)
}

func main() {
	listener, err := net.Listen("tcp", "127.0.0.1:0") // port 0 = "OS, pick me any free port"
	if err != nil {
		log.Fatal(err)
	}
	go func() {
		conn, err := listener.Accept()
		if err != nil {
			return
		}
		handleOneConnection(conn)
	}()

	// Now play the CLIENT: open our own TCP connection and type the request by hand.
	client, err := net.Dial("tcp", listener.Addr().String())
	if err != nil {
		log.Fatal(err)
	}
	requestText := fmt.Sprintf(
		"GET / HTTP/1.1\r\n"+
			"Host: %s\r\n"+
			"Connection: close\r\n"+
			"\r\n", listener.Addr().String())
	client.Write([]byte(requestText))

	responseBuf := make([]byte, 4096)
	n, _ := client.Read(responseBuf)
	responseText := string(responseBuf[:n])
	client.Close()
	listener.Close()

	fmt.Println("---- raw response bytes received by the client ----")
	fmt.Print(responseText)

	statusLine := strings.SplitN(responseText, "\r\n", 2)[0]
	parts := strings.SplitN(responseText, "\r\n\r\n", 2)
	headerBlock, body := parts[0], parts[1]
	expectedLength := len(responseBody)

	if statusLine != "HTTP/1.1 200 OK" {
		panic("FAILED: wrong status line: " + statusLine)
	}
	if !strings.Contains(headerBlock, fmt.Sprintf("Content-Length: %d", expectedLength)) {
		panic("FAILED: missing/wrong Content-Length header")
	}
	if body != string(responseBody) {
		panic("FAILED: body mismatch")
	}
	fmt.Println("OK")
}
