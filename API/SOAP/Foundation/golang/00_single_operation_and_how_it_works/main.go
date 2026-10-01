/*
FOUNDATION LEVEL 00 (start here) - A basic SOAP endpoint, explained end to end
=================================================================================
If someone says "build me a basic SOAP endpoint", THIS is what they mean: one
HTTP server, one URL that accepts POSTs, one operation. A client posts an XML
document called an ENVELOPE; the server reads which operation was asked for,
does the work, and posts back another envelope. Nothing about WSDL, namespaces,
faults or security yet - just enough to watch the whole loop happen once.

THE MENTAL MODEL (read this before the code)

	SOAP is "XML instead of JSON, riding the same plain HTTP you already know".
	There is no magic transport. It is still:
	    POST /soap HTTP/1.1  +  a body of bytes  ->  200 OK  +  a body of bytes
	The only differences from a REST call are:
	  - the body is always an XML <Envelope>, never bare JSON
	  - the URL does NOT say what you want: ONE url serves every operation, and
	    the operation name is the first element INSIDE the envelope's <Body>
	    (so the server DISPATCHES on XML content, not on the path or the verb)
	Level 13 proves the "plain HTTP" claim by typing a whole envelope over a
	bare TCP socket with no libraries at all.

You will learn
  - the anatomy of a SOAP envelope at a glance: Envelope > Body > <OperationName>
  - that one SOAP endpoint = one URL + one HTTP verb (POST), always
  - how a server dispatches: look at the name of the first child of <Body>
  - how encoding/xml spells a namespaced element in a struct tag:
    `xml:"<namespace> <localname>"` - the space is the separator
  - that SOAP still obeys plain HTTP rules underneath - a wrong URL is a plain
    old 404, nothing SOAP-ish about it

Run it         go run ./SOAP/Foundation/golang/00_single_operation_and_how_it_works
Keep serving   go run ./SOAP/Foundation/golang/00_single_operation_and_how_it_works -serve   (curl hint is printed on start)
*/
package main

import (
	"bytes"
	"encoding/xml"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
)

// Two namespaces, and you cannot avoid them even at level 00 (level 04 explains
// WHY they exist). Read them as "vocabularies":
//
//	nsSOAP = the envelope vocabulary, identical for every SOAP service on earth
//	nsTNS  = OUR service's own vocabulary ("target namespace"), our operations
const (
	nsSOAP = "http://schemas.xmlsoap.org/soap/envelope/"
	nsTNS  = "http://foundation.example.com/soap"
)

