/*
LEVEL 03 (core) - io.ReadAll and io.LimitReader

You will learn
  - io.ReadAll reads a Reader until EOF and returns everything as []byte,
    with a nil error on a clean EOF (not io.EOF itself)
  - io.LimitReader wraps a Reader so reads stop after N bytes, even if the
    underlying source has more - critical for bounding untrusted input
  - LimitReader's N field can be inspected to see how much quota is left

Run: go run ./GoStdLib/03_io/level_03_readall_and_limitreader
*/

package main

import (
	"fmt"
	"io"
	"strings"
)

func main() {
	src := strings.NewReader("the quick brown fox jumps over the lazy dog")

	all, err := io.ReadAll(src)
	if err != nil {
		panic(fmt.Sprintf("ReadAll failed: %v", err))
	}
	if string(all) != "the quick brown fox jumps over the lazy dog" {
		panic(fmt.Sprintf("ReadAll content mismatch: got %q", all))
	}

	// ReadAll on an empty reader returns a non-nil, zero-length slice and no error.
	empty, err := io.ReadAll(strings.NewReader(""))
	if err != nil {
		panic(fmt.Sprintf("ReadAll on empty reader failed: %v", err))
	}
	if len(empty) != 0 {
		panic(fmt.Sprintf("expected 0 bytes from empty reader, got %d", len(empty)))
	}

	// LimitReader: cap how much gets read regardless of source size.
	full := strings.NewReader("0123456789")
	limited := io.LimitReader(full, 4)
	capped, err := io.ReadAll(limited)
	if err != nil {
		panic(fmt.Sprintf("ReadAll on LimitReader failed: %v", err))
	}
	if string(capped) != "0123" {
		panic(fmt.Sprintf("LimitReader mismatch: got %q, want %q", capped, "0123"))
	}

	// The underlying reader is NOT exhausted - only the limited view stopped.
	rest, err := io.ReadAll(full)
	if err != nil {
		panic(fmt.Sprintf("ReadAll on remainder failed: %v", err))
	}
	if string(rest) != "456789" {
		panic(fmt.Sprintf("expected remaining underlying bytes %q, got %q", "456789", rest))
	}

	// Asking a LimitReader for more than it allows still stops exactly at N,
	// even across multiple manual Read calls.
	lr := &io.LimitedReader{R: strings.NewReader("abcdefgh"), N: 3}
	buf := make([]byte, 10)
	n, _ := lr.Read(buf)
	if n != 3 {
		panic(fmt.Sprintf("expected LimitedReader to cap the single Read at 3 bytes, got %d", n))
	}
	if lr.N != 0 {
		panic(fmt.Sprintf("expected LimitedReader.N to reach 0, got %d", lr.N))
	}
	n2, err2 := lr.Read(buf)
	if n2 != 0 || err2 != io.EOF {
		panic(fmt.Sprintf("expected (0, io.EOF) once quota is exhausted, got (%d, %v)", n2, err2))
	}

	fmt.Printf("ReadAll: %d bytes\n", len(all))
	fmt.Printf("LimitReader(4): %q, remainder still readable: %q\n", capped, rest)
	fmt.Println("OK")
}
