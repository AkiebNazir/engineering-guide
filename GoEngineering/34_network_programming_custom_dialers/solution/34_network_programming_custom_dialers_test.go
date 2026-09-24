package netdial

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"runtime"
	"strings"
	"sync"
	"testing"
	"time"
)

// ----------------------------------------------------------------------------
// Connection reuse
// ----------------------------------------------------------------------------

// TestLesson_DrainBodyToReuseConnections: the transport can only return a
// connection to the pool once the response body has been read to EOF.
func TestLesson_DrainBodyToReuseConnections(t *testing.T) {
	payload := bytes.Repeat([]byte("x"), 256<<10) // 256 KiB body
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write(payload)
	}))
	defer srv.Close()

	run := func(drain bool) int64 {
		cd := &CountingDialer{}
		o := DefaultClientOptions()
		o.Dial = cd.DialContext
		client := NewClient(o)
		defer client.CloseIdleConnections()
		for range 10 {
			resp, err := client.Get(srv.URL)
			if err != nil {
				t.Fatal(err)
			}
			if drain {
				_, _ = io.Copy(io.Discard, resp.Body)
			}
			resp.Body.Close()
		}
		return cd.Dials()
	}

	drained, undrained := run(true), run(false)
	t.Logf("10 sequential requests: body drained → %d dial(s); closed without reading → %d dials", drained, undrained)
	if drained != 1 {
		t.Fatalf("drained bodies should reuse one connection, got %d dials", drained)
	}
	if undrained <= drained {
		t.Fatalf("expected unread bodies to force new connections, got %d", undrained)
	}
}

// TestLesson_DefaultIdlePoolIsTwoPerHost shows the churn from
// http.DefaultTransport's MaxIdleConnsPerHost=2 under concurrency.
func TestLesson_DefaultIdlePoolIsTwoPerHost(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(2 * time.Millisecond)
		_, _ = io.WriteString(w, "ok")
	}))
	defer srv.Close()

	burst := func(perHost int) int64 {
		cd := &CountingDialer{}
		o := DefaultClientOptions()
		o.Dial = cd.DialContext
		o.MaxIdleConnsPerHost = perHost
		client := NewClient(o)
		defer client.CloseIdleConnections()
		for range 5 { // five bursts of 20 concurrent requests
			var wg sync.WaitGroup
			for range 20 {
				wg.Go(func() {
					resp, err := client.Get(srv.URL)
					if err != nil {
						t.Error(err)
						return
					}
					_, _ = io.Copy(io.Discard, resp.Body)
					resp.Body.Close()
				})
			}
			wg.Wait()
		}
		return cd.Dials()
	}

	two, thirtyTwo := burst(http.DefaultMaxIdleConnsPerHost), burst(32)
	t.Logf("5 bursts × 20 concurrent: MaxIdleConnsPerHost=%d → %d dials; =32 → %d dials",
		http.DefaultMaxIdleConnsPerHost, two, thirtyTwo)
	if two <= thirtyTwo {
		t.Fatalf("expected a 2-connection idle pool to re-dial more: %d vs %d", two, thirtyTwo)
	}
}

// ----------------------------------------------------------------------------
// Timeout layers
// ----------------------------------------------------------------------------

func TestLesson_TimeoutLayers(t *testing.T) {
	// Headers after 300ms.
	slowHeaders := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		select {
		case <-time.After(300 * time.Millisecond):
		case <-r.Context().Done():
		}
		_, _ = io.WriteString(w, "late")
	}))
	defer slowHeaders.Close()

	// Headers immediately, body after 300ms.
	slowBody := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		http.NewResponseController(w).Flush()
		select {
		case <-time.After(300 * time.Millisecond):
		case <-r.Context().Done():
		}
		_, _ = io.WriteString(w, "late body")
	}))
	defer slowBody.Close()

	fetch := func(c *http.Client, url string) (time.Duration, error) {
		start := time.Now()
		resp, err := c.Get(url)
		if err == nil {
			_, err = io.ReadAll(resp.Body)
			resp.Body.Close()
		}
		return time.Since(start), err
	}

	// 1. The default client waits as long as the server wants.
	took, err := fetch(http.DefaultClient, slowHeaders.URL)
	if err != nil || took < 300*time.Millisecond {
		t.Fatalf("DefaultClient: %v after %v", err, took)
	}
	t.Logf("http.DefaultClient (no timeouts):           waited the full %v", took.Round(10*time.Millisecond))

	// 2. ResponseHeaderTimeout cuts off slow headers...
	o := DefaultClientOptions()
	o.ResponseHeaderTimeout = 50 * time.Millisecond
	o.RequestTimeout = 0
	headerOnly := NewClient(o)
	took, err = fetch(headerOnly, slowHeaders.URL)
	if !IsTimeout(err) || took > 250*time.Millisecond {
		t.Fatalf("ResponseHeaderTimeout: err=%v took=%v", err, took)
	}
	t.Logf("ResponseHeaderTimeout=50ms, slow headers:   %v after %v", err, took.Round(time.Millisecond))

	// 3. ...but does NOT cover a slow body.
	took, err = fetch(headerOnly, slowBody.URL)
	if err != nil || took < 300*time.Millisecond {
		t.Fatalf("slow body with only ResponseHeaderTimeout: err=%v took=%v", err, took)
	}
	t.Logf("ResponseHeaderTimeout=50ms, slow body:      succeeded after %v (body not covered)", took.Round(10*time.Millisecond))

	// 4. Client.Timeout covers the whole exchange including the body.
	o.RequestTimeout = 100 * time.Millisecond
	whole := NewClient(o)
	took, err = fetch(whole, slowBody.URL)
	if !IsTimeout(err) || took > 250*time.Millisecond {
		t.Fatalf("Client.Timeout: err=%v took=%v", err, took)
	}
	t.Logf("Client.Timeout=100ms, slow body:            timed out after %v", took.Round(time.Millisecond))
}

