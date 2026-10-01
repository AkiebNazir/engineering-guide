/*
LAB 01 (basic) - A gateway on net/http/httputil.ReverseProxy: routing, Rewrite, errors, streaming
==================================================================================================
Python lab 01 wrote the proxy loop by hand. In Go you almost never do: httputil.ReverseProxy is a
production-grade proxy (Caddy, Traefik and many in-house gateways build on it or on the same
ideas). This lab is about using it CORRECTLY, because its defaults and its older hook are easy
to get wrong.

	client --> gateway :edge --/api/users/*----> users   (prefix stripped: /users/42)
	                          --/api/orders/*---> orders
	                          --/api/events-----> events  (server-sent events, streamed)

You will learn

  - Rewrite (Go 1.20+) vs the legacy Director: with Rewrite, hop-by-hop headers are removed
    BEFORE your hook runs, and X-Forwarded-* are only what you set with pr.SetXForwarded(); with
    Director a client-sent "X-Forwarded-For: 1.2.3.4" survives and upstreams trust a spoofed IP
  - routing with a ServeMux in front of several proxies, and pr.SetURL + path rewriting
  - ErrorHandler: map "connection refused" to 502 and "upstream too slow" to 504, with a JSON
    body, instead of the default empty 502
  - ModifyResponse: strip upstream fingerprints (Server, X-Powered-By), add security headers
  - timeouts on the Transport (ResponseHeaderTimeout) rather than on the whole request, so long
    streams still work, and FlushInterval: -1 so SSE events reach the client immediately

Run it   go run ./Gateway/labs/golang/01_reverse_proxy_with_httputil
*/
package main

import (
	"bufio"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"net/http/httputil"
	"net/url"
	"strings"
	"time"
)

func must(cond bool, msg string) {
	if !cond {
		panic("FAILED: " + msg)
	}
}

// echo is an upstream that reports what it received.
func echo(name string) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Query().Get("sleep") != "" {
			time.Sleep(300 * time.Millisecond)
		}
		w.Header().Set("Server", "Apache/2.4.1 (Unix)")
		w.Header().Set("X-Powered-By", "PHP/5.6")
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{
			"service": name, "path": r.URL.Path, "xff": r.Header.Get("X-Forwarded-For"),
			"xfproto": r.Header.Get("X-Forwarded-Proto"), "connection_hdr": r.Header.Get("X-Secret-Hop"),
		})
	})
}

func sse() http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/event-stream")
		for i := 1; i <= 3; i++ {
			fmt.Fprintf(w, "data: tick %d\n\n", i)
			http.NewResponseController(w).Flush()
			time.Sleep(80 * time.Millisecond)
		}
	})
}

// newProxy builds a correctly configured ReverseProxy for one upstream.
func newProxy(target *url.URL, stripPrefix string) *httputil.ReverseProxy {
	return &httputil.ReverseProxy{
		Rewrite: func(pr *httputil.ProxyRequest) {
			pr.SetURL(target) // scheme + host (+ base path) of the upstream
			pr.Out.URL.Path = "/" + strings.TrimPrefix(strings.TrimPrefix(pr.In.URL.Path, stripPrefix), "/")
			pr.Out.URL.RawPath = ""
			pr.SetXForwarded() // X-Forwarded-For = the real peer only; -Host; -Proto
			pr.Out.Host = target.Host
		},
		Transport: &http.Transport{
			DialContext:           (&net.Dialer{Timeout: 500 * time.Millisecond}).DialContext,
			ResponseHeaderTimeout: 150 * time.Millisecond, // time to FIRST byte, not a cap on streams
			MaxIdleConnsPerHost:   64,                     // default is 2: a busy gateway needs more
		},
		FlushInterval: -1, // flush every write: required for SSE / streaming responses
		ModifyResponse: func(resp *http.Response) error {
			resp.Header.Del("Server")
			resp.Header.Del("X-Powered-By")
			resp.Header.Set("X-Content-Type-Options", "nosniff")
			return nil
		},
		ErrorHandler: func(w http.ResponseWriter, r *http.Request, err error) {
			status, code := http.StatusBadGateway, "upstream_unavailable"
			var ne net.Error
			if errors.As(err, &ne) && ne.Timeout() || errors.Is(err, context.DeadlineExceeded) {
				status, code = http.StatusGatewayTimeout, "upstream_timeout"
			}
			w.Header().Set("Content-Type", "application/problem+json")
			w.WriteHeader(status)
			json.NewEncoder(w).Encode(map[string]any{"status": status, "code": code})
		},
	}
}

// legacyDirectorProxy is what many older tutorials show. Kept to demonstrate the spoofing problem.
func legacyDirectorProxy(target *url.URL) *httputil.ReverseProxy {
	return &httputil.ReverseProxy{Director: func(r *http.Request) {
		r.URL.Scheme, r.URL.Host = target.Scheme, target.Host
		// ReverseProxy then APPENDS the peer IP to whatever X-Forwarded-For the client sent
	}}
}

