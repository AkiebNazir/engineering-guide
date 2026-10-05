/*
Problem 04 — Custom io.Reader/io.Writer (streaming transforms, io.Pipe, backpressure)

WHAT WE'RE BUILDING

A small library of composable streaming primitives built entirely on
`io.Reader`/`io.Writer`:

  - `UpperReader`: wraps an io.Reader, uppercasing bytes as they stream
    through, with NO full-buffer copy of the underlying data.
  - `CountingWriter`: wraps an io.Writer, counting bytes written through
    it (a common production need — total bytes sent, checksums, etc.).
  - `LineSplitWriter` (or similar): a Writer that buffers arbitrary
    chunks and invokes a callback once per complete line, handling writes
    that split a line across multiple Write calls.
  - A producer/consumer pipeline wired with `io.Pipe`, demonstrating real
    backpressure: a slow reader must cause a fast writer to block, not
    buffer unboundedly in memory.

# WHY THIS MATTERS IN REAL SYSTEMS

`io.Reader`/`io.Writer` are the single most important interfaces in Go's
standard library — nearly everything that moves bytes (files, network
connections, compressors, hashers, HTTP bodies, `bytes.Buffer`) implements
them, which is precisely what lets you compose a gzip writer, a TLS
connection, and a rate limiter into one pipeline without any of them
knowing about the others. The skill this problem builds — wrapping an
existing Reader/Writer to add behavior while staying streaming
(constant memory, not "load it all, transform it, write it all") — is
what separates code that works on a 10KB test fixture from code that
survives a 10GB production file or an unbounded network stream.
`io.Pipe` specifically demonstrates *backpressure*: it is a synchronous,
unbuffered in-memory pipe where a Write blocks until a matching Read
consumes it — the correct primitive when you need to connect a producer
and consumer as goroutines without an unbounded buffer growing between
them.

CONCEPTS COVERED

  - Implementing `io.Reader`: `Read(p []byte) (n int, err error)` and its
    exact contract (may return n>0 AND err on the same call; io.EOF
    semantics; a Read is allowed to return less than len(p) even if more
    data is available)
  - Implementing `io.Writer`: `Write(p []byte) (n int, err error)` and its
    contract (must consume all of p or return an error explaining why not
    — a Writer that silently drops bytes without erroring is a bug)
  - `io.Pipe` for backpressure and goroutine-to-goroutine streaming
  - Composing readers/writers: `io.Copy`, `io.MultiWriter`, `io.TeeReader`
    as prior art to model your own types after
  - Buffering split/partial data across multiple Write calls (the
    LineSplitWriter's core challenge)
  - Goroutine lifecycle: a `io.Pipe` producer goroutine must always call
    `PipeWriter.Close` or `CloseWithError`, or a reader blocks forever
  - Error propagation through a chain of wrapped readers/writers

# SPEC

	type UpperReader struct { ... }
	func NewUpperReader(r io.Reader) *UpperReader
	func (u *UpperReader) Read(p []byte) (int, error)

UpperReader.Read must uppercase ASCII bytes in-place within the caller's
buffer `p` after delegating to the wrapped reader — it must NOT read the
entire underlying stream into memory first. It should transparently
forward io.EOF and any other error from the wrapped reader.

	type CountingWriter struct { ... }
	func NewCountingWriter(w io.Writer) *CountingWriter
	func (c *CountingWriter) Write(p []byte) (int, error)
	func (c *CountingWriter) Count() int64

CountingWriter must be safe to read Count() from a different goroutine
than the one calling Write (use atomic, not a bare int64 field) since a
production use case is a metrics goroutine polling Count() while writes
happen concurrently on the hot path.

	type LineSplitWriter struct { ... }
	func NewLineSplitWriter(onLine func(line string)) *LineSplitWriter
	func (l *LineSplitWriter) Write(p []byte) (int, error)
	func (l *LineSplitWriter) Flush() error // handle a trailing partial line with no final \n

LineSplitWriter must correctly handle a single logical line arriving
split across N separate Write calls (e.g. Write("abc"), Write("def\n")
must invoke onLine("abcdef") exactly once, not twice or with garbage).
Lines are delimited by '\n'; a trailing '\r' before '\n' should be
stripped (CRLF handling). Flush delivers any buffered trailing partial
line (with no newline) to onLine and must be idempotent (calling it twice
after all data is written doesn't double-deliver).

	func StreamPipeline(src io.Reader, dst io.Writer) error

StreamPipeline demonstrates io.Pipe-based backpressure: it reads from
src, transforms through UpperReader, and writes to dst, but structured so
a producer goroutine writes into a PipeWriter and a consumer goroutine
(or the caller) reads from the PipeReader — i.e. don't just chain
io.Copy(dst, NewUpperReader(src)) directly (that's the trivial,
non-goroutine version); build the version that actually exercises
io.Pipe's synchronous handoff between two goroutines, and correctly
propagates any read/write error from either side back to the caller via
`CloseWithError`.

ACCEPTANCE CRITERIA

  - UpperReader passes data through correctly for buffer sizes smaller
    than the input (forces multiple Read calls) and exactly matches
    strings.ToUpper's ASCII behavior (non-ASCII bytes pass through
    unchanged — no need to handle full Unicode case folding).
  - CountingWriter's count is correct after many small concurrent writes
    from multiple goroutines (verify with `go test -race`).
  - LineSplitWriter handles: a line in one Write, a line split across
    multiple Writes, multiple lines in one Write, CRLF line endings, and
    a trailing partial line delivered only via Flush.
  - StreamPipeline correctly propagates an error from a failing src Read
    or dst Write back to the caller (not silently swallowed, not a
    goroutine leak on error).
  - No test in this package needs more than a few KB of test data or
    blocks for more than a fraction of a second — if a test hangs, that's
    almost certainly a missing PipeWriter.Close/CloseWithError.
*/
package streamtransform

