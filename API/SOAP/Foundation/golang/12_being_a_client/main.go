/*
FOUNDATION LEVEL 12 - Being the client: calling a SOAP service properly
===========================================================================
Levels 00-11 were all SERVER code. In real work you far more often CONSUME a
SOAP service than write one - SOAP is the protocol of other people's legacy
systems. So this level flips the lens: a small server plays "the vendor's
service" (a cut-down level 11, plus a deliberately flaky operation), and the
interesting code is the client calling it.

A CHOICE, EXPLAINED: this file keeps hand-building the envelope with
encoding/xml instead of reaching for a WSDL-generated client. The retry/fault
logic below is the actual lesson, and every other file in Foundation is
stdlib-only so nothing here needs installing. A generated client's real value
is producing all of this from a WSDL automatically - that is
../../labs/golang/05_wsdl_driven_json_gateway. Use one at work; read this to
know what it is doing for you.

THE RULE THAT MATTERS: never retry blindly. Level 05 built the distinction,
and this is what it was for:

	soap:Client  -> your message is wrong. Retrying it unchanged will fail
	                identically, forever. Fix the message or give up.
	soap:Server  -> the service failed. A retry may well succeed.
	no envelope  -> you never reached the SOAP code at all (timeout, refused
	                connection, 404, 415). Retry only if it was transient.

You will learn
  - a reusable "call one operation" client function, and why it returns the
    Fault as an error instead of leaving a raw HTTP status to interpret
  - turning a <soap:Fault> into a real Go error carrying its detail name
  - retry with EXPONENTIAL BACKOFF on soap:Server, and never on soap:Client
  - treating a timeout and a fault as two different failure kinds
  - why a retried CreateOrder can create two orders, and what to do about it

Run it   go run ./SOAP/Foundation/golang/12_being_a_client
*/
package main

import (
	"encoding/xml"
	"errors"
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
	nsTNS  = "http://foundation.example.com/orders"
)

var attempts = map[string]int{"GetStatus": 0, "Flaky": 0}