func get(u string, hdr map[string]string) (int, http.Header, map[string]string) {
	req, _ := http.NewRequest(http.MethodGet, u, nil)
	for k, v := range hdr {
		req.Header.Set(k, v)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	var body map[string]string
	json.NewDecoder(resp.Body).Decode(&body)
	return resp.StatusCode, resp.Header, body
}

func main() {
	users := httptest.NewServer(echo("users"))
	defer users.Close()
	orders := httptest.NewServer(echo("orders"))
	defer orders.Close()
	events := httptest.NewServer(sse())
	defer events.Close()
	dead := httptest.NewServer(echo("dead"))
	deadURL, _ := url.Parse(dead.URL)
	dead.Close() // nothing listens there any more

	u, _ := url.Parse(users.URL)
	o, _ := url.Parse(orders.URL)
	e, _ := url.Parse(events.URL)
	mux := http.NewServeMux()
	mux.Handle("/api/users/", newProxy(u, "/api"))
	mux.Handle("/api/orders/", newProxy(o, "/api"))
	mux.Handle("GET /api/events", newProxy(e, "/api"))
	mux.Handle("/api/billing/", newProxy(deadURL, "/api"))
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/problem+json")
		w.WriteHeader(http.StatusNotFound)
		io.WriteString(w, `{"status":404,"code":"no_route"}`)
	})
	gw := httptest.NewServer(mux)
	defer gw.Close()

	fmt.Println("== 1. routing + prefix stripping ==")
	for _, p := range []string{"/api/users/42", "/api/orders/7/items", "/api/nothing"} {
		status, _, body := get(gw.URL+p, nil)
		fmt.Printf("   %-22s -> %d %s %s\n", p, status, body["service"], body["path"])
	}
	_, _, b := get(gw.URL+"/api/users/42", nil)
	must(b["service"] == "users" && b["path"] == "/users/42", "routed and stripped")

	fmt.Println("\n== 2. header hygiene: Rewrite vs legacy Director ==")
	spoof := map[string]string{"X-Forwarded-For": "6.6.6.6", "Connection": "X-Secret-Hop", "X-Secret-Hop": "leak"}
	_, hdr, b := get(gw.URL+"/api/users/1", spoof)
	fmt.Printf("   Rewrite : upstream saw X-Forwarded-For=%q proto=%q, hop header=%q\n", b["xff"], b["xfproto"], b["connection_hdr"])
	must(b["xff"] == "127.0.0.1" && b["connection_hdr"] == "", "spoofed XFF replaced, hop-by-hop removed")
	legacy := httptest.NewServer(legacyDirectorProxy(u))
	defer legacy.Close()
	_, _, lb := get(legacy.URL+"/users/1", spoof)
	fmt.Printf("   Director: upstream saw X-Forwarded-For=%q  <- the client's fake IP comes first\n", lb["xff"])
	must(strings.HasPrefix(lb["xff"], "6.6.6.6"), "director keeps the spoofed value")
	fmt.Printf("   response headers: Server=%q X-Powered-By=%q X-Content-Type-Options=%q\n",
		hdr.Get("Server"), hdr.Get("X-Powered-By"), hdr.Get("X-Content-Type-Options"))
	must(hdr.Get("Server") == "" && hdr.Get("X-Content-Type-Options") == "nosniff", "ModifyResponse")

	fmt.Println("\n== 3. failures become clear status codes ==")
	s1, _, b1 := get(gw.URL+"/api/billing/1", nil)
	s2, _, b2 := get(gw.URL+"/api/orders/1?sleep=1", nil)
	fmt.Printf("   upstream down -> %d %s;  upstream slower than 150 ms -> %d %s\n", s1, b1["code"], s2, b2["code"])
	must(s1 == 502 && s2 == 504, "502 vs 504")

	fmt.Println("\n== 4. streaming: SSE events arrive one by one ==")
	resp, err := http.Get(gw.URL + "/api/events")
	must(err == nil, "sse request")
	start := time.Now()
	sc := bufio.NewScanner(resp.Body)
	var arrivals []time.Duration
	for sc.Scan() {
		if strings.HasPrefix(sc.Text(), "data:") {
			arrivals = append(arrivals, time.Since(start).Round(10*time.Millisecond))
			fmt.Printf("   %-12s at +%v\n", sc.Text(), arrivals[len(arrivals)-1])
		}
	}
	resp.Body.Close()
	must(len(arrivals) == 3 && arrivals[0] < 60*time.Millisecond, "first event not buffered")
	took := time.Since(start).Round(10 * time.Millisecond)
	must(took > 150*time.Millisecond, "stream outlived ResponseHeaderTimeout")
	fmt.Printf("   the whole stream took %v, longer than ResponseHeaderTimeout: that timeout only\n", took)
	fmt.Println("   bounds the wait for response HEADERS, which is exactly what a streaming gateway needs.")

	fmt.Println("\nOK")
}