func TestLesson_TLSHandshakeTimeout(t *testing.T) {
	// A TCP listener that accepts and then never speaks TLS: the connect
	// succeeds instantly, only the handshake hangs.
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer ln.Close()
	go func() {
		for {
			c, err := ln.Accept()
			if err != nil {
				return
			}
			defer c.Close()
		}
	}()

	o := DefaultClientOptions()
	o.TLSHandshakeTimeout = 100 * time.Millisecond
	start := time.Now()
	_, err = NewClient(o).Get("https://" + ln.Addr().String())
	took := time.Since(start)
	if err == nil || !strings.Contains(err.Error(), "TLS handshake timeout") || took > time.Second {
		t.Fatalf("err=%v took=%v", err, took)
	}
	t.Logf("silent TLS peer: %q after %v", err, took.Round(time.Millisecond))
}

// ----------------------------------------------------------------------------
// Dialers
// ----------------------------------------------------------------------------

func TestPinnedDialerKeepsHostHeader(t *testing.T) {
	var gotHost string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotHost = r.Host
		_, _ = io.WriteString(w, "pinned")
	}))
	defer srv.Close()

	base := (&net.Dialer{Timeout: time.Second}).DialContext
	o := DefaultClientOptions()
	o.Dial = PinnedDialer(base, map[string]string{"api.internal.example:80": srv.Listener.Addr().String()})
	resp, err := NewClient(o).Get("http://api.internal.example/v1/health")
	if err != nil {
		t.Fatal(err)
	}
	body, _ := io.ReadAll(resp.Body)
	resp.Body.Close()
	if string(body) != "pinned" || gotHost != "api.internal.example" {
		t.Fatalf("body=%q Host=%q", body, gotHost)
	}
}

func TestDialTimeoutViaContext(t *testing.T) {
	// A dial func that never connects — stands in for a black-holed address.
	blackhole := func(ctx context.Context, network, addr string) (net.Conn, error) {
		<-ctx.Done()
		return nil, &net.OpError{Op: "dial", Net: network, Err: ctx.Err()}
	}
	o := DefaultClientOptions()
	o.Dial = blackhole
	o.RequestTimeout = 80 * time.Millisecond
	start := time.Now()
	_, err := NewClient(o).Get("http://10.255.255.1/")
	if !IsTimeout(err) || time.Since(start) > time.Second {
		t.Fatalf("err=%v", err)
	}
}

// ----------------------------------------------------------------------------
// Framing and the TCP server
// ----------------------------------------------------------------------------

func TestEchoServerRoundTrip(t *testing.T) {
	s, err := StartEchoServer("127.0.0.1:0", time.Second)
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()

	conn, err := net.Dial("tcp", s.Addr())
	if err != nil {
		t.Fatal(err)
	}
	defer conn.Close()

	for _, msg := range [][]byte{[]byte("hello"), {}, bytes.Repeat([]byte{0xAB}, 100_000)} {
		if err := WriteFrame(conn, msg, time.Second); err != nil {
			t.Fatal(err)
		}
		got, err := ReadFrame(conn, 1<<20, time.Second)
		if err != nil || !bytes.Equal(got, msg) {
			t.Fatalf("echo of %d bytes: got %d bytes, err %v", len(msg), len(got), err)
		}
	}
}

// TestLesson_TCPIsAStream proves that one Write is not one Read: a frame
// dribbled one byte at a time still decodes, because ReadFrame uses
// io.ReadFull rather than a single conn.Read.
func TestLesson_TCPIsAStream(t *testing.T) {
	client, server := net.Pipe() // synchronous, in-memory full-duplex conn
	defer client.Close()
	defer server.Close()

	var frame bytes.Buffer
	_ = WriteFrame(nopDeadlineConn{&frame}, []byte("fragmented"), 0)
	go func() {
		for _, b := range frame.Bytes() {
			_, _ = client.Write([]byte{b}) // 14 separate writes
		}
	}()

	got, err := ReadFrame(server, 64, time.Second)
	if err != nil || string(got) != "fragmented" {
		t.Fatalf("got %q err %v", got, err)
	}
}

