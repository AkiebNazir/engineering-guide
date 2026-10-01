/*
LEVEL 09 (advanced) - production trap: Scanner.Bytes() aliases the internal buffer

You will learn
  - Scanner.Bytes() returns a slice into the scanner's OWN internal buffer
  - that buffer is overwritten on the next Scan() call - storing the slice
    without copying corrupts what you thought you'd already saved
  - the fix: copy the bytes (or just use Text(), which already copies) before
    the next Scan()

Run: go run ./GoStdLib/04_bufio/level_09_scanner_bytes_aliasing
*/

package main

import (
	"bufio"
	"bytes"
	"fmt"
	"io"
)

// tinyReader forces bufio.Scanner to refill its buffer in small, uneven
// chunks (instead of satisfying the whole scan from one big Read), which is
// what makes the scanner shift/compact its internal buffer - and that shift
// is what overwrites previously-returned Bytes() slices.
type tinyReader struct {
	data []byte
}

func (t *tinyReader) Read(p []byte) (int, error) {
	if len(t.data) == 0 {
		return 0, io.EOF
	}
	n := copy(p, t.data[:min(3, len(t.data))]) // never more than 3 bytes at a time
	t.data = t.data[n:]
	return n, nil
}

func main() {
	input := "aaaa\nbb\ncccccc\n"
	const tinyBufSize = 8 // smaller than the input, forces multiple fills + compaction

	// --- BROKEN: collect scanner.Bytes() directly across iterations. ---
	broken := bufio.NewScanner(&tinyReader{data: []byte(input)})
	broken.Buffer(make([]byte, tinyBufSize), 64)
	var brokenTokens [][]byte
	for broken.Scan() {
		brokenTokens = append(brokenTokens, broken.Bytes()) // aliasing bug
	}
	if err := broken.Err(); err != nil {
		panic(fmt.Sprintf("scanner error: %v", err))
	}
	if len(brokenTokens) != 3 {
		panic(fmt.Sprintf("got %d tokens, expected 3", len(brokenTokens)))
	}

	// By the time we look back, the buffer has been shifted/refilled under
	// earlier tokens - at least one of the retained slices no longer reads
	// back what it did at the moment it was returned.
	corrupted := !bytes.Equal(brokenTokens[0], []byte("aaaa")) ||
		!bytes.Equal(brokenTokens[1], []byte("bb"))
	if !corrupted {
		panic("expected the aliasing bug to corrupt earlier retained slices, but all still read back correctly")
	}
	fmt.Printf("BROKEN: retained slices now read back as %q, %q, %q (should be \"aaaa\", \"bb\", \"cccccc\")\n",
		brokenTokens[0], brokenTokens[1], brokenTokens[2])

	// --- FIXED: copy the bytes out before the next Scan() overwrites them. ---
	fixed := bufio.NewScanner(&tinyReader{data: []byte(input)})
	fixed.Buffer(make([]byte, tinyBufSize), 64)
	var fixedTokens [][]byte
	for fixed.Scan() {
		tok := fixed.Bytes()
		owned := make([]byte, len(tok))
		copy(owned, tok)
		fixedTokens = append(fixedTokens, owned)
	}
	if err := fixed.Err(); err != nil {
		panic(fmt.Sprintf("scanner error: %v", err))
	}

	expected := [][]byte{[]byte("aaaa"), []byte("bb"), []byte("cccccc")}
	if len(fixedTokens) != len(expected) {
		panic(fmt.Sprintf("got %d tokens, expected %d", len(fixedTokens), len(expected)))
	}
	for i, want := range expected {
		if !bytes.Equal(fixedTokens[i], want) {
			panic(fmt.Sprintf("fixedTokens[%d] = %q, expected %q", i, fixedTokens[i], want))
		}
	}
	fmt.Printf("FIXED: copied slices read back correctly: %q %q %q\n", fixedTokens[0], fixedTokens[1], fixedTokens[2])

	fmt.Println("OK")
}
