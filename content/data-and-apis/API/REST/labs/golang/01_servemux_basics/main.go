/*
LAB 01 (basic) - net/http ServeMux: routing with methods and wildcards (Go 1.22+)
==================================================================================
You will learn
  - the smallest Go web server: a Handler is anything with ServeHTTP(w, r)
  - patterns that include the METHOD:        "GET /users/{id}"
  - path wildcards read with r.PathValue:    {id}   {path...}   and the exact-match {$}
  - free behaviour from the mux: automatic 405 + Allow header, HEAD for GET, trailing slash rules
  - "most specific pattern wins" - and that ambiguous patterns panic at startup (good!)
  - r.Pattern (Go 1.23): which route matched, handy for logging and metrics labels

Run it         go run ./REST/labs/golang/01_servemux_basics          (demo, then exits)
Keep serving   go run ./REST/labs/golang/01_servemux_basics -serve   (curl -i localhost:8080/users/7)
*/
package main

import (
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
)

func newMux() *http.ServeMux {
	mux := http.NewServeMux()

	// "{$}" = the root and nothing else. Plain "/" would match EVERY unmatched path.
	mux.HandleFunc("GET /{$}", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintln(w, "welcome")
	})

	// {id} matches exactly one path segment.
	mux.HandleFunc("GET /users/{id}", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "user %s (matched by %q)\n", r.PathValue("id"), r.Pattern)
	})

	// A more specific pattern beats a more general one, regardless of registration order.
	mux.HandleFunc("GET /users/me", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintln(w, "the current user")
	})

	// Different method, same path: allowed.
	mux.HandleFunc("DELETE /users/{id}", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNoContent)
	})

	// {path...} swallows the rest of the URL, slashes included.
	mux.HandleFunc("GET /files/{path...}", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "file at %q\n", r.PathValue("path"))
	})

	// Query string is separate from the path: /search?q=go&limit=5
	mux.HandleFunc("GET /search", func(w http.ResponseWriter, r *http.Request) {
		q := r.URL.Query()
		fmt.Fprintf(w, "q=%q limit=%q\n", q.Get("q"), q.Get("limit"))
	})

	// Host-specific patterns are supported too: mux.HandleFunc("GET api.example.com/v1/ping", ...)
	return mux
}

func main() {
	serve := flag.Bool("serve", false, "keep serving on :8080 instead of running the demo")
	flag.Parse()
	mux := newMux()

	if *serve {
		log.Println("listening on http://localhost:8080")
		log.Fatal(http.ListenAndServe("127.0.0.1:8080", mux))
	}

	ln, err := net.Listen("tcp", "127.0.0.1:0") // port 0 = any free port
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, mux)
	base := "http://" + ln.Addr().String()

	show := func(method, path string) {
		req, _ := http.NewRequest(method, base+path, nil)
		res, err := http.DefaultClient.Do(req)
		if err != nil {
			log.Fatal(err)
		}
		defer res.Body.Close()
		body, _ := io.ReadAll(res.Body)
		allow := ""
		if a := res.Header.Get("Allow"); a != "" {
			allow = "  Allow: " + a
		}
		fmt.Printf("%-6s %-22s -> %d  %q%s\n", method, path, res.StatusCode, string(body), allow)
	}

	show("GET", "/")
	show("GET", "/users/7")
	show("GET", "/users/me")              // the specific route wins over /users/{id}
	show("GET", "/files/docs/2026/a.pdf") // {path...} keeps the slashes
	show("GET", "/search?q=go&limit=5")
	show("DELETE", "/users/7")
	show("POST", "/users/7")      // path exists but not for POST -> 405 + Allow
	show("GET", "/nope")          // nothing matches -> 404
	show("GET", "/users/7/extra") // {id} is ONE segment -> 404

	// Conflicting patterns are rejected when the server starts, not at 3 a.m. in production.
	conflict := func() (panicked bool) {
		defer func() { panicked = recover() != nil }()
		m := http.NewServeMux()
		m.HandleFunc("GET /a/{x}/b", func(http.ResponseWriter, *http.Request) {})
		m.HandleFunc("GET /a/b/{y}", func(http.ResponseWriter, *http.Request) {}) // both match /a/b/b
		return false
	}()
	fmt.Println("conflict detected at registration:", conflict)
	if !conflict {
		panic("FAILED: ambiguous patterns must be rejected")
	}
	fmt.Println("OK")
}
