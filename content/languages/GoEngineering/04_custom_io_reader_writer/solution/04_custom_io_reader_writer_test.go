package streamtransform

import (
	"bytes"
	"errors"
	"fmt"
	"io"
	"strings"
	"sync"
	"testing"
	"time"
)

func TestUpperReaderFullRead(t *testing.T) {
	src := strings.NewReader("Hello, World! 123")
	r := NewUpperReader(src)

	got, err := io.ReadAll(r)
	if err != nil {
		t.Fatalf("ReadAll: %v", err)
	}
	want := "HELLO, WORLD! 123"
	if string(got) != want {
		t.Fatalf("got %q, want %q", got, want)
	}
}

func TestUpperReaderSmallBuffer(t *testing.T) {
	// Force many small Read calls (buffer far smaller than input) to
	// exercise the multi-Read path, not just a single Read that happens to
	// consume everything at once.
	input := strings.Repeat("abcXYZ123 ", 50)
	r := NewUpperReader(strings.NewReader(input))

	var out bytes.Buffer
	buf := make([]byte, 3) // deliberately tiny
	for {
		n, err := r.Read(buf)
		out.Write(buf[:n])
		if err == io.EOF {
			break
		}
		if err != nil {
			t.Fatalf("Read: %v", err)
		}
	}

	want := strings.ToUpper(input)
	if out.String() != want {
		t.Fatalf("got %q, want %q", out.String(), want)
	}
}

func TestUpperReaderMatchesStringsToUpperASCII(t *testing.T) {
	input := "The Quick Brown Fox Jumps Over 42 Lazy Dogs!?"
	r := NewUpperReader(strings.NewReader(input))
	got, err := io.ReadAll(r)
	if err != nil {
		t.Fatalf("ReadAll: %v", err)
	}
	if string(got) != strings.ToUpper(input) {
		t.Fatalf("got %q, want %q", got, strings.ToUpper(input))
	}
}

// errReader returns some data then a non-nil error, to test that an
// io.Reader wrapper honors the "n>0 AND err on the same call" contract.
type errReader struct {
	data []byte
	err  error
	sent bool
}

func (e *errReader) Read(p []byte) (int, error) {
	if e.sent {
		return 0, e.err
	}
	n := copy(p, e.data)
	e.sent = true
	return n, e.err // n > 0 together with err, same call
}

func TestUpperReaderReturnsDataWithSameCallError(t *testing.T) {
	er := &errReader{data: []byte("abc"), err: io.EOF}
	r := NewUpperReader(er)

	buf := make([]byte, 10)
	n, err := r.Read(buf)
	if err != io.EOF {
		t.Fatalf("expected io.EOF, got %v", err)
	}
	if n != 3 {
		t.Fatalf("expected n=3, got %d", n)
	}
	if string(buf[:n]) != "ABC" {
		t.Fatalf("expected data to be uppercased even with err set, got %q", buf[:n])
	}
}

func TestUpperReaderPropagatesNonEOFError(t *testing.T) {
	wantErr := errors.New("boom")
	er := &errReader{data: nil, err: wantErr, sent: true} // immediately errors
	r := NewUpperReader(er)

	buf := make([]byte, 10)
	_, err := r.Read(buf)
	if !errors.Is(err, wantErr) {
		t.Fatalf("expected wrapped/propagated error, got %v", err)
	}
}

func TestCountingWriterCountsCorrectly(t *testing.T) {
	var dst bytes.Buffer
	cw := NewCountingWriter(&dst)

	chunks := []string{"hello", ", ", "world", "!"}
	var want int64
	for _, c := range chunks {
		n, err := cw.Write([]byte(c))
		if err != nil {
			t.Fatalf("Write: %v", err)
		}
		if n != len(c) {
			t.Fatalf("Write returned n=%d, want %d", n, len(c))
		}
		want += int64(len(c))
	}

	if got := cw.Count(); got != want {
		t.Fatalf("Count() = %d, want %d", got, want)
	}
	if dst.String() != "hello, world!" {
		t.Fatalf("underlying writer got %q", dst.String())
	}
}

func TestCountingWriterConcurrentWritesAndReads(t *testing.T) {
	// Race many goroutines writing through the same CountingWriter against
	// a goroutine repeatedly polling Count() — the exact scenario the spec
	// calls out ("a metrics goroutine polling Count() while writes happen
	// concurrently"). Run this test with -race to catch a bare int64
	// regression.
	var dst safeDiscard
	cw := NewCountingWriter(&dst)

	const writers = 16
	const writesPerWriter = 200
	payload := []byte("x")

	var wg sync.WaitGroup
	wg.Add(writers)
	for i := 0; i < writers; i++ {
		go func() {
			defer wg.Done()
			for j := 0; j < writesPerWriter; j++ {
				if _, err := cw.Write(payload); err != nil {
					t.Errorf("Write: %v", err)
					return
				}
			}
		}()
	}

	stop := make(chan struct{})
	var readerWg sync.WaitGroup
	readerWg.Add(1)
	go func() {
		defer readerWg.Done()
		for {
			select {
			case <-stop:
				return
			default:
				_ = cw.Count()
			}
		}
	}()

	wg.Wait()
	close(stop)
	readerWg.Wait()

	want := int64(writers * writesPerWriter)
	if got := cw.Count(); got != want {
		t.Fatalf("Count() = %d, want %d", got, want)
	}
}

