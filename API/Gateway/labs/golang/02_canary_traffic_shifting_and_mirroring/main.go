/*
LAB 02 (advanced) - Progressive delivery at the gateway: canary weights, sticky users, mirroring, auto-rollback
===============================================================================================================
A gateway does not only route by PATH; it routes by WHO and HOW MUCH. That makes it the place
where new versions meet real traffic safely, which is what Argo Rollouts, Flagger, Envoy's
weighted_clusters / request_mirror_policies and Kong's canary plugin automate.

	                      +--95%--> orders v1 (stable)
	client --> gateway ---+
	                      +---5%--> orders v2 (canary)       + a COPY of v1 traffic --> v3 (shadow, response discarded)

You will learn

  - WEIGHTED routing, and why it must be STICKY: hash(user id) into 0..9999 buckets, not a coin
    flip per request, or one user bounces between versions (and between UI versions) mid-session
  - an OVERRIDE header (x-canary: always / never) so testers and the rollout controller can pin
    a version, and why it must be stripped from outside traffic unless authenticated
  - TRAFFIC MIRRORING (shadowing): send a copy of each request to a new version asynchronously,
    compare, never let its latency or errors reach the client, and only for SAFE methods
  - an automatic ROLLBACK loop: compare the canary's error rate with the stable one over a
    window; if worse by a margin (with a minimum sample size), set the weight to 0

Run it   go run ./Gateway/labs/golang/02_canary_traffic_shifting_and_mirroring
*/
package main

import (
	"fmt"
	"hash/fnv"
	"io"
	"net/http"
	"net/http/httptest"
	"net/http/httputil"
	"net/url"
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

// ================================================================ upstream versions ===
type version struct {
	name     string
	failRate atomic.Int64 // per 1000
	seen     atomic.Int64
	srv      *httptest.Server
}

func newVersion(name string, delay time.Duration) *version {
	v := &version{name: name}
	var n atomic.Int64
	v.srv = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		v.seen.Add(1)
		time.Sleep(delay)
		if k := n.Add(1); (k*7919)%1000 < v.failRate.Load() { // spread failures evenly over requests
			http.Error(w, "boom", http.StatusInternalServerError)
			return
		}
		w.Header().Set("X-Version", name)
		io.WriteString(w, name)
	}))
	return v
}

// ================================================================= the gateway ===
type stats struct{ total, errors atomic.Int64 }

type Gateway struct {
	stable, canary *httputil.ReverseProxy
	weight         atomic.Int64 // canary share in basis points (0..10000)
	mirrorTo       string       // "" = no mirroring
	mirrored       atomic.Int64
	st             map[string]*stats
	mu             sync.Mutex
	trustedTesters map[string]bool
}

func proxyTo(raw string) *httputil.ReverseProxy {
	u, _ := url.Parse(raw)
	return &httputil.ReverseProxy{Rewrite: func(pr *httputil.ProxyRequest) { pr.SetURL(u); pr.SetXForwarded() }}
}

func bucket(userID string) int64 {
	h := fnv.New32a()
	h.Write([]byte("orders-rollout-7:" + userID)) // salt per rollout, so the SAME users are not always first
	return int64(h.Sum32() % 10000)
}

func (g *Gateway) pick(r *http.Request) string {
	override := r.Header.Get("X-Canary")
	if override != "" && !g.trustedTesters[r.Header.Get("X-User")] {
		override = "" // outside callers may not choose their version
	}
	switch override {
	case "always":
		return "canary"
	case "never":
		return "stable"
	}
	user := r.Header.Get("X-User")
	if user == "" { // anonymous: fall back to a cookie/ip in real life; here, stable
		return "stable"
	}
	if bucket(user) < g.weight.Load() {
		return "canary"
	}
	return "stable"
}

func (g *Gateway) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	target := g.pick(r)
	r.Header.Del("X-Canary")
	if g.mirrorTo != "" && (r.Method == http.MethodGet || r.Method == http.MethodHead) {
		shadow, _ := http.NewRequest(r.Method, g.mirrorTo+r.URL.RequestURI(), nil)
		shadow.Header = r.Header.Clone()
		shadow.Header.Set("X-Shadow", "true") // so the shadow can skip side effects (emails, charges)
		go func() {                           // fire and forget: never on the client's critical path
			if resp, err := (&http.Client{Timeout: time.Second}).Do(shadow); err == nil {
				io.Copy(io.Discard, resp.Body)
				resp.Body.Close()
				g.mirrored.Add(1)
			}
		}()
	}
	rec := &codeRecorder{ResponseWriter: w, code: 200}
	if target == "canary" {
		g.canary.ServeHTTP(rec, r)
	} else {
		g.stable.ServeHTTP(rec, r)
	}
	g.st[target].total.Add(1)
	if rec.code >= 500 {
		g.st[target].errors.Add(1)
	}
}

type codeRecorder struct {
	http.ResponseWriter
	code int
}

func (c *codeRecorder) WriteHeader(code int) { c.code = code; c.ResponseWriter.WriteHeader(code) }

