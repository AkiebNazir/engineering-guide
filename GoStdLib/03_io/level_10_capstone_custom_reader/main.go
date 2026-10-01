/*
LEVEL 10 (capstone) - a custom Reader from scratch, driven through Copy/Limit/MultiWriter

You will learn
  - writing a minimal io.Reader from nothing but the Read(p []byte) (int, error)
    signature: a repeatingReader that cycles a short pattern up to a fixed total
  - wiring it through io.LimitReader, io.TeeReader, and io.MultiWriter together,
    exactly like levels 3, 5, and 9 taught individually, now combined
  - handling the n>0-with-EOF case correctly on the very last Read (level 4's lesson)

Run: go run ./GoStdLib/03_io/level_10_capstone_custom_reader
*/

package main

import (
	"bytes"
	"fmt"
	"io"
)

// repeatingReader is a from-scratch io.Reader: it cycles through "pattern"
// until it has produced exactly "total" bytes, then reports io.EOF - on the
// same call as the final bytes, per the Read contract (level 4's lesson).
type repeatingReader struct {
	pattern []byte
	total   int
	sent    int
}

func (r *repeatingReader) Read(p []byte) (int, error) {
	if r.sent >= r.total {
		return 0, io.EOF
	}
	remaining := r.total - r.sent
	n := len(p)
	if n > remaining {
		n = remaining
	}
	for i := 0; i < n; i++ {
		p[i] = r.pattern[(r.sent+i)%len(r.pattern)]
	}
	r.sent += n
	if r.sent >= r.total {
		return n, io.EOF // last chunk carries EOF, exactly as level 4 demonstrated
	}
	return n, nil
}

func main() {
	src := &repeatingReader{pattern: []byte("abc"), total: 10} // "abcabcabca"

	// Cap it with LimitReader (level 3), tee a copy into a side buffer while
	// reading (level 5), and fan the primary destination out to TWO writers
	// with MultiWriter (level 5), all driving the SAME custom Reader.
	limited := io.LimitReader(src, 8) // only the first 8 of the 10 bytes

	var sideEffect bytes.Buffer
	tee := io.TeeReader(limited, &sideEffect)

	var destA, destB bytes.Buffer
	fanOut := io.MultiWriter(&destA, &destB)

	n, err := io.Copy(fanOut, tee)
	if err != nil {
		panic(fmt.Sprintf("io.Copy failed: %v", err))
	}

	const want = "abcabcab" // first 8 bytes of "abcabcabca"
	if n != int64(len(want)) {
		panic(fmt.Sprintf("expected %d bytes copied, got %d", len(want), n))
	}
	if destA.String() != want {
		panic(fmt.Sprintf("destA mismatch: got %q, want %q", destA.String(), want))
	}
	if destB.String() != want {
		panic(fmt.Sprintf("destB mismatch: got %q, want %q", destB.String(), want))
	}
	if sideEffect.String() != want {
		panic(fmt.Sprintf("tee side-effect mismatch: got %q, want %q", sideEffect.String(), want))
	}

	// The custom Reader itself, driven directly without the LimitReader,
	// must still honor the full 10-byte total and the n>0-with-EOF rule on
	// its last call.
	direct := &repeatingReader{pattern: []byte("xy"), total: 5} // "xyxyx"
	full, ferr := io.ReadAll(direct)
	if ferr != nil {
		panic(fmt.Sprintf("ReadAll on custom reader failed: %v", ferr))
	}
	if string(full) != "xyxyx" {
		panic(fmt.Sprintf("direct read mismatch: got %q, want %q", full, "xyxyx"))
	}

	fmt.Printf("fanned out %d bytes to two destinations + a tee side-effect: %q\n", n, destA.String())
	fmt.Printf("custom Reader read directly to completion: %q\n", full)
	fmt.Println("OK")
}
