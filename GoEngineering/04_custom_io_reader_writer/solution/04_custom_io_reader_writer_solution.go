// Package streamtransform is the reference implementation of Problem 04:
// composable streaming io.Reader/io.Writer wrappers plus an io.Pipe-based
// producer/consumer pipeline demonstrating real backpressure. Read the
// header comment in ../explanation/04_custom_io_reader_writer_explanation.go
// first — it has the full spec and rationale; this file focuses on *how*
// and *why* each line is written the way it is.
package streamtransform

import (
	"bytes"
	"io"
	"sync/atomic"
)

// UpperReader wraps an io.Reader, uppercasing ASCII bytes as they stream
// through.
//
// The only field is the wrapped reader — UpperReader holds no buffer of its
// own. That's the entire point: the transform happens IN the caller's
// buffer, in Read, so memory use stays O(len(p)) regardless of how much data
// flows through, whether that's 10 bytes or 10GB.
type UpperReader struct {
	r io.Reader
}

// NewUpperReader returns an UpperReader wrapping r.
func NewUpperReader(r io.Reader) *UpperReader {
	return &UpperReader{r: r}
}

// Read implements io.Reader: delegates to the wrapped reader into p, then
// uppercases the bytes actually read (p[:n]) in place.
//
// The critical detail is the order of operations: we transform p[:n] BEFORE
// checking err, not after an early return on err != nil. The io.Reader
// contract explicitly permits (and, e.g. bytes.Reader on the final chunk,
// commonly does) returning n>0 together with a non-nil error — including
// io.EOF — on the same call. A naive `if err != nil { return 0, err }` guard
// placed before the transform would silently drop the last chunk of any
// stream that doesn't happen to end exactly on a Read-buffer boundary. Doing
// the transform unconditionally on p[:n], then returning (n, err) verbatim,
// is correct regardless of which case we're in.
func (u *UpperReader) Read(p []byte) (int, error) {
	n, err := u.r.Read(p)
	for i, b := range p[:n] {
		if b >= 'a' && b <= 'z' {
			p[i] = b - ('a' - 'A')
		}
	}
	return n, err
}

// CountingWriter wraps an io.Writer, atomically counting bytes written.
//
// count is atomic.Int64, not a bare int64, because the spec explicitly
// requires Count() to be safe to call from a different goroutine than the
// one doing the writing — a metrics/reporting goroutine polling Count()
// while the hot path keeps writing. A bare int64 would be a data race
// (caught by `go test -race`) the instant that happens.
type CountingWriter struct {
	w     io.Writer
	count atomic.Int64
}

// NewCountingWriter returns a CountingWriter wrapping w.
func NewCountingWriter(w io.Writer) *CountingWriter {
	return &CountingWriter{w: w}
}

// Write implements io.Writer: delegates to the wrapped writer and atomically
// adds the number of bytes ACTUALLY written to the running count.
//
// We add n (the wrapped Write's return value), not len(p). If the
// underlying Write short-writes and returns an error, io.Writer's contract
// says it must report how much it actually consumed via n — counting
// len(p) instead would overstate bytes genuinely written to the underlying
// sink, which defeats the purpose of a byte-accounting wrapper (e.g. billing
// or a "bytes sent to the client" metric).
func (c *CountingWriter) Write(p []byte) (int, error) {
	n, err := c.w.Write(p)
	c.count.Add(int64(n))
	return n, err
}

// Count returns the total bytes written so far. Safe to call concurrently
// with Write — atomic.Int64.Load is a single atomic load instruction, no
// locking needed.
func (c *CountingWriter) Count() int64 {
	return c.count.Load()
}

// LineSplitWriter buffers arbitrary write chunks and invokes onLine once
// per complete line (delimited by '\n', with an optional preceding '\r'
// stripped for CRLF inputs).
//
// buf accumulates bytes across Write calls until a '\n' is found; flushed
// tracks whether the trailing partial line (if any) has already been
// delivered by Flush, so a second Flush call after all data is done is a
// no-op rather than re-delivering (or, worse, delivering an empty string).
type LineSplitWriter struct {
	onLine  func(line string)
	buf     []byte
	flushed bool
}

// NewLineSplitWriter returns a LineSplitWriter that invokes onLine for each
// complete line seen across however many Write calls it takes to assemble
// one.
func NewLineSplitWriter(onLine func(line string)) *LineSplitWriter {
	return &LineSplitWriter{onLine: onLine}
}

