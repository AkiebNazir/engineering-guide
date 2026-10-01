/*
LAB 05 (advanced) - The product around the pipe: subscriptions, per-endpoint secrets, circuit breaker, delivery log and replay
=============================================================================================================================
What customers of a webhook platform expect - and what you will build here:

  - SUBSCRIPTIONS: each endpoint picks the event types it wants ("invoice.*", "order.shipped", "*")

  - PER-ENDPOINT SECRETS: a leak of one customer's secret must not affect anyone else

  - a CIRCUIT BREAKER per endpoint - closed -> open -> half-open:

    closed ----(N consecutive failures)----> OPEN  (don't even try; defer the events)
    ^                                        |
    |                                  cooldown passes
    +---(probe succeeds)--- HALF-OPEN <------+     (let exactly ONE request through)
    |
    probe fails -> back to OPEN

    It protects the failing customer (no hammering), your workers (no waiting on timeouts) and every
    other customer (no starvation).

  - a DELIVERY LOG per endpoint, a REPLAY button, and a TEST-EVENT ("ping") endpoint - the support
    tooling that turns "your webhooks are broken" tickets into self-service

  - a small management API on net/http (Go 1.22 patterns)

Run it   go run ./Webhooks/labs/golang/05_subscriptions_breaker_and_replay
*/
package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"path"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

// ------------------------------------------------------------- circuit breaker ---
type state int

const (
	closed state = iota
	open
	halfOpen
)

func (s state) String() string { return [...]string{"CLOSED", "OPEN", "HALF-OPEN"}[s] }

type Breaker struct {
	mu        sync.Mutex
	st        state
	failures  int
	openedAt  time.Time
	probing   bool
	threshold int
	cooldown  time.Duration
	now       func() time.Time
}

// Allow says whether a request may be sent NOW.
func (b *Breaker) Allow() bool {
	b.mu.Lock()
	defer b.mu.Unlock()
	switch b.st {
	case closed:
		return true
	case open:
		if b.now().Sub(b.openedAt) >= b.cooldown {
			b.st, b.probing = halfOpen, true // cooldown over: allow ONE probe
			return true
		}
		return false
	default: // halfOpen: only the single probe is in flight
		if !b.probing {
			b.probing = true
			return true
		}
		return false
	}
}

func (b *Breaker) Report(success bool) {
	b.mu.Lock()
	defer b.mu.Unlock()
	if success {
		b.st, b.failures, b.probing = closed, 0, false
		return
	}
	b.failures++
	if b.st == halfOpen || b.failures >= b.threshold {
		b.st, b.openedAt, b.probing = open, b.now(), false
	}
}

func (b *Breaker) State() state { b.mu.Lock(); defer b.mu.Unlock(); return b.st }

// -------------------------------------------------------------------- registry ---
type Endpoint struct {
	ID      string   `json:"id"`
	URL     string   `json:"url"`
	Events  []string `json:"events"`
	secret  string
	breaker *Breaker
}

type Delivery struct {
	ID       int       `json:"id"`
	Endpoint string    `json:"endpoint"`
	EventID  string    `json:"event_id"`
	Type     string    `json:"type"`
	Status   string    `json:"status"` // delivered | failed | deferred
	Code     int       `json:"code,omitempty"`
	At       time.Time `json:"at"`
	body     []byte
}

type Platform struct {
	mu         sync.Mutex
	endpoints  map[string]*Endpoint
	deliveries []*Delivery
	nextID     int
	client     *http.Client
	now        func() time.Time
}

func matches(patterns []string, eventType string) bool {
	for _, p := range patterns {
		if ok, _ := path.Match(p, eventType); ok || p == "*" { // "invoice.*" style globs; note path.Match: '*' does not cross '/'
			return true
		}
	}
	return false
}

func (p *Platform) Register(ep *Endpoint, threshold int, cooldown time.Duration) {
	ep.breaker = &Breaker{threshold: threshold, cooldown: cooldown, now: p.now}
	p.mu.Lock()
	p.endpoints[ep.ID] = ep
	p.mu.Unlock()
}

