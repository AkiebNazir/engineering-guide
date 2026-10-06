/*
LAB 03 (advanced) - A webhook delivery engine in Go: worker pool, retries with jitter, per-endpoint limits
==========================================================================================================
You will learn

  - the architecture of the SENDER side:

    events -> [ jobs channel ] -> N workers -> HTTP POST -> classify -> delivered | retry(timer) | dead-letter
    ^                                          |
    +---------- time.AfterFunc(backoff) -------+

  - a bounded worker pool (N goroutines) so 10,000 events do not open 10,000 connections

  - a PER-ENDPOINT concurrency cap (semaphore) acquired with a NON-blocking select: one slow
    customer must not park every worker (head-of-line blocking). The lab measures this.

  - a proper http.Client for webhooks:  total Timeout, no redirects, response body drained + closed
    (so keep-alive connections are reused) but LIMITED (a hostile endpoint cannot stream gigabytes)

  - classifying outcomes: 2xx ok | 429 + Retry-After | 410 disable | everything else retry

  - exponential backoff with FULL JITTER, and honouring Retry-After

  - accounting: a sync.WaitGroup that counts jobs until they are TERMINAL (delivered or dead)

  - so Stop() can wait for retries that are still waiting on timers

  - graceful shutdown that does not lose work

Run it   go run ./Webhooks/labs/golang/03_delivery_worker_pool
*/
package main

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"math/rand/v2"
	"net/http"
	"net/http/httptest"
	"sort"
	"strconv"
	"sync"
	"sync/atomic"
	"time"
)

// ------------------------------------------------------------------ engine ---
type Job struct {
	EventID  string
	Endpoint *Endpoint
	Body     []byte
	Attempt  int
}

type Endpoint struct {
	Name string
	URL  string
	sem  chan struct{} // per-endpoint concurrency limit
	// state below guarded by mu
	mu       sync.Mutex
	Disabled bool
	Failures int
}

type Outcome struct {
	Delivered bool
	Attempts  int
	Reason    string
	At        time.Time
}

type Engine struct {
	client   *http.Client
	jobs     chan Job
	wg       sync.WaitGroup // jobs not yet TERMINAL (delivered / dead)
	workers  sync.WaitGroup
	stopping atomic.Bool

	base       time.Duration // first backoff step (tiny in this demo; seconds/minutes in production)
	maxAttempt int

	mu       sync.Mutex
	outcomes map[string]Outcome // "event@endpoint" -> result
	attempts atomic.Int64
	inFlight atomic.Int64
	maxSeen  atomic.Int64 // highest concurrent in-flight requests observed
}

func NewEngine(workers int, base time.Duration, maxAttempt int) *Engine {
	e := &Engine{
		client: &http.Client{
			Timeout:       400 * time.Millisecond,
			CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }, // never follow redirects
		},
		jobs: make(chan Job, 1024), base: base, maxAttempt: maxAttempt, outcomes: map[string]Outcome{},
	}
	for i := 0; i < workers; i++ {
		e.workers.Add(1)
		go func() {
			defer e.workers.Done()
			for j := range e.jobs {
				e.process(j)
			}
		}()
	}
	return e
}

func NewEndpoint(name, url string, maxConcurrent int) *Endpoint {
	return &Endpoint{Name: name, URL: url, sem: make(chan struct{}, maxConcurrent)}
}

// Submit accepts a new event for an endpoint.
func (e *Engine) Submit(ep *Endpoint, eventID string, body []byte) bool {
	if e.stopping.Load() {
		return false
	}
	e.wg.Add(1)
	e.jobs <- Job{EventID: eventID, Endpoint: ep, Body: body}
	return true
}

func (e *Engine) finish(j Job, ok bool, reason string) {
	e.mu.Lock()
	e.outcomes[j.EventID+"@"+j.Endpoint.Name] = Outcome{ok, j.Attempt + 1, reason, time.Now()}
	e.mu.Unlock()
	e.wg.Done() // this job is now TERMINAL
}

func (e *Engine) retryLater(j Job, wait time.Duration, why string) {
	j.Attempt++
	if j.Attempt >= e.maxAttempt {
		e.finish(Job{EventID: j.EventID, Endpoint: j.Endpoint, Attempt: j.Attempt - 1}, false, "dead-lettered after "+why)
		return
	}
	time.AfterFunc(wait, func() { e.jobs <- j }) // the job stays "not terminal", so wg still counts it
}

func (e *Engine) backoff(attempt int) time.Duration {
	ceiling := e.base << attempt // base * 2^attempt
	return time.Duration(rand.Int64N(int64(ceiling)) + 1)
}

