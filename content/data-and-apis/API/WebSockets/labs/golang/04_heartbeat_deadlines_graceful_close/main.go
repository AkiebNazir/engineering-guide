/*
LAB 04 (advanced) - Heartbeats, idle deadlines and graceful shutdown with close codes
======================================================================================
You will learn

  - dead-peer detection: the server pings on a timer and closes connections whose pong never comes
    back. In coder/websocket control frames are processed while Read is running, so:
    a client that KEEPS READING answers pings automatically
    a client that STOPS READING (frozen app, dead network) never answers -> detected

  - a keepalive loop:  every N seconds  c.Ping(ctx with timeout)  -> on error, hang up

  - idle timeout: separate from ping - "this client has sent no application message for N seconds"

  - GRACEFUL SHUTDOWN: tell every client "going away" (close 1001) and wait for their replies,
    concurrently, within a deadline. Clients read the code and RECONNECT with jittered backoff -
    without a stampede.

  - the closing handshake: Close() sends a close frame and WAITS for the peer's; CloseNow() just drops TCP

    server                                    clients
    | ---- Close(1001, "restart in 5s") ---->  see websocket.CloseStatus(err) == 1001
    | <--- Close (echo) ---------------------   reconnect after random(0..2s)

Run it   go run ./WebSockets/labs/golang/04_heartbeat_deadlines_graceful_close
*/
package main

import (
	"context"
	"errors"
	"fmt"
	"math/rand/v2"
	"net"
	"net/http"
	"sync"
	"sync/atomic"
	"time"

	"github.com/coder/websocket"
)

// ------------------------------------------------------------------ server --
type Server struct {
	mu    sync.Mutex
	conns map[*websocket.Conn]struct{}

	pingEvery, pingTimeout, idleTimeout time.Duration
	deadPeers, idleClosed               atomic.Int64
}

func (s *Server) track(c *websocket.Conn, add bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if add {
		s.conns[c] = struct{}{}
	} else {
		delete(s.conns, c)
	}
}

func (s *Server) count() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return len(s.conns)
}

func (s *Server) handle(w http.ResponseWriter, r *http.Request) {
	c, err := websocket.Accept(w, r, nil)
	if err != nil {
		return
	}
	defer c.CloseNow()
	s.track(c, true)
	defer s.track(c, false)

	ctx, cancel := context.WithCancel(r.Context())
	defer cancel()

	// Keepalive: runs beside the read loop. Ping() only completes while someone is calling Read().
	go func() {
		t := time.NewTicker(s.pingEvery)
		defer t.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-t.C:
				pctx, pcancel := context.WithTimeout(ctx, s.pingTimeout)
				err := c.Ping(pctx)
				pcancel()
				if err != nil && ctx.Err() == nil {
					s.deadPeers.Add(1)
					c.CloseNow() // no point in a polite close: the peer is not answering
					cancel()
					return
				}
			}
		}
	}()

	for {
		rctx, rcancel := context.WithTimeout(ctx, s.idleTimeout) // IDLE deadline: no APPLICATION messages
		typ, data, err := c.Read(rctx)
		rcancel()
		if err != nil {
			if rctx.Err() == context.DeadlineExceeded && ctx.Err() == nil {
				s.idleClosed.Add(1)
				c.Close(websocket.StatusPolicyViolation, "idle timeout")
			}
			return
		}
		c.Write(ctx, typ, append([]byte("echo: "), data...))
	}
}

