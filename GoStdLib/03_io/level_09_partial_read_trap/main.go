/*
LEVEL 09 (advanced) - correctness trap: assuming one Read() fills the buffer

You will learn
  - io.Reader's contract NEVER promises that Read fills the whole slice you
    pass it, even if more data is available and no error occurred - a single
    short read is completely legal, not an edge case
  - "assume one Read call gets everything" is a real, common bug that silently
    truncates or corrupts data instead of crashing - demonstrated here for real
  - the fix: loop until the buffer is full or an error occurs (io.ReadFull
    does exactly this for a known target size)

Run: go run ./GoStdLib/03_io/level_09_partial_read_trap
*/

package main

import (
	"bytes"
	"errors"
	"fmt"
	"io"
)

// stingyReader legally returns AT MOST maxPerCall bytes per Read, even when
// the caller's buffer is bigger and more data remains - exactly how a real
// network connection or pipe behaves under load.
type stingyReader struct {
	data       []byte
	pos        int
	maxPerCall int
}

func (r *stingyReader) Read(p []byte) (int, error) {
	if r.pos >= len(r.data) {
		return 0, io.EOF
	}
	max := r.maxPerCall
	if len(p) < max {
		max = len(p)
	}
	end := r.pos + max
	if end > len(r.data) {
		end = len(r.data)
	}
	n := copy(p, r.data[r.pos:end])
	r.pos += n
	return n, nil // nil error: perfectly legal short read, not EOF yet
}

func main() {
	payload := []byte("this payload is definitely longer than five bytes per call")

	// THE TRAP: a naive caller assumes ONE Read call fills the 64-byte buffer.
	naiveSrc := &stingyReader{data: payload, maxPerCall: 5}
	buf := make([]byte, 64)
	n, err := naiveSrc.Read(buf) // single call, no loop
	if err != nil {
		panic(fmt.Sprintf("unexpected error on first Read: %v", err))
	}
	naiveResult := buf[:n]

	if n >= len(payload) {
		panic(fmt.Sprintf("test setup broken: expected a short read, got the full %d bytes in one call", n))
	}
	if !bytes.Equal(naiveResult, payload[:n]) {
		panic("naive read produced unexpected bytes")
	}
	// This is the bug, made visible: the "obvious" single-Read code silently
	// ends up with only a fragment of the real payload, no error to notice.
	if bytes.Equal(naiveResult, payload) {
		panic("test is broken: naive read should NOT equal the full payload")
	}

	// THE FIX: io.ReadFull loops internally until the buffer is full, or
	// returns io.ErrUnexpectedEOF/io.EOF if the source runs out first.
	fixedSrc := &stingyReader{data: payload, maxPerCall: 5}
	fixedBuf := make([]byte, len(payload))
	fn, ferr := io.ReadFull(fixedSrc, fixedBuf)
	if ferr != nil {
		panic(fmt.Sprintf("io.ReadFull failed: %v", ferr))
	}
	if fn != len(payload) {
		panic(fmt.Sprintf("expected io.ReadFull to fill all %d bytes, got %d", len(payload), fn))
	}
	if !bytes.Equal(fixedBuf, payload) {
		panic(fmt.Sprintf("io.ReadFull result mismatch: got %q, want %q", fixedBuf, payload))
	}

	// io.ReadFull also reports the right error when there ISN'T enough data:
	// io.ErrUnexpectedEOF (not plain io.EOF) because SOME bytes were read
	// before the source ran out.
	shortSrc := &stingyReader{data: []byte("short"), maxPerCall: 2}
	tooBig := make([]byte, 10)
	_, shortErr := io.ReadFull(shortSrc, tooBig)
	if !errors.Is(shortErr, io.ErrUnexpectedEOF) {
		panic(fmt.Sprintf("expected io.ErrUnexpectedEOF, got %v", shortErr))
	}

	fmt.Printf("naive single Read got only %d of %d bytes: %q\n", n, len(payload), naiveResult)
	fmt.Printf("io.ReadFull correctly assembled all %d bytes: %q\n", fn, fixedBuf)
	fmt.Printf("io.ReadFull on a too-short source reports: %v\n", shortErr)
	fmt.Println("OK")
}
