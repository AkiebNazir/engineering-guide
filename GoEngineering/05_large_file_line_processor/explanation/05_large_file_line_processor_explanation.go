/*
Problem 05 — Large file line processor (bufio.Scanner limits, chunked reads,
memory-bounded parsing)

# WHAT WE'RE BUILDING

A small library for processing line-oriented files that may be far larger
than available memory, without ever loading the whole file at once:

  - `ScanLines`: a bufio.Scanner-based line processor with an explicit,
    caller-controlled maximum line size — and correct, identifiable error
    handling when a line exceeds it (Scanner's default limit is a common
    silent-failure trap in production code).
  - `CountLines`: a fast, O(1)-memory line counter using raw chunked reads
    (no Scanner, no per-line allocation) — the `wc -l` approach, useful when
    you need a count and nothing else and don't want per-line overhead.
  - `ReadUnboundedLines`: a bufio.Reader-based processor for the case where
    individual lines can be arbitrarily long and you cannot predeclare a
    max buffer size, trading Scanner's hard cap for per-line allocation.
  - `ProcessFile`: the real-world entry point — opens a file, guarantees
    Close, and wires ScanLines with context cancellation.

# WHY THIS MATTERS IN REAL SYSTEMS

`bufio.Scanner` is the default reach-for-it tool for line-oriented parsing
in Go, and it has a sharp edge nearly every engineer hits at least once in
production: its default token buffer is capped at 64KB (`bufio.MaxScanTokenSize`),
and when a single line exceeds it, `Scan()` returns `false` and
`Err()` returns `bufio.ErrTooLong` — which, if you don't check `Err()` after
the scan loop (a *very* easy thing to forget, since the loop just "ends"),
looks exactly like the file ended normally. That's a silent data-loss bug:
you process 90% of a log file and never find out the rest didn't run. This
problem is about knowing that limit exists, configuring it deliberately via
`Scanner.Buffer`, and having a fallback strategy (chunked reads or
`bufio.Reader`) for when a hard cap isn't acceptable at all — the same
category of decision you make choosing between a bounded worker pool and an
unbounded goroutine-per-request design: predictable resource use versus
raw flexibility.

# CONCEPTS COVERED

  - `bufio.Scanner` internals: default vs configured buffer size via
    `Scanner.Buffer(initial []byte, max int)`, `bufio.ErrTooLong`, and why
    `Err()` must always be checked after a `for scanner.Scan()` loop exits
  - `scanner.Bytes()` vs `scanner.Text()`: Bytes() aliases the scanner's
    internal buffer and is invalidated by the next Scan() call — a very
    common "looks correct, corrupts data under load" bug when a caller
    retains it past that point
  - Chunked reads via `io.Reader.Read` directly, without Scanner, for
    O(1)-memory processing when you don't need per-line boundaries at all
  - `bufio.Reader.ReadBytes`/`ReadString` as an alternative for unbounded
    line lengths, and the memory trade-off vs a hard Scanner cap
  - Context cancellation threaded through a tight read loop — checking
    `ctx.Err()` per iteration, not per line, when iterations are cheap and
    frequent, to bound how long a canceled call keeps running
  - Custom structured errors (`*LineError`) that identify exactly which
    line failed and wrap the underlying cause with `%w`, so callers can
    `errors.As`/`errors.Is` for both "which line" and "what kind of error"

# SPEC

	var ErrLineTooLong = errors.New("lineprocessor: line exceeds maximum buffer size")

	type LineError struct {
		LineNum int64
		Err     error
	}
	func (e *LineError) Error() string
	func (e *LineError) Unwrap() error

LineError identifies which 1-indexed line a failure occurred at. It wraps
either an error returned by a caller-supplied LineFunc, or ErrLineTooLong
when a line exceeds a configured maximum. `errors.As(err, &le)` must recover
the LineNum; `errors.Is(err, ErrLineTooLong)` (or the caller's own sentinel,
if that's what LineFunc returned) must still work through the wrap.

	type LineFunc func(lineNum int64, line []byte) error

LineFunc is called once per line (1-indexed). The line slice's validity
rules differ per function below — read each one's doc comment.

	func ScanLines(ctx context.Context, r io.Reader, maxLineBytes int, fn LineFunc) (int64, error)

Processes r line-by-line using bufio.Scanner, configured via Scanner.Buffer
so the maximum line size is exactly maxLineBytes (not the 64KB default).
Returns the number of lines successfully processed and, if any, the first
error encountered — from fn, from a line exceeding maxLineBytes (wrapped as
*LineError around ErrLineTooLong), from the underlying reader, or from ctx
being canceled. The line slice passed to fn is only valid until fn returns
(it aliases the Scanner's internal buffer) — fn must copy it if it needs to
retain the data.

	func CountLines(ctx context.Context, r io.Reader) (int64, error)

Counts newline ('\n') bytes in r using fixed-size chunked reads — no
per-line allocation, no Scanner, O(1) memory regardless of file size or
individual line length. Matches `wc -l` semantics: a final line with no
trailing '\n' is not counted. ctx is checked once per chunk (not
per-byte/per-line — chunks are the natural, cheap granularity here).

	func ReadUnboundedLines(ctx context.Context, r io.Reader, fn LineFunc) (int64, error)

Processes r line-by-line using bufio.Reader.ReadBytes, with NO maximum line
size — a single line may be arbitrarily long; memory for that one line
grows to fit it (this is the trade-off vs ScanLines: no silent truncation
or hard error on a huge line, but also no predictable memory ceiling — use
this only when you've decided that trade-off is the right one, e.g.
ingesting a feed with rare-but-legitimate huge lines). The line slice
passed to fn is only valid until fn returns; fn must copy it to retain it.
ctx is checked once per line.

	func ProcessFile(ctx context.Context, path string, maxLineBytes int, fn LineFunc) (int64, error)

Opens path, guarantees the file is closed (even on error / panic paths),
and processes it via ScanLines. This is the entry point real callers use;
ScanLines/CountLines/ReadUnboundedLines take io.Reader so they're testable
against in-memory data without touching a filesystem.

# ACCEPTANCE CRITERIA

  - ScanLines correctly processes a file whose longest line is smaller than
    maxLineBytes, and returns a *LineError wrapping ErrLineTooLong
    identifying the correct 1-indexed line number when a line exceeds
    maxLineBytes — including a line that exceeds the *default* 64KB Scanner
    limit but fits within a larger maxLineBytes you configure (proves
    Scanner.Buffer is actually being used, not just the zero-value
    Scanner).
  - CountLines returns the correct count for: an empty reader (0), a file
    with no trailing newline (last partial line NOT counted, matching
    `wc -l`), and a file that is a single line far larger than any
    reasonable in-memory chunk size (proves it never buffers a whole line).
  - ReadUnboundedLines correctly processes a single line larger than
    bufio.MaxScanTokenSize (64KB) with NO configured maximum and no error —
    the exact case that would fail (or require reconfiguration) in
    ScanLines.
  - A LineFunc that returns an error stops processing immediately (no
    further lines processed) and the returned error unwraps via
    errors.As to a *LineError with the correct LineNum and via errors.Is to
    the caller's original sentinel error.
  - All three iterate-and-call functions return promptly (well under a
    second in tests) when ctx is already canceled or canceled during
    processing — no function processes the entire remaining input after
    cancellation.
  - CRLF line endings are stripped correctly (no trailing '\r' left in the
    line bytes passed to fn) in both ScanLines (bufio.ScanLines already
    does this) and ReadUnboundedLines (must be handled explicitly).
*/
package lineprocessor