// Write implements io.Writer.
//
// We append the whole chunk p to buf first, then repeatedly search from the
// front for '\n' with bytes.IndexByte — the idiomatic, allocation-free way
// to scan for a delimiter in a byte slice. bytes.Split isn't usable here:
// it requires the whole input to already be complete, which mid-stream it
// isn't — the very last "line" in any given Write might just be the first
// half of a line that finishes in a future Write.
//
// Every call to Write appends new data before checking flushed, so writing
// again after a Flush "un-flushes" correctly (flushed only matters to make
// repeated Flush calls with no intervening Write idempotent).
func (l *LineSplitWriter) Write(p []byte) (int, error) {
	l.buf = append(l.buf, p...)
	l.flushed = false

	for {
		idx := bytes.IndexByte(l.buf, '\n')
		if idx == -1 {
			break
		}
		line := l.buf[:idx]
		line = bytes.TrimSuffix(line, []byte("\r")) // CRLF handling
		l.onLine(string(line))
		l.buf = l.buf[idx+1:]
	}

	// This Writer never rejects data because of line-splitting bookkeeping —
	// buffering a partial line isn't a write failure — so we always report
	// the full length consumed, satisfying io.Writer's "must consume all of
	// p or return an error" contract.
	return len(p), nil
}

// Flush delivers any buffered trailing partial line (no terminating '\n')
// to onLine. Idempotent: once the buffered remainder has been delivered (or
// there was nothing to deliver), calling Flush again does nothing until
// more data arrives via Write.
func (l *LineSplitWriter) Flush() error {
	if l.flushed || len(l.buf) == 0 {
		l.flushed = true
		return nil
	}
	line := bytes.TrimSuffix(l.buf, []byte("\r"))
	l.onLine(string(line))
	l.buf = l.buf[:0]
	l.flushed = true
	return nil
}

// StreamPipeline reads from src, uppercases via UpperReader, and writes to
// dst, using an io.Pipe to hand data between a producer goroutine (reading
// src, writing the PipeWriter) and the calling goroutine (reading the
// PipeReader, writing dst).
//
// Why this is the "real" version and not just io.Copy(dst,
// NewUpperReader(src)): a direct chain works, but it does everything on one
// goroutine with no decoupling between the source and destination — fine
// for a toy example, but it doesn't exercise (or teach) io.Pipe's actual
// value proposition. io.Pipe is a synchronous, UNBUFFERED in-memory pipe: a
// PipeWriter.Write blocks until a matching PipeReader.Read has consumed
// that data. That's real backpressure — if dst is slow, the consumer's
// io.Copy(dst, pr) blocks on Write, which means pr's buffer isn't being
// drained, which means the producer's io.Copy(pw, ...) blocks on Write to
// pw. A slow consumer throttles the producer without either side needing to
// know about the other, and without any unbounded buffer growing in
// between — the exact behavior you want connecting, e.g., a slow network
// upload to a fast disk read.
func StreamPipeline(src io.Reader, dst io.Writer) error {
	pr, pw := io.Pipe()

	// producerErr is only ever written by the producer goroutine and only
	// ever read by the calling goroutine AFTER that goroutine has confirmed
	// (via the done channel) that the producer has finished — so there's no
	// data race despite no explicit lock guarding it.
	var producerErr error
	done := make(chan struct{})

	go func() {
		defer close(done)
		// Deferred immediately after pipe creation (well, immediately in
		// this goroutine's body) rather than at the end of the function: if
		// io.Copy panics or an earlier line here ever grows a new early
		// return, the PipeWriter still gets closed and the consumer's Read
		// doesn't block forever. This is the single most common io.Pipe bug
		// the explanation file calls out.
		_, err := io.Copy(pw, NewUpperReader(src))
		producerErr = err
		// CloseWithError(nil) is equivalent to Close(), but writing it
		// explicitly documents intent: we always want the consumer's
		// subsequent Read to observe io.EOF on success, or err (surfaced via
		// pr.Read) on failure.
		pw.CloseWithError(err)
	}()

	_, consumerErr := io.Copy(dst, pr)

	// Wait for the producer to fully finish (and for producerErr to be
	// safely readable) before inspecting producerErr — closing pw unblocks
	// the consumer's io.Copy, but doesn't guarantee the producer goroutine's
	// assignment to producerErr has happened-before this point without this
	// synchronization.
	<-done

	// Prefer the producer's error: if reading src failed, that's the root
	// cause, and it surfaces on the consumer side only as a generic
	// "io: read/write on closed pipe" (via CloseWithError) that loses the
	// original cause if we don't check producerErr first. A consumer-side
	// error (dst failing) is only reported when the producer succeeded.
	if producerErr != nil {
		return producerErr
	}
	return consumerErr
}

