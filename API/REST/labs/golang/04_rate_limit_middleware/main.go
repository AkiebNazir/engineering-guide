/*
LAB 04 (advanced) - A per-client rate limiter as middleware (token bucket, stdlib only)
=======================================================================================
You will learn

  - the TOKEN BUCKET: a bucket holds up to `burst` tokens and refills at `rate` tokens/second.
    Each request spends one. Empty bucket -> 429. Bursts are allowed, the long-run average is capped.

    capacity 5, refill 2/s
    t=0.0  [#####]  5 requests pass instantly            (burst)
    t=0.0  [     ]  6th request -> 429  Retry-After: 1
    t=0.5  [#    ]  1 token has refilled

  - per-client limits: key by API key if present, else by client IP (never one global counter)

  - the response contract clients rely on: 429 + Retry-After + RateLimit-* headers

  - making time injectable (a `now func() time.Time`) so tests are instant and deterministic

  - memory hygiene: evict idle buckets or the map grows forever (an easy DoS)

  - why a FIXED WINDOW is worse: it lets a client double the rate around the window edge

Run it   go run ./REST/labs/golang/04_rate_limit_middleware
*/
package main

import (
	"fmt"
	"math"
	"net"
	"net/http"
	"net/http/httptest"
	"strconv"
	"sync"
	"time"
)

type bucket struct {
	tokens float64
	last   time.Time
}

type Limiter struct {
	rate  float64 // tokens added per second
	burst float64 // bucket capacity
	now   func() time.Time

	mu      sync.Mutex
	buckets map[string]*bucket
}

func NewLimiter(rate float64, burst int, now func() time.Time) *Limiter {
	return &Limiter{rate: rate, burst: float64(burst), now: now, buckets: map[string]*bucket{}}
}

// Allow spends one token for key. It reports whether the request may proceed, how many
// tokens remain, and (if denied) how long until one token is available.
func (l *Limiter) Allow(key string) (ok bool, remaining int, retryAfter time.Duration) {
	l.mu.Lock()
	defer l.mu.Unlock()

	now := l.now()
	b, found := l.buckets[key]
	if !found {
		b = &bucket{tokens: l.burst, last: now} // new clients start with a full bucket
		l.buckets[key] = b
	}
	// refill for the time that passed, capped at capacity
	b.tokens = math.Min(l.burst, b.tokens+now.Sub(b.last).Seconds()*l.rate)
	b.last = now

	if b.tokens >= 1 {
		b.tokens--
		return true, int(b.tokens), 0
	}
	wait := time.Duration((1 - b.tokens) / l.rate * float64(time.Second))
	return false, 0, wait
}

// Sweep drops buckets that have been idle long enough to be full again (they carry no information).
func (l *Limiter) Sweep(idle time.Duration) (removed int) {
	l.mu.Lock()
	defer l.mu.Unlock()
	cutoff := l.now().Add(-idle)
	for k, b := range l.buckets {
		if b.last.Before(cutoff) {
			delete(l.buckets, k)
			removed++
		}
	}
	return
}

// clientKey decides WHO is being limited.
// Only trust X-Forwarded-For when you run behind a proxy you control; otherwise anyone can spoof it
// and get a fresh bucket per request.
func clientKey(r *http.Request) string {
	if k := r.Header.Get("X-API-Key"); k != "" {
		return "key:" + k
	}
	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		host = r.RemoteAddr
	}
	return "ip:" + host
}

func RateLimit(l *Limiter) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ok, remaining, retry := l.Allow(clientKey(r))
			w.Header().Set("RateLimit-Limit", strconv.Itoa(int(l.burst)))
			w.Header().Set("RateLimit-Remaining", strconv.Itoa(remaining))
			if !ok {
				secs := int(math.Ceil(retry.Seconds())) // Retry-After is whole seconds
				w.Header().Set("Retry-After", strconv.Itoa(secs))
				w.Header().Set("Content-Type", "application/problem+json")
				w.WriteHeader(http.StatusTooManyRequests)
				fmt.Fprintf(w, `{"type":"about:blank","title":"Too Many Requests","status":429,"detail":"retry in %ds"}`, secs)
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}

// ------------------------------------------------------------------- demo ---
type fakeClock struct{ t time.Time }

func (c *fakeClock) Now() time.Time          { return c.t }
func (c *fakeClock) Advance(d time.Duration) { c.t = c.t.Add(d) }