func TestReadFrameRejectsOversizedBeforeAllocating(t *testing.T) {
	client, server := net.Pipe()
	defer client.Close()
	defer server.Close()
	go func() { _, _ = client.Write([]byte{0xFF, 0xFF, 0xFF, 0xFF}) }() // claims 4 GiB

	var before, after runtime.MemStats
	runtime.ReadMemStats(&before)
	_, err := ReadFrame(server, 1<<20, time.Second)
	runtime.ReadMemStats(&after)
	if !errors.Is(err, ErrFrameTooLarge) {
		t.Fatalf("err = %v", err)
	}
	if grew := after.TotalAlloc - before.TotalAlloc; grew > 1<<20 {
		t.Fatalf("allocated %d bytes for a rejected frame", grew)
	}
}

func TestLesson_ReadDeadlineAndIdleTimeout(t *testing.T) {
	s, err := StartEchoServer("127.0.0.1:0", 100*time.Millisecond)
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()

	// Client-side read deadline: the server has nothing to say.
	conn, err := net.Dial("tcp", s.Addr())
	if err != nil {
		t.Fatal(err)
	}
	defer conn.Close()
	start := time.Now()
	_, err = ReadFrame(conn, 1024, 30*time.Millisecond)
	if !IsTimeout(err) {
		t.Fatalf("read with deadline: %v", err)
	}
	t.Logf("client read deadline 30ms: %v after %v", err, time.Since(start).Round(time.Millisecond))

	// Server-side idle timeout: after ~100ms of silence the server hangs up,
	// so the next read sees EOF instead of blocking forever.
	start = time.Now()
	_, err = ReadFrame(conn, 1024, 2*time.Second)
	took := time.Since(start)
	if !errors.Is(err, io.EOF) || took > time.Second {
		t.Fatalf("expected EOF from idle server close, got %v after %v", err, took)
	}
	t.Logf("server idle timeout 100ms: client saw %v after a further %v", err, took.Round(time.Millisecond))
}

func TestEchoServerCloseUnblocksAndWaits(t *testing.T) {
	s, err := StartEchoServer("127.0.0.1:0", time.Hour) // idle timeout won't save us
	if err != nil {
		t.Fatal(err)
	}
	var conns []net.Conn
	for range 5 {
		c, err := net.Dial("tcp", s.Addr())
		if err != nil {
			t.Fatal(err)
		}
		conns = append(conns, c)
	}
	time.Sleep(20 * time.Millisecond) // let the handlers block in ReadFrame

	done := make(chan error, 1)
	go func() { done <- s.Close() }()
	select {
	case <-done:
	case <-time.After(2 * time.Second):
		t.Fatal("Close hung waiting for handlers blocked in Read")
	}
	for _, c := range conns {
		c.Close()
	}
	if _, err := net.DialTimeout("tcp", s.Addr(), 200*time.Millisecond); err == nil {
		t.Fatal("server still accepting after Close")
	}
}

type nopDeadlineConn struct{ w io.Writer }

func (c nopDeadlineConn) Write(p []byte) (int, error)    { return c.w.Write(p) }
func (nopDeadlineConn) Read([]byte) (int, error)         { return 0, io.EOF }
func (nopDeadlineConn) Close() error                     { return nil }
func (nopDeadlineConn) LocalAddr() net.Addr              { return nil }
func (nopDeadlineConn) RemoteAddr() net.Addr             { return nil }
func (nopDeadlineConn) SetDeadline(time.Time) error      { return nil }
func (nopDeadlineConn) SetReadDeadline(time.Time) error  { return nil }
func (nopDeadlineConn) SetWriteDeadline(time.Time) error { return nil }

// ----------------------------------------------------------------------------
// Runnable examples
// ----------------------------------------------------------------------------

func ExampleWriteFrame() {
	s, _ := StartEchoServer("127.0.0.1:0", time.Second)
	defer s.Close()
	conn, _ := net.Dial("tcp", s.Addr())
	defer conn.Close()

	_ = WriteFrame(conn, []byte("ping"), time.Second)
	reply, err := ReadFrame(conn, 1024, time.Second)
	fmt.Println(string(reply), err)
	// Output: ping <nil>
}

func ExampleIsTimeout() {
	ctx, cancel := context.WithTimeout(context.Background(), time.Millisecond)
	defer cancel()
	<-ctx.Done()
	wrapped := fmt.Errorf("fetch profile: %w", ctx.Err())
	fmt.Println(IsTimeout(wrapped), IsTimeout(io.EOF), IsTimeout(nil))
	// Output: true false false
}
