// Package netdial is the reference solution for Problem 34 — Network
// Programming & Custom Dialers.
package netdial

import (
	"context"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"sync"
	"sync/atomic"
	"time"
)

// DialFunc is the signature of net.Dialer.DialContext and
// http.Transport.DialContext.
type DialFunc func(ctx context.Context, network, addr string) (net.Conn, error)

// ============================================================================
// 1. A production HTTP client
// ============================================================================

// ClientOptions configures every timeout layer explicitly.
type ClientOptions struct {
	DialTimeout           time.Duration // TCP connect (per attempt)
	KeepAliveIdle         time.Duration // TCP keep-alive: idle time before first probe
	TLSHandshakeTimeout   time.Duration
	ResponseHeaderTimeout time.Duration // request written → response headers received
	IdleConnTimeout       time.Duration // how long a pooled idle connection lives
	RequestTimeout        time.Duration // http.Client.Timeout: dial through reading the BODY
	MaxIdleConnsPerHost   int
	Dial                  DialFunc // optional: custom dialer (counting, pinning, unix sockets)
}

// DefaultClientOptions are conservative values for service-to-service calls.
// Tune per dependency; the point is that none of them is "infinite".
func DefaultClientOptions() ClientOptions {
	return ClientOptions{
		DialTimeout:           3 * time.Second,
		KeepAliveIdle:         30 * time.Second,
		TLSHandshakeTimeout:   3 * time.Second,
		ResponseHeaderTimeout: 5 * time.Second,
		IdleConnTimeout:       90 * time.Second,
		RequestTimeout:        10 * time.Second,
		MaxIdleConnsPerHost:   32,
	}
}

// NewClient builds an *http.Client from o.
//
// Why not http.DefaultClient: its Timeout is zero (no limit at all), and
// http.DefaultTransport keeps only DefaultMaxIdleConnsPerHost = 2 idle
// connections per host — at 50 concurrent requests to one backend, 48
// connections are closed after every burst and re-dialed on the next one,
// burning CPU on handshakes and piling up sockets in TIME_WAIT.
func NewClient(o ClientOptions) *http.Client {
	dial := o.Dial
	if dial == nil {
		d := &net.Dialer{
			Timeout: o.DialTimeout,
			// Go 1.23+: full control of TCP keep-alive probes. Probes detect
			// peers that vanished without a FIN/RST (crashed host, dropped
			// NAT mapping) on connections that are otherwise idle forever.
			KeepAliveConfig: net.KeepAliveConfig{
				Enable: true,
				Idle:   o.KeepAliveIdle,
			},
		}
		dial = d.DialContext
	}
	transport := &http.Transport{
		Proxy:                 http.ProxyFromEnvironment,
		DialContext:           dial,
		ForceAttemptHTTP2:     true, // a custom DialContext disables HTTP/2 unless forced
		TLSHandshakeTimeout:   o.TLSHandshakeTimeout,
		ResponseHeaderTimeout: o.ResponseHeaderTimeout,
		IdleConnTimeout:       o.IdleConnTimeout,
		MaxIdleConns:          max(100, o.MaxIdleConnsPerHost),
		MaxIdleConnsPerHost:   o.MaxIdleConnsPerHost,
		ExpectContinueTimeout: time.Second,
	}
	return &http.Client{Transport: transport, Timeout: o.RequestTimeout}
}

// ============================================================================
// 2. Custom dialers
// ============================================================================

// CountingDialer counts outbound connection attempts — the cheapest possible
// way to verify connection pooling works (it's also what a "new connections
// per second" metric is built on).
type CountingDialer struct {
	Dialer *net.Dialer
	dials  atomic.Int64
}

// DialContext dials and counts.
func (d *CountingDialer) DialContext(ctx context.Context, network, addr string) (net.Conn, error) {
	d.dials.Add(1)
	dialer := d.Dialer
	if dialer == nil {
		dialer = &net.Dialer{}
	}
	return dialer.DialContext(ctx, network, addr)
}

// Dials reports how many connections have been dialed.
func (d *CountingDialer) Dials() int64 { return d.dials.Load() }

// PinnedDialer routes connections for specific host:port addresses to other
// addresses, bypassing DNS — like curl --resolve. Uses: pointing a client at
// a local test server while keeping the real Host header and TLS SNI,
// canarying one backend, or sidecar/mesh addresses. Unmatched addresses go to
// base unchanged.
func PinnedDialer(base DialFunc, overrides map[string]string) DialFunc {
	return func(ctx context.Context, network, addr string) (net.Conn, error) {
		if target, ok := overrides[addr]; ok {
			addr = target
		}
		return base(ctx, network, addr)
	}
}

// ============================================================================
// 3. Timeout classification
// ============================================================================

// IsTimeout reports whether err is any kind of timeout: a net.Error with
// Timeout() (dial, read/write deadline, http.Client.Timeout), a deadline
// exceeded on an *os/net* deadline, or a context deadline.
func IsTimeout(err error) bool {
	if err == nil {
		return false
	}
	if errors.Is(err, os.ErrDeadlineExceeded) || errors.Is(err, context.DeadlineExceeded) {
		return true
	}
	var ne net.Error
	return errors.As(err, &ne) && ne.Timeout()
}

