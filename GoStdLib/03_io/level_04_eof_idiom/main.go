/*
LEVEL 04 (core) - the io.EOF idiom, including n>0 AND io.EOF in one call

You will learn
  - io.EOF is a plain `error` value (errors.New("EOF")), not a panic - "no more
    data" is normal control flow, checked with errors.Is(err, io.EOF)
  - the Read contract explicitly PERMITS returning n>0 together with io.EOF in
    the SAME call: "a Reader returning a non-zero number of bytes at the end
    of the input stream may return either err == EOF or err == nil"
  - the correct read loop always processes n bytes BEFORE checking err

Run: go run ./GoStdLib/03_io/level_04_eof_idiom
*/

package main

import (
	"errors"
	"fmt"
	"io"
)

// finalChunkReader serves its payload from an internal offset, and - per what
// the io.Reader contract explicitly allows - returns io.EOF ALONGSIDE the
// final chunk of data instead of waiting for a separate zero-byte Read to
// signal the end. Whether that final chunk arrives on the first call or the
// last of several depends only on how big the caller's buffer is.
type finalChunkReader struct {
	data []byte
	pos  int
}

func (r *finalChunkReader) Read(p []byte) (int, error) {
	if r.pos >= len(r.data) {
		return 0, io.EOF
	}
	n := copy(p, r.data[r.pos:])
	r.pos += n
	if r.pos >= len(r.data) {
		return n, io.EOF // n > 0 AND io.EOF, together, on purpose
	}
	return n, nil
}

func main() {
	src := &finalChunkReader{data: []byte("last bytes ride along with EOF")}
	buf := make([]byte, 64)

	n, err := src.Read(buf)

	// THE TRAP if done wrong: checking err first and discarding n would lose
	// these bytes. The correct order is: use n now, THEN look at err.
	got := string(buf[:n])
	if got != "last bytes ride along with EOF" {
		panic(fmt.Sprintf("expected to recover the payload from the same call as EOF, got %q", got))
	}
	if !errors.Is(err, io.EOF) {
		panic(fmt.Sprintf("expected io.EOF alongside the data, got %v", err))
	}
	if n == 0 {
		panic("expected n > 0 in the very call that also reports io.EOF")
	}

	// A correct manual read loop: always consume n before checking err, and
	// only stop looping once err != nil.
	src2 := &finalChunkReader{data: []byte("read loops must drain n before checking err")}
	var collected []byte
	readBuf := make([]byte, 8) // small buffer: forces multiple Read calls
	for {
		cn, cerr := src2.Read(readBuf)
		if cn > 0 {
			collected = append(collected, readBuf[:cn]...)
		}
		if cerr != nil {
			if !errors.Is(cerr, io.EOF) {
				panic(fmt.Sprintf("unexpected read error: %v", cerr))
			}
			break // EOF is the expected, successful end of the stream
		}
	}
	want := "read loops must drain n before checking err"
	if string(collected) != want {
		panic(fmt.Sprintf("loop collected wrong data: got %q, want %q", collected, want))
	}

	// io.EOF is a plain value, safe to compare directly, and it is not special
	// beyond being the agreed sentinel - errors.Is is the wrapper-safe way in.
	if io.EOF.Error() != "EOF" {
		panic(fmt.Sprintf("expected io.EOF.Error() == %q, got %q", "EOF", io.EOF.Error()))
	}

	fmt.Printf("single call returned n=%d bytes together with err=%v\n", n, err)
	fmt.Printf("read loop collected %d bytes across multiple 8-byte Read calls\n", len(collected))
	fmt.Println("OK")
}