func sign(secret string, ts int64, body []byte) string {
	m := hmac.New(sha256.New, []byte(secret))
	fmt.Fprintf(m, "%d.", ts)
	m.Write(body)
	return hex.EncodeToString(m.Sum(nil))
}

func (p *Platform) record(ep *Endpoint, eventID, typ string, body []byte, status string, code int) *Delivery {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.nextID++
	d := &Delivery{ID: p.nextID, Endpoint: ep.ID, EventID: eventID, Type: typ, Status: status, Code: code, At: p.now(), body: body}
	p.deliveries = append(p.deliveries, d)
	return d
}

func (p *Platform) send(ep *Endpoint, eventID, typ string, body []byte) *Delivery {
	if !ep.breaker.Allow() { // breaker open: do NOT touch the network
		return p.record(ep, eventID, typ, body, "deferred", 0)
	}
	ts := p.now().Unix()
	req, _ := http.NewRequest("POST", ep.URL, strings.NewReader(string(body)))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Webhook-Id", eventID)
	req.Header.Set("Webhook-Signature", fmt.Sprintf("t=%d,v1=%s", ts, sign(ep.secret, ts, body))) // THIS endpoint's secret
	res, err := p.client.Do(req)
	code := 0
	if err == nil {
		code = res.StatusCode
		io.Copy(io.Discard, io.LimitReader(res.Body, 64<<10))
		res.Body.Close()
	}
	ok := err == nil && code >= 200 && code < 300
	ep.breaker.Report(ok)
	if ok {
		return p.record(ep, eventID, typ, body, "delivered", code)
	}
	return p.record(ep, eventID, typ, body, "failed", code)
}

// Publish fans one event out to every subscribed endpoint, concurrently.
func (p *Platform) Publish(eventID, typ string, data any) map[string]string {
	body, _ := json.Marshal(map[string]any{"id": eventID, "type": typ, "data": data})
	p.mu.Lock()
	var targets []*Endpoint
	for _, ep := range p.endpoints {
		if matches(ep.Events, typ) {
			targets = append(targets, ep)
		}
	}
	p.mu.Unlock()
	results := map[string]string{}
	var mu sync.Mutex
	var wg sync.WaitGroup
	for _, ep := range targets {
		wg.Add(1)
		go func() {
			defer wg.Done()
			d := p.send(ep, eventID, typ, body)
			mu.Lock()
			results[ep.ID] = d.Status
			mu.Unlock()
		}()
	}
	wg.Wait()
	return results
}

// ---------------------------------------------------------- management API ---
func (p *Platform) API() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /endpoints/{id}/deliveries", func(w http.ResponseWriter, r *http.Request) {
		p.mu.Lock()
		var out []*Delivery
		for _, d := range p.deliveries {
			if d.Endpoint == r.PathValue("id") {
				out = append(out, d)
			}
		}
		p.mu.Unlock()
		json.NewEncoder(w).Encode(out)
	})
	mux.HandleFunc("POST /endpoints/{id}/deliveries/{did}/replay", func(w http.ResponseWriter, r *http.Request) {
		did, _ := strconv.Atoi(r.PathValue("did"))
		p.mu.Lock()
		ep := p.endpoints[r.PathValue("id")]
		var orig *Delivery
		for _, d := range p.deliveries {
			if d.ID == did && ep != nil && d.Endpoint == ep.ID {
				orig = d
			}
		}
		p.mu.Unlock()
		if orig == nil {
			http.NotFound(w, r)
			return
		}
		nd := p.send(ep, orig.EventID, orig.Type, orig.body) // SAME event id: receivers dedupe it
		json.NewEncoder(w).Encode(nd)
	})
	mux.HandleFunc("POST /endpoints/{id}/test", func(w http.ResponseWriter, r *http.Request) {
		p.mu.Lock()
		ep := p.endpoints[r.PathValue("id")]
		p.mu.Unlock()
		if ep == nil {
			http.NotFound(w, r)
			return
		}
		body, _ := json.Marshal(map[string]any{"id": "evt_test_" + strconv.FormatInt(time.Now().UnixNano(), 36), "type": "ping", "data": map[string]string{"hello": "world"}})
		json.NewEncoder(w).Encode(p.send(ep, "evt_test", "ping", body)) // test events bypass subscriptions
	})
	return mux
}

