/*
LAB 04 (advanced) - Sending webhooks safely: defeating SSRF (Server-Side Request Forgery)
=========================================================================================
The moment your product lets customers register a URL, YOUR SERVERS make requests to addresses
CUSTOMERS choose. A malicious customer registers:

	http://169.254.169.254/latest/meta-data/iam/security-credentials/     <- cloud credentials!
	http://localhost:6379/                                               <- your Redis
	http://10.0.3.7:8500/v1/kv/                                          <- an internal admin API

...and your "webhook delivery" happily fetches them from inside your network (and may even show
the response body in the dashboard). This is SSRF, and it has caused major breaches.

You will learn
  - why validating the URL/hostname up front is NOT enough:
  - DNS REBINDING: a name resolves to a public IP during your check and to 127.0.0.1 when
    the HTTP client connects a moment later
  - numeric tricks: 2130706433, 0x7f000001, 127.1, IPv6 ::1, ::ffff:127.0.0.1
  - REDIRECTS: a public URL answers 302 -> http://127.0.0.1/secret
  - THE fix: check the IP address at CONNECT time, inside net.Dialer.Control. That callback receives
    the address the socket is really about to connect to - after DNS, after every trick - and can veto it.
  - defence in depth: refuse redirects, https-only in production, bounded response, tight timeouts,
    ignore proxy environment variables (a proxy would connect on your behalf and bypass the check),
    and never echo response bodies back to the customer

Run it   go run ./Webhooks/labs/golang/04_ssrf_safe_sender
*/
package main

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"net/netip"
	"strings"
	"sync/atomic"
	"syscall"
	"time"
)

// ------------------------------------------------------- what counts as internal ---
var extraBlocked = []netip.Prefix{
	netip.MustParsePrefix("100.64.0.0/10"),  // carrier-grade NAT (also Alibaba metadata 100.100.100.200)
	netip.MustParsePrefix("192.0.0.0/24"),   // IETF protocol assignments
	netip.MustParsePrefix("198.18.0.0/15"),  // benchmarking
	netip.MustParsePrefix("169.254.0.0/16"), // link-local: cloud metadata services live here
	netip.MustParsePrefix("fd00:ec2::/32"),  // AWS IPv6 metadata endpoint
}

func isBlocked(ip netip.Addr) bool {
	ip = ip.Unmap() // ::ffff:127.0.0.1 is really 127.0.0.1
	if ip.IsLoopback() || ip.IsPrivate() || ip.IsLinkLocalUnicast() || ip.IsLinkLocalMulticast() ||
		ip.IsUnspecified() || ip.IsMulticast() || ip.IsInterfaceLocalMulticast() {
		return true
	}
	for _, p := range extraBlocked {
		if p.Contains(ip) {
			return true
		}
	}
	return false
}

var ErrBlocked = errors.New("destination address is not allowed")

// safeDialer vetoes connections to internal addresses AT CONNECT TIME.
// allow is a test hook standing in for "this one address is a legitimate public host".
func safeDialer(allow func(addrPort string) bool, blockedCount *atomic.Int64) *net.Dialer {
	return &net.Dialer{
		Timeout: 3 * time.Second,
		Control: func(network, address string, _ syscall.RawConn) error {
			// `address` is "ip:port": the REAL destination, after DNS resolution.
			if allow != nil && allow(address) {
				return nil
			}
			ap, err := netip.ParseAddrPort(address)
			if err != nil || isBlocked(ap.Addr()) {
				blockedCount.Add(1)
				return fmt.Errorf("%w: %s", ErrBlocked, address)
			}
			return nil
		},
	}
}

// NewSafeClient is the client to use for every customer-supplied URL.
func NewSafeClient(dial func(ctx context.Context, network, addr string) (net.Conn, error)) *http.Client {
	return &http.Client{
		Timeout: 5 * time.Second,
		Transport: &http.Transport{
			Proxy:               nil, // ignore HTTP(S)_PROXY: a proxy would connect for us and bypass the dial check
			DialContext:         dial,
			TLSHandshakeTimeout: 3 * time.Second,
			DisableKeepAlives:   true,
		},
		CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }, // NEVER follow
	}
}

