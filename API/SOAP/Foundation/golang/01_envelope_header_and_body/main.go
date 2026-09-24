/*
FOUNDATION LEVEL 01 - Envelope anatomy: Header vs Body
==========================================================
Level 00 used only half the envelope. The full shape is fixed and tiny:

	<soap:Envelope>            the only legal root element
	  <soap:Header>            OPTIONAL, at most one, MUST come first
	    ...metadata...         who you are, trace ids, routing (levels 07-10)
	  </soap:Header>
	  <soap:Body>              REQUIRED, exactly one, MUST come last
	    <TheOperation>...      the actual payload: what you are asking for
	  </soap:Body>
	</soap:Envelope>

The split is the whole point of SOAP: BODY is the message for the final
recipient, HEADER is instructions for anyone handling the message along the way
(a gateway, a logger, an auth proxy). This level builds and parses both
explicitly, so that levels 07-10 are "put something in the Header" rather than
"learn a new concept".

You will learn
  - the four fixed parts of every SOAP message and their required order
  - Header is optional and Body is not - and how to reject a Body-less envelope
  - modelling "optional" in Go: a POINTER field is nil when the element was
    absent, which is exactly the distinction XML makes
  - why metadata belongs in the Header, not as extra fields in the Body
  - how to read both halves of a message with one xml.Unmarshal pass

Run it   go run ./SOAP/Foundation/golang/01_envelope_header_and_body
*/
package main

import (
	"bytes"
	"encoding/xml"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
)

const (
	nsSOAP = "http://schemas.xmlsoap.org/soap/envelope/"
	nsTNS  = "http://foundation.example.com/soap"
)

// ---- what we RECEIVE: both halves, in one pass ----
type requestEnvelope struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`

	// A POINTER, because <soap:Header> is optional. nil means "the element was
	// not there at all" - Go's cleanest way to express XML's optionality.
	Header *requestHeader `xml:"http://schemas.xmlsoap.org/soap/envelope/ Header"`

	// NOT a pointer: Body is mandatory, so an absent one is a broken message
	// and we want the zero value to be obviously empty.
	Body requestBody `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

type requestHeader struct {
	// The raw contents, so we can tell "<soap:Header/>" from a header that
	// actually carried something, even when we do not know the element names.
	Inner    []byte `xml:",innerxml"`
	CallerID string `xml:"http://foundation.example.com/soap CallerName"`
}

type requestBody struct {
	Inner []byte `xml:",innerxml"`
	Echo  *echo  `xml:"http://foundation.example.com/soap Echo"`
}

type echo struct {
	Text string `xml:"http://foundation.example.com/soap text"`
}