// safeDiscard is like io.Discard but as a concrete type usable as a struct
// field target; io.Discard itself is already safe for concurrent use, this
// just avoids any ambiguity about what's under test.
type safeDiscard struct{}

func (safeDiscard) Write(p []byte) (int, error) { return len(p), nil }

func TestLineSplitWriterSingleWriteSingleLine(t *testing.T) {
	var lines []string
	w := NewLineSplitWriter(func(line string) { lines = append(lines, line) })

	if _, err := w.Write([]byte("hello world\n")); err != nil {
		t.Fatalf("Write: %v", err)
	}
	want := []string{"hello world"}
	if !stringSlicesEqual(lines, want) {
		t.Fatalf("got %v, want %v", lines, want)
	}
}

func TestLineSplitWriterLineSplitAcrossWrites(t *testing.T) {
	var lines []string
	w := NewLineSplitWriter(func(line string) { lines = append(lines, line) })

	if _, err := w.Write([]byte("abc")); err != nil {
		t.Fatalf("Write: %v", err)
	}
	if len(lines) != 0 {
		t.Fatalf("expected no line delivered yet, got %v", lines)
	}
	if _, err := w.Write([]byte("def\n")); err != nil {
		t.Fatalf("Write: %v", err)
	}
	want := []string{"abcdef"}
	if !stringSlicesEqual(lines, want) {
		t.Fatalf("got %v, want %v", lines, want)
	}
}

func TestLineSplitWriterMultipleLinesInOneWrite(t *testing.T) {
	var lines []string
	w := NewLineSplitWriter(func(line string) { lines = append(lines, line) })

	if _, err := w.Write([]byte("one\ntwo\nthree\n")); err != nil {
		t.Fatalf("Write: %v", err)
	}
	want := []string{"one", "two", "three"}
	if !stringSlicesEqual(lines, want) {
		t.Fatalf("got %v, want %v", lines, want)
	}
}

func TestLineSplitWriterCRLF(t *testing.T) {
	var lines []string
	w := NewLineSplitWriter(func(line string) { lines = append(lines, line) })

	if _, err := w.Write([]byte("windows line\r\nunix line\n")); err != nil {
		t.Fatalf("Write: %v", err)
	}
	want := []string{"windows line", "unix line"}
	if !stringSlicesEqual(lines, want) {
		t.Fatalf("got %v, want %v", lines, want)
	}
}

func TestLineSplitWriterCRLFSplitAcrossWrites(t *testing.T) {
	// The trickiest case: the '\r' arrives at the end of one Write and the
	// '\n' arrives at the start of the next.
	var lines []string
	w := NewLineSplitWriter(func(line string) { lines = append(lines, line) })

	if _, err := w.Write([]byte("partial\r")); err != nil {
		t.Fatalf("Write: %v", err)
	}
	if _, err := w.Write([]byte("\nnext")); err != nil {
		t.Fatalf("Write: %v", err)
	}
	if err := w.Flush(); err != nil {
		t.Fatalf("Flush: %v", err)
	}
	want := []string{"partial", "next"}
	if !stringSlicesEqual(lines, want) {
		t.Fatalf("got %v, want %v", lines, want)
	}
}

func TestLineSplitWriterFlushDeliversTrailingPartialLine(t *testing.T) {
	var lines []string
	w := NewLineSplitWriter(func(line string) { lines = append(lines, line) })

	if _, err := w.Write([]byte("no newline at all")); err != nil {
		t.Fatalf("Write: %v", err)
	}
	if len(lines) != 0 {
		t.Fatalf("expected nothing delivered before Flush, got %v", lines)
	}
	if err := w.Flush(); err != nil {
		t.Fatalf("Flush: %v", err)
	}
	want := []string{"no newline at all"}
	if !stringSlicesEqual(lines, want) {
		t.Fatalf("got %v, want %v", lines, want)
	}
}

func TestLineSplitWriterFlushIsIdempotent(t *testing.T) {
	var calls int
	w := NewLineSplitWriter(func(line string) { calls++ })

	if _, err := w.Write([]byte("trailing")); err != nil {
		t.Fatalf("Write: %v", err)
	}
	if err := w.Flush(); err != nil {
		t.Fatalf("Flush: %v", err)
	}
	if err := w.Flush(); err != nil {
		t.Fatalf("second Flush: %v", err)
	}
	if err := w.Flush(); err != nil {
		t.Fatalf("third Flush: %v", err)
	}
	if calls != 1 {
		t.Fatalf("expected exactly 1 delivery from repeated Flush calls, got %d", calls)
	}
}