// ============================= "the vendor's service" ========================
// Deliberately thin - it exists only to give the client something to talk to.
type incomingEnvelope struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Body    struct {
		Operation struct {
			XMLName xml.Name
		} `xml:",any"`
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

type soapFault struct {
	XMLName xml.Name     `xml:"http://schemas.xmlsoap.org/soap/envelope/ Fault"`
	Code    string       `xml:"faultcode"`
	String  string       `xml:"faultstring"`
	Detail  *faultDetail `xml:"detail,omitempty"`
}

type faultDetail struct {
	Named struct {
		XMLName xml.Name
	} `xml:",any"`
}

type outEnvelope struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Body    struct {
		Status *struct {
			XMLName xml.Name `xml:"http://foundation.example.com/orders GetStatusResponse"`
			Status  string   `xml:"http://foundation.example.com/orders status"`
		}
		Flaky *struct {
			XMLName xml.Name `xml:"http://foundation.example.com/orders FlakyResponse"`
			Result  string   `xml:"http://foundation.example.com/orders result"`
		}
		Slow *struct {
			XMLName xml.Name `xml:"http://foundation.example.com/orders SlowResponse"`
		}
		Fault *soapFault
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

func buildFault(w http.ResponseWriter, status int, code, message, detailName string) {
	var env outEnvelope
	f := &soapFault{Code: code, String: message}
	if detailName != "" {
		f.Detail = &faultDetail{}
		f.Detail.Named.XMLName = xml.Name{Space: nsTNS, Local: detailName}
	}
	env.Body.Fault = f
	out, err := xml.Marshal(env)
	if err != nil {
		log.Fatal(err)
	}
	w.Header().Set("Content-Type", "text/xml; charset=utf-8")
	w.WriteHeader(status)
	w.Write(append([]byte(xml.Header), out...))
}

func writeEnvelope(w http.ResponseWriter, env outEnvelope) {
	out, err := xml.Marshal(env)
	if err != nil {
		log.Fatal(err)
	}
	w.Header().Set("Content-Type", "text/xml; charset=utf-8")
	w.WriteHeader(http.StatusOK)
	w.Write(append([]byte(xml.Header), out...))
}

func vendorHandler(w http.ResponseWriter, r *http.Request) {
	raw, _ := io.ReadAll(r.Body)
	var parsed incomingEnvelope
	xml.Unmarshal(raw, &parsed)
	local := parsed.Body.Operation.XMLName.Local

	switch local {
	case "GetStatus":
		attempts["GetStatus"]++
		var env outEnvelope
		env.Body.Status = &struct {
			XMLName xml.Name `xml:"http://foundation.example.com/orders GetStatusResponse"`
			Status  string   `xml:"http://foundation.example.com/orders status"`
		}{Status: "UP"}
		writeEnvelope(w, env)

	case "Flaky":
		// Fails twice with a SERVER fault, then works - a service restarting
		// or briefly overloaded, not actually broken.
		attempts["Flaky"]++
		if attempts["Flaky"] <= 2 {
			buildFault(w, http.StatusInternalServerError, "soap:Server", "database connection pool exhausted", "")
			return
		}
		var env outEnvelope
		env.Body.Flaky = &struct {
			XMLName xml.Name `xml:"http://foundation.example.com/orders FlakyResponse"`
			Result  string   `xml:"http://foundation.example.com/orders result"`
		}{Result: "finally"}
		writeEnvelope(w, env)

	case "CreateOrder":
		buildFault(w, http.StatusInternalServerError, "soap:Client", "quantity must be at least 1", "InvalidValue")

	case "Slow":
		time.Sleep(1500 * time.Millisecond) // longer than the client's timeout
		var env outEnvelope
		env.Body.Slow = &struct {
			XMLName xml.Name `xml:"http://foundation.example.com/orders SlowResponse"`
		}{}
		writeEnvelope(w, env)

	default:
		buildFault(w, http.StatusInternalServerError, "soap:Client", "unknown operation "+local, "")
	}
}

// ================================= THE CLIENT =================================
// soapFaultErr is a <soap:Fault> as a Go error, carrying the parts a caller
// needs to make a decision: the code (retry or not) and the detail (which error).
type soapFaultErr struct {
	code, message, detailName string
}

func (e *soapFaultErr) Error() string { return e.code + ": " + e.message }

// retryable: THE decision, in one place. soap:Server (or SOAP 1.2's env:Receiver)
// means the service failed; anything else means our own message is wrong.
func (e *soapFaultErr) retryable() bool {
	i := strings.LastIndex(e.code, ":")
	suffix := e.code[i+1:]
	return suffix == "Server" || suffix == "Receiver"
}

// callOnce POSTs one operation and returns the parsed response, or a
// *soapFaultErr. Note a fault arrives as an HTTP 500 WITH a body (level 06),
// so the error branch must still read and parse it - a bare status-code check
// would throw the entire error message away.
func callOnce(client *http.Client, url, operation string) (*outEnvelope, error) {
	body := fmt.Sprintf(
		`<soap:Envelope xmlns:soap="%s"><soap:Header/><soap:Body>`+
			`<t:%s xmlns:t="%s"/></soap:Body></soap:Envelope>`, nsSOAP, operation, nsTNS)

	req, err := http.NewRequest(http.MethodPost, url, strings.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "text/xml; charset=utf-8")
	// Many servers dispatch on SOAPAction instead of the body element, and
	// some reject the request outright if it is missing.
	req.Header.Set("SOAPAction", fmt.Sprintf("%q", nsTNS+"/"+operation))

	res, err := client.Do(req)
	if err != nil {
		return nil, err // no envelope came back at all: nothing to parse
	}
	defer res.Body.Close()
	raw, _ := io.ReadAll(res.Body)

	var env outEnvelope
	if err := xml.Unmarshal(raw, &env); err != nil {
		return nil, err
	}
	if env.Body.Fault != nil {
		detailName := ""
		if env.Body.Fault.Detail != nil {
			detailName = env.Body.Fault.Detail.Named.XMLName.Local
		}
		return nil, &soapFaultErr{code: env.Body.Fault.Code, message: env.Body.Fault.String, detailName: detailName}
	}
	return &env, nil
}

// callWithRetries retries only what is worth retrying, waiting longer each time.
func callWithRetries(client *http.Client, url, operation string, maxAttempts int) (*outEnvelope, error) {
	var lastErr error
	for attempt := 1; attempt <= maxAttempts; attempt++ {
		env, err := callOnce(client, url, operation)
		if err == nil {
			return env, nil
		}
		lastErr = err

		var sfe *soapFaultErr
		if errors.As(err, &sfe) {
			if !sfe.retryable() || attempt == maxAttempts {
				return nil, err // soap:Client: give up immediately
			}
			wait := time.Duration(50*(1<<(attempt-1))) * time.Millisecond
			fmt.Printf("  attempt %d: %s - retrying in %s\n", attempt, sfe.code, wait)
			time.Sleep(wait)
			continue
		}

		// No envelope came back at all: a timeout or a refused connection.
		// Same backoff idea, but we know NOTHING about whether the server
		// already did the work - see the closing note about idempotency.
		if attempt == maxAttempts {
			return nil, err
		}
		wait := time.Duration(50*(1<<(attempt-1))) * time.Millisecond
		fmt.Printf("  attempt %d: no response (%T) - backing off\n", attempt, err)
		time.Sleep(wait)
	}
	return nil, lastErr
}

func demo(url string) {
	fmt.Println("== 1. the happy path ==")
	env, err := callWithRetries(&http.Client{Timeout: time.Second}, url, "GetStatus", 5)
	if err != nil {
		panic("FAILED: " + err.Error())
	}
	fmt.Printf("  GetStatus -> status=%s\n", env.Body.Status.Status)
	if env.Body.Status.Status != "UP" || attempts["GetStatus"] != 1 {
		panic("FAILED: a successful call must not be retried")
	}

	fmt.Println("\n== 2. a soap:Server fault IS worth retrying ==")
	env, err = callWithRetries(&http.Client{Timeout: time.Second}, url, "Flaky", 5)
	if err != nil {
		panic("FAILED: " + err.Error())
	}
	fmt.Printf("  Flaky -> %q after %d attempts\n", env.Body.Flaky.Result, attempts["Flaky"])
	if env.Body.Flaky.Result != "finally" || attempts["Flaky"] != 3 {
		panic("FAILED: expected 2 failures then 1 success")
	}

	fmt.Println("\n== 3. a soap:Client fault is NOT - fail fast, do not hammer ==")
	before := time.Now()
	_, err = callWithRetries(&http.Client{Timeout: time.Second}, url, "CreateOrder", 5)
	elapsed := time.Since(before)
	var sfe *soapFaultErr
	if !errors.As(err, &sfe) {
		panic("FAILED: expected a soap fault")
	}
	fmt.Printf("  CreateOrder -> %s <%s> %q\n", sfe.code, sfe.detailName, sfe.message)
	fmt.Printf("  gave up after %s with NO retries "+
		"(the same message would fail the same way forever)\n", elapsed)
	if sfe.detailName != "InvalidValue" || sfe.retryable() || elapsed > 200*time.Millisecond {
		panic("FAILED")
	}

	fmt.Println("\n== 4. no answer at all is a different failure kind ==")
	_, err = callOnce(&http.Client{Timeout: 200 * time.Millisecond}, url, "Slow")
	if err == nil {
		panic("FAILED: expected a timeout")
	}
	if errors.As(err, &sfe) {
		panic("FAILED: a timeout must not be a soap fault")
	}
	fmt.Printf("  Slow (timeout 200ms) -> %T   (no envelope: nothing to parse)\n", err)

	fmt.Println("\n== 5. the warning that goes with every retry loop ==")
	fmt.Println("  a retried CreateOrder can create the order TWICE: the first attempt")
	fmt.Println("  may have succeeded and only the RESPONSE been lost. Fix it by sending")
	fmt.Println("  a client-generated id (wsa:MessageID, level 07) the server remembers,")
	fmt.Println("  so the second attempt returns the FIRST attempt's answer instead of")
	fmt.Println("  doing the work again - see ../../labs/golang/03_client_timeouts_faults_retries.")

	fmt.Println("\nOK")
}

func main() {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	mux := http.NewServeMux()
	mux.HandleFunc("/orders", vendorHandler)
	go http.Serve(listener, mux)

	demo("http://" + listener.Addr().String() + "/orders")
}
