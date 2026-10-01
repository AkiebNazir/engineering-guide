/*
FOUNDATION LEVEL 06 - HTTP status codes in a SOAP world
===========================================================
SOAP rides HTTP, so every response still has a status code - but SOAP uses
almost none of them. REST spends its error vocabulary on status codes (400,
401, 403, 404, 409, 422, ...). SOAP spends it inside <soap:Fault> and leaves
HTTP with essentially two codes:

	HTTP 200  +  <Body><XxxResponse>   it worked
	HTTP 500  +  <Body><soap:Fault>    it did not (SOAP 1.1, ANY fault)

That is the whole convention, and it surprises everyone: a 500 from a SOAP
service usually means "you sent a bad account number", not "the server is on
fire". SOAP 1.2 softened it - a sender fault SHOULD be HTTP 400 - so real
clients must treat "4xx or 5xx" as "read the body, there is a Fault in it".

THE FULL PICTURE (what comes from where)

	200 + response body   success                        SOAP decides
	500 + Fault body      any fault, SOAP 1.1            SOAP decides
	400 + Fault body      sender fault, SOAP 1.2         SOAP decides
	404                   wrong URL                      the HTTP layer
	405                   GET on a SOAP endpoint         the HTTP layer
	415                   wrong Content-Type             the HTTP layer
	401/403               an HTTP-level auth proxy       the HTTP layer
	-> rule of thumb: if the response HAS an envelope, the envelope is the truth.
	   If it does not, the request never reached the SOAP code at all.

You will learn
  - why a well-formed SOAP service returns 500 for a client's own mistake
  - the 1.1 (always 500) vs 1.2 (400 for sender faults) difference, including
    1.2's renamed Fault children: Code/Value and Reason/Text
  - which codes come from HTTP itself and never carry an envelope
  - that a SOAP client must always read the BODY of an error response
  - why SOAP does not need 404/409/422: the Fault's detail says it instead

Run it   go run ./SOAP/Foundation/golang/06_http_status_codes_in_soap
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
	"strings"
)

const (
	nsSOAP11 = "http://schemas.xmlsoap.org/soap/envelope/"
	nsSOAP12 = "http://www.w3.org/2003/05/soap-envelope"
	nsTNS    = "http://foundation.example.com/soap"
)

var soapContentTypes = []string{"text/xml", "application/soap+xml"}

// ---- SOAP 1.1 shapes ----
type fault11 struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Fault"`
	Code    string   `xml:"faultcode"`
	String  string   `xml:"faultstring"`
}

type pingResponse struct {
	XMLName xml.Name `xml:"http://foundation.example.com/soap PingResponse"`
	Message string   `xml:"http://foundation.example.com/soap message"`
}

type envelope11 struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Body    struct {
		Ping  *pingResponse
		Fault *fault11
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

// ---- SOAP 1.2 shapes: same idea, different spelling ----
// 1.2 renamed everything AND changed the recommended status code: namespaced
// children, Code/Value instead of faultcode, Reason/Text instead of
// faultstring, and Sender/Receiver instead of Client/Server.
type envelope12 struct {
	XMLName xml.Name `xml:"http://www.w3.org/2003/05/soap-envelope Envelope"`
	Body    struct {
		Fault struct {
			Value  string `xml:"http://www.w3.org/2003/05/soap-envelope Code>Value"`
			Reason string `xml:"http://www.w3.org/2003/05/soap-envelope Reason>Text"`
		} `xml:"http://www.w3.org/2003/05/soap-envelope Fault"`
	} `xml:"http://www.w3.org/2003/05/soap-envelope Body"`
}

func marshal(v any) []byte {
	out, err := xml.Marshal(v)
	if err != nil {
		log.Fatal(err)
	}
	return append([]byte(xml.Header), out...)
}

func response11(response *pingResponse, f *fault11) []byte {
	var env envelope11
	env.Body.Ping, env.Body.Fault = response, f
	return marshal(env)
}

func dispatch(raw []byte) (int, []byte) {
	var probe struct {
		XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
		Body    struct {
			Operation struct {
				XMLName xml.Name
			} `xml:",any"`
		} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
	}
	if err := xml.Unmarshal(raw, &probe); err != nil {
		return http.StatusInternalServerError,
			response11(nil, &fault11{Code: "soap:Client", String: "malformed XML"})
	}

	switch probe.Body.Operation.XMLName.Local {
	case "Ping":
		// Success: a plain 200.
		return http.StatusOK, response11(&pingResponse{Message: "Pong"}, nil)

	case "BadRequest":
		// The CLIENT is at fault, and SOAP 1.1 still says HTTP 500. This is
		// the line that makes SOAP 500s so misleading in dashboards.
		return http.StatusInternalServerError,
			response11(nil, &fault11{Code: "soap:Client", String: "you sent something wrong"})

	case "BadRequest12":
		var env envelope12
		env.Body.Fault.Value = "env:Sender"
		env.Body.Fault.Reason = "you sent something wrong"
		return http.StatusBadRequest, marshal(env) // the 1.2 way

	case "Explode":
		// We really did break. SAME status code as the client's mistake above;
		// only <faultcode> tells the two apart. That is why level 12 retries on
		// soap:Server and never on soap:Client.
		return http.StatusInternalServerError,
			response11(nil, &fault11{Code: "soap:Server", String: "database unavailable"})
	}

	return http.StatusInternalServerError, response11(nil, &fault11{
		Code:   "soap:Client",
		String: "unknown operation " + probe.Body.Operation.XMLName.Local,
	})
}

func handler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		// A SOAP endpoint takes POST only. A GET never reaches the SOAP code,
		// so there is no envelope to send back - this is pure HTTP.
		w.Header().Set("Allow", "POST")
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}
	if r.URL.Path != "/soap" {
		w.WriteHeader(http.StatusNotFound) // pure HTTP: wrong address
		return
	}

	contentType := strings.TrimSpace(strings.Split(r.Header.Get("Content-Type"), ";")[0])
	known := false
	for _, allowed := range soapContentTypes {
		if contentType == allowed {
			known = true
		}
	}
	if !known {
		w.WriteHeader(http.StatusUnsupportedMediaType) // pure HTTP: "I do not speak that"
		return
	}

	raw, _ := io.ReadAll(r.Body)
	status, out := dispatch(raw)
	w.Header().Set("Content-Type", "text/xml; charset=utf-8")
	w.WriteHeader(status)
	w.Write(out)
}

// hasEnvelope is the rule that makes a SOAP client robust: is there an envelope
// at all? If not, the request never got as far as the SOAP layer.
func hasEnvelope(raw []byte) bool {
	var probe struct {
		XMLName xml.Name
	}
	if err := xml.Unmarshal(raw, &probe); err != nil {
		return false
	}
	return probe.XMLName.Local == "Envelope"
}

func faultCode(raw []byte) string {
	var eleven envelope11
	if err := xml.Unmarshal(raw, &eleven); err == nil && eleven.Body.Fault != nil {
		return eleven.Body.Fault.Code
	}
	var twelve envelope12
	if err := xml.Unmarshal(raw, &twelve); err == nil {
		return twelve.Body.Fault.Value
	}
	return ""
}

func post(url, operation, contentType string) (int, []byte) {
	envelope := fmt.Sprintf(
		`<soap:Envelope xmlns:soap="%s"><soap:Body><t:%s xmlns:t="%s"/></soap:Body></soap:Envelope>`,
		nsSOAP11, operation, nsTNS)
	res, err := http.Post(url, contentType, bytes.NewReader([]byte(envelope)))
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
	mux.HandleFunc("/", handler)
	go http.Serve(listener, mux)
	base := "http://" + listener.Addr().String()
	url := base + "/soap"

	fmt.Println("== 1. codes the SOAP layer chooses (every one carries an envelope) ==")
	cases := []struct {
		label, operation string
		status           int
		code             string
	}{
		{"success", "Ping", 200, ""},
		{"client's fault (1.1)", "BadRequest", 500, "soap:Client"},
		{"client's fault (1.2)", "BadRequest12", 400, "env:Sender"},
		{"server's fault", "Explode", 500, "soap:Server"},
		{"unknown operation", "Nope", 500, "soap:Client"},
	}
	for _, c := range cases {
		status, raw := post(url, c.operation, "text/xml; charset=utf-8")
		code := faultCode(raw)
		fmt.Printf("  %-21s -> HTTP %d  envelope=%t  faultcode=%q\n",
			c.label, status, hasEnvelope(raw), code)
		if status != c.status || code != c.code || !hasEnvelope(raw) {
			panic("FAILED")
		}
	}

	fmt.Println("\n== 2. codes the HTTP layer chooses (NO envelope: never reached SOAP) ==")
	status, raw := post(url, "Ping", "application/json")
	fmt.Printf("  wrong Content-Type    -> HTTP %d  envelope=%t\n", status, hasEnvelope(raw))
	if status != http.StatusUnsupportedMediaType || hasEnvelope(raw) {
		panic("FAILED")
	}

	status, raw = post(base+"/wrong-url", "Ping", "text/xml")
	fmt.Printf("  wrong URL             -> HTTP %d  envelope=%t\n", status, hasEnvelope(raw))
	if status != http.StatusNotFound || hasEnvelope(raw) {
		panic("FAILED")
	}

	res, err := http.Get(url) // a GET, not a POST
	if err != nil {
		log.Fatal(err)
	}
	res.Body.Close()
	fmt.Printf("  GET instead of POST   -> HTTP %d  Allow: %s\n",
		res.StatusCode, res.Header.Get("Allow"))
	if res.StatusCode != http.StatusMethodNotAllowed {
		panic("FAILED")
	}

	fmt.Println("\n== 3. the takeaway a client must implement ==")
	fmt.Println("  1) never trust the status code alone - 500 usually means YOUR mistake")
	fmt.Println("  2) if the body parses as an Envelope, the Fault inside it is the real error")
	fmt.Println("  3) if it does not, the request never got past HTTP (bad URL/verb/content type)")
	fmt.Println("  4) retry on soap:Server / env:Receiver only - see level 12")

	fmt.Println("\nOK")
}
