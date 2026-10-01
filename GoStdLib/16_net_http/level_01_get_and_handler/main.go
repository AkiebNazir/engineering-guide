/*
LEVEL 01 (basics) - a handler, a test server, and one GET

You will learn
  - a server-side handler is any func(http.ResponseWriter, *http.Request):
    write headers, then a status (optional, 200 by default), then the body
  - httptest.NewServer starts a real HTTP server on 127.0.0.1 with a free
    port the OS picks, so examples and tests never fight over a fixed port
  - http.Get returns a *http.Response whose Body is a stream you MUST
    close, even if you never read it - the connection is only returned to
    the pool (or released) once the body is closed

Run: go run ./GoStdLib/16_net_http/level_01_get_and_handler
*/

package main

import (
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
)

func hello(w http.ResponseWriter, r *http.Request) {
	name := r.URL.Query().Get("name")
	if name == "" {
		name = "world"
	}
	w.Header().Set("Content-Type", "text/plain; charset=utf-8")
	fmt.Fprintf(w, "hello, %s\n", name)
}

func main() {
	srv := httptest.NewServer(http.HandlerFunc(hello))
	defer srv.Close()
	fmt.Println("test server listening on", srv.URL)

	resp, err := http.Get(srv.URL + "/?name=gopher")
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close() // always: returns the connection to the pool

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		panic(err)
	}

	fmt.Printf("status=%q content-type=%q body=%q\n", resp.Status, resp.Header.Get("Content-Type"), body)
	if resp.StatusCode != http.StatusOK {
		panic(fmt.Sprintf("want 200, got %d", resp.StatusCode))
	}
	if string(body) != "hello, gopher\n" {
		panic(fmt.Sprintf("unexpected body %q", body))
	}
	if !strings.HasPrefix(resp.Header.Get("Content-Type"), "text/plain") {
		panic("content type header was not sent")
	}
	// Content-Length was set by net/http itself: a small body written in one
	// go is buffered, so the server knows its length before sending headers.
	if resp.ContentLength != int64(len("hello, gopher\n")) {
		panic(fmt.Sprintf("want Content-Length %d, got %d", len("hello, gopher\n"), resp.ContentLength))
	}
	fmt.Println("OK")
}
