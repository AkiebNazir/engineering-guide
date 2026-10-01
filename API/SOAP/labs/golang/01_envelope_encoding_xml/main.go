/*
LAB 01 (basic) - SOAP envelopes with encoding/xml: structs in, XML out, XML in, structs out
===========================================================================================
You will learn
  - modelling a SOAP message as Go structs with `xml:` tags - the standard library is all you need
  - XML NAMESPACES in struct tags:   `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
    (the string before the space is the namespace, after it the local name)
  - the generic envelope pattern: Body holds an `Content []byte` with `xml:",innerxml"` OR a typed struct
  - marshalling with xml.MarshalIndent and prefix control (xmlns:soap="...")
  - unmarshalling a response, including a FAULT, and turning the Fault into a Go error type that
    works with errors.As
  - encoding/xml gotchas: unknown elements are ignored silently, xsd:decimal has no native Go type
    (use strings and shopspring/decimal or big.Rat), attributes vs elements, omitempty for optionals
  - the security note: Go's encoding/xml does not expand external entities (no XXE), but you should still
    bound the input size and depth - shown with an io.LimitReader

Run it   go run ./SOAP/labs/golang/01_envelope_encoding_xml
*/
package main

import (
	"bytes"
	"encoding/xml"
	"errors"
	"fmt"
	"io"
	"math/big"
	"strings"
)

const (
	nsSOAP = "http://schemas.xmlsoap.org/soap/envelope/"
	nsBank = "http://bank.example.com/ws"
)

// ---------------------------------------------------------------- request ---
type Envelope struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Header  *Header  `xml:"http://schemas.xmlsoap.org/soap/envelope/ Header,omitempty"`
	Body    Body     `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

type Header struct {
	CorrelationID string `xml:"http://bank.example.com/ws CorrelationId,omitempty"`
}

type Body struct {
	GetBalance         *GetBalance         `xml:"http://bank.example.com/ws GetBalance,omitempty"`
	GetBalanceResponse *GetBalanceResponse `xml:"http://bank.example.com/ws GetBalanceResponse,omitempty"`
	Fault              *Fault              `xml:"http://schemas.xmlsoap.org/soap/envelope/ Fault,omitempty"`
}

type GetBalance struct {
	AccountID string `xml:"http://bank.example.com/ws accountId"`
}

type GetBalanceResponse struct {
	Balance  string `xml:"http://bank.example.com/ws balance"` // xsd:decimal: keep as string, parse with big.Rat when needed
	Currency string `xml:"http://bank.example.com/ws currency"`
}

// Fault is BOTH the XML shape and a Go error.
type Fault struct {
	Code   string `xml:"faultcode"` // NOTE: 1.1 fault children are UNQUALIFIED (no namespace)
	String string `xml:"faultstring"`
	Detail *struct {
		Inner string `xml:",innerxml"`
	} `xml:"detail"`
}

func (f *Fault) Error() string { return fmt.Sprintf("SOAP fault %s: %s", f.Code, f.String) }

// ------------------------------------------------------------------ helpers ---
func marshal(env Envelope) []byte {
	out, err := xml.MarshalIndent(env, "", "  ")
	if err != nil {
		panic(err)
	}
	return append([]byte(xml.Header), out...)
}

// parse reads at most 1 MiB and returns the envelope, or the Fault as an error.
func parse(raw []byte) (*Envelope, error) {
	var env Envelope
	dec := xml.NewDecoder(io.LimitReader(bytes.NewReader(raw), 1<<20))
	if err := dec.Decode(&env); err != nil {
		return nil, fmt.Errorf("invalid SOAP message: %w", err)
	}
	if env.Body.Fault != nil {
		return &env, env.Body.Fault
	}
	return &env, nil
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	fmt.Println("== 1. struct -> XML ==")
	req := Envelope{Header: &Header{CorrelationID: "req-42"}, Body: Body{GetBalance: &GetBalance{AccountID: "ACC-1001"}}}
	wire := marshal(req)
	fmt.Println(string(wire))
	must(bytes.Contains(wire, []byte("GetBalance")) && bytes.Contains(wire, []byte(nsBank)), "namespaces are emitted")
	fmt.Println("  Note: encoding/xml writes a default xmlns on every element and cannot emit `soap:` prefixes. That is valid,")
	fmt.Println("  namespace-correct XML that compliant servers accept; for a legacy server that insists on the `soap:` prefix,")
	fmt.Println("  render the envelope from a text/template and use struct marshalling only for the Body payload.")

	fmt.Println("\n== 2. XML (from a server) -> struct ==")
	response := `<?xml version="1.0"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <GetBalanceResponse xmlns="http://bank.example.com/ws"><balance>1042.50</balance><currency>EUR</currency></GetBalanceResponse>
  </soap:Body>
