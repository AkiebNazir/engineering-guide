/*
FOUNDATION LEVEL 01 - Routing: many paths, many methods
=========================================================
Level 01 answered every path the same way. A real API looks at the request
and decides what to do - that decision-making is "routing". Go 1.22+'s
http.ServeMux does the routing FOR you if you give it method+path patterns,
but this level does it by hand first, with a plain map, so the mux in level
03 onward is not a black box.

You will learn
  - r.Method is the HTTP verb; r.URL.Path is the path (level 00 reused both blindly)
  - an unmatched path must reply 404 (Not Found), not silently do the wrong thing
  - an unmatched verb on a KNOWN path must reply 405 (Method Not Allowed)

Run it   go run ./REST/Foundation/golang/01_routing_methods_and_paths
*/
package main

import (
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
)

// Two "pages" this tiny server knows about. Everything else is 404.
var routes = map[string]string{
	"/":      "welcome\n",
	"/about": "a foundation-level REST server\n",
}

func handler(w http.ResponseWriter, r *http.Request) {
	body, known := routes[r.URL.Path]

	switch {
	case r.Method == http.MethodGet && known:
		w.Write([]byte(body))
	case r.Method == http.MethodGet && !known:
		http.Error(w, "not found", http.StatusNotFound)
	case r.Method == http.MethodDelete && known:
		// DELETE is only meaningful on a known page in this toy example.
		http.Error(w, "you cannot delete a static page", http.StatusMethodNotAllowed)
	default:
		http.Error(w, "not found", http.StatusNotFound)
	}
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, http.HandlerFunc(handler))
	base := "http://" + ln.Addr().String()

	call := func(method, path string) (int, string) {
		req, _ := http.NewRequest(method, base+path, nil)
		res, err := http.DefaultClient.Do(req)
		if err != nil {
			log.Fatal(err)
		}
		defer res.Body.Close()
		b, _ := io.ReadAll(res.Body)
		return res.StatusCode, string(b)
	}

	s, b := call("GET", "/")
	fmt.Printf("GET /       -> %d %q\n", s, b)
	if s != 200 || b != routes["/"] {
		panic("FAILED")
	}

	s, b = call("GET", "/about")
	fmt.Printf("GET /about  -> %d %q\n", s, b)
	if s != 200 || b != routes["/about"] {
		panic("FAILED")
	}

	s, b = call("GET", "/nope")
	fmt.Printf("GET /nope   -> %d %q   (unknown path -> 404)\n", s, b)
	if s != 404 {
		panic("FAILED")
	}

	s, b = call("DELETE", "/about")
	fmt.Printf("DELETE /about -> %d %q   (known path, wrong verb -> 405)\n", s, b)
	if s != 405 {
		panic("FAILED")
	}
	fmt.Println("OK")
}
