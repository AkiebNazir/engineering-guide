// Package lineprocessor is the reference implementation of Problem 05:
// memory-bounded line processing for files that may be far larger than
// available RAM. Read the header comment in
// ../explanation/05_large_file_line_processor_explanation.go first — it has
// the full spec and rationale; this file focuses on *how* and *why* each
// line is written the way it is.
package lineprocessor

import (
	"bufio"
	"bytes"
	"context"
	"errors"
	"fmt"
	"io"
	"os"
)

// ErrLineTooLong is wrapped by a *LineError when a line exceeds the
// maxLineBytes configured for ScanLines.
var ErrLineTooLong = errors.New("lineprocessor: line exceeds maximum buffer size")

// LineError identifies which line a processing failure occurred at.
//
// A dedicated error type (rather than just fmt.Errorf-ing the line number
// into a string) lets callers programmatically recover the line number via
// errors.As, while Unwrap still lets errors.Is see through to the
// underlying cause (ErrLineTooLong, or whatever sentinel a caller's own
// LineFunc returned) — you get both "which line" and "what kind of error"
// without parsing a message string.
type LineError struct {
	LineNum int64
	Err     error
}

// Error implements the error interface.
func (e *LineError) Error() string {
	return fmt.Sprintf("lineprocessor: line %d: %v", e.LineNum, e.Err)
}

// Unwrap exposes the underlying error so errors.Is/errors.As traverse
// through LineError to ErrLineTooLong or a caller's own sentinel.
func (e *LineError) Unwrap() error {
	return e.Err
}

// LineFunc is called once per line. line is 1-indexed via lineNum. The line
// slice is only valid until fn returns — ScanLines and ReadUnboundedLines
// both hand it a slice aliasing an internal buffer that gets reused/grown
// on the next line, so fn must copy it (e.g. append([]byte(nil), line...))
// to retain it past the call.
type LineFunc func(lineNum int64, line []byte) error

// scanChunkSize is the read-ahead chunk CountLines uses. 64KB balances
// syscall overhead (bigger chunks mean fewer Read calls) against per-call
// stack/cache footprint; there's nothing magic about this exact number for
// correctness — it only affects throughput.
const scanChunkSize = 64 * 1024

// ScanLines processes r line-by-line via bufio.Scanner, configured with an
// explicit maximum line size instead of relying on the 64KB default.
//
// The ctx.Err() check inside the loop is what makes this cancellable at
// all — bufio.Scanner has no context awareness of its own, so without this
// check a canceled ctx would be silently ignored until the scan finishes on
// its own (potentially processing gigabytes of data the caller no longer
// wants).
func ScanLines(ctx context.Context, r io.Reader, maxLineBytes int, fn LineFunc) (int64, error) {
	if err := ctx.Err(); err != nil {
		return 0, err
	}

	scanner := bufio.NewScanner(r)
	// The initial buffer just sets starting capacity (Scanner grows it as
	// needed up to max); using min(scanChunkSize, maxLineBytes) avoids
	// over-allocating up front when a caller configures a small
	// maxLineBytes, while still starting reasonably large for the common
	// case.
	initial := scanChunkSize
	if maxLineBytes < initial {
		initial = maxLineBytes
	}
	scanner.Buffer(make([]byte, 0, initial), maxLineBytes)

	var lineNum int64
	for scanner.Scan() {
		if err := ctx.Err(); err != nil {
			return lineNum, err
		}
		lineNum++
		if err := fn(lineNum, scanner.Bytes()); err != nil {
			return lineNum, &LineError{LineNum: lineNum, Err: err}
		}
	}

	// This check is the single most important line in this function: the
	// for-loop above exits identically (Scan() returns false) whether the
	// input ended cleanly OR a line exceeded maxLineBytes OR the
	// underlying reader errored. Skipping this check is how ErrTooLong (or
	// any read failure) silently masquerades as a clean, complete parse.
	if err := scanner.Err(); err != nil {
		if errors.Is(err, bufio.ErrTooLong) {
			// The line that triggered ErrTooLong was never yielded by
			// Scan(), so it's the line AFTER the last one we successfully
			// processed.
			return lineNum, &LineError{LineNum: lineNum + 1, Err: ErrLineTooLong}
		}
		return lineNum, fmt.Errorf("lineprocessor: scan: %w", err)
	}

	return lineNum, nil
}