import (
	"io"
)

// UpperReader wraps an io.Reader, uppercasing ASCII bytes as they stream
// through without buffering the whole underlying stream.
type UpperReader struct {
	// TODO: fields (just the wrapped reader)
}

// NewUpperReader returns an UpperReader wrapping r.
func NewUpperReader(r io.Reader) *UpperReader {
	panic("TODO: implement NewUpperReader")
}

// Read implements io.Reader: delegates to the wrapped reader into p, then
// uppercases the bytes actually read (p[:n]) in place.
//
// TODO: implement. Remember the io.Reader contract: it is valid (and
// common) for the underlying Read to return n>0 and a non-nil err
// (including io.EOF) on the SAME call — you must still uppercase and
// return those n bytes, not discard them because err != nil.
func (u *UpperReader) Read(p []byte) (int, error) {
	panic("TODO: implement UpperReader.Read")
}

// CountingWriter wraps an io.Writer, atomically counting bytes written.
type CountingWriter struct {
	w io.Writer
	// TODO: an atomic counter field
}

// NewCountingWriter returns a CountingWriter wrapping w.
func NewCountingWriter(w io.Writer) *CountingWriter {
	panic("TODO: implement NewCountingWriter")
}

// Write implements io.Writer: delegates to the wrapped writer and
// atomically adds the number of bytes actually written (not len(p) — if
// the underlying Write short-writes and errors, count only what was
// actually written) to the running count.
// TODO: implement.
func (c *CountingWriter) Write(p []byte) (int, error) {
	panic("TODO: implement CountingWriter.Write")
}

// Count returns the total bytes written so far. Safe to call
// concurrently with Write.
// TODO: implement using an atomic load.
func (c *CountingWriter) Count() int64 {
	panic("TODO: implement CountingWriter.Count")
}

// LineSplitWriter buffers arbitrary write chunks and invokes onLine once
// per complete line (delimited by '\n', with an optional preceding '\r'
// stripped).
type LineSplitWriter struct {
	onLine func(line string)
	// TODO: a buffer for partial lines spanning multiple Write calls, and
	// a flag/marker for Flush idempotency
}

// NewLineSplitWriter returns a LineSplitWriter that invokes onLine for
// each complete line seen across however many Write calls it takes to
// assemble one.
func NewLineSplitWriter(onLine func(line string)) *LineSplitWriter {
	panic("TODO: implement NewLineSplitWriter")
}

// Write implements io.Writer.
//
// TODO: implement. Append p to an internal buffer, then repeatedly find
// and extract '\n'-delimited lines from the front of the buffer, stripping
// a trailing '\r' from each, invoking onLine for each, and leaving any
// remaining partial line (no trailing '\n' yet) in the buffer for the
// next Write or Flush. Must always return (len(p), nil) — this Writer
// never rejects data because "line splitting" isn't an error condition
// in the io.Writer sense.
func (l *LineSplitWriter) Write(p []byte) (int, error) {
	panic("TODO: implement LineSplitWriter.Write")
}

// Flush delivers any buffered trailing partial line (one with no
// terminating '\n') to onLine, if any bytes remain buffered. Idempotent:
// calling Flush again after it already delivered (or after there was
// nothing buffered) does nothing.
// TODO: implement.
func (l *LineSplitWriter) Flush() error {
	panic("TODO: implement LineSplitWriter.Flush")
}