// validateURL is a cheap first filter for good error messages. It is NOT the security boundary.
func validateURL(raw string, allowHTTP bool) error {
	req, err := http.NewRequest("POST", raw, nil)
	if err != nil {
		return err
	}
	if req.URL.User != nil {
		return errors.New("credentials in URL are not allowed")
	}
	if req.URL.Scheme != "https" && !(allowHTTP && req.URL.Scheme == "http") {
		return errors.New("only https URLs are allowed")
	}
	if req.URL.Hostname() == "" {
		return errors.New("missing host")
	}
	return nil
}

func fetch(client *http.Client, url string) (string, error) {
	res, err := client.Post(url, "application/json", strings.NewReader("{}"))
	if err != nil {
		return "", err
	}
	defer res.Body.Close()
	b, _ := io.ReadAll(io.LimitReader(res.Body, 4096)) // bounded read
	return fmt.Sprintf("%d %s", res.StatusCode, strings.TrimSpace(string(b))), nil
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	// The "internal service" nobody outside should reach: cloud metadata, admin API, Redis...
	var internalHits atomic.Int64
	internal := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		internalHits.Add(1)
		fmt.Fprint(w, "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG")
	}))
	defer internal.Close()
	internalAddr := internal.Listener.Addr().String()
	_, internalPort, _ := net.SplitHostPort(internalAddr)

	// An attacker-controlled "public" server that redirects into our network.
	attacker := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.Redirect(w, r, "http://"+internalAddr+"/latest/meta-data/", http.StatusFound)
	}))
	defer attacker.Close()
	attackerAddr := attacker.Listener.Addr().String()

	var blocked atomic.Int64
	// Test hook: pretend the attacker's listener is a legitimate PUBLIC host (in the real world it would be).
	safe := NewSafeClient(safeDialer(func(a string) bool { return a == attackerAddr }, &blocked).DialContext)

	fmt.Println("== 1. the vulnerability: a naive sender reaches internal services ==")
	naive := &http.Client{Timeout: 3 * time.Second}
	out, err := fetch(naive, "http://"+internalAddr+"/")
	fmt.Printf("  naive client -> %s (err=%v)\n", out, err)
	must(strings.Contains(out, "AWS_SECRET"), "the naive client leaks the secret")
	before := internalHits.Load()

	fmt.Println("\n== 2. the safe client refuses every internal destination ==")
	targets := []string{
		"http://" + internalAddr + "/",                    // loopback
		"http://localhost:" + internalPort + "/",          // a NAME that resolves to loopback
		"http://[::1]:" + internalPort + "/",              // IPv6 loopback
		"http://[::ffff:127.0.0.1]:" + internalPort + "/", // IPv4-mapped IPv6
		"http://127.1:" + internalPort + "/",              // short form
		"http://2130706433:" + internalPort + "/",         // 127.0.0.1 as one decimal number
		"http://0x7f000001:" + internalPort + "/",         // ... in hex
		"http://0:" + internalPort + "/",                  // 0.0.0.0 = "this host" on Linux
		"http://10.0.3.7:8500/v1/kv/",                     // RFC 1918 private
		"http://192.168.1.1/",
		"http://172.16.5.5/",
		"http://169.254.169.254/latest/meta-data/", // AWS/GCP/Azure metadata
		"http://100.100.100.200/latest/meta-data/", // Alibaba metadata (CGNAT range)
		"http://[fe80::1]/",                        // IPv6 link-local
	}
	for _, t := range targets {
		_, err := fetch(safe, t)
		verdict := "REFUSED"
		if err == nil {
			verdict = "!!! REACHED !!!"
		} else if !errors.Is(err, ErrBlocked) {
			verdict = "failed (not resolvable/parsable): " + shorten(err.Error())
		}
		fmt.Printf("  %-46s %s\n", t, verdict)
		must(err != nil, t+" must not succeed")
	}
	must(internalHits.Load() == before, "the internal service must not have received ANY request")
	fmt.Printf("  the internal service saw %d new requests; the dial guard vetoed %d connection attempts\n", internalHits.Load()-before, blocked.Load())

	fmt.Println("\n== 3. the redirect attack ==")
	fmt.Println("  attacker's public URL answers 302 -> http://<internal>/latest/meta-data/")
	out, err = fetch(naive, "http://"+attackerAddr+"/")
	fmt.Printf("  naive client follows the redirect and leaks: %s\n", out)
	must(strings.Contains(out, "AWS_SECRET"), "naive client follows redirect")
	out, err = fetch(safe, "http://"+attackerAddr+"/")
	fmt.Printf("  safe client (redirects off)                 : %s (err=%v)\n", out, err)
	must(err == nil && strings.HasPrefix(out, "302"), "safe client reports the 302 and stops")
	must(!strings.Contains(out, "AWS_SECRET"), "no leak")

	fmt.Println("\n== 4. DNS rebinding: check-then-connect is broken, connect-time checking is not ==")
	lookups := atomic.Int64{}
	rebind := func(host string) string { // an attacker-run DNS server: public on the 1st answer, loopback afterwards
		if lookups.Add(1) == 1 {
			return "203.0.113.9" // TEST-NET-3: looks public
		}
		return "127.0.0.1"
	}
	// naive design: resolve + validate first, then let the HTTP client connect (which resolves AGAIN)
	firstAnswer := rebind("rebind.attacker.test")
	ap, _ := netip.ParseAddr(firstAnswer)
	fmt.Printf("  validation lookup: rebind.attacker.test -> %s  (blocked? %v)  => the URL is approved\n", firstAnswer, isBlocked(ap))
	must(!isBlocked(ap), "the pre-check is fooled")
	plain := &net.Dialer{Timeout: 3 * time.Second}
	naiveRebind := &http.Client{Timeout: 3 * time.Second, Transport: &http.Transport{
		DialContext: func(ctx context.Context, network, addr string) (net.Conn, error) {
			_, port, _ := net.SplitHostPort(addr)
			return plain.DialContext(ctx, network, net.JoinHostPort(rebind("rebind.attacker.test"), port)) // 2nd lookup: 127.0.0.1
		}}}
	out, err = fetch(naiveRebind, "http://rebind.attacker.test:"+internalPort+"/")
	fmt.Printf("  connect-time lookup returned 127.0.0.1 -> naive client got: %s\n", out)
	must(strings.Contains(out, "AWS_SECRET"), "rebinding defeats check-then-connect")

	lookups.Store(1) // the attacker's DNS now answers 127.0.0.1 every time
	guarded := safeDialer(nil, &blocked)
	safeRebind := NewSafeClient(func(ctx context.Context, network, addr string) (net.Conn, error) {
		_, port, _ := net.SplitHostPort(addr)
		return guarded.DialContext(ctx, network, net.JoinHostPort(rebind("rebind.attacker.test"), port))
	})
	_, err = fetch(safeRebind, "http://rebind.attacker.test:"+internalPort+"/")
	fmt.Printf("  same attack against the Control-guarded dialer -> %v\n", shorten(fmt.Sprint(err)))
	must(errors.Is(err, ErrBlocked), "connect-time guard stops rebinding")

	fmt.Println("\n== 5. cheap URL pre-validation (good error messages, NOT the security boundary) ==")
	for _, u := range []string{"https://hooks.example.com/x", "http://hooks.example.com/x", "https://user:pw@hooks.example.com/", "ftp://x/"} {
		fmt.Printf("  %-40s -> %v\n", u, validateURL(u, false))
	}

	fmt.Println("\nChecklist: guard in Dialer.Control | no proxy | no redirects | https only | timeouts | bounded body |")
	fmt.Println("           never show response bodies to the customer | send from a network segment with egress rules")
	fmt.Println("\nOK")
}

func shorten(s string) string {
	if len(s) > 90 {
		return s[:90] + "..."
	}
	return s
}