func main() {
	clock := &fakeClock{t: time.Unix(1_700_000_000, 0)}
	limiter := NewLimiter(2 /* per second */, 5 /* burst */, clock.Now)
	h := RateLimit(limiter)(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { fmt.Fprint(w, "ok") }))

	hit := func(remoteAddr, apiKey string) *httptest.ResponseRecorder {
		req := httptest.NewRequest("GET", "/", nil)
		req.RemoteAddr = remoteAddr
		if apiKey != "" {
			req.Header.Set("X-API-Key", apiKey)
		}
		rec := httptest.NewRecorder()
		h.ServeHTTP(rec, req)
		return rec
	}
	must := func(ok bool, what string) {
		if !ok {
			panic("FAILED: " + what)
		}
	}

	fmt.Println("-- burst of 7 from one IP (capacity 5) --")
	codes := []int{}
	for i := 0; i < 7; i++ {
		rec := hit("203.0.113.5:5000", "")
		codes = append(codes, rec.Code)
	}
	fmt.Println("statuses:", codes)
	must(fmt.Sprint(codes) == "[200 200 200 200 200 429 429]", "burst allowed then blocked")

	rec := hit("203.0.113.5:5000", "")
	fmt.Printf("blocked response: %d Retry-After=%s Remaining=%s body=%s\n",
		rec.Code, rec.Header().Get("Retry-After"), rec.Header().Get("RateLimit-Remaining"), rec.Body.String())
	must(rec.Header().Get("Retry-After") == "1", "Retry-After")

	fmt.Println("-- another client is unaffected --")
	must(hit("198.51.100.9:1234", "").Code == 200, "per-client isolation")
	must(hit("198.51.100.9:9999", "").Code == 200, "same IP different port shares a bucket")

	fmt.Println("-- API key beats IP: two keys behind one NAT get separate buckets --")
	must(hit("203.0.113.5:5000", "key-A").Code == 200, "key A")
	must(hit("203.0.113.5:5000", "key-B").Code == 200, "key B")

	fmt.Println("-- refill: 2 tokens/second, wait 1s --")
	clock.Advance(time.Second)
	a, b, c := hit("203.0.113.5:5000", "").Code, hit("203.0.113.5:5000", "").Code, hit("203.0.113.5:5000", "").Code
	fmt.Println("after 1s:", a, b, c, "(two tokens came back)")
	must(a == 200 && b == 200 && c == 429, "refill")

	fmt.Println("-- eviction of idle clients --")
	fmt.Println("buckets before:", len(limiter.buckets))
	clock.Advance(10 * time.Minute)
	fmt.Println("swept:", limiter.Sweep(5*time.Minute), "buckets after:", len(limiter.buckets))
	must(len(limiter.buckets) == 0, "sweep")

	fmt.Println("-- why not a fixed window? both configured as \"5 requests per 10 seconds\" --")
	// Fixed window: a counter that resets every 10s boundary.
	windowCount, currentWindow := 0, int64(-1)
	fixedAllow := func(t time.Time) bool {
		if w := t.Unix() / 10; w != currentWindow {
			currentWindow, windowCount = w, 0
		}
		windowCount++
		return windowCount <= 5
	}
	bucketLimiter := NewLimiter(0.5, 5, clock.Now) // 0.5 tokens/s * 10s = 5 per 10s on average
	start := time.Unix(1_700_000_000, 0).Add(time.Hour)
	start = start.Add(-time.Duration(start.Unix()%10) * time.Second) // align to a window boundary
	fixedOK, bucketOK := 0, 0
	for i := 0; i < 10; i++ { // 5 requests at t=9.9s (end of window 1) then 5 at t=10.0s (start of window 2)
		t := start.Add(9900 * time.Millisecond)
		if i >= 5 {
			t = start.Add(10 * time.Second)
		}
		clock.t = t
		if fixedAllow(t) {
			fixedOK++
		}
		if ok, _, _ := bucketLimiter.Allow("x"); ok {
			bucketOK++
		}
	}
	fmt.Printf("10 requests inside 0.1s -> fixed window allowed %d, token bucket allowed %d\n", fixedOK, bucketOK)
	must(fixedOK == 10 && bucketOK == 5, "fixed window double-burst")
	fmt.Println("OK")
}
