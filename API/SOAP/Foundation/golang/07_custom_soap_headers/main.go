/*
FOUNDATION LEVEL 07 - Custom SOAP headers: metadata inside the envelope
===========================================================================
Level 01 left <soap:Header> empty. This is what it is for: elements that are
ABOUT the message rather than part of the request. Routing, correlation ids,
transaction ids, session tokens, timestamps - all of it goes in the Header, in
your own namespace, as ordinary XML.

SOAP HEADER vs HTTP HEADER - the distinction that justifies all this XML:

	an HTTP header dies at the next hop. The envelope does not. If a message
	travels HTTP -> message queue -> another HTTP call, the SOAP Header rides
	along untouched, and it can be signed as part of the document (WS-Security
	does exactly that - see ../../labs/golang/04_ws_security_username_token).
	That is the "SOAP is transport-independent" claim, made concrete.

The industry standardised the obvious headers as WS-Addressing:

	<wsa:MessageID>  this message's unique id
	<wsa:To>         the intended destination
	<wsa:Action>     which operation (so infrastructure can route WITHOUT
	                 parsing the Body - the point of the exercise below)
	<wsa:RelatesTo>  "this is the reply to MessageID X"

You will learn
  - putting your own elements in <soap:Header>, in your own namespace
  - reading the Header BEFORE the Body - the dispatcher's real order of work
  - a WS-Addressing-style MessageID / Action / RelatesTo round trip
  - why headers survive hops and re-transports when HTTP headers do not
  - mustUnderstand="1": "reject the whole message if you don't know this
    header" - the one header attribute worth knowing (labs cover it properly)

Run it   go run ./SOAP/Foundation/golang/07_custom_soap_headers
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
	nsWSA  = "http://www.w3.org/2005/08/addressing" // the real WS-Addressing namespace
	nsTNS  = "http://foundation.example.com/soap"
)

// Headers this service knows how to honour. Anything else marked
// mustUnderstand="1" must be rejected outright.
var understood = map[xml.Name]bool{
	{Space: nsWSA, Local: "MessageID"}: true,
	{Space: nsWSA, Local: "To"}:        true,
	{Space: nsWSA, Local: "Action"}:    true,
	{Space: nsTNS, Local: "TraceId"}:   true,
}

type requestEnvelope struct {
	XMLName xml.Name       `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Header  *requestHeader `xml:"http://schemas.xmlsoap.org/soap/envelope/ Header"`
	Body    struct {
		Reserve *struct {
			Seat string `xml:"http://foundation.example.com/soap seat"`
		} `xml:"http://foundation.example.com/soap Reserve"`
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

type requestHeader struct {
	MessageID string `xml:"http://www.w3.org/2005/08/addressing MessageID"`
	To        string `xml:"http://www.w3.org/2005/08/addressing To"`
	Action    string `xml:"http://www.w3.org/2005/08/addressing Action"`
	TraceID   string `xml:"http://foundation.example.com/soap TraceId"`

	// Every header child, whatever it is called, so we can enforce
	// mustUnderstand on elements we have never heard of.
	Children []headerChild `xml:",any"`
}

type headerChild struct {
	XMLName        xml.Name
	MustUnderstand string `xml:"http://schemas.xmlsoap.org/soap/envelope/ mustUnderstand,attr"`
}

// ---- what we send back ----
type responseEnvelope struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Header  struct {
		// RelatesTo is how the caller matches this reply to its request - vital
		// once replies can come back out of order (or over a queue).
		RelatesTo string `xml:"http://www.w3.org/2005/08/addressing RelatesTo,omitempty"`
		TraceID   string `xml:"http://foundation.example.com/soap TraceId,omitempty"`
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Header"`
	Body struct {
		Reserve *reserveResponse
		Fault   *soapFault
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

type reserveResponse struct {
	XMLName       xml.Name `xml:"http://foundation.example.com/soap ReserveResponse"`
	ReservationID string   `xml:"http://foundation.example.com/soap reservationId"`
}

type soapFault struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Fault"`
	Code    string   `xml:"faultcode"`
	String  string   `xml:"faultstring"`
}

func marshalResponse(env responseEnvelope) []byte {
	out, err := xml.Marshal(env)
	if err != nil {
		log.Fatal(err)
	}
	return append([]byte(xml.Header), out...)
}

func faultResponse(code, message string) (int, []byte) {
	var env responseEnvelope
	env.Body.Fault = &soapFault{Code: code, String: message}
	return http.StatusInternalServerError, marshalResponse(env)
}

func dispatch(raw []byte) (int, []byte) {
	var request requestEnvelope
	if err := xml.Unmarshal(raw, &request); err != nil {
		return faultResponse("soap:Client", "malformed XML")
	}

	// ---- STEP 1: the Header, before we look at the Body at all ----
	// This is the real reason infrastructure likes SOAP headers: a router, a
	// logger or an auth gateway (levels 09-10) can do its whole job here and
	// never parse the payload.
	header := request.Header
	if header == nil || header.MessageID == "" {
		return faultResponse("soap:Client", "wsa:MessageID header is required")
	}

	// mustUnderstand="1" means "fail loudly rather than silently ignore me".
	// Note the ATTRIBUTE is namespaced: soap:mustUnderstand, not mustUnderstand.
	for _, child := range header.Children {
		must := child.MustUnderstand == "1" || child.MustUnderstand == "true"
		if must && !understood[child.XMLName] {
			return faultResponse("soap:MustUnderstand",
				fmt.Sprintf("header {%s}%s is marked mustUnderstand but this service does not know it",
					child.XMLName.Space, child.XMLName.Local))
		}
	}
	fmt.Printf("  [server] header read first: action=%q trace=%q id=%.13s...\n",
		header.Action, header.TraceID, header.MessageID)

	// ---- STEP 2: only now, the Body ----
	if request.Body.Reserve == nil {
		return faultResponse("soap:Client", "unknown operation")
	}
	if header.Action != "" && header.Action != nsTNS+"/Reserve" {
		// The Action header and the Body element must agree, or someone is
		// routing this message somewhere it does not belong.
		return faultResponse("soap:Client",
			"wsa:Action "+header.Action+" does not match the Body element")
	}

	// ---- STEP 3: answer WITH headers of our own ----
	var env responseEnvelope
	env.Header.RelatesTo = header.MessageID
	env.Header.TraceID = header.TraceID
	env.Body.Reserve = &reserveResponse{ReservationID: "RES-77"}
	return http.StatusOK, marshalResponse(env)
}

func handler(w http.ResponseWriter, r *http.Request) {
	raw, _ := io.ReadAll(r.Body)
	status, out := dispatch(raw)
	w.Header().Set("Content-Type", "text/xml; charset=utf-8")
	w.WriteHeader(status)
	w.Write(out)
}

func reserve(url, headers string) (int, responseEnvelope, []byte) {
	envelope := fmt.Sprintf(
		`<soap:Envelope xmlns:soap="%s"><soap:Header>%s</soap:Header><soap:Body>`+
			`<t:Reserve xmlns:t="%s"><t:seat>12A</t:seat></t:Reserve>`+
			`</soap:Body></soap:Envelope>`, nsSOAP, headers, nsTNS)
	res, err := http.Post(url, "text/xml; charset=utf-8", bytes.NewReader([]byte(envelope)))
	if err != nil {
		log.Fatal(err)
	}
	defer res.Body.Close()
	raw, _ := io.ReadAll(res.Body)

	var parsed responseEnvelope
	if err := xml.Unmarshal(raw, &parsed); err != nil {
		log.Fatal(err)
	}
	return res.StatusCode, parsed, raw
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

	messageID := "urn:uuid:4f3c1a20-0001-4000-8000-000000000042"
	addressing := fmt.Sprintf(
		`<wsa:MessageID xmlns:wsa="%s">%s</wsa:MessageID>`+
			`<wsa:To xmlns:wsa="%s">%s</wsa:To>`+
			`<wsa:Action xmlns:wsa="%s">%s/Reserve</wsa:Action>`+
			`<t:TraceId xmlns:t="%s">trace-abc</t:TraceId>`,
		nsWSA, messageID, nsWSA, url, nsWSA, nsTNS, nsTNS)

	fmt.Println("== 1. a request whose Header carries WS-Addressing metadata ==")
	status, parsed, raw := reserve(url, addressing)
	fmt.Println("  " + string(bytes.ReplaceAll(raw, []byte("><"), []byte(">\n  <"))))
	fmt.Printf("  -> HTTP %d, the reply's wsa:RelatesTo == our MessageID: %t\n",
		status, parsed.Header.RelatesTo == messageID)
	if status != http.StatusOK || parsed.Header.RelatesTo != messageID ||
		parsed.Header.TraceID != "trace-abc" || parsed.Body.Reserve.ReservationID != "RES-77" {
		panic("FAILED")
	}

	fmt.Println("\n== 2. a required header missing -> fault, Body never even parsed ==")
	status, parsed, _ = reserve(url, fmt.Sprintf(`<wsa:To xmlns:wsa="%s">%s</wsa:To>`, nsWSA, url))
	fmt.Printf("  -> HTTP %d %q\n", status, parsed.Body.Fault.String)
	if status != http.StatusInternalServerError || parsed.Body.Fault == nil {
		panic("FAILED")
	}

	fmt.Println("\n== 3. Action disagreeing with the Body element -> fault ==")
	mismatched := fmt.Sprintf(
		`<wsa:MessageID xmlns:wsa="%s">%s</wsa:MessageID>`+
			`<wsa:Action xmlns:wsa="%s">%s/CancelEverything</wsa:Action>`,
		nsWSA, messageID, nsWSA, nsTNS)
	status, parsed, _ = reserve(url, mismatched)
	fmt.Printf("  -> HTTP %d %q\n", status, parsed.Body.Fault.String)
	if status != http.StatusInternalServerError {
		panic("FAILED")
	}

	fmt.Println("\n== 4. mustUnderstand=\"1\" on a header we do not know ==")
	exotic := fmt.Sprintf(
		`<wsa:MessageID xmlns:wsa="%s">%s</wsa:MessageID>`+
			`<v:QuantumPriority xmlns:v="http://vendor.example.com" soap:mustUnderstand="1">high</v:QuantumPriority>`,
		nsWSA, messageID)
	status, parsed, _ = reserve(url, exotic)
	fmt.Printf("  -> HTTP %d %s   (ignoring it silently would be the dangerous choice)\n",
		status, parsed.Body.Fault.Code)
	if status != http.StatusInternalServerError || parsed.Body.Fault.Code != "soap:MustUnderstand" {
		panic("FAILED")
	}

	fmt.Println("\n== 5. the SAME header WITHOUT mustUnderstand is ignored happily ==")
	optional := fmt.Sprintf(
		`<wsa:MessageID xmlns:wsa="%s">%s</wsa:MessageID>`+
			`<v:QuantumPriority xmlns:v="http://vendor.example.com">high</v:QuantumPriority>`,
		nsWSA, messageID)
	status, _, _ = reserve(url, optional)
	fmt.Printf("  -> HTTP %d   (unknown-but-optional headers are skipped, by design)\n", status)
	if status != http.StatusOK {
		panic("FAILED")
	}

	fmt.Println("\nOK")
}
