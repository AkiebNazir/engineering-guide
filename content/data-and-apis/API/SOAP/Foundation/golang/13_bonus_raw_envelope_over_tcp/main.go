/*
FOUNDATION BONUS - What is a SOAP call, really? (optional, read after level 00)
==================================================================================
Every level so far used net/http and encoding/xml and never asked what those
do underneath. This file answers that: a SOAP call is a string of text sent
over a TCP socket. Nothing more. It proves it by building the HTTP request AND
the SOAP envelope by hand, as string concatenation, sending them over a bare
"net" socket, and picking the answer apart with strings.Index - no net/http,
no XML library of any kind.

This is optional. Nothing in levels 01-12 depends on it. It exists to answer
"but what is all that XML machinery actually doing for me?" once you are
curious - and to make one specific point: SOAP's reputation for heaviness comes
from the TOOLING (WSDL generators, WS-* stacks), not from the wire format,
which is this small.

WHY YOU MUST NOT DO THIS FOR REAL: the parsing below is strings.Index. It
breaks the moment the server uses a different namespace prefix, adds
whitespace, escapes a character as &amp;, or splits the response across two
TCP reads. That fragility is exactly what a real XML parser exists to absorb.

You will learn
  - the complete bytes of a SOAP call: HTTP request line, headers, blank line,
    then an XML envelope as the body
  - that Content-Length is mandatory - it is the only thing telling the other
    side where the body ends
  - the SOAPAction header, and why it exists at the HTTP level at all
  - that "SOAP" is a convention about the body's shape, not a transport
  - exactly why string-matching XML is a bug waiting to happen

Run it   go run ./SOAP/Foundation/golang/13_bonus_raw_envelope_over_tcp
*/
package main

import (
	"bufio"
	"fmt"
	"log"
	"net"
	"strconv"
	"strings"
)

const (
	nsSOAP = "http://schemas.xmlsoap.org/soap/envelope/"
	nsTNS  = "http://foundation.example.com/soap"
)

// ---- the request envelope, typed out by hand, exactly as it goes on the wire ----
var requestEnvelope = `<?xml version="1.0" encoding="utf-8"?>` +
	`<soap:Envelope xmlns:soap="` + nsSOAP + `">` +
	`<soap:Header/>` +
	`<soap:Body><t:Ping xmlns:t="` + nsTNS + `"><t:who>raw socket</t:who></t:Ping></soap:Body>` +
	`</soap:Envelope>`

var responseEnvelope = `<?xml version="1.0" encoding="utf-8"?>` +
	`<soap:Envelope xmlns:soap="` + nsSOAP + `">` +
	`<soap:Body><t:PingResponse xmlns:t="` + nsTNS + `"><t:message>Pong</t:message></t:PingResponse></soap:Body>` +
	`</soap:Envelope>`

// buildHTTPRequest: four parts, and that is the entire HTTP protocol for our
// purposes: a request line, some headers (one per line), a BLANK line, then
// the body. Every line ends with \r\n - carriage return AND line feed, not
// just \n.
func buildHTTPRequest(hostHeader, body string) string {
	return "POST /soap HTTP/1.1\r\n" +
		"Host: " + hostHeader + "\r\n" +
		"Content-Type: text/xml; charset=utf-8\r\n" +
		// SOAPAction is SOAP 1.1's one concession to the HTTP layer: it lets a
		// proxy or firewall route on the operation without parsing any XML.
		`SOAPAction: "` + nsTNS + `/Ping"` + "\r\n" +
		"Content-Length: " + strconv.Itoa(len(body)) + "\r\n" +
		"Connection: close\r\n" +
		"\r\n" +
		body
}

// buildHTTPResponse: a response has the same four parts, with a status line
// at the top instead of a request line.
func buildHTTPResponse(body string) string {
	return "HTTP/1.1 200 OK\r\n" +
		"Content-Type: text/xml; charset=utf-8\r\n" +
		"Content-Length: " + strconv.Itoa(len(body)) + "\r\n" +
		"Connection: close\r\n" +
		"\r\n" +
		body
}