func (e *Engine) process(j Job) {
	ep := j.Endpoint
	ep.mu.Lock()
	disabled := ep.Disabled
	ep.mu.Unlock()
	if disabled {
		e.finish(j, false, "endpoint disabled")
		return
	}

	// Acquire this endpoint's slot WITHOUT BLOCKING. If the endpoint is at its cap, put the job back
	// for a moment and free this worker for someone else. (Blocking here - `ep.sem <- struct{}{}` -
	// would let one crowded endpoint park every worker and starve all the others.)
	select {
	case ep.sem <- struct{}{}:
	default:
		time.AfterFunc(5*time.Millisecond, func() { e.jobs <- j })
		return
	}
	n := e.inFlight.Add(1)
	for {
		m := e.maxSeen.Load()
		if n <= m || e.maxSeen.CompareAndSwap(m, n) {
			break
		}
	}
	status, retryAfter, err := e.post(ep.URL, j.Body)
	e.inFlight.Add(-1)
	<-ep.sem
	e.attempts.Add(1)

	switch {
	case err == nil && status >= 200 && status < 300:
		ep.mu.Lock()
		ep.Failures = 0
		ep.mu.Unlock()
		e.finish(j, true, "delivered")
	case err == nil && status == 410:
		ep.mu.Lock()
		ep.Disabled = true
		ep.mu.Unlock()
		e.finish(j, false, "410 Gone: endpoint disabled")
	case err == nil && status == 429:
		wait := e.backoff(j.Attempt)
		if retryAfter > wait { // obey the receiver's pacing when it is longer than ours
			wait = retryAfter
		}
		e.retryLater(j, wait, "429")
	default: // 5xx, other 4xx, timeouts, connection errors
		why := "timeout/connection error"
		if err == nil {
			why = strconv.Itoa(status)
		}
		e.retryLater(j, e.backoff(j.Attempt), why)
	}
}