// ============================================================================
// 4. Length-prefixed framing with deadlines
// ============================================================================

// ErrFrameTooLarge is returned when a peer announces a frame above the limit.
var ErrFrameTooLarge = errors.New("netdial: frame too large")

// WriteFrame writes a 4-byte big-endian length followed by payload.
//
// Deadlines on net.Conn are ABSOLUTE times, not durations: a deadline set
// once applies to every later operation until changed. So the pattern is
// "set before each logical operation". A zero timeout clears the deadline.
func WriteFrame(conn net.Conn, payload []byte, timeout time.Duration) error {
	if len(payload) > int(^uint32(0)) {
		return ErrFrameTooLarge
	}
	if err := setDeadline(conn.SetWriteDeadline, timeout); err != nil {
		return err
	}
	var hdr [4]byte
	binary.BigEndian.PutUint32(hdr[:], uint32(len(payload)))
	// net.Buffers lets writev(2) send header+payload in one syscall without
	// copying them into a new slice.
	bufs := net.Buffers{hdr[:], payload}
	_, err := bufs.WriteTo(conn)
	return err
}

// ReadFrame reads one frame, rejecting announced lengths above maxSize
// BEFORE allocating — otherwise one malicious 4-byte header could make the
// server allocate 4 GiB.
func ReadFrame(conn net.Conn, maxSize int, timeout time.Duration) ([]byte, error) {
	if err := setDeadline(conn.SetReadDeadline, timeout); err != nil {
		return nil, err
	}
	var hdr [4]byte
	// TCP is a byte STREAM: one Read may return 1 byte of the header, or the
	// header plus half the payload. io.ReadFull loops until it has exactly
	// len(buf) bytes. A plain conn.Read here is the classic framing bug.
	if _, err := io.ReadFull(conn, hdr[:]); err != nil {
		return nil, err
	}
	n := binary.BigEndian.Uint32(hdr[:])
	if uint64(n) > uint64(maxSize) {
		return nil, fmt.Errorf("%w: %d > %d", ErrFrameTooLarge, n, maxSize)
	}
	payload := make([]byte, n)
	if _, err := io.ReadFull(conn, payload); err != nil {
		return nil, err
	}
	return payload, nil
}

func setDeadline(set func(time.Time) error, timeout time.Duration) error {
	if timeout <= 0 {
		return set(time.Time{})
	}
	return set(time.Now().Add(timeout))
}

// ============================================================================
// 5. A TCP server with idle timeouts and graceful Close
// ============================================================================

// EchoServer echoes frames back to the sender.
type EchoServer struct {
	ln          net.Listener
	idleTimeout time.Duration
	maxFrame    int

	mu     sync.Mutex
	conns  map[net.Conn]struct{}
	closed bool
	wg     sync.WaitGroup
}

// StartEchoServer listens on addr (use "127.0.0.1:0" for a random port).
// Connections that send nothing for idleTimeout are closed, which is what
// keeps a server from accumulating dead or abandoned connections (and what
// defends against slowloris-style clients that open sockets and trickle).
func StartEchoServer(addr string, idleTimeout time.Duration) (*EchoServer, error) {
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		return nil, err
	}
	s := &EchoServer{ln: ln, idleTimeout: idleTimeout, maxFrame: 1 << 20, conns: map[net.Conn]struct{}{}}
	s.wg.Add(1)
	go s.acceptLoop()
	return s, nil
}

// Addr is the listening address.
func (s *EchoServer) Addr() string { return s.ln.Addr().String() }

func (s *EchoServer) acceptLoop() {
	defer s.wg.Done()
	for {
		conn, err := s.ln.Accept()
		if err != nil {
			if errors.Is(err, net.ErrClosed) {
				return // Close() was called
			}
			// Temporary errors (EMFILE: out of file descriptors) must not
			// kill the accept loop; back off briefly and keep serving.
			time.Sleep(5 * time.Millisecond)
			continue
		}
		if !s.track(conn) {
			conn.Close()
			return
		}
		s.wg.Add(1)
		go s.serve(conn)
	}
}

func (s *EchoServer) track(conn net.Conn) bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.closed {
		return false
	}
	s.conns[conn] = struct{}{}
	return true
}

func (s *EchoServer) serve(conn net.Conn) {
	defer s.wg.Done()
	defer func() {
		s.mu.Lock()
		delete(s.conns, conn)
		s.mu.Unlock()
		conn.Close()
	}()
	for {
		frame, err := ReadFrame(conn, s.maxFrame, s.idleTimeout)
		if err != nil {
			return // EOF, idle timeout, oversized frame, or Close()
		}
		if err := WriteFrame(conn, frame, 5*time.Second); err != nil {
			return
		}
	}
}

// Close stops accepting, closes every open connection (unblocking their
// reads), and waits for all handler goroutines to exit.
func (s *EchoServer) Close() error {
	s.mu.Lock()
	if s.closed {
		s.mu.Unlock()
		return nil
	}
	s.closed = true
	err := s.ln.Close()
	for c := range s.conns {
		c.Close()
	}
	s.mu.Unlock()
	s.wg.Wait()
	return err
}
