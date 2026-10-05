/*
LEVEL 06 (measured) - connection reuse: what the Transport pool actually does

You will learn
  - http.Transport keeps idle keep-alive connections and reuses them, but
    only if you read the response body to EOF and close it. Close an unread
    body and that connection is thrown away
  - MaxIdleConnsPerHost defaults to 2 (http.DefaultMaxIdleConnsPerHost).
    With 50 concurrent requests to one host, all but 2 connections are
    closed after each burst and re-dialled on the next one - the classic
    "why do we open thousands of connections to our own API" problem
  - this level counts new TCP connections on the server side
    (http.Server.ConnState) and times each variant, printing the real
    numbers from this run

Run: cd content/languages/GoStdLib && go run ./16_net_http/level_06_measured_connection_reuse
*/

package main

import (
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

var newConns atomic.Int64

func newServer() *httptest.Server {
	payload := strings.Repeat("x", 64<<10) // 64 KB, bigger than any read-ahead buffer
	srv := httptest.NewUnstartedServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		io.WriteString(w, payload)
	}))
	srv.Config.ConnState = func(c net.Conn, s http.ConnState) {
		if s == http.StateNew {
			newConns.Add(1)
		}
	}
	srv.Start()
	return srv
}

type result struct {
	name  string
	conns int64
	took  time.Duration
}

// sequential sends n requests one after another with a fresh Transport.
func sequential(url, name string, n int, tr *http.Transport, drain bool) result {
	client := &http.Client{Transport: tr}
	defer tr.CloseIdleConnections()
	newConns.Store(0)
	start := time.Now()
	for i := 0; i < n; i++ {
		resp, err := client.Get(url)
		if err != nil {
			panic(err)
		}
		if drain {
			io.Copy(io.Discard, resp.Body)
		}
		resp.Body.Close()
	}
	return result{name, newConns.Load(), time.Since(start)}
}

// bursts sends `rounds` bursts of `width` concurrent requests.
func bursts(url, name string, rounds, width int, tr *http.Transport) result {
	client := &http.Client{Transport: tr}
	defer tr.CloseIdleConnections()
	newConns.Store(0)
	start := time.Now()
	for r := 0; r < rounds; r++ {
		var wg sync.WaitGroup
		for i := 0; i < width; i++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				resp, err := client.Get(url)
				if err != nil {
					panic(err)
				}
				io.Copy(io.Discard, resp.Body)
				resp.Body.Close()
			}()
		}
		wg.Wait()
	}
	return result{name, newConns.Load(), time.Since(start)}
}

func main() {
	srv := newServer()
	defer srv.Close()
	const n = 300

	results := []result{
		sequential(srv.URL, "drain + close body", n, &http.Transport{}, true),
		sequential(srv.URL, "close without reading", n, &http.Transport{}, false),
		sequential(srv.URL, "DisableKeepAlives", n, &http.Transport{DisableKeepAlives: true}, true),
		bursts(srv.URL, "50-wide bursts, MaxIdleConnsPerHost=2 (default)", 20, 50, &http.Transport{}),
		bursts(srv.URL, "50-wide bursts, MaxIdleConnsPerHost=50", 20, 50, &http.Transport{MaxIdleConnsPerHost: 50}),
	}
	for _, r := range results {
		fmt.Printf("%-50s new connections=%4d  took=%v\n", r.name, r.conns, r.took.Round(time.Millisecond))
	}

	if results[0].conns != 1 {
		panic(fmt.Sprintf("a drained, closed body should reuse one connection, got %d", results[0].conns))
	}
	if results[1].conns < n/2 {
		panic(fmt.Sprintf("closing unread 64KB bodies should force new connections, got only %d", results[1].conns))
	}
	if results[2].conns != n {
		panic(fmt.Sprintf("DisableKeepAlives should dial every time: %d", results[2].conns))
	}
	if results[3].conns <= 2*results[4].conns {
		panic(fmt.Sprintf("default MaxIdleConnsPerHost should churn far more connections: %d vs %d", results[3].conns, results[4].conns))
	}
	fmt.Println("OK")
}