// CountLines counts '\n' bytes in r using one reused fixed-size buffer, for
// O(1) memory regardless of file size or individual line length. Matches
// `wc -l` semantics: a trailing partial line with no '\n' is not counted.
func CountLines(ctx context.Context, r io.Reader) (int64, error) {
	if err := ctx.Err(); err != nil {
		return 0, err
	}

	// Allocated ONCE, outside the loop, and reused for every Read call —
	// this is what makes the function's memory use independent of the
	// input size. Allocating inside the loop would turn a streaming
	// O(1)-memory function into one that pressures the GC proportionally
	// to how many chunks the file contains.
	buf := make([]byte, scanChunkSize)

	var count int64
	for {
		n, err := r.Read(buf)
		// Count before checking err: Read is permitted to return n>0
		// together with a non-nil error (including io.EOF) on the same
		// call, and the final chunk of data is exactly where that most
		// often happens.
		count += int64(bytes.Count(buf[:n], []byte{'\n'}))

		if err == io.EOF {
			return count, nil
		}
		if err != nil {
			return count, fmt.Errorf("lineprocessor: count: %w", err)
		}

		// Checked once per chunk, not per byte — chunks are the natural,
		// cheap granularity for this tight a loop; per-byte would add
		// meaningful overhead for no observable benefit (a canceled ctx
		// is still noticed within one chunk's worth of I/O, i.e.
		// effectively immediately).
		if err := ctx.Err(); err != nil {
			return count, err
		}
	}
}

// ReadUnboundedLines processes r line-by-line via bufio.Reader.ReadBytes,
// with no maximum line length — memory for a single line grows to fit it,
// however large it is. This is the deliberate trade-off against ScanLines:
// no ErrTooLong, no configuration needed up front, but also no predictable
// memory ceiling.
func ReadUnboundedLines(ctx context.Context, r io.Reader, fn LineFunc) (int64, error) {
	if err := ctx.Err(); err != nil {
		return 0, err
	}

	br := bufio.NewReader(r)
	var lineNum int64

	for {
		// ReadBytes accumulates into its own growable buffer until it
		// finds '\n' or hits EOF — the delimiter is included in the
		// returned slice when found. Like Read/Write, this can return
		// data AND a non-nil error together (typically io.EOF with a
		// final line that has no trailing '\n'), so we process `line`
		// before branching on err.
		line, err := br.ReadBytes('\n')

		if len(line) > 0 {
			line = bytes.TrimSuffix(line, []byte("\n"))
			line = bytes.TrimSuffix(line, []byte("\r")) // CRLF handling
			lineNum++
			if ferr := fn(lineNum, line); ferr != nil {
				return lineNum, &LineError{LineNum: lineNum, Err: ferr}
			}
		}

		if err == io.EOF {
			return lineNum, nil
		}
		if err != nil {
			return lineNum, fmt.Errorf("lineprocessor: read: %w", err)
		}

		// Checked once per line: unlike CountLines's fixed-size chunks, a
		// "line" here can already be arbitrarily expensive to have
		// produced, so per-line is the right granularity — finer-grained
		// checks would add cost without meaningfully improving
		// cancellation latency.
		if err := ctx.Err(); err != nil {
			return lineNum, err
		}
	}
}

// ProcessFile opens path, guarantees it is closed, and processes it via
// ScanLines with the given maxLineBytes.
func ProcessFile(ctx context.Context, path string, maxLineBytes int, fn LineFunc) (int64, error) {
	f, err := os.Open(path)
	if err != nil {
		return 0, fmt.Errorf("lineprocessor: open %q: %w", path, err)
	}
	// A failed Close on a read-only file descriptor essentially never
	// indicates lost data (unlike a write path, e.g. problem 06's
	// WriteFile, where a Close error can mean buffered data never made it
	// to disk) — so a plain defer, without capturing and surfacing the
	// Close error, is the appropriate level of rigor here. Worth stating
	// explicitly rather than leaving readers to wonder if it was an
	// oversight.
	defer f.Close()

	return ScanLines(ctx, f, maxLineBytes, fn)
}