// StreamPipeline reads from src, uppercases via UpperReader, and writes
// to dst, using an io.Pipe to hand data between a producer goroutine
// (reading src, writing the PipeWriter) and a consumer (reading the
// PipeReader, writing dst) — demonstrating io.Pipe's synchronous,
// backpressure-providing handoff rather than a direct io.Copy chain.
//
// TODO: implement:
//  1. pr, pw := io.Pipe()
//  2. In a goroutine: io.Copy(pw, NewUpperReader(src)), then
//     pw.CloseWithError(err) with the io.Copy error (nil is fine — Close
//     vs CloseWithError(nil) are equivalent, but CloseWithError makes the
//     intent explicit either way).
//  3. In the calling goroutine (or another one — your call, document
//     it): io.Copy(dst, pr), capturing its error.
//  4. Wait for both to finish (if you used a second goroutine for step 3,
//     you need a way to wait for it — a channel or sync.WaitGroup) and
//     return whichever error is non-nil (prefer the earliest one if both
//     failed).
func StreamPipeline(src io.Reader, dst io.Writer) error {
	panic("TODO: implement StreamPipeline")
}

/*
HINTS

  - `io.Reader.Read`'s contract explicitly permits returning n>0 with a
    non-nil error on the same call (see the io.Reader doc comment in the
    stdlib itself) — callers are required to process the n bytes
    returned before checking/handling err. A reader wrapper that doesn't
    handle this (e.g. `if err != nil { return 0, err }` before looking at
    n) silently drops the last chunk of every stream that doesn't end
    exactly on a Read boundary.
  - `bytes.IndexByte(buf, '\n')` is the idiomatic, fast way to find line
    boundaries in a buffer — much faster than a manual byte-by-byte scan
    or bytes.Split (which would require the whole buffer to already be
    complete, which it isn't, mid-stream).
  - A goroutine writing into an io.Pipe MUST close the PipeWriter (Close
    or CloseWithError) when done, or the corresponding PipeReader's Read
    blocks forever — this is the single most common io.Pipe bug and
    exactly why "no test should hang" is called out in the acceptance
    criteria.
  - `strings.Builder` or a `[]byte` buffer both work for LineSplitWriter's
    internal buffer; a `[]byte` avoids an extra allocation on the final
    string conversion path if you're careful, but strings.Builder is
    perfectly fine and more readable — this problem doesn't need to be
    allocation-obsessive.

COMMON PITFALLS

  - Uppercasing bytes into a NEW buffer instead of in-place in p — works,
    but doubles the memory traffic and often introduces an unnecessary
    allocation per Read call; the whole point of streaming through the
    caller-provided buffer is to avoid that.
  - CountingWriter using a plain `int64` field instead of `atomic.Int64` —
    passes single-goroutine tests, then `go test -race` (or production
    under real concurrent load) reveals the bug immediately.
  - LineSplitWriter losing a trailing partial line because the caller
    forgot to call Flush — document loudly that Flush is mandatory for
    correctness on any non-newline-terminated input, the same way
    bufio.Writer requires a final Flush.
  - A pipeline goroutine that panics or returns early without closing the
    PipeWriter (e.g. an early `return err` before reaching the
    close/defer) — always set up the close via `defer` immediately after
    creating the pipe, not as the last line of the function body.
  - Forgetting to propagate BOTH sides' errors in StreamPipeline — if only
    the consumer's io.Copy error is returned, a failure reading src (which
    surfaces as an error on the PRODUCER side, propagated to the consumer
    only as a generic "io: read/write on closed pipe" via
    CloseWithError) gets lost or misreported.

STRETCH GOALS

  - Implement a `RateLimitedWriter` using golang.org/x/time/rate (already
    vendored) that blocks Write calls to enforce a maximum bytes/sec.
  - Implement a `TeeLineWriter` that both forwards bytes unchanged to an
    underlying io.Writer AND invokes onLine per line, in one wrapper.
  - Make LineSplitWriter emit lines via a channel instead of a callback,
    and compare the two APIs' backpressure characteristics (a callback
    forces synchronous processing on the writer's goroutine; a channel
    lets the consumer pull at its own pace but needs an unbounded or
    bounded buffer decision).
  - Add a max-line-length guard to LineSplitWriter that errors instead of
    buffering unboundedly on a pathological input with no newlines at
    all (mirrors bufio.Scanner's `ErrTooLong` — foreshadows problem 05).
*/
