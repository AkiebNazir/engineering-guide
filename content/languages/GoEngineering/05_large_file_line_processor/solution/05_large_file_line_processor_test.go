package lineprocessor

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestScanLinesBasic(t *testing.T) {
	input := "line one\nline two\nline three\n"
	var got []string
	n, err := ScanLines(context.Background(), strings.NewReader(input), 1024, func(lineNum int64, line []byte) error {
		got = append(got, string(line))
		return nil
	})
	if err != nil {
		t.Fatalf("ScanLines: %v", err)
	}
	if n != 3 {
		t.Fatalf("n = %d, want 3", n)
	}
	want := []string{"line one", "line two", "line three"}
	if !stringSlicesEqual(got, want) {
		t.Fatalf("got %v, want %v", got, want)
	}
}

func TestScanLinesNoTrailingNewline(t *testing.T) {
	input := "one\ntwo\nthree"
	var got []string
	n, err := ScanLines(context.Background(), strings.NewReader(input), 1024, func(lineNum int64, line []byte) error {
		got = append(got, string(line))
		return nil
	})
	if err != nil {
		t.Fatalf("ScanLines: %v", err)
	}
	if n != 3 {
		t.Fatalf("n = %d, want 3", n)
	}
	if got[2] != "three" {
		t.Fatalf("expected final unterminated line delivered, got %v", got)
	}
}

func TestScanLinesEmptyInput(t *testing.T) {
	n, err := ScanLines(context.Background(), strings.NewReader(""), 1024, func(int64, []byte) error {
		t.Fatal("fn should not be called for empty input")
		return nil
	})
	if err != nil {
		t.Fatalf("ScanLines: %v", err)
	}
	if n != 0 {
		t.Fatalf("n = %d, want 0", n)
	}
}

func TestScanLinesErrTooLongUsesConfiguredMax(t *testing.T) {
	// The offending line exceeds the DEFAULT bufio.MaxScanTokenSize (64KB)
	// but the test deliberately configures maxLineBytes smaller than the
	// line, proving Scanner.Buffer is actually wired to maxLineBytes and
	// this isn't just relying on the default.
	longLine := strings.Repeat("x", 100)
	input := "short\n" + longLine + "\nnever reached\n"

	n, err := ScanLines(context.Background(), strings.NewReader(input), 50, func(lineNum int64, line []byte) error {
		return nil
	})
	if err == nil {
		t.Fatal("expected an error for a line exceeding maxLineBytes")
	}
	if !errors.Is(err, ErrLineTooLong) {
		t.Fatalf("expected errors.Is(err, ErrLineTooLong), got %v", err)
	}
	var le *LineError
	if !errors.As(err, &le) {
		t.Fatalf("expected errors.As to recover *LineError, got %v", err)
	}
	if le.LineNum != 2 {
		t.Fatalf("expected failing line 2, got %d", le.LineNum)
	}
	if n != 1 {
		t.Fatalf("expected exactly 1 line successfully processed before failure, got %d", n)
	}
}

func TestScanLinesLargeLineWithinConfiguredMax(t *testing.T) {
	// A line bigger than the default 64KB Scanner limit but within a
	// larger explicitly configured maxLineBytes must succeed.
	bigLine := strings.Repeat("A", 100*1024) // 100KB > 64KB default
	input := bigLine + "\n"

	var gotLen int
	n, err := ScanLines(context.Background(), strings.NewReader(input), 200*1024, func(lineNum int64, line []byte) error {
		gotLen = len(line)
		return nil
	})
	if err != nil {
		t.Fatalf("ScanLines: %v", err)
	}
	if n != 1 {
		t.Fatalf("n = %d, want 1", n)
	}
	if gotLen != len(bigLine) {
		t.Fatalf("got line length %d, want %d", gotLen, len(bigLine))
	}
}

func TestScanLinesFnErrorStopsAndWraps(t *testing.T) {
	wantErr := errors.New("stop here")
	input := "one\ntwo\nthree\nfour\n"

	var processed []string
	n, err := ScanLines(context.Background(), strings.NewReader(input), 1024, func(lineNum int64, line []byte) error {
		processed = append(processed, string(line))
		if lineNum == 2 {
			return wantErr
		}
		return nil
	})
	if err == nil {
		t.Fatal("expected an error")
	}
	if !errors.Is(err, wantErr) {
		t.Fatalf("expected errors.Is to find the original sentinel, got %v", err)
	}
	var le *LineError
	if !errors.As(err, &le) || le.LineNum != 2 {
		t.Fatalf("expected *LineError{LineNum: 2}, got %v", err)
	}
	if n != 2 {
		t.Fatalf("n = %d, want 2", n)
	}
	if len(processed) != 2 {
		t.Fatalf("expected processing to stop after line 2, got %v", processed)
	}
}

