/*
LEVEL 04 (core) - real errors: io.EOF from Buffer.ReadString/ReadByte

You will learn
  - bytes.Buffer.ReadString(delim) reads up to and including delim, or returns
    everything it has plus a real io.EOF if delim never appears
  - the same io.EOF sentinel used across the whole io ecosystem - check it with
    errors.Is, not by comparing error strings
  - ReadByte on an empty Buffer returns the same io.EOF

Run: go run ./GoStdLib/07_bytes/level_04_eof_and_readstring
*/

package main

import (
	"bytes"
	"errors"
	"fmt"
	"io"
)

func main() {
	buf := bytes.NewBufferString("first;second;third")

	// ReadString('\'') successfully finds the delimiter twice...
	first, err := buf.ReadString(';')
	if err != nil {
		panic(fmt.Sprintf("unexpected error on first ReadString: %v", err))
	}
	if first != "first;" {
		panic(fmt.Sprintf("first = %q, want %q", first, "first;"))
	}

	second, err := buf.ReadString(';')
	if err != nil {
		panic(fmt.Sprintf("unexpected error on second ReadString: %v", err))
	}
	if second != "second;" {
		panic(fmt.Sprintf("second = %q, want %q", second, "second;"))
	}

	// ...but the delimiter never appears a third time, so ReadString returns
	// what remains AND a real io.EOF, for real, not a fabricated description.
	third, err := buf.ReadString(';')
	if !errors.Is(err, io.EOF) {
		panic(fmt.Sprintf("expected io.EOF on third ReadString, got %v", err))
	}
	if third != "third" {
		panic(fmt.Sprintf("third = %q, want %q (data up to EOF is still returned)", third, "third"))
	}

	// The buffer is now empty. ReadByte on an empty Buffer returns the same
	// sentinel - one error value, reused everywhere in io.
	if _, err := buf.ReadByte(); !errors.Is(err, io.EOF) {
		panic(fmt.Sprintf("expected io.EOF from ReadByte on empty buffer, got %v", err))
	}

	// A wrapped EOF still satisfies errors.Is - this is why errors.Is exists.
	wrapped := fmt.Errorf("reading config: %w", io.EOF)
	if !errors.Is(wrapped, io.EOF) {
		panic("wrapped io.EOF should still satisfy errors.Is")
	}
	// But it must never be found by comparing strings or with ==.
	if wrapped == io.EOF { //nolint:errorlint // deliberately shown as the wrong way
		panic("wrapped error must not be == io.EOF directly")
	}

	fmt.Println("confirmed: ReadString/ReadByte report end-of-data with real io.EOF")
	fmt.Println("OK")
}