import (
	"context"
	"errors"
	"io"
)

// ErrLineTooLong is wrapped by a *LineError when a line exceeds the
// maxLineBytes configured for ScanLines.
var ErrLineTooLong = errors.New("lineprocessor: line exceeds maximum buffer size")

// LineError identifies which line a processing failure occurred at.
type LineError struct {
	LineNum int64
	Err     error
}

// TODO: implement Error() string — format as something like
// "lineprocessor: line %d: %v" combining LineNum and Err.
func (e *LineError) Error() string {
	panic("TODO: implement LineError.Error")
}

// TODO: implement Unwrap() error — return e.Err so errors.Is/errors.As see
// through this wrapper to both ErrLineTooLong and any caller-supplied
// sentinel error returned from a LineFunc.
func (e *LineError) Unwrap() error {
	panic("TODO: implement LineError.Unwrap")
}

// LineFunc is called once per line. line is 1-indexed via lineNum. The
// validity of the line slice past the call depends on which processing
// function invoked it — see each function's doc comment; assume it is NOT
// safe to retain without copying unless documented otherwise.
type LineFunc func(lineNum int64, line []byte) error

// ScanLines processes r line-by-line via bufio.Scanner with an explicit
// maximum line size, returning the count of lines processed and the first
// error encountered (if any).
//
// TODO: implement.
//  1. Check ctx.Err() before starting.
//  2. bufio.NewScanner(r), then scanner.Buffer(...) to raise the max token
//     size to maxLineBytes — remember the initial buffer passed to Buffer
//     is just a starting capacity hint; max is the hard cap that replaces
//     bufio.MaxScanTokenSize (64KB).
//  3. Loop `for scanner.Scan()`, checking ctx.Err() each iteration (return
//     promptly on cancellation), incrementing a 1-indexed line counter,
//     and calling fn(lineNum, scanner.Bytes()) — on a fn error, wrap it in
//     a *LineError with the current line number and return immediately.
//  4. After the loop, ALWAYS check scanner.Err() — this is the step that's
//     easy to skip and exactly how ErrTooLong gets silently swallowed. If
//     it's bufio.ErrTooLong, wrap it as a *LineError{LineNum: lineNum+1,
//     Err: ErrLineTooLong} (the failing line is the NEXT one, since Scan()
//     returned false without yielding it). Any other non-nil Err() should
//     be wrapped with context too.
func ScanLines(ctx context.Context, r io.Reader, maxLineBytes int, fn LineFunc) (int64, error) {
	panic("TODO: implement ScanLines")
}

