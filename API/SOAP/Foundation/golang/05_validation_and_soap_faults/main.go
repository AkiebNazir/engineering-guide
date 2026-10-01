/*
FOUNDATION LEVEL 05 - Validation and <soap:Fault>: SOAP's own error channel
===============================================================================
Levels 01-04 answered bad input with a bare HTTP 400 and a plain-text string.
No SOAP client on earth understands that. SOAP defines exactly ONE error shape,
and it lives inside the envelope like everything else:

	<soap:Body>
	  <soap:Fault>
	    <faultcode>soap:Client</faultcode>              WHO is to blame
	    <faultstring>amount must be &gt; 0</faultstring>  human-readable why
	    <faultactor>...</faultactor>                    optional: which node failed
	    <detail>                                        optional: MACHINE-readable why
	      <t:InvalidAmount><t:field>amount</t:field></t:InvalidAmount>
	    </detail>
	  </soap:Fault>
	</soap:Body>

The two faultcodes that matter: `soap:Client` means "your message was wrong, do
not retry it unchanged", `soap:Server` means "we failed, retrying might work".
That single distinction is what level 12's retry logic keys off.

WATCH OUT: the Fault's children (faultcode, faultstring, detail) are NOT
namespaced in SOAP 1.1 - `<faultcode>`, never `<soap:faultcode>`, which is why
their struct tags below carry no namespace. The VALUE of faultcode, though, is a
namespaced QName (`soap:Client`). It is a genuine wart.

You will learn
  - the exact <soap:Fault> shape, and why a fault travels in the Body
  - soap:Client vs soap:Server, and the retry decision that hangs off it
  - <detail> with a named child element, so clients can branch on the error
    KIND instead of regex-matching an English sentence
  - modelling a fault as a Go error type, so validation code is just `return err`
  - that a fault is a normal, expected outcome - not a crash (level 08)

Run it   go run ./SOAP/Foundation/golang/05_validation_and_soap_faults
*/
package main

import (
	"bytes"
	"encoding/xml"
	"errors"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"strconv"
)

const (
	nsSOAP = "http://schemas.xmlsoap.org/soap/envelope/"
	nsTNS  = "http://foundation.example.com/soap"
)

var balances = map[string]float64{"ACC-1": 500.00}

// ---- the fault, as BOTH an XML shape and a Go error ----
type soapFault struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Fault"`

	// NOTE: no namespace in these tags. SOAP 1.1 fault children are unqualified.
	Code   string       `xml:"faultcode"`
	String string       `xml:"faultstring"`
	Detail *faultDetail `xml:"detail,omitempty"`
}

// The detail's child element NAME is the machine-readable error kind, so it has
// to be dynamic - hence xml.Name set at runtime rather than a fixed tag.
type faultDetail struct {
	// `,any` on DECODING means "match whatever child element is in there",
	// which is exactly what we need when the element's NAME is the payload.
	Named namedDetail `xml:",any"`
}

type namedDetail struct {
	XMLName xml.Name
	Fields  []detailField `xml:",any"`
}

type detailField struct {
	XMLName xml.Name
	Value   string `xml:",chardata"`
}

// Error makes soapFault usable with errors.As, so the operation code can just
// `return nil, fault(...)` and one place turns it into XML.
func (f *soapFault) Error() string { return f.Code + ": " + f.String }

func fault(code, message, detailName string, fields ...string) *soapFault {
	f := &soapFault{Code: code, String: message}
	if detailName != "" {
		named := namedDetail{XMLName: xml.Name{Space: nsTNS, Local: detailName}}
		for i := 0; i+1 < len(fields); i += 2 {
			named.Fields = append(named.Fields, detailField{
				XMLName: xml.Name{Space: nsTNS, Local: fields[i]},
				Value:   fields[i+1],
			})
		}
		f.Detail = &faultDetail{Named: named}
	}
	return f
}