// serveOneConnection is the whole server: accept one connection, read the
// request, write bytes back. Doing the header-then-body read correctly here is
// most of what net/http was quietly handling for us in every other level.
func serveOneConnection(listener net.Listener) {
	conn, err := listener.Accept()
	if err != nil {
		return
	}
	defer conn.Close()

	reader := bufio.NewReader(conn)
	var headerBlock strings.Builder
	contentLength := 0
	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			return
		}
		headerBlock.WriteString(line)
		if strings.HasPrefix(strings.ToLower(line), "content-length:") {
			n, _ := strconv.Atoi(strings.TrimSpace(line[len("content-length:"):]))
			contentLength = n
		}
		if line == "\r\n" {
			break
		}
	}

	body := make([]byte, contentLength)
	read := 0
	for read < contentLength {
		n, err := reader.Read(body[read:])
		if err != nil {
			return
		}
		read += n
	}

	fmt.Println("---- raw bytes the server received ----")
	fmt.Print(headerBlock.String())
	fmt.Println(string(body))

	// "Dispatch", string-matching style. This is the fragile part, on purpose.
	if strings.Contains(string(body), "Ping") {
		conn.Write([]byte(buildHTTPResponse(responseEnvelope)))
	} else {
		conn.Write([]byte(buildHTTPResponse("<unknown/>")))
	}
}

func main() {
	listener, err := net.Listen("tcp", "127.0.0.1:0") // port 0 = "OS, give me any free port"
	if err != nil {
		log.Fatal(err)
	}
	go serveOneConnection(listener)

	// ---- now play the CLIENT, with nothing but a socket ----
	client, err := net.Dial("tcp", listener.Addr().String())
	if err != nil {
		log.Fatal(err)
	}
	client.Write([]byte(buildHTTPRequest(listener.Addr().String(), requestEnvelope)))

	var received strings.Builder
	buf := make([]byte, 4096)
	for {
		n, err := client.Read(buf) // "Connection: close" means Read returns EOF at the end
		if n > 0 {
			received.Write(buf[:n])
		}
		if err != nil {
			break
		}
	}
	client.Close()
	listener.Close()

	text := received.String()
	fmt.Println("---- raw bytes the client received ----")
	fmt.Print(text)

	parts := strings.SplitN(text, "\r\n", 2)
	statusLine, rest := parts[0], parts[1]
	headerVsBody := strings.SplitN(rest, "\r\n\r\n", 2)
	headerBlock, body := headerVsBody[0], headerVsBody[1]

	// ---- "parsing" XML with strings.Index, to show why nobody should ----
	start := strings.Index(body, "<t:message>") + len("<t:message>")
	end := strings.Index(body, "</t:message>")
	message := body[start:end]

	fmt.Println("---- what we extracted ----")
	fmt.Printf("status line : %s\n", statusLine)
	fmt.Printf("body length : %d bytes\n", len(body))
	fmt.Printf("<t:message> : %q\n", message)

	if statusLine != "HTTP/1.1 200 OK" {
		panic("FAILED: wrong status line: " + statusLine)
	}
	if !strings.Contains(headerBlock, "Content-Length: "+strconv.Itoa(len(responseEnvelope))) {
		panic("FAILED: missing/wrong Content-Length header")
	}
	if body != responseEnvelope {
		panic("FAILED: body mismatch")
	}
	if message != "Pong" {
		panic("FAILED: wrong message")
	}

	// The point, stated once: the same document with a different prefix is the
	// SAME document (level 04) - and our string matching would miss it entirely.
	equivalent := `<?xml version="1.0" encoding="utf-8"?>` +
		`<soap:Envelope xmlns:soap="` + nsSOAP + `">` +
		`<soap:Body><ns1:PingResponse xmlns:ns1="` + nsTNS + `">` +
		`<ns1:message>Pong</ns1:message></ns1:PingResponse></soap:Body>` +
		`</soap:Envelope>`
	if strings.Contains(equivalent, "<t:message>") {
		panic("FAILED: equivalent document unexpectedly matched the t: prefix")
	}
	if strings.Index(equivalent, "<t:message>") != -1 {
		panic("FAILED")
	}
	fmt.Println("\nthe same response with 'ns1:' instead of 't:' is an IDENTICAL document,")
	fmt.Println("and strings.Index(doc, \"<t:message>\") would return -1 on it. That is why")
	fmt.Println("levels 00-12 used a real XML parser, and why you should too.")

	fmt.Println("OK")
}