// CountLines counts '\n' bytes in r using fixed-size chunked reads, with
// O(1) memory regardless of file size or individual line length. Matches
// `wc -l` semantics: a trailing partial line with no '\n' is not counted.
//
// TODO: implement.
//  1. Check ctx.Err() before starting.
//  2. Allocate ONE fixed-size buffer (e.g. 64KB) outside any loop and reuse
//     it across Read calls — allocating inside the loop defeats the whole
//     point of "O(1) memory, no per-line allocation".
//  3. Loop: r.Read(buf), count '\n' occurrences in buf[:n] (bytes.Count is
//     the idiomatic, fast way), check ctx.Err() once per chunk (not more
//     often — that's needless overhead for something this tight), handle
//     io.EOF as normal completion (not an error) per the io.Reader
//     contract, and remember Read can return n>0 AND err on the same call
//     (count before checking err).
func CountLines(ctx context.Context, r io.Reader) (int64, error) {
	panic("TODO: implement CountLines")
}

// ReadUnboundedLines processes r line-by-line via bufio.Reader.ReadBytes,
// with no maximum line length — a single line may consume as much memory
// as it needs. Use only when you've deliberately decided you need that
// flexibility over ScanLines's predictable cap.
//
// TODO: implement.
//  1. Check ctx.Err() before starting.
//  2. bufio.NewReader(r) (default internal buffer size is fine — that's
//     just the read-ahead chunk size, unrelated to the max line length,
//     which here is unbounded).
//  3. Loop: br.ReadBytes('\n'). ReadBytes returns data read so far AND an
//     error together when it hits EOF before finding the delimiter — like
//     io.Reader, you must process non-empty data before checking err.
//     Strip the trailing '\n' (and a preceding '\r', for CRLF) before
//     calling fn. On io.EOF with no trailing delimiter found: if there's
//     leftover data, treat it as one final line and call fn, then stop
//     normally (not an error) — an unterminated final line is valid input,
//     unlike ScanLines's Scanner semantics point above about CountLines
//     (CountLines and ReadUnboundedLines intentionally differ: one is a
//     count matching `wc -l`, the other actually delivers every line's
//     content to the caller, including a trailing partial one).
//  4. Check ctx.Err() once per line (lines are the natural granularity
//     here, since a line can be arbitrarily expensive/large already).
//  5. On a fn error, wrap in *LineError with the current line number and
//     return immediately.
func ReadUnboundedLines(ctx context.Context, r io.Reader, fn LineFunc) (int64, error) {
	panic("TODO: implement ReadUnboundedLines")
}

