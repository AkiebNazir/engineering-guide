/*
LAB 03 (advanced) - Gateway as BFF: fan-out aggregation, response caching, request coalescing
=============================================================================================
Some gateways do more than forward: a Backend-for-Frontend (BFF) route answers ONE client call by
calling several services, and an edge cache stops identical requests from reaching them at all.
This lab builds both, and shows the failure modes that make them hard.

	GET /bff/home/{user} --+--> profile   (required, 100 ms budget)
	                       +--> orders    (optional, 100 ms budget)   --> one JSON document,
	                       +--> recommend (optional, 100 ms budget)       partial if needed

You will learn

  - fan-out in PARALLEL with a per-call deadline (context.WithTimeout) so the page costs
    max(latencies), not their sum
  - REQUIRED vs OPTIONAL parts: a missing optional part becomes null + a "degraded" list; a missing
    required part fails the whole call (502). Decide this per field with the product owner
  - a response CACHE keyed on method + path + the headers the response VARIES on, honouring the
    upstream's Cache-Control: max-age, private and no-store
  - STALE-WHILE-REVALIDATE: serve the stale copy instantly and refresh in the background
  - REQUEST COALESCING (singleflight, hand-written): when the cache entry expires under load,
    100 concurrent misses must become ONE upstream call, not 100 (the "thundering herd" or
    "cache stampede")

Run it   go run ./Gateway/labs/golang/03_aggregation_caching_and_coalescing
*/
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

func must(cond bool, msg string) {
	if !cond {
		panic("FAILED: " + msg)
	}
}

// ================================================================== upstreams ===
type upstream struct {
	delay atomic.Int64 // ms
	calls atomic.Int64
	srv   *httptest.Server
}

func newUpstream(name, cacheControl string) *upstream {
	u := &upstream{}
	u.srv = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		u.calls.Add(1)
		select {
		case <-time.After(time.Duration(u.delay.Load()) * time.Millisecond):
		case <-r.Context().Done(): // the gateway gave up: stop working too
			return
		}
		if cacheControl != "" {
			w.Header().Set("Cache-Control", cacheControl)
		}
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprintf(w, `{"from":%q,"path":%q,"n":%d}`, name, r.URL.Path, u.calls.Load())
	}))
	return u
}

// ============================================================ fan-out aggregation ===
type part struct {
	name, url string
	required  bool
}

func fetchJSON(ctx context.Context, url string) (any, error) {
	req, _ := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("status %d", resp.StatusCode)
	}
	var v any
	return v, json.NewDecoder(resp.Body).Decode(&v)
}

func aggregate(parts []part, budget time.Duration) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		user := r.PathValue("user")
		out := map[string]any{}
		degraded := []string{}
		var mu sync.Mutex
		var wg sync.WaitGroup
		failedRequired := false
		for _, p := range parts {
			wg.Add(1)
			go func(p part) {
				defer wg.Done()
				ctx, cancel := context.WithTimeout(r.Context(), budget)
				defer cancel()
				v, err := fetchJSON(ctx, p.url+"/"+user)
				mu.Lock()
				defer mu.Unlock()
				if err != nil {
					out[p.name] = nil
					degraded = append(degraded, p.name)
					failedRequired = failedRequired || p.required
					return
				}
				out[p.name] = v
			}(p)
		}
		wg.Wait()
		w.Header().Set("Content-Type", "application/json")
		if failedRequired {
			w.WriteHeader(http.StatusBadGateway)
			json.NewEncoder(w).Encode(map[string]any{"error": "required part unavailable", "degraded": degraded})
			return
		}
		out["degraded"] = degraded
		json.NewEncoder(w).Encode(out)
	}
}

// ==================================================================== caching ===
type entry struct {
	body                []byte
	header              http.Header
	freshUntil, staleOK time.Time
}

type Cache struct {
	mu       sync.Mutex
	entries  map[string]*entry
	inflight map[string]*call // singleflight
	upstream string
	varyOn   []string
	fetches  atomic.Int64
}

type call struct {
	wg  sync.WaitGroup
	e   *entry
	err error
}

func (c *Cache) key(r *http.Request) string {
	k := r.Method + " " + r.URL.RequestURI()
	for _, h := range c.varyOn { // Vary: the same URL in another language is a different object
		k += "|" + h + "=" + r.Header.Get(h)
	}
	return k
}

