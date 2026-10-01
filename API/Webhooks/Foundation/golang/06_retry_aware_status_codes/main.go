/*
FOUNDATION LEVEL 06 - Retry-aware responses: your status code is an instruction
==================================================================================
Level 02 picked status codes from the receiver's chair. This level sits in the
SENDER's chair and shows what those numbers actually do, because the sender has
no other channel: it cannot read your error message, it will not open your
dashboard. It reads one integer and decides your fate.

	2xx        done. Delete the delivery, stop, never send this event again.
	408, 429   slow down, then retry (429 usually with a Retry-After header)
	5xx        please retry me later - you said the problem is yours and temporary
	other 4xx  do NOT retry. You told me this payload will never work; retrying
	           identical bytes cannot change your answer. Park it in a dead-letter
	           queue and alert a human instead.

The consequences of getting this wrong are real and asymmetric. Returning 500
for a permanently bad payload means the sender retries for days, and a retry
queue backs up behind an event that can never succeed. Returning 200 for
something you failed to handle means the event is GONE: the sender deletes it,
nobody retries, and you have silently lost data. When in doubt, 500 is the safer
mistake - a duplicate (level 03 handles it) is recoverable, a lost event is not.

You will learn
  - the sender-side decision function: status code in -> retry / stop / fail-fast out
  - why 2xx is a promise you must not make lightly
  - Retry-After, and a sender that honours it instead of its own backoff
  - that redirects (3xx) are not success: most senders do not follow them, and
    Go's http.Client follows them by default, so you must turn that off

Run it   go run ./Webhooks/Foundation/golang/06_retry_aware_status_codes
*/
package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
)

// ---------------------------------------------------------------------------
// THE SENDER'S SIDE: the whole retry policy, as one pure function.
// ---------------------------------------------------------------------------
const (
	stop       = "stop" // delivered, we are finished
	retry      = "retry"
	deadLetter = "dead" // permanently rejected: stop retrying, tell a human
)

// decide takes the status code, or 0 for "no answer at all".
func decide(status int) string {
	switch {
	case status == 0:
		return retry // timeout / connection refused: no answer is not a "no"
	case status >= 200 && status < 300:
		return stop
	case status == 408 || status == 429:
		return retry // explicitly "later", not "never"
	case status >= 500 && status < 600:
		return retry // the receiver called it temporary
	case status >= 300 && status < 400:
		return deadLetter // a redirect is a misconfigured endpoint, not a delivery
	default:
		return deadLetter // every other 4xx: identical bytes will fail identically
	}
}

// ---------------------------------------------------------------------------
// THE RECEIVER'S SIDE: one endpoint per answer, so we can see each decision.
// ---------------------------------------------------------------------------
type answer struct {
	status int
	body   map[string]any
}

var routes = map[string]answer{
	"/ok":             {200, map[string]any{"accepted": true}},
	"/queued":         {202, map[string]any{"queued": true}},
	"/malformed":      {400, map[string]any{"error": "data.amount is not a number - this will never parse"}},
	"/unknown-source": {401, map[string]any{"error": "bad signature"}},
	"/too-many":       {429, map[string]any{"error": "slow down"}},
	"/database-down":  {503, map[string]any{"error": "temporarily unavailable"}},
	"/moved":          {302, map[string]any{"error": "we changed our URL and forgot to tell you"}},
}

func receiver(w http.ResponseWriter, r *http.Request) {
	a, known := routes[r.URL.Path]
	if !known {
		a = answer{404, map[string]any{"error": "not found"}}
	}
	w.Header().Set("Content-Type", "application/json")
	if a.status == 429 {
		w.Header().Set("Retry-After", "2") // seconds; the sender should obey this
	}
	if a.status == 302 {
		w.Header().Set("Location", "/ok")
	}
	w.WriteHeader(a.status)
	json.NewEncoder(w).Encode(a.body)
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, http.HandlerFunc(receiver))
	base := "http://" + ln.Addr().String()

	// Most webhook senders do NOT follow redirects (a moved endpoint is a config
	// change you must acknowledge, and following one could leak the signature to
	// a third host). Go follows them by default, so we switch that off.
	client := &http.Client{
		CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse },
	}

	deliver := func(path string) (int, string) {
		req, _ := http.NewRequest("POST", base+path,
			bytes.NewBufferString(`{"type":"order.paid","id":"evt_1","data":{}}`))
		req.Header.Set("Content-Type", "application/json")
		res, err := client.Do(req)
		if err != nil {
			if errors.Is(err, io.EOF) {
				return 0, ""
			}
			log.Fatal(err)
		}
		defer res.Body.Close()
		io.ReadAll(res.Body)
		return res.StatusCode, res.Header.Get("Retry-After")
	}

	expected := []struct {
		path string
		want string
	}{
		{"/ok", stop},
		{"/queued", stop},
		{"/malformed", deadLetter},
		{"/unknown-source", deadLetter},
		{"/too-many", retry},
		{"/database-down", retry},
		{"/moved", deadLetter},
	}
	for _, c := range expected {
		status, retryAfter := deliver(c.path)
		decision := decide(status)
		hint := ""
		if retryAfter != "" {
			hint = fmt.Sprintf("  (Retry-After: %ss - wait that long, not your own guess)", retryAfter)
		}
		fmt.Printf("POST %-17s -> %d -> sender decides: %s%s\n", c.path, status, decision, hint)
		if decision != c.want {
			panic("FAILED: " + c.path)
		}
	}

	// No answer at all is a retry, not a failure: the event may well have been
	// processed, we simply never heard back (this is level 03's whole reason).
	fmt.Printf("POST (connection timed out) -> no status -> sender decides: %s\n", decide(0))
	if decide(0) != retry {
		panic("FAILED")
	}
	fmt.Println("OK")
}