func (e *Engine) post(url string, body []byte) (status int, retryAfter time.Duration, err error) {
	req, _ := http.NewRequest("POST", url, bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	res, err := e.client.Do(req)
	if err != nil {
		return 0, 0, err
	}
	defer res.Body.Close()
	io.Copy(io.Discard, io.LimitReader(res.Body, 64<<10)) // drain (up to 64 KiB) so the connection can be reused
	if s := res.Header.Get("Retry-After"); s != "" {
		if secs, err := strconv.ParseFloat(s, 64); err == nil {
			retryAfter = time.Duration(secs * float64(time.Second))
		}
	}
	return res.StatusCode, retryAfter, nil
}

// Stop refuses new work, waits for every accepted job to reach a terminal state, then ends the workers.
func (e *Engine) Stop(ctx context.Context) error {
	e.stopping.Store(true)
	done := make(chan struct{})
	go func() { e.wg.Wait(); close(done) }()
	select {
	case <-done:
		close(e.jobs)
		e.workers.Wait()
		return nil
	case <-ctx.Done():
		return ctx.Err() // out of time: in production, persist the pending jobs before exiting
	}
}

// ------------------------------------------------------------- test servers ---
type counters struct{ hits sync.Map }

func (c *counters) inc(key string) int {
	v, _ := c.hits.LoadOrStore(key, new(atomic.Int64))
	return int(v.(*atomic.Int64).Add(1))
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	var cnt counters
	newServer := func(h http.HandlerFunc) *httptest.Server { return httptest.NewServer(h) }

	healthy := newServer(func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(200) })
	flaky := newServer(func(w http.ResponseWriter, r *http.Request) { // fails the first 2 attempts of EVERY event
		body, _ := io.ReadAll(r.Body)
		if cnt.inc("flaky:"+string(body)) <= 2 {
			w.WriteHeader(503)
			return
		}
		w.WriteHeader(200)
	})
	slow := newServer(func(w http.ResponseWriter, r *http.Request) { time.Sleep(700 * time.Millisecond); w.WriteHeader(200) })
	limited := newServer(func(w http.ResponseWriter, r *http.Request) {
		if cnt.inc("limited") == 1 {
			w.Header().Set("Retry-After", "0.3")
			w.WriteHeader(429)
			return
		}
		w.WriteHeader(200)
	})
	gone := newServer(func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(410) })
	down := newServer(func(w http.ResponseWriter, r *http.Request) {})
	downURL := down.URL
	down.Close() // connection refused from now on
	var concurrent, maxConcurrent atomic.Int64
	crowded := newServer(func(w http.ResponseWriter, r *http.Request) { // records how many requests overlap
		n := concurrent.Add(1)
		for {
			m := maxConcurrent.Load()
			if n <= m || maxConcurrent.CompareAndSwap(m, n) {
				break
			}
		}
		time.Sleep(50 * time.Millisecond)
		concurrent.Add(-1)
		w.WriteHeader(200)
	})
	defer func() {
		healthy.Close()
		flaky.Close()
		slow.Close()
		limited.Close()
		gone.Close()
		crowded.Close()
	}()

	engine := NewEngine(8, 20*time.Millisecond, 5)
	eps := map[string]*Endpoint{
		"healthy": NewEndpoint("healthy", healthy.URL, 4), "flaky": NewEndpoint("flaky", flaky.URL, 4),
		"slow": NewEndpoint("slow", slow.URL, 4), "limited": NewEndpoint("limited", limited.URL, 4),
		"gone": NewEndpoint("gone", gone.URL, 4), "down": NewEndpoint("down", downURL, 4),
		"crowded": NewEndpoint("crowded", crowded.URL, 2), // per-endpoint cap = 2
	}

	fmt.Println("== submitting 1 event to each endpoint, plus 20 to a crowded one (cap: 2 at a time) ==")
	start := time.Now()
	for name, ep := range eps {
		if name != "crowded" {
			engine.Submit(ep, "evt_1", []byte(`{"id":"evt_1"}`))
		}
	}
	for i := 0; i < 20; i++ {
		engine.Submit(eps["crowded"], fmt.Sprintf("evt_c%d", i), []byte("{}"))
	}
	engine.Submit(eps["healthy"], "evt_fast", []byte("{}")) // submitted AFTER the 20 crowded events
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	must(engine.Stop(ctx) == nil, "Stop waits for every job to finish (including timers still pending)")
	fmt.Printf("  all jobs terminal after %s; %d HTTP attempts in total\n", time.Since(start).Round(time.Millisecond), engine.attempts.Load())

	fmt.Println("\n== outcomes ==")
	names := []string{"healthy", "flaky", "limited", "slow", "gone", "down"}
	sort.Strings(names)
	for _, n := range names {
		o := engine.outcomes["evt_1@"+n]
		fmt.Printf("  %-8s delivered=%-5v attempts=%d  %s\n", n, o.Delivered, o.Attempts, o.Reason)
	}
	must(engine.outcomes["evt_1@healthy"].Delivered && engine.outcomes["evt_1@healthy"].Attempts == 1, "healthy first try")
	must(engine.outcomes["evt_1@flaky"].Delivered && engine.outcomes["evt_1@flaky"].Attempts == 3, "flaky succeeds on attempt 3")
	must(engine.outcomes["evt_1@limited"].Delivered && engine.outcomes["evt_1@limited"].Attempts == 2, "429 then success")
	must(!engine.outcomes["evt_1@slow"].Delivered && engine.outcomes["evt_1@slow"].Attempts == 5, "slow endpoint times out every attempt")
	must(!engine.outcomes["evt_1@down"].Delivered && engine.outcomes["evt_1@down"].Attempts == 5, "down endpoint dead-lettered")
	must(!engine.outcomes["evt_1@gone"].Delivered && eps["gone"].Disabled, "410 disables")

	delivered := 0
	for i := 0; i < 20; i++ {
		if engine.outcomes[fmt.Sprintf("evt_c%d@crowded", i)].Delivered {
			delivered++
		}
	}
	fmt.Printf("\n== per-endpoint concurrency cap ==\n  20 events to one endpoint with cap 2 on an 8-worker pool: %d delivered, max simultaneous requests at the server = %d\n",
		delivered, maxConcurrent.Load())
	must(delivered == 20 && maxConcurrent.Load() <= 2, "cap respected: one endpoint cannot monopolise the pool")
	var lastCrowded time.Time
	for i := 0; i < 20; i++ {
		if at := engine.outcomes[fmt.Sprintf("evt_c%d@crowded", i)].At; at.After(lastCrowded) {
			lastCrowded = at
		}
	}
	fast := engine.outcomes["evt_fast@healthy"].At
	fmt.Printf("  the healthy endpoint's event (queued BEHIND all 20) was delivered %s before the crowded backlog finished\n",
		lastCrowded.Sub(fast).Round(time.Millisecond))
	must(fast.Before(lastCrowded), "no head-of-line blocking: the healthy event overtook the crowded backlog")
	fmt.Printf("  overall max in-flight requests across all endpoints: %d (pool size 8)\n", engine.maxSeen.Load())
	must(engine.maxSeen.Load() <= 8, "worker pool bound")

	fmt.Println("\n== after Stop(), new events are refused ==")
	must(!engine.Submit(eps["healthy"], "evt_late", []byte("{}")), "no work accepted after Stop")
	fmt.Println("  Submit returned false: the caller must persist the event and try after restart")
	fmt.Println("\nOK")
}