// requestEnvelope is the GENERIC shape: we do not yet know which operation is
// inside, so Body keeps the raw inner XML plus the first child's NAME.
//
//	`xml:",innerxml"` = "give me the raw bytes between the tags"
//	`xml:",any"`      = "match whatever element is here, whatever it is called"
//
// Together they are the standard Go recipe for "dispatch first, decode later".
type requestEnvelope struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Body    struct {
		Inner     []byte `xml:",innerxml"`
		Operation struct {
			XMLName xml.Name
		} `xml:",any"`
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

// The typed request for THIS operation, decoded in a second pass.
type pingRequest struct {
	XMLName xml.Name `xml:"http://foundation.example.com/soap Ping"`
	Who     string   `xml:"http://foundation.example.com/soap who"`
}

// What the CLIENT builds: the same Envelope > Body > operation nesting, only
// with a concrete operation type instead of "whatever is in there".
type pingCall struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Body    struct {
		Ping pingRequest
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

// ---- the response side: the same envelope shape, built from structs ----
type responseEnvelope struct {
	XMLName xml.Name     `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Body    responseBody `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

type responseBody struct {
	PingResponse *pingResponse
}

// By convention the answer to <Ping> is named <PingResponse>. Nothing enforces
// that here; a WSDL (see ../../labs) would.
type pingResponse struct {
	XMLName xml.Name `xml:"http://foundation.example.com/soap PingResponse"`
	Message string   `xml:"http://foundation.example.com/soap message"`
}

// dispatch is the SOAP part of a SOAP server, in ten lines: parse the envelope,
// look at the ONE element inside <Body>, and switch on its name. That element's
// name IS the operation - there is no route table.
func dispatch(raw []byte) ([]byte, error) {
	var env requestEnvelope
	if err := xml.Unmarshal(raw, &env); err != nil {
		return nil, fmt.Errorf("not a SOAP envelope: %w", err)
	}

	// xml.Name splits a qualified name into its two halves: Space is the
	// namespace, Local is the tag itself. Matching on BOTH is the correct
	// habit from day one (level 04 shows what matching only Local costs you).
	name := env.Body.Operation.XMLName
	if name.Space != nsTNS || name.Local != "Ping" {
		// The GROWN-UP answer is a <soap:Fault> (level 05); for now we keep
		// level 00 honest and tiny by refusing to invent one.
		return nil, fmt.Errorf("this endpoint has no operation named {%s}%s", name.Space, name.Local)
	}

	var request pingRequest
	if err := xml.Unmarshal(env.Body.Inner, &request); err != nil {
		return nil, err
	}

	out, err := xml.Marshal(responseEnvelope{
		Body: responseBody{PingResponse: &pingResponse{Message: "Pong"}},
	})
	if err != nil {
		return nil, err
	}
	// Go's marshaller writes xmlns="..." on the elements instead of declaring a
	// soap: prefix once at the top. Both spellings mean EXACTLY the same thing
	// to any parser (level 04) - it is just more verbose to read.
	return append([]byte(xml.Header), out...), nil
}

func handler(w http.ResponseWriter, r *http.Request) {
	// Note there is no GET branch at all: a SOAP endpoint answers POST, and
	// only POST, because every request carries an XML document as its body.
	if r.URL.Path != "/soap" {
		w.WriteHeader(http.StatusNotFound) // plain HTTP rules still apply, see level 06
		return
	}

	raw, err := io.ReadAll(r.Body)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		return
	}

	out, err := dispatch(raw)
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		return
	}

	// "text/xml" is the SOAP 1.1 content type (1.2 uses application/soap+xml).
	w.Header().Set("Content-Type", "text/xml; charset=utf-8")
	w.WriteHeader(http.StatusOK)
	w.Write(out)
}

func main() {
	serve := flag.Bool("serve", false, "keep serving on :8080 instead of running the demo")
	flag.Parse()

	mux := http.NewServeMux()
	mux.HandleFunc("/", handler)

	if *serve {
		fmt.Print("listening on http://localhost:8080/soap - try:\n\n")
		fmt.Printf("  curl -s -X POST localhost:8080/soap -H 'Content-Type: text/xml' -d \\\n"+
			"    '<soap:Envelope xmlns:soap=\"%s\"><soap:Body><Ping xmlns=\"%s\"/></soap:Body></soap:Envelope>'\n\n",
			nsSOAP, nsTNS)
		log.Fatal(http.ListenAndServe("127.0.0.1:8080", mux))
	}

	// port 0 = "operating system, hand me any free port", so this demo never
	// collides with anything already listening on your machine.
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(listener, mux)
	base := "http://" + listener.Addr().String()

	// THE CLIENT. curl, a Java app, or a generated stub all do exactly this:
	// build an envelope, POST it, parse the envelope that comes back.
	var call pingCall
	call.Body.Ping.Who = "level 00 demo"
	requestXML, err := xml.Marshal(call)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("---- request body we POST ----")
	fmt.Println(string(requestXML))

	res, err := http.Post(base+"/soap", "text/xml; charset=utf-8", bytes.NewReader(requestXML))
	if err != nil {
		log.Fatal(err)
	}
	raw, _ := io.ReadAll(res.Body)
	res.Body.Close()

	fmt.Println("---- response body we got back ----")
	fmt.Println(string(raw))

	// Walk down the same three steps on the way out: Envelope > Body > operation.
	var parsed struct {
		XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
		Body    struct {
			PingResponse pingResponse `xml:"http://foundation.example.com/soap PingResponse"`
		} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
	}
	if err := xml.Unmarshal(raw, &parsed); err != nil {
		log.Fatal(err)
	}

	fmt.Printf("HTTP status      : %d   (SOAP success is a boring 200, see level 06)\n", res.StatusCode)
	fmt.Printf("parsed <message> : %q\n", parsed.Body.PingResponse.Message)
	if res.StatusCode != http.StatusOK || parsed.Body.PingResponse.Message != "Pong" {
		panic("FAILED")
	}

	// Same server, wrong URL: SOAP adds nothing here. It is plain HTTP.
	bad, err := http.Post(base+"/nope", "text/xml", bytes.NewReader(requestXML))
	if err != nil {
		log.Fatal(err)
	}
	bad.Body.Close()
	fmt.Printf("POST /nope       : %d   (a wrong URL is a normal HTTP 404, not a SOAP concept)\n", bad.StatusCode)
	if bad.StatusCode != http.StatusNotFound {
		panic("FAILED")
	}

	fmt.Println("OK")
}