// ---- envelopes ----
type requestEnvelope struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Body    struct {
		// A POINTER, so nil tells us "this was not a Withdraw call at all",
		// which is a different failure from "a Withdraw with bad arguments".
		Withdraw *struct {
			AccountID *string `xml:"http://foundation.example.com/soap accountId"`
			Amount    *string `xml:"http://foundation.example.com/soap amount"`
		} `xml:"http://foundation.example.com/soap Withdraw"`
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

type withdrawResponse struct {
	XMLName xml.Name `xml:"http://foundation.example.com/soap WithdrawResponse"`
	Balance string   `xml:"http://foundation.example.com/soap balance"`
}

type responseEnvelope struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Body    struct {
		Response *withdrawResponse
		Fault    *soapFault
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

func marshalEnvelope(response *withdrawResponse, f *soapFault) []byte {
	var env responseEnvelope
	env.Body.Response, env.Body.Fault = response, f
	out, err := xml.Marshal(env)
	if err != nil {
		log.Fatal(err)
	}
	return append([]byte(xml.Header), out...)
}

// withdraw validates everything first, then acts. Every rejection is one return.
func withdraw(accountID, amountText *string) (*withdrawResponse, error) {
	if accountID == nil || amountText == nil {
		return nil, fault("soap:Client", "accountId and amount are both required",
			"MissingElement", "element", "accountId|amount")
	}
	amount, err := strconv.ParseFloat(*amountText, 64)
	if err != nil {
		return nil, fault("soap:Client", "amount is not a number: "+*amountText,
			"InvalidAmount", "field", "amount", "got", *amountText)
	}
	if amount <= 0 {
		return nil, fault("soap:Client", "amount must be greater than zero",
			"InvalidAmount", "field", "amount", "got", *amountText)
	}
	balance, known := balances[*accountID]
	if !known {
		return nil, fault("soap:Client", "no such account: "+*accountID,
			"AccountNotFound", "accountId", *accountID)
	}
	if balance < amount {
		// A BUSINESS fault: the message was perfectly well formed, the request
		// is simply not allowed. Still soap:Client - do not retry unchanged.
		return nil, fault("soap:Client", "insufficient funds", "InsufficientFunds",
			"available", fmt.Sprintf("%.2f", balance), "requested", *amountText)
	}

	balances[*accountID] = balance - amount
	return &withdrawResponse{Balance: fmt.Sprintf("%.2f", balances[*accountID])}, nil
}

func dispatch(raw []byte) (int, []byte) {
	response, err := func() (*withdrawResponse, error) {
		var env requestEnvelope
		if err := xml.Unmarshal(raw, &env); err != nil {
			return nil, fault("soap:Client", "malformed XML: "+err.Error(), "")
		}
		if env.Body.Withdraw == nil {
			return nil, fault("soap:Client", "expected a Withdraw element inside soap:Body",
				"UnknownOperation")
		}
		return withdraw(env.Body.Withdraw.AccountID, env.Body.Withdraw.Amount)
	}()

	var f *soapFault
	if errors.As(err, &f) {
		// SOAP 1.1 convention: a fault rides an HTTP 500, even when the CLIENT
		// is at fault. Level 06 lays out that whole status-code story.
		return http.StatusInternalServerError, marshalEnvelope(nil, f)
	}
	return http.StatusOK, marshalEnvelope(response, nil)
}

func handler(w http.ResponseWriter, r *http.Request) {
	raw, _ := io.ReadAll(r.Body)
	status, out := dispatch(raw)
	w.Header().Set("Content-Type", "text/xml; charset=utf-8")
	w.WriteHeader(status)
	w.Write(out)
}

// ---- the client side ----
func callWithdraw(url, params string) (int, []byte) {
	envelope := fmt.Sprintf(
		`<soap:Envelope xmlns:soap="%s"><soap:Header/><soap:Body>`+
			`<t:Withdraw xmlns:t="%s">%s</t:Withdraw></soap:Body></soap:Envelope>`,
		nsSOAP, nsTNS, params)
	return post(url, envelope)
}

func post(url, envelope string) (int, []byte) {
	res, err := http.Post(url, "text/xml; charset=utf-8", bytes.NewReader([]byte(envelope)))
	if err != nil {
		log.Fatal(err)
	}
	defer res.Body.Close()
	// A fault arrives as a 500 WITH a body. Never ignore the body of an error
	// response in SOAP: the body IS the error.
	raw, _ := io.ReadAll(res.Body)
	return res.StatusCode, raw
}

func parse(raw []byte) responseEnvelope {
	var env responseEnvelope
	if err := xml.Unmarshal(raw, &env); err != nil {
		log.Fatal(err)
	}
	return env
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

	fmt.Println("== 1. a valid call, for contrast ==")
	status, raw := callWithdraw(url, "<t:accountId>ACC-1</t:accountId><t:amount>100.00</t:amount>")
	env := parse(raw)
	fmt.Printf("  Withdraw(ACC-1, 100.00) -> HTTP %d, balance=%s\n", status, env.Body.Response.Balance)
	if status != http.StatusOK || env.Body.Response.Balance != "400.00" {
		panic("FAILED")
	}

	fmt.Println("\n== 2. the full raw fault, once, so the shape is concrete ==")
	status, raw = callWithdraw(url, "<t:accountId>ACC-1</t:accountId><t:amount>-5</t:amount>")
	fmt.Printf("  HTTP %d\n", status)
	fmt.Println("  " + string(bytes.ReplaceAll(raw, []byte("><"), []byte(">\n  <"))))

	fmt.Println("== 3. every validation failure, as a fault ==")
	cases := []struct {
		label, params, detail string
	}{
		{"negative amount", "<t:accountId>ACC-1</t:accountId><t:amount>-5</t:amount>", "InvalidAmount"},
		{"not a number", "<t:accountId>ACC-1</t:accountId><t:amount>ten</t:amount>", "InvalidAmount"},
		{"unknown account", "<t:accountId>ACC-9</t:accountId><t:amount>5</t:amount>", "AccountNotFound"},
		{"too poor", "<t:accountId>ACC-1</t:accountId><t:amount>9999</t:amount>", "InsufficientFunds"},
		{"missing element", "<t:accountId>ACC-1</t:accountId>", "MissingElement"},
	}
	for _, c := range cases {
		status, raw = callWithdraw(url, c.params)
		f := parse(raw).Body.Fault
		fmt.Printf("  %-16s -> HTTP %d  %-12s <%s>  %q\n",
			c.label, status, f.Code, f.Detail.Named.XMLName.Local, f.String)
		if status != http.StatusInternalServerError || f.Code != "soap:Client" ||
			f.Detail.Named.XMLName.Local != c.detail {
			panic("FAILED")
		}
	}

	fmt.Println("\n== 4. why <detail> matters: branch on the KIND, not on the English ==")
	_, raw = callWithdraw(url, "<t:accountId>ACC-1</t:accountId><t:amount>9999</t:amount>")
	detail := parse(raw).Body.Fault.Detail.Named
	fields := map[string]string{}
	for _, field := range detail.Fields {
		fields[field.XMLName.Local] = field.Value
	}
	fmt.Printf("  caught <%s> with %v\n", detail.XMLName.Local, fields)
	fmt.Println("  -> a client can show 'you have 400.00, you asked for 9999' without parsing prose")
	if fields["available"] != "400.00" || fields["requested"] != "9999" {
		panic("FAILED")
	}

	fmt.Println("\n== 5. malformed XML is a fault too, not a stack trace ==")
	status, raw = post(url, "<soap:Envelope><not-closed>")
	f := parse(raw).Body.Fault
	fmt.Printf("  garbage in -> HTTP %d  %s  %q\n", status, f.Code, f.String)
	if status != http.StatusInternalServerError || f.Code != "soap:Client" {
		panic("FAILED")
	}

	fmt.Println("\nOK")
}