/*
BEST PRACTICES DEMONSTRATED
  - scanner.Err() is checked immediately after every `for scanner.Scan()`
    loop, distinguishing bufio.ErrTooLong (via errors.Is, not string
    matching) from other read failures, and reporting which line it
    happened at.
  - CountLines allocates its chunk buffer exactly once, outside the read
    loop, keeping the function's memory footprint independent of input
    size — the whole point of a "large file" processor.
  - Both Read (io.Reader) and ReadBytes (bufio.Reader) results are
    processed for their data BEFORE branching on their error, honoring the
    contract that n>0/non-empty-data and a terminal error can arrive on the
    same call.
  - ctx.Err() is checked at a granularity matched to the cost of each
    iteration: per-chunk in CountLines, per-line in ScanLines and
    ReadUnboundedLines — neither so coarse that cancellation is slow to
    take effect, nor so fine it adds measurable overhead.
  - LineError wraps the underlying cause via Unwrap, so callers can recover
    structured detail (LineNum) with errors.As while errors.Is still works
    through the chain for sentinel checks.

ALTERNATIVE APPROACHES / TRADE-OFFS
  - ScanLines vs ReadUnboundedLines is the central trade-off this problem
    teaches: a hard, predictable memory ceiling with an explicit failure
    mode (ScanLines) versus no ceiling and no failure mode for line length,
    at the cost of an attacker- or bad-data-controlled line being able to
    grow memory usage without bound. Pick ScanLines whenever the input
    isn't fully trusted (uploaded files, external feeds); ReadUnboundedLines
    is reasonable for trusted internal data where you've already ruled out
    the unbounded-growth risk.
  - CountLines vs `ScanLines` for counting: CountLines is faster and does
    zero per-line allocation because it never materializes individual
    lines at all — use it whenever you only need a count. The moment you
    need to inspect line content, ScanLines/ReadUnboundedLines are
    required; there's no way to get per-line semantics without the
    per-line cost.
  - A memory-mapped file (`golang.org/x/exp/mmap` or syscall.Mmap) can beat
    all three approaches for repeated random-access scans of the same huge
    file (the OS handles paging, no explicit chunked reads), but adds
    platform-specific complexity and doesn't fit a streaming/pipe use case
    (stdin, a network body) the way io.Reader-based processing does.
  - A worker-pool / parallel chunk-split approach (see the explanation
    file's stretch goals) trades implementation complexity for
    throughput on multi-core machines with genuinely large files — not
    worth it below a few hundred MB where I/O, not CPU, is the bottleneck.

TESTING NOTES
  - ScanLines's ErrTooLong test must use a maxLineBytes SMALLER than the
    offending line but configure it explicitly (not rely on the 64KB
    default) so the test also proves Scanner.Buffer is actually wired up —
    a bug that ignored maxLineBytes entirely could otherwise pass a test
    that only checks "some error occurs" on a >64KB line.
  - ReadUnboundedLines's key test is a single line LARGER than
    bufio.MaxScanTokenSize (64KB) processed with no error — the exact case
    where ScanLines (with a small/default max) would fail, proving the two
    functions' trade-off is real and not just documented.
  - Context-cancellation tests should use a reader that can produce
    effectively unbounded data (e.g. an io.Reader wrapping
    strings.NewReader in a loop, or a custom infinite reader) and assert
    the function returns quickly after ctx is canceled partway through —
    not that it eventually finishes the whole (large) input.
  - CountLines's "single huge line, no memory blowup" test can't easily
    assert on actual RSS from within a unit test; instead assert
    correctness (right count) while feeding it a reader that generates data
    on the fly (not a pre-materialized giant byte slice) — if the test
    itself needed to hold the whole line in memory to construct it, it
    wouldn't be proving the point.

FAILURE MODES TO KNOW ABOUT
  - A line at exactly maxLineBytes (no newline within that many bytes) in
    ScanLines: still triggers ErrTooLong, because Scanner's max is the
    largest TOKEN (line) it will buffer, and a token needs room for the
    delimiter search to complete — off-by-one behavior worth testing
    explicitly if a caller's code depends on an exact boundary.
  - ReadUnboundedLines on a pathological, endless single line (e.g. a
    corrupted file with no '\n' at all, or an attacker deliberately
    sending one): the function will grow the accumulation buffer without
    bound until memory is exhausted or the reader itself errors/closes —
    exactly the risk called out above; never point this function at
    untrusted input without an upstream size limit (e.g. an
    io.LimitReader wrapping r).
  - CountLines and ReadUnboundedLines disagree on purpose about a
    trailing unterminated final line (not counted vs delivered as content)
    — callers switching between the two for the same file should not
    expect line counts to match if the file lacks a final newline.
*/