// analyse is one tick of a rollout controller (what Flagger / Argo Rollouts run every interval).
func (g *Gateway) analyse(minRequests int64, maxExtraErrorRate float64) string {
	c, s := g.st["canary"], g.st["stable"]
	if c.total.Load() < minRequests {
		return fmt.Sprintf("wait: only %d canary requests (need %d)", c.total.Load(), minRequests)
	}
	cr := float64(c.errors.Load()) / float64(c.total.Load())
	sr := float64(s.errors.Load()) / float64(max(1, s.total.Load()))
	if cr > sr+maxExtraErrorRate {
		g.weight.Store(0)
		return fmt.Sprintf("ROLLBACK: canary errors %.1f%% vs stable %.1f%% -> weight 0", 100*cr, 100*sr)
	}
	return fmt.Sprintf("healthy: canary %.1f%% vs stable %.1f%% errors", 100*cr, 100*sr)
}

func call(gw, user string, hdr map[string]string) (string, int) {
	req, _ := http.NewRequest(http.MethodGet, gw+"/orders", nil)
	if user != "" {
		req.Header.Set("X-User", user)
	}
	for k, v := range hdr {
		req.Header.Set(k, v)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	b, _ := io.ReadAll(resp.Body)
	return strings.TrimSpace(string(b)), resp.StatusCode
}

func main() {
	v1, v2, v3 := newVersion("v1", 0), newVersion("v2", 0), newVersion("v3-shadow", 200*time.Millisecond)
	for _, v := range []*version{v1, v2, v3} {
		defer v.srv.Close()
	}
	g := &Gateway{stable: proxyTo(v1.srv.URL), canary: proxyTo(v2.srv.URL),
		st: map[string]*stats{"stable": {}, "canary": {}}, trustedTesters: map[string]bool{"qa-anna": true}}
	g.weight.Store(500) // 5%
	gw := httptest.NewServer(g)
	defer gw.Close()

	fmt.Println("== 1. 5% canary, sticky per user ==")
	users := make([]string, 2000)
	canaryUsers := 0
	for i := range users {
		users[i] = fmt.Sprintf("user-%d", i)
		if got, _ := call(gw.URL, users[i], nil); got == "v2" {
			canaryUsers++
		}
	}
	flips := 0
	for _, u := range users[:200] { // the same users again: nobody may change version
		first, _ := call(gw.URL, u, nil)
		again, _ := call(gw.URL, u, nil)
		if first != again {
			flips++
		}
	}
	fmt.Printf("   %d of 2000 users (%.1f%%) on v2; version flips for returning users: %d\n",
		canaryUsers, 100*float64(canaryUsers)/2000, flips)
	must(canaryUsers > 60 && canaryUsers < 140 && flips == 0, "about 5%, and sticky")

	fmt.Println("\n== 2. widen to 25%: users already on v2 stay on v2 ==")
	onV2 := []string{}
	for _, u := range users {
		if bucket(u) < 500 {
			onV2 = append(onV2, u)
		}
	}
	g.weight.Store(2500)
	stillV2 := 0
	for _, u := range onV2 {
		if got, _ := call(gw.URL, u, nil); got == "v2" {
			stillV2++
		}
	}
	fmt.Printf("   %d of %d early canary users still on v2 (bucket < 500 is also < 2500)\n", stillV2, len(onV2))
	must(stillV2 == len(onV2), "monotonic rollout")

	fmt.Println("\n== 3. override header: only for trusted testers ==")
	a, _ := call(gw.URL, "qa-anna", map[string]string{"X-Canary": "always"})
	m, _ := call(gw.URL, "user-3", map[string]string{"X-Canary": "always"})
	fmt.Printf("   qa-anna + x-canary:always -> %s;  random user + x-canary:always -> %s (header ignored)\n", a, m)
	must(a == "v2" && m == "v1", "override gated")

	fmt.Println("\n== 4. mirroring GETs to v3 (slow: 200 ms) without slowing clients ==")
	g.mirrorTo = v3.srv.URL
	start := time.Now()
	for i := 0; i < 20; i++ {
		call(gw.URL, users[i], map[string]string{"X-Canary": "never"})
	}
	took := time.Since(start)
	time.Sleep(300 * time.Millisecond)
	fmt.Printf("   20 client requests took %v in total; v3 received %d shadow copies\n", took.Round(time.Millisecond), v3.seen.Load())
	must(took < 200*time.Millisecond && v3.seen.Load() == 20, "shadow is off the critical path")
	g.mirrorTo = ""

	fmt.Println("\n== 5. automatic rollback: v2 starts failing 8% of requests ==")
	g.st = map[string]*stats{"stable": {}, "canary": {}}
	v2.failRate.Store(80)
	v1.failRate.Store(5)
	fmt.Println("   " + g.analyse(100, 0.02))
	for _, u := range users {
		call(gw.URL, u, nil)
	}
	verdict := g.analyse(100, 0.02)
	fmt.Println("   " + verdict)
	must(strings.HasPrefix(verdict, "ROLLBACK") && g.weight.Load() == 0, "rolled back")
	after := 0
	for _, u := range onV2 {
		if got, _ := call(gw.URL, u, nil); got == "v2" {
			after++
		}
	}
	fmt.Printf("   after rollback: %d users on v2\n", after)
	must(after == 0, "everyone back on stable")

	fmt.Println("\nOK")
}
