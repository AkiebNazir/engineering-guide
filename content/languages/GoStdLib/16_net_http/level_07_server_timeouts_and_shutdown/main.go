/*
LEVEL 07 (lifecycle) - server timeouts and graceful shutdown

You will learn
  - http.ListenAndServe(addr, h) builds a Server with NO timeouts: a client
    that opens a connection and sends headers one byte a minute (slowloris)
    holds a goroutine and a file descriptor forever
  - the four http.Server timeouts:
      ReadHeaderTimeout - time to receive the request headers (set it, always)
      ReadTimeout       - headers + body
      WriteTimeout      - from end of headers read to end of response write
      IdleTimeout       - how long a keep-alive connection may sit idle
  - Server.Shutdown(ctx) stops accepting, lets in-flight requests finish,
    then returns; ListenAndServe/Serve returns http.ErrServerClosed, which
    is the normal exit, not a failure

Run: cd content/languages/GoStdLib && go run ./16_net_http/level_07_server_timeouts_and_shutdown
*/

package main

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"time"
)

// startServer serves h on a free loopback port and returns the server, its
// address and a channel that receives Serve's return value.
func startServer(srv *http.Server) (string, <-chan error) {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		panic(err)
	}
	done := make(chan error, 1)
	go func() { done <- srv.Serve(ln) }()
	return ln.Addr().String(), done
}

// slowloris sends half a request and reports how long the server kept the
// connection open, up to `wait`.
func slowloris(addr string, wait time.Duration) (closedAfter time.Duration, closed bool) {
	conn, err := net.Dial("tcp", addr)
	if err != nil {
		panic(err)
	}
	defer conn.Close()
	start := time.Now()
	io.WriteString(conn, "GET / HTTP/1.1\r\nHost: lab\r\n") // no final blank line: headers never finish
	conn.SetReadDeadline(time.Now().Add(wait))
	_, err = io.ReadAll(conn)
	if errors.Is(err, os.ErrDeadlineExceeded) {
		return time.Since(start), false // we gave up first: server still holding it
	}
	return time.Since(start), true
}

func main() {
	hello := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { io.WriteString(w, "hi") })

	// 1. No timeouts (what http.ListenAndServe gives you).
	bare := &http.Server{Handler: hello}
	addr, _ := startServer(bare)
	took, closed := slowloris(addr, 1*time.Second)
	fmt.Printf("no ReadHeaderTimeout:      half-sent request still open after %v (closed=%v)\n", took.Round(10*time.Millisecond), closed)
	if closed {
		panic("a server without timeouts should keep the stalled connection open")
	}
	bare.Close()

	// 2. ReadHeaderTimeout closes it.
	guarded := &http.Server{Handler: hello, ReadHeaderTimeout: 200 * time.Millisecond}
	addr, _ = startServer(guarded)
	took, closed = slowloris(addr, 2*time.Second)
	fmt.Printf("ReadHeaderTimeout=200ms:   server closed the connection after %v (closed=%v)\n", took.Round(10*time.Millisecond), closed)
	if !closed || took > time.Second {
		panic("ReadHeaderTimeout should have closed the slow connection quickly")
	}
	guarded.Close()

	// 3. Graceful shutdown lets an in-flight request finish.
	slow := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(300 * time.Millisecond)
		io.WriteString(w, "finished")
	})
	srv := &http.Server{
		Handler:           slow,
		ReadHeaderTimeout: 2 * time.Second,
		ReadTimeout:       5 * time.Second,
		WriteTimeout:      5 * time.Second,
		IdleTimeout:       30 * time.Second,
	}
	addr, served := startServer(srv)
	type res struct {
		body string
		err  error
	}
	inflight := make(chan res, 1)
	go func() {
		resp, err := http.Get("http://" + addr + "/")
		if err != nil {
			inflight <- res{"", err}
			return
		}
		b, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		inflight <- res{string(b), nil}
	}()
	time.Sleep(100 * time.Millisecond) // the request is now inside the handler

	shutStart := time.Now()
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	if err := srv.Shutdown(ctx); err != nil {
		panic(err)
	}
	shutTook := time.Since(shutStart)
	r := <-inflight
	serveErr := <-served
	_, dialErr := net.DialTimeout("tcp", addr, 200*time.Millisecond)

	fmt.Printf("Shutdown waited %v; in-flight request got %q (err=%v)\n", shutTook.Round(10*time.Millisecond), r.body, r.err)
	fmt.Printf("Serve returned %v; new dial after shutdown: %v\n", serveErr, dialErr != nil)
	if r.err != nil || r.body != "finished" {
		panic("the in-flight request should have completed during graceful shutdown")
	}
	if !errors.Is(serveErr, http.ErrServerClosed) {
		panic("Serve should return http.ErrServerClosed after Shutdown")
	}
	if dialErr == nil {
		panic("the listener should be closed after Shutdown")
	}
	fmt.Println("OK")
}