// ------------------------------------------------------------- customer side ---
type customer struct {
	srv     *httptest.Server
	hits    atomic.Int64
	failing atomic.Bool
	secret  string
	badSigs atomic.Int64
}

func newCustomer(secret string) *customer {
	c := &customer{secret: secret}
	c.srv = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		c.hits.Add(1)
		body, _ := io.ReadAll(r.Body)
		var t int64
		var sig string
		for _, part := range strings.Split(r.Header.Get("Webhook-Signature"), ",") {
			k, v, _ := strings.Cut(part, "=")
			if k == "t" {
				t, _ = strconv.ParseInt(v, 10, 64)
			} else if k == "v1" {
				sig = v
			}
		}
		if !hmac.Equal([]byte(sig), []byte(sign(c.secret, t, body))) {
			c.badSigs.Add(1)
			w.WriteHeader(401)
			return
		}
		if c.failing.Load() {
			w.WriteHeader(503)
			return
		}
		w.WriteHeader(200)
	}))
	return c
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	clock := struct {
		sync.Mutex
		t time.Time
	}{t: time.Unix(1_800_000_000, 0)}
	now := func() time.Time { clock.Lock(); defer clock.Unlock(); return clock.t }
	advance := func(d time.Duration) { clock.Lock(); clock.t = clock.t.Add(d); clock.Unlock() }

	p := &Platform{endpoints: map[string]*Endpoint{}, client: &http.Client{Timeout: time.Second}, now: now}
	billing, shipping, audit := newCustomer("sec_billing"), newCustomer("sec_shipping"), newCustomer("sec_audit")
	defer billing.srv.Close()
	defer shipping.srv.Close()
	defer audit.srv.Close()
	p.Register(&Endpoint{ID: "billing", URL: billing.srv.URL, Events: []string{"invoice.*"}, secret: "sec_billing"}, 3, time.Minute)
	p.Register(&Endpoint{ID: "shipping", URL: shipping.srv.URL, Events: []string{"order.shipped", "order.delivered"}, secret: "sec_shipping"}, 3, time.Minute)
	p.Register(&Endpoint{ID: "audit", URL: audit.srv.URL, Events: []string{"*"}, secret: "sec_audit"}, 3, time.Minute)

	fmt.Println("== 1. subscription routing ==")
	for _, ev := range []struct{ id, typ string }{{"e1", "invoice.paid"}, {"e2", "order.shipped"}, {"e3", "user.created"}, {"e4", "invoice.failed"}} {
		res := p.Publish(ev.id, ev.typ, map[string]string{"k": "v"})
		var to []string
		for id := range res {
			to = append(to, id)
		}
		fmt.Printf("  %-15s -> %d endpoint(s): %v\n", ev.typ, len(res), sortStrings(to))
	}
	must(billing.hits.Load() == 2 && shipping.hits.Load() == 1 && audit.hits.Load() == 4, "routing matrix")
	must(billing.badSigs.Load()+shipping.badSigs.Load()+audit.badSigs.Load() == 0, "each endpoint verified with its OWN secret")
	fmt.Println("  every request verified with that endpoint's own secret (0 signature failures)")

	fmt.Println("\n== 2. billing's server starts failing: watch the breaker ==")
	billing.failing.Store(true)
	for i := 1; i <= 6; i++ {
		res := p.Publish(fmt.Sprintf("f%d", i), "invoice.paid", nil)
		ep := p.endpoints["billing"]
		fmt.Printf("  event f%d: billing=%-9s breaker=%-9s | audit=%s\n", i, res["billing"], ep.breaker.State(), res["audit"])
	}
	must(p.endpoints["billing"].breaker.State() == open, "breaker opened")
	hitsWhenOpen := billing.hits.Load()
	fmt.Printf("  billing received %d requests in total for 6 events: the last 3 were never sent (deferred)\n", hitsWhenOpen-2)
	must(hitsWhenOpen-2 == 3, "breaker stopped traffic after the 3rd failure")
	must(audit.hits.Load() == 4+6, "audit customer was completely unaffected")

	fmt.Println("\n== 3. cooldown, half-open probe, recovery ==")
	advance(30 * time.Second)
	p.Publish("g1", "invoice.paid", nil)
	fmt.Printf("  +30s : breaker still %s (cooldown is 60s); requests to billing unchanged: %v\n", p.endpoints["billing"].breaker.State(), billing.hits.Load() == hitsWhenOpen)
	must(billing.hits.Load() == hitsWhenOpen, "still open")
	advance(31 * time.Second)
	p.Publish("g2", "invoice.paid", nil) // half-open: ONE probe goes out ... and fails
	fmt.Printf("  +61s : one PROBE was sent (%d new request) and failed -> breaker %s again\n", billing.hits.Load()-hitsWhenOpen, p.endpoints["billing"].breaker.State())
	must(billing.hits.Load() == hitsWhenOpen+1 && p.endpoints["billing"].breaker.State() == open, "failed probe re-opens")
	billing.failing.Store(false) // the customer fixes their server
	advance(61 * time.Second)
	res := p.Publish("g3", "invoice.paid", nil)
	fmt.Printf("  +122s: customer fixed it; probe succeeded -> billing=%s, breaker %s\n", res["billing"], p.endpoints["billing"].breaker.State())
	must(res["billing"] == "delivered" && p.endpoints["billing"].breaker.State() == closed, "recovered")

	fmt.Println("\n== 4. support tooling: delivery log, replay of what was deferred, test event ==")
	api := httptest.NewServer(p.API())
	defer api.Close()
	get := func(method, url string) []byte {
		req, _ := http.NewRequest(method, api.URL+url, nil)
		res, err := http.DefaultClient.Do(req)
		must(err == nil, "api call")
		defer res.Body.Close()
		b, _ := io.ReadAll(res.Body)
		return b
	}
	var list []Delivery
	json.Unmarshal(get("GET", "/endpoints/billing/deliveries"), &list)
	counts := map[string]int{}
	var firstDeferred int
	for _, d := range list {
		counts[d.Status]++
		if d.Status == "deferred" && firstDeferred == 0 {
			firstDeferred = d.ID
		}
	}
	fmt.Printf("  GET .../billing/deliveries -> %d records: %v\n", len(list), counts)
	must(counts["deferred"] >= 3 && counts["failed"] >= 4 && counts["delivered"] >= 3, "delivery log has the full history")

	var replayed Delivery
	json.Unmarshal(get("POST", "/endpoints/billing/deliveries/"+strconv.Itoa(firstDeferred)+"/replay"), &replayed)
	fmt.Printf("  POST .../deliveries/%d/replay -> event %s: %s (same event id, so a receiver's dedupe still works)\n", firstDeferred, replayed.EventID, replayed.Status)
	must(replayed.Status == "delivered", "replay succeeded after recovery")

	var ping Delivery
	json.Unmarshal(get("POST", "/endpoints/shipping/test"), &ping)
	fmt.Printf("  POST .../shipping/test -> %s event: %s (bypasses subscriptions; lets customers verify their setup)\n", ping.Type, ping.Status)
	must(ping.Type == "ping" && ping.Status == "delivered", "test event")
	fmt.Println("\nOK")
}

func sortStrings(s []string) []string {
	for i := range s {
		for j := i + 1; j < len(s); j++ {
			if s[j] < s[i] {
				s[i], s[j] = s[j], s[i]
			}
		}
	}
	return s
}
