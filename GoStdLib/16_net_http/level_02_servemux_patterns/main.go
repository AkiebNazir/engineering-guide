/*
LEVEL 02 (core API) - routing with ServeMux patterns (Go 1.22+)

You will learn
  - since Go 1.22 the standard http.ServeMux understands methods and path
    wildcards: "GET /items/{id}" matches only GET (and HEAD), and
    r.PathValue("id") returns the segment - no third-party router needed
    for most services
  - "{path...}" matches the rest of the path; a pattern ending in "/"
    matches the whole subtree; "{$}" matches only the exact path
  - the most specific pattern wins regardless of registration order, and
    registering two patterns that conflict panics at startup
  - a path that matches but with the wrong method gets 405 Method Not
    Allowed with an Allow header, automatically

Run: go run ./GoStdLib/16_net_http/level_02_servemux_patterns
*/

package main

import (
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
)

func newMux() *http.ServeMux {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /{$}", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprint(w, "home")
	})
	mux.HandleFunc("GET /items/{id}", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "item %s", r.PathValue("id"))
	})
	// More specific than /items/{id}, so it wins for this one path.
	mux.HandleFunc("GET /items/latest", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprint(w, "the latest item")
	})
	mux.HandleFunc("POST /items", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Location", "/items/42")
		w.WriteHeader(http.StatusCreated)
	})
	mux.HandleFunc("GET /files/{path...}", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "file %s", r.PathValue("path"))
	})
	return mux
}

type check struct {
	method, path string
	wantStatus   int
	wantBody     string
}

func main() {
	srv := httptest.NewServer(newMux())
	defer srv.Close()

	checks := []check{
		{"GET", "/", 200, "home"},
		{"GET", "/nope", 404, "404 page not found\n"},
		{"GET", "/items/7", 200, "item 7"},
		{"GET", "/items/latest", 200, "the latest item"},
		{"HEAD", "/items/7", 200, ""}, // GET patterns also serve HEAD, without a body
		{"DELETE", "/items/7", 405, "Method Not Allowed\n"},
		{"POST", "/items", 201, ""},
		{"GET", "/files/css/site/main.css", 200, "file css/site/main.css"},
	}
	for _, c := range checks {
		req, err := http.NewRequest(c.method, srv.URL+c.path, nil)
		if err != nil {
			panic(err)
		}
		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			panic(err)
		}
		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		extra := ""
		if allow := resp.Header.Get("Allow"); allow != "" {
			extra = " Allow=" + allow
		}
		if loc := resp.Header.Get("Location"); loc != "" {
			extra = " Location=" + loc
		}
		fmt.Printf("%-6s %-26s -> %d %q%s\n", c.method, c.path, resp.StatusCode, body, extra)
		if resp.StatusCode != c.wantStatus || string(body) != c.wantBody {
			panic(fmt.Sprintf("%s %s: want %d %q, got %d %q", c.method, c.path, c.wantStatus, c.wantBody, resp.StatusCode, body))
		}
	}

	// Conflicting registrations are caught at startup, not at request time.
	func() {
		defer func() {
			r := recover()
			if r == nil || !strings.Contains(fmt.Sprint(r), "conflicts with") {
				panic(fmt.Sprintf("expected a conflict panic, got %v", r))
			}
			fmt.Println("conflicting patterns rejected at registration:", strings.SplitN(fmt.Sprint(r), "\n", 2)[0])
		}()
		m := http.NewServeMux()
		m.HandleFunc("GET /a/{x}", func(http.ResponseWriter, *http.Request) {})
		m.HandleFunc("GET /a/{y}", func(http.ResponseWriter, *http.Request) {})
	}()
	fmt.Println("OK")
}
