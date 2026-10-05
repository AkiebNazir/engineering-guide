/*
FOUNDATION LEVEL 09 - Authentication: proving who you are, inside the envelope
==================================================================================
Middleware (level 08) is the mechanism; authentication is the first thing
everyone puts in it. Authentication answers exactly ONE question: "do we
recognize this caller at all?" It says NOTHING about what they may do - that is
level 10, authorization, and keeping the two apart is the whole point.

WHERE THE CREDENTIAL GOES. A REST API sends `Authorization: Bearer xyz`, an HTTP
header. SOAP can do that too, but the SOAP-native answer is a security element
in <soap:Header>, because (level 07) the envelope survives hops and can be
signed. The real standard is WS-Security's UsernameToken:

	<soap:Header>
	  <wsse:Security>
	    <wsse:UsernameToken>
	      <wsse:Username>alice</wsse:Username>
	      <wsse:Password Type="...#PasswordText">s3cret</wsse:Password>
	    </wsse:UsernameToken>
	  </wsse:Security>
	</soap:Header>

This level uses the same SHAPE with a simple opaque token, so the lesson is the
check and not the ceremony. ../../labs/golang/04_ws_security_username_token does
the real WS-Security version with digests, nonces and timestamps.

There is no "401" here: a SOAP service answers with a Fault (level 05). The
401-equivalent is faultcode soap:Client plus a <detail> element that names the
problem, so the caller can tell "I am not logged in" from "you typo'd a field".

You will learn
  - reading a credential out of <soap:Header> before the Body is parsed at all
  - authentication as middleware: it can short-circuit the chain entirely
  - the Fault that means "who even are you" - the 401 of the SOAP world
  - carrying the identified caller alongside the request so operations (and
    level 10's role check) never re-verify the token
  - why the credential belongs in the envelope, not only in an HTTP header

Run it   go run ./SOAP/Foundation/golang/09_authentication_token_in_header
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
	// The real WS-Security namespace, so the header element you see here is
	// the one you will meet in the wild.
	nsWSSE = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
	nsTNS  = "http://foundation.example.com/soap"
)

type identity struct {
	User string
	Role string
}

// A stand-in for "who is allowed in". A real service verifies a signed SAML
// assertion or looks the token up in a store instead of this map.
var tokens = map[string]identity{
	"alice-token": {User: "alice", Role: "admin"},
	"bob-token":   {User: "bob", Role: "viewer"},
}

// request is what travels down the chain. Caller starts nil and is filled in BY
// the authentication middleware - never by the caller themselves.
type request struct {
	envelope requestEnvelope
	caller   *identity
}

type dispatcher func(*request) (int, []byte)

type requestEnvelope struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Header  struct {
		// The nesting mirrors the XML exactly: Security > UsernameToken > Password.
		Password string `xml:"http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd Security>UsernameToken>Password"`
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Header"`
	Body struct {
		Operation struct {
			XMLName xml.Name
		} `xml:",any"`
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

type whoAmIResponse struct {
	XMLName xml.Name `xml:"http://foundation.example.com/soap WhoAmIResponse"`
	User    string   `xml:"http://foundation.example.com/soap user"`
	Role    string   `xml:"http://foundation.example.com/soap role"`
}

type soapFault struct {
	XMLName xml.Name     `xml:"http://schemas.xmlsoap.org/soap/envelope/ Fault"`
	Code    string       `xml:"faultcode"`
	String  string       `xml:"faultstring"`
	Detail  *faultDetail `xml:"detail,omitempty"`
}

// The detail's child element NAME is the machine-readable error kind, so it is
// set at runtime. `,any` on decoding means "match whatever child is in there".
type faultDetail struct {
	Named struct {
		XMLName xml.Name
	} `xml:",any"`
}

type responseEnvelope struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Body    struct {
		WhoAmI *whoAmIResponse
		Fault  *soapFault
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

func marshalEnvelope(env responseEnvelope) []byte {
	out, err := xml.Marshal(env)
	if err != nil {
		log.Fatal(err)
	}
	return append([]byte(xml.Header), out...)
}

func faultResponse(code, message, detailName string) (int, []byte) {
	f := &soapFault{Code: code, String: message}
	if detailName != "" {
		f.Detail = &faultDetail{}
		f.Detail.Named.XMLName = xml.Name{Space: nsTNS, Local: detailName}
	}
	var env responseEnvelope
	env.Body.Fault = f
	return http.StatusInternalServerError, marshalEnvelope(env)
}

func withAuthentication(next dispatcher) dispatcher {
	return func(r *request) (int, []byte) {
		token := r.envelope.Header.Password

		if token == "" {
			// The 401 of SOAP. HTTP status stays 500 (level 06) - the FAULT
			// carries the meaning, and <detail> names it for machines.
			return faultResponse("soap:Client", "no credentials in the SOAP header", "Unauthenticated")
		}

		caller, known := tokens[token]
		if !known {
			// Same fault, deliberately the same vague faultstring: telling an
			// attacker which half of the credential was wrong is a gift.
			return faultResponse("soap:Client", "unknown or expired token", "Unauthenticated")
		}

		r.caller = &caller // everything downstream now knows who this is
		fmt.Printf("  [auth] recognized %s (role=%s)\n", caller.User, caller.Role)
		return next(r)
	}
}

func dispatch(r *request) (int, []byte) {
	switch r.envelope.Body.Operation.XMLName.Local {
	case "WhoAmI":
		// No token checking here at all - by the time an operation runs, the
		// caller is a known fact. That separation is what middleware buys you.
		var env responseEnvelope
		env.Body.WhoAmI = &whoAmIResponse{User: r.caller.User, Role: r.caller.Role}
		return http.StatusOK, marshalEnvelope(env)
	default:
		return faultResponse("soap:Client", "unknown operation", "")
	}
}

var pipeline = withAuthentication(dispatch)

func handler(w http.ResponseWriter, r *http.Request) {
	raw, _ := io.ReadAll(r.Body)

	var parsed requestEnvelope
	var status int
	var out []byte
	if err := xml.Unmarshal(raw, &parsed); err != nil {
		status, out = faultResponse("soap:Client", "malformed XML", "")
	} else {
		status, out = pipeline(&request{envelope: parsed})
	}

	w.Header().Set("Content-Type", "text/xml; charset=utf-8")
	w.WriteHeader(status)
	w.Write(out)
}

// securityHeader is the client side: a WS-Security-shaped header carrying one
// token.
func securityHeader(token string) string {
	if token == "" {
		return ""
	}
	return fmt.Sprintf(
		`<wsse:Security xmlns:wsse="%s"><wsse:UsernameToken>`+
			`<wsse:Username>the-token-holder</wsse:Username>`+
			`<wsse:Password>%s</wsse:Password>`+
			`</wsse:UsernameToken></wsse:Security>`, nsWSSE, token)
}

func call(url, operation, token string) (int, responseEnvelope, []byte) {
	body := fmt.Sprintf(
		`<soap:Envelope xmlns:soap="%s"><soap:Header>%s</soap:Header>`+
			`<soap:Body><t:%s xmlns:t="%s"/></soap:Body></soap:Envelope>`,
		nsSOAP, securityHeader(token), operation, nsTNS)
	res, err := http.Post(url, "text/xml; charset=utf-8", bytes.NewReader([]byte(body)))
	if err != nil {
		log.Fatal(err)
	}
	defer res.Body.Close()
	raw, _ := io.ReadAll(res.Body)
	var parsed responseEnvelope
	if err := xml.Unmarshal(raw, &parsed); err != nil {
		log.Fatal(err)
	}
	return res.StatusCode, parsed, []byte(body)
}

func detailOf(env responseEnvelope) string {
	if env.Body.Fault == nil || env.Body.Fault.Detail == nil {
		return ""
	}
	return env.Body.Fault.Detail.Named.XMLName.Local
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

	fmt.Println("== 1. no credentials at all ==")
	status, parsed, _ := call(url, "WhoAmI", "")
	fmt.Printf("  WhoAmI (no header)     -> %d %s <%s>\n",
		status, parsed.Body.Fault.Code, detailOf(parsed))
	if status != http.StatusInternalServerError || detailOf(parsed) != "Unauthenticated" {
		panic("FAILED")
	}

	fmt.Println("\n== 2. a token nobody has ever issued ==")
	status, parsed, _ = call(url, "WhoAmI", "hunter2")
	fmt.Printf("  WhoAmI (bad token)     -> %d %q <%s>\n",
		status, parsed.Body.Fault.String, detailOf(parsed))
	if status != http.StatusInternalServerError || detailOf(parsed) != "Unauthenticated" {
		panic("FAILED")
	}

	fmt.Println("\n== 3. a real token ==")
	status, parsed, sent := call(url, "WhoAmI", "alice-token")
	fmt.Printf("  WhoAmI (alice-token)   -> %d user=%s role=%s\n",
		status, parsed.Body.WhoAmI.User, parsed.Body.WhoAmI.Role)
	if status != http.StatusOK || parsed.Body.WhoAmI.User != "alice" || parsed.Body.WhoAmI.Role != "admin" {
		panic("FAILED")
	}

	status, parsed, _ = call(url, "WhoAmI", "bob-token")
	fmt.Printf("  WhoAmI (bob-token)     -> %d user=%s role=%s\n",
		status, parsed.Body.WhoAmI.User, parsed.Body.WhoAmI.Role)
	if status != http.StatusOK || parsed.Body.WhoAmI.User != "bob" || parsed.Body.WhoAmI.Role != "viewer" {
		panic("FAILED")
	}
	fmt.Println("  -> bob got in. Whether bob may DO anything is level 10's question.")

	fmt.Println("\n== 4. what the authenticated request actually looked like ==")
	fmt.Println("  " + string(bytes.ReplaceAll(sent, []byte("><"), []byte(">\n  <"))))

	fmt.Println("OK")
}