// Shutdown closes EVERY connection concurrently with 1001, bounded by ctx.
func (s *Server) Shutdown(ctx context.Context, reason string) {
	s.mu.Lock()
	conns := make([]*websocket.Conn, 0, len(s.conns))
	for c := range s.conns {
		conns = append(conns, c)
	}
	s.mu.Unlock()

	var wg sync.WaitGroup
	for _, c := range conns {
		wg.Add(1)
		go func() {
			defer wg.Done()
			done := make(chan struct{})
			go func() { c.Close(websocket.StatusGoingAway, reason); close(done) }() // waits for the peer's reply
			select {
			case <-done:
			case <-ctx.Done():
				c.CloseNow() // out of time: drop it
			}
		}()
	}
	wg.Wait()
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	srv := &Server{conns: map[*websocket.Conn]struct{}{}, pingEvery: 100 * time.Millisecond,
		pingTimeout: 400 * time.Millisecond, idleTimeout: 1500 * time.Millisecond}
	ln, _ := net.Listen("tcp", "127.0.0.1:0")
	httpSrv := &http.Server{Handler: http.HandlerFunc(srv.handle)}
	go httpSrv.Serve(ln)
	url := "ws://" + ln.Addr().String()
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()

	dial := func() *websocket.Conn {
		c, _, err := websocket.Dial(ctx, url, nil)
		must(err == nil, fmt.Sprint(err))
		return c
	}

	fmt.Println("== 1. dead-peer detection ==")
	healthy := dial()
	frozen := dial() // connected, but its application never calls Read: pings go unanswered
	_ = frozen
	var healthyReads atomic.Int64
	go func() { // the healthy client reads continuously, so the library answers pings for it
		for {
			if _, _, err := healthy.Read(ctx); err != nil {
				return
			}
			healthyReads.Add(1)
		}
	}()
	time.Sleep(900 * time.Millisecond)
	fmt.Printf("  after 900ms: dead peers detected by the server = %d, open connections = %d\n", srv.deadPeers.Load(), srv.count())
	must(srv.deadPeers.Load() == 1, "exactly the frozen client was detected")
	must(srv.count() == 1, "the healthy client survived")

	fmt.Println("\n== 2. idle timeout is separate from liveness ==")
	fmt.Println("  the healthy client answers pings (alive) but sends NO messages ...")
	time.Sleep(900 * time.Millisecond)
	fmt.Printf("  server closed it for idleness: idleClosed = %d\n", srv.idleClosed.Load())
	must(srv.idleClosed.Load() == 1, "idle client closed")
	fmt.Println("  (ping proves the TCP path and the client library are alive; the idle timeout enforces that the")
	fmt.Println("   user/application is actually DOING something - important for resource-limited servers)")

	fmt.Println("\n== 3. graceful shutdown: 20 clients told 'going away', all within ~ms ==")
	srv.idleTimeout = time.Hour // stop idle-closing for this part
	type result struct {
		status websocket.StatusCode
		reason string
		at     time.Duration
	}
	results := make(chan result, 20)
	shutdownAt := time.Time{}
	var startMu sync.Mutex
	for i := 0; i < 20; i++ {
		c := dial()
		go func() {
			_, _, err := c.Read(ctx) // blocks until the server closes
			startMu.Lock()
			at := time.Since(shutdownAt)
			startMu.Unlock()
			results <- result{websocket.CloseStatus(err), closeReason(err), at}
		}()
	}
	time.Sleep(200 * time.Millisecond)
	sctx, scancel := context.WithTimeout(ctx, 3*time.Second)
	startMu.Lock()
	shutdownAt = time.Now()
	startMu.Unlock()
	srv.Shutdown(sctx, "restarting, reconnect in 0-2s")
	scancel()
	took := time.Since(shutdownAt)

	var worst time.Duration
	for i := 0; i < 20; i++ {
		r := <-results
		must(r.status == websocket.StatusGoingAway, fmt.Sprintf("client got %d", r.status))
		if r.at > worst {
			worst = r.at
		}
		if i == 0 {
			fmt.Printf("  a client saw: status=%d reason=%q\n", r.status, r.reason)
		}
	}
	fmt.Printf("  all 20 clients received 1001; Shutdown took %s (concurrent, not 20 x sequential)\n", took.Round(time.Millisecond))

	fmt.Println("\n== 4. reconnect with jitter so 20 clients do not stampede ==")
	var delays []time.Duration
	for i := 0; i < 20; i++ {
		delays = append(delays, time.Duration(rand.Int64N(int64(2*time.Second)))) // full jitter over 0..2s
	}
	lo, hi := delays[0], delays[0]
	for _, d := range delays {
		lo, hi = min(lo, d), max(hi, d)
	}
	fmt.Printf("  clients would reconnect between %s and %s (spread over the window, not all at once)\n", lo.Round(time.Millisecond), hi.Round(time.Millisecond))
	must(hi-lo > 500*time.Millisecond, "jitter spreads reconnects")
	httpSrv.Close()
	fmt.Println("\nOK")
}

func closeReason(err error) string {
	var ce websocket.CloseError
	if errors.As(err, &ce) {
		return ce.Reason
	}
	return ""
}