// ProcessFile opens path, guarantees it is closed, and processes it via
// ScanLines with the given maxLineBytes.
//
// TODO: implement.
//  1. os.Open(path); wrap any error with context (which path failed).
//  2. defer f.Close() — and in a stricter version you might want to check
//     the deferred Close's error too (see problem 06's atomic file store
//     for the "close error matters" pattern), but for a read-only file a
//     failed Close basically never indicates lost data, so a simple defer
//     is the right level of rigor here; document that choice rather than
//     silently doing the bare minimum.
//  3. Call ScanLines(ctx, f, maxLineBytes, fn) and return its result.
func ProcessFile(ctx context.Context, path string, maxLineBytes int, fn LineFunc) (int64, error) {
	panic("TODO: implement ProcessFile")
}

/*
HINTS

  - `bufio.MaxScanTokenSize` (64KB) is the Scanner's default max token size
    if you never call Buffer — worth reading the stdlib source/doc comment
    for `Scanner.Buffer` once; it's short and exactly explains the
    initial-capacity-vs-max-cap distinction ScanLines needs.
  - `errors.Is(scanner.Err(), bufio.ErrTooLong)` is the correct check — do
    not string-compare the error message.
  - `bytes.Count(buf, []byte{'\n'})` is the fast, allocation-free way to
    count newlines in a chunk for CountLines.
  - `bufio.Reader.ReadBytes` and `ReadString` both grow their own internal
    accumulation buffer as needed when a line is longer than the reader's
    internal read-ahead buffer — that growth is exactly where
    ReadUnboundedLines gets its "no hard cap" property, and exactly why it
    has no memory ceiling either.
  - For all three ctx-aware functions, checking ctx.Err() is cheap (an
    atomic-ish read internally) but still shouldn't be done more often than
    the natural iteration granularity (per chunk for CountLines, per line
    for the other two) — checking per-byte would be wasteful for no
    benefit.

COMMON PITFALLS

  - Forgetting to check `scanner.Err()` after a `for scanner.Scan()` loop —
    the loop just stops, indistinguishable at a glance from a clean EOF,
    which is exactly how ErrTooLong (and any underlying read error) goes
    unnoticed in real codebases.
  - Retaining `scanner.Bytes()` (or a ReadBytes result) past the point
    where it's valid — e.g. appending it directly to a slice the caller
    keeps around — without copying first; both alias reused internal
    buffers.
  - Allocating a new buffer on every iteration of CountLines's read loop
    instead of reusing one — turns an O(1)-memory, low-GC-pressure function
    into one that pressures the GC proportionally to file size, defeating
    its purpose.
  - Checking `err != nil` before processing `n` bytes from a Read/ReadBytes
    call — drops the final chunk/line exactly like the UpperReader pitfall
    in problem 04; the same io.Reader contract applies here.
  - Treating CountLines and ReadUnboundedLines's "final unterminated line"
    behavior as interchangeable — they're deliberately different (count vs
    deliver-content) and conflating them is a spec bug, not a style choice.

STRETCH GOALS

  - Add a `ScanLinesParallel` that splits a file into N byte-range chunks
    (seeking to the nearest line boundary after each split point) and
    processes chunks concurrently with an errgroup, preserving overall line
    ordering in the results — a realistic pattern for multi-GB log
    processing on a multi-core box.
  - Add progress reporting: a callback invoked every N processed lines or
    every N bytes read, useful for a CLI progress bar on a large file.
  - Make ReadUnboundedLines accept an optional soft warning threshold
    (log/report, don't fail) for exceptionally long lines, as a middle
    ground between ScanLines's hard cap and no limit at all.
  - Benchmark ScanLines vs CountLines vs ReadUnboundedLines against the
    same large generated file (`go test -bench`) to make the per-line
    allocation cost of each approach concrete rather than theoretical.
*/
