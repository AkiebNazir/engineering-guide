/*
FOUNDATION LEVEL 08 - Middleware: code that wraps every operation
=====================================================================
Levels 00-07 put everything an operation needed inside the dispatcher itself.
Middleware is a WRAPPER: a function that takes a dispatcher and returns a new
dispatcher which runs code before and/or after calling the original - without
touching the original's code at all.

In SOAP this pattern is even more valuable than in REST, because a SOAP
dispatcher is the ONE choke point for every operation in the service (one URL,
remember). Logging, authentication (level 09), authorization (level 10), schema
validation and tracing all get bolted on here, once, for fifty operations at a
time. Real stacks call these "handler chains" (Java JAX-WS) or "interceptors".

The SOAP-specific twist: a panic inside an operation must come back out as a
<soap:Fault> with faultcode soap:Server. net/http's default behaviour on a panic
is to kill the connection with no response at all, which breaks every SOAP
client in existence - they parse XML, and only XML.

You will learn
  - a middleware has the SAME shape as a dispatcher: bytes in, (status, bytes) out
  - chaining: wrapping a wrapper in a wrapper, in a chosen order
  - ORDER matters: logging OUTSIDE recovery still logs a panicking call;
    logging INSIDE it would never run
  - recover() in a deferred func, and converting the panic into clean XML -
    the difference between "our service is broken" and "our service is down"
  - that one panicking operation must not take down the whole server

Run it   go run ./SOAP/Foundation/golang/08_middleware_logging_and_recovery
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
	"time"
)

const (
	nsSOAP = "http://schemas.xmlsoap.org/soap/envelope/"
	nsTNS  = "http://foundation.example.com/soap"
)

// A dispatcher: raw request bytes -> (http status, raw response bytes).
type dispatcher func(raw []byte) (int, []byte)

// middleware takes one dispatcher and returns a new one wrapping it.
type middleware func(dispatcher) dispatcher

// logLines lets the demo assert on what the logger actually saw.
var logLines []string

type pingResponse struct {
	XMLName xml.Name `xml:"http://foundation.example.com/soap PingResponse"`
	Message string   `xml:"http://foundation.example.com/soap message"`
}

type soapFault struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Fault"`
	Code    string   `xml:"faultcode"`
	String  string   `xml:"faultstring"`
}

type envelope struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Body    struct {
		Ping  *pingResponse
		Fault *soapFault
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

func marshalEnvelope(response *pingResponse, f *soapFault) []byte {
	var env envelope
	env.Body.Ping, env.Body.Fault = response, f
	out, err := xml.Marshal(env)
	if err != nil {
		log.Fatal(err)
	}
	return append([]byte(xml.Header), out...)
}

// operationName peeks at the operation name WITHOUT running it - what logging
// needs. A SOAP access log that only records "POST /soap 200" is useless:
// every request looks identical. The operation name lives in the XML, so the
// logging middleware has to crack the envelope open itself.
func operationName(raw []byte) string {
	var probe struct {
		XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
		Body    struct {
			Operation struct {
				XMLName xml.Name
			} `xml:",any"`
		} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
	}
	if err := xml.Unmarshal(raw, &probe); err != nil {
		return "<unparseable>"
	}
	return probe.Body.Operation.XMLName.Local
}

// ---- the "real" service logic, with zero knowledge of logging or recovery ----
func dispatch(raw []byte) (int, []byte) {
	switch operationName(raw) {
	case "Ping":
		return http.StatusOK, marshalEnvelope(&pingResponse{Message: "Pong"}, nil)
	case "Boom":
		// A BUG, on purpose: an unhandled panic in the middle of an operation,
		// the way a real one would come from a nil map write or a bad index.
		panic("simulated bug: index out of range in pricing")
	default:
		return http.StatusInternalServerError,
			marshalEnvelope(nil, &soapFault{Code: "soap:Client", String: "unknown operation"})
	}
}

// ---- middleware #1: which operation, what outcome, how long ----
func withLogging(next dispatcher) dispatcher {
	return func(raw []byte) (int, []byte) {
		name := operationName(raw)
		started := time.Now()
		status, out := next(raw)
		elapsed := time.Since(started)

		// Log the FAULTCODE, not just the status: level 06 showed that HTTP 500
		// alone cannot tell "your fault" from "our fault".
		var parsed envelope
		code := ""
		if err := xml.Unmarshal(out, &parsed); err == nil && parsed.Body.Fault != nil {
			code = " " + parsed.Body.Fault.Code
		}
		line := fmt.Sprintf("%s -> HTTP %d%s (%.2fms)", name, status, code,
			float64(elapsed.Microseconds())/1000)
		logLines = append(logLines, line)
		fmt.Printf("  [log] %s\n", line)
		return status, out
	}
}

// ---- middleware #2: any panic becomes a well-formed soap:Server fault ----
func withRecovery(next dispatcher) dispatcher {
	return func(raw []byte) (status int, out []byte) {
		// A deferred closure with named return values: when recover() catches
		// something, we OVERWRITE what this function returns.
		defer func() {
			if recovered := recover(); recovered != nil {
				fmt.Printf("  [recovery] caught %v - one call becomes a Fault, the server stays up\n",
					recovered)
				// Deliberately generic text: never leak a stack trace or an
				// internal table name to a caller.
				status = http.StatusInternalServerError
				out = marshalEnvelope(nil, &soapFault{Code: "soap:Server", String: "internal error"})
			}
		}()
		return next(raw)
	}
}

// chain builds the pipeline outside in, so the FIRST middleware listed is the
// outermost one - the order you read is the order a request passes through.
func chain(base dispatcher, layers ...middleware) dispatcher {
	for i := len(layers) - 1; i >= 0; i-- {
		base = layers[i](base)
	}
	return base
}

// Logging is OUTSIDE recovery, so a panicking operation still produces a log
// line (recovery converts the panic into a real response before logging ever
// sees it). Swap the two and Boom vanishes from the log - the single most
// common mistake in a handler chain.
var pipeline = chain(dispatch, withLogging, withRecovery)

func handler(w http.ResponseWriter, r *http.Request) {
	raw, _ := io.ReadAll(r.Body)
	status, out := pipeline(raw)
	w.Header().Set("Content-Type", "text/xml; charset=utf-8")
	w.WriteHeader(status)
	w.Write(out)
}

func call(url, operation string) (int, envelope) {
	body := fmt.Sprintf(
		`<soap:Envelope xmlns:soap="%s"><soap:Body><t:%s xmlns:t="%s"/></soap:Body></soap:Envelope>`,
		nsSOAP, operation, nsTNS)
	res, err := http.Post(url, "text/xml; charset=utf-8", bytes.NewReader([]byte(body)))
	if err != nil {
		log.Fatal(err)
	}
	defer res.Body.Close()
	raw, _ := io.ReadAll(res.Body)
	var parsed envelope
	if err := xml.Unmarshal(raw, &parsed); err != nil {
		log.Fatal(err)
	}
	return res.StatusCode, parsed
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

	fmt.Println("== 1. a normal call passes through both wrappers ==")
	status, parsed := call(url, "Ping")
	fmt.Printf("  Ping -> %d %q\n", status, parsed.Body.Ping.Message)
	if status != http.StatusOK || parsed.Body.Ping.Message != "Pong" {
		panic("FAILED")
	}

	fmt.Println("\n== 2. an operation that panics ==")
	status, parsed = call(url, "Boom")
	fmt.Printf("  Boom -> %d %s %q   (a Fault a client can parse, not a dead socket)\n",
		status, parsed.Body.Fault.Code, parsed.Body.Fault.String)
	if status != http.StatusInternalServerError || parsed.Body.Fault.Code != "soap:Server" ||
		parsed.Body.Fault.String != "internal error" {
		panic("FAILED")
	}
	if strings.Contains(parsed.Body.Fault.String, "index out of range") {
		panic("FAILED: never leak internals")
	}

	fmt.Println("\n== 3. the server survived that panic ==")
	status, _ = call(url, "Ping")
	fmt.Printf("  Ping -> %d   (still alive, still serving everyone else)\n", status)
	if status != http.StatusOK {
		panic("FAILED")
	}

	fmt.Println("\n== 4. what the logging middleware recorded ==")
	for _, line := range logLines {
		fmt.Printf("  %s\n", line)
	}
	if len(logLines) != 3 ||
		!strings.HasPrefix(logLines[0], "Ping -> HTTP 200") ||
		// THE POINT: the panicking call IS in the log, because logging wraps recovery.
		!strings.HasPrefix(logLines[1], "Boom -> HTTP 500 soap:Server") {
		panic("FAILED")
	}
	fmt.Println("  -> the panic is in the log because logging wraps recovery, not the other way round")

	fmt.Println("\nOK")
}
