/*
LAB 03 (advanced) - A resilient SOAP client: timeouts, fault classification, safe retries, redacted logs
=========================================================================================================
Enterprise SOAP backends are slow, flaky, and sit behind proxies that answer with HTML error pages.
A client that just calls http.Post and unmarshals will hang, crash on HTML, or retry the wrong things.

You will learn

  - THREE timeouts and where they live:
    http.Client.Timeout / Transport timeouts   (dial, TLS, response headers)   per attempt
    context deadline                            the WHOLE operation including retries

  - classify every outcome into one of four buckets - and only ONE of them is worth retrying blindly:

    network error / timeout           -> retry (idempotent operations only)
    HTTP 5xx with an HTML body        -> retry (a proxy/gateway hiccup, not a SOAP answer)
    SOAP fault "Server"/"Receiver"    -> retry ONLY if the operation is idempotent
    SOAP fault "Client"/"Sender"      -> NEVER retry: the same message fails the same way

  - IDEMPOTENCY decides retries: GetBalance may be retried freely; Transfer must NOT be retried
    after an ambiguous failure (it may already have happened!) unless the service supports a request id

  - detecting a non-XML response by Content-Type before parsing

  - logging raw XML for debugging WITHOUT leaking secrets (regexp redaction of passwords/tokens)

  - exponential backoff with jitter, and honouring ctx cancellation between attempts

Run it   go run ./SOAP/labs/golang/03_client_timeouts_faults_retries
*/
package main

import (
	"bytes"
	"context"
	"encoding/xml"
	"errors"
	"fmt"
	"io"
	"math/rand/v2"
	"net"
	"net/http"
	"net/http/httptest"
	"regexp"
	"strings"
	"sync/atomic"
	"time"
)

const (
	nsSOAP = "http://schemas.xmlsoap.org/soap/envelope/"
	nsBank = "http://bank.example.com/ws"
)

// ------------------------------------------------------------------- errors ---
type Fault struct {
	Code   string `xml:"faultcode"`
	String string `xml:"faultstring"`
}

func (f *Fault) Error() string { return "SOAP fault " + f.Code + ": " + f.String }
func (f *Fault) IsClientFault() bool {
	c := strings.ToLower(f.Code)
	return strings.HasSuffix(c, "client") || strings.HasSuffix(c, "sender")
}

type TransportError struct {
	Err       error
	Retryable bool
}

func (e *TransportError) Error() string { return e.Err.Error() }
func (e *TransportError) Unwrap() error { return e.Err }

// ------------------------------------------------------------------- client ---
type Client struct {
	URL         string
	HTTP        *http.Client
	MaxAttempts int
	BaseBackoff time.Duration
	Log         func(format string, a ...any)
}

var secretRe = regexp.MustCompile(`(?i)(<(?:\w+:)?(?:Password|Token|Nonce)[^>]*>)[^<]*(</)`)

func redact(b []byte) string { return secretRe.ReplaceAllString(string(b), "${1}***${2}") }