func parseCC(v string) (maxAge, swr int, store bool) {
	store = true
	for _, d := range strings.Split(v, ",") {
		d = strings.TrimSpace(d)
		switch {
		case d == "no-store" || d == "private": // private: a SHARED cache must not keep it
			store = false
		case strings.HasPrefix(d, "max-age="):
			maxAge, _ = strconv.Atoi(strings.TrimPrefix(d, "max-age="))
		case strings.HasPrefix(d, "stale-while-revalidate="):
			swr, _ = strconv.Atoi(strings.TrimPrefix(d, "stale-while-revalidate="))
		}
	}
	return
}

// fetch coalesces concurrent misses for the same key into one upstream request.
func (c *Cache) fetch(key string, r *http.Request) (*entry, error) {
	c.mu.Lock()
	if e, ok := c.entries[key]; ok && time.Now().Before(e.freshUntil) {
		c.mu.Unlock() // re-check under the lock: a fetch may have finished since our cache lookup
		return e, nil
	}
	if cl, ok := c.inflight[key]; ok {
		c.mu.Unlock()
		cl.wg.Wait() // someone is already fetching it: wait for their answer
		return cl.e, cl.err
	}
	cl := &call{}
	cl.wg.Add(1)
	c.inflight[key] = cl
	c.mu.Unlock()

	c.fetches.Add(1)
	req, _ := http.NewRequest(r.Method, c.upstream+r.URL.RequestURI(), nil)
	for _, h := range c.varyOn {
		req.Header.Set(h, r.Header.Get(h))
	}
	resp, err := http.DefaultClient.Do(req)
	if err == nil {
		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		maxAge, swr, store := parseCC(resp.Header.Get("Cache-Control"))
		now := time.Now()
		cl.e = &entry{body, resp.Header.Clone(), now.Add(time.Duration(maxAge) * time.Millisecond),
			now.Add(time.Duration(maxAge+swr) * time.Millisecond)} // lab time: 1 "second" = 1 ms
		c.mu.Lock()
		if store && maxAge > 0 {
			c.entries[key] = cl.e
		}
		c.mu.Unlock()
	}
	cl.err = err
	c.mu.Lock()
	delete(c.inflight, key)
	c.mu.Unlock()
	cl.wg.Done()
	return cl.e, cl.err
}

func (c *Cache) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	key := c.key(r)
	c.mu.Lock()
	e := c.entries[key]
	c.mu.Unlock()
	now := time.Now()
	status := "MISS"
	switch {
	case e != nil && now.Before(e.freshUntil):
		status = "HIT"
	case e != nil && now.Before(e.staleOK):
		status = "STALE"
		go c.fetch(key, r.Clone(context.Background())) // revalidate in the background
	default:
		var err error
		if e, err = c.fetch(key, r); err != nil {
			http.Error(w, "upstream error", http.StatusBadGateway)
			return
		}
	}
	w.Header().Set("X-Cache", status)
	w.Header().Set("Content-Type", e.header.Get("Content-Type"))
	w.Write(e.body)
}

