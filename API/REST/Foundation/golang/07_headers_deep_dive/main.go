/*
FOUNDATION LEVEL 07 - Headers: metadata about the message, not the message itself
====================================================================================
Every level so far used one or two headers without dwelling on them. Headers
are just more "key: value" text lines, the same shape as the request line itself - anyone
can add their own. This level uses them on purpose: content negotiation, a
custom application header, and conditional requests via ETag (a cheap
fingerprint).

You will learn
  - r.Header.Get("X") reads any request header, case-insensitively
  - a server can offer more than one representation and pick by Accept
  - custom headers (commonly prefixed like X-Request-Id) travel like any other
  - ETag + If-None-Match is how a client says "only send it if it changed" -> 304

Run it   go run ./REST/Foundation/golang/07_headers_deep_dive
*/
package main

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"strings"
)

const articleText = "REST uses headers for everything HTTP itself needs to say."

func etag() string {
	sum := sha256.Sum256([]byte(articleText))
	return fmt.Sprintf("%x", sum)[:16]
}

func handler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/article" {
		w.WriteHeader(http.StatusNotFound)
		return
	}

	tag := etag()
	if r.Header.Get("If-None-Match") == tag {
		// The client already has this exact version - tell it so, send NOTHING back.
		w.Header().Set("ETag", tag)
		w.WriteHeader(http.StatusNotModified)
		return
	}

	requestID := r.Header.Get("X-Request-Id")
	if requestID == "" {
		requestID = "none"
	}
	w.Header().Set("ETag", tag)
	w.Header().Set("X-Echo-Request-Id", requestID) // a custom response header

	if strings.Contains(r.Header.Get("Accept"), "application/json") {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{"text": articleText})
		return
	}
	w.Header().Set("Content-Type", "text/plain")
	fmt.Fprint(w, articleText)
}

func get(base, path string, headers map[string]string) (int, http.Header, string) {
	req, _ := http.NewRequest("GET", base+path, nil)
	for k, v := range headers {
		req.Header.Set(k, v)
	}
	res, err := http.DefaultClient.Do(req)
	if err != nil {
		log.Fatal(err)
	}
	defer res.Body.Close()
	b, _ := io.ReadAll(res.Body)
	return res.StatusCode, res.Header, string(b)
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, http.HandlerFunc(handler))
	base := "http://" + ln.Addr().String()

	s, h, b := get(base, "/article", map[string]string{"Accept": "text/plain", "X-Request-Id": "req-1"})
	fmt.Printf("GET /article  Accept=text/plain        -> %d Content-Type=%s %q\n", s, h.Get("Content-Type"), b)
	if h.Get("Content-Type") != "text/plain" || h.Get("X-Echo-Request-Id") != "req-1" {
		panic("FAILED")
	}

	s, h, b = get(base, "/article", map[string]string{"Accept": "application/json"})
	fmt.Printf("GET /article  Accept=application/json  -> %d Content-Type=%s %q\n", s, h.Get("Content-Type"), b)
	if h.Get("Content-Type") != "application/json" {
		panic("FAILED")
	}
	currentETag := h.Get("ETag")

	s, _, b = get(base, "/article", map[string]string{"Accept": "text/plain", "If-None-Match": currentETag})
	fmt.Printf("GET /article  If-None-Match=<current>  -> %d %q   (unchanged -> 304, empty body)\n", s, b)
	if s != 304 || b != "" {
		panic("FAILED")
	}
	fmt.Println("OK")
}