type response struct {
	Body struct {
		Fault   *Fault `xml:"http://schemas.xmlsoap.org/soap/envelope/ Fault"`
		Content []byte `xml:",innerxml"`
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

// Call sends one operation. `idempotent` decides whether ambiguous failures may be retried.
func (c *Client) Call(ctx context.Context, action, requestInner string, idempotent bool) ([]byte, error) {
	envelope := fmt.Sprintf(`<soap:Envelope xmlns:soap=%q><soap:Body>%s</soap:Body></soap:Envelope>`, nsSOAP, requestInner)
	var lastErr error
	for attempt := 1; attempt <= c.MaxAttempts; attempt++ {
		out, err := c.once(ctx, action, envelope, attempt)
		if err == nil {
			return out, nil
		}
		lastErr = err
		if !c.shouldRetry(err, idempotent) || attempt == c.MaxAttempts {
			break
		}
		wait := time.Duration(rand.Int64N(int64(c.BaseBackoff<<(attempt-1))) + 1) // full jitter
		c.Log("    attempt %d failed (%v); retrying in %s", attempt, short(err), wait.Round(time.Millisecond))
		select {
		case <-time.After(wait):
		case <-ctx.Done(): // the caller's overall deadline wins over any retry plan
			return nil, fmt.Errorf("gave up during backoff: %w", ctx.Err())
		}
	}
	return nil, lastErr
}

func (c *Client) shouldRetry(err error, idempotent bool) bool {
	var f *Fault
	if errors.As(err, &f) {
		return idempotent && !f.IsClientFault() // a Client fault would fail identically every time
	}
	var te *TransportError
	if errors.As(err, &te) {
		return idempotent && te.Retryable
	}
	return false
}

func (c *Client) once(ctx context.Context, action, envelope string, attempt int) ([]byte, error) {
	req, _ := http.NewRequestWithContext(ctx, "POST", c.URL, strings.NewReader(envelope))
	req.Header.Set("Content-Type", "text/xml; charset=utf-8")
	req.Header.Set("SOAPAction", `"`+action+`"`)
	c.Log("    -> attempt %d: %s", attempt, redact([]byte(envelope)))
	res, err := c.HTTP.Do(req)
	if err != nil { // dial refused, timeout, reset ...
		return nil, &TransportError{Err: err, Retryable: true}
	}
	defer res.Body.Close()
	raw, err := io.ReadAll(io.LimitReader(res.Body, 1<<20))
	if err != nil {
		return nil, &TransportError{Err: err, Retryable: true}
	}
	c.Log("    <- HTTP %d %s: %.90s", res.StatusCode, res.Header.Get("Content-Type"), strings.ReplaceAll(string(raw), "\n", " "))

	// A proxy/gateway error page is NOT a SOAP message. Check before parsing.
	ct := res.Header.Get("Content-Type")
	if !strings.Contains(ct, "xml") {
		return nil, &TransportError{Err: fmt.Errorf("HTTP %d with non-XML body (%s): a proxy or gateway answered, not the service", res.StatusCode, ct),
			Retryable: res.StatusCode >= 500}
	}
	var env response
	if err := xml.NewDecoder(bytes.NewReader(raw)).Decode(&env); err != nil {
		return nil, &TransportError{Err: fmt.Errorf("unparseable SOAP response: %w", err), Retryable: false}
	}
	if env.Body.Fault != nil {
		return nil, env.Body.Fault
	}
	return env.Body.Content, nil
}

func short(err error) string {
	s := err.Error()
	if len(s) > 60 {
		return s[:60] + "..."
	}
	return s
}

// ------------------------------------------------------- a menagerie of backends ---
func soapReply(w http.ResponseWriter, status int, inner string) {
	w.Header().Set("Content-Type", "text/xml; charset=utf-8")
	w.WriteHeader(status)
	fmt.Fprintf(w, `<soap:Envelope xmlns:soap=%q><soap:Body>%s</soap:Body></soap:Envelope>`, nsSOAP, inner)
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	var flakyHits, serverFaultHits, clientFaultHits, slowHits, htmlHits atomic.Int64
	mux := http.NewServeMux()
	ok := fmt.Sprintf(`<GetBalanceResponse xmlns=%q><balance>1042.50</balance></GetBalanceResponse>`, nsBank)
	mux.HandleFunc("/flaky", func(w http.ResponseWriter, r *http.Request) { // proxy HTML error twice, then fine
		if flakyHits.Add(1) <= 2 {
			w.Header().Set("Content-Type", "text/html")
			w.WriteHeader(502)
			fmt.Fprint(w, "<html><body><h1>502 Bad Gateway</h1></body></html>")
			return
		}
		soapReply(w, 200, ok)
	})
	mux.HandleFunc("/serverfault", func(w http.ResponseWriter, r *http.Request) { // transient application fault, then fine
		if serverFaultHits.Add(1) <= 1 {
			soapReply(w, 500, `<soap:Fault><faultcode>soap:Server</faultcode><faultstring>database busy</faultstring></soap:Fault>`)
			return
		}
		soapReply(w, 200, ok)
	})
	mux.HandleFunc("/clientfault", func(w http.ResponseWriter, r *http.Request) {
		clientFaultHits.Add(1)
		soapReply(w, 500, `<soap:Fault><faultcode>soap:Client</faultcode><faultstring>No such account</faultstring></soap:Fault>`)
	})
	mux.HandleFunc("/slow", func(w http.ResponseWriter, r *http.Request) {
		slowHits.Add(1)
		select {
		case <-time.After(2 * time.Second):
		case <-r.Context().Done():
		}
	})
	mux.HandleFunc("/html", func(w http.ResponseWriter, r *http.Request) {
		htmlHits.Add(1)
		w.Header().Set("Content-Type", "text/html")
		w.WriteHeader(200)
		fmt.Fprint(w, "<html>Maintenance window</html>")
	})
	srv := httptest.NewServer(mux)
	defer srv.Close()

	verbose := false
	log := func(f string, a ...any) {
		if verbose {
			fmt.Printf(f+"\n", a...)
		}
	}
	newClient := func(path string) *Client {
		return &Client{URL: srv.URL + path, MaxAttempts: 4, BaseBackoff: 20 * time.Millisecond, Log: log,
			HTTP: &http.Client{Transport: &http.Transport{
				DialContext:           (&net.Dialer{Timeout: 500 * time.Millisecond}).DialContext,
				ResponseHeaderTimeout: 300 * time.Millisecond, // per-attempt: how long to wait for the SERVICE to answer
			}}}
	}
	getBalance := fmt.Sprintf(`<GetBalance xmlns=%q><accountId>ACC-1001</accountId></GetBalance>`, nsBank)
	newCtx := func() (context.Context, context.CancelFunc) {
		return context.WithTimeout(context.Background(), 3*time.Second)
	}

	fmt.Println("== 1. proxy HTML errors: retried, then success (idempotent read) ==")
	verbose = true
	ctx, cancel := newCtx()
	out, err := newClient("/flaky").Call(ctx, nsBank+"/GetBalance", getBalance, true)
	cancel()
	verbose = false
	fmt.Printf("  result: err=%v, backend hits=%d, payload has balance: %v\n", err, flakyHits.Load(), strings.Contains(string(out), "1042.50"))
	must(err == nil && flakyHits.Load() == 3, "retried twice then succeeded")

	fmt.Println("\n== 2. soap:Server fault: retried for an idempotent op, NOT for a non-idempotent one ==")
	ctx, cancel = newCtx()
	_, err = newClient("/serverfault").Call(ctx, nsBank+"/GetBalance", getBalance, true)
	cancel()
	fmt.Printf("  idempotent GetBalance : err=%v, hits=%d\n", err, serverFaultHits.Load())
	must(err == nil && serverFaultHits.Load() == 2, "retry helped")
	serverFaultHits.Store(0)
	ctx, cancel = newCtx()
	_, err = newClient("/serverfault").Call(ctx, nsBank+"/Transfer", `<Transfer xmlns="`+nsBank+`"/>`, false)
	cancel()
	fmt.Printf("  NON-idempotent Transfer: err=%v, hits=%d  (one attempt only: it may have happened already)\n", short(err), serverFaultHits.Load())
	must(err != nil && serverFaultHits.Load() == 1, "no blind retry of a non-idempotent op")

	fmt.Println("\n== 3. soap:Client fault: never retried, even for idempotent operations ==")
	ctx, cancel = newCtx()
	_, err = newClient("/clientfault").Call(ctx, nsBank+"/GetBalance", getBalance, true)
	cancel()
	var f *Fault
	fmt.Printf("  err is *Fault: %v (%s), hits=%d\n", errors.As(err, &f), f.String, clientFaultHits.Load())
	must(errors.As(err, &f) && clientFaultHits.Load() == 1, "client fault not retried")

	fmt.Println("\n== 4. a hung backend: per-attempt timeout, then the overall deadline ==")
	start := time.Now()
	ctx, cancel = context.WithTimeout(context.Background(), 700*time.Millisecond)
	_, err = newClient("/slow").Call(ctx, nsBank+"/GetBalance", getBalance, true)
	cancel()
	fmt.Printf("  gave up after %s with: %s (hits=%d)\n", time.Since(start).Round(10*time.Millisecond), short(err), slowHits.Load())
	must(err != nil && time.Since(start) < 1200*time.Millisecond && slowHits.Load() >= 2, "bounded total time")

	fmt.Println("\n== 5. 200 OK with an HTML maintenance page is not a SOAP answer ==")
	ctx, cancel = newCtx()
	_, err = newClient("/html").Call(ctx, nsBank+"/Transfer", `<Transfer xmlns="`+nsBank+`"/>`, false)
	cancel()
	fmt.Println("  ", short(err))
	must(err != nil, "non-XML rejected before parsing")

	fmt.Println("\n== 6. log redaction ==")
	secretReq := `<soap:Header><wsse:Security><wsse:UsernameToken><wsse:Username>alice</wsse:Username><wsse:Password Type="x">hunter2</wsse:Password><wsse:Nonce>abc123==</wsse:Nonce></wsse:UsernameToken></wsse:Security></soap:Header>`
	fmt.Println("  ", redact([]byte(secretReq)))
	must(!strings.Contains(redact([]byte(secretReq)), "hunter2") && !strings.Contains(redact([]byte(secretReq)), "abc123"), "secrets redacted")
	fmt.Println("\nOK")
}