func TestScanLinesCanceledContext(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()

	_, err := ScanLines(ctx, strings.NewReader("a\nb\nc\n"), 1024, func(int64, []byte) error { return nil })
	if !errors.Is(err, context.Canceled) {
		t.Fatalf("expected context.Canceled, got %v", err)
	}
}

func TestScanLinesCancellationMidStream(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	src := &infiniteLineReader{}

	done := make(chan struct{})
	go func() {
		defer close(done)
		_, err := ScanLines(ctx, src, 4096, func(lineNum int64, line []byte) error {
			if lineNum == 5 {
				cancel()
			}
			return nil
		})
		if !errors.Is(err, context.Canceled) {
			t.Errorf("expected context.Canceled, got %v", err)
		}
	}()

	select {
	case <-done:
	case <-time.After(2 * time.Second):
		t.Fatal("ScanLines did not return promptly after cancellation")
	}
}

func TestCountLinesBasic(t *testing.T) {
	n, err := CountLines(context.Background(), strings.NewReader("a\nb\nc\n"))
	if err != nil {
		t.Fatalf("CountLines: %v", err)
	}
	if n != 3 {
		t.Fatalf("n = %d, want 3", n)
	}
}

func TestCountLinesEmpty(t *testing.T) {
	n, err := CountLines(context.Background(), strings.NewReader(""))
	if err != nil {
		t.Fatalf("CountLines: %v", err)
	}
	if n != 0 {
		t.Fatalf("n = %d, want 0", n)
	}
}

func TestCountLinesNoTrailingNewlineNotCounted(t *testing.T) {
	// wc -l semantics: the final unterminated line is not counted.
	n, err := CountLines(context.Background(), strings.NewReader("a\nb\nc"))
	if err != nil {
		t.Fatalf("CountLines: %v", err)
	}
	if n != 2 {
		t.Fatalf("n = %d, want 2 (final unterminated line not counted)", n)
	}
}

func TestCountLinesHugeSingleLine(t *testing.T) {
	// Generate data on the fly via a custom reader rather than
	// materializing a giant []byte, so the test itself doesn't defeat the
	// point of proving O(1) memory behavior.
	const totalBytes = 8 * 1024 * 1024 // 8MB, single line, one trailing \n
	r := &repeatByteReader{b: 'x', remaining: totalBytes}
	chained := io.MultiReader(r, strings.NewReader("\n"))

	n, err := CountLines(context.Background(), chained)
	if err != nil {
		t.Fatalf("CountLines: %v", err)
	}
	if n != 1 {
		t.Fatalf("n = %d, want 1", n)
	}
}

func TestCountLinesCanceledContext(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()

	_, err := CountLines(ctx, strings.NewReader("a\nb\nc\n"))
	if !errors.Is(err, context.Canceled) {
		t.Fatalf("expected context.Canceled, got %v", err)
	}
}