// ---- what we SEND: the same two halves ----
type responseEnvelope struct {
	XMLName xml.Name        `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Header  responseHeader  `xml:"http://schemas.xmlsoap.org/soap/envelope/ Header"`
	Body    responseEchoBdy `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

// Services commonly answer with a header of their own - here a trace id, so the
// client can correlate logs.
type responseHeader struct {
	TraceID string `xml:"http://foundation.example.com/soap TraceId"`
}

type responseEchoBdy struct {
	EchoResponse echoResponse `xml:"http://foundation.example.com/soap EchoResponse"`
}

type echoResponse struct {
	Text string `xml:"http://foundation.example.com/soap text"`
}

func dispatch(raw []byte) (int, []byte) {
	var env requestEnvelope
	if err := xml.Unmarshal(raw, &env); err != nil {
		return http.StatusBadRequest, []byte("not a SOAP envelope")
	}

	// ---- the HEADER half (metadata about the message) ----
	// A nil pointer here is NOT an error: Header is optional.
	empty := true
	caller := "<none>"
	if env.Header != nil {
		empty = len(bytes.TrimSpace(env.Header.Inner)) == 0
		if env.Header.CallerID != "" {
			caller = env.Header.CallerID
		}
	}
	fmt.Printf("  [server] header present=%t, empty=%t, caller=%s\n",
		env.Header != nil, empty, caller)

	// ---- the BODY half (the actual request) ----
	// Body is mandatory. A missing one is a malformed message, and level 05
	// will upgrade this blunt 400 into a proper <soap:Fault>.
	if len(bytes.TrimSpace(env.Body.Inner)) == 0 {
		return http.StatusBadRequest, []byte("envelope has no Body content")
	}
	if env.Body.Echo == nil {
		return http.StatusBadRequest, []byte("unknown operation")
	}

	out, err := xml.Marshal(responseEnvelope{
		Header: responseHeader{TraceID: "trace-0001"},
		Body:   responseEchoBdy{EchoResponse: echoResponse{Text: env.Body.Echo.Text}},
	})
	if err != nil {
		return http.StatusInternalServerError, []byte(err.Error())
	}
	return http.StatusOK, append([]byte(xml.Header), out...)
}

func handler(w http.ResponseWriter, r *http.Request) {
	raw, _ := io.ReadAll(r.Body)
	status, out := dispatch(raw)
	w.Header().Set("Content-Type", "text/xml; charset=utf-8")
	w.WriteHeader(status)
	w.Write(out)
}

func post(url string, body string) (int, []byte) {
	res, err := http.Post(url, "text/xml; charset=utf-8", bytes.NewReader([]byte(body)))
	if err != nil {
		log.Fatal(err)
	}
	defer res.Body.Close()
	raw, _ := io.ReadAll(res.Body)
	return res.StatusCode, raw
}

func main() {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	mux := http.NewServeMux()
	mux.HandleFunc("/soap", handler)
	go http.Serve(listener, mux)
	url := "http://" + listener.Addr().String() + "/soap"

	// Hand-written envelopes here, so the ORDER and the emptiness of the
	// Header are visible in the source rather than hidden behind a marshaller.
	emptyHeader := fmt.Sprintf(
		`<soap:Envelope xmlns:soap="%s"><soap:Header/>`+
			`<soap:Body><t:Echo xmlns:t="%s"><t:text>hello envelope</t:text></t:Echo></soap:Body>`+
			`</soap:Envelope>`, nsSOAP, nsTNS)

	fmt.Println("== 1. empty Header, one operation in the Body ==")
	status, raw := post(url, emptyHeader)
	var parsed struct {
		XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
		Header  struct {
			TraceID string `xml:"http://foundation.example.com/soap TraceId"`
		} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Header"`
		Body struct {
			Text string `xml:"http://foundation.example.com/soap EchoResponse>text"`
		} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
	}
	if err := xml.Unmarshal(raw, &parsed); err != nil {
		log.Fatal(err)
	}
	fmt.Printf("  -> %d  response Header TraceId=%q, Body text=%q\n",
		status, parsed.Header.TraceID, parsed.Body.Text)
	if status != http.StatusOK || parsed.Body.Text != "hello envelope" || parsed.Header.TraceID != "trace-0001" {
		panic("FAILED")
	}

	fmt.Println("\n== 2. a Header WITH metadata in it (a preview of levels 07-10) ==")
	withMetadata := fmt.Sprintf(
		`<soap:Envelope xmlns:soap="%s"><soap:Header>`+
			`<t:CallerName xmlns:t="%s">level-01-demo</t:CallerName></soap:Header>`+
			`<soap:Body><t:Echo xmlns:t="%s"><t:text>hello envelope</t:text></t:Echo></soap:Body>`+
			`</soap:Envelope>`, nsSOAP, nsTNS, nsTNS)
	status, _ = post(url, withMetadata)
	fmt.Printf("  -> %d   (the Body was identical; only the metadata changed)\n", status)
	if status != http.StatusOK {
		panic("FAILED")
	}

	fmt.Println("\n== 3. an envelope with NO Body is not a SOAP message at all ==")
	headless := fmt.Sprintf(`<soap:Envelope xmlns:soap="%s"><soap:Header/></soap:Envelope>`, nsSOAP)
	status, raw = post(url, headless)
	fmt.Printf("  -> %d %q   (Header alone is meaningless: Body is mandatory)\n", status, raw)
	if status != http.StatusBadRequest {
		panic("FAILED")
	}

	fmt.Println("\nOK")
}
