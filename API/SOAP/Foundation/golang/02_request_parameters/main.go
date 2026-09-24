/*
FOUNDATION LEVEL 02 - Request parameters: how a caller passes arguments
==========================================================================
REST has three places to put an argument: the path, the query string, and the
body. SOAP has exactly ONE: child elements of the operation element inside the
Body. There is no `/orders/42`, no `?limit=10` - `<GetQuote>` simply carries
`<symbol>` and `<quantity>` inside it, and the URL never changes.

That single rule is why one SOAP endpoint can serve fifty operations from one
URL, and why the wire format stays readable: every argument is a named element,
never a positional one.

You will learn
  - "document/literal wrapped" - the universal shape: one wrapper element named
    after the operation, its children are the parameters
  - letting encoding/xml map child elements straight onto typed struct fields,
    including ints - the decoder does the parsing and tells you when it fails
  - why a required parameter needs a POINTER field: without one you cannot tell
    "<quantity>0</quantity>" from "no <quantity> element at all"
  - that element ORDER is part of the contract in XML (unlike JSON keys), even
    though the decoder itself does not insist on it
  - how missing optional parameters differ from missing required ones

Run it   go run ./SOAP/Foundation/golang/02_request_parameters
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

var prices = map[string]float64{"ACME": 12.50, "GLOBEX": 340.00}

type requestEnvelope struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Body    struct {
		GetQuote *getQuote `xml:"http://foundation.example.com/soap GetQuote"`
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

// The parameters, as a struct. This IS the "document/literal wrapped" shape:
// the type is named after the operation, its fields are the parameters.
type getQuote struct {
	Symbol string `xml:"http://foundation.example.com/soap symbol"`

	// POINTERS for the parameters where absence matters:
	//   *int    - nil means the element was missing; 0 means it was sent as 0
	//   *string - nil means missing, so we can substitute a DEFAULT
	// Without the pointer, "absent" and "zero value" are indistinguishable -
	// the single most common encoding/xml mistake.
	Quantity *int    `xml:"http://foundation.example.com/soap quantity"`
	Currency *string `xml:"http://foundation.example.com/soap currency"`
}

type responseEnvelope struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Body    struct {
		Response getQuoteResponse `xml:"http://foundation.example.com/soap GetQuoteResponse"`
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

type getQuoteResponse struct {
	Total    string `xml:"http://foundation.example.com/soap total"`
	Currency string `xml:"http://foundation.example.com/soap currency"`
}

func dispatch(raw []byte) (int, []byte) {
	var env requestEnvelope
	if err := xml.Unmarshal(raw, &env); err != nil {
		// A non-numeric <quantity> lands HERE: the decoder reports
		// "strconv.ParseInt: parsing \"three\": invalid syntax". XML is text,
		// and someone has to turn it into an int - here the decoder does it,
		// and level 05 turns this blunt 400 into a proper SOAP Fault.
		return http.StatusBadRequest, []byte("cannot decode request: " + err.Error())
	}

	request := env.Body.GetQuote
	if request == nil {
		return http.StatusBadRequest, []byte("unknown operation")
	}

	// ---- required parameters ----
	if request.Symbol == "" || request.Quantity == nil {
		return http.StatusBadRequest, []byte("missing required parameter (symbol, quantity)")
	}

	// ---- the OPTIONAL one: absent means "use the default", not "bad request".
	// In a real service the WSDL would say minOccurs="0" for exactly this.
	currency := "EUR"
	if request.Currency != nil {
		currency = *request.Currency
	}

	price, known := prices[request.Symbol]
	if !known {
		return http.StatusBadRequest, []byte("unknown symbol")
	}

	// The business logic works on plain typed Go values - which is the whole
	// reason the decoding above bothered to produce them.
	var out responseEnvelope
	out.Body.Response = getQuoteResponse{
		Total:    fmt.Sprintf("%.2f", price*float64(*request.Quantity)),
		Currency: currency,
	}
	body, err := xml.Marshal(out)
	if err != nil {
		return http.StatusInternalServerError, []byte(err.Error())
	}
	return http.StatusOK, append([]byte(xml.Header), body...)
}

func handler(w http.ResponseWriter, r *http.Request) {
	raw, _ := io.ReadAll(r.Body)
	status, out := dispatch(raw)
	w.Header().Set("Content-Type", "text/xml; charset=utf-8")
	w.WriteHeader(status)
	w.Write(out)
}

// callGetQuote is the client side of the same rule: one element per named
// parameter, built as a string here so the wire shape stays in plain sight.
func callGetQuote(url string, params string) (int, []byte) {
	envelope := fmt.Sprintf(
		`<soap:Envelope xmlns:soap="%s"><soap:Header/><soap:Body>`+
			`<t:GetQuote xmlns:t="%s">%s</t:GetQuote>`+
			`</soap:Body></soap:Envelope>`, nsSOAP, nsTNS, params)
	res, err := http.Post(url, "text/xml; charset=utf-8", bytes.NewReader([]byte(envelope)))
	if err != nil {
		log.Fatal(err)
	}
	defer res.Body.Close()
	raw, _ := io.ReadAll(res.Body)
	return res.StatusCode, raw
}

func parseQuote(raw []byte) getQuoteResponse {
	var env responseEnvelope
	if err := xml.Unmarshal(raw, &env); err != nil {
		log.Fatal(err)
	}
	return env.Body.Response
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

	fmt.Println("== 1. all parameters supplied ==")
	status, raw := callGetQuote(url,
		"<t:symbol>ACME</t:symbol><t:quantity>4</t:quantity><t:currency>USD</t:currency>")
	quote := parseQuote(raw)
	fmt.Printf("  GetQuote(ACME, 4, USD) -> %d total=%s %s\n", status, quote.Total, quote.Currency)
	if status != http.StatusOK || quote.Total != "50.00" || quote.Currency != "USD" {
		panic("FAILED")
	}

	fmt.Println("\n== 2. the OPTIONAL parameter left out entirely ==")
	status, raw = callGetQuote(url, "<t:symbol>GLOBEX</t:symbol><t:quantity>2</t:quantity>")
	quote = parseQuote(raw)
	fmt.Printf("  GetQuote(GLOBEX, 2)    -> %d currency=%s   (defaulted, not an error)\n",
		status, quote.Currency)
	if status != http.StatusOK || quote.Currency != "EUR" || quote.Total != "680.00" {
		panic("FAILED")
	}

	fmt.Println("\n== 3. a REQUIRED parameter left out ==")
	status, raw = callGetQuote(url, "<t:symbol>ACME</t:symbol>")
	fmt.Printf("  GetQuote(ACME)         -> %d %q\n", status, raw)
	if status != http.StatusBadRequest {
		panic("FAILED")
	}

	fmt.Println("\n== 4. right element, wrong kind of text ==")
	status, raw = callGetQuote(url, "<t:symbol>ACME</t:symbol><t:quantity>three</t:quantity>")
	fmt.Printf("  quantity='three'       -> %d %q\n", status, raw)
	if status != http.StatusBadRequest || !bytes.Contains(raw, []byte("invalid syntax")) {
		panic("FAILED")
	}

	fmt.Println("\n== 5. quantity=0 is NOT the same as no quantity ==")
	status, raw = callGetQuote(url, "<t:symbol>ACME</t:symbol><t:quantity>0</t:quantity>")
	quote = parseQuote(raw)
	fmt.Printf("  quantity=0             -> %d total=%s   (accepted: the pointer was non-nil)\n",
		status, quote.Total)
	if status != http.StatusOK || quote.Total != "0.00" {
		panic("FAILED")
	}

	fmt.Println("\nOK")
}