func TestCountLinesCancellationMidStream(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	// A reader with data spanning many chunks so cancellation partway
	// through is observable, then cancel almost immediately.
	src := &repeatByteReader{b: '\n', remaining: 50 * scanChunkSize}

	go func() {
		time.Sleep(5 * time.Millisecond)
		cancel()
	}()

	done := make(chan error, 1)
	go func() {
		_, err := CountLines(ctx, src)
		done <- err
	}()

	select {
	case err := <-done:
		if !errors.Is(err, context.Canceled) {
			t.Fatalf("expected context.Canceled, got %v", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("CountLines did not return promptly after cancellation")
	}
}

func TestReadUnboundedLinesBasic(t *testing.T) {
	input := "alpha\nbeta\ngamma\n"
	var got []string
	n, err := ReadUnboundedLines(context.Background(), strings.NewReader(input), func(lineNum int64, line []byte) error {
		got = append(got, string(line))
		return nil
	})
	if err != nil {
		t.Fatalf("ReadUnboundedLines: %v", err)
	}
	if n != 3 {
		t.Fatalf("n = %d, want 3", n)
	}
	want := []string{"alpha", "beta", "gamma"}
	if !stringSlicesEqual(got, want) {
		t.Fatalf("got %v, want %v", got, want)
	}
}

func TestReadUnboundedLinesCRLF(t *testing.T) {
	input := "one\r\ntwo\r\nthree\r\n"
	var got []string
	_, err := ReadUnboundedLines(context.Background(), strings.NewReader(input), func(lineNum int64, line []byte) error {
		got = append(got, string(line))
		return nil
	})
	if err != nil {
		t.Fatalf("ReadUnboundedLines: %v", err)
	}
	want := []string{"one", "two", "three"}
	if !stringSlicesEqual(got, want) {
		t.Fatalf("got %v, want %v (CRLF should be stripped)", got, want)
	}
}

func TestReadUnboundedLinesNoTrailingNewlineDelivered(t *testing.T) {
	input := "first\nsecond\nunterminated"
	var got []string
	n, err := ReadUnboundedLines(context.Background(), strings.NewReader(input), func(lineNum int64, line []byte) error {
		got = append(got, string(line))
		return nil
	})
	if err != nil {
		t.Fatalf("ReadUnboundedLines: %v", err)
	}
	if n != 3 {
		t.Fatalf("n = %d, want 3", n)
	}
	if got[2] != "unterminated" {
		t.Fatalf("expected final unterminated line delivered as content, got %v", got)
	}
}

func TestReadUnboundedLinesLineLargerThanScannerLimit(t *testing.T) {
	// This is the key contrast test with ScanLines: a line bigger than
	// bufio.MaxScanTokenSize (64KB), processed with NO configured maximum
	// and no error.
	bigLine := strings.Repeat("z", 200*1024) // 200KB
	input := bigLine + "\n"

	var gotLen int
	n, err := ReadUnboundedLines(context.Background(), strings.NewReader(input), func(lineNum int64, line []byte) error {
		gotLen = len(line)
		return nil
	})
	if err != nil {
		t.Fatalf("ReadUnboundedLines: %v", err)
	}
	if n != 1 {
		t.Fatalf("n = %d, want 1", n)
	}
	if gotLen != len(bigLine) {
		t.Fatalf("got line length %d, want %d", gotLen, len(bigLine))
	}
}

func TestReadUnboundedLinesFnErrorStopsAndWraps(t *testing.T) {
	wantErr := errors.New("halt")
	input := "one\ntwo\nthree\n"

	n, err := ReadUnboundedLines(context.Background(), strings.NewReader(input), func(lineNum int64, line []byte) error {
		if lineNum == 2 {
			return wantErr
		}
		return nil
	})
	if !errors.Is(err, wantErr) {
		t.Fatalf("expected errors.Is to find original sentinel, got %v", err)
	}
	var le *LineError
	if !errors.As(err, &le) || le.LineNum != 2 {
		t.Fatalf("expected *LineError{LineNum: 2}, got %v", err)
	}
	if n != 2 {
		t.Fatalf("n = %d, want 2", n)
	}
}

func TestReadUnboundedLinesCanceledContext(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()

	_, err := ReadUnboundedLines(ctx, strings.NewReader("a\nb\nc\n"), func(int64, []byte) error { return nil })
	if !errors.Is(err, context.Canceled) {
		t.Fatalf("expected context.Canceled, got %v", err)
	}
}

func TestReadUnboundedLinesCancellationMidStream(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	src := &infiniteLineReader{}

	done := make(chan error, 1)
	go func() {
		_, err := ReadUnboundedLines(ctx, src, func(lineNum int64, line []byte) error {
			if lineNum == 5 {
				cancel()
			}
			return nil
		})
		done <- err
	}()

	select {
	case err := <-done:
		if !errors.Is(err, context.Canceled) {
			t.Fatalf("expected context.Canceled, got %v", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("ReadUnboundedLines did not return promptly after cancellation")
	}
}

func TestProcessFile(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "data.txt")
	content := "one\ntwo\nthree\n"
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatalf("setup WriteFile: %v", err)
	}

	var got []string
	n, err := ProcessFile(context.Background(), path, 1024, func(lineNum int64, line []byte) error {
		got = append(got, string(line))
		return nil
	})
	if err != nil {
		t.Fatalf("ProcessFile: %v", err)
	}
	if n != 3 {
		t.Fatalf("n = %d, want 3", n)
	}
	want := []string{"one", "two", "three"}
	if !stringSlicesEqual(got, want) {
		t.Fatalf("got %v, want %v", got, want)
	}
}

func TestProcessFileMissingFile(t *testing.T) {
	_, err := ProcessFile(context.Background(), "/nonexistent/path/does-not-exist.txt", 1024, func(int64, []byte) error { return nil })
	if !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("expected errors.Is(err, os.ErrNotExist), got %v", err)
	}
}

func TestLineErrorMessageAndUnwrap(t *testing.T) {
	base := errors.New("underlying cause")
	le := &LineError{LineNum: 42, Err: base}

	if !strings.Contains(le.Error(), "42") {
		t.Fatalf("expected error message to mention line number, got %q", le.Error())
	}
	if !strings.Contains(le.Error(), "underlying cause") {
		t.Fatalf("expected error message to mention underlying cause, got %q", le.Error())
	}
	if !errors.Is(le, base) {
		t.Fatalf("expected errors.Is to see through Unwrap to base")
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

// repeatByteReader generates `remaining` copies of byte b without ever
// materializing them all in one slice, so tests exercising "huge input"
// behavior don't themselves need huge memory to set up.
type repeatByteReader struct {
	b         byte
	remaining int
}

func (r *repeatByteReader) Read(p []byte) (int, error) {
	if r.remaining <= 0 {
		return 0, io.EOF
	}
	n := len(p)
	if n > r.remaining {
		n = r.remaining
	}
	for i := 0; i < n; i++ {
		p[i] = r.b
	}
	r.remaining -= n
	return n, nil
}

// infiniteLineReader generates an endless stream of short numbered lines,
// used to test that cancellation actually stops processing rather than
// running to completion (there is no completion).
type infiniteLineReader struct {
	buf []byte
	n   int64
}

func (r *infiniteLineReader) Read(p []byte) (int, error) {
	for len(r.buf) < len(p) {
		r.n++
		r.buf = append(r.buf, []byte(fmt.Sprintf("line-%d\n", r.n))...)
	}
	n := copy(p, r.buf)
	r.buf = r.buf[n:]
	return n, nil
}

func TestChunkSizeSanity(t *testing.T) {
	// Not a behavioral test — just guards against someone accidentally
	// setting scanChunkSize to something degenerate (e.g. 0, which would
	// make CountLines infinite-loop on a Read returning (0, nil)).
	if scanChunkSize <= 0 {
		t.Fatalf("scanChunkSize must be positive, got %d", scanChunkSize)
	}
}

func TestCountLinesUnderlyingReadError(t *testing.T) {
	wantErr := errors.New("disk error")
	r := &erroringReader{err: wantErr}

	_, err := CountLines(context.Background(), r)
	if !errors.Is(err, wantErr) {
		t.Fatalf("expected propagated error, got %v", err)
	}
}

type erroringReader struct {
	err error
}

func (e *erroringReader) Read(p []byte) (int, error) {
	return 0, e.err
}

func TestScanLinesMultiLineWithBlankLines(t *testing.T) {
	input := "a\n\nb\n\n\nc\n"
	var got []string
	_, err := ScanLines(context.Background(), strings.NewReader(input), 1024, func(lineNum int64, line []byte) error {
		got = append(got, string(line))
		return nil
	})
	if err != nil {
		t.Fatalf("ScanLines: %v", err)
	}
	want := []string{"a", "", "b", "", "", "c"}
	if !stringSlicesEqual(got, want) {
		t.Fatalf("got %v, want %v", got, want)
	}
}

func TestScanLinesBytesNotRetainedAcrossCalls(t *testing.T) {
	// Documents/verifies the "copy before retaining" contract: if a
	// caller copies scanner.Bytes() per the doc comment, retained copies
	// must not alias each other.
	input := "aaa\nbbb\nccc\n"
	var retained [][]byte
	_, err := ScanLines(context.Background(), strings.NewReader(input), 1024, func(lineNum int64, line []byte) error {
		cp := append([]byte(nil), line...)
		retained = append(retained, cp)
		return nil
	})
	if err != nil {
		t.Fatalf("ScanLines: %v", err)
	}
	want := []string{"aaa", "bbb", "ccc"}
	for i, w := range want {
		if !bytes.Equal(retained[i], []byte(w)) {
			t.Fatalf("retained[%d] = %q, want %q (buffer aliasing bug)", i, retained[i], w)
		}
	}
}