func TestLineSplitWriterFlushOnEmptyBufferIsNoop(t *testing.T) {
	var calls int
	w := NewLineSplitWriter(func(line string) { calls++ })

	if _, err := w.Write([]byte("complete line\n")); err != nil {
		t.Fatalf("Write: %v", err)
	}
	if calls != 1 {
		t.Fatalf("expected 1 call after complete line, got %d", calls)
	}
	if err := w.Flush(); err != nil {
		t.Fatalf("Flush: %v", err)
	}
	if calls != 1 {
		t.Fatalf("Flush after a fully-terminated line should not deliver again, got %d calls", calls)
	}
}

func stringSlicesEqual(a, b []string) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if a[i] != b[i] {
			return false
		}
	}
	return true
}

func TestStreamPipelineSuccess(t *testing.T) {
	src := strings.NewReader("stream this data through the pipeline")
	var dst bytes.Buffer

	if err := StreamPipeline(src, &dst); err != nil {
		t.Fatalf("StreamPipeline: %v", err)
	}

	want := strings.ToUpper("stream this data through the pipeline")
	if dst.String() != want {
		t.Fatalf("got %q, want %q", dst.String(), want)
	}
}

// failingReader errors after yielding some bytes, simulating a source that
// dies mid-stream (e.g. a reset connection).
type failingReader struct {
	data []byte
	err  error
	done bool
}

func (f *failingReader) Read(p []byte) (int, error) {
	if f.done {
		return 0, f.err
	}
	n := copy(p, f.data)
	f.done = true
	return n, nil
}

func TestStreamPipelinePropagatesSourceError(t *testing.T) {
	wantErr := errors.New("source exploded")
	src := &failingReader{data: []byte("partial data"), err: wantErr}
	var dst bytes.Buffer

	err := StreamPipeline(src, &dst)
	if err == nil {
		t.Fatal("expected an error from StreamPipeline")
	}
	if !errors.Is(err, wantErr) {
		t.Fatalf("expected propagated source error, got %v", err)
	}
}

// failingWriter errors on every Write, simulating a destination that
// rejects data (e.g. disk full, connection reset).
type failingWriter struct {
	err error
}

func (f *failingWriter) Write(p []byte) (int, error) {
	return 0, f.err
}

func TestStreamPipelinePropagatesDestError(t *testing.T) {
	wantErr := errors.New("dest rejected write")
	src := strings.NewReader(strings.Repeat("data ", 100))
	dst := &failingWriter{err: wantErr}

	err := StreamPipeline(src, dst)
	if err == nil {
		t.Fatal("expected an error from StreamPipeline")
	}
	if !errors.Is(err, wantErr) {
		t.Fatalf("expected propagated dest error, got %v", err)
	}
}

func TestStreamPipelineCompletesQuickly(t *testing.T) {
	// Per the acceptance criteria: no test in this package should block for
	// more than a fraction of a second. Run StreamPipeline in a goroutine
	// and fail the test if it doesn't finish promptly — this is how a
	// missing PipeWriter.Close/CloseWithError would surface as a hang
	// instead of silently passing.
	src := strings.NewReader(strings.Repeat("x", 4096))
	var dst bytes.Buffer

	done := make(chan error, 1)
	go func() {
		done <- StreamPipeline(src, &dst)
	}()

	select {
	case err := <-done:
		if err != nil {
			t.Fatalf("StreamPipeline: %v", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("StreamPipeline did not complete in time — likely a missing PipeWriter close")
	}
}

func TestLineSplitWriterManySmallWrites(t *testing.T) {
	var lines []string
	w := NewLineSplitWriter(func(line string) { lines = append(lines, line) })

	full := "the quick brown fox\njumps over\nthe lazy dog\n"
	for _, b := range []byte(full) {
		if _, err := w.Write([]byte{b}); err != nil {
			t.Fatalf("Write: %v", err)
		}
	}
	want := []string{"the quick brown fox", "jumps over", "the lazy dog"}
	if !stringSlicesEqual(lines, want) {
		t.Fatalf("got %v, want %v", lines, want)
	}
}

func TestCountingWriterUnderlyingWriteError(t *testing.T) {
	wantErr := errors.New("write failed")
	cw := NewCountingWriter(&failingWriter{err: wantErr})

	n, err := cw.Write([]byte("data"))
	if n != 0 {
		t.Fatalf("expected n=0 on failed write, got %d", n)
	}
	if !errors.Is(err, wantErr) {
		t.Fatalf("expected propagated error, got %v", err)
	}
	if cw.Count() != 0 {
		t.Fatalf("expected count to remain 0 after a failed write, got %d", cw.Count())
	}
}

func ExampleUpperReader() {
	r := NewUpperReader(strings.NewReader("hello from the example"))
	data, _ := io.ReadAll(r)
	fmt.Println(string(data))
	// Output: HELLO FROM THE EXAMPLE
}