/*
BEST PRACTICES DEMONSTRATED
  - UpperReader transforms in the caller's buffer (p[:n]) instead of
    allocating a new one — zero extra allocations per Read call, true
    streaming behavior regardless of total stream size.
  - CountingWriter uses atomic.Int64 rather than a mutex-guarded int64: for
    a single counter with no other state to protect, an atomic is both
    simpler and faster than sync.Mutex + a plain field.
  - LineSplitWriter always returns (len(p), nil) from Write, honoring the
    io.Writer contract that a Writer must consume everything it's handed or
    explain why not — buffering a partial line is bookkeeping, not failure.
  - StreamPipeline closes the PipeWriter via a defer set up at the very top
    of the producer goroutine, guaranteeing the consumer never blocks
    forever even if a future edit adds an early return before the current
    single io.Copy call.
  - Errors are propagated from BOTH sides of the pipeline and disambiguated
    (producer error preferred, since a pipe-closed error on the consumer
    side is usually just a symptom of the real, producer-side failure).

ALTERNATIVE APPROACHES / TRADE-OFFS
  - Direct chain, io.Copy(dst, NewUpperReader(src)), no goroutines: simpler,
    fewer moving parts, and correct for the common case where src and dst
    are both fast (files, in-memory buffers). Loses the property that a
    blocked dst throttles reads from src independently of any explicit
    buffering — matters once either side can be slow or unbounded (a slow
    HTTP client, a network socket).
  - A buffered pipe (e.g. wrapping io.Pipe with your own bounded ring
    buffer, or using a buffered channel of []byte chunks) trades some
    backpressure precision for throughput: producer and consumer can run
    slightly ahead of each other instead of lockstepping on every Write, at
    the cost of bounded (but nonzero) extra memory and more code to get
    right. io.Pipe's unbuffered synchronous handoff is the simplest correct
    starting point; reach for a buffered variant only after profiling shows
    the lockstep handoff is the bottleneck.
  - LineSplitWriter's callback-based API forces synchronous processing on
    the writer's goroutine — onLine runs inline inside Write, so a slow
    onLine directly slows down whoever is writing. A channel-based variant
    (see the explanation file's stretch goals) decouples that at the cost of
    needing an explicit bounded/unbounded buffering decision for the
    channel.
  - bytes.Buffer instead of a raw []byte for LineSplitWriter's internal
    buffer: works too, but a raw slice with manual re-slicing (l.buf =
    l.buf[idx+1:]) avoids bytes.Buffer's extra internal bookkeeping for a
    case this simple; bytes.Buffer earns its keep when you also need
    io.Reader/io.Writer interop on the buffer itself.

TESTING NOTES
  - CountingWriter's concurrency guarantee is only meaningfully tested under
    `go test -race`: a single-goroutine test would pass even with a bare
    int64 field, which is exactly the bug this design is meant to prevent.
  - UpperReader's tests must use a small buffer size (e.g. io.CopyBuffer
    with a tiny buffer, or manual Read(p) calls with len(p) far smaller than
    the input) to actually exercise the multi-Read path — testing only with
    io.ReadAll's large internal buffer could hide an off-by-one in a version
    that (incorrectly) assumed one Read reads everything.
  - LineSplitWriter's split-across-multiple-Writes case is the one most
    likely to regress silently; a table-driven test that issues N separate
    Write calls with arbitrary split points (including splitting mid-CRLF,
    i.e. one Write ending in '\r' and the next starting with '\n') is worth
    more than many single-Write cases.
  - StreamPipeline tests must keep payloads small (a few KB) and assert
    completion within a short deadline (e.g. via a test timeout or a
    select on a done channel) — per the acceptance criteria, any hang in
    this package is almost certainly a missing PipeWriter.Close/
    CloseWithError, and a hanging test is the fastest way to surface that.

FAILURE MODES TO KNOW ABOUT
  - A src.Read that returns a permanent error (e.g. a closed file, a reset
    network connection) after some data: StreamPipeline's producer io.Copy
    stops, CloseWithError propagates that error to the consumer's Read, and
    StreamPipeline returns it — no goroutine leak, no partial silent
    success.
  - A dst.Write that fails partway through a large stream: the consumer's
    io.Copy returns that error; because it only surfaces once the producer
    has already been given every byte src has (io.Pipe applies backpressure,
    but doesn't cancel the producer), the producer goroutine still runs to
    completion (or its own error) and closes pw normally — no leak, just a
    slightly wasted read of src that's already in flight when dst dies.
  - Calling LineSplitWriter.Flush from a different goroutine than Write
    without external synchronization is a data race (this type, like
    bufio.Writer, is not concurrency-safe by design — wrap it in a mutex at
    the call site if multiple goroutines need to write through one
    instance).
*/