func get(url string, hdr map[string]string) (int, string, string) {
	req, _ := http.NewRequest(http.MethodGet, url, nil)
	for k, v := range hdr {
		req.Header.Set(k, v)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	b, _ := io.ReadAll(resp.Body)
	return resp.StatusCode, resp.Header.Get("X-Cache"), strings.TrimSpace(string(b))
}

func main() {
	profile, orders, recs := newUpstream("profile", ""), newUpstream("orders", ""), newUpstream("recommend", "")
	for _, u := range []*upstream{profile, orders, recs} {
		u.delay.Store(40)
		defer u.srv.Close()
	}
	mux := http.NewServeMux()
	mux.HandleFunc("GET /bff/home/{user}", aggregate([]part{
		{"profile", profile.srv.URL + "/profile", true},
		{"orders", orders.srv.URL + "/orders", false},
		{"recommend", recs.srv.URL + "/recommend", false},
	}, 100*time.Millisecond))

	catalogue := newUpstream("catalogue", "public, max-age=150, stale-while-revalidate=300")
	defer catalogue.srv.Close()
	secret := newUpstream("account", "private, max-age=150")
	defer secret.srv.Close()
	cache := &Cache{entries: map[string]*entry{}, inflight: map[string]*call{}, upstream: catalogue.srv.URL, varyOn: []string{"Accept-Language"}}
	privCache := &Cache{entries: map[string]*entry{}, inflight: map[string]*call{}, upstream: secret.srv.URL}
	mux.Handle("GET /catalogue/", cache)
	mux.Handle("GET /account/", privCache)
	gw := httptest.NewServer(mux)
	defer gw.Close()

	fmt.Println("== 1. fan-out: three 40 ms calls in parallel ==")
	start := time.Now()
	code, _, body := get(gw.URL+"/bff/home/u1", nil)
	took := time.Since(start)
	fmt.Printf("   %d in %v: %s\n", code, took.Round(time.Millisecond), body[:90]+"...")
	must(code == 200 && took < 110*time.Millisecond, "parallel, not 120 ms sequential")

	fmt.Println("\n== 2. an optional part is slow: degrade, don't fail ==")
	recs.delay.Store(500)
	start = time.Now()
	code, _, body = get(gw.URL+"/bff/home/u1", nil)
	fmt.Printf("   %d in %v: ...%s\n", code, time.Since(start).Round(time.Millisecond), body[len(body)-45:])
	must(code == 200 && strings.Contains(body, `"recommend":null`) && strings.Contains(body, `"degraded":["recommend"]`), "degraded")
	recs.delay.Store(40)

	fmt.Println("\n== 3. the required part is down: fail the whole call ==")
	profile.delay.Store(500)
	code, _, body = get(gw.URL+"/bff/home/u1", nil)
	fmt.Printf("   %d %s\n", code, body)
	must(code == 502, "required part")
	profile.delay.Store(40)

	fmt.Println("\n== 4. caching with Cache-Control + Vary (1 'second' = 1 ms in this lab) ==")
	catalogue.delay.Store(5)
	for i, lang := range []string{"en", "en", "de", "en"} {
		_, xc, b := get(gw.URL+"/catalogue/kettles", map[string]string{"Accept-Language": lang})
		fmt.Printf("   request %d lang=%s -> %-5s %s\n", i+1, lang, xc, b)
	}
	must(catalogue.calls.Load() == 2, "one fetch per language")
	for i := 0; i < 3; i++ {
		get(gw.URL+"/account/me", nil)
	}
	fmt.Printf("   /account/me (Cache-Control: private) x3 -> %d upstream calls: a shared cache must not store it\n", secret.calls.Load())
	must(secret.calls.Load() == 3, "private not cached")

	fmt.Println("\n== 5. stale-while-revalidate: expired, but served instantly ==")
	time.Sleep(160 * time.Millisecond) // past max-age, inside stale window
	catalogue.delay.Store(80)
	start = time.Now()
	_, xc, _ := get(gw.URL+"/catalogue/kettles", map[string]string{"Accept-Language": "en"})
	fmt.Printf("   %s in %v (upstream now takes 80 ms; refresh runs in the background)\n", xc, time.Since(start).Round(time.Millisecond))
	must(xc == "STALE" && time.Since(start) < 60*time.Millisecond, "swr")
	time.Sleep(120 * time.Millisecond)
	_, xc, _ = get(gw.URL+"/catalogue/kettles", map[string]string{"Accept-Language": "en"})
	fmt.Printf("   next request: %s (the background refresh landed)\n", xc)
	must(xc == "HIT", "refreshed")

	fmt.Println("\n== 6. stampede: 100 concurrent misses on a cold key ==")
	before := catalogue.calls.Load()
	var wg sync.WaitGroup
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func() { defer wg.Done(); get(gw.URL+"/catalogue/toasters", map[string]string{"Accept-Language": "en"}) }()
	}
	wg.Wait()
	n := catalogue.calls.Load() - before
	fmt.Printf("   100 clients -> %d upstream call(s) thanks to coalescing\n", n)
	must(n == 1, "singleflight")
	fmt.Println("   (Go's golang.org/x/sync/singleflight is the library version; nginx calls it proxy_cache_lock)")

	fmt.Println("\nOK")
}