</soap:Envelope>`
	env, err := parse([]byte(response))
	must(err == nil, fmt.Sprint(err))
	r := env.Body.GetBalanceResponse
	fmt.Printf("  balance=%q currency=%q\n", r.Balance, r.Currency)
	bal, _ := new(big.Rat).SetString(r.Balance) // exact decimal arithmetic, no float rounding
	fee, _ := new(big.Rat).SetString("0.10")
	fmt.Println("  balance - 0.10 =", new(big.Rat).Sub(bal, fee).FloatString(2), "(computed exactly with big.Rat)")
	must(new(big.Rat).Sub(bal, fee).FloatString(2) == "1042.40", "exact decimals")

	fmt.Println("\n== 3. the SAME element name in another namespace is NOT matched ==")
	wrongNS := strings.Replace(response, nsBank, "http://evil.example.com", 1)
	env, _ = parse([]byte(wrongNS))
	fmt.Println("  GetBalanceResponse decoded from the wrong namespace:", env.Body.GetBalanceResponse)
	must(env.Body.GetBalanceResponse == nil, "namespace-aware decoding")
	fmt.Println("  (Go silently ignores what it cannot map: ALWAYS check the fields you need are present)")

	fmt.Println("\n== 4. a Fault becomes a Go error ==")
	faultXML := `<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><soap:Fault>
  <faultcode>soap:Client</faultcode><faultstring>No such account: ACC-9</faultstring>
  <detail><AccountNotFound xmlns="http://bank.example.com/ws"><accountId>ACC-9</accountId></AccountNotFound></detail>
</soap:Fault></soap:Body></soap:Envelope>`
	_, err = parse([]byte(faultXML))
	var f *Fault
	if errors.As(err, &f) {
		fmt.Printf("  errors.As -> code=%q message=%q\n  detail XML: %s\n", f.Code, f.String, strings.TrimSpace(f.Detail.Inner))
	}
	must(f != nil && f.Code == "soap:Client" && strings.Contains(f.Detail.Inner, "AccountNotFound"), "fault as error")

	fmt.Println("\n== 5. garbage and oversized input ==")
	_, err = parse([]byte("<not-closed>"))
	fmt.Println("  malformed XML ->", err)
	must(err != nil, "malformed")
	huge := []byte(`<soap:Envelope xmlns:soap="` + nsSOAP + `"><soap:Body>` + strings.Repeat("<a>", 100) + strings.Repeat("x", 2<<20))
	_, err = parse(huge)
	fmt.Println("  2 MiB truncated by the limit reader ->", err)
	must(err != nil, "oversized")

	fmt.Println("\n== 6. escaping is automatic when you marshal ==")
	evil := Envelope{Body: Body{GetBalance: &GetBalance{AccountID: `</accountId><injected/>`}}}
	out := string(marshal(evil))
	fmt.Println(" ", strings.TrimSpace(out[strings.Index(out, "<accountId"):strings.Index(out, "</GetBalance>")]))
	must(!strings.Contains(out, "<injected/>"), "no XML injection")
	fmt.Println("  (struct marshalling escapes for you - the reason to prefer it over string concatenation)")
	fmt.Println("\nOK")
}
